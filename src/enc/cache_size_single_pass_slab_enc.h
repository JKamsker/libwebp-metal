// Copyright 2026
//
// Private interface for the cache-size single-pass slab experiment.

#ifndef WEBP_ENC_CACHE_SIZE_SINGLE_PASS_SLAB_ENC_H_
#define WEBP_ENC_CACHE_SIZE_SINGLE_PASS_SLAB_ENC_H_

#include <stddef.h>
#include <stdint.h>

#include "src/enc/backward_references_enc.h"

#ifdef __cplusplus
extern "C" {
#endif

// Returns 1 only for an exact, leased opt-in, 0 when absent, and -1 when an
// invalid opt-in or missing exclusive benchmark session is refused.
int VP8LCacheSizeSinglePassSlabRuntimeState(void);

// Single-reference-pass candidate for CalculateBestCacheSize(). On failure,
// *best_cache_bits is unchanged.
int VP8LCalculateBestCacheSizeSinglePassSlab(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* refs,
    int* best_cache_bits);

// Candidate-build-only test hooks. No installed or public header exposes them.
int VP8LCompareCacheSizeSinglePassSlabForTest(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* refs,
    int cache_bits_max, int* baseline_bits, int* candidate_bits);
int VP8LCacheSizeSinglePassSlabLayoutForTest(
    int cache_bits_max, size_t* slab_bytes, int* histogram_count,
    int* cache_count);
int VP8LCacheSizeSinglePassSlabAllocationForTest(int cache_bits_max);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_CACHE_SIZE_SINGLE_PASS_SLAB_ENC_H_
