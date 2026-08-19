// Copyright 2026
//
// Whole-pass CUDA port of the VP8 lossy macroblock decimation (VP8Decimate at
// RD_OPT_BASIC through RD_OPT_TRELLIS_ALL): intra16/intra4/chroma mode search,
// quantization, trellis optimization, and reconstruction. Macroblocks are
// processed in skewed anti-diagonal order
// (t = x + 2y) so every block sees its left, top, and top-right neighbors'
// reconstruction, non-zero context, prediction modes, and diffusion errors
// exactly as the CPU raster scan does. Cost tables are fixed for the whole
// pass (the fork's token loop no longer refreshes them mid-pass), and all
// arithmetic is integer, so the output decisions are bit-exact with the CPU
// path and the final bitstream is byte-identical.

#include "src/enc/cuda_enc.h"

#if defined(WEBP_CUDA_ENABLE_LOSSY_DECIMATE)

#include <cuda_runtime.h>

#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#else
#include <pthread.h>
#endif

#include "src/enc/cuda_decimate_dsp.cuh"

// CPU cost tables reused verbatim on the device.
extern "C" {
extern const uint16_t VP8EntropyCost[256];
extern const uint16_t VP8LevelFixedCosts[2048];
extern const uint16_t VP8FixedCostsI16[4];
extern const uint16_t VP8FixedCostsUV[4];
extern const uint16_t VP8FixedCostsI4[10][10][10];
}

