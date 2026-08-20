// Copyright 2026
//
// Private container policy shared by the CUDA transcoding tools and tests.

#ifndef WEBP_TOOLS_CUDA_TRANSCODE_COMMON_H_
#define WEBP_TOOLS_CUDA_TRANSCODE_COMMON_H_

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE = 0,
  WEBP_TRANSCODE_INPUT_MALFORMED,
  WEBP_TRANSCODE_INPUT_LOSSLESS,
  WEBP_TRANSCODE_INPUT_ALPHA,
  WEBP_TRANSCODE_INPUT_ANIMATION,
  WEBP_TRANSCODE_INPUT_MULTIPLE_IMAGES
} WebPTranscodeInputStatus;

typedef struct {
  const uint8_t* bytes;
  size_t size;
} WebPTranscodeChunk;

typedef struct {
  WebPTranscodeInputStatus status;
  const char* reason;
  int width;
  int height;
  WebPTranscodeChunk vp8;
  WebPTranscodeChunk iccp;
  WebPTranscodeChunk exif;
  WebPTranscodeChunk xmp;
} WebPTranscodeInput;

// Strictly parses one complete RIFF WebP object. Only a single opaque lossy
// VP8 image is NVDEC-eligible. ICCP, EXIF, and XMP payloads are borrowed for
// byte-exact copying to the output; all other valid inputs receive a stable
// decline reason and remain eligible for a full CPU fallback.
int WebPTranscodeParseInput(const uint8_t* data, size_t size,
                            WebPTranscodeInput* input);

const char* WebPTranscodeInputStatusName(WebPTranscodeInputStatus status);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_TOOLS_CUDA_TRANSCODE_COMMON_H_
