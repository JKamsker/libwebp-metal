// Copyright 2026
//
// Private Metal adapter for the backend-neutral encoder accelerator interface.

#ifndef WEBP_ENC_METAL_ENC_H_
#define WEBP_ENC_METAL_ENC_H_

#include "src/enc/accelerator_enc.h"

#ifdef __cplusplus
extern "C" {
#endif

const WebPEncoderAccelerator* WebPGetMetalEncoderAccelerator(void);

// Implemented by the Metal Objective-C++ translation units and used only by
// the adapter descriptor.
int VP8LColorSpaceTransformMetal(int width, int height, int bits, int quality,
                                 uint32_t* argb, uint32_t* image);

int VP8LHashChainFillMetalCandidates(const uint32_t* pixels,
                                     const int32_t* chain, int size,
                                     int xsize, int iter_max,
                                     uint32_t window_size, int low_effort,
                                     uint32_t* candidates);

int WebPImportRGBToYUVAMetal(const uint8_t* red, const uint8_t* green,
                             const uint8_t* blue, int step,
                             int source_stride, int width, int height,
                             uint8_t* y, uint8_t* u, uint8_t* v, int y_stride,
                             int uv_stride);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_METAL_ENC_H_