namespace {

// ---------------------------------------------------------------------------
// Constants mirroring the encoder.

constexpr int kNumPredModes = 4;    // intra16 / chroma modes
constexpr int kNumBModes = 10;      // intra4 modes
constexpr int kMaxVariableLevel = 67;
constexpr int kMaxLevel = 2047;
constexpr int kFlatnessLimitI16 = 10;
constexpr int kFlatnessLimitI4 = 3;
constexpr int kFlatnessLimitUV = 2;
constexpr int kFlatnessPenalty = 140;
constexpr int kRDDistoMult = 256;
constexpr long long kMaxCost = 0x7fffffffffffffLL;
constexpr unsigned int kDecimateThreads = 128u;
constexpr uint32_t kRDBasic = 1u;
constexpr uint32_t kRDTrellis = 2u;
constexpr uint32_t kRDTrellisAll = 3u;

// StoreDiffusionErrors / CorrectDCValues constants.
constexpr int kDerrC1 = 7;
constexpr int kDerrC2 = 8;
constexpr int kDerrShift = 4;
constexpr int kDerrScale = 1;

__device__ static const uint16_t kWeightY[16] = {
    38, 32, 20, 9, 32, 28, 17, 7, 20, 17, 10, 4, 9, 7, 4, 2};

__device__ static const uint8_t kEncBands[16 + 1] = {
    0, 1, 2, 3, 6, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 0};

// Snake positions of the i4 top pointer (VP8TopLeftI4).
__device__ static const uint8_t kTopLeftI4[16] = {
    17, 21, 25, 29, 13, 17, 21, 25, 9, 13, 17, 21, 5, 9, 13, 17};

// ---------------------------------------------------------------------------
// Host-uploaded static cost tables (copied from the encoder's symbols so the
// device never re-transcribes them).

struct StaticCostTables {
  uint16_t entropy_cost[256];        // VP8EntropyCost
  uint16_t level_fixed_costs[2048];  // VP8LevelFixedCosts[kMaxLevel + 1]
  uint16_t fixed_costs_i16[4];
  uint16_t fixed_costs_uv[4];
  uint16_t fixed_costs_i4[10][10][10];
};

struct DecimateKernelParams {
  uint32_t width;
  uint32_t height;
  uint32_t mb_w;
  uint32_t mb_h;
  uint32_t y_stride;       // source picture strides
  uint32_t uv_stride;
  uint32_t recon_y_stride;
  uint32_t recon_uv_stride;
  int32_t max_i4_header_bits;
  uint32_t use_error_diffusion;
  uint32_t rd_opt_level;
  uint32_t diagonal;       // current skewed diagonal (x + 2y)
  uint32_t y_min;          // first tile row on this diagonal
};

// Per-segment parameters in device-friendly layout (mirrors the ABI struct).
struct DeviceSegment {
  CudaVP8Matrix y1;
  CudaVP8Matrix y2;
  CudaVP8Matrix uv;
  int32_t lambda_i16;
  int32_t lambda_i4;
  int32_t lambda_uv;
  int32_t lambda_mode;
  int32_t lambda_trellis_i16;
  int32_t lambda_trellis_i4;
  int32_t lambda_trellis_uv;
  int32_t tlambda;
  int32_t min_disto;
};

// Result layout must match WebPAcceleratorDecimateResult byte-for-byte.
struct DeviceResult {
  int16_t y_dc_levels[16];
  int16_t y_ac_levels[16][16];
  int16_t uv_levels[8][16];
  uint32_t nz;
  uint32_t distortion;
  uint32_t header_bits;
  uint8_t is_i4;
  uint8_t mode_i16;
  uint8_t mode_uv;
  uint8_t store_max_delta;
  uint8_t modes_i4[16];
  int8_t derr[2][3];
  uint8_t reserved[2];
  uint16_t max_delta;
};

// All device buffers a pass works on.
struct DeviceView {
  const uint8_t* src_y;
  const uint8_t* src_u;
  const uint8_t* src_v;
  uint8_t* recon_y;
  uint8_t* recon_u;
  uint8_t* recon_v;
  const uint8_t* segments;         // per-MB segment id
  const DeviceSegment* segment_params;
  const uint16_t* level_costs;     // [4][8][3][68]
  const uint8_t* coeff_probas;     // [4][8][3][11]
  const StaticCostTables* tables;
  uint32_t* nz_words;              // per-MB packed nz (mb_w * mb_h)
  uint8_t* preds;                  // (4*mb_w+1) x (4*mb_h+1) with boundary
  int8_t* top_derr;                // per MB column: [mb_w][2][2]
  DeviceResult* results;
  // Diagnostic (WEBP_CUDA_DECIMATE_TIMING=2): per-phase cycle accumulators
  // [import, i16-numeric, i16-select, i4, uv-numeric, uv-select+assembly,
  // recon-write]. nullptr in normal operation.
  unsigned long long* phase_cycles;
};

// ---------------------------------------------------------------------------
// Cost model (bit-exact ports from cost_enc.c / dsp/cost.c).

// Pointers to the hot cost tables the serial residual-cost walks chase.
// The kernel points these at shared-memory copies so the walks' dependent
// loads hit shared latency instead of global.
struct CostCache {
  const uint16_t* level_costs;   // [4][8][3][68]
  const uint8_t* probas;         // [4][8][3][11]
  const uint16_t* entropy_cost;  // [256]
  const uint16_t* level_fixed;   // [2048]
};

__device__ __forceinline__ int BitCostDev(const CostCache* c, int bit,
                                          uint8_t proba) {
  return !bit ? c->entropy_cost[proba] : c->entropy_cost[255 - proba];
}

__device__ __forceinline__ int LevelCostDev(const CostCache* c,
                                            const uint16_t* table, int level) {
  return c->level_fixed[level] +
         table[(level > kMaxVariableLevel) ? kMaxVariableLevel : level];
}

// level_costs layout: [type][band][ctx][68]; probas layout: [type][band][ctx][11].
__device__ __forceinline__ const uint16_t* LevelCostTable(
    const CostCache* c, int type, int band, int ctx) {
  return c->level_costs + (((type * 8) + band) * 3 + ctx) * 68;
}

__device__ __forceinline__ uint8_t FirstProba(const CostCache* c, int type,
                                              int band, int ctx) {
  return c->probas[(((type * 8) + band) * 3 + ctx) * 11];
}

// GetResidualCost_C for one 16-coefficient block. 'first' is 0 or 1.
__device__ int ResidualCostDev(const CostCache* c, int ctx0, int first,
                               int coeff_type, const int16_t* coeffs) {
  int last = -1;
  for (int n = 15; n >= 0; --n) {
    if (coeffs[n]) {
      last = n;
      break;
    }
  }
  int n = first;
  const int p0 = FirstProba(c, coeff_type, kEncBands[n], ctx0);
  const uint16_t* t = LevelCostTable(c, coeff_type, kEncBands[n], ctx0);
  int cost = (ctx0 == 0) ? BitCostDev(c, 1, p0) : 0;
  if (last < 0) {
    return BitCostDev(c, 0, p0);
  }
  for (; n < last; ++n) {
    const int val = abs(coeffs[n]);
    const int ctx = (val >= 2) ? 2 : val;
    cost += LevelCostDev(c, t, val);
    t = LevelCostTable(c, coeff_type, kEncBands[n + 1], ctx);
  }
  {
    const int val = abs(coeffs[n]);
    cost += LevelCostDev(c, t, val);
    if (n < 15) {
      const int b = kEncBands[n + 1];
      const int ctx = (val == 1) ? 1 : 2;
      const int last_p0 = FirstProba(c, coeff_type, b, ctx);
      cost += BitCostDev(c, 0, last_p0);
    }
  }
  return cost;
}

// Warp-cooperative GetResidualCost_C: each coefficient's incoming context
// depends only on the previous coefficient's value (0/1/2+), so all 16
// costs are computed on parallel lanes and warp-reduced. Bit-exact against
// ResidualCostDev; must be called by all 32 lanes of a warp with uniform
// arguments. *nz_out receives BlockNonZero(coeffs).
__device__ int ResidualCostCoop16(const CostCache* c, int ctx0, int first,
                                  int coeff_type, const int16_t* coeffs,
                                  int lane, int* nz_out) {
  const unsigned mask = 0xffffffffu;
  const int n = lane;
  const int v = (n < 16) ? ((coeffs[n] < 0) ? -coeffs[n] : coeffs[n]) : 0;
  const unsigned nzmask = __ballot_sync(mask, v != 0) & 0xffffu;
  const int p0 = FirstProba(c, coeff_type, kEncBands[first], ctx0);
  *nz_out = (nzmask != 0);
  if (nzmask == 0) return BitCostDev(c, 0, p0);
  const int last = 31 - __clz(nzmask);
  const int vprev = __shfl_up_sync(mask, v, 1);
  int cost = 0;
  if (n >= first && n <= last) {
    const int ctx_in = (n == first) ? ctx0 : ((vprev >= 2) ? 2 : vprev);
    const uint16_t* const t =
        LevelCostTable(c, coeff_type, kEncBands[n], ctx_in);
    cost = LevelCostDev(c, t, v);
    if (n == last && n < 15) {
      const int ctx_eob = (v == 1) ? 1 : 2;
      cost += BitCostDev(c, 0,
                         FirstProba(c, coeff_type, kEncBands[n + 1], ctx_eob));
    }
  }
  for (int off = 16; off; off >>= 1) {
    cost += __shfl_down_sync(mask, cost, off);
  }
  cost = __shfl_sync(mask, cost, 0);
  return cost + ((ctx0 == 0) ? BitCostDev(c, 1, p0) : 0);
}

__device__ __forceinline__ int BlockNonZero(const int16_t* coeffs) {
  for (int n = 15; n >= 0; --n) {
    if (coeffs[n]) return 1;
  }
  return 0;
}

// TrellisQuantizeBlock, kept integer- and tie-exact with quant_enc.c. The
// method-5 path calls this only for the modes selected by the basic search.
struct TrellisNode {
  int8_t prev;
  int8_t sign;
  int16_t level;
};

struct TrellisScoreState {
  long long score;
  const uint16_t* costs;
};

__device__ __forceinline__ long long TrellisRDScore(int lambda,
                                                    long long rate,
                                                    long long distortion) {
  return rate * lambda + kRDDistoMult * distortion;
}

__device__ int TrellisQuantizeBlockDev(
    const CostCache* c, int16_t in[16], int16_t out[16], int ctx0,
    int coeff_type, const CudaVP8Matrix* mtx, int lambda) {
  static const int kWeights[16] = {30, 27, 19, 11, 27, 24, 17, 10,
                                   19, 17, 12, 8,  11, 10, 8,  6};
  TrellisNode nodes[16][2];
  TrellisScoreState states[2][2];
  TrellisScoreState* current = states[0];
  TrellisScoreState* previous = states[1];
  int best_path[3] = {-1, -1, -1};
  const int first = (coeff_type == 0) ? 1 : 0;
  long long best_score;
  int last;

  {
    const int threshold = mtx->q[1] * mtx->q[1] / 4;
    const int last_proba = FirstProba(c, coeff_type, kEncBands[first], ctx0);
    last = first - 1;
    for (int n = 15; n >= first; --n) {
      const int j = kCudaZigzag[n];
      const int error = in[j] * in[j];
      if (error > threshold) {
        last = n;
        break;
      }
    }
    if (last < 15) ++last;
    best_score = TrellisRDScore(lambda, BitCostDev(c, 0, last_proba), 0);
    for (int m = 0; m <= 1; ++m) {
      const long long rate = (ctx0 == 0) ? BitCostDev(c, 1, last_proba) : 0;
      current[m].score = TrellisRDScore(lambda, rate, 0);
      current[m].costs =
          LevelCostTable(c, coeff_type, kEncBands[first], ctx0);
    }
  }

  for (int n = first; n <= last; ++n) {
    const int j = kCudaZigzag[n];
    const uint32_t q = mtx->q[j];
    const uint32_t iq = mtx->iq[j];
    const int sign = (in[j] < 0);
    const int32_t coeff0 = (sign ? -in[j] : in[j]) + mtx->sharpen[j];
    int level0 = CudaQuantDiv(coeff0, iq, 0);
    int threshold_level = CudaQuantDiv(coeff0, iq, 0x80u << 9);
    TrellisScoreState* const swap = current;
    if (threshold_level > kMaxLevel) threshold_level = kMaxLevel;
    if (level0 > kMaxLevel) level0 = kMaxLevel;
    current = previous;
    previous = swap;

    for (int m = 0; m <= 1; ++m) {
      TrellisNode* const node = &nodes[n][m];
      const int level = level0 + m;
      const int ctx = (level > 2) ? 2 : level;
      const int band = kEncBands[n + 1];
      long long best_current;
      int best_previous = 0;
      if (n + 1 < 16) {
        current[m].costs = LevelCostTable(c, coeff_type, band, ctx);
      } else {
        current[m].costs = nullptr;
      }
      if (level < 0 || level > threshold_level) {
        current[m].score = kMaxCost;
        continue;
      }
      {
        const int new_error = coeff0 - level * (int32_t)q;
        const int delta_error =
            kWeights[j] * (new_error * new_error - coeff0 * coeff0);
        const long long base_score = TrellisRDScore(lambda, 0, delta_error);
        best_current =
            previous[0].score +
            TrellisRDScore(lambda,
                           LevelCostDev(c, previous[0].costs, level), 0);
        for (int p = 1; p <= 1; ++p) {
          const long long score =
              previous[p].score +
              TrellisRDScore(lambda,
                             LevelCostDev(c, previous[p].costs, level), 0);
          if (score < best_current) {
            best_current = score;
            best_previous = p;
          }
        }
        best_current += base_score;
      }
      node->sign = (int8_t)sign;
      node->level = (int16_t)level;
      node->prev = (int8_t)best_previous;
      current[m].score = best_current;
      if (level != 0 && best_current < best_score) {
        const long long last_position_cost =
            (n < 15) ? BitCostDev(c, 0, FirstProba(c, coeff_type, band, ctx))
                     : 0;
        const long long score =
            best_current + TrellisRDScore(lambda, last_position_cost, 0);
        if (score < best_score) {
          best_score = score;
          best_path[0] = n;
          best_path[1] = m;
          best_path[2] = best_previous;
        }
      }
    }
  }

  if (coeff_type == 0) {
    for (int i = 1; i < 16; ++i) in[i] = out[i] = 0;
  } else {
    for (int i = 0; i < 16; ++i) in[i] = out[i] = 0;
  }
  if (best_path[0] == -1) return 0;
  {
    int non_zero = 0;
    int best_node = best_path[1];
    int n = best_path[0];
    nodes[n][best_node].prev = (int8_t)best_path[2];
    for (; n >= first; --n) {
      const TrellisNode* const node = &nodes[n][best_node];
      const int j = kCudaZigzag[n];
      out[n] = node->sign ? -node->level : node->level;
      non_zero |= node->level;
      in[j] = (int16_t)(out[n] * mtx->q[j]);
      best_node = node->prev;
    }
    return (non_zero != 0);
  }
}

// ---------------------------------------------------------------------------
// Non-zero context words (iterator_enc.c NzToBytes/BytesToNz layouts).

struct NzContext {
  int top_nz[9];
  int left_nz[9];
};

__device__ void NzToBytes(uint32_t tnz, uint32_t lnz, NzContext* ctx) {
#define BITV(nz, n) (!!((nz) & (1u << (n))))
  ctx->top_nz[0] = BITV(tnz, 12);
  ctx->top_nz[1] = BITV(tnz, 13);
  ctx->top_nz[2] = BITV(tnz, 14);
  ctx->top_nz[3] = BITV(tnz, 15);
  ctx->top_nz[4] = BITV(tnz, 18);
  ctx->top_nz[5] = BITV(tnz, 19);
  ctx->top_nz[6] = BITV(tnz, 22);
  ctx->top_nz[7] = BITV(tnz, 23);
  ctx->top_nz[8] = BITV(tnz, 24);
  ctx->left_nz[0] = BITV(lnz, 3);
  ctx->left_nz[1] = BITV(lnz, 7);
  ctx->left_nz[2] = BITV(lnz, 11);
  ctx->left_nz[3] = BITV(lnz, 15);
  ctx->left_nz[4] = BITV(lnz, 17);
  ctx->left_nz[5] = BITV(lnz, 19);
  ctx->left_nz[6] = BITV(lnz, 21);
  ctx->left_nz[7] = BITV(lnz, 23);
#undef BITV
}

__device__ uint32_t BytesToNz(const NzContext* ctx) {
  uint32_t nz = 0;
  nz |= (ctx->top_nz[0] << 12) | (ctx->top_nz[1] << 13);
  nz |= (ctx->top_nz[2] << 14) | (ctx->top_nz[3] << 15);
  nz |= (ctx->top_nz[4] << 18) | (ctx->top_nz[5] << 19);
  nz |= (ctx->top_nz[6] << 22) | (ctx->top_nz[7] << 23);
  nz |= (ctx->top_nz[8] << 24);
  nz |= (ctx->left_nz[0] << 3) | (ctx->left_nz[1] << 7);
  nz |= (ctx->left_nz[2] << 11);
  nz |= (ctx->left_nz[4] << 17) | (ctx->left_nz[6] << 21);
  return nz;
}

// ---------------------------------------------------------------------------
// Mode-score bookkeeping (quant_enc.c InitScore/CopyScore/AddScore/SetRDScore).

struct ModeScore {
  long long D, SD, H, R, score;
  uint32_t nz;
};

__device__ __forceinline__ void InitScoreDev(ModeScore* rd) {
  rd->D = 0;
  rd->SD = 0;
  rd->R = 0;
  rd->H = 0;
  rd->nz = 0;
  rd->score = kMaxCost;
}

__device__ __forceinline__ void CopyScoreDev(ModeScore* dst,
                                             const ModeScore* src) {
  dst->D = src->D;
  dst->SD = src->SD;
  dst->R = src->R;
  dst->H = src->H;
  dst->nz = src->nz;
  dst->score = src->score;
}

__device__ __forceinline__ void AddScoreDev(ModeScore* dst,
                                            const ModeScore* src) {
  dst->D += src->D;
  dst->SD += src->SD;
  dst->R += src->R;
  dst->H += src->H;
  dst->nz |= src->nz;
  dst->score += src->score;
}

__device__ __forceinline__ void SetRDScoreDev(int lambda, ModeScore* rd) {
  rd->score = (rd->R + rd->H) * (long long)lambda +
              kRDDistoMult * (rd->D + rd->SD);
}

#define MULT_8B_DEV(a, b) (((a) * (b) + 128) >> 8)

// ---------------------------------------------------------------------------
// Shared per-macroblock working set.

struct MBWork {
  // Source and reconstruction in the encoder's BPS packed layout.
  uint8_t yuv_in[kCudaYuvSizeEnc];
  uint8_t yuv_out[kCudaYuvSizeEnc];    // running best (i16 -> maybe i4 -> +uv)
  uint8_t yuv_out2[kCudaYuvSizeEnc];   // scratch
  uint8_t yuv_p[kCudaPredSizeEnc];     // prediction cache
  // Borders: index 0 holds the top-left sample, samples start at index 1.
  uint8_t y_left[1 + 16];
  // U and V left borders share one buffer with the iterator's 16-byte
  // spacing: [0] U top-left, [1..8] U column, [16] V top-left, [17..24] V
  // column. IntraChromaPreds advances its left pointer by 16 for V.
  uint8_t uv_left[1 + 8 + 7 + 1 + 8];
  uint8_t y_top[16 + 4];
  uint8_t uv_top[16];
  int pred_dc[3];  // Y, U, V DC prediction values
  uint8_t i4_boundary[37];
  // Intra16 per-mode scratch.
  int16_t i16_tmp[4][16][16];
  int16_t i16_dc[4][16];
  int16_t i16_ac_levels[4][16][16];
  int16_t i16_dc_levels[4][16];
  uint8_t i16_out[4][16 * kCudaBPS];
  uint32_t i16_nz[4];
  long long i16_sse[4];
  long long i16_sd[4];
  int i16_flat[4];
  // Intra4 per-mode scratch (one sub-block at a time).
  int16_t i4_tmp[kNumBModes][16];
  int16_t i4_levels[kNumBModes][16];
  uint8_t i4_out[kNumBModes][4 * kCudaBPS];  // 4x4 samples, BPS stride
  int i4_transform_tmp[kNumBModes][16];
  int i4_nz[kNumBModes];
  long long i4_sse[kNumBModes];
  long long i4_sd[kNumBModes];
  int i4_flat[kNumBModes];
  long long i4_rcost[kNumBModes];
  // Chroma per-mode scratch.
  int16_t uv_tmp[4][8][16];
  int16_t uv_levels_all[4][8][16];
  uint8_t uv_out[4][8 * kCudaBPS];
  uint32_t uv_nz[4];
  long long uv_sse[4];
  int8_t uv_derr[4][2][3];
  // Decision state.
  NzContext nz_ctx;                 // neighbor-derived, evolves like the CPU
  DeviceResult rd;                  // staged result
  long long rd_score;
  long long rd_D, rd_SD, rd_R, rd_H;
};

// Four lanes cooperate on one I4 mode. Eight mode groups fit in warp 0 and
// the remaining two in warp 1, preserving the compact ten-way mode mapping
// while exposing the independent rows/columns of the separable transforms.
__device__ __forceinline__ void I4FTransformCoop4(
    const uint8_t* src, const uint8_t* ref, int16_t* out, int* tmp, int lane,
    unsigned int warp_mask) {
  const uint8_t* const src_row = src + lane * kCudaBPS;
  const uint8_t* const ref_row = ref + lane * kCudaBPS;
  const int d0 = src_row[0] - ref_row[0];
  const int d1 = src_row[1] - ref_row[1];
  const int d2 = src_row[2] - ref_row[2];
  const int d3 = src_row[3] - ref_row[3];
  const int a0 = d0 + d3;
  const int a1 = d1 + d2;
  const int a2 = d1 - d2;
  const int a3 = d0 - d3;
  tmp[0 + lane * 4] = (a0 + a1) * 8;
  tmp[1 + lane * 4] = (a2 * 2217 + a3 * 5352 + 1812) >> 9;
  tmp[2 + lane * 4] = (a0 - a1) * 8;
  tmp[3 + lane * 4] = (a3 * 2217 - a2 * 5352 + 937) >> 9;
  __syncwarp(warp_mask);

  const int b0 = tmp[0 + lane] + tmp[12 + lane];
  const int b1 = tmp[4 + lane] + tmp[8 + lane];
  const int b2 = tmp[4 + lane] - tmp[8 + lane];
  const int b3 = tmp[0 + lane] - tmp[12 + lane];
  out[0 + lane] = (int16_t)((b0 + b1 + 7) >> 4);
  out[4 + lane] =
      (int16_t)(((b2 * 2217 + b3 * 5352 + 12000) >> 16) + (b3 != 0));
  out[8 + lane] = (int16_t)((b0 - b1 + 7) >> 4);
  out[12 + lane] = (int16_t)((b3 * 2217 - b2 * 5352 + 51000) >> 16);
}

__device__ __forceinline__ int I4QuantizeBlockCoop4(
    int16_t* in, int16_t* out, const CudaVP8Matrix* mtx, int lane,
    unsigned int warp_mask) {
  int non_zero = 0;
  for (int n = lane; n < 16; n += 4) {
    const int j = kCudaZigzag[n];
    const int sign = (in[j] < 0);
    const uint32_t coeff = (sign ? -in[j] : in[j]) + mtx->sharpen[j];
    if (coeff > mtx->zthresh[j]) {
      const uint32_t Q = mtx->q[j];
      const uint32_t iQ = mtx->iq[j];
      const uint32_t B = mtx->bias[j];
      int level = CudaQuantDiv(coeff, iQ, B);
      if (level > kMaxLevel) level = kMaxLevel;
      if (sign) level = -level;
      in[j] = (int16_t)(level * (int)Q);
      out[n] = (int16_t)level;
      non_zero |= level;
    } else {
      out[n] = 0;
      in[j] = 0;
    }
  }
  const unsigned int group_shift = ((threadIdx.x & 31) >> 2) * 4;
  const unsigned int group_mask = 0xfu << group_shift;
  const unsigned int non_zero_lanes = __ballot_sync(warp_mask, non_zero != 0);
  return (non_zero_lanes & group_mask) != 0;
}

__device__ __forceinline__ void I4ITransformCoop4(
    const uint8_t* ref, const int16_t* in, uint8_t* dst, int* tmp, int lane,
    unsigned int warp_mask) {
  const int a = in[lane] + in[8 + lane];
  const int b = in[lane] - in[8 + lane];
  const int c = CudaTransformAc3Mul2(in[4 + lane]) -
                CudaTransformAc3Mul1(in[12 + lane]);
  const int d = CudaTransformAc3Mul1(in[4 + lane]) +
                CudaTransformAc3Mul2(in[12 + lane]);
  tmp[0 + lane * 4] = a + d;
  tmp[1 + lane * 4] = b + c;
  tmp[2 + lane * 4] = b - c;
  tmp[3 + lane * 4] = a - d;
  __syncwarp(warp_mask);

  const int dc = tmp[lane] + 4;
  const int e = dc + tmp[8 + lane];
  const int f = dc - tmp[8 + lane];
  const int g = CudaTransformAc3Mul2(tmp[4 + lane]) -
                CudaTransformAc3Mul1(tmp[12 + lane]);
  const int h = CudaTransformAc3Mul1(tmp[4 + lane]) +
                CudaTransformAc3Mul2(tmp[12 + lane]);
  uint8_t* const dst_row = dst + lane * kCudaBPS;
  const uint8_t* const ref_row = ref + lane * kCudaBPS;
  dst_row[0] = CudaClip8b(ref_row[0] + ((e + h) >> 3));
  dst_row[1] = CudaClip8b(ref_row[1] + ((f + g) >> 3));
  dst_row[2] = CudaClip8b(ref_row[2] + ((f - g) >> 3));
  dst_row[3] = CudaClip8b(ref_row[3] + ((e - h) >> 3));
}

// ---------------------------------------------------------------------------
// Import and borders.

__device__ void ImportSourceBlock(const uint8_t* src, uint32_t src_stride,
                                  uint8_t* dst, int w, int h, int size) {
  // ImportBlock: replicate the last column, then the last row.
  int i, j;
  for (i = 0; i < h; ++i) {
    for (j = 0; j < w; ++j) dst[j] = src[j];
    for (j = w; j < size; ++j) dst[j] = dst[w - 1];
    dst += kCudaBPS;
    src += src_stride;
  }
  for (i = h; i < size; ++i) {
    for (j = 0; j < size; ++j) dst[j] = dst[j - kCudaBPS];
    dst += kCudaBPS;
  }
}

__device__ void ImportMB(const DeviceView* v, const DecimateKernelParams* p,
                         int x, int y, MBWork* w) {
  const uint8_t* const ysrc = v->src_y + ((size_t)y * p->y_stride + x) * 16;
  const uint8_t* const usrc = v->src_u + ((size_t)y * p->uv_stride + x) * 8;
  const uint8_t* const vsrc = v->src_v + ((size_t)y * p->uv_stride + x) * 8;
  const int iw = min((int)p->width - x * 16, 16);
  const int ih = min((int)p->height - y * 16, 16);
  const int uv_w = (iw + 1) >> 1;
  const int uv_h = (ih + 1) >> 1;
  ImportSourceBlock(ysrc, p->y_stride, w->yuv_in + kCudaYOffEnc, iw, ih, 16);
  ImportSourceBlock(usrc, p->uv_stride, w->yuv_in + kCudaUOffEnc, uv_w, uv_h,
                    8);
  ImportSourceBlock(vsrc, p->uv_stride, w->yuv_in + kCudaVOffEnc, uv_w, uv_h,
                    8);
}

// Thread-parallel ImportMB. The replicate-last-column-then-last-row rule is
// the pure function dst(r, c) = src(min(r, h-1), min(c, w-1)), so every
// destination element is independent.
__device__ void ImportMBParallel(const DeviceView* v,
                                 const DecimateKernelParams* p, int x, int y,
                                 MBWork* w, int tid, int nthreads) {
  const uint8_t* const ysrc = v->src_y + ((size_t)y * p->y_stride + x) * 16;
  const uint8_t* const usrc = v->src_u + ((size_t)y * p->uv_stride + x) * 8;
  const uint8_t* const vsrc = v->src_v + ((size_t)y * p->uv_stride + x) * 8;
  const int iw = min((int)p->width - x * 16, 16);
  const int ih = min((int)p->height - y * 16, 16);
  const int uv_w = (iw + 1) >> 1;
  const int uv_h = (ih + 1) >> 1;
  for (int i = tid; i < 16 * 16 + 2 * 8 * 8; i += nthreads) {
    if (i < 256) {
      const int r = i >> 4, c = i & 15;
      w->yuv_in[kCudaYOffEnc + r * kCudaBPS + c] =
          ysrc[(size_t)min(r, ih - 1) * p->y_stride + min(c, iw - 1)];
    } else if (i < 320) {
      const int b = i - 256, r = b >> 3, c = b & 7;
      w->yuv_in[kCudaUOffEnc + r * kCudaBPS + c] =
          usrc[(size_t)min(r, uv_h - 1) * p->uv_stride + min(c, uv_w - 1)];
    } else {
      const int b = i - 320, r = b >> 3, c = b & 7;
      w->yuv_in[kCudaVOffEnc + r * kCudaBPS + c] =
          vsrc[(size_t)min(r, uv_h - 1) * p->uv_stride + min(c, uv_w - 1)];
    }
  }
}

// Rebuild the iterator's left/top borders from the reconstructed planes with
// the exact out-of-frame conventions (left 129, top 127, InitLeft top-left).
__device__ void BuildBorders(const DeviceView* v,
                             const DecimateKernelParams* p, int x, int y,
                             MBWork* w) {
  const uint32_t ys = p->recon_y_stride;
  const uint32_t uvs = p->recon_uv_stride;
  int i;
  if (x > 0) {
    const uint8_t* const ly =
        v->recon_y + (size_t)y * 16 * ys + (size_t)x * 16 - 1;
    const uint8_t* const lu =
        v->recon_u + (size_t)y * 8 * uvs + (size_t)x * 8 - 1;
    const uint8_t* const lv =
        v->recon_v + (size_t)y * 8 * uvs + (size_t)x * 8 - 1;
    for (i = 0; i < 16; ++i) w->y_left[1 + i] = ly[(size_t)i * ys];
    for (i = 0; i < 8; ++i) {
      w->uv_left[1 + i] = lu[(size_t)i * uvs];
      w->uv_left[17 + i] = lv[(size_t)i * uvs];
    }
    if (y > 0) {
      w->y_left[0] = *(ly - ys);
      w->uv_left[0] = *(lu - uvs);
      w->uv_left[16] = *(lv - uvs);
    } else {
      // The saved top row was initialized to 127 before the first row.
      w->y_left[0] = 127;
      w->uv_left[0] = 127;
      w->uv_left[16] = 127;
    }
  } else {
    const uint8_t top_left = (y > 0) ? 129 : 127;
    w->y_left[0] = top_left;
    w->uv_left[0] = top_left;
    w->uv_left[16] = top_left;
    for (i = 0; i < 16; ++i) w->y_left[1 + i] = 129;
    for (i = 0; i < 8; ++i) {
      w->uv_left[1 + i] = 129;
      w->uv_left[17 + i] = 129;
    }
  }
  if (y > 0) {
    const uint8_t* const ty =
        v->recon_y + ((size_t)y * 16 - 1) * ys + (size_t)x * 16;
    const uint8_t* const tu =
        v->recon_u + ((size_t)y * 8 - 1) * uvs + (size_t)x * 8;
    const uint8_t* const tv =
        v->recon_v + ((size_t)y * 8 - 1) * uvs + (size_t)x * 8;
    for (i = 0; i < 16; ++i) w->y_top[i] = ty[i];
    // Top-right luma context (used by intra4 only): next macroblock when it
    // exists, else the CPU's replication of the last valid sample.
    if (x < (int)p->mb_w - 1) {
      for (i = 0; i < 4; ++i) w->y_top[16 + i] = ty[16 + i];
    } else {
      for (i = 0; i < 4; ++i) w->y_top[16 + i] = ty[15];
    }
    for (i = 0; i < 8; ++i) {
      w->uv_top[i] = tu[i];
      w->uv_top[8 + i] = tv[i];
    }
  } else {
    for (i = 0; i < 20; ++i) w->y_top[i] = 127;
    for (i = 0; i < 16; ++i) w->uv_top[i] = 127;
  }
}

__device__ int PredictionDC(const uint8_t* left, const uint8_t* top,
                            int size, int round, int shift) {
  int dc = 0;
  if (top != nullptr) {
    for (int i = 0; i < size; ++i) dc += top[i];
    if (left != nullptr) {
      for (int i = 0; i < size; ++i) dc += left[i];
    } else {
      dc += dc;
    }
    return (dc + round) >> shift;
  }
  if (left != nullptr) {
    for (int i = 0; i < size; ++i) dc += left[i];
    dc += dc;
    return (dc + round) >> shift;
  }
  return 0x80;
}

__device__ void MakeIntraPredsParallel(MBWork* w, int x, int y, int tid,
                                       int nthreads) {
  const uint8_t* const y_left = (x > 0) ? w->y_left + 1 : nullptr;
  const uint8_t* const y_top = (y > 0) ? w->y_top : nullptr;
  const uint8_t* const uv_left = (x > 0) ? w->uv_left + 1 : nullptr;
  const uint8_t* const uv_top = (y > 0) ? w->uv_top : nullptr;
  for (int i = tid; i < 4 * 16 * 16 + 4 * 2 * 8 * 8; i += nthreads) {
    if (i < 4 * 16 * 16) {
      const int mode = i >> 8;
      const int pixel = i & 255;
      const int r = pixel >> 4, c = pixel & 15;
      uint8_t value;
      if (mode == 0) {
        value = (uint8_t)w->pred_dc[0];
      } else if (mode == 1) {
        value = (y_left != nullptr)
                    ? ((y_top != nullptr)
                           ? CudaClip8b(y_top[c] + y_left[r] - y_left[-1])
                           : y_left[r])
                    : ((y_top != nullptr) ? y_top[c] : 129);
      } else if (mode == 2) {
        value = (y_top != nullptr) ? y_top[c] : 127;
      } else {
        value = (y_left != nullptr) ? y_left[r] : 129;
      }
      w->yuv_p[kCudaVP8I16ModeOffsets[mode] + r * kCudaBPS + c] = value;
    } else {
      const int index = i - 4 * 16 * 16;
      const int mode = index >> 7;
      const int channel_pixel = index & 127;
      const int channel = channel_pixel >> 6;
      const int pixel = channel_pixel & 63;
      const int r = pixel >> 3, c = pixel & 7;
      const uint8_t* const left =
          (uv_left != nullptr) ? uv_left + channel * 16 : nullptr;
      const uint8_t* const top =
          (uv_top != nullptr) ? uv_top + channel * 8 : nullptr;
      uint8_t value;
      if (mode == 0) {
        value = (uint8_t)w->pred_dc[1 + channel];
      } else if (mode == 1) {
        value = (left != nullptr)
                    ? ((top != nullptr)
                           ? CudaClip8b(top[c] + left[r] - left[-1])
                           : left[r])
                    : ((top != nullptr) ? top[c] : 129);
      } else if (mode == 2) {
        value = (top != nullptr) ? top[c] : 127;
      } else {
        value = (left != nullptr) ? left[r] : 129;
      }
      w->yuv_p[kCudaVP8UVModeOffsets[mode] + channel * 8 +
               r * kCudaBPS + c] = value;
    }
  }
}

// VP8IteratorStartI4's 37-sample boundary snake.
__device__ void StartI4Boundary(MBWork* w) {
  int i;
  for (i = 0; i < 17; ++i) {
    // The CPU reads y_left[15 - i], reaching y_left[-1] (the top-left
    // sample, our index 0) at i == 16.
    w->i4_boundary[i] = (i == 16) ? w->y_left[0] : w->y_left[1 + (15 - i)];
  }
  for (i = 0; i < 16 + 4; ++i) {
    // BuildBorders already applied the far-right replication to
    // y_top[16..19], covering both CPU branches.
    w->i4_boundary[17 + i] = w->y_top[i];
  }
}

// VP8IteratorRotateI4: refresh the snake from the just-reconstructed
// sub-block (in the BPS best-blocks buffer) and advance.
__device__ int RotateI4(MBWork* w, int* i4, const uint8_t* best_blocks_bps) {
  const uint8_t* const blk = best_blocks_bps + kCudaVP8Scan[*i4];
  uint8_t* const top = w->i4_boundary + kTopLeftI4[*i4];
  int i;
  for (i = 0; i <= 3; ++i) {
    top[-4 + i] = blk[i + 3 * kCudaBPS];
  }
  if ((*i4 & 3) != 3) {
    for (i = 0; i <= 2; ++i) {
      top[i] = blk[3 + (2 - i) * kCudaBPS];
    }
  } else {
    for (i = 0; i <= 3; ++i) {
      top[i] = top[i + 4];
    }
  }
  ++*i4;
  return (*i4 < 16);
}

// ---------------------------------------------------------------------------
// Error diffusion (QuantizeSingle/CorrectDCValues ports).

__device__ int QuantizeSingleDev(int16_t* v, const CudaVP8Matrix* mtx) {
  int value = *v;
  const int sign = (value < 0);
  if (sign) value = -value;
  if (value > (int)mtx->zthresh[0]) {
    const int q_value =
        CudaQuantDiv(value, mtx->iq[0], mtx->bias[0]) * mtx->q[0];
    const int err = (value - q_value);
    *v = sign ? -q_value : q_value;
    return (sign ? -err : err) >> kDerrScale;
  }
  *v = 0;
  return (sign ? -value : value) >> kDerrScale;
}

__device__ void CorrectDCValuesDev(const int8_t top_derr[2][2],
                                   const int8_t left_derr[2][2],
                                   const CudaVP8Matrix* mtx, int16_t tmp[][16],
                                   int8_t derr_out[2][3]) {
  int ch;
  for (ch = 0; ch <= 1; ++ch) {
    const int8_t* const top = top_derr[ch];
    const int8_t* const left = left_derr[ch];
    int16_t(*const c)[16] = &tmp[ch * 4];
    int err0, err1, err2, err3;
    c[0][0] += (kDerrC1 * top[0] + kDerrC2 * left[0]) >>
               (kDerrShift - kDerrScale);
    err0 = QuantizeSingleDev(&c[0][0], mtx);
    c[1][0] += (kDerrC1 * top[1] + kDerrC2 * err0) >>
               (kDerrShift - kDerrScale);
    err1 = QuantizeSingleDev(&c[1][0], mtx);
    c[2][0] += (kDerrC1 * err0 + kDerrC2 * left[1]) >>
               (kDerrShift - kDerrScale);
    err2 = QuantizeSingleDev(&c[2][0], mtx);
    c[3][0] += (kDerrC1 * err1 + kDerrC2 * err2) >>
               (kDerrShift - kDerrScale);
    err3 = QuantizeSingleDev(&c[3][0], mtx);
    derr_out[ch][0] = (int8_t)err1;
    derr_out[ch][1] = (int8_t)err2;
    derr_out[ch][2] = (int8_t)err3;
  }
}

// ---------------------------------------------------------------------------
// Neighbor state loads (wavefront inputs).

__device__ __forceinline__ uint32_t LoadNzWord(const DeviceView* v,
                                               const DecimateKernelParams* p,
                                               int x, int y) {
  if (x < 0 || y < 0) return 0u;
  return v->nz_words[(size_t)y * p->mb_w + x];
}

// Derives this macroblock's incoming top/left diffusion errors from the
// neighbors' stored errors, mirroring StoreDiffusionErrors.
__device__ void LoadDiffusionErrors(const DeviceView* v,
                                    const DecimateKernelParams* p, int x,
                                    int y, int8_t top_derr[2][2],
                                    int8_t left_derr[2][2]) {
  for (int ch = 0; ch <= 1; ++ch) {
    if (y > 0) {
      const DeviceResult* const t =
          &v->results[(size_t)(y - 1) * p->mb_w + x];
      const int8_t left1 = (int8_t)(3 * t->derr[ch][2] >> 2);
      top_derr[ch][0] = t->derr[ch][1];
      top_derr[ch][1] = (int8_t)(t->derr[ch][2] - left1);
    } else {
      top_derr[ch][0] = 0;
      top_derr[ch][1] = 0;
    }
    if (x > 0) {
      const DeviceResult* const l =
          &v->results[(size_t)y * p->mb_w + (x - 1)];
      left_derr[ch][0] = l->derr[ch][0];
      left_derr[ch][1] = (int8_t)(3 * l->derr[ch][2] >> 2);
    } else {
      left_derr[ch][0] = 0;
      left_derr[ch][1] = 0;
    }
  }
}

// Method 5 performs the ordinary mode search above, then trellis-quantizes
// only the selected modes. This must happen before the macroblock publishes
// its reconstruction: later wavefront blocks predict from these final pixels.
__device__ void ApplySelectedModeTrellis(
    const DecimateKernelParams* p, const CostCache* costs,
    const DeviceSegment* dqm, MBWork* w) {
  NzContext context = w->nz_ctx;
  uint32_t non_zero = 0;

  if (!w->rd.is_i4) {
    const int mode = w->rd.mode_i16;
    for (int block = 0; block < 16; ++block) {
      const uint8_t* const src =
          w->yuv_in + kCudaYOffEnc + kCudaVP8Scan[block];
      const uint8_t* const ref =
          w->yuv_p + kCudaVP8I16ModeOffsets[mode] + kCudaVP8Scan[block];
      CudaFTransform(src, ref, w->i16_tmp[mode][block]);
    }
    CudaFTransformWHT(w->i16_tmp[mode][0], w->i16_dc[mode]);
    non_zero |=
        (uint32_t)CudaQuantizeBlockWHT(w->i16_dc[mode],
                                       w->rd.y_dc_levels, &dqm->y2)
        << 24;
    for (int by = 0; by < 4; ++by) {
      for (int bx = 0; bx < 4; ++bx) {
        const int block = bx + by * 4;
        const int ctx = context.top_nz[bx] + context.left_nz[by];
        int16_t* const transformed = w->i16_tmp[mode][block];
        transformed[0] = 0;
        const int nz = TrellisQuantizeBlockDev(
            costs, transformed, w->rd.y_ac_levels[block], ctx, 0, &dqm->y1,
            dqm->lambda_trellis_i16);
        context.top_nz[bx] = context.left_nz[by] = nz;
        non_zero |= (uint32_t)nz << block;
        w->rd.y_ac_levels[block][0] = 0;
      }
    }
    CudaTransformWHT(w->i16_dc[mode], w->i16_tmp[mode][0]);
    for (int block = 0; block < 16; ++block) {
      const uint8_t* const ref =
          w->yuv_p + kCudaVP8I16ModeOffsets[mode] + kCudaVP8Scan[block];
      CudaITransformOne(ref, w->i16_tmp[mode][block],
                        w->yuv_out + kCudaYOffEnc + kCudaVP8Scan[block]);
    }
  } else {
    int block = 0;
    StartI4Boundary(w);
    do {
      const int mode = w->rd.modes_i4[block];
      const int bx = block & 3;
      const int by = block >> 2;
      const int ctx = context.top_nz[bx] + context.left_nz[by];
      const uint8_t* const src =
          w->yuv_in + kCudaYOffEnc + kCudaVP8Scan[block];
      uint8_t* const dst =
          w->yuv_out + kCudaYOffEnc + kCudaVP8Scan[block];
      CudaIntra4PredMode(w->yuv_p,
                         w->i4_boundary + kTopLeftI4[block], mode);
      const uint8_t* const ref = w->yuv_p + kCudaVP8I4ModeOffsets[mode];
      CudaFTransform(src, ref, w->i4_tmp[mode]);
      const int nz = TrellisQuantizeBlockDev(
          costs, w->i4_tmp[mode], w->rd.y_ac_levels[block], ctx, 3,
          &dqm->y1, dqm->lambda_trellis_i4);
      non_zero |= (uint32_t)nz << block;
      CudaITransformOne(ref, w->i4_tmp[mode], dst);
    } while (RotateI4(w, &block, w->yuv_out + kCudaYOffEnc));
  }

  {
    const int mode = w->rd.mode_uv;
    int8_t discarded_derr[2][3];
    for (int block = 0; block < 8; ++block) {
      const uint8_t* const src =
          w->yuv_in + kCudaUOffEnc + kCudaVP8ScanUV[block];
      const uint8_t* const ref =
          w->yuv_p + kCudaVP8UVModeOffsets[mode] + kCudaVP8ScanUV[block];
      CudaFTransform(src, ref, w->uv_tmp[mode][block]);
    }
    if (p->use_error_diffusion) {
      int8_t top_derr[2][2];
      int8_t left_derr[2][2];
      // The CPU stores the basic-search diffusion errors before running the
      // selected-mode trellis pass. CorrectDCValues therefore reads the
      // just-stored current errors, not the macroblock's original incoming
      // errors. Rebuild those top/left values exactly and deliberately retain
      // w->rd.derr from the basic selected UV mode.
      for (int ch = 0; ch < 2; ++ch) {
        const int8_t left1 = (int8_t)(3 * w->rd.derr[ch][2] >> 2);
        left_derr[ch][0] = w->rd.derr[ch][0];
        left_derr[ch][1] = left1;
        top_derr[ch][0] = w->rd.derr[ch][1];
        top_derr[ch][1] = (int8_t)(w->rd.derr[ch][2] - left1);
      }
      CorrectDCValuesDev(top_derr, left_derr, &dqm->uv,
                         w->uv_tmp[mode], discarded_derr);
    }
    // DO_TRELLIS_UV is disabled in quant_enc.c. Method 5 re-runs the selected
    // chroma mode with the ordinary quantizer after luma trellis.
    for (int block = 0; block < 8; ++block) {
      const int nz = CudaQuantizeBlock(w->uv_tmp[mode][block],
                                       w->rd.uv_levels[block], &dqm->uv);
      non_zero |= (uint32_t)nz << (16 + block);
    }
    for (int block = 0; block < 8; ++block) {
      const uint8_t* const ref =
          w->yuv_p + kCudaVP8UVModeOffsets[mode] + kCudaVP8ScanUV[block];
      CudaITransformOne(ref, w->uv_tmp[mode][block],
                        w->yuv_out + kCudaUOffEnc + kCudaVP8ScanUV[block]);
    }
  }
  w->rd.nz = non_zero;
}

// ---------------------------------------------------------------------------
// The per-macroblock decision (thread 0 orchestrates; all threads help with
// the numeric phases; __syncthreads separates the phases).

__global__ void __launch_bounds__(kDecimateThreads) DecimateKernel(
    DeviceView v, DecimateKernelParams p, uint8_t* left_nz8) {
  __shared__ MBWork w;
  __shared__ unsigned long long ph_ts[8];
  const int y = (int)(p.y_min + blockIdx.x);
  const int x = (int)p.diagonal - 2 * y;
  const int mb_index = y * (int)p.mb_w + x;
  const int tid = (int)threadIdx.x;
  // A shared-memory copy of these tables measured neutral (the walks are
  // dependency-bound and the tables stay L1-resident), so the cache points
  // at the global tables directly.
  const CostCache cc = {v.level_costs, v.coeff_probas,
                        v.tables->entropy_cost, v.tables->level_fixed_costs};
  // DeviceResult is exported byte-for-byte. Initialize named padding and
  // fields that may be unused when the I4 search aborts so repeated requests
  // cannot expose stale shared memory or produce nondeterministic bytes.
  {
    uint8_t* const rd_bytes = (uint8_t*)&w.rd;
    for (int i = tid; i < (int)sizeof(w.rd);
         i += (int)blockDim.x) {
      rd_bytes[i] = 0;
    }
  }
#define PHASE_TS(k) \
  do { \
    if (v.phase_cycles != nullptr && tid == 0) ph_ts[k] = clock64(); \
  } while (0)
  PHASE_TS(0);
  const DeviceSegment* const dqm = &v.segment_params[v.segments[mb_index]];
  const int tlambda = dqm->tlambda;

  // ---- Phase 0: import, borders, predictions (parallel-friendly setup).
  ImportMBParallel(&v, &p, x, y, &w, tid, (int)blockDim.x);
  if (tid == 0) {
    BuildBorders(&v, &p, x, y, &w);
    w.pred_dc[0] = PredictionDC((x > 0) ? w.y_left + 1 : nullptr,
                                (y > 0) ? w.y_top : nullptr, 16, 16, 5);
    w.pred_dc[1] = PredictionDC((x > 0) ? w.uv_left + 1 : nullptr,
                                (y > 0) ? w.uv_top : nullptr, 8, 8, 4);
    w.pred_dc[2] = PredictionDC((x > 0) ? w.uv_left + 17 : nullptr,
                                (y > 0) ? w.uv_top + 8 : nullptr, 8, 8, 4);
    // Incoming non-zero context; left_nz[8] is carried separately.
    NzToBytes(LoadNzWord(&v, &p, x, y - 1), LoadNzWord(&v, &p, x - 1, y),
              &w.nz_ctx);
    w.nz_ctx.left_nz[8] = (x > 0) ? left_nz8[mb_index - 1] : 0;
  }
  __syncthreads();
  MakeIntraPredsParallel(&w, x, y, tid, (int)blockDim.x);
  __syncthreads();
  PHASE_TS(1);

  // ---- Phase 1 (parallel): intra16 transforms/quantization/reconstruction.
  if (tid < 64) {
    const int mode = tid >> 4;
    const int block = tid & 15;
    const uint8_t* const src = w.yuv_in + kCudaYOffEnc + kCudaVP8Scan[block];
    const uint8_t* const ref =
        w.yuv_p + kCudaVP8I16ModeOffsets[mode] + kCudaVP8Scan[block];
    CudaFTransform(src, ref, w.i16_tmp[mode][block]);
  }
  __syncthreads();
  if (tid < 4) {
    const int mode = tid;
    CudaFTransformWHT(w.i16_tmp[mode][0], w.i16_dc[mode]);
    w.i16_nz[mode] =
        (uint32_t)CudaQuantizeBlockWHT(w.i16_dc[mode],
                                       w.i16_dc_levels[mode], &dqm->y2)
        << 24;
    w.i16_sse[mode] = 0;
    w.i16_sd[mode] = 0;
  }
  __syncthreads();
  if (p.rd_opt_level == kRDTrellisAll && tid < 4) {
    const int mode = tid;
    NzContext context = w.nz_ctx;
    for (int by = 0; by < 4; ++by) {
      for (int bx = 0; bx < 4; ++bx) {
        const int block = bx + by * 4;
        const int ctx = context.top_nz[bx] + context.left_nz[by];
        w.i16_tmp[mode][block][0] = 0;
        w.i16_ac_levels[mode][block][0] = 0;
        const int nz = TrellisQuantizeBlockDev(
            &cc, w.i16_tmp[mode][block], w.i16_ac_levels[mode][block], ctx,
            0, &dqm->y1, dqm->lambda_trellis_i16);
        context.top_nz[bx] = context.left_nz[by] = nz;
        w.i16_nz[mode] |= (uint32_t)nz << block;
      }
    }
  } else if (p.rd_opt_level != kRDTrellisAll && tid < 64) {
    const int mode = tid >> 4;
    const int block = tid & 15;
    int nz_bit;
    w.i16_tmp[mode][block][0] = 0;  // DC coded separately via WHT
    nz_bit = CudaQuantizeBlock(w.i16_tmp[mode][block],
                               w.i16_ac_levels[mode][block], &dqm->y1);
    atomicOr(&w.i16_nz[mode], (uint32_t)nz_bit << block);
  }
  __syncthreads();
  if (tid < 4) {
    // CudaQuantizeBlockWHT rewrote i16_dc in place with the reconstructed
    // coefficients; the inverse WHT scatters them back into the AC blocks.
    CudaTransformWHT(w.i16_dc[tid], w.i16_tmp[tid][0]);
  }
  __syncthreads();
  if (tid < 64) {
    const int mode = tid >> 4;
    const int block = tid & 15;
    const uint8_t* const ref =
        w.yuv_p + kCudaVP8I16ModeOffsets[mode] + kCudaVP8Scan[block];
    CudaITransformOne(ref, w.i16_tmp[mode][block],
                      w.i16_out[mode] + kCudaVP8Scan[block]);
  }
  __syncthreads();
  if (tid < 64) {
    const int mode = tid >> 4;
    const int block = tid & 15;
    const uint8_t* const src = w.yuv_in + kCudaYOffEnc + kCudaVP8Scan[block];
    const uint8_t* const rec = w.i16_out[mode] + kCudaVP8Scan[block];
    atomicAdd((unsigned long long*)&w.i16_sse[mode],
              (unsigned long long)CudaSSE4x4(src, rec));
    if (tlambda) {
      atomicAdd((unsigned long long*)&w.i16_sd[mode],
                (unsigned long long)CudaDisto4x4(src, rec, kWeightY));
    }
  }
  __syncthreads();
  PHASE_TS(2);

  // ---- Phase 2: intra16 selection (PickBestIntra16). The residual-cost
  // walks run one mode per warp; thread 0 then replays the CPU's exact
  // sequential comparison (including the flatness chain) on the precomputed
  // values.
  __shared__ long long i16_R[4];
  __shared__ int i16_levels_flat[4];
  if (tid < 4 * 32) {  // one mode per warp; 16 lanes cooperate per block
    const int mode = tid >> 5;
    const int lane = tid & 31;
    NzContext c = w.nz_ctx;
    int nz_bit;
    long long R = ResidualCostCoop16(&cc, c.top_nz[8] + c.left_nz[8], 0, 1,
                                     w.i16_dc_levels[mode], lane, &nz_bit);
    for (int by = 0; by < 4; ++by) {
      for (int bx = 0; bx < 4; ++bx) {
        const int ctx = c.top_nz[bx] + c.left_nz[by];
        const int16_t* const lv = w.i16_ac_levels[mode][bx + by * 4];
        R += ResidualCostCoop16(&cc, ctx, 1, 0, lv, lane, &nz_bit);
        c.top_nz[bx] = c.left_nz[by] = nz_bit;
      }
    }
    if (lane == 0) {
      i16_R[mode] = R;
      i16_levels_flat[mode] =
          CudaIsFlat(w.i16_ac_levels[mode][0], 16, kFlatnessLimitI16);
    }
  }
  __syncthreads();
  if (tid == 0) {
    int is_flat = CudaIsFlatSource16(w.yuv_in + kCudaYOffEnc);
    long long best_score = 0;
    int best_mode = -1;
    long long best_D = 0, best_SD = 0, best_H = 0, best_R = 0;
    uint32_t best_nz = 0;
    for (int mode = 0; mode < kNumPredModes; ++mode) {
      ModeScore rd_cur;
      rd_cur.nz = w.i16_nz[mode];
      rd_cur.D = w.i16_sse[mode];
      rd_cur.SD = tlambda ? MULT_8B_DEV(tlambda, w.i16_sd[mode]) : 0;
      rd_cur.H = v.tables->fixed_costs_i16[mode];
      rd_cur.R = i16_R[mode];
      if (is_flat) {
        is_flat = i16_levels_flat[mode];
        if (is_flat) {
          rd_cur.D *= 2;
          rd_cur.SD *= 2;
        }
      }
      SetRDScoreDev(dqm->lambda_i16, &rd_cur);
      if (mode == 0 || rd_cur.score < best_score) {
        best_score = rd_cur.score;
        best_mode = mode;
        best_D = rd_cur.D;
        best_SD = rd_cur.SD;
        best_H = rd_cur.H;
        best_R = rd_cur.R;
        best_nz = rd_cur.nz;
      }
    }
    w.rd.mode_i16 = (uint8_t)best_mode;
    w.rd.is_i4 = 0;
    w.rd.nz = best_nz;
    w.rd_D = best_D;
    w.rd_SD = best_SD;
    w.rd_H = best_H;
    w.rd_R = best_R;
    {
      ModeScore final_rd;
      final_rd.D = best_D;
      final_rd.SD = best_SD;
      final_rd.H = best_H;
      final_rd.R = best_R;
      final_rd.nz = best_nz;
      SetRDScoreDev(dqm->lambda_mode, &final_rd);
      w.rd_score = final_rd.score;
    }
    // StoreMaxDelta candidate, evaluated on the intra16 result like the CPU.
    w.rd.store_max_delta = 0;
    w.rd.max_delta = 0;
    if ((best_nz & 0x100ffffu) == 0x1000000u && best_D > dqm->min_disto) {
      const int v0 = CudaAbs(w.i16_dc_levels[best_mode][1]);
      const int v1 = CudaAbs(w.i16_dc_levels[best_mode][2]);
      const int v2 = CudaAbs(w.i16_dc_levels[best_mode][4]);
      int max_v = (v1 > v0) ? v1 : v0;
      max_v = (v2 > max_v) ? v2 : max_v;
      w.rd.store_max_delta = 1;
      w.rd.max_delta = (uint16_t)max_v;
    }
  }
  __syncthreads();
  // Winner copies in parallel (selection above published w.rd.mode_i16).
  {
    const int m = w.rd.mode_i16;
    for (int i = tid; i < 16 * 16; i += (int)blockDim.x) {
      w.rd.y_ac_levels[i >> 4][i & 15] = w.i16_ac_levels[m][i >> 4][i & 15];
    }
    if (tid < 16) w.rd.y_dc_levels[tid] = w.i16_dc_levels[m][tid];
    for (int i = tid; i < 16 * 16; i += (int)blockDim.x) {
      const int r = i >> 4, cx = i & 15;
      w.yuv_out[kCudaYOffEnc + r * kCudaBPS + cx] =
          w.i16_out[m][r * kCudaBPS + cx];
    }
  }
  __syncthreads();
  PHASE_TS(3);

  // ---- Phase 3: intra4 search (PickBestIntra4), sub-blocks in sequence.
  if (p.max_i4_header_bits > 0) {
    __shared__ int i4_abort;
    __shared__ int i4_index;
    __shared__ NzContext i4_ctx;
    __shared__ long long i4_best_score;   // running rd_best.score
    __shared__ long long i4_best_D, i4_best_SD, i4_best_H, i4_best_R;
    __shared__ uint32_t i4_best_nz;
    __shared__ int i4_header_bits;
    __shared__ int16_t i4_best_levels[16][16];
    if (tid == 0) {
      ModeScore rd_best;
      InitScoreDev(&rd_best);
      rd_best.H = 211;
      SetRDScoreDev(dqm->lambda_mode, &rd_best);
      i4_abort = 0;
      i4_index = 0;
      i4_best_score = rd_best.score;
      i4_best_D = 0;
      i4_best_SD = 0;
      i4_best_H = 211;
      i4_best_R = 0;
      i4_best_nz = 0;
      i4_header_bits = 0;
      i4_ctx = w.nz_ctx;  // VP8IteratorStartI4 re-imports the context
      StartI4Boundary(&w);
      // best_blocks accumulate in yuv_out2 luma.
    }
    __syncthreads();
    // Work inside a warp must stay divergence-free (divergent branches
    // serialize), so parallelism beyond the 10 data-parallel mode lanes is
    // spread across warps: predictions round-robin on the warp leaders, the
    // transform chain on warp 0's lanes, and the three independent metrics
    // (residual cost / SSE+flatness / texture distortion) each on their own
    // warp. Block-wide barriers separate the stages.
    for (int step = 0; step < 16; ++step) {
      if (i4_abort) break;  // uniform: last written before a barrier
      {
        const int warp = tid >> 5, lane = tid & 31;
        if (lane == 0 && warp < 4) {
          for (int m = warp; m < kNumBModes; m += 4) {
            CudaIntra4PredMode(w.yuv_p, w.i4_boundary + kTopLeftI4[i4_index],
                               m);
          }
        }
      }
      __syncthreads();
      if (tid < 4 * kNumBModes) {
        const int mode = tid >> 2;
        const int mode_lane = tid & 3;
        const unsigned int warp_mask = __activemask();
        const uint8_t* const src =
            w.yuv_in + kCudaYOffEnc + kCudaVP8Scan[i4_index];
        const uint8_t* const ref = w.yuv_p + kCudaVP8I4ModeOffsets[mode];
        int nz = 0;
        I4FTransformCoop4(src, ref, w.i4_tmp[mode],
                          w.i4_transform_tmp[mode], mode_lane, warp_mask);
        __syncwarp(warp_mask);
        if (p.rd_opt_level == kRDTrellisAll) {
          if (mode_lane == 0) {
            const int bx = i4_index & 3, by = i4_index >> 2;
            const int ctx = i4_ctx.top_nz[bx] + i4_ctx.left_nz[by];
            nz = TrellisQuantizeBlockDev(
                &cc, w.i4_tmp[mode], w.i4_levels[mode], ctx, 3, &dqm->y1,
                dqm->lambda_trellis_i4);
          }
        } else {
          nz = I4QuantizeBlockCoop4(w.i4_tmp[mode], w.i4_levels[mode],
                                    &dqm->y1, mode_lane, warp_mask);
        }
        if (mode_lane == 0) w.i4_nz[mode] = nz;
        __syncwarp(warp_mask);
        I4ITransformCoop4(ref, w.i4_tmp[mode], w.i4_out[mode],
                          w.i4_transform_tmp[mode], mode_lane, warp_mask);
      }
      __syncthreads();
      {
        const int warp = tid >> 5, lane = tid & 31;
        const uint8_t* const src =
            w.yuv_in + kCudaYOffEnc + kCudaVP8Scan[i4_index];
        const int bx = i4_index & 3, by = i4_index >> 2;
        if (warp == 0 && lane < kNumBModes) {
          // Full residual cost precomputed for every mode: the CPU's
          // early-out only skips this computation for modes it rejects
          // anyway, so replaying its comparison order on complete values
          // selects identically. Ten concurrent per-lane serial walks beat
          // sequential cooperative walks here (measured).
          w.i4_rcost[lane] = ResidualCostDev(
              &cc, i4_ctx.top_nz[bx] + i4_ctx.left_nz[by], 0, 3,
              w.i4_levels[lane]);
        } else if (warp == 2 && lane < kNumBModes) {
          w.i4_sse[lane] = CudaSSE4x4(src, w.i4_out[lane]);
          w.i4_flat[lane] =
              (lane > 0) ? CudaIsFlat(w.i4_levels[lane], 1, kFlatnessLimitI4)
                         : 0;
        } else if (warp == 3 && lane < kNumBModes) {
          w.i4_sd[lane] =
              tlambda ? CudaDisto4x4(src, w.i4_out[lane], kWeightY) : 0;
        }
      }
      __syncthreads();
      if (tid == 0) {
        // Mode cost context from neighboring prediction modes.
        const int bx = i4_index & 3, by = i4_index >> 2;
        const int preds_w = 4 * (int)p.mb_w + 1;
        const uint8_t* const preds_base =
            v.preds + (size_t)(4 * y + by) * preds_w + (4 * x + bx);
        const int left_mode = (bx == 0)
                                  ? preds_base[-1]
                                  : w.rd.modes_i4[i4_index - 1];
        const int top_mode = (by == 0)
                                 ? preds_base[-preds_w]
                                 : w.rd.modes_i4[i4_index - 4];
        const uint16_t* const mode_costs =
            v.tables->fixed_costs_i4[top_mode][left_mode];
        ModeScore rd_i4;
        int best_mode = -1;
        InitScoreDev(&rd_i4);
        for (int mode = 0; mode < kNumBModes; ++mode) {
          ModeScore rd_tmp;
          rd_tmp.D = w.i4_sse[mode];
          rd_tmp.SD = tlambda ? MULT_8B_DEV(tlambda, w.i4_sd[mode]) : 0;
          rd_tmp.H = mode_costs[mode];
          rd_tmp.nz = (uint32_t)w.i4_nz[mode] << i4_index;
          rd_tmp.R = w.i4_flat[mode] ? kFlatnessPenalty : 0;
          SetRDScoreDev(dqm->lambda_i4, &rd_tmp);
          if (best_mode >= 0 && rd_tmp.score >= rd_i4.score) continue;
          rd_tmp.R += w.i4_rcost[mode];
          SetRDScoreDev(dqm->lambda_i4, &rd_tmp);
          if (best_mode < 0 || rd_tmp.score < rd_i4.score) {
            CopyScoreDev(&rd_i4, &rd_tmp);
            best_mode = mode;
            for (int k = 0; k < 16; ++k) {
              i4_best_levels[i4_index][k] = w.i4_levels[mode][k];
            }
          }
        }
        SetRDScoreDev(dqm->lambda_mode, &rd_i4);
        i4_best_D += rd_i4.D;
        i4_best_SD += rd_i4.SD;
        i4_best_H += rd_i4.H;
        i4_best_R += rd_i4.R;
        i4_best_nz |= rd_i4.nz;
        i4_best_score += rd_i4.score;
        if (i4_best_score >= w.rd_score) {
          i4_abort = 1;
        } else {
          i4_header_bits += (int)rd_i4.H;
          if (i4_header_bits > p.max_i4_header_bits) {
            i4_abort = 1;
          } else {
            // Commit the chosen block into best_blocks and rotate.
            uint8_t* const dst =
                w.yuv_out2 + kCudaYOffEnc + kCudaVP8Scan[i4_index];
            for (int r = 0; r < 4; ++r) {
              for (int c = 0; c < 4; ++c) {
                dst[r * kCudaBPS + c] = w.i4_out[best_mode][r * kCudaBPS + c];
              }
            }
            w.rd.modes_i4[i4_index] = (uint8_t)best_mode;
            i4_ctx.top_nz[bx] = i4_ctx.left_nz[by] =
                (rd_i4.nz ? 1 : 0);
            RotateI4(&w, &i4_index, w.yuv_out2 + kCudaYOffEnc);
          }
        }
      }
      __syncthreads();
    }
    if (tid == 0 && !i4_abort) {
      // Intra4 wins: adopt its score, levels, and reconstruction.
      w.rd.is_i4 = 1;
      w.rd.nz = i4_best_nz;
      w.rd_D = i4_best_D;
      w.rd_SD = i4_best_SD;
      w.rd_H = i4_best_H;
      w.rd_R = i4_best_R;
      w.rd_score = i4_best_score;
    }
    __syncthreads();
    if (!i4_abort) {
      for (int i = tid; i < 16 * 16; i += (int)blockDim.x) {
        w.rd.y_ac_levels[i >> 4][i & 15] = i4_best_levels[i >> 4][i & 15];
      }
      for (int i = tid; i < 16 * 16; i += (int)blockDim.x) {
        const int r = i >> 4, cx = i & 15;
        w.yuv_out[kCudaYOffEnc + r * kCudaBPS + cx] =
            w.yuv_out2[kCudaYOffEnc + r * kCudaBPS + cx];
      }
    }
    __syncthreads();
  }
  PHASE_TS(4);

  // ---- Phase 4 (parallel): chroma transforms per mode.
  if (tid < 32) {
    const int mode = tid >> 3;
    const int block = tid & 7;
    const uint8_t* const src =
        w.yuv_in + kCudaUOffEnc + kCudaVP8ScanUV[block];
    const uint8_t* const ref =
        w.yuv_p + kCudaVP8UVModeOffsets[mode] + kCudaVP8ScanUV[block];
    CudaFTransform(src, ref, w.uv_tmp[mode][block]);
    if (block == 0) {
      w.uv_nz[mode] = 0;
      w.uv_sse[mode] = 0;
    }
  }
  __syncthreads();
  if (tid < 4 && p.use_error_diffusion) {
    int8_t top_derr[2][2];
    int8_t left_derr[2][2];
    LoadDiffusionErrors(&v, &p, x, y, top_derr, left_derr);
    CorrectDCValuesDev(top_derr, left_derr, &dqm->uv, w.uv_tmp[tid],
                       w.uv_derr[tid]);
  }
  __syncthreads();
  if (tid < 32) {
    const int mode = tid >> 3;
    const int block = tid & 7;
    const int nz_bit = CudaQuantizeBlock(w.uv_tmp[mode][block],
                                         w.uv_levels_all[mode][block],
                                         &dqm->uv);
    atomicOr(&w.uv_nz[mode], (uint32_t)nz_bit << block);
    const uint8_t* const ref =
        w.yuv_p + kCudaVP8UVModeOffsets[mode] + kCudaVP8ScanUV[block];
    // ScanUV offsets are relative to the U origin (columns 0..15 hold U|V).
    CudaITransformOne(ref, w.uv_tmp[mode][block],
                      w.uv_out[mode] + kCudaVP8ScanUV[block]);
  }
  __syncthreads();
  if (tid < 32) {
    const int mode = tid >> 3;
    const int block = tid & 7;
    const uint8_t* const src =
        w.yuv_in + kCudaUOffEnc + kCudaVP8ScanUV[block];
    const uint8_t* const rec = w.uv_out[mode] + kCudaVP8ScanUV[block];
    atomicAdd((unsigned long long*)&w.uv_sse[mode],
              (unsigned long long)CudaSSE4x4(src, rec));
  }
  __syncthreads();
  PHASE_TS(5);

  // ---- Phase 5: chroma selection (PickBestUV). Cost walks run one mode per
  // warp; thread 0 replays the CPU comparison order on precomputed values.
  __shared__ long long uv_R[4];
  if (tid < 4 * 32) {  // one mode per warp; 16 lanes cooperate per block
    const int mode = tid >> 5;
    const int lane = tid & 31;
    NzContext c = w.nz_ctx;
    long long R = 0;
    int nz_bit;
    for (int ch = 0; ch <= 2; ch += 2) {
      for (int by = 0; by < 2; ++by) {
        for (int bx = 0; bx < 2; ++bx) {
          const int b = ch * 2 + bx + by * 2;
          const int ctx = c.top_nz[4 + ch + bx] + c.left_nz[4 + ch + by];
          const int16_t* const lv = w.uv_levels_all[mode][b];
          R += ResidualCostCoop16(&cc, ctx, 0, 2, lv, lane, &nz_bit);
          c.top_nz[4 + ch + bx] = c.left_nz[4 + ch + by] = nz_bit;
        }
      }
    }
    if (lane == 0) {
      if (mode > 0 &&
          CudaIsFlat(w.uv_levels_all[mode][0], 8, kFlatnessLimitUV)) {
        R += kFlatnessPenalty * 8;
      }
      uv_R[mode] = R;
    }
  }
  __syncthreads();
  if (tid == 0) {
    ModeScore rd_best;
    int best_mode = -1;
    InitScoreDev(&rd_best);
    for (int mode = 0; mode < kNumPredModes; ++mode) {
      ModeScore rd_uv;
      rd_uv.nz = w.uv_nz[mode] << 16;
      rd_uv.D = w.uv_sse[mode];
      rd_uv.SD = 0;
      rd_uv.H = v.tables->fixed_costs_uv[mode];
      rd_uv.R = uv_R[mode];
      SetRDScoreDev(dqm->lambda_uv, &rd_uv);
      if (mode == 0 || rd_uv.score < rd_best.score) {
        CopyScoreDev(&rd_best, &rd_uv);
        best_mode = mode;
      }
    }
    w.rd.mode_uv = (uint8_t)best_mode;
    if (p.use_error_diffusion) {
      for (int ch = 0; ch < 2; ++ch) {
        for (int k = 0; k < 3; ++k) {
          w.rd.derr[ch][k] = w.uv_derr[best_mode][ch][k];
        }
      }
    } else {
      for (int ch = 0; ch < 2; ++ch) {
        for (int k = 0; k < 3; ++k) w.rd.derr[ch][k] = 0;
      }
    }
    // AddScore(rd, rd_best) for the totals the token loop consumes.
    w.rd.nz |= rd_best.nz;
    w.rd_D += rd_best.D;
    w.rd_H += rd_best.H;
    w.rd.distortion = (uint32_t)w.rd_D;
    w.rd.header_bits = (uint32_t)w.rd_H;
  }
  __syncthreads();
  // Chroma winner copies in parallel (selection published w.rd.mode_uv).
  {
    const int m = w.rd.mode_uv;
    for (int i = tid; i < 8 * 16; i += (int)blockDim.x) {
      w.rd.uv_levels[i >> 4][i & 15] = w.uv_levels_all[m][i >> 4][i & 15];
    }
    for (int i = tid; i < 8 * 16; i += (int)blockDim.x) {
      const int r = i >> 4, cx = i & 15;
      w.yuv_out[kCudaUOffEnc + r * kCudaBPS + cx] =
          w.uv_out[m][r * kCudaBPS + cx];
    }
  }
  __syncthreads();
  if (tid == 0 && p.rd_opt_level == kRDTrellis) {
    ApplySelectedModeTrellis(&p, &cc, dqm, &w);
  }
  __syncthreads();
  if (tid == 0) {
    // ---- Final: outgoing non-zero word (RecordTokens equivalent),
    // prediction-mode map, and the left-carried intra16-DC context.
    {
      NzContext c = w.nz_ctx;
      if (!w.rd.is_i4) {
        const int dc_nz = BlockNonZero(w.rd.y_dc_levels);
        c.top_nz[8] = c.left_nz[8] = dc_nz;
        left_nz8[mb_index] = (uint8_t)dc_nz;
      } else {
        left_nz8[mb_index] = (uint8_t)w.nz_ctx.left_nz[8];
      }
      for (int by = 0; by < 4; ++by) {
        for (int bx = 0; bx < 4; ++bx) {
          c.top_nz[bx] = c.left_nz[by] =
              BlockNonZero(w.rd.y_ac_levels[bx + by * 4]);
        }
      }
      for (int ch = 0; ch <= 2; ch += 2) {
        for (int by = 0; by < 2; ++by) {
          for (int bx = 0; bx < 2; ++bx) {
            c.top_nz[4 + ch + bx] = c.left_nz[4 + ch + by] =
                BlockNonZero(w.rd.uv_levels[ch * 2 + bx + by * 2]);
          }
        }
      }
      v.nz_words[mb_index] = BytesToNz(&c);
    }
    {
      const int preds_w = 4 * (int)p.mb_w + 1;
      uint8_t* const preds =
          v.preds + (size_t)(4 * y) * preds_w + (size_t)(4 * x);
      for (int r = 0; r < 4; ++r) {
        for (int cx = 0; cx < 4; ++cx) {
          preds[r * preds_w + cx] =
              w.rd.is_i4 ? w.rd.modes_i4[r * 4 + cx] : w.rd.mode_i16;
        }
      }
    }
  }
  __syncthreads();
  // Result struct store in parallel words.
  {
    const uint32_t* const src32 = (const uint32_t*)&w.rd;
    uint32_t* const dst32 = (uint32_t*)&v.results[mb_index];
    for (int i = tid; i < (int)(sizeof(DeviceResult) / 4);
         i += (int)blockDim.x) {
      dst32[i] = src32[i];
    }
  }
  __syncthreads();
  PHASE_TS(6);

  // ---- Phase 6 (parallel): write the reconstruction to the planes.
  for (int i = tid; i < 16 * 16; i += (int)blockDim.x) {
    const int r = i >> 4, cx = i & 15;
    v.recon_y[((size_t)y * 16 + r) * p.recon_y_stride + (size_t)x * 16 + cx] =
        w.yuv_out[kCudaYOffEnc + r * kCudaBPS + cx];
  }
  for (int i = tid; i < 8 * 8; i += (int)blockDim.x) {
    const int r = i >> 3, cx = i & 7;
    v.recon_u[((size_t)y * 8 + r) * p.recon_uv_stride + (size_t)x * 8 + cx] =
        w.yuv_out[kCudaUOffEnc + r * kCudaBPS + cx];
    v.recon_v[((size_t)y * 8 + r) * p.recon_uv_stride + (size_t)x * 8 + cx] =
        w.yuv_out[kCudaUOffEnc + 8 + r * kCudaBPS + cx];
  }
  __syncthreads();
  PHASE_TS(7);
  if (v.phase_cycles != nullptr && tid == 0) {
    for (int k = 0; k < 7; ++k) {
      atomicAdd(&v.phase_cycles[k], ph_ts[k + 1] - ph_ts[k]);
    }
  }
#undef PHASE_TS
}

// ---------------------------------------------------------------------------
// Host adapter. The unit owns its own stream and buffers, independent of the
// main CUDA backend's staging set.

#if defined(_WIN32)
typedef SRWLOCK DecimateMutex;
#define DECIMATE_MUTEX_INITIALIZER SRWLOCK_INIT
static void LockDecimate(DecimateMutex* m) { AcquireSRWLockExclusive(m); }
static void UnlockDecimate(DecimateMutex* m) { ReleaseSRWLockExclusive(m); }
#else
typedef pthread_mutex_t DecimateMutex;
#define DECIMATE_MUTEX_INITIALIZER PTHREAD_MUTEX_INITIALIZER
static void LockDecimate(DecimateMutex* m) { (void)pthread_mutex_lock(m); }
static void UnlockDecimate(DecimateMutex* m) { (void)pthread_mutex_unlock(m); }
#endif

constexpr int kMaxDecimateBands = 8;

struct DecimateState {
  bool available = false;
  bool quarantined = false;
  bool tables_uploaded = false;
  int device = 0;
  cudaStream_t stream = nullptr;
  cudaStream_t copy_stream = nullptr;
  void* device_arena = nullptr;
  size_t arena_capacity = 0;
  StaticCostTables* device_tables = nullptr;
  uint8_t* host_staging = nullptr;
  size_t host_staging_capacity = 0;
  // Streaming pass in flight (BEGIN issued, not all bands collected).
  bool pass_pending = false;
  int pending_band_count = 0;
  int pending_requested_band_count = 0;
  int pending_next_band = 0;
  int pending_rows_per_band = 0;
  int pending_mb_w = 0;
  int pending_mb_h = 0;
  size_t pending_off_results = 0;
  size_t pending_off_recon_y = 0;
  size_t pending_off_recon_u = 0;
  size_t pending_off_recon_v = 0;
  size_t pending_host_off_results = 0;
  size_t pending_host_off_recon_y = 0;
  size_t pending_host_off_recon_u = 0;
  size_t pending_host_off_recon_v = 0;
  size_t pending_recon_y_stride = 0;
  size_t pending_recon_uv_stride = 0;
  cudaEvent_t band_events[kMaxDecimateBands] = {};
  // WEBP_CUDA_DECIMATE_TIMING=1: measure the device wall time of each pass
  // (first diagonal launch to last diagonal completion) and print it.
  bool timing = false;
  int timing_level = 0;  // 2 adds per-phase kernel cycle accounting
  unsigned long long* phase_cycles_dev = nullptr;
  cudaEvent_t timing_begin = nullptr;
  cudaEvent_t timing_end = nullptr;
};

DecimateState g_decimate_state;
DecimateMutex g_decimate_mutex = DECIMATE_MUTEX_INITIALIZER;

bool DecimateStringEqualsIgnoreCase(const char* value, const char* expected) {
  while (*value != '\0' && *expected != '\0') {
    char a = *value++;
    char b = *expected++;
    if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
    if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
    if (a != b) return false;
  }
  return *value == *expected;
}

bool DecimateFlag(const char* name, bool default_value) {
  const char* const value = getenv(name);
  if (value == nullptr || value[0] == '\0') return default_value;
  return strcmp(value, "0") != 0 &&
         !DecimateStringEqualsIgnoreCase(value, "false") &&
         !DecimateStringEqualsIgnoreCase(value, "no");
}

bool DecimateParseSize(const char* name, size_t* parsed_value) {
  const char* const value = getenv(name);
  char* end = nullptr;
  unsigned long long parsed;
  if (value == nullptr || value[0] == '\0' || value[0] == '-') return false;
  errno = 0;
  parsed = strtoull(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' ||
      parsed > (unsigned long long)SIZE_MAX) {
    return false;
  }
  *parsed_value = (size_t)parsed;
  return true;
}

int DecimateEnvironmentDevice(void) {
  const char* const value = getenv("WEBP_CUDA_DEVICE");
  char* end = nullptr;
  long parsed;
  if (value == nullptr || value[0] == '\0') return 0;
  errno = 0;
  parsed = strtol(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' || parsed < 0 ||
      parsed > INT_MAX) {
    return -1;
  }
  return (int)parsed;
}

bool CheckedAddSize(size_t a, size_t b, size_t* result) {
  if (a > SIZE_MAX - b) return false;
  *result = a + b;
  return true;
}

bool CheckedMulSize(size_t a, size_t b, size_t* result) {
  if (a != 0 && b > SIZE_MAX / a) return false;
  *result = a * b;
  return true;
}

bool CheckedAlignUp(size_t value, size_t* result) {
  size_t with_padding;
  if (!CheckedAddSize(value, 255u, &with_padding)) return false;
  *result = with_padding & ~(size_t)255u;
  return true;
}

bool AddAlignedSlice(size_t offset, size_t bytes, size_t* next) {
  size_t aligned;
  return CheckedAlignUp(bytes, &aligned) &&
         CheckedAddSize(offset, aligned, next);
}

void DecimateClearPending(DecimateState* state) {
  state->pass_pending = false;
  state->pending_band_count = 0;
  state->pending_requested_band_count = 0;
  state->pending_next_band = 0;
}

void DecimateReleaseAll(DecimateState* state) {
  if (state->stream != nullptr) (void)cudaStreamSynchronize(state->stream);
  if (state->copy_stream != nullptr) {
    (void)cudaStreamSynchronize(state->copy_stream);
  }
  if (state->device_arena != nullptr) (void)cudaFree(state->device_arena);
  if (state->device_tables != nullptr) (void)cudaFree(state->device_tables);
  if (state->phase_cycles_dev != nullptr) {
    (void)cudaFree(state->phase_cycles_dev);
  }
  if (state->timing_begin != nullptr) {
    (void)cudaEventDestroy(state->timing_begin);
  }
  if (state->timing_end != nullptr) {
    (void)cudaEventDestroy(state->timing_end);
  }
  for (int i = 0; i < kMaxDecimateBands; ++i) {
    if (state->band_events[i] != nullptr) {
      (void)cudaEventDestroy(state->band_events[i]);
    }
  }
  if (state->copy_stream != nullptr) {
    (void)cudaStreamDestroy(state->copy_stream);
  }
  if (state->stream != nullptr) (void)cudaStreamDestroy(state->stream);
  free(state->host_staging);
  *state = DecimateState();
}

bool DecimateInitialize(DecimateState* state) {
  int device_count = 0;
  if (state->available) return true;
  if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count == 0) {
    (void)cudaGetLastError();
    return false;
  }
  state->device = DecimateEnvironmentDevice();
  if (state->device < 0 || state->device >= device_count ||
      cudaSetDevice(state->device) != cudaSuccess) {
    (void)cudaGetLastError();
    state->device = 0;
    return false;
  }
  if (cudaStreamCreateWithFlags(&state->stream, cudaStreamNonBlocking) !=
      cudaSuccess) {
    DecimateReleaseAll(state);
    return false;
  }
  if (cudaStreamCreateWithFlags(&state->copy_stream, cudaStreamNonBlocking) !=
      cudaSuccess) {
    DecimateReleaseAll(state);
    return false;
  }
  for (int i = 0; i < kMaxDecimateBands; ++i) {
    if (cudaEventCreateWithFlags(&state->band_events[i],
                                 cudaEventDisableTiming) != cudaSuccess) {
      DecimateReleaseAll(state);
      return false;
    }
  }
  state->timing = DecimateFlag("WEBP_CUDA_DECIMATE_TIMING", false);
  if (state->timing) {
    const char* const level = getenv("WEBP_CUDA_DECIMATE_TIMING");
    state->timing_level = (level != nullptr) ? atoi(level) : 1;
    if (state->timing_level >= 2 &&
        cudaMalloc((void**)&state->phase_cycles_dev,
                   7 * sizeof(unsigned long long)) != cudaSuccess) {
      state->phase_cycles_dev = nullptr;
      state->timing_level = 1;
      (void)cudaGetLastError();
    }
    if (cudaEventCreate(&state->timing_begin) != cudaSuccess ||
        cudaEventCreate(&state->timing_end) != cudaSuccess) {
      DecimateReleaseAll(state);
      return false;
    }
  }
  state->available = true;
  return true;
}

