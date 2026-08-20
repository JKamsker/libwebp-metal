// Copyright 2026
//
// Exact private device-YUV handoff coverage for CUDA analysis and decimation.

#include <cuda_runtime.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#else
#include <unistd.h>
#endif

#include "src/enc/cuda_enc.h"
#include "src/webp/encode.h"

namespace {

bool SetEnvironment(const char* name, const char* value) {
#if defined(_WIN32)
  return _putenv_s(name, value) == 0;
#else
  return setenv(name, value, 1) == 0;
#endif
}

bool ConfigureCUDA() {
  return SetEnvironment("WEBP_ACCELERATOR", "cuda") &&
         SetEnvironment("WEBP_CUDA", "1") &&
         SetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS", "1") &&
         SetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS_MIN_MACROBLOCKS", "0") &&
         SetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "1") &&
         SetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS", "0");
}

void FillPicture(WebPPicture* picture) {
  const int uv_width = (picture->width + 1) / 2;
  const int uv_height = (picture->height + 1) / 2;
  for (int y = 0; y < picture->height; ++y) {
    for (int x = 0; x < picture->width; ++x) {
      picture->y[(size_t)y * picture->y_stride + x] =
          (uint8_t)((x * 29 + y * 17 + ((x ^ y) & 31) * 5) & 255);
    }
  }
  for (int y = 0; y < uv_height; ++y) {
    for (int x = 0; x < uv_width; ++x) {
      picture->u[(size_t)y * picture->uv_stride + x] =
          (uint8_t)((x * 11 + y * 23 + 73) & 255);
      picture->v[(size_t)y * picture->uv_stride + x] =
          (uint8_t)((x * 31 + y * 7 + 19) & 255);
    }
  }
}

bool Encode(WebPPicture* picture, int method, int quality,
            WebPMemoryWriter* writer) {
  WebPConfig config;
  if (!WebPConfigInit(&config)) return false;
  config.lossless = 0;
  config.method = method;
  config.quality = (float)quality;
  config.exact = 1;
  WebPMemoryWriterInit(writer);
  picture->writer = WebPMemoryWrite;
  picture->custom_ptr = writer;
  return WebPEncode(&config, picture) != 0;
}

bool CheckCase(int width, int height, int method, int quality,
               bool expect_direct) {
  WebPPicture source, placeholder;
  WebPMemoryWriter reference, external;
  uint8_t *device_y = nullptr, *device_u = nullptr, *device_v = nullptr;
  const size_t y_bytes = (size_t)width * height;
  const size_t uv_width = ((size_t)width + 1u) / 2u;
  const size_t uv_height = ((size_t)height + 1u) / 2u;
  const size_t uv_bytes = uv_width * uv_height;
  uint64_t copied = 0;
  uint32_t stages;
  bool ok = false;
  if (!WebPPictureInit(&source) || !WebPPictureInit(&placeholder)) return false;
  source.use_argb = placeholder.use_argb = 0;
  source.colorspace = placeholder.colorspace = WEBP_YUV420;
  source.width = placeholder.width = width;
  source.height = placeholder.height = height;
  if (!WebPPictureAlloc(&source) || !WebPPictureAlloc(&placeholder)) goto end;
  FillPicture(&source);
  if (cudaMalloc(&device_y, y_bytes) != cudaSuccess ||
      cudaMalloc(&device_u, uv_bytes) != cudaSuccess ||
      cudaMalloc(&device_v, uv_bytes) != cudaSuccess ||
      cudaMemcpy2D(device_y, width, source.y, source.y_stride, width, height,
                   cudaMemcpyHostToDevice) != cudaSuccess ||
      cudaMemcpy2D(device_u, uv_width, source.u, source.uv_stride, uv_width,
                   uv_height, cudaMemcpyHostToDevice) != cudaSuccess ||
      cudaMemcpy2D(device_v, uv_width, source.v, source.uv_stride, uv_width,
                   uv_height, cudaMemcpyHostToDevice) != cudaSuccess) {
    goto end;
  }
  if (!Encode(&source, method, quality, &reference)) goto end;
  WebPCUDAResetSuccessfulStages();
  if (WebPCUDARegisterExternalYUV420(
          device_y, width, device_u, uv_width, device_v, uv_width,
          placeholder.y, placeholder.y_stride, placeholder.u, placeholder.v,
          placeholder.uv_stride, width, height, &copied) !=
          WEBP_ACCELERATOR_SUCCESS ||
      copied != 2u * (y_bytes + 2u * uv_bytes) ||
      !Encode(&placeholder, method, quality, &external)) {
    goto clear_reference;
  }
  stages = WebPCUDAGetSuccessfulStages();
  {
    const bool direct =
        (stages & (WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS |
                   WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE)) ==
        (WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS |
         WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE);
    if (direct != expect_direct) {
      fprintf(stderr,
              "unexpected external YUV dispatch for %dx%d m%d q%d "
              "stages=0x%x\n",
              width, height, method, quality, stages);
      WebPMemoryWriterClear(&external);
      goto clear_reference;
    }
    if (!direct) {
      // The handoff is transactional: discard any placeholder-derived encode
      // and retry the complete image from the normal host picture.
      WebPMemoryWriterClear(&external);
      WebPCUDAClearExternalYUV420();
      if (!Encode(&source, method, quality, &external)) goto clear_reference;
    }
  }
  if (reference.size != external.size ||
      memcmp(reference.mem, external.mem, reference.size)) {
    fprintf(stderr, "external YUV mismatch for %dx%d m%d q%d stages=0x%x\n",
            width, height, method, quality, stages);
    WebPMemoryWriterClear(&external);
    goto clear_reference;
  }
  WebPMemoryWriterClear(&external);
  ok = true;
clear_reference:
  WebPMemoryWriterClear(&reference);
end:
  WebPCUDAClearExternalYUV420();
  if (device_y != nullptr) cudaFree(device_y);
  if (device_u != nullptr) cudaFree(device_u);
  if (device_v != nullptr) cudaFree(device_v);
  WebPPictureFree(&source);
  WebPPictureFree(&placeholder);
  return ok;
}

}  // namespace

int main() {
  static const int kQualities[] = {0, 25, 75, 98, 100};
  int device_count = 0;
  int cases = 0;
  if (cudaGetDeviceCount(&device_count) != cudaSuccess || device_count == 0) {
    return 77;
  }
  if (!ConfigureCUDA()) return 1;
  for (int method = 0; method <= 6; ++method) {
    for (size_t q = 0; q < sizeof(kQualities) / sizeof(kQualities[0]); ++q) {
      if (!CheckCase(17, 13, method, kQualities[q], method >= 3) ||
          !CheckCase(257, 255, method, kQualities[q], method >= 3)) {
        return 1;
      }
      cases += 2;
    }
  }
  for (int method = 3; method <= 6; ++method) {
    for (size_t q = 1; q + 1 < sizeof(kQualities) / sizeof(kQualities[0]);
         ++q) {
      if (!CheckCase(1600, 1200, method, kQualities[q], true)) return 1;
      ++cases;
    }
  }
  for (int repetition = 0; repetition < 8; ++repetition) {
    if (!CheckCase(17, 13, 2, 25, false) ||
        !CheckCase(17, 13, 3, 25, true) ||
        !CheckCase(257, 255, 4, 75, true) ||
        !CheckCase(1600, 1200, 5, 98, true)) {
      return 1;
    }
    cases += 4;
  }
  printf("PASS: %d device-resident YUV handoffs/fallbacks are byte-exact "
         "across methods, qualities, tiny, odd, realistic, and repeated "
         "encodes\n",
         cases);
  return 0;
}
