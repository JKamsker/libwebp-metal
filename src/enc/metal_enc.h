// Copyright 2026
//
// Internal entry points for optional Metal encoder acceleration.

#ifndef WEBP_ENC_METAL_ENC_H_
#define WEBP_ENC_METAL_ENC_H_

#include <stdint.h>

#include "src/webp/encode.h"

#ifdef __cplusplus
extern "C" {
#endif

// Returns 1 when Metal produced the transformed pixels and transform image.
// Returns 0 without modifying the caller's buffers when the Metal path is not
// available or encounters a recoverable failure.
int VP8LColorSpaceTransformMetal(int width, int height, int bits, int quality,
                                 uint32_t* argb, uint32_t* image);

// Returns 1 when Metal produced candidates for every pixel. Returns 0 to use
// the existing CPU candidate search.
int VP8LHashChainFillMetalCandidates(const uint32_t* pixels,
                                     const int32_t* chain, int size,
                                     int xsize, int iter_max,
                                     uint32_t window_size, int low_effort,
                                     uint32_t* candidates);

// Returns 1 when Metal populated the already allocated Y/U/V planes. Returns
// 0 to use libwebp's normal conversion.
int WebPImportRGBToYUVAMetal(const uint8_t* red, const uint8_t* green,
                             const uint8_t* blue, int step,
                             int source_stride, WebPPicture* picture);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_METAL_ENC_H_
