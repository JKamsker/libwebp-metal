// Copyright 2026
//
// One-pass, one-allocation color-cache size search experiment.

#include "src/enc/cache_size_single_pass_slab_enc.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dsp/lossless_common.h"
#include "src/enc/histogram_enc.h"
#include "src/utils/color_cache_utils.h"
#include "src/utils/utils.h"
#include "src/webp/format_constants.h"

typedef struct {
  VP8LHistogram* histograms[MAX_COLOR_CACHE_BITS + 1];
  VP8LColorCache caches[MAX_COLOR_CACHE_BITS + 1];
  size_t bytes;
} CacheSizeSlab;

static int ExactEnvironmentValue(const char* const name,
                                 const char* const expected) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, expected) == 0;
}

int VP8LCacheSizeSinglePassSlabRuntimeState(void) {
  const char* const value =
      getenv("WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT");
  if (value == NULL) return 0;
  if (strcmp(value, "1") != 0) {
    fprintf(stderr,
            "cache-size single-pass slab experiment refuses invalid "
            "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT (expected exact "
            "value 1)\n");
    return -1;
  }
  if (!ExactEnvironmentValue("WEBP_BENCHMARK_SESSION", "exclusive")) {
    fprintf(stderr,
            "cache-size single-pass slab experiment refuses activation "
            "without WEBP_BENCHMARK_SESSION=exclusive\n");
    return -1;
  }
  return 1;
}

static size_t SlabBytes(int cache_bits_max) {
  uint64_t bytes = sizeof(CacheSizeSlab) + WEBP_ALIGN_CST;
  int i;
  for (i = 0; i <= cache_bits_max; ++i) {
    bytes += WEBP_ALIGN_CST + sizeof(VP8LHistogram);
    bytes += (uint64_t)VP8LHistogramNumCodes(i) * sizeof(uint32_t);
  }
  for (i = 1; i <= cache_bits_max; ++i) {
    bytes += WEBP_ALIGN_CST;
    bytes += ((uint64_t)1u << i) * sizeof(uint32_t);
  }
  return CheckSizeOverflow(bytes) ? (size_t)bytes : 0;
}

int VP8LCacheSizeSinglePassSlabLayoutForTest(
    int cache_bits_max, size_t* const slab_bytes,
    int* const histogram_count, int* const cache_count) {
  if (cache_bits_max < 0 || cache_bits_max > MAX_COLOR_CACHE_BITS ||
      slab_bytes == NULL || histogram_count == NULL || cache_count == NULL) {
    return 0;
  }
  *slab_bytes = SlabBytes(cache_bits_max);
  *histogram_count = cache_bits_max + 1;
  *cache_count = cache_bits_max;
  return *slab_bytes != 0;
}

static CacheSizeSlab* AllocateSlab(int cache_bits_max) {
  const size_t bytes = SlabBytes(cache_bits_max);
  CacheSizeSlab* slab;
  uint8_t* cursor;
  int i;
  if (bytes == 0 || ExactEnvironmentValue(
                        "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_INJECT_FAILURE",
                        "1")) {
    return NULL;
  }
  // This is the candidate's only dynamic allocation and the only zero-fill.
  // Histograms, variable literal arrays, and all cache colors share it.
  slab = (CacheSizeSlab*)WebPSafeCalloc(1, bytes);
  if (slab == NULL) return NULL;
  slab->bytes = bytes;
  cursor = (uint8_t*)WEBP_ALIGN(slab + 1);
  for (i = 0; i <= cache_bits_max; ++i) {
    VP8LHistogram* histogram;
    cursor = (uint8_t*)WEBP_ALIGN(cursor);
    histogram = (VP8LHistogram*)cursor;
    cursor += sizeof(*histogram);
    histogram->literal = (uint32_t*)cursor;
    cursor += (size_t)VP8LHistogramNumCodes(i) * sizeof(*histogram->literal);
    VP8LHistogramInit(histogram, i, /*init_arrays=*/0);
    slab->histograms[i] = histogram;
  }
  for (i = 1; i <= cache_bits_max; ++i) {
    VP8LColorCache* const cache = &slab->caches[i];
    cursor = (uint8_t*)WEBP_ALIGN(cursor);
    cache->colors = (uint32_t*)cursor;
    cursor += ((size_t)1u << i) * sizeof(*cache->colors);
    cache->hash_bits = i;
    cache->hash_shift = 32 - i;
  }
  assert((size_t)(cursor - (uint8_t*)slab) <= slab->bytes);
  return slab;
}

