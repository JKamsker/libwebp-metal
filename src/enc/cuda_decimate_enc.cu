// Copyright 2026
//
// Whole-pass CUDA port of the VP8 lossy macroblock decimation (VP8Decimate at
// RD_OPT_BASIC): intra16/intra4/chroma mode search, quantization, and
// reconstruction. Macroblocks are processed in skewed anti-diagonal order
// (t = x + 2y) so every block sees its left, top, and top-right neighbors'
// reconstruction, non-zero context, prediction modes, and diffusion errors
// exactly as the CPU raster scan does. Cost tables are fixed for the whole
// pass (the fork's token loop no longer refreshes them mid-pass), and all
// arithmetic is integer, so the output decisions are bit-exact with the CPU
// path and the final bitstream is byte-identical.

#include "src/enc/cuda_enc.h"

#if defined(WEBP_CUDA_ENABLE_LOSSY_DECIMATE)

#include <cuda_runtime.h>

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
};

// ---------------------------------------------------------------------------
// Cost model (bit-exact ports from cost_enc.c / dsp/cost.c).

__device__ __forceinline__ int BitCostDev(const StaticCostTables* t, int bit,
                                          uint8_t proba) {
  return !bit ? t->entropy_cost[proba] : t->entropy_cost[255 - proba];
}

__device__ __forceinline__ int LevelCostDev(const StaticCostTables* t,
                                            const uint16_t* table, int level) {
  return t->level_fixed_costs[level] +
         table[(level > kMaxVariableLevel) ? kMaxVariableLevel : level];
}

// level_costs layout: [type][band][ctx][68]; probas layout: [type][band][ctx][11].
__device__ __forceinline__ const uint16_t* LevelCostTable(
    const DeviceView* v, int type, int band, int ctx) {
  return v->level_costs + (((type * 8) + band) * 3 + ctx) * 68;
}

__device__ __forceinline__ uint8_t FirstProba(const DeviceView* v, int type,
                                              int band, int ctx) {
  return v->coeff_probas[(((type * 8) + band) * 3 + ctx) * 11];
}

// GetResidualCost_C for one 16-coefficient block. 'first' is 0 or 1.
__device__ int ResidualCostDev(const DeviceView* v, int ctx0, int first,
                               int coeff_type, const int16_t* coeffs) {
  int last = -1;
  for (int n = 15; n >= 0; --n) {
    if (coeffs[n]) {
      last = n;
      break;
    }
  }
  int n = first;
  const int p0 = FirstProba(v, coeff_type, kEncBands[n], ctx0);
  const uint16_t* t = LevelCostTable(v, coeff_type, kEncBands[n], ctx0);
  int cost = (ctx0 == 0) ? BitCostDev(v->tables, 1, p0) : 0;
  if (last < 0) {
    return BitCostDev(v->tables, 0, p0);
  }
  for (; n < last; ++n) {
    const int val = abs(coeffs[n]);
    const int ctx = (val >= 2) ? 2 : val;
    cost += LevelCostDev(v->tables, t, val);
    t = LevelCostTable(v, coeff_type, kEncBands[n + 1], ctx);
  }
  {
    const int val = abs(coeffs[n]);
    cost += LevelCostDev(v->tables, t, val);
    if (n < 15) {
      const int b = kEncBands[n + 1];
      const int ctx = (val == 1) ? 1 : 2;
      const int last_p0 = FirstProba(v, coeff_type, b, ctx);
      cost += BitCostDev(v->tables, 0, last_p0);
    }
  }
  return cost;
}

