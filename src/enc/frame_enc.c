// Copyright 2011 Google Inc. All Rights Reserved.
//
// Use of this source code is governed by a BSD-style license
// that can be found in the COPYING file in the root of the source
// tree. An additional intellectual property rights grant can be found
// in the file PATENTS. All contributing project authors may
// be found in the AUTHORS file in the root of the source tree.
// -----------------------------------------------------------------------------
//
//   frame coding and analysis
//
// Author: Skal (pascal.massimino@gmail.com)

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dec/common_dec.h"
#include "src/dsp/dsp.h"
#include "src/enc/accelerator_enc.h"
#include "src/enc/cost_enc.h"
#include "src/enc/vp8i_enc.h"
#include "src/enc/profile_enc.h"
#include "src/utils/bit_writer_utils.h"
#include "src/utils/thread_utils.h"
#include "src/utils/utils.h"
#include "src/webp/encode.h"
#include "src/webp/format_constants.h"  // RIFF constants
#include "src/webp/types.h"

#define SEGMENT_VISU 0
#define DEBUG_SEARCH 0  // useful to track search convergence

//------------------------------------------------------------------------------
// multi-pass convergence

#define HEADER_SIZE_ESTIMATE \
  (RIFF_HEADER_SIZE + CHUNK_HEADER_SIZE + VP8_FRAME_HEADER_SIZE)
#define DQ_LIMIT 0.4  // convergence is considered reached if dq < DQ_LIMIT
// we allow 2k of extra head-room in PARTITION0 limit.
#define PARTITION0_SIZE_LIMIT ((VP8_MAX_PARTITION0_SIZE - 2048ULL) << 11)

static float Clamp(float v, float min, float max) {
  return (v < min) ? min : (v > max) ? max : v;
}

typedef struct {  // struct for organizing convergence in either size or PSNR
  int is_first;
  float dq;
  float q, last_q;
  float qmin, qmax;
  double value, last_value;  // PSNR or size
  double target;
  int do_size_search;
} PassStats;

static int InitPassStats(const VP8Encoder* const enc, PassStats* const s) {
  const uint64_t target_size = (uint64_t)enc->config->target_size;
  const int do_size_search = (target_size != 0);
  const float target_PSNR = enc->config->target_PSNR;

  s->is_first = 1;
  s->dq = 10.f;
  s->qmin = 1.f * enc->config->qmin;
  s->qmax = 1.f * enc->config->qmax;
  s->q = s->last_q = Clamp(enc->config->quality, s->qmin, s->qmax);
  s->target = do_size_search       ? (double)target_size
              : (target_PSNR > 0.) ? target_PSNR
                                   : 40.;  // default, just in case
  s->value = s->last_value = 0.;
  s->do_size_search = do_size_search;
  return do_size_search;
}

static float ComputeNextQ(PassStats* const s) {
  float dq;
  if (s->is_first) {
    dq = (s->value > s->target) ? -s->dq : s->dq;
    s->is_first = 0;
  } else if (s->value != s->last_value) {
    const double slope = (s->target - s->value) / (s->last_value - s->value);
    dq = (float)(slope * (s->last_q - s->q));
  } else {
    dq = 0.;  // we're done?!
  }
  // Limit variable to avoid large swings.
  s->dq = Clamp(dq, -30.f, 30.f);
  s->last_q = s->q;
  s->last_value = s->value;
  s->q = Clamp(s->q + s->dq, s->qmin, s->qmax);
  return s->q;
}

//------------------------------------------------------------------------------
// Tables for level coding

const uint8_t VP8Cat3[] = {173, 148, 140};
const uint8_t VP8Cat4[] = {176, 155, 140, 135};
const uint8_t VP8Cat5[] = {180, 157, 141, 134, 130};
const uint8_t VP8Cat6[] = {254, 254, 243, 230, 196, 177,
                           153, 140, 133, 130, 129};

//------------------------------------------------------------------------------
// Reset the statistics about: number of skips, token proba, level cost,...

static void ResetStats(VP8Encoder* const enc) {
  VP8EncProba* const proba = &enc->proba;
  VP8CalculateLevelCosts(proba);
  proba->nb_skip = 0;
}

//------------------------------------------------------------------------------
// Skip decision probability

#define SKIP_PROBA_THRESHOLD 250  // value below which using skip_proba is OK.

static int CalcSkipProba(uint64_t nb, uint64_t total) {
  return (int)(total ? (total - nb) * 255 / total : 255);
}

// Returns the bit-cost for coding the skip probability.
static int FinalizeSkipProba(VP8Encoder* const enc) {
  VP8EncProba* const proba = &enc->proba;
  const int nb_mbs = enc->mb_w * enc->mb_h;
  const int nb_events = proba->nb_skip;
  int size;
  proba->skip_proba = CalcSkipProba(nb_events, nb_mbs);
  proba->use_skip_proba = (proba->skip_proba < SKIP_PROBA_THRESHOLD);
  size = 256;  // 'use_skip_proba' bit
  if (proba->use_skip_proba) {
    size += nb_events * VP8BitCost(1, proba->skip_proba) +
            (nb_mbs - nb_events) * VP8BitCost(0, proba->skip_proba);
    size += 8 * 256;  // cost of signaling the 'skip_proba' itself.
  }
  return size;
}

// Collect statistics and deduce probabilities for next coding pass.
// Return the total bit-cost for coding the probability updates.
static int CalcTokenProba(int nb, int total) {
  assert(nb <= total);
  return nb ? (255 - nb * 255 / total) : 255;
}

// Cost of coding 'nb' 1's and 'total-nb' 0's using 'proba' probability.
static int BranchCost(int nb, int total, int proba) {
  return nb * VP8BitCost(1, proba) + (total - nb) * VP8BitCost(0, proba);
}

static void ResetTokenStats(VP8Encoder* const enc) {
  VP8EncProba* const proba = &enc->proba;
  memset(proba->stats, 0, sizeof(proba->stats));
}

static int FinalizeTokenProbas(VP8EncProba* const proba) {
  int has_changed = 0;
  int size = 0;
  int t, b, c, p;
  for (t = 0; t < NUM_TYPES; ++t) {
    for (b = 0; b < NUM_BANDS; ++b) {
      for (c = 0; c < NUM_CTX; ++c) {
        for (p = 0; p < NUM_PROBAS; ++p) {
          const proba_t stats = proba->stats[t][b][c][p];
          const int nb = (stats >> 0) & 0xffff;
          const int total = (stats >> 16) & 0xffff;
          const int update_proba = VP8CoeffsUpdateProba[t][b][c][p];
          const int old_p = VP8CoeffsProba0[t][b][c][p];
          const int new_p = CalcTokenProba(nb, total);
          const int old_cost =
              BranchCost(nb, total, old_p) + VP8BitCost(0, update_proba);
          const int new_cost = BranchCost(nb, total, new_p) +
                               VP8BitCost(1, update_proba) + 8 * 256;
          const int use_new_p = (old_cost > new_cost);
          size += VP8BitCost(use_new_p, update_proba);
          if (use_new_p) {  // only use proba that seem meaningful enough.
            proba->coeffs[t][b][c][p] = new_p;
            has_changed |= (new_p != old_p);
            size += 8 * 256;
          } else {
            proba->coeffs[t][b][c][p] = old_p;
          }
        }
      }
    }
  }
  proba->dirty = has_changed;
  return size;
}

//------------------------------------------------------------------------------
// Finalize Segment probability based on the coding tree

