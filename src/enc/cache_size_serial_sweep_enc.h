// Copyright 2026
//
// Private interface for the cache-size serial-sweep implementation experiment.

#ifndef WEBP_ENC_CACHE_SIZE_SERIAL_SWEEP_ENC_H_
#define WEBP_ENC_CACHE_SIZE_SERIAL_SWEEP_ENC_H_

#include <stdint.h>

#include "src/enc/backward_references_enc.h"

#ifdef __cplusplus
extern "C" {
#endif

// Returns 1 when the candidate is explicitly enabled, 0 when it is off, and
// -1 when an invalid opt-in or missing exclusive benchmark session is refused.
int VP8LCacheSizeSerialSweepRuntimeState(void);

// Candidate for CalculateBestCacheSize(). Returns 0 on allocation or injected
// failure. *best_cache_bits is changed only on success.
int VP8LCalculateBestCacheSizeSerialSweep(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* refs,
    int* best_cache_bits);

// Candidate-build-only test hook. It executes the unmodified baseline and the
// candidate independently over the same immutable inputs.
int VP8LCompareCacheSizeSearchForTest(
    const uint32_t* argb, int quality, const VP8LBackwardRefs* refs,
    int cache_bits_max, int* baseline_bits, int* candidate_bits);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_CACHE_SIZE_SERIAL_SWEEP_ENC_H_