// The static cost tables never change: upload them once into a persistent
// buffer so per-image calls skip both the copy and the mid-call synchronize.
bool DecimateEnsureTables(DecimateState* state) {
  if (state->tables_uploaded) return true;
  if (state->device_tables == nullptr &&
      cudaMalloc((void**)&state->device_tables, sizeof(StaticCostTables)) !=
          cudaSuccess) {
    (void)cudaGetLastError();
    return false;
  }
  StaticCostTables tables;
  memcpy(tables.entropy_cost, VP8EntropyCost, sizeof(tables.entropy_cost));
  memcpy(tables.level_fixed_costs, VP8LevelFixedCosts,
         sizeof(tables.level_fixed_costs));
  memcpy(tables.fixed_costs_i16, VP8FixedCostsI16,
         sizeof(tables.fixed_costs_i16));
  memcpy(tables.fixed_costs_uv, VP8FixedCostsUV,
         sizeof(tables.fixed_costs_uv));
  memcpy(tables.fixed_costs_i4, VP8FixedCostsI4,
         sizeof(tables.fixed_costs_i4));
  if (cudaMemcpy(state->device_tables, &tables, sizeof(tables),
                 cudaMemcpyHostToDevice) != cudaSuccess) {
    (void)cudaGetLastError();
    (void)cudaFree(state->device_tables);
    state->device_tables = nullptr;
    return false;
  }
  state->tables_uploaded = true;
  return true;
}

