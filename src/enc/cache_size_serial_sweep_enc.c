// Copyright 2026
//
// Cache-resident serial sweep for the lossless color-cache size search.

#include "src/enc/cache_size_serial_sweep_enc.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dsp/lossless_common.h"
#include "src/enc/histogram_enc.h"
#include "src/utils/color_cache_utils.h"
#include "src/utils/utils.h"
#include "src/webp/format_constants.h"

static int ExactEnvironmentValue(const char* const name,
                                 const char* const expected) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, expected) == 0;
}

int VP8LCacheSizeSerialSweepRuntimeState(void) {
  const char* const value =
      getenv("WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT");
  if (value == NULL) return 0;
  if (strcmp(value, "1") != 0) {
    fprintf(stderr,
            "cache-size serial-sweep experiment refuses invalid "
            "WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT (expected exact value "
            "1)\n");
    return -1;
  }
  if (!ExactEnvironmentValue("WEBP_BENCHMARK_SESSION", "exclusive")) {
    fprintf(stderr,
            "cache-size serial-sweep experiment refuses activation without "
            "WEBP_BENCHMARK_SESSION=exclusive\n");
    return -1;
  }
  return 1;
}

int VP8LCalculateBestCacheSizeSerialSweep(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* const refs,
    int* const best_cache_bits) {
  const int cache_bits_max = (quality <= 25) ? 0 : *best_cache_bits;
  VP8LHistogram* histo = NULL;
  VP8LColorCache hasher;
  uint64_t entropy_min = WEBP_UINT64_MAX;
  int hasher_init = 0;
  int best_bits = 0;
  int cache_bits;
  int ok = 0;

  assert(argb != NULL);
  assert(refs != NULL);
  assert(best_cache_bits != NULL);
  assert(cache_bits_max >= 0 && cache_bits_max <= MAX_COLOR_CACHE_BITS);

  if (cache_bits_max == 0) {
    *best_cache_bits = 0;
    return 1;
  }
  if (ExactEnvironmentValue(
          "WEBP_CACHE_SIZE_SERIAL_SWEEP_INJECT_FAILURE", "1")) {
    return 0;
  }

  // One maximum-sized histogram and one maximum-sized cache are reused for
  // every candidate. The baseline keeps all candidates live together. This
  // serial organization exchanges repeated immutable reference traversal for
  // a single-candidate working set and two allocations instead of 2 * max + 1.
  histo = VP8LAllocateHistogram(cache_bits_max);
  if (histo == NULL) goto Error;
  hasher_init = VP8LColorCacheInit(&hasher, cache_bits_max);
  if (!hasher_init) goto Error;

  for (cache_bits = 0; cache_bits <= cache_bits_max; ++cache_bits) {
    const uint32_t* argb_cursor = argb;
    VP8LRefsCursor c = VP8LRefsCursorInit(refs);
    VP8LHistogramInit(histo, cache_bits, /*init_arrays=*/1);
    if (cache_bits > 0) {
      hasher.hash_bits = cache_bits;
      hasher.hash_shift = 32 - cache_bits;
      memset(hasher.colors, 0,
             ((size_t)1u << cache_bits) * sizeof(*hasher.colors));
    }

    while (VP8LRefsCursorOk(&c)) {
      const PixOrCopy* const v = c.cur_pos;
      if (PixOrCopyIsLiteral(v)) {
        const uint32_t pix = *argb_cursor++;
        const uint32_t a = (pix >> 24) & 0xff;
        const uint32_t r = (pix >> 16) & 0xff;
        const uint32_t g = (pix >> 8) & 0xff;
        const uint32_t b = pix & 0xff;
        if (cache_bits == 0) {
          ++histo->blue[b];
          ++histo->literal[g];
          ++histo->red[r];
          ++histo->alpha[a];
        } else {
          const int key = VP8LHashPix(pix, hasher.hash_shift);
          if (VP8LColorCacheLookup(&hasher, key) == pix) {
            ++histo->literal[NUM_LITERAL_CODES + NUM_LENGTH_CODES + key];
          } else {
            VP8LColorCacheSet(&hasher, key, pix);
            ++histo->blue[b];
            ++histo->literal[g];
            ++histo->red[r];
            ++histo->alpha[a];
          }
        }
      } else {
        int code, extra_bits, extra_bits_value;
        int len = (int)PixOrCopyLength(v);
        VP8LPrefixEncode(len, &code, &extra_bits, &extra_bits_value);
        ++histo->literal[NUM_LITERAL_CODES + code];
        if (cache_bits == 0) {
          argb_cursor += len;
        } else {
          uint32_t argb_prev = *argb_cursor ^ 0xffffffffu;
          do {
            if (*argb_cursor != argb_prev) {
              VP8LColorCacheInsert(&hasher, *argb_cursor);
              argb_prev = *argb_cursor;
            }
            ++argb_cursor;
          } while (--len != 0);
        }
      }
      VP8LRefsCursorNext(&c);
    }

    {
      const uint64_t entropy = VP8LHistogramEstimateBits(histo);
      // Strict comparison and ascending candidate order preserve baseline ties.
      if (cache_bits == 0 || entropy < entropy_min) {
        entropy_min = entropy;
        best_bits = cache_bits;
      }
    }
  }
  *best_cache_bits = best_bits;
  ok = 1;

Error:
  if (hasher_init) VP8LColorCacheClear(&hasher);
  VP8LFreeHistogram(histo);
  return ok;
}