static int GetProba(int a, int b) {
  const int total = a + b;
  return (total == 0) ? 255  // that's the default probability.
                      : (255 * a + total / 2) / total;  // rounded proba
}

static void ResetSegments(VP8Encoder* const enc) {
  int n;
  for (n = 0; n < enc->mb_w * enc->mb_h; ++n) {
    enc->mb_info[n].segment = 0;
  }
}

static void SetSegmentProbas(VP8Encoder* const enc) {
  int p[NUM_MB_SEGMENTS] = {0};
  int n;

  for (n = 0; n < enc->mb_w * enc->mb_h; ++n) {
    const VP8MBInfo* const mb = &enc->mb_info[n];
    ++p[mb->segment];
  }
#if !defined(WEBP_DISABLE_STATS)
  if (enc->pic->stats != NULL) {
    for (n = 0; n < NUM_MB_SEGMENTS; ++n) {
      enc->pic->stats->segment_size[n] = p[n];
    }
  }
#endif
  if (enc->segment_hdr.num_segments > 1) {
    uint8_t* const probas = enc->proba.segments;
    probas[0] = GetProba(p[0] + p[1], p[2] + p[3]);
    probas[1] = GetProba(p[0], p[1]);
    probas[2] = GetProba(p[2], p[3]);

    enc->segment_hdr.update_map =
        (probas[0] != 255) || (probas[1] != 255) || (probas[2] != 255);
    if (!enc->segment_hdr.update_map) ResetSegments(enc);
    enc->segment_hdr.size =
        p[0] * (VP8BitCost(0, probas[0]) + VP8BitCost(0, probas[1])) +
        p[1] * (VP8BitCost(0, probas[0]) + VP8BitCost(1, probas[1])) +
        p[2] * (VP8BitCost(1, probas[0]) + VP8BitCost(0, probas[2])) +
        p[3] * (VP8BitCost(1, probas[0]) + VP8BitCost(1, probas[2]));
  } else {
    enc->segment_hdr.update_map = 0;
    enc->segment_hdr.size = 0;
  }
}

//------------------------------------------------------------------------------
// Coefficient coding

static int PutCoeffs(VP8BitWriter* const bw, int ctx, const VP8Residual* res) {
  int n = res->first;
  // should be prob[VP8EncBands[n]], but it's equivalent for n=0 or 1
  const uint8_t* p = res->prob[n][ctx];
  if (!VP8PutBit(bw, res->last >= 0, p[0])) {
    return 0;
  }

  while (n < 16) {
    const int c = res->coeffs[n++];
    const int sign = c < 0;
    int v = sign ? -c : c;
    if (!VP8PutBit(bw, v != 0, p[1])) {
      p = res->prob[VP8EncBands[n]][0];
      continue;
    }
    if (!VP8PutBit(bw, v > 1, p[2])) {
      p = res->prob[VP8EncBands[n]][1];
    } else {
      if (!VP8PutBit(bw, v > 4, p[3])) {
        if (VP8PutBit(bw, v != 2, p[4])) {
          VP8PutBit(bw, v == 4, p[5]);
        }
      } else if (!VP8PutBit(bw, v > 10, p[6])) {
        if (!VP8PutBit(bw, v > 6, p[7])) {
          VP8PutBit(bw, v == 6, 159);
        } else {
          VP8PutBit(bw, v >= 9, 165);
          VP8PutBit(bw, !(v & 1), 145);
        }
      } else {
        int mask;
        const uint8_t* tab;
        if (v < 3 + (8 << 1)) {  // VP8Cat3  (3b)
          VP8PutBit(bw, 0, p[8]);
          VP8PutBit(bw, 0, p[9]);
          v -= 3 + (8 << 0);
          mask = 1 << 2;
          tab = VP8Cat3;
        } else if (v < 3 + (8 << 2)) {  // VP8Cat4  (4b)
          VP8PutBit(bw, 0, p[8]);
          VP8PutBit(bw, 1, p[9]);
          v -= 3 + (8 << 1);
          mask = 1 << 3;
          tab = VP8Cat4;
        } else if (v < 3 + (8 << 3)) {  // VP8Cat5  (5b)
          VP8PutBit(bw, 1, p[8]);
          VP8PutBit(bw, 0, p[10]);
          v -= 3 + (8 << 2);
          mask = 1 << 4;
          tab = VP8Cat5;
        } else {  // VP8Cat6 (11b)
          VP8PutBit(bw, 1, p[8]);
          VP8PutBit(bw, 1, p[10]);
          v -= 3 + (8 << 3);
          mask = 1 << 10;
          tab = VP8Cat6;
        }
        while (mask) {
          VP8PutBit(bw, !!(v & mask), *tab++);
          mask >>= 1;
        }
      }
      p = res->prob[VP8EncBands[n]][2];
    }
    VP8PutBitUniform(bw, sign);
    if (n == 16 || !VP8PutBit(bw, n <= res->last, p[0])) {
      return 1;  // EOB
    }
  }
  return 1;
}

static void CodeResiduals(VP8BitWriter* const bw, VP8EncIterator* const it,
                          const VP8ModeScore* const rd) {
  int x, y, ch;
  VP8Residual res;
  uint64_t pos1, pos2, pos3;
  const int i16 = (it->mb->type == 1);
  const int segment = it->mb->segment;
  VP8Encoder* const enc = it->enc;

  VP8IteratorNzToBytes(it);

  pos1 = VP8BitWriterPos(bw);
  if (i16) {
    VP8InitResidual(0, 1, enc, &res);
    VP8SetResidualCoeffs(rd->y_dc_levels, &res);
    it->top_nz[8] = it->left_nz[8] =
        PutCoeffs(bw, it->top_nz[8] + it->left_nz[8], &res);
    VP8InitResidual(1, 0, enc, &res);
  } else {
    VP8InitResidual(0, 3, enc, &res);
  }

  // luma-AC
  for (y = 0; y < 4; ++y) {
    for (x = 0; x < 4; ++x) {
      const int ctx = it->top_nz[x] + it->left_nz[y];
      VP8SetResidualCoeffs(rd->y_ac_levels[x + y * 4], &res);
      it->top_nz[x] = it->left_nz[y] = PutCoeffs(bw, ctx, &res);
    }
  }
  pos2 = VP8BitWriterPos(bw);

  // U/V
  VP8InitResidual(0, 2, enc, &res);
  for (ch = 0; ch <= 2; ch += 2) {
    for (y = 0; y < 2; ++y) {
      for (x = 0; x < 2; ++x) {
        const int ctx = it->top_nz[4 + ch + x] + it->left_nz[4 + ch + y];
        VP8SetResidualCoeffs(rd->uv_levels[ch * 2 + x + y * 2], &res);
        it->top_nz[4 + ch + x] = it->left_nz[4 + ch + y] =
            PutCoeffs(bw, ctx, &res);
      }
    }
  }
  pos3 = VP8BitWriterPos(bw);
  it->luma_bits = pos2 - pos1;
  it->uv_bits = pos3 - pos2;
  it->bit_count[segment][i16] += it->luma_bits;
  it->bit_count[segment][2] += it->uv_bits;
  VP8IteratorBytesToNz(it);
}