bool DecimateEnsureArena(DecimateState* state, size_t bytes) {
  void* replacement = nullptr;
  if (bytes <= state->arena_capacity) return true;
  if (cudaMalloc(&replacement, bytes) != cudaSuccess) {
    (void)cudaGetLastError();
    return false;
  }
  if (state->device_arena != nullptr) (void)cudaFree(state->device_arena);
  state->device_arena = replacement;
  state->arena_capacity = bytes;
  return true;
}

bool DecimateEnsureHostStaging(DecimateState* state, size_t bytes) {
  void* replacement;
  if (bytes <= state->host_staging_capacity) return true;
  replacement = realloc(state->host_staging, bytes);
  if (replacement == nullptr) return false;
  state->host_staging = (uint8_t*)replacement;
  state->host_staging_capacity = bytes;
  return true;
}

struct DecimateLayout {
  size_t mb_count;
  size_t src_y_bytes;
  size_t src_uv_bytes;
  size_t recon_y_stride;
  size_t recon_uv_stride;
  size_t recon_y_bytes;
  size_t recon_uv_bytes;
  size_t preds_w;
  size_t preds_bytes;
  size_t results_bytes;
  size_t off_src_y;
  size_t off_src_u;
  size_t off_src_v;
  size_t off_recon_y;
  size_t off_recon_u;
  size_t off_recon_v;
  size_t off_segments;
  size_t off_seg_params;
  size_t off_level_costs;
  size_t off_probas;
  size_t off_nz;
  size_t off_preds;
  size_t off_left_nz8;
  size_t off_results;
  size_t arena_bytes;
  size_t host_off_results;
  size_t host_off_recon_y;
  size_t host_off_recon_u;
  size_t host_off_recon_v;
  size_t host_bytes;
};

