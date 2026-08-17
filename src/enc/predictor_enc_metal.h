// Copyright 2026
//
// Experimental Metal entry point for lossless predictor residuals.

#ifndef WEBP_ENC_PREDICTOR_ENC_METAL_H_
#define WEBP_ENC_PREDICTOR_ENC_METAL_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Applies the already-selected predictor map to 'argb'. This experiment only
// implements the exact (non-near-lossless) residual operation. If 'exact' is
// zero, it declines images containing fully transparent pixels because the CPU
// cleanup path has scan-order dependencies.
//
// Returns 1 only after the device has completed and the result has been copied
// back to 'argb'. Returns 0 without modifying 'argb' when disabled,
// unsupported, invalid, or after any recoverable device/validation failure.
// All pointers are borrowed for the duration of this synchronous call.
int VP8LResidualImageMetalExperimental(int width, int height, int bits,
                                       const uint32_t* modes, int exact,
                                       uint32_t* argb);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_PREDICTOR_ENC_METAL_H_