// Same as CodeResiduals, but doesn't actually write anything.
// Instead, it just records the event distribution.
static void RecordResiduals(VP8EncIterator* const it,
                            const VP8ModeScore* const rd) {
  int x, y, ch;
  VP8Residual res;
  VP8Encoder* const enc = it->enc;

  VP8IteratorNzToBytes(it);

  if (it->mb->type == 1) {  // i16x16
    VP8InitResidual(0, 1, enc, &res);
    VP8SetResidualCoeffs(rd->y_dc_levels, &res);
    it->top_nz[8] = it->left_nz[8] =
        VP8RecordCoeffs(it->top_nz[8] + it->left_nz[8], &res);
    VP8InitResidual(1, 0, enc, &res);
  } else {
    VP8InitResidual(0, 3, enc, &res);
  }

  // luma-AC
  for (y = 0; y < 4; ++y) {
    for (x = 0; x < 4; ++x) {
      const int ctx = it->top_nz[x] + it->left_nz[y];
      VP8SetResidualCoeffs(rd->y_ac_levels[x + y * 4], &res);
      it->top_nz[x] = it->left_nz[y] = VP8RecordCoeffs(ctx, &res);
    }
  }

  // U/V
  VP8InitResidual(0, 2, enc, &res);
  for (ch = 0; ch <= 2; ch += 2) {
    for (y = 0; y < 2; ++y) {
      for (x = 0; x < 2; ++x) {
        const int ctx = it->top_nz[4 + ch + x] + it->left_nz[4 + ch + y];
        VP8SetResidualCoeffs(rd->uv_levels[ch * 2 + x + y * 2], &res);
        it->top_nz[4 + ch + x] = it->left_nz[4 + ch + y] =
            VP8RecordCoeffs(ctx, &res);
      }
    }
  }

  VP8IteratorBytesToNz(it);
}

//------------------------------------------------------------------------------
// Token buffer

#if !defined(DISABLE_TOKEN_BUFFER)

// Accelerated whole-pass decimate state. The backend computes every
// macroblock's mode decision, levels, and reconstruction for one pass; the
// loop then replays them through the ordinary token/side-info bookkeeping.
typedef struct {
  WebPAcceleratorDecimateResult* results;
  uint8_t* recon;      // one allocation: Y plane then U then V
  uint8_t* segments;
  uint8_t* recon_y;
  uint8_t* recon_u;
  uint8_t* recon_v;
  int recon_y_stride;
  int recon_uv_stride;
  // Streaming: the request outlives TryAcceleratedDecimate so bands can be
  // collected lazily while the device still computes later ones.
  WebPAcceleratorDecimateSegment segment_params[NUM_MB_SEGMENTS];
  WebPAcceleratorDecimateRequest request;
  int band_count;
  int rows_per_band;
  int bands_collected;
  // Pipelined token recording: a single worker thread records each
  // collected band's macroblocks in raster order (the exact CPU order, so
  // the saturating probability statistics evolve identically) while the
  // main thread replays the same band. All the recorder needs — levels,
  // modes, and non-zero context words — lives in 'results'.
  WebPWorker record_worker;
  int record_worker_started;  // Reset() succeeded; thread must be ended
  int record_pipeline;        // pipeline enabled for this pass
  int record_active;          // a job is launched and not yet synced
  int record_ok;              // sticky recording success (main thread only)
  int record_rows;            // rows handed to the recorder so far
  int record_job_start;       // row range of the in-flight job
  int record_job_end;
  uint32_t* record_nz;        // shadow nz words of the last recorded row
} AcceleratedDecimatePass;

// RecordTokens for a range of rows, reading everything from the collected
// GPU results instead of the iterator. The nz-context bookkeeping mirrors
// VP8IteratorNzToBytes/BytesToNz exactly: the top words come from the shadow
// row, the left word is the previously packed word of this row (0 at the
// border, like enc->nz[-1]), and the left-DC context is carried separately
// and reset per row (like InitLeft).
static int RecordTokensFromResults(VP8Encoder* const enc,
                                   AcceleratedDecimatePass* const pass,
                                   int start_row, int end_row) {
#define NZ_BIT(word, n) (!!((word) & (1u << (n))))
  const int mb_w = enc->mb_w;
  int row;
  for (row = start_row; row < end_row; ++row) {
    uint32_t lnz = 0;   // left border word (enc->nz[-1] is the constant 0)
    int left_nz8 = 0;   // left-DC context, reset at each row start
    int mb_x;
    for (mb_x = 0; mb_x < mb_w; ++mb_x) {
      const WebPAcceleratorDecimateResult* const r =
          &pass->results[row * mb_w + mb_x];
      VP8TBuffer* const tokens = &enc->tokens[row & (enc->num_parts - 1)];
      const uint32_t tnz = pass->record_nz[mb_x];
      int top_nz[9], left_nz[9];
      VP8Residual res;
      uint32_t nz = 0;
      int bx, by, ch;
      top_nz[0] = NZ_BIT(tnz, 12);
      top_nz[1] = NZ_BIT(tnz, 13);
      top_nz[2] = NZ_BIT(tnz, 14);
      top_nz[3] = NZ_BIT(tnz, 15);
      top_nz[4] = NZ_BIT(tnz, 18);
      top_nz[5] = NZ_BIT(tnz, 19);
      top_nz[6] = NZ_BIT(tnz, 22);
      top_nz[7] = NZ_BIT(tnz, 23);
      top_nz[8] = NZ_BIT(tnz, 24);
      left_nz[0] = NZ_BIT(lnz, 3);
      left_nz[1] = NZ_BIT(lnz, 7);
      left_nz[2] = NZ_BIT(lnz, 11);
      left_nz[3] = NZ_BIT(lnz, 15);
      left_nz[4] = NZ_BIT(lnz, 17);
      left_nz[5] = NZ_BIT(lnz, 19);
      left_nz[6] = NZ_BIT(lnz, 21);
      left_nz[7] = NZ_BIT(lnz, 23);
      left_nz[8] = left_nz8;
      if (!r->is_i4) {  // i16x16
        const int ctx = top_nz[8] + left_nz[8];
        VP8InitResidual(0, 1, enc, &res);
        VP8SetResidualCoeffs(r->y_dc_levels, &res);
        top_nz[8] = left_nz[8] = VP8RecordCoeffTokens(ctx, &res, tokens);
        VP8InitResidual(1, 0, enc, &res);
      } else {
        VP8InitResidual(0, 3, enc, &res);
      }
      for (by = 0; by < 4; ++by) {
        for (bx = 0; bx < 4; ++bx) {
          const int ctx = top_nz[bx] + left_nz[by];
          VP8SetResidualCoeffs(r->y_ac_levels[bx + by * 4], &res);
          top_nz[bx] = left_nz[by] = VP8RecordCoeffTokens(ctx, &res, tokens);
        }
      }
      VP8InitResidual(0, 2, enc, &res);
      for (ch = 0; ch <= 2; ch += 2) {
        for (by = 0; by < 2; ++by) {
          for (bx = 0; bx < 2; ++bx) {
            const int ctx = top_nz[4 + ch + bx] + left_nz[4 + ch + by];
            VP8SetResidualCoeffs(r->uv_levels[ch * 2 + bx + by * 2], &res);
            top_nz[4 + ch + bx] = left_nz[4 + ch + by] =
                VP8RecordCoeffTokens(ctx, &res, tokens);
          }
        }
      }
      nz |= (top_nz[0] << 12) | (top_nz[1] << 13);
      nz |= (top_nz[2] << 14) | (top_nz[3] << 15);
      nz |= (top_nz[4] << 18) | (top_nz[5] << 19);
      nz |= (top_nz[6] << 22) | (top_nz[7] << 23);
      nz |= (top_nz[8] << 24);
      nz |= (left_nz[0] << 3) | (left_nz[1] << 7);
      nz |= (left_nz[2] << 11);
      nz |= (left_nz[4] << 17) | (left_nz[6] << 21);
      pass->record_nz[mb_x] = nz;
      lnz = nz;
      left_nz8 = left_nz[8];
      if (tokens->error) return 0;
    }
  }
  return 1;
#undef NZ_BIT
}

