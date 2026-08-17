// Copyright 2026

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/accelerator_enc.h"

typedef struct {
  WebPAcceleratorResult color_result;
  int color_calls;
  int hash_calls;
} FakeContext;

static WebPAcceleratorResult FakeColorTransform(
    void* opaque, const WebPAcceleratorColorTransformRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->color_calls;
  assert(request->width == 2);
  assert(request->height == 1);
  assert(request->bits == 5);
  assert(request->quality == 75);
  if (context->color_result == WEBP_ACCELERATOR_SUCCESS) {
    request->argb[0] = 0x11223344u;
    request->transform_image[0] = 0x55667788u;
  }
  return context->color_result;
}

static WebPAcceleratorResult FakeHashChain(
    void* opaque, const WebPAcceleratorHashChainRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  (void)request;
  ++context->hash_calls;
  return WEBP_ACCELERATOR_SUCCESS;
}

static WebPEncoderAccelerator MakeBackend(FakeContext* context) {
  WebPEncoderAccelerator backend;
  memset(&backend, 0, sizeof(backend));
  backend.abi_version = WEBP_ENCODER_ACCELERATOR_ABI_VERSION;
  backend.struct_size = sizeof(backend);
  backend.name = "fake";
  backend.stages = WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM;
  backend.properties = WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |
                       WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT |
                       WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC;
  backend.context = context;
  backend.color_transform = FakeColorTransform;
  backend.hash_chain = FakeHashChain;
  return backend;
}

int main(void) {
  FakeContext context;
  WebPEncoderAccelerator backend;
  uint32_t argb[2] = {1u, 2u};
  uint32_t transform_image[1] = {3u};
  const WebPAcceleratorColorTransformRequest color_request = {
      2, 1, 5, 75, argb, transform_image};
  const uint32_t pixels[3] = {1u, 2u, 3u};
  const int32_t chain[3] = {-1, 0, 1};
  uint32_t candidates[3] = {4u, 5u, 6u};
  const WebPAcceleratorHashChainRequest hash_request = {
      pixels, chain, 3, 3, 8, 32u, 0, candidates};

  memset(&context, 0, sizeof(context));
  backend = MakeBackend(&context);
  if (getenv("WEBP_ACCELERATOR") != NULL &&
      strcmp(getenv("WEBP_ACCELERATOR"), "none") == 0) {
    assert(WebPSetEncoderAcceleratorForTesting(&backend));
    assert(WebPAccelerateColorTransform(&color_request) ==
           WEBP_ACCELERATOR_NOT_RUN);
    assert(context.color_calls == 0);
    assert(argb[0] == 1u && transform_image[0] == 3u);
    puts("PASS: accelerator common CPU override");
    return 0;
  }

  assert(WebPSetEncoderAcceleratorForTesting(NULL));
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_NOT_RUN);
  assert(argb[0] == 1u && transform_image[0] == 3u);

  assert(WebPSetEncoderAcceleratorForTesting(&backend));
  context.color_result = WEBP_ACCELERATOR_SUCCESS;
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_SUCCESS);
  assert(context.color_calls == 1);
  assert(argb[0] == 0x11223344u);
  assert(transform_image[0] == 0x55667788u);

  argb[0] = 7u;
  transform_image[0] = 8u;
  context.color_result = WEBP_ACCELERATOR_NOT_RUN;
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_NOT_RUN);
  assert(argb[0] == 7u && transform_image[0] == 8u);

  context.color_result = WEBP_ACCELERATOR_ERROR;
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_ERROR);
  assert(argb[0] == 7u && transform_image[0] == 8u);

  assert(WebPAccelerateHashChain(&hash_request) == WEBP_ACCELERATOR_NOT_RUN);
  assert(context.hash_calls == 0);
  assert(candidates[0] == 4u && candidates[1] == 5u && candidates[2] == 6u);

  backend.properties = WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS;
  assert(!WebPSetEncoderAcceleratorForTesting(&backend));
  backend = MakeBackend(&context);
  backend.color_transform = NULL;
  assert(WebPSetEncoderAcceleratorForTesting(&backend));
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_ERROR);

  assert(WebPSetEncoderAcceleratorForTesting(NULL));
  puts("PASS: accelerator interface");
  return 0;
}