__device__ __forceinline__ int BlockNonZero(const int16_t* coeffs) {
  for (int n = 15; n >= 0; --n) {
    if (coeffs[n]) return 1;
  }
  return 0;
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
  int i4_nz[kNumBModes];
  long long i4_sse[kNumBModes];
  long long i4_sd[kNumBModes];
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

// ---------------------------------------------------------------------------
// The per-macroblock decision (thread 0 orchestrates; all threads help with
// the numeric phases; __syncthreads separates the phases).

__global__ void __launch_bounds__(kDecimateThreads) DecimateKernel(
    DeviceView v, DecimateKernelParams p, uint8_t* left_nz8) {
  __shared__ MBWork w;
  const int y = (int)(p.y_min + blockIdx.x);
  const int x = (int)p.diagonal - 2 * y;
  const int mb_index = y * (int)p.mb_w + x;
  const int tid = (int)threadIdx.x;
  const DeviceSegment* const dqm = &v.segment_params[v.segments[mb_index]];
  const int tlambda = dqm->tlambda;

  // ---- Phase 0: import, borders, predictions (parallel-friendly setup).
  if (tid == 0) {
    ImportMB(&v, &p, x, y, &w);
    BuildBorders(&v, &p, x, y, &w);
    // VP8MakeLuma16Preds / VP8MakeChroma8Preds NULL conventions.
    CudaIntra16Preds(w.yuv_p, (x > 0) ? w.y_left + 1 : NULL,
                     (y > 0) ? w.y_top : NULL);
    CudaIntraChromaPreds(w.yuv_p, (x > 0) ? w.uv_left + 1 : NULL,
                         (y > 0) ? w.uv_top : NULL);
    // Incoming non-zero context; left_nz[8] is carried separately.
    NzToBytes(LoadNzWord(&v, &p, x, y - 1), LoadNzWord(&v, &p, x - 1, y),
              &w.nz_ctx);
    w.nz_ctx.left_nz[8] = (x > 0) ? left_nz8[mb_index - 1] : 0;
  }
  __syncthreads();

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
  if (tid < 64) {
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

  // ---- Phase 2 (serial): intra16 selection, exactly PickBestIntra16.
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
      // VP8GetCostLuma16: fresh neighbor context each evaluation.
      {
        NzContext c = w.nz_ctx;
        long long R = ResidualCostDev(&v, c.top_nz[8] + c.left_nz[8], 0, 1,
                                      w.i16_dc_levels[mode]);
        for (int by = 0; by < 4; ++by) {
          for (int bx = 0; bx < 4; ++bx) {
            const int ctx = c.top_nz[bx] + c.left_nz[by];
            const int16_t* const lv = w.i16_ac_levels[mode][bx + by * 4];
            R += ResidualCostDev(&v, ctx, 1, 0, lv);
            c.top_nz[bx] = c.left_nz[by] = BlockNonZero(lv);
          }
        }
        rd_cur.R = R;
      }
      if (is_flat) {
        is_flat = CudaIsFlat(w.i16_ac_levels[mode][0], 16, kFlatnessLimitI16);
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
    // Copy the winning levels and reconstruction into the running best.
    for (int b = 0; b < 16; ++b) {
      for (int k = 0; k < 16; ++k) {
        w.rd.y_ac_levels[b][k] = w.i16_ac_levels[best_mode][b][k];
      }
    }
    for (int k = 0; k < 16; ++k) {
      w.rd.y_dc_levels[k] = w.i16_dc_levels[best_mode][k];
    }
    for (int r = 0; r < 16; ++r) {
      for (int cx = 0; cx < 16; ++cx) {
        w.yuv_out[kCudaYOffEnc + r * kCudaBPS + cx] =
            w.i16_out[best_mode][r * kCudaBPS + cx];
      }
    }
    // StoreMaxDelta candidate, evaluated on the intra16 result like the CPU.
    w.rd.store_max_delta = 0;
    w.rd.max_delta = 0;
    if ((best_nz & 0x100ffffu) == 0x1000000u && best_D > dqm->min_disto) {
      const int v0 = CudaAbs(w.rd.y_dc_levels[1]);
      const int v1 = CudaAbs(w.rd.y_dc_levels[2]);
      const int v2 = CudaAbs(w.rd.y_dc_levels[4]);
      int max_v = (v1 > v0) ? v1 : v0;
      max_v = (v2 > max_v) ? v2 : max_v;
      w.rd.store_max_delta = 1;
      w.rd.max_delta = (uint16_t)max_v;
    }
  }
  __syncthreads();

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
    for (int step = 0; step < 16 && !i4_abort; ++step) {
      if (tid == 0) {
        CudaIntra4Preds(w.yuv_p, w.i4_boundary + kTopLeftI4[i4_index]);
      }
      __syncthreads();
      if (tid < kNumBModes) {
        const int mode = tid;
        const uint8_t* const src =
            w.yuv_in + kCudaYOffEnc + kCudaVP8Scan[i4_index];
        const uint8_t* const ref = w.yuv_p + kCudaVP8I4ModeOffsets[mode];
        CudaFTransform(src, ref, w.i4_tmp[mode]);
        w.i4_nz[mode] = CudaQuantizeBlock(w.i4_tmp[mode], w.i4_levels[mode],
                                          &dqm->y1);
        CudaITransformOne(ref, w.i4_tmp[mode], w.i4_out[mode]);
        w.i4_sse[mode] = CudaSSE4x4(src, w.i4_out[mode]);
        w.i4_sd[mode] =
            tlambda ? CudaDisto4x4(src, w.i4_out[mode], kWeightY) : 0;
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
          if (mode > 0 &&
              CudaIsFlat(w.i4_levels[mode], 1, kFlatnessLimitI4)) {
            rd_tmp.R = kFlatnessPenalty;
          } else {
            rd_tmp.R = 0;
          }
          SetRDScoreDev(dqm->lambda_i4, &rd_tmp);
          if (best_mode >= 0 && rd_tmp.score >= rd_i4.score) continue;
          rd_tmp.R += ResidualCostDev(
              &v, i4_ctx.top_nz[bx] + i4_ctx.left_nz[by], 0, 3,
              w.i4_levels[mode]);
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
      for (int b = 0; b < 16; ++b) {
        for (int k = 0; k < 16; ++k) {
          w.rd.y_ac_levels[b][k] = i4_best_levels[b][k];
        }
      }
      for (int r = 0; r < 16; ++r) {
        for (int cx = 0; cx < 16; ++cx) {
          w.yuv_out[kCudaYOffEnc + r * kCudaBPS + cx] =
              w.yuv_out2[kCudaYOffEnc + r * kCudaBPS + cx];
        }
      }
    }
    __syncthreads();
  }

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

  // ---- Phase 5 (serial): chroma selection, exactly PickBestUV.
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
      {
        NzContext c = w.nz_ctx;
        long long R = 0;
        for (int ch = 0; ch <= 2; ch += 2) {
          for (int by = 0; by < 2; ++by) {
            for (int bx = 0; bx < 2; ++bx) {
              const int b = ch * 2 + bx + by * 2;
              const int ctx = c.top_nz[4 + ch + bx] + c.left_nz[4 + ch + by];
              const int16_t* const lv = w.uv_levels_all[mode][b];
              R += ResidualCostDev(&v, ctx, 0, 2, lv);
              c.top_nz[4 + ch + bx] = c.left_nz[4 + ch + by] =
                  BlockNonZero(lv);
            }
          }
        }
        rd_uv.R = R;
      }
      if (mode > 0 &&
          CudaIsFlat(w.uv_levels_all[mode][0], 8, kFlatnessLimitUV)) {
        rd_uv.R += kFlatnessPenalty * 8;
      }
      SetRDScoreDev(dqm->lambda_uv, &rd_uv);
      if (mode == 0 || rd_uv.score < rd_best.score) {
        CopyScoreDev(&rd_best, &rd_uv);
        best_mode = mode;
      }
    }
    w.rd.mode_uv = (uint8_t)best_mode;
    for (int b = 0; b < 8; ++b) {
      for (int k = 0; k < 16; ++k) {
        w.rd.uv_levels[b][k] = w.uv_levels_all[best_mode][b][k];
      }
    }
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
    // Copy the chosen chroma reconstruction into the running best.
    for (int r = 0; r < 8; ++r) {
      for (int cx = 0; cx < 16; ++cx) {
        w.yuv_out[kCudaUOffEnc + r * kCudaBPS + cx] =
            w.uv_out[best_mode][r * kCudaBPS + cx];
      }
    }
    // AddScore(rd, rd_best) for the totals the token loop consumes.
    w.rd.nz |= rd_best.nz;
    w.rd_D += rd_best.D;
    w.rd_H += rd_best.H;
    w.rd.distortion = (uint32_t)w.rd_D;
    w.rd.header_bits = (uint32_t)w.rd_H;

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
    v.results[mb_index] = w.rd;
  }
  __syncthreads();

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

struct DecimateState {
  bool initialization_attempted = false;
  bool available = false;
  bool quarantined = false;
  bool tables_uploaded = false;
  int device = 0;
  cudaStream_t stream = nullptr;
  void* device_arena = nullptr;
  size_t arena_capacity = 0;
  StaticCostTables* device_tables = nullptr;
};

DecimateState g_decimate_state;
DecimateMutex g_decimate_mutex = DECIMATE_MUTEX_INITIALIZER;

bool DecimateFlag(const char* name, bool default_value) {
  const char* const value = getenv(name);
  if (value == nullptr || value[0] == '\0') return default_value;
  return strcmp(value, "0") != 0;
}

bool DecimateInitialize(DecimateState* state) {
  if (state->initialization_attempted) return state->available;
  state->initialization_attempted = true;
  int device_count = 0;
  if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count == 0) {
    (void)cudaGetLastError();
    return false;
  }
  if (cudaSetDevice(state->device) != cudaSuccess) return false;
  if (cudaStreamCreateWithFlags(&state->stream, cudaStreamNonBlocking) !=
      cudaSuccess) {
    state->quarantined = true;
    return false;
  }
  state->available = true;
  return true;
}