static int RecordBandJobHook(void* arg1, void* arg2) {
  AcceleratedDecimatePass* const pass = (AcceleratedDecimatePass*)arg1;
  VP8Encoder* const enc = (VP8Encoder*)arg2;
  return RecordTokensFromResults(enc, pass, pass->record_job_start,
                                 pass->record_job_end);
}

// Waits for any in-flight recording job; folds its status into record_ok.
// Only the main thread touches record_ok, always at these sync points.
static int AcceleratedDecimateSyncRecorder(AcceleratedDecimatePass* const
                                               pass) {
  if (pass->record_active) {
    if (!WebPGetWorkerInterface()->Sync(&pass->record_worker)) {
      pass->record_ok = 0;
    }
    pass->record_active = 0;
  }
  return pass->record_ok;
}

// Collects result bands up to the one containing macroblock row 'mb_y'.
// Returns 0 when a collection fails; the caller then falls back to the CPU
// decimate for the remaining macroblocks (the replayed state is complete, so
// the switch is seamless).
static int AcceleratedDecimateEnsureRow(VP8Encoder* const enc,
                                        AcceleratedDecimatePass* const pass,
                                        int mb_y) {
  while (pass->bands_collected * pass->rows_per_band <= mb_y) {
    pass->request.phase = WEBP_ACCELERATOR_DECIMATE_COLLECT;
    pass->request.band_index = pass->bands_collected;
    if (WebPAccelerateLossyDecimate(&pass->request) !=
        WEBP_ACCELERATOR_SUCCESS) {
      return 0;
    }
    ++pass->bands_collected;
    if (pass->record_pipeline) {
      int end_row = pass->bands_collected * pass->rows_per_band;
      if (end_row > enc->mb_h) end_row = enc->mb_h;
      // one in-flight job at a time keeps the raster recording order exact
      AcceleratedDecimateSyncRecorder(pass);
      if (pass->record_ok && end_row > pass->record_rows) {
        pass->record_job_start = pass->record_rows;
        pass->record_job_end = end_row;
        pass->record_rows = end_row;
        if (pass->record_worker_started) {
          WebPGetWorkerInterface()->Launch(&pass->record_worker);
          pass->record_active = 1;
        } else if (!RecordBandJobHook(pass, enc)) {
          pass->record_ok = 0;
        }
      }
    }
  }
  return 1;
}

static void AcceleratedDecimateClear(AcceleratedDecimatePass* const pass) {
  if (pass->record_worker_started) {
    const WebPWorkerInterface* const worker_interface =
        WebPGetWorkerInterface();
    worker_interface->Sync(&pass->record_worker);
    worker_interface->End(&pass->record_worker);
  }
  WebPSafeFree(pass->record_nz);
  WebPSafeFree(pass->results);
  WebPSafeFree(pass->recon);
  WebPSafeFree(pass->segments);
  memset(pass, 0, sizeof(*pass));
}

// Returns 1 and fills 'pass' when a backend computed the whole pass.
static int TryAcceleratedDecimate(VP8Encoder* const enc,
                                  AcceleratedDecimatePass* const pass) {
  const int mb_count = enc->mb_w * enc->mb_h;
  const size_t y_size = (size_t)enc->mb_w * 16 * enc->mb_h * 16;
  const size_t uv_size = (size_t)enc->mb_w * 8 * enc->mb_h * 8;
  WebPAcceleratorDecimateSegment* segment_params;
  WebPAcceleratorDecimateRequest* request;
  int i;
  memset(pass, 0, sizeof(*pass));
  segment_params = pass->segment_params;
  request = &pass->request;
  // The exact contract requires the basic (non-trellis) search and the
  // fork's stable cost tables; a restored upstream mid-pass refresh cadence
  // would serialize decisions on token statistics again.
  if (enc->rd_opt_level != RD_OPT_BASIC || enc->method < 2 ||
      getenv("WEBP_TOKEN_REFRESH_SHIFT") != NULL) {
    return 0;
  }
  VP8CalculateLevelCosts(&enc->proba);
  pass->results = (WebPAcceleratorDecimateResult*)WebPSafeMalloc(
      mb_count, sizeof(*pass->results));
  pass->recon = (uint8_t*)WebPSafeMalloc(1, y_size + 2 * uv_size);
  pass->segments = (uint8_t*)WebPSafeMalloc(mb_count, 1);
  if (pass->results == NULL || pass->recon == NULL ||
      pass->segments == NULL) {
    AcceleratedDecimateClear(pass);
    return 0;
  }
  for (i = 0; i < mb_count; ++i) {
    pass->segments[i] = enc->mb_info[i].segment;
  }
  for (i = 0; i < NUM_MB_SEGMENTS; ++i) {
    const VP8SegmentInfo* const dqm = &enc->dqm[i];
    WebPAcceleratorDecimateSegment* const params = &pass->segment_params[i];
    memcpy(params->y1.q, dqm->y1.q, sizeof(params->y1.q));
    memcpy(params->y1.iq, dqm->y1.iq, sizeof(params->y1.iq));
    memcpy(params->y1.bias, dqm->y1.bias, sizeof(params->y1.bias));
    memcpy(params->y1.zthresh, dqm->y1.zthresh, sizeof(params->y1.zthresh));
    memcpy(params->y1.sharpen, dqm->y1.sharpen, sizeof(params->y1.sharpen));
    memcpy(params->y2.q, dqm->y2.q, sizeof(params->y2.q));
    memcpy(params->y2.iq, dqm->y2.iq, sizeof(params->y2.iq));
    memcpy(params->y2.bias, dqm->y2.bias, sizeof(params->y2.bias));
    memcpy(params->y2.zthresh, dqm->y2.zthresh, sizeof(params->y2.zthresh));
    memcpy(params->y2.sharpen, dqm->y2.sharpen, sizeof(params->y2.sharpen));
    memcpy(params->uv.q, dqm->uv.q, sizeof(params->uv.q));
    memcpy(params->uv.iq, dqm->uv.iq, sizeof(params->uv.iq));
    memcpy(params->uv.bias, dqm->uv.bias, sizeof(params->uv.bias));
    memcpy(params->uv.zthresh, dqm->uv.zthresh, sizeof(params->uv.zthresh));
    memcpy(params->uv.sharpen, dqm->uv.sharpen, sizeof(params->uv.sharpen));
    params->lambda_i16 = dqm->lambda_i16;
    params->lambda_i4 = dqm->lambda_i4;
    params->lambda_uv = dqm->lambda_uv;
    params->lambda_mode = dqm->lambda_mode;
    params->tlambda = dqm->tlambda;
    params->min_disto = dqm->min_disto;
  }
  pass->recon_y = pass->recon;
  pass->recon_u = pass->recon + y_size;
  pass->recon_v = pass->recon + y_size + uv_size;
  pass->recon_y_stride = enc->mb_w * 16;
  pass->recon_uv_stride = enc->mb_w * 8;
  request->width = enc->pic->width;
  request->height = enc->pic->height;
  request->mb_w = enc->mb_w;
  request->mb_h = enc->mb_h;
  request->y = enc->pic->y;
  request->u = enc->pic->u;
  request->v = enc->pic->v;
  request->y_stride = enc->pic->y_stride;
  request->uv_stride = enc->pic->uv_stride;
  request->segments = pass->segments;
  request->segment_params = segment_params;
  request->level_costs = &enc->proba.level_cost[0][0][0][0];
  request->coeff_probas = &enc->proba.coeffs[0][0][0][0];
  request->max_i4_header_bits = enc->max_i4_header_bits;
  request->use_error_diffusion = (enc->top_derr != NULL);
  request->results = pass->results;
  request->recon_y = pass->recon_y;
  request->recon_u = pass->recon_u;
  request->recon_v = pass->recon_v;
  request->recon_y_stride = pass->recon_y_stride;
  request->recon_uv_stride = pass->recon_uv_stride;
  // Stream the pass in bands so macroblock replay and token recording can
  // overlap with the device still computing later rows.
  pass->band_count = (enc->mb_h >= 16) ? 8 : (enc->mb_h >= 8) ? 4 : 1;
  pass->rows_per_band = (enc->mb_h + pass->band_count - 1) / pass->band_count;
  pass->bands_collected = 0;
  // Pipelined recording: WEBP_TOKEN_RECORD_PIPELINE=0 records inline on the
  // main thread instead (the emitted bytes are identical either way).
  pass->record_ok = 1;
  pass->record_pipeline = 1;
  {
    const char* const env = getenv("WEBP_TOKEN_RECORD_PIPELINE");
    if (env != NULL && !strcmp(env, "0")) pass->record_pipeline = 0;
  }
  if (pass->record_pipeline) {
    pass->record_nz =
        (uint32_t*)WebPSafeCalloc(enc->mb_w, sizeof(*pass->record_nz));
    if (pass->record_nz == NULL) {
      pass->record_pipeline = 0;
    } else {
      const WebPWorkerInterface* const worker_interface =
          WebPGetWorkerInterface();
      worker_interface->Init(&pass->record_worker);
      pass->record_worker.data1 = pass;
      pass->record_worker.data2 = enc;
      pass->record_worker.hook = RecordBandJobHook;
      // no thread: bands still record synchronously at each collect point
      pass->record_worker_started = worker_interface->Reset(&pass->record_worker);
    }
  }
  request->phase = WEBP_ACCELERATOR_DECIMATE_BEGIN;
  request->band_count = pass->band_count;
  request->band_index = 0;
  if (WebPAccelerateLossyDecimate(request) != WEBP_ACCELERATOR_SUCCESS) {
    AcceleratedDecimateClear(pass);
    return 0;
  }
  return 1;
}

