// Copyright 2026
//
// Internal, opt-in encoder stage profiling.

#ifndef WEBP_ENC_PROFILE_ENC_H_
#define WEBP_ENC_PROFILE_ENC_H_

#include <stddef.h>
#include <stdint.h>

#include "src/webp/encode.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_PROFILE_LOSSLESS_PREPARE = 0,
  WEBP_PROFILE_LOSSLESS_CONTAINER_SETUP,
  WEBP_PROFILE_LOSSLESS_ANALYZE,
  WEBP_PROFILE_LOSSLESS_ENCODER_INIT,
  WEBP_PROFILE_LOSSLESS_PALETTE,
  WEBP_PROFILE_LOSSLESS_INPUT_COPY,
  WEBP_PROFILE_LOSSLESS_SUBTRACT_GREEN,
  WEBP_PROFILE_LOSSLESS_PREDICTOR,
  WEBP_PROFILE_LOSSLESS_CROSS_COLOR,
  WEBP_PROFILE_LOSSLESS_HASH_CHAIN,
  WEBP_PROFILE_LOSSLESS_BACKWARD_REFS,
  WEBP_PROFILE_LOSSLESS_HISTOGRAM,
  WEBP_PROFILE_LOSSLESS_HUFFMAN,
  WEBP_PROFILE_LOSSLESS_BITSTREAM,
  WEBP_PROFILE_LOSSLESS_STREAM_FINALIZE,
  WEBP_PROFILE_LOSSLESS_RIFF_WRITE,
  WEBP_PROFILE_METAL_INIT,
  WEBP_PROFILE_METAL_CROSS_COLOR_DISPATCH,
  WEBP_PROFILE_METAL_HASH_PIPELINE_INIT,
  WEBP_PROFILE_METAL_HASH_DISPATCH,
  WEBP_PROFILE_LOSSY_IMPORT,
  WEBP_PROFILE_LOSSY_ENCODER_INIT,
  WEBP_PROFILE_LOSSY_ANALYZE,
  WEBP_PROFILE_LOSSY_STAT_LOOP,
  WEBP_PROFILE_LOSSY_ENCODE_LOOP,
  WEBP_PROFILE_LOSSY_ALPHA,
  WEBP_PROFILE_LOSSY_WRITE,
  WEBP_PROFILE_STAGE_COUNT
} WebPProfileStage;

// A session is enabled only when WEBP_STAGE_PROFILE is set to a true value.
// The API is intentionally internal: normal callers pay one predictable branch
// at each coarse encoder boundary and no per-pixel instrumentation cost.
void WebPProfileBeginSession(const WebPConfig* config,
                             const WebPPicture* picture);
void WebPProfileEndSession(int ok, int error_code);
uint64_t WebPProfileStageBegin(WebPProfileStage stage);
void WebPProfileStageEnd(WebPProfileStage stage, uint64_t start_ns);
void WebPProfileSetOutputSize(size_t output_size);
void WebPProfileMarkMetalCrossColor(void);
void WebPProfileMarkMetalHash(void);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_PROFILE_ENC_H_