bool BuildDecimateLayout(const WebPAcceleratorDecimateRequest* request,
                         DecimateLayout* layout) {
  const size_t level_cost_bytes =
      4u * 8u * 3u * 68u * sizeof(uint16_t);
  const size_t proba_bytes = 4u * 8u * 3u * 11u;
  size_t uv_height, recon_y_height, recon_uv_height, preds_h;
  size_t next;
  memset(layout, 0, sizeof(*layout));
  if (!CheckedMulSize((size_t)request->mb_w, (size_t)request->mb_h,
                      &layout->mb_count) ||
      !CheckedMulSize((size_t)request->y_stride, (size_t)request->height,
                      &layout->src_y_bytes)) {
    return false;
  }
  uv_height = ((size_t)request->height + 1u) / 2u;
  if (!CheckedMulSize((size_t)request->uv_stride, uv_height,
                      &layout->src_uv_bytes) ||
      !CheckedMulSize((size_t)request->mb_w, 16u,
                      &layout->recon_y_stride) ||
      !CheckedMulSize((size_t)request->mb_w, 8u,
                      &layout->recon_uv_stride) ||
      !CheckedMulSize((size_t)request->mb_h, 16u, &recon_y_height) ||
      !CheckedMulSize((size_t)request->mb_h, 8u, &recon_uv_height) ||
      !CheckedMulSize(layout->recon_y_stride, recon_y_height,
                      &layout->recon_y_bytes) ||
      !CheckedMulSize(layout->recon_uv_stride, recon_uv_height,
                      &layout->recon_uv_bytes) ||
      !CheckedMulSize(layout->mb_count, sizeof(DeviceResult),
                      &layout->results_bytes) ||
      !CheckedMulSize((size_t)request->mb_w, 4u, &layout->preds_w) ||
      !CheckedAddSize(layout->preds_w, 1u, &layout->preds_w) ||
      !CheckedMulSize((size_t)request->mb_h, 4u, &preds_h) ||
      !CheckedAddSize(preds_h, 1u, &preds_h) ||
      !CheckedMulSize(layout->preds_w, preds_h, &layout->preds_bytes)) {
    return false;
  }

  layout->off_src_y = 0;
  if (!AddAlignedSlice(layout->off_src_y, layout->src_y_bytes, &next)) {
    return false;
  }
  layout->off_src_u = next;
  if (!AddAlignedSlice(next, layout->src_uv_bytes, &next)) return false;
  layout->off_src_v = next;
  if (!AddAlignedSlice(next, layout->src_uv_bytes, &next)) return false;
  layout->off_recon_y = next;
  if (!AddAlignedSlice(next, layout->recon_y_bytes, &next)) return false;
  layout->off_recon_u = next;
  if (!AddAlignedSlice(next, layout->recon_uv_bytes, &next)) return false;
  layout->off_recon_v = next;
  if (!AddAlignedSlice(next, layout->recon_uv_bytes, &next)) return false;
  layout->off_segments = next;
  if (!AddAlignedSlice(next, layout->mb_count, &next)) return false;
  layout->off_seg_params = next;
  if (!AddAlignedSlice(next, 4u * sizeof(DeviceSegment), &next)) return false;
  layout->off_level_costs = next;
  if (!AddAlignedSlice(next, level_cost_bytes, &next)) return false;
  layout->off_probas = next;
  if (!AddAlignedSlice(next, proba_bytes, &next)) return false;
  layout->off_nz = next;
  if (!AddAlignedSlice(next, layout->mb_count * sizeof(uint32_t), &next)) {
    return false;
  }
  layout->off_preds = next;
  if (!AddAlignedSlice(next, layout->preds_bytes, &next)) return false;
  layout->off_left_nz8 = next;
  if (!AddAlignedSlice(next, layout->mb_count, &next)) return false;
  layout->off_results = next;
  if (!AddAlignedSlice(next, layout->results_bytes, &layout->arena_bytes)) {
    return false;
  }

  layout->host_off_results = 0;
  if (!CheckedAddSize(layout->host_off_results, layout->results_bytes,
                      &layout->host_off_recon_y) ||
      !CheckedAddSize(layout->host_off_recon_y, layout->recon_y_bytes,
                      &layout->host_off_recon_u) ||
      !CheckedAddSize(layout->host_off_recon_u, layout->recon_uv_bytes,
                      &layout->host_off_recon_v) ||
      !CheckedAddSize(layout->host_off_recon_v, layout->recon_uv_bytes,
                      &layout->host_bytes)) {
    return false;
  }
  return true;
}