bool DecimateEnsureArena(DecimateState* state, size_t bytes) {
  if (bytes <= state->arena_capacity) return true;
  if (state->device_arena != nullptr) {
    (void)cudaFree(state->device_arena);
    state->device_arena = nullptr;
    state->arena_capacity = 0;
  }
  if (cudaMalloc(&state->device_arena, bytes) != cudaSuccess) {
    (void)cudaGetLastError();
    return false;
  }
  state->arena_capacity = bytes;
  return true;
}

size_t AlignUp(size_t value) { return (value + 255u) & ~(size_t)255u; }

}  // namespace

// CPU cost tables reused verbatim on the device.
extern "C" {
extern const uint16_t VP8EntropyCost[256];
extern const uint16_t VP8LevelFixedCosts[2048];
extern const uint16_t VP8FixedCostsI16[4];
extern const uint16_t VP8FixedCostsUV[4];
extern const uint16_t VP8FixedCostsI4[10][10][10];
}

static_assert(sizeof(DeviceResult) == sizeof(WebPAcceleratorDecimateResult),
              "device result must mirror the ABI struct");
static_assert(sizeof(DeviceSegment) ==
                  sizeof(WebPAcceleratorDecimateSegment),
              "device segment must mirror the ABI struct");

extern "C" WebPAcceleratorResult WebPCUDALossyDecimate(
    void* context, const WebPAcceleratorDecimateRequest* request) {
  (void)context;
  if (!DecimateFlag("WEBP_CUDA", true) ||
      !DecimateFlag("WEBP_CUDA_LOSSY_DECIMATE", true)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (request == nullptr || request->y == nullptr || request->u == nullptr ||
      request->v == nullptr || request->segments == nullptr ||
      request->segment_params == nullptr || request->level_costs == nullptr ||
      request->coeff_probas == nullptr || request->results == nullptr ||
      request->recon_y == nullptr || request->recon_u == nullptr ||
      request->recon_v == nullptr || request->width <= 0 ||
      request->height <= 0 || request->mb_w <= 0 || request->mb_h <= 0) {
    return WEBP_ACCELERATOR_ERROR;
  }
  const size_t mb_count = (size_t)request->mb_w * request->mb_h;
  {
    // The roughly 140 ms context-creation cost is only worth paying for
    // large images; once a context exists (the unit ran before, or the
    // process committed to the CUDA backend and the prewarm created one),
    // even small images win.
    const char* const backend = getenv("WEBP_ACCELERATOR");
    const bool context_warm =
        g_decimate_state.available ||
        (backend != nullptr && strcmp(backend, "cuda") == 0);
    const char* const min_mbs = getenv("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS");
    const size_t minimum = (min_mbs != nullptr)
                               ? (size_t)atoll(min_mbs)
                               : (context_warm ? 64u : 4000u);
    if (mb_count < minimum) return WEBP_ACCELERATOR_NOT_RUN;
  }

  WebPAcceleratorResult result = WEBP_ACCELERATOR_NOT_RUN;
  LockDecimate(&g_decimate_mutex);
  DecimateState* const state = &g_decimate_state;
  do {
    if (state->quarantined || !DecimateInitialize(state)) break;
    if (cudaSetDevice(state->device) != cudaSuccess) {
      state->quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
      break;
    }
    const size_t src_y_bytes = (size_t)request->y_stride * request->height;
    const size_t uv_height = (request->height + 1) / 2;
    const size_t src_uv_bytes = (size_t)request->uv_stride * uv_height;
    const size_t recon_y_bytes =
        (size_t)request->mb_w * 16 * request->mb_h * 16;
    const size_t recon_uv_bytes =
        (size_t)request->mb_w * 8 * request->mb_h * 8;
    const size_t preds_w = 4 * (size_t)request->mb_w + 1;
    const size_t preds_h = 4 * (size_t)request->mb_h + 1;
    const size_t preds_bytes = preds_w * preds_h;
    const size_t results_bytes = mb_count * sizeof(DeviceResult);
    const size_t level_cost_bytes = 4u * 8u * 3u * 68u * sizeof(uint16_t);
    const size_t proba_bytes = 4u * 8u * 3u * 11u;
    // Arena layout, 256-byte aligned slices.
    const size_t off_src_y = 0;
    const size_t off_src_u = off_src_y + AlignUp(src_y_bytes);
    const size_t off_src_v = off_src_u + AlignUp(src_uv_bytes);
    const size_t off_recon_y = off_src_v + AlignUp(src_uv_bytes);
    const size_t off_recon_u = off_recon_y + AlignUp(recon_y_bytes);
    const size_t off_recon_v = off_recon_u + AlignUp(recon_uv_bytes);
    const size_t off_segments = off_recon_v + AlignUp(recon_uv_bytes);
    const size_t off_seg_params = off_segments + AlignUp(mb_count);
    const size_t off_level_costs =
        off_seg_params + AlignUp(4 * sizeof(DeviceSegment));
    const size_t off_probas = off_level_costs + AlignUp(level_cost_bytes);
    const size_t off_tables = off_probas + AlignUp(proba_bytes);
    const size_t off_nz = off_tables + AlignUp(sizeof(StaticCostTables));
    const size_t off_preds = off_nz + AlignUp(mb_count * sizeof(uint32_t));
    const size_t off_left_nz8 = off_preds + AlignUp(preds_bytes);
    const size_t off_results = off_left_nz8 + AlignUp(mb_count);
    const size_t total = off_results + AlignUp(results_bytes);
    if (!DecimateEnsureArena(state, total)) break;
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
      error = cudaMemcpyAsync(arena + off_tables, &tables, sizeof(tables),
                              cudaMemcpyHostToDevice, state->stream);
      if (error == cudaSuccess) {
        // The tables snapshot lives on the stack; synchronize before it goes
        // out of scope.
        error = cudaStreamSynchronize(state->stream);
      }
    }
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
    view.tables = (const StaticCostTables*)(arena + off_tables);
    view.nz_words = (uint32_t*)(arena + off_nz);
    // The preds pointer addresses the interior origin like the encoder's.
    view.preds = arena + off_preds + preds_w + 1;
    view.top_derr = nullptr;
    view.results = (DeviceResult*)(arena + off_results);

    DecimateKernelParams params;
    params.width = (uint32_t)request->width;
    params.height = (uint32_t)request->height;
    params.mb_w = (uint32_t)request->mb_w;
    params.mb_h = (uint32_t)request->mb_h;
    params.y_stride = (uint32_t)request->y_stride;
    params.uv_stride = (uint32_t)request->uv_stride;
    params.recon_y_stride = (uint32_t)request->mb_w * 16u;
    params.recon_uv_stride = (uint32_t)request->mb_w * 8u;
    params.max_i4_header_bits = request->max_i4_header_bits;
    params.use_error_diffusion = (uint32_t)request->use_error_diffusion;

    (void)cudaGetLastError();
    const int last_diagonal =
        (request->mb_w - 1) + 2 * (request->mb_h - 1);
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
    }
    if (error == cudaSuccess) {
      error = cudaMemcpyAsync(request->results, view.results, results_bytes,
                              cudaMemcpyDeviceToHost, state->stream);
    }
    if (error == cudaSuccess) {
      error = cudaMemcpyAsync(request->recon_y, view.recon_y, recon_y_bytes,
                              cudaMemcpyDeviceToHost, state->stream);
    }
    if (error == cudaSuccess) {
      error = cudaMemcpyAsync(request->recon_u, view.recon_u, recon_uv_bytes,
                              cudaMemcpyDeviceToHost, state->stream);
    }
    if (error == cudaSuccess) {
      error = cudaMemcpyAsync(request->recon_v, view.recon_v, recon_uv_bytes,
                              cudaMemcpyDeviceToHost, state->stream);
    }
    if (error == cudaSuccess) error = cudaStreamSynchronize(state->stream);
    if (error != cudaSuccess) {
      (void)cudaStreamSynchronize(state->stream);
      if (DecimateFlag("WEBP_CUDA_VERBOSE", false)) {
        fprintf(stderr, "WebP-CUDA: lossy decimate failed: %s\n",
                cudaGetErrorString(error));
      }
      state->quarantined = true;
      result = WEBP_ACCELERATOR_ERROR;
      break;
    }
    if (DecimateFlag("WEBP_CUDA_VERBOSE", false)) {
      fprintf(stderr, "WebP-CUDA: lossy decimate of %dx%d (%zu MBs)\n",
              request->width, request->height, mb_count);
    }
    result = WEBP_ACCELERATOR_SUCCESS;
  } while (0);
  UnlockDecimate(&g_decimate_mutex);
  return result;
}

#endif  // WEBP_CUDA_ENABLE_LOSSY_DECIMATE
