// Copyright 2026
//
// Metal registration for the private encoder accelerator interface.

#include "src/enc/metal_enc.h"

static WebPAcceleratorResult MetalColorTransform(
    void* context, const WebPAcceleratorColorTransformRequest* request) {
  (void)context;
  return VP8LColorSpaceTransformMetal(
             request->width, request->height, request->bits, request->quality,
             request->argb, request->transform_image)
             ? WEBP_ACCELERATOR_SUCCESS
             : WEBP_ACCELERATOR_NOT_RUN;
}

static WebPAcceleratorResult MetalHashChain(
    void* context, const WebPAcceleratorHashChainRequest* request) {
  (void)context;
  return VP8LHashChainFillMetalCandidates(
             request->pixels, request->chain, request->size, request->xsize,
             request->iter_max, request->window_size, request->low_effort,
             request->candidates)
             ? WEBP_ACCELERATOR_SUCCESS
             : WEBP_ACCELERATOR_NOT_RUN;
}

static WebPAcceleratorResult MetalRGBToYUV(
    void* context, const WebPAcceleratorRGBToYUVRequest* request) {
  (void)context;
  return WebPImportRGBToYUVAMetal(
             request->red, request->green, request->blue, request->step,
             request->source_stride, request->width, request->height,
             request->y, request->u, request->v, request->y_stride,
             request->uv_stride)
             ? WEBP_ACCELERATOR_SUCCESS
             : WEBP_ACCELERATOR_NOT_RUN;
}

const WebPEncoderAccelerator* WebPGetMetalEncoderAccelerator(void) {
  static const WebPEncoderAccelerator backend = {
      WEBP_ENCODER_ACCELERATOR_ABI_VERSION,
      sizeof(WebPEncoderAccelerator),
      "metal",
      WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM |
          WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN |
          WEBP_ACCELERATOR_STAGE_RGB_TO_YUV,
      WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |
          WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT |
          WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC |
          WEBP_ACCELERATOR_PROPERTY_PERSISTENT_RESOURCES |
          WEBP_ACCELERATOR_PROPERTY_SERIALIZED,
      NULL,
      MetalColorTransform,
      MetalHashChain,
      MetalRGBToYUV,
      NULL,
      NULL};
  return &backend;
}