bool ValidateDecimateRequest(const WebPAcceleratorDecimateRequest* request,
                             DecimateLayout* layout) {
  size_t expected_mb_w, expected_mb_h;
  size_t uv_width;
  if (request == nullptr || request->y == nullptr || request->u == nullptr ||
      request->v == nullptr || request->segments == nullptr ||
      request->segment_params == nullptr || request->level_costs == nullptr ||
      request->coeff_probas == nullptr || request->results == nullptr ||
      request->recon_y == nullptr || request->recon_u == nullptr ||
      request->recon_v == nullptr || request->width <= 0 ||
      request->height <= 0 || request->mb_w <= 0 || request->mb_h <= 0 ||
      request->phase < WEBP_ACCELERATOR_DECIMATE_WHOLE ||
      request->phase > WEBP_ACCELERATOR_DECIMATE_COLLECT) {
    return false;
  }
  expected_mb_w = ((size_t)request->width - 1u) / 16u + 1u;
  expected_mb_h = ((size_t)request->height - 1u) / 16u + 1u;
  uv_width = ((size_t)request->width + 1u) / 2u;
  if ((size_t)request->mb_w != expected_mb_w ||
      (size_t)request->mb_h != expected_mb_h ||
      request->y_stride < request->width || request->uv_stride <= 0 ||
      (size_t)request->uv_stride < uv_width ||
      request->recon_y_stride <= 0 || request->recon_uv_stride <= 0 ||
      (size_t)request->recon_y_stride < (size_t)request->mb_w * 16u ||
      (size_t)request->recon_uv_stride < (size_t)request->mb_w * 8u ||
      (request->use_error_diffusion != 0 &&
       request->use_error_diffusion != 1)) {
    return false;
  }
  if (request->phase != WEBP_ACCELERATOR_DECIMATE_WHOLE &&
      (request->band_count <= 0 ||
       request->band_count > kMaxDecimateBands)) {
    return false;
  }
  if (request->phase == WEBP_ACCELERATOR_DECIMATE_BEGIN &&
      request->band_index != 0) {
    return false;
  }
  if (!BuildDecimateLayout(request, layout)) return false;
  for (size_t i = 0; i < layout->mb_count; ++i) {
    if (request->segments[i] >= 4u) return false;
  }
  return true;
}

