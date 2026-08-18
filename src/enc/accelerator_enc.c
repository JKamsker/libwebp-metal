// Copyright 2026
//
// Backend selection and dispatch for private encoder acceleration.

#include "src/enc/accelerator_enc.h"

#include <stdlib.h>
#include <string.h>

#if defined(WEBP_USE_METAL)
#include "src/enc/metal_enc.h"
#endif
#if defined(WEBP_USE_CUDA)
#include "src/enc/cuda_enc.h"
#endif

#define WEBP_ACCELERATOR_REQUIRED_PROPERTIES                  \
  (WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |                    \
   WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT)

#if defined(WEBP_ACCELERATOR_TESTING)
static const WebPEncoderAccelerator* g_test_backend = NULL;
#endif

static int IsDisabledByEnvironment(void) {
  const char* const preference = getenv("WEBP_ACCELERATOR");
  return preference != NULL &&
         (!strcmp(preference, "none") || !strcmp(preference, "cpu") ||
          !strcmp(preference, "0"));
}

static int BackendMatchesEnvironment(
    const WebPEncoderAccelerator* const backend) {
  const char* const preference = getenv("WEBP_ACCELERATOR");
  return preference == NULL || preference[0] == '\0' ||
         !strcmp(preference, "auto") || !strcmp(preference, backend->name);
}

static int IsValidBackend(const WebPEncoderAccelerator* const backend) {
  return backend != NULL &&
         backend->abi_version == WEBP_ENCODER_ACCELERATOR_ABI_VERSION &&
         backend->struct_size >= sizeof(*backend) && backend->name != NULL &&
         backend->name[0] != '\0' &&
         (backend->properties & WEBP_ACCELERATOR_REQUIRED_PROPERTIES) ==
             WEBP_ACCELERATOR_REQUIRED_PROPERTIES;
}

static size_t GetBackends(const WebPEncoderAccelerator** backends,
                          size_t capacity) {
  size_t count = 0;
#if !defined(WEBP_ACCELERATOR_TESTING) && !defined(WEBP_USE_METAL) && \
    !defined(WEBP_USE_CUDA)
  (void)backends;
  (void)capacity;
#endif
#if defined(WEBP_ACCELERATOR_TESTING)
  if (g_test_backend != NULL && count < capacity) {
    backends[count++] = g_test_backend;
  }
#else
#if defined(WEBP_USE_METAL)
  if (count < capacity) backends[count++] = WebPGetMetalEncoderAccelerator();
#endif
#if defined(WEBP_USE_CUDA)
  if (count < capacity) backends[count++] = WebPGetCUDAEncoderAccelerator();
#endif
#endif
  return count;
}

static WebPAcceleratorResult NormalizeResult(WebPAcceleratorResult result) {
  return (result == WEBP_ACCELERATOR_NOT_RUN ||
          result == WEBP_ACCELERATOR_SUCCESS ||
          result == WEBP_ACCELERATOR_ERROR)
             ? result
             : WEBP_ACCELERATOR_ERROR;
}

WebPAcceleratorResult WebPAccelerateColorTransform(
    const WebPAcceleratorColorTransformRequest* const request) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (request == NULL || count == 0 || IsDisabledByEnvironment()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    WebPAcceleratorResult result;
    if (!IsValidBackend(backend)) return WEBP_ACCELERATOR_ERROR;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages &
          WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM)) {
      continue;
    }
    if (backend->color_transform == NULL) return WEBP_ACCELERATOR_ERROR;
    result =
        NormalizeResult(backend->color_transform(backend->context, request));
    if (result != WEBP_ACCELERATOR_NOT_RUN) return result;
  }
  return WEBP_ACCELERATOR_NOT_RUN;
}