static int RecordTokens(VP8EncIterator* const it, const VP8ModeScore* const rd,
                        VP8TBuffer* const tokens) {
  int x, y, ch;
  VP8Residual res;
  VP8Encoder* const enc = it->enc;

  VP8IteratorNzToBytes(it);
  if (it->mb->type == 1) {  // i16x16
    const int ctx = it->top_nz[8] + it->left_nz[8];
    VP8InitResidual(0, 1, enc, &res);
    VP8SetResidualCoeffs(rd->y_dc_levels, &res);
    it->top_nz[8] = it->left_nz[8] = VP8RecordCoeffTokens(ctx, &res, tokens);
    VP8InitResidual(1, 0, enc, &res);
  } else {
    VP8InitResidual(0, 3, enc, &res);
  }

  // luma-AC
  for (y = 0; y < 4; ++y) {
    for (x = 0; x < 4; ++x) {
      const int ctx = it->top_nz[x] + it->left_nz[y];
      VP8SetResidualCoeffs(rd->y_ac_levels[x + y * 4], &res);
      it->top_nz[x] = it->left_nz[y] = VP8RecordCoeffTokens(ctx, &res, tokens);
    }
  }

  // U/V
  VP8InitResidual(0, 2, enc, &res);
  for (ch = 0; ch <= 2; ch += 2) {
    for (y = 0; y < 2; ++y) {
      for (x = 0; x < 2; ++x) {
        const int ctx = it->top_nz[4 + ch + x] + it->left_nz[4 + ch + y];
        VP8SetResidualCoeffs(rd->uv_levels[ch * 2 + x + y * 2], &res);
        it->top_nz[4 + ch + x] = it->left_nz[4 + ch + y] =
            VP8RecordCoeffTokens(ctx, &res, tokens);
      }
    }
  }
  VP8IteratorBytesToNz(it);
  return !tokens->error;
}

#endif  // !DISABLE_TOKEN_BUFFER

//------------------------------------------------------------------------------
// ExtraInfo map / Debug function

#if !defined(WEBP_DISABLE_STATS)

#if SEGMENT_VISU
static void SetBlock(uint8_t* p, int value, int size) {
  int y;
  for (y = 0; y < size; ++y) {
    memset(p, value, size);
    p += BPS;
  }
}
#endif

static void ResetSSE(VP8Encoder* const enc) {
  enc->sse[0] = 0;
  enc->sse[1] = 0;
  enc->sse[2] = 0;
  // Note: enc->sse[3] is managed by alpha.c
  enc->sse_count = 0;
}

static void StoreSSE(const VP8EncIterator* const it) {
  VP8Encoder* const enc = it->enc;
  const uint8_t* const in = it->yuv_in;
  const uint8_t* const out = it->yuv_out;
  // Note: not totally accurate at boundary. And doesn't include in-loop filter.
  enc->sse[0] += VP8SSE16x16(in + Y_OFF_ENC, out + Y_OFF_ENC);
  enc->sse[1] += VP8SSE8x8(in + U_OFF_ENC, out + U_OFF_ENC);
  enc->sse[2] += VP8SSE8x8(in + V_OFF_ENC, out + V_OFF_ENC);
  enc->sse_count += 16 * 16;
}

static void StoreSideInfo(const VP8EncIterator* const it) {
  VP8Encoder* const enc = it->enc;
  const VP8MBInfo* const mb = it->mb;
  WebPPicture* const pic = enc->pic;

  if (pic->stats != NULL) {
    StoreSSE(it);
    enc->block_count[0] += (mb->type == 0);
    enc->block_count[1] += (mb->type == 1);
    enc->block_count[2] += (mb->skip != 0);
  }

  if (pic->extra_info != NULL) {
    uint8_t* const info = &pic->extra_info[it->x + it->y * enc->mb_w];
    switch (pic->extra_info_type) {
      case 1:
        *info = mb->type;
        break;
      case 2:
        *info = mb->segment;
        break;
      case 3:
        *info = enc->dqm[mb->segment].quant;
        break;
      case 4:
        *info = (mb->type == 1) ? it->preds[0] : 0xff;
        break;
      case 5:
        *info = mb->uv_mode;
        break;
      case 6: {
        const int b = (int)((it->luma_bits + it->uv_bits + 7) >> 3);
        *info = (b > 255) ? 255 : b;
        break;
      }
      case 7:
        *info = mb->alpha;
        break;
      default:
        *info = 0;
        break;
    }
  }
#if SEGMENT_VISU  // visualize segments and prediction modes
  SetBlock(it->yuv_out + Y_OFF_ENC, mb->segment * 64, 16);
  SetBlock(it->yuv_out + U_OFF_ENC, it->preds[0] * 64, 8);
  SetBlock(it->yuv_out + V_OFF_ENC, mb->uv_mode * 64, 8);
#endif
}

