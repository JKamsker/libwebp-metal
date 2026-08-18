// Copyright 2026

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/accelerator_enc.h"

typedef struct {
  WebPAcceleratorResult color_result;
  WebPAcceleratorResult hash_result;
  WebPAcceleratorResult rgb_result;
  WebPAcceleratorResult near_lossless_result;
  WebPAcceleratorResult lossy_analysis_result;
  WebPAcceleratorResult predictor_result;
  WebPAcceleratorResult histogram_result;
  int color_calls;
  int hash_calls;
  int rgb_calls;
  int near_lossless_calls;
  int lossy_analysis_calls;
  int predictor_calls;
  int histogram_calls;
  int end_encode_calls;
  int expected_rgb_method;
  int expected_rgb_quality;
} FakeContext;

static void FakeEndEncode(void* opaque) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->end_encode_calls;
}

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
  assert(request->size == 3);
  assert(request->xsize == 3);
  assert(request->iter_max == 8);
  assert(request->window_size == 32u);
  if (context->hash_result == WEBP_ACCELERATOR_SUCCESS) {
    request->candidates[0] = 99u;
  }
  return context->hash_result;
}

static WebPAcceleratorResult FakeRGBToYUV(
    void* opaque, const WebPAcceleratorRGBToYUVRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->rgb_calls;
  assert(request->step == 4);
  assert(request->source_stride == 13);
  assert(request->width == 2);
  assert(request->height == 2);
  assert(request->y_stride == 5);
  assert(request->uv_stride == 3);
  assert(request->method == context->expected_rgb_method);
  assert(request->quality == context->expected_rgb_quality);
  if (context->rgb_result == WEBP_ACCELERATOR_SUCCESS) {
    request->y[0] = 42u;
    request->u[0] = 43u;
    request->v[0] = 44u;
  }
  return context->rgb_result;
}

static WebPAcceleratorResult FakeNearLossless(
    void* opaque, const WebPAcceleratorNearLosslessRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->near_lossless_calls;
  assert(request->source_stride == 3);
  assert(request->width == 2);
  assert(request->height == 3);
  assert(request->limit_bits == 4);
  if (context->near_lossless_result == WEBP_ACCELERATOR_SUCCESS) {
    request->output[0] = 45u;
  }
  return context->near_lossless_result;
}

static WebPAcceleratorResult FakeLossyAnalysis(
    void* opaque, const WebPAcceleratorLossyAnalysisRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  if (request == NULL) return context->lossy_analysis_result;
  ++context->lossy_analysis_calls;
  assert(request->width == 2);
  assert(request->height == 2);
  assert(request->method == 4);
  assert(request->quality == 75);
  if (context->lossy_analysis_result == WEBP_ACCELERATOR_SUCCESS) {
    request->results[0].alpha = 46u;
  }
  return context->lossy_analysis_result;
}

static WebPAcceleratorResult FakePredictor(
    void* opaque, const WebPAcceleratorPredictorRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->predictor_calls;
  assert(request->width == 2);
  assert(request->height == 1);
  assert(request->min_bits == 2);
  assert(request->max_bits == 5);
  assert(request->max_quantization == 1);
  assert(request->exact == 1);
  assert(request->used_subtract_green == 0);
  if (context->predictor_result == WEBP_ACCELERATOR_SUCCESS) {
    request->residuals[0] = 47u;
    request->mode_image[0] = 0xff000b00u;
    *request->best_bits = 5;
  }
  return context->predictor_result;
}

static WebPAcceleratorResult FakeHistogram(
    void* opaque, const WebPAcceleratorHistogramRequest* request) {
  FakeContext* const context = (FakeContext*)opaque;
  ++context->histogram_calls;
  assert(request->span_count == 1u);
  assert(request->command_count == 1u);
  assert(request->spans[0].count == 1u);
  assert(request->cache_bits == 0);
  assert(request->literal_count == 280u);
  if (context->histogram_result == WEBP_ACCELERATOR_SUCCESS) {
    request->literal[0] = 48u;
  }
  return context->histogram_result;
}