int VP8LCacheSizeSinglePassSlabAllocationForTest(int cache_bits_max) {
  CacheSizeSlab* slab;
  if (cache_bits_max < 0 || cache_bits_max > MAX_COLOR_CACHE_BITS) return 0;
  slab = AllocateSlab(cache_bits_max);
  if (slab == NULL) return 0;
  WebPSafeFree(slab);
  return 1;
}

int VP8LCalculateBestCacheSizeSinglePassSlab(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* const refs,
    int* const best_cache_bits) {
  const int cache_bits_max = (quality <= 25) ? 0 : *best_cache_bits;
  uint64_t entropy_min = WEBP_UINT64_MAX;
  CacheSizeSlab* slab;
  VP8LRefsCursor c;
  int best_bits = 0;
  int i;

  assert(argb != NULL);
  assert(refs != NULL);
  assert(best_cache_bits != NULL);
  assert(cache_bits_max >= 0 && cache_bits_max <= MAX_COLOR_CACHE_BITS);
  if (cache_bits_max == 0) {
    *best_cache_bits = 0;
    return 1;
  }
  slab = AllocateSlab(cache_bits_max);
  if (slab == NULL) return 0;
  c = VP8LRefsCursorInit(refs);

  // Preserve upstream's single traversal, simultaneous cache states, key
  // derivation, update order, and copy-color suppression exactly.
  while (VP8LRefsCursorOk(&c)) {
    const PixOrCopy* const v = c.cur_pos;
    if (PixOrCopyIsLiteral(v)) {
      const uint32_t pix = *argb++;
      const uint32_t a = (pix >> 24) & 0xff;
      const uint32_t r = (pix >> 16) & 0xff;
      const uint32_t g = (pix >> 8) & 0xff;
      const uint32_t b = pix & 0xff;
      int key = VP8LHashPix(pix, 32 - cache_bits_max);
      ++slab->histograms[0]->blue[b];
      ++slab->histograms[0]->literal[g];
      ++slab->histograms[0]->red[r];
      ++slab->histograms[0]->alpha[a];
      for (i = cache_bits_max; i >= 1; --i, key >>= 1) {
        VP8LHistogram* const histogram = slab->histograms[i];
        VP8LColorCache* const cache = &slab->caches[i];
        if (VP8LColorCacheLookup(cache, key) == pix) {
          ++histogram->literal[NUM_LITERAL_CODES + NUM_LENGTH_CODES + key];
        } else {
          VP8LColorCacheSet(cache, key, pix);
          ++histogram->blue[b];
          ++histogram->literal[g];
          ++histogram->red[r];
          ++histogram->alpha[a];
        }
      }
    } else {
      int code, extra_bits, extra_bits_value;
      int len = (int)PixOrCopyLength(v);
      uint32_t argb_prev = *argb ^ 0xffffffffu;
      VP8LPrefixEncode(len, &code, &extra_bits, &extra_bits_value);
      for (i = 0; i <= cache_bits_max; ++i) {
        ++slab->histograms[i]->literal[NUM_LITERAL_CODES + code];
      }
      do {
        if (*argb != argb_prev) {
          int key = VP8LHashPix(*argb, 32 - cache_bits_max);
          for (i = cache_bits_max; i >= 1; --i, key >>= 1) {
            slab->caches[i].colors[key] = *argb;
          }
          argb_prev = *argb;
        }
        ++argb;
      } while (--len != 0);
    }
    VP8LRefsCursorNext(&c);
  }

  for (i = 0; i <= cache_bits_max; ++i) {
    const uint64_t entropy =
        VP8LHistogramEstimateBits(slab->histograms[i]);
    if (i == 0 || entropy < entropy_min) {
      entropy_min = entropy;
      best_bits = i;
    }
  }
  WebPSafeFree(slab);
  *best_cache_bits = best_bits;
  return 1;
}