static void ResetSideInfo(const VP8EncIterator* const it) {
  VP8Encoder* const enc = it->enc;
  WebPPicture* const pic = enc->pic;
  if (pic->stats != NULL) {
    memset(enc->block_count, 0, sizeof(enc->block_count));
  }
  ResetSSE(enc);
}
#else   // defined(WEBP_DISABLE_STATS)
static void ResetSSE(VP8Encoder* const enc) { (void)enc; }
static void StoreSideInfo(const VP8EncIterator* const it) {
  VP8Encoder* const enc = it->enc;
  WebPPicture* const pic = enc->pic;
  if (pic->extra_info != NULL) {
    if (it->x == 0 && it->y == 0) {  // only do it once, at start
      memset(pic->extra_info, 0,
             enc->mb_w * enc->mb_h * sizeof(*pic->extra_info));
    }
  }
}

static void ResetSideInfo(const VP8EncIterator* const it) { (void)it; }
#endif  // !defined(WEBP_DISABLE_STATS)

static double GetPSNR(uint64_t mse, uint64_t size) {
  return (mse > 0 && size > 0) ? 10. * log10(255. * 255. * size / mse) : 99;
}

//------------------------------------------------------------------------------
//  StatLoop(): only collect statistics (number of skips, token usage, ...).
//  This is used for deciding optimal probabilities. It also modifies the
//  quantizer value if some target (size, PSNR) was specified.

static void SetLoopParams(VP8Encoder* const enc, float q) {
  // Make sure the quality parameter is inside valid bounds
  q = Clamp(q, 0.f, 100.f);

  VP8SetSegmentParams(enc, q);  // setup segment quantizations and filters
  SetSegmentProbas(enc);        // compute segment probabilities

  ResetStats(enc);
  ResetSSE(enc);
}

static uint64_t OneStatPass(VP8Encoder* const enc, VP8RDLevel rd_opt,
                            int nb_mbs, int percent_delta, PassStats* const s) {
  VP8EncIterator it;
  uint64_t size = 0;
  uint64_t size_p0 = 0;
  uint64_t distortion = 0;
  const uint64_t pixel_count = (uint64_t)nb_mbs * 384;

  VP8IteratorInit(enc, &it);
  SetLoopParams(enc, s->q);
  do {
    VP8ModeScore info;
    VP8IteratorImport(&it, NULL);
    if (VP8Decimate(&it, &info, rd_opt)) {
      // Just record the number of skips and act like skip_proba is not used.
      ++enc->proba.nb_skip;
    }
    RecordResiduals(&it, &info);
    size += info.R + info.H;
    size_p0 += info.H;
    distortion += info.D;
    if (percent_delta && !VP8IteratorProgress(&it, percent_delta)) {
      return 0;
    }
    VP8IteratorSaveBoundary(&it);
  } while (VP8IteratorNext(&it) && --nb_mbs > 0);

  size_p0 += enc->segment_hdr.size;
  if (s->do_size_search) {
    size += FinalizeSkipProba(enc);
    size += FinalizeTokenProbas(&enc->proba);
    size = ((size + size_p0 + 1024) >> 11) + HEADER_SIZE_ESTIMATE;
    s->value = (double)size;
  } else {
    s->value = GetPSNR(distortion, pixel_count);
  }
  return size_p0;
}

static int StatLoop(VP8Encoder* const enc) {
  const int method = enc->method;
  const int do_search = enc->do_search;
  const int fast_probe = ((method == 0 || method == 3) && !do_search);
  int num_pass_left = enc->config->pass;
  const int task_percent = 20;
  const int percent_per_pass =
      (task_percent + num_pass_left / 2) / num_pass_left;
  const int final_percent = enc->percent + task_percent;
  const VP8RDLevel rd_opt =
      (method >= 3 || do_search) ? RD_OPT_BASIC : RD_OPT_NONE;
  int nb_mbs = enc->mb_w * enc->mb_h;
  PassStats stats;

  InitPassStats(enc, &stats);
  ResetTokenStats(enc);

  // Fast mode: quick analysis pass over few mbs. Better than nothing.
  if (fast_probe) {
    if (method == 3) {  // we need more stats for method 3 to be reliable.
      nb_mbs = (nb_mbs > 200) ? nb_mbs >> 1 : 100;
    } else {
      nb_mbs = (nb_mbs > 200) ? nb_mbs >> 2 : 50;
    }
  }

  while (num_pass_left-- > 0) {
    const int is_last_pass = (fabs(stats.dq) <= DQ_LIMIT) ||
                             (num_pass_left == 0) ||
                             (enc->max_i4_header_bits == 0);
    const uint64_t size_p0 =
        OneStatPass(enc, rd_opt, nb_mbs, percent_per_pass, &stats);
    if (size_p0 == 0) return 0;
#if (DEBUG_SEARCH > 0)
    printf("#%d value:%.1lf -> %.1lf   q:%.2f -> %.2f\n", num_pass_left,
           stats.last_value, stats.value, stats.last_q, stats.q);
#endif
    if (enc->max_i4_header_bits > 0 && size_p0 > PARTITION0_SIZE_LIMIT) {
      ++num_pass_left;
      enc->max_i4_header_bits >>= 1;  // strengthen header bit limitation...
      continue;                       // ...and start over
    }
    if (is_last_pass) {
      break;
    }
    // If no target size: just do several pass without changing 'q'
    if (do_search) {
      ComputeNextQ(&stats);
      if (fabs(stats.dq) <= DQ_LIMIT) break;
    }
  }
  if (!do_search || !stats.do_size_search) {
    // Need to finalize probas now, since it wasn't done during the search.
    FinalizeSkipProba(enc);
    FinalizeTokenProbas(&enc->proba);
  }
  VP8CalculateLevelCosts(&enc->proba);  // finalize costs
  return WebPReportProgress(enc->pic, final_percent, &enc->percent);
}

//------------------------------------------------------------------------------
// Main loops
//

static const uint8_t kAverageBytesPerMB[8] = {50, 24, 16, 9, 7, 5, 3, 2};

static int PreLoopInitialize(VP8Encoder* const enc) {
  int p;
  int ok = 1;
  const int average_bytes_per_MB = kAverageBytesPerMB[enc->base_quant >> 4];
  const int bytes_per_parts =
      enc->mb_w * enc->mb_h * average_bytes_per_MB / enc->num_parts;
  // Initialize the bit-writers
  for (p = 0; ok && p < enc->num_parts; ++p) {
    ok = VP8BitWriterInit(enc->parts + p, bytes_per_parts);
  }
  if (!ok) {
    VP8EncFreeBitWriters(enc);  // malloc error occurred
    return WebPEncodingSetError(enc->pic, VP8_ENC_ERROR_OUT_OF_MEMORY);
  }
  return ok;
}