static WebPEncoderAccelerator MakeBackend(FakeContext* context) {
  WebPEncoderAccelerator backend;
  memset(&backend, 0, sizeof(backend));
  backend.abi_version = WEBP_ENCODER_ACCELERATOR_ABI_VERSION;
  backend.struct_size = sizeof(backend);
  backend.name = "fake";
  backend.stages = WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM |
                   WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN |
                   WEBP_ACCELERATOR_STAGE_RGB_TO_YUV |
                   WEBP_ACCELERATOR_STAGE_NEAR_LOSSLESS |
                   WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS |
                   WEBP_ACCELERATOR_STAGE_LOSSLESS_PREDICTOR |
                   WEBP_ACCELERATOR_STAGE_LOSSLESS_HISTOGRAM;
  backend.properties = WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |
                       WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT |
                       WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC;
  backend.context = context;
  backend.color_transform = FakeColorTransform;
  backend.hash_chain = FakeHashChain;
  backend.rgb_to_yuv = FakeRGBToYUV;
  backend.near_lossless = FakeNearLossless;
  backend.lossy_analysis = FakeLossyAnalysis;
  backend.predictor = FakePredictor;
  backend.histogram = FakeHistogram;
  backend.end_encode = FakeEndEncode;
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
  const uint8_t rgba[26] = {0};
  uint8_t y[10] = {7u};
  uint8_t u[3] = {8u};
  uint8_t v[3] = {9u};
  const WebPAcceleratorRGBToYUVRequest rgb_request = {
      rgba, rgba + 1, rgba + 2, 4, 13, 2, 2, y, u, v, 5, 3, -1, -1};
  const uint32_t near_source[9] = {0};
  uint32_t near_output[6] = {10u};
  const WebPAcceleratorNearLosslessRequest near_lossless_request = {
      near_source, 3, 2, 3, 4, near_output};
  WebPAcceleratorLossyAnalysisResult analysis_result = {0};
  const WebPAcceleratorLossyAnalysisRequest lossy_analysis_request = {
      y, u, v, 5, 3, 2, 2, 4, 75, &analysis_result};
  uint32_t predictor_source[2] = {11u, 12u};
  uint32_t predictor_modes[1] = {13u};
  int predictor_bits = 0;
  const WebPAcceleratorPredictorRequest predictor_request = {
      2, 1, 2, 5, 1, 1, 0, predictor_source, predictor_source,
      predictor_modes, &predictor_bits};
  const WebPAcceleratorHistogramCommand histogram_command = {0, 0, 1,
                                                              0xff000000u};
  const WebPAcceleratorHistogramSpan histogram_span = {&histogram_command, 1};
  uint32_t histogram_literal[280] = {0};
  uint32_t histogram_red[256] = {0};
  uint32_t histogram_blue[256] = {0};
  uint32_t histogram_alpha[256] = {0};
  uint32_t histogram_distance[40] = {0};
  const WebPAcceleratorHistogramRequest histogram_request = {
      &histogram_span, 1,   1,          0, histogram_literal,
      280,             histogram_red,   histogram_blue,
      histogram_alpha, histogram_distance};

  memset(&context, 0, sizeof(context));
  context.hash_result = WEBP_ACCELERATOR_SUCCESS;
  context.rgb_result = WEBP_ACCELERATOR_SUCCESS;
  context.near_lossless_result = WEBP_ACCELERATOR_SUCCESS;
  context.lossy_analysis_result = WEBP_ACCELERATOR_SUCCESS;
  context.predictor_result = WEBP_ACCELERATOR_SUCCESS;
  context.histogram_result = WEBP_ACCELERATOR_SUCCESS;
  context.expected_rgb_method = 5;
  context.expected_rgb_quality = 63;
  backend = MakeBackend(&context);
  if (getenv("WEBP_ACCELERATOR") != NULL &&
      strcmp(getenv("WEBP_ACCELERATOR"), "none") == 0) {
    assert(WebPSetEncoderAcceleratorForTesting(&backend));
    assert(WebPAccelerateColorTransform(&color_request) ==
           WEBP_ACCELERATOR_NOT_RUN);
    assert(!WebPAcceleratorLossyAnalysisEnabled());
    WebPAcceleratorEndEncode();
    assert(context.end_encode_calls == 1);
    assert(context.color_calls == 0);
    assert(argb[0] == 1u && transform_image[0] == 3u);
    puts("PASS: accelerator common CPU override");
    return 0;
  }

  assert(WebPSetEncoderAcceleratorForTesting(NULL));
  assert(!WebPAcceleratorLossyAnalysisEnabled());
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_NOT_RUN);
  assert(argb[0] == 1u && transform_image[0] == 3u);

  assert(WebPSetEncoderAcceleratorForTesting(&backend));
  WebPAcceleratorEndEncode();
  assert(context.end_encode_calls == 1);
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

  context.color_result = (WebPAcceleratorResult)99;
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_ERROR);
  assert(argb[0] == 7u && transform_image[0] == 8u);

  assert(WebPAccelerateHashChain(&hash_request) == WEBP_ACCELERATOR_SUCCESS);
  assert(context.hash_calls == 1);
  assert(candidates[0] == 99u);

  WebPAcceleratorBeginEncode(0, 5, 63);
  assert(WebPAccelerateRGBToYUV(&rgb_request) == WEBP_ACCELERATOR_SUCCESS);
  assert(context.rgb_calls == 1);
  assert(y[0] == 42u && u[0] == 43u && v[0] == 44u);
  WebPAcceleratorEndEncode();
  context.expected_rgb_method = -1;
  context.expected_rgb_quality = -1;
  assert(WebPAccelerateRGBToYUV(&rgb_request) == WEBP_ACCELERATOR_SUCCESS);
  assert(context.rgb_calls == 2);

  assert(WebPAccelerateNearLossless(&near_lossless_request) ==
         WEBP_ACCELERATOR_SUCCESS);
  assert(context.near_lossless_calls == 1);
  assert(near_output[0] == 45u);

  assert(WebPAccelerateLossyAnalysis(&lossy_analysis_request) ==
         WEBP_ACCELERATOR_SUCCESS);
  assert(context.lossy_analysis_calls == 1);
  assert(analysis_result.alpha == 46u);
  assert(WebPAcceleratorLossyAnalysisEnabled());

  assert(WebPAcceleratePredictor(&predictor_request) ==
         WEBP_ACCELERATOR_SUCCESS);
  assert(context.predictor_calls == 1);
  assert(predictor_source[0] == 47u);
  assert(predictor_modes[0] == 0xff000b00u);
  assert(predictor_bits == 5);

  assert(WebPAccelerateHistogram(&histogram_request) ==
         WEBP_ACCELERATOR_SUCCESS);
  assert(context.histogram_calls == 1);
  assert(histogram_literal[0] == 48u);

  assert(WebPAccelerateColorTransform(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAccelerateHashChain(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAccelerateRGBToYUV(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAccelerateNearLossless(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAccelerateLossyAnalysis(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAcceleratePredictor(NULL) == WEBP_ACCELERATOR_NOT_RUN);
  assert(WebPAccelerateHistogram(NULL) == WEBP_ACCELERATOR_NOT_RUN);

  backend.properties = WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS;
  assert(!WebPSetEncoderAcceleratorForTesting(&backend));
  backend = MakeBackend(&context);
  backend.color_transform = NULL;
  assert(WebPSetEncoderAcceleratorForTesting(&backend));
  assert(WebPAccelerateColorTransform(&color_request) ==
         WEBP_ACCELERATOR_ERROR);

  backend = MakeBackend(&context);
  backend.abi_version++;
  assert(!WebPSetEncoderAcceleratorForTesting(&backend));
  backend = MakeBackend(&context);
  backend.struct_size--;
  assert(!WebPSetEncoderAcceleratorForTesting(&backend));
  backend = MakeBackend(&context);
  backend.name = "";
  assert(!WebPSetEncoderAcceleratorForTesting(&backend));

  assert(WebPSetEncoderAcceleratorForTesting(NULL));
  puts("PASS: accelerator interface");
  return 0;
}
