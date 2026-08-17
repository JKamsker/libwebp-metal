// Copyright 2026
//
// Private, backend-neutral encoder accelerator interface.

#ifndef WEBP_ENC_ACCELERATOR_ENC_H_
#define WEBP_ENC_ACCELERATOR_ENC_H_

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define WEBP_ENCODER_ACCELERATOR_ABI_VERSION 1u

// These are deliberately encoder stages, not low-level GPU kernels. A backend
// advertises only the stages whose complete CPU call-site contract it can
// implement.
typedef enum {
  WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM = 1u << 0,
  WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN = 1u << 1,
  WEBP_ACCELERATOR_STAGE_RGB_TO_YUV = 1u << 2
} WebPAcceleratorStage;

// SUCCESS is the only result for which a caller may consume output buffers.
// NOT_RUN covers an unavailable, disabled, or declined operation and permits
// another backend to be tried. ERROR is a recoverable accelerator failure; the
// dispatcher stops trying accelerators and the caller uses its CPU path.
typedef enum {
  WEBP_ACCELERATOR_NOT_RUN = 0,
  WEBP_ACCELERATOR_SUCCESS = 1,
  WEBP_ACCELERATOR_ERROR = 2
} WebPAcceleratorResult;

typedef enum {
  // Required by ABI v1. A callback returns only after its outputs are visible
  // to the host.
  WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS = 1u << 0,
  // Required by ABI v1. Caller-owned outputs are unchanged on NOT_RUN/ERROR.
  WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT = 1u << 1,
  // Repeated calls on one backend produce the same result for the same input.
  // This does not imply byte identity with the CPU encoder.
  WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC = 1u << 2,
  // The backend retains private device/pipeline/staging resources across calls.
  WEBP_ACCELERATOR_PROPERTY_PERSISTENT_RESOURCES = 1u << 3,
  // The backend serializes operations that share its persistent resources.
  WEBP_ACCELERATOR_PROPERTY_SERIALIZED = 1u << 4
} WebPAcceleratorProperty;

typedef struct {
  int width;
  int height;
  int bits;
  int quality;
  // Borrowed mutable buffers. argb has width * height elements and
  // transform_image has ceil(width / 2^bits) * ceil(height / 2^bits).
  uint32_t* argb;
  uint32_t* transform_image;
} WebPAcceleratorColorTransformRequest;

typedef struct {
  // Borrowed inputs with size elements.
  const uint32_t* pixels;
  const int32_t* chain;
  int size;
  int xsize;
  int iter_max;
  uint32_t window_size;
  int low_effort;
  // Borrowed mutable output with size elements.
  uint32_t* candidates;
} WebPAcceleratorHashChainRequest;

typedef struct {
  // Borrowed channel pointers into the same packed source image.
  const uint8_t* red;
  const uint8_t* green;
  const uint8_t* blue;
  int step;
  int source_stride;
  int width;
  int height;
  // Borrowed mutable WebP YUV420 planes allocated by the caller.
  uint8_t* y;
  uint8_t* u;
  uint8_t* v;
  int y_stride;
  int uv_stride;
} WebPAcceleratorRGBToYUVRequest;

typedef struct WebPEncoderAccelerator WebPEncoderAccelerator;

struct WebPEncoderAccelerator {
  uint32_t abi_version;
  size_t struct_size;
  const char* name;
  uint32_t stages;
  uint32_t properties;
  void* context;

  WebPAcceleratorResult (*color_transform)(
      void* context, const WebPAcceleratorColorTransformRequest* request);
  WebPAcceleratorResult (*hash_chain)(
      void* context, const WebPAcceleratorHashChainRequest* request);
  WebPAcceleratorResult (*rgb_to_yuv)(
      void* context, const WebPAcceleratorRGBToYUVRequest* request);

  // Optional lifecycle hooks for a future encoder-level batch boundary.
  // ABI v1 operations are synchronous, so flush may be NULL. trim may release
  // cached backend-owned buffers, but must leave the descriptor usable.
  WebPAcceleratorResult (*flush)(void* context);
  void (*trim)(void* context);
};

WebPAcceleratorResult WebPAccelerateColorTransform(
    const WebPAcceleratorColorTransformRequest* request);
WebPAcceleratorResult WebPAccelerateHashChain(
    const WebPAcceleratorHashChainRequest* request);
WebPAcceleratorResult WebPAccelerateRGBToYUV(
    const WebPAcceleratorRGBToYUVRequest* request);

#if defined(WEBP_ACCELERATOR_TESTING)
// Installs one process-global fake backend. Test programs must not call this
// concurrently with accelerator dispatch. Passing NULL clears the fake.
int WebPSetEncoderAcceleratorForTesting(
    const WebPEncoderAccelerator* backend);
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_ACCELERATOR_ENC_H_