static int PostLoopFinalize(VP8EncIterator* const it, int ok) {
  VP8Encoder* const enc = it->enc;
  if (ok) {  // Finalize the partitions, check for extra errors.
    int p;
    for (p = 0; p < enc->num_parts; ++p) {
      VP8BitWriterFinish(enc->parts + p);
      ok &= !enc->parts[p].error;
    }
  }

  if (ok) {  // All good. Finish up.
#if !defined(WEBP_DISABLE_STATS)
    if (enc->pic->stats != NULL) {  // finalize byte counters...
      int i, s;
      for (i = 0; i <= 2; ++i) {
        for (s = 0; s < NUM_MB_SEGMENTS; ++s) {
          enc->residual_bytes[i][s] = (int)((it->bit_count[s][i] + 7) >> 3);
        }
      }
    }
#endif
    VP8AdjustFilterStrength(it);  // ...and store filter stats.
  } else {
    // Something bad happened -> need to do some memory cleanup.
    VP8EncFreeBitWriters(enc);
    return WebPEncodingSetError(enc->pic, VP8_ENC_ERROR_OUT_OF_MEMORY);
  }
  return ok;
}

//------------------------------------------------------------------------------
//  VP8EncLoop(): does the final bitstream coding.

static void ResetAfterSkip(VP8EncIterator* const it) {
  if (it->mb->type == 1) {
    *it->nz = 0;  // reset all predictors
    it->left_nz[8] = 0;
  } else {
    *it->nz &= (1 << 24);  // preserve the dc_nz bit
  }
}

int VP8EncLoop(VP8Encoder* const enc) {
  VP8EncIterator it;
  int ok = PreLoopInitialize(enc);
  uint64_t profile_start;
  if (!ok) return 0;

  profile_start = WebPProfileStageBegin(WEBP_PROFILE_LOSSY_STAT_LOOP);
  StatLoop(enc);  // stats-collection loop
  WebPProfileStageEnd(WEBP_PROFILE_LOSSY_STAT_LOOP, profile_start);

  VP8IteratorInit(enc, &it);
  VP8InitFilter(&it);
  do {
    VP8ModeScore info;
    const int dont_use_skip = !enc->proba.use_skip_proba;
    const VP8RDLevel rd_opt = enc->rd_opt_level;

    VP8IteratorImport(&it, NULL);
    // Warning! order is important: first call VP8Decimate() and
    // *then* decide how to code the skip decision if there's one.
    if (!VP8Decimate(&it, &info, rd_opt) || dont_use_skip) {
      CodeResiduals(it.bw, &it, &info);
      if (it.bw->error) {
        // enc->pic->error_code is set in PostLoopFinalize().
        ok = 0;
        break;
      }
    } else {  // reset predictors after a skip
      ResetAfterSkip(&it);
    }
    StoreSideInfo(&it);
    VP8StoreFilterStats(&it);
    VP8IteratorExport(&it);
    ok = VP8IteratorProgress(&it, 20);
    VP8IteratorSaveBoundary(&it);
  } while (ok && VP8IteratorNext(&it));

  return PostLoopFinalize(&it, ok);
}

//------------------------------------------------------------------------------
// Single pass using Token Buffer.

#if !defined(DISABLE_TOKEN_BUFFER)

#define MIN_COUNT 96  // minimum number of macroblocks before updating stats

typedef struct {
  VP8TBuffer* tokens;
  VP8BitWriter* bw;
  const uint8_t* probas;
} TokenEmitJob;

static int TokenEmitJobHook(void* arg1, void* arg2) {
  TokenEmitJob* const job = (TokenEmitJob*)arg1;
  (void)arg2;
  return VP8EmitTokens(job->tokens, job->bw, job->probas, 1);
}

// Emits every token partition; partitions past the first run on worker
// threads (the partition contents do not depend on the thread schedule).
// WEBP_TOKEN_EMIT_THREADS=0 forces serial emission.
static int EmitTokenPartitions(VP8Encoder* const enc) {
  const uint8_t* const probas = (const uint8_t*)enc->proba.coeffs;
  const int num_parts = enc->num_parts;
  const WebPWorkerInterface* const worker_interface = WebPGetWorkerInterface();
  WebPWorker workers[MAX_NUM_PARTITIONS];
  TokenEmitJob jobs[MAX_NUM_PARTITIONS];
  int started = 0;
  int ok = 1;
  int use_threads = (num_parts > 1);
  int p;
  {
    const char* const env = getenv("WEBP_TOKEN_EMIT_THREADS");
    if (env != NULL && !strcmp(env, "0")) use_threads = 0;
  }
  for (p = 0; p < num_parts; ++p) {
    jobs[p].tokens = &enc->tokens[p];
    jobs[p].bw = enc->parts + p;
    jobs[p].probas = probas;
  }
  if (use_threads) {
    for (p = 1; p < num_parts; ++p) {
      WebPWorker* const worker = &workers[p];
      worker_interface->Init(worker);
      worker->data1 = &jobs[p];
      worker->data2 = NULL;
      worker->hook = TokenEmitJobHook;
      if (!worker_interface->Reset(worker)) {
        worker_interface->End(worker);
        break;  // no thread: this and later partitions emit on this thread
      }
      worker_interface->Launch(worker);
      ++started;
    }
  }
  ok &= TokenEmitJobHook(&jobs[0], NULL);
  for (p = 1 + started; p < num_parts; ++p) {
    ok &= TokenEmitJobHook(&jobs[p], NULL);
  }
  for (p = 1; p <= started; ++p) {
    ok &= worker_interface->Sync(&workers[p]);
    worker_interface->End(&workers[p]);
  }
  return ok;
}