void CommitPlaneRows(uint8_t* destination, size_t destination_stride,
                     const uint8_t* source, size_t source_stride,
                     size_t first_row, size_t row_count) {
  for (size_t row = 0; row < row_count; ++row) {
    memcpy(destination + (first_row + row) * destination_stride,
           source + (first_row + row) * source_stride, source_stride);
  }
}

void DecimateReportTiming(DecimateState* state, int mb_w, int mb_h) {
  if (!state->timing || state->timing_end == nullptr ||
      cudaEventSynchronize(state->timing_end) != cudaSuccess) {
    return;
  }
  float ms = 0.f;
  if (cudaEventElapsedTime(&ms, state->timing_begin, state->timing_end) ==
      cudaSuccess) {
    fprintf(stderr, "decimate GPU wall: %.2f ms (%dx%d MBs)\n", ms, mb_w,
            mb_h);
  }
  if (state->phase_cycles_dev != nullptr) {
    unsigned long long cycles[7] = {0};
    if (cudaMemcpy(cycles, state->phase_cycles_dev, sizeof(cycles),
                   cudaMemcpyDeviceToHost) == cudaSuccess) {
      static const char* const kPhaseNames[7] = {
          "import", "i16-num", "i16-sel", "i4", "uv-num", "uv-sel",
          "recon"};
      unsigned long long total = 0;
      for (int k = 0; k < 7; ++k) total += cycles[k];
      fprintf(stderr, "decimate phases (%% of block cycles):");
      for (int k = 0; k < 7; ++k) {
        fprintf(stderr, " %s %.1f%%", kPhaseNames[k],
                total ? 100.0 * (double)cycles[k] / (double)total : 0.0);
      }
      fprintf(stderr, "\n");
    }
  }
}

}  // namespace

static_assert(sizeof(DeviceResult) == sizeof(WebPAcceleratorDecimateResult),
              "device result must mirror the ABI struct");
static_assert(sizeof(DeviceSegment) ==
                  sizeof(WebPAcceleratorDecimateSegment),
              "device segment must mirror the ABI struct");