WebPAcceleratorResult WebPAccelerateHashChain(
    const WebPAcceleratorHashChainRequest* const request) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (request == NULL || count == 0 || IsDisabledByEnvironment()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    WebPAcceleratorResult result;
    if (!IsValidBackend(backend)) return WEBP_ACCELERATOR_ERROR;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages & WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN)) {
      continue;
    }
    if (backend->hash_chain == NULL) return WEBP_ACCELERATOR_ERROR;
    result = NormalizeResult(backend->hash_chain(backend->context, request));
    if (result != WEBP_ACCELERATOR_NOT_RUN) return result;
  }
  return WEBP_ACCELERATOR_NOT_RUN;
}

WebPAcceleratorResult WebPAccelerateRGBToYUV(
    const WebPAcceleratorRGBToYUVRequest* const request) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (request == NULL || count == 0 || IsDisabledByEnvironment()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    WebPAcceleratorResult result;
    if (!IsValidBackend(backend)) return WEBP_ACCELERATOR_ERROR;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages & WEBP_ACCELERATOR_STAGE_RGB_TO_YUV)) {
      continue;
    }
    if (backend->rgb_to_yuv == NULL) return WEBP_ACCELERATOR_ERROR;
    result = NormalizeResult(backend->rgb_to_yuv(backend->context, request));
    if (result != WEBP_ACCELERATOR_NOT_RUN) return result;
  }
  return WEBP_ACCELERATOR_NOT_RUN;
}

WebPAcceleratorResult WebPAccelerateNearLossless(
    const WebPAcceleratorNearLosslessRequest* const request) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (request == NULL || count == 0 || IsDisabledByEnvironment()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    WebPAcceleratorResult result;
    if (!IsValidBackend(backend)) return WEBP_ACCELERATOR_ERROR;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages & WEBP_ACCELERATOR_STAGE_NEAR_LOSSLESS)) {
      continue;
    }
    if (backend->near_lossless == NULL) return WEBP_ACCELERATOR_ERROR;
    result = NormalizeResult(
        backend->near_lossless(backend->context, request));
    if (result != WEBP_ACCELERATOR_NOT_RUN) return result;
  }
  return WEBP_ACCELERATOR_NOT_RUN;
}

WebPAcceleratorResult WebPAccelerateLossyAnalysis(
    const WebPAcceleratorLossyAnalysisRequest* const request) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (request == NULL || count == 0 || IsDisabledByEnvironment()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    WebPAcceleratorResult result;
    if (!IsValidBackend(backend)) return WEBP_ACCELERATOR_ERROR;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages & WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS)) {
      continue;
    }
    if (backend->lossy_analysis == NULL) return WEBP_ACCELERATOR_ERROR;
    result = NormalizeResult(
        backend->lossy_analysis(backend->context, request));
    if (result != WEBP_ACCELERATOR_NOT_RUN) return result;
  }
  return WEBP_ACCELERATOR_NOT_RUN;
}

int WebPAcceleratorLossyAnalysisEnabled(void) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (count == 0 || IsDisabledByEnvironment()) return 0;
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    if (!IsValidBackend(backend)) return 0;
    if (!BackendMatchesEnvironment(backend) ||
        !(backend->stages & WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS)) {
      continue;
    }
    if (backend->lossy_analysis == NULL) return 0;
    return NormalizeResult(backend->lossy_analysis(backend->context, NULL)) ==
           WEBP_ACCELERATOR_SUCCESS;
  }
  return 0;
}

void WebPAcceleratorEndEncode(void) {
  const WebPEncoderAccelerator* backends[4];
  const size_t count =
      GetBackends(backends, sizeof(backends) / sizeof(*backends));
  size_t i;
  if (count == 0) return;
  for (i = 0; i < count; ++i) {
    const WebPEncoderAccelerator* const backend = backends[i];
    // Cleanup is intentionally independent of the current environment. A
    // caller may change dispatch policy between picture import and encode.
    if (IsValidBackend(backend) && backend->end_encode != NULL) {
      backend->end_encode(backend->context);
    }
  }
}

#if defined(WEBP_ACCELERATOR_TESTING)
int WebPSetEncoderAcceleratorForTesting(
    const WebPEncoderAccelerator* const backend) {
  if (backend != NULL && !IsValidBackend(backend)) return 0;
  g_test_backend = backend;
  return 1;
}
#endif