int VP8EncTokenLoop(VP8Encoder* const enc) {
  // This fork does not refresh the cost tables mid-pass. Upstream refreshes
  // them roughly eight times per pass, which serializes macroblock decisions
  // on the token statistics of earlier rows and caps accelerated wavefront
  // parallelism at the refresh-band height. Measured on the publication
  // corpus, removing the refresh changes compressed sizes by under one
  // percent in either direction (photos slightly smaller, textures slightly
  // larger); the emitted probabilities are still finalized from full-image
  // statistics before tokens are written. WEBP_TOKEN_REFRESH_SHIFT=3
  // restores the upstream cadence for comparison.
  int max_count = enc->mb_w * enc->mb_h;
  {
    const char* const refresh_shift = getenv("WEBP_TOKEN_REFRESH_SHIFT");
    if (refresh_shift != NULL) {
      const int shift = atoi(refresh_shift);
      if (shift > 0 && shift < 31) max_count >>= shift;
    }
  }
  int num_pass_left = enc->config->pass;
  int remaining_progress = 40;  // percents
  const int do_search = enc->do_search;
  VP8EncIterator it;
  VP8EncProba* const proba = &enc->proba;
  const VP8RDLevel rd_opt = enc->rd_opt_level;
  const uint64_t pixel_count = (uint64_t)enc->mb_w * enc->mb_h * 384;
  PassStats stats;
  int ok;

  InitPassStats(enc, &stats);
  ok = PreLoopInitialize(enc);
  if (!ok) return 0;

  if (max_count < MIN_COUNT) max_count = MIN_COUNT;

  assert(enc->num_parts >= 1 && enc->num_parts <= MAX_NUM_PARTITIONS);
  assert(enc->use_tokens);
  assert(proba->use_skip_proba == 0);
  assert(rd_opt >= RD_OPT_BASIC);  // otherwise, token-buffer won't be useful
  assert(num_pass_left > 0);

  while (ok && num_pass_left-- > 0) {
    const int is_last_pass = (fabs(stats.dq) <= DQ_LIMIT) ||
                             (num_pass_left == 0) ||
                             (enc->max_i4_header_bits == 0);
    uint64_t size_p0 = 0;
    uint64_t distortion = 0;
    int cnt = max_count;
    AcceleratedDecimatePass accel_pass;
    int accelerated;
    // The final number of passes is not trivial to know in advance.
    const int pass_progress = remaining_progress / (2 + num_pass_left);
    remaining_progress -= pass_progress;
    VP8IteratorInit(enc, &it);
    SetLoopParams(enc, stats.q);
    if (is_last_pass) {
      ResetTokenStats(enc);
      VP8InitFilter(&it);  // don't collect stats until last pass (too costly)
    }
    {
      int p;
      for (p = 0; p < enc->num_parts; ++p) VP8TBufferClear(&enc->tokens[p]);
    }
    {
      const uint64_t accel_start =
          WebPProfileStageBegin(WEBP_PROFILE_LOSSY_DECIMATE);
      accelerated = TryAcceleratedDecimate(enc, &accel_pass);
      WebPProfileStageEnd(WEBP_PROFILE_LOSSY_DECIMATE, accel_start);
    }
    do {
      VP8ModeScore info;
      {
        const uint64_t import_start =
            WebPProfileStageBegin(WEBP_PROFILE_LOSSY_ITER_IMPORT);
        VP8IteratorImport(&it, NULL);
        WebPProfileStageEnd(WEBP_PROFILE_LOSSY_ITER_IMPORT, import_start);
      }
      if (--cnt < 0) {
        FinalizeTokenProbas(proba);
        VP8CalculateLevelCosts(proba);  // refresh cost tables for rd-opt
        cnt = max_count;
      }
      {
        const uint64_t decimate_start =
            WebPProfileStageBegin(WEBP_PROFILE_LOSSY_DECIMATE);
        if (accelerated &&
            !AcceleratedDecimateEnsureRow(enc, &accel_pass, it.y)) {
          // A band collection failed; the replayed state is complete up to
          // this macroblock, so the CPU search continues seamlessly. Stop
          // the recorder first so the CPU path appends tokens after it.
          AcceleratedDecimateSyncRecorder(&accel_pass);
          if (accel_pass.record_pipeline) {
            // With pipelined recording the main thread skipped the inline
            // RecordTokens that maintains the iterator's packed nz words;
            // the recorder's shadow row is exactly the last recorded row
            // (the one above this fallback row), so install it before the
            // CPU search reads its top contexts. Fallback lands on a band
            // boundary, so a row start needs no partial-row left state.
            memcpy(enc->nz, accel_pass.record_nz,
                   (size_t)enc->mb_w * sizeof(*enc->nz));
          }
          accelerated = 0;
        }
        if (accelerated) {
          VP8ReplayDecimate(&it, &info,
                            &accel_pass.results[it.y * enc->mb_w + it.x],
                            accel_pass.recon_y, accel_pass.recon_u,
                            accel_pass.recon_v, accel_pass.recon_y_stride,
                            accel_pass.recon_uv_stride);
        } else {
          VP8Decimate(&it, &info, rd_opt);
        }
        WebPProfileStageEnd(WEBP_PROFILE_LOSSY_DECIMATE, decimate_start);
      }
      {
        const uint64_t record_start =
            WebPProfileStageBegin(WEBP_PROFILE_LOSSY_RECORD_TOKENS);
        if (accelerated && accel_pass.record_pipeline) {
          ok = accel_pass.record_ok;  // the worker records this band
        } else if (accel_pass.record_pipeline && !accel_pass.record_ok) {
          ok = 0;  // pipelined recording failed before the CPU fallback
        } else {
          ok = RecordTokens(&it, &info,
                            &enc->tokens[it.y & (enc->num_parts - 1)]);
        }
        WebPProfileStageEnd(WEBP_PROFILE_LOSSY_RECORD_TOKENS, record_start);
      }
      if (!ok) {
        WebPEncodingSetError(enc->pic, VP8_ENC_ERROR_OUT_OF_MEMORY);
        break;
      }
      size_p0 += info.H;
      distortion += info.D;
      if (is_last_pass) {
        const uint64_t side_start =
            WebPProfileStageBegin(WEBP_PROFILE_LOSSY_SIDE_INFO);
        StoreSideInfo(&it);
        VP8StoreFilterStats(&it);
        VP8IteratorExport(&it);
        ok = VP8IteratorProgress(&it, pass_progress);
        WebPProfileStageEnd(WEBP_PROFILE_LOSSY_SIDE_INFO, side_start);
      }
      {
        const uint64_t boundary_start =
            WebPProfileStageBegin(WEBP_PROFILE_LOSSY_SAVE_BOUNDARY);
        VP8IteratorSaveBoundary(&it);
        WebPProfileStageEnd(WEBP_PROFILE_LOSSY_SAVE_BOUNDARY, boundary_start);
      }
    } while (ok && VP8IteratorNext(&it));
    if (ok && accel_pass.record_pipeline &&
        !AcceleratedDecimateSyncRecorder(&accel_pass)) {
      ok = WebPEncodingSetError(enc->pic, VP8_ENC_ERROR_OUT_OF_MEMORY);
    }
    AcceleratedDecimateClear(&accel_pass);
    if (!ok) break;

    size_p0 += enc->segment_hdr.size;
    if (stats.do_size_search) {
      uint64_t size = FinalizeTokenProbas(&enc->proba);
      int p;
      for (p = 0; p < enc->num_parts; ++p) {
        size += VP8EstimateTokenSize(&enc->tokens[p],
                                     (const uint8_t*)proba->coeffs);
      }
      size = (size + size_p0 + 1024) >> 11;  // -> size in bytes
      size += HEADER_SIZE_ESTIMATE;
      stats.value = (double)size;
    } else {  // compute and store PSNR
      stats.value = GetPSNR(distortion, pixel_count);
    }

#if (DEBUG_SEARCH > 0)
    printf(
        "#%2d metric:%.1lf -> %.1lf   last_q=%.2lf q=%.2lf dq=%.2lf "
        " range:[%.1f, %.1f]\n",
        num_pass_left, stats.last_value, stats.value, stats.last_q, stats.q,
        stats.dq, stats.qmin, stats.qmax);
#endif
    if (enc->max_i4_header_bits > 0 && size_p0 > PARTITION0_SIZE_LIMIT) {
      ++num_pass_left;
      enc->max_i4_header_bits >>= 1;  // strengthen header bit limitation...
      if (is_last_pass) {
        ResetSideInfo(&it);
      }
      continue;  // ...and start over
    }
    if (is_last_pass) {
      break;  // done
    }
    if (do_search) {
      ComputeNextQ(&stats);  // Adjust q
    }
  }
  if (ok) {
    const uint64_t emit_start =
        WebPProfileStageBegin(WEBP_PROFILE_LOSSY_EMIT_TOKENS);
    if (!stats.do_size_search) {
      FinalizeTokenProbas(&enc->proba);
    }
    ok = EmitTokenPartitions(enc);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSY_EMIT_TOKENS, emit_start);
  }
  ok = ok && WebPReportProgress(enc->pic, enc->percent + remaining_progress,
                                &enc->percent);
  {
    const uint64_t post_start =
        WebPProfileStageBegin(WEBP_PROFILE_LOSSY_POST_LOOP);
    ok = PostLoopFinalize(&it, ok);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSY_POST_LOOP, post_start);
    return ok;
  }
}

#else

int VP8EncTokenLoop(VP8Encoder* const enc) {
  (void)enc;
  return 0;  // we shouldn't be here.
}

#endif  // DISABLE_TOKEN_BUFFER

//------------------------------------------------------------------------------