extern "C" WebPAcceleratorResult WebPCUDALossyDecimate(
    void* context, const WebPAcceleratorDecimateRequest* request) {
  DecimateLayout layout;
  (void)context;
  if (!DecimateFlag("WEBP_CUDA", true) ||
      !DecimateFlag("WEBP_CUDA_LOSSY_DECIMATE", true)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (!ValidateDecimateRequest(request, &layout)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  if (request->rd_opt_level < (int)kRDBasic ||
      request->rd_opt_level > (int)kRDTrellisAll) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  const size_t mb_count = layout.mb_count;
  if (request->phase == WEBP_ACCELERATOR_DECIMATE_COLLECT) {
    // Wait for one band's completion event, then copy its rows out on the
    // dedicated copy stream so later diagonals keep running.
    WebPAcceleratorResult collect_result = WEBP_ACCELERATOR_ERROR;
    LockDecimate(&g_decimate_mutex);
    DecimateState* const state = &g_decimate_state;
    do {
      if (!state->pass_pending || state->pending_mb_w != request->mb_w ||
          state->pending_mb_h != request->mb_h ||
          request->band_count != state->pending_requested_band_count ||
          request->band_index != state->pending_next_band ||
          request->band_index < 0 ||
          request->band_index >= state->pending_band_count) {
        break;
      }
      if (cudaSetDevice(state->device) != cudaSuccess) {
        state->quarantined = true;
        break;
      }
      const int band = request->band_index;
      {
        // Test hook: WEBP_CUDA_DECIMATE_FAIL_COLLECT=<band> fails that
        // band's collection to exercise the encoder's mid-image CPU
        // fallback. The pass is drained so the next image accelerates.
        const char* const fail_env = getenv("WEBP_CUDA_DECIMATE_FAIL_COLLECT");
        if (fail_env != nullptr && fail_env[0] != '\0' &&
            atoi(fail_env) == band) {
          (void)cudaStreamSynchronize(state->stream);
          (void)cudaStreamSynchronize(state->copy_stream);
          DecimateClearPending(state);
          break;
        }
      }
      const int row_start = band * state->pending_rows_per_band;
      const int row_end_raw = row_start + state->pending_rows_per_band;
      const int row_end =
          row_end_raw < request->mb_h ? row_end_raw : request->mb_h;
      const size_t mb_start = (size_t)row_start * request->mb_w;
      const size_t mb_end = (size_t)row_end * request->mb_w;
      const size_t y_first_row = (size_t)row_start * 16u;
      const size_t y_row_count = (size_t)(row_end - row_start) * 16u;
      const size_t uv_first_row = (size_t)row_start * 8u;
      const size_t uv_row_count = (size_t)(row_end - row_start) * 8u;
      uint8_t* const arena = (uint8_t*)state->device_arena;
      uint8_t* const staging = state->host_staging;
      const char* const fail_download =
          getenv("WEBP_CUDA_DECIMATE_FAIL_DOWNLOAD");
      const int injected_step =
          (fail_download != nullptr && fail_download[0] != '\0')
              ? atoi(fail_download)
              : -1;
      int copy_step = 0;
      bool injected_failure = false;
      cudaError_t error = cudaStreamWaitEvent(
          state->copy_stream, state->band_events[band], 0);
      if (error == cudaSuccess) {
        error = cudaMemcpyAsync(
            staging + state->pending_host_off_results +
                mb_start * sizeof(DeviceResult),
            (const DeviceResult*)(arena + state->pending_off_results) +
                mb_start,
            (mb_end - mb_start) * sizeof(DeviceResult),
            cudaMemcpyDeviceToHost, state->copy_stream);
        if (error == cudaSuccess && injected_step == copy_step++) {
          error = cudaErrorUnknown;
          injected_failure = true;
        }
      }
      if (error == cudaSuccess) {
        error = cudaMemcpyAsync(
            staging + state->pending_host_off_recon_y +
                y_first_row * state->pending_recon_y_stride,
            arena + state->pending_off_recon_y +
                y_first_row * state->pending_recon_y_stride,
            y_row_count * state->pending_recon_y_stride,
            cudaMemcpyDeviceToHost, state->copy_stream);
        if (error == cudaSuccess && injected_step == copy_step++) {
          error = cudaErrorUnknown;
          injected_failure = true;
        }
      }
      if (error == cudaSuccess) {
        error = cudaMemcpyAsync(
            staging + state->pending_host_off_recon_u +
                uv_first_row * state->pending_recon_uv_stride,
            arena + state->pending_off_recon_u +
                uv_first_row * state->pending_recon_uv_stride,
            uv_row_count * state->pending_recon_uv_stride,
            cudaMemcpyDeviceToHost, state->copy_stream);
        if (error == cudaSuccess && injected_step == copy_step++) {
          error = cudaErrorUnknown;
          injected_failure = true;
        }
      }
      if (error == cudaSuccess) {
        error = cudaMemcpyAsync(
            staging + state->pending_host_off_recon_v +
                uv_first_row * state->pending_recon_uv_stride,
            arena + state->pending_off_recon_v +
                uv_first_row * state->pending_recon_uv_stride,
            uv_row_count * state->pending_recon_uv_stride,
            cudaMemcpyDeviceToHost, state->copy_stream);
        if (error == cudaSuccess && injected_step == copy_step++) {
          error = cudaErrorUnknown;
          injected_failure = true;
        }
      }
      if (error == cudaSuccess) {
        error = cudaStreamSynchronize(state->copy_stream);
      }
      if (error != cudaSuccess) {
        (void)cudaStreamSynchronize(state->stream);
        (void)cudaStreamSynchronize(state->copy_stream);
        DecimateClearPending(state);
        if (!injected_failure) state->quarantined = true;
        break;
      }
      memcpy(request->results + mb_start,
             staging + state->pending_host_off_results +
                 mb_start * sizeof(DeviceResult),
             (mb_end - mb_start) * sizeof(DeviceResult));
      CommitPlaneRows(request->recon_y, (size_t)request->recon_y_stride,
                      staging + state->pending_host_off_recon_y,
                      state->pending_recon_y_stride, y_first_row,
                      y_row_count);
      CommitPlaneRows(request->recon_u, (size_t)request->recon_uv_stride,
                      staging + state->pending_host_off_recon_u,
                      state->pending_recon_uv_stride, uv_first_row,
                      uv_row_count);
      CommitPlaneRows(request->recon_v, (size_t)request->recon_uv_stride,
                      staging + state->pending_host_off_recon_v,
                      state->pending_recon_uv_stride, uv_first_row,
                      uv_row_count);
      if (band == state->pending_band_count - 1) {
        DecimateReportTiming(state, state->pending_mb_w, state->pending_mb_h);
        DecimateClearPending(state);
      } else {
        ++state->pending_next_band;
      }
      collect_result = WEBP_ACCELERATOR_SUCCESS;
    } while (0);
    UnlockDecimate(&g_decimate_mutex);
    return collect_result;
  }
  {
    // The context-creation cost is only worth paying for large images. Once a
    // context exists (the unit ran before, or the process committed to CUDA
    // and the prewarm created one), Turing still needs enough work to cover
    // its higher per-dispatch overhead. These conservative cutoffs are the
    // first repeatable wins across both the RTX 2080 SUPER and the faster
    // hardware used for the original implementation.
    const char* const backend = getenv("WEBP_ACCELERATOR");
    const bool context_warm =
        g_decimate_state.available ||
        (backend != nullptr && strcmp(backend, "cuda") == 0);
    const char* const min_mbs = getenv("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS");
    size_t minimum = context_warm ? 784u : 12544u;
    if (min_mbs != nullptr && min_mbs[0] != '\0' &&
        !DecimateParseSize("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS", &minimum)) {
      if (DecimateFlag("WEBP_CUDA_VERBOSE", false)) {
        fprintf(stderr,
                "WebP-CUDA: invalid WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS\n");
      }
      return WEBP_ACCELERATOR_ERROR;
    }
    if (mb_count < minimum) return WEBP_ACCELERATOR_NOT_RUN;
  }

  WebPAcceleratorResult result = WEBP_ACCELERATOR_NOT_RUN;
  const int streaming = (request->phase == WEBP_ACCELERATOR_DECIMATE_BEGIN);
  const int requested_band_count = streaming ? request->band_count : 1;
  LockDecimate(&g_decimate_mutex);
  DecimateState* const state = &g_decimate_state;
  do {
    if (state->quarantined || !DecimateInitialize(state)) break;
    if (cudaSetDevice(state->device) != cudaSuccess) {
      state->quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
      break;
    }
    if (state->pass_pending) {
      // Abandon an uncollected pass: drain the device before reusing arena.
      cudaError_t drain_error = cudaStreamSynchronize(state->stream);
      if (drain_error == cudaSuccess) {
        drain_error = cudaStreamSynchronize(state->copy_stream);
      }
      if (drain_error != cudaSuccess) {
        state->quarantined = true;
        result = WEBP_ACCELERATOR_ERROR;
        break;
      }
      DecimateClearPending(state);
    }
    if (!DecimateEnsureTables(state)) break;
    const size_t src_y_bytes = layout.src_y_bytes;
    const size_t src_uv_bytes = layout.src_uv_bytes;
    const size_t recon_y_bytes = layout.recon_y_bytes;
    const size_t recon_uv_bytes = layout.recon_uv_bytes;
    const size_t preds_w = layout.preds_w;
    const size_t preds_bytes = layout.preds_bytes;
    const size_t results_bytes = layout.results_bytes;
    const size_t level_cost_bytes = 4u * 8u * 3u * 68u * sizeof(uint16_t);
    const size_t proba_bytes = 4u * 8u * 3u * 11u;
    const size_t off_src_y = layout.off_src_y;
    const size_t off_src_u = layout.off_src_u;
    const size_t off_src_v = layout.off_src_v;
    const size_t off_recon_y = layout.off_recon_y;
    const size_t off_recon_u = layout.off_recon_u;
    const size_t off_recon_v = layout.off_recon_v;
    const size_t off_segments = layout.off_segments;
    const size_t off_seg_params = layout.off_seg_params;
    const size_t off_level_costs = layout.off_level_costs;
    const size_t off_probas = layout.off_probas;
    const size_t off_nz = layout.off_nz;
    const size_t off_preds = layout.off_preds;
    const size_t off_left_nz8 = layout.off_left_nz8;
    const size_t off_results = layout.off_results;
    if (!DecimateEnsureArena(state, layout.arena_bytes) ||
        !DecimateEnsureHostStaging(state, layout.host_bytes)) {
      break;
    }
    uint8_t* const arena = (uint8_t*)state->device_arena;
    cudaError_t error = cudaSuccess;
#define UPLOAD(offset, ptr, bytes)                                          \
  if (error == cudaSuccess) {                                               \
    error = cudaMemcpyAsync(arena + (offset), (ptr), (bytes),               \
                            cudaMemcpyHostToDevice, state->stream);         \
  }
    UPLOAD(off_src_y, request->y, src_y_bytes);
    UPLOAD(off_src_u, request->u, src_uv_bytes);
    UPLOAD(off_src_v, request->v, src_uv_bytes);
    UPLOAD(off_segments, request->segments, mb_count);
    UPLOAD(off_seg_params, request->segment_params, 4 * sizeof(DeviceSegment));
    UPLOAD(off_level_costs, request->level_costs, level_cost_bytes);
    UPLOAD(off_probas, request->coeff_probas, proba_bytes);
#undef UPLOAD
    if (error == cudaSuccess) {
      error = cudaMemsetAsync(arena + off_preds, 0, preds_bytes,
                              state->stream);
    }
    if (error == cudaSuccess) {
      error = cudaMemsetAsync(arena + off_nz, 0, mb_count * sizeof(uint32_t),
                              state->stream);
    }
    if (error == cudaSuccess) {
      error = cudaMemsetAsync(arena + off_left_nz8, 0, mb_count,
                              state->stream);
    }
    if (error != cudaSuccess) {
      (void)cudaStreamSynchronize(state->stream);
      state->quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
      break;
    }

    DeviceView view;
    view.src_y = arena + off_src_y;
    view.src_u = arena + off_src_u;
    view.src_v = arena + off_src_v;
    view.recon_y = arena + off_recon_y;
    view.recon_u = arena + off_recon_u;
    view.recon_v = arena + off_recon_v;
    view.segments = arena + off_segments;
    view.segment_params = (const DeviceSegment*)(arena + off_seg_params);
    view.level_costs = (const uint16_t*)(arena + off_level_costs);
    view.coeff_probas = arena + off_probas;
    view.tables = state->device_tables;
    view.nz_words = (uint32_t*)(arena + off_nz);
    // The preds pointer addresses the interior origin like the encoder's.
    view.preds = arena + off_preds + preds_w + 1;
    view.top_derr = nullptr;
    view.results = (DeviceResult*)(arena + off_results);
    view.phase_cycles = state->phase_cycles_dev;
    if (state->phase_cycles_dev != nullptr) {
      (void)cudaMemsetAsync(state->phase_cycles_dev, 0,
                            7 * sizeof(unsigned long long), state->stream);
    }

    DecimateKernelParams params;
    params.width = (uint32_t)request->width;
    params.height = (uint32_t)request->height;
    params.mb_w = (uint32_t)request->mb_w;
    params.mb_h = (uint32_t)request->mb_h;
    params.y_stride = (uint32_t)request->y_stride;
    params.uv_stride = (uint32_t)request->uv_stride;
    params.recon_y_stride = (uint32_t)layout.recon_y_stride;
    params.recon_uv_stride = (uint32_t)layout.recon_uv_stride;
    params.max_i4_header_bits = request->max_i4_header_bits;
    params.use_error_diffusion = (uint32_t)request->use_error_diffusion;
    params.rd_opt_level = (uint32_t)request->rd_opt_level;

    (void)cudaGetLastError();
    const int last_diagonal =
        (request->mb_w - 1) + 2 * (request->mb_h - 1);
    const int rows_per_band =
        (request->mb_h + requested_band_count - 1) / requested_band_count;
    const int effective_band_count =
        (request->mb_h + rows_per_band - 1) / rows_per_band;
    if (state->timing) {
      (void)cudaEventRecord(state->timing_begin, state->stream);
    }
    for (int d = 0; d <= last_diagonal && error == cudaSuccess; ++d) {
      const int y_min =
          (d > request->mb_w - 1) ? (d - (request->mb_w - 1) + 1) / 2 : 0;
      const int y_max = (d / 2 < request->mb_h - 1) ? d / 2
                                                    : request->mb_h - 1;
      const int count = y_max - y_min + 1;
      if (count <= 0) continue;
      params.diagonal = (uint32_t)d;
      params.y_min = (uint32_t)y_min;
      DecimateKernel<<<count, kDecimateThreads, 0, state->stream>>>(
          view, params, arena + off_left_nz8);
      error = cudaGetLastError();
      if (streaming && error == cudaSuccess) {
        // A band of macroblock rows is complete once the diagonal reaching
        // its last row's rightmost block has run.
        for (int band = 0; band < effective_band_count; ++band) {
          const int end_raw = (band + 1) * rows_per_band;
          const int end_row =
              end_raw < request->mb_h ? end_raw : request->mb_h;
          if (d == (request->mb_w - 1) + 2 * (end_row - 1)) {
            error = cudaEventRecord(state->band_events[band], state->stream);
          }
        }
      }
    }
    if (state->timing && error == cudaSuccess) {
      error = cudaEventRecord(state->timing_end, state->stream);
    }
    if (streaming && error == cudaSuccess) {
      state->pass_pending = true;
      state->pending_band_count = effective_band_count;
      state->pending_requested_band_count = requested_band_count;
      state->pending_next_band = 0;
      state->pending_rows_per_band = rows_per_band;
      state->pending_mb_w = request->mb_w;
      state->pending_mb_h = request->mb_h;
      state->pending_off_results = off_results;
      state->pending_off_recon_y = off_recon_y;
      state->pending_off_recon_u = off_recon_u;
      state->pending_off_recon_v = off_recon_v;
      state->pending_host_off_results = layout.host_off_results;
      state->pending_host_off_recon_y = layout.host_off_recon_y;
      state->pending_host_off_recon_u = layout.host_off_recon_u;
      state->pending_host_off_recon_v = layout.host_off_recon_v;
      state->pending_recon_y_stride = layout.recon_y_stride;
      state->pending_recon_uv_stride = layout.recon_uv_stride;
      result = WEBP_ACCELERATOR_SUCCESS;
      break;
    }
    const char* const fail_download =
        getenv("WEBP_CUDA_DECIMATE_FAIL_DOWNLOAD");
    const int injected_step =
        (fail_download != nullptr && fail_download[0] != '\0')
            ? atoi(fail_download)
            : -1;
    int copy_step = 0;
    bool injected_failure = false;
#define DOWNLOAD_STAGED(host_offset, device_ptr, bytes)                    \
  if (error == cudaSuccess) {                                               \
    error = cudaMemcpyAsync(state->host_staging + (host_offset),            \
                            (device_ptr), (bytes), cudaMemcpyDeviceToHost,   \
                            state->stream);                                 \
    if (error == cudaSuccess && injected_step == copy_step++) {             \
      error = cudaErrorUnknown;                                             \
      injected_failure = true;                                              \
    }                                                                       \
  }
    DOWNLOAD_STAGED(layout.host_off_results, view.results, results_bytes);
    DOWNLOAD_STAGED(layout.host_off_recon_y, view.recon_y, recon_y_bytes);
    DOWNLOAD_STAGED(layout.host_off_recon_u, view.recon_u, recon_uv_bytes);
    DOWNLOAD_STAGED(layout.host_off_recon_v, view.recon_v, recon_uv_bytes);
#undef DOWNLOAD_STAGED
    if (error == cudaSuccess) error = cudaStreamSynchronize(state->stream);
    if (error != cudaSuccess) {
      (void)cudaStreamSynchronize(state->stream);
      if (DecimateFlag("WEBP_CUDA_VERBOSE", false)) {
        fprintf(stderr, "WebP-CUDA: lossy decimate failed: %s\n",
                cudaGetErrorString(error));
      }
      if (!injected_failure) state->quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
      break;
    }
    memcpy(request->results,
           state->host_staging + layout.host_off_results, results_bytes);
    CommitPlaneRows(request->recon_y, (size_t)request->recon_y_stride,
                    state->host_staging + layout.host_off_recon_y,
                    layout.recon_y_stride, 0,
                    recon_y_bytes / layout.recon_y_stride);
    CommitPlaneRows(request->recon_u, (size_t)request->recon_uv_stride,
                    state->host_staging + layout.host_off_recon_u,
                    layout.recon_uv_stride, 0,
                    recon_uv_bytes / layout.recon_uv_stride);
    CommitPlaneRows(request->recon_v, (size_t)request->recon_uv_stride,
                    state->host_staging + layout.host_off_recon_v,
                    layout.recon_uv_stride, 0,
                    recon_uv_bytes / layout.recon_uv_stride);
    DecimateReportTiming(state, request->mb_w, request->mb_h);
    if (DecimateFlag("WEBP_CUDA_VERBOSE", false)) {
      fprintf(stderr,
              "WebP-CUDA: lossy decimate of %dx%d (%zu MBs, %d diagonals)\n",
              request->width, request->height, mb_count, last_diagonal + 1);
    }
    result = WEBP_ACCELERATOR_SUCCESS;
  } while (0);
  UnlockDecimate(&g_decimate_mutex);
  return result;
}

// Called from the CUDA backend's process-start prewarm thread: creating the
// stream and uploading the static tables here overlaps with image decode.
extern "C" void WebPCUDALossyDecimatePrewarm(void) {
  LockDecimate(&g_decimate_mutex);
  if (!g_decimate_state.quarantined &&
      DecimateInitialize(&g_decimate_state) &&
      cudaSetDevice(g_decimate_state.device) == cudaSuccess) {
    (void)DecimateEnsureTables(&g_decimate_state);
  }
  UnlockDecimate(&g_decimate_mutex);
}

extern "C" WebPAcceleratorResult WebPCUDALossyDecimateFlush(void) {
  WebPAcceleratorResult result = WEBP_ACCELERATOR_NOT_RUN;
  LockDecimate(&g_decimate_mutex);
  if (g_decimate_state.available && !g_decimate_state.quarantined) {
    cudaError_t error = cudaSetDevice(g_decimate_state.device);
    if (error == cudaSuccess && g_decimate_state.stream != nullptr) {
      error = cudaStreamSynchronize(g_decimate_state.stream);
    }
    if (error == cudaSuccess && g_decimate_state.copy_stream != nullptr) {
      error = cudaStreamSynchronize(g_decimate_state.copy_stream);
    }
    if (error == cudaSuccess) {
      result = WEBP_ACCELERATOR_SUCCESS;
    } else {
      g_decimate_state.quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
    }
  }
  UnlockDecimate(&g_decimate_mutex);
  return result;
}

extern "C" void WebPCUDALossyDecimateEndEncode(void) {
  LockDecimate(&g_decimate_mutex);
  if (g_decimate_state.available) {
    cudaError_t error = cudaSetDevice(g_decimate_state.device);
    if (error == cudaSuccess && g_decimate_state.stream != nullptr) {
      error = cudaStreamSynchronize(g_decimate_state.stream);
    }
    if (error == cudaSuccess && g_decimate_state.copy_stream != nullptr) {
      error = cudaStreamSynchronize(g_decimate_state.copy_stream);
    }
    if (error != cudaSuccess) {
      g_decimate_state.quarantined = true;
    } else {
      DecimateClearPending(&g_decimate_state);
    }
  } else {
    DecimateClearPending(&g_decimate_state);
  }
  UnlockDecimate(&g_decimate_mutex);
}

extern "C" void WebPCUDALossyDecimateTrim(void) {
  LockDecimate(&g_decimate_mutex);
  if (g_decimate_state.available) {
    if (cudaSetDevice(g_decimate_state.device) == cudaSuccess) {
      DecimateReleaseAll(&g_decimate_state);
    } else {
      g_decimate_state.quarantined = true;
    }
  } else {
    DecimateReleaseAll(&g_decimate_state);
  }
  UnlockDecimate(&g_decimate_mutex);
}

#endif  // WEBP_CUDA_ENABLE_LOSSY_DECIMATE
