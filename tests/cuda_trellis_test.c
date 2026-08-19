// Copyright 2026
//
// Byte-parity coverage for CUDA lossy decimation with method-5 selected-mode
// trellis and method-6 all-candidate trellis.

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(WEBP_CUDA_DIRECT_PRIVATE_TEST)
#include "src/enc/cuda_enc.h"
#endif
#include "tools/benchmark_platform.h"
#include "webp/encode.h"

enum { kWidth = 513, kHeight = 517 };

static int ConfigureBackend(int use_cuda, int fail_collect_band,
                            int fail_download_step) {
  char fail_band[16];
  char fail_download[16];
  int ok = 1;
  ok &= WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR",
                                    use_cuda ? "cuda" : "none");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA", use_cuda ? "1" : "0");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "1");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS", "0");
  ok &= WebPBenchmarkSetEnvironment(
      "WEBP_CUDA_DECIMATE_TEST_PADDED_STRIDES", "1");
  // Isolate decimation: picture import and analysis remain on their ordinary
  // CPU implementations for both sides of the byte comparison.
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_COLOR", "0");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS", "0");
  if (fail_collect_band >= 0) {
    snprintf(fail_band, sizeof(fail_band), "%d", fail_collect_band);
    ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_DECIMATE_FAIL_COLLECT",
                                      fail_band);
  } else {
    ok &= WebPBenchmarkUnsetEnvironment("WEBP_CUDA_DECIMATE_FAIL_COLLECT");
  }
  if (fail_download_step >= 0) {
    snprintf(fail_download, sizeof(fail_download), "%d", fail_download_step);
    ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_DECIMATE_FAIL_DOWNLOAD",
                                      fail_download);
  } else {
    ok &= WebPBenchmarkUnsetEnvironment("WEBP_CUDA_DECIMATE_FAIL_DOWNLOAD");
  }
  return ok;
}

static int Encode(const uint8_t* rgba, int width, int height, int method,
                  int quality, int passes, int use_cuda, int fail_collect_band,
                  int fail_download_step,
                  WebPMemoryWriter* writer) {
  WebPConfig config;
  WebPPicture picture;
  int ok = 0;
  if (!ConfigureBackend(use_cuda, fail_collect_band, fail_download_step) ||
      !WebPConfigInit(&config) || !WebPPictureInit(&picture)) {
    return 0;
  }
  config.method = method;
  config.quality = (float)quality;
  config.pass = passes;
  config.exact = 1;
  picture.width = width;
  picture.height = height;
  picture.use_argb = 1;
  WebPMemoryWriterInit(writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = writer;
  if (WebPPictureImportRGBA(&picture, rgba, width * 4) &&
      WebPEncode(&config, &picture)) {
    ok = 1;
  } else {
    fprintf(stderr,
            "%s encode failed (method=%d quality=%d pass=%d error=%d)\n",
            use_cuda ? "CUDA" : "CPU", method, quality, passes,
            picture.error_code);
    WebPMemoryWriterClear(writer);
  }
  WebPPictureFree(&picture);
  return ok;
}

static int CheckCase(const uint8_t* rgba, int method, int quality, int passes,
                     int fail_collect_band, int fail_download_step, int width,
                     int height) {
  WebPMemoryWriter cpu, cuda;
  int ok;
  if (!Encode(rgba, width, height, method, quality, passes, 0, -1, -1,
              &cpu)) {
    return 0;
  }
  if (!Encode(rgba, width, height, method, quality, passes, 1,
              fail_collect_band, fail_download_step, &cuda)) {
    WebPMemoryWriterClear(&cpu);
    return 0;
  }
  ok = cpu.size == cuda.size && !memcmp(cpu.mem, cuda.mem, cpu.size);
  if (!ok) {
    fprintf(stderr,
            "CPU/CUDA trellis mismatch (method=%d quality=%d pass=%d "
            "fail_band=%d fail_download=%d size=%dx%d bytes=%zu/%zu)\n",
            method, quality, passes, fail_collect_band, fail_download_step,
            width, height, cpu.size, cuda.size);
  }
  WebPMemoryWriterClear(&cpu);
  WebPMemoryWriterClear(&cuda);
  return ok;
}

static void FillRGBA(uint8_t* rgba, size_t rgba_size) {
  size_t i;
  for (i = 0; i < rgba_size; i += 4) {
    const uint32_t pixel = (uint32_t)(i >> 2);
    rgba[i + 0] = (uint8_t)(pixel * 37u + pixel / 11u);
    rgba[i + 1] = (uint8_t)(pixel * 17u + pixel / 29u);
    rgba[i + 2] = (uint8_t)(pixel * 53u + pixel / 7u);
    rgba[i + 3] = (uint8_t)((pixel % 19u) ? 255u : (pixel * 13u));
  }
}

static int CheckBandRemainders(void) {
  const int width = 65;
  int mb_h;
  for (mb_h = 16; mb_h < 24; ++mb_h) {
    const int height = mb_h * 16 - 3;
    const size_t rgba_size = (size_t)width * height * 4u;
    uint8_t* const rgba = (uint8_t*)malloc(rgba_size);
    int ok;
    if (rgba == NULL) return 0;
    FillRGBA(rgba, rgba_size);
    ok = CheckCase(rgba, 2, 75, 1, -1, -1, width, height);
    free(rgba);
    if (!ok) return 0;
  }
  return 1;
}

#if defined(WEBP_CUDA_DIRECT_PRIVATE_TEST)
static int CheckInvalidDirectRequests(void) {
  const WebPEncoderAccelerator* const backend =
      WebPGetCUDAEncoderAccelerator();
  uint8_t y[16 * 16] = {0};
  uint8_t u[8 * 8] = {0};
  uint8_t v[8 * 8] = {0};
  uint8_t segments[1] = {0};
  WebPAcceleratorDecimateSegment segment_params[4];
  uint16_t level_costs[4 * 8 * 3 * 68];
  uint8_t coeff_probas[4 * 8 * 3 * 11];
  WebPAcceleratorDecimateResult result;
  uint8_t recon_y[23 * 16];
  uint8_t recon_u[13 * 8];
  uint8_t recon_v[13 * 8];
  WebPAcceleratorDecimateRequest request;
  WebPAcceleratorDecimateResult result_before;
  uint8_t recon_y_before[sizeof(recon_y)];
  memset(segment_params, 0, sizeof(segment_params));
  memset(level_costs, 0, sizeof(level_costs));
  memset(coeff_probas, 0, sizeof(coeff_probas));
  memset(&result, 0x5a, sizeof(result));
  memset(recon_y, 0x6b, sizeof(recon_y));
  memset(recon_u, 0x7c, sizeof(recon_u));
  memset(recon_v, 0x8d, sizeof(recon_v));
  memset(&request, 0, sizeof(request));
  request.width = 16;
  request.height = 16;
  request.mb_w = 1;
  request.mb_h = 1;
  request.phase = WEBP_ACCELERATOR_DECIMATE_WHOLE;
  request.y = y;
  request.u = u;
  request.v = v;
  request.y_stride = 16;
  request.uv_stride = 8;
  request.segments = segments;
  request.segment_params = segment_params;
  request.level_costs = level_costs;
  request.coeff_probas = coeff_probas;
  request.rd_opt_level = 1;
  request.results = &result;
  request.recon_y = recon_y;
  request.recon_u = recon_u;
  request.recon_v = recon_v;
  request.recon_y_stride = 23;
  request.recon_uv_stride = 13;
  result_before = result;
  memcpy(recon_y_before, recon_y, sizeof(recon_y));

  request.mb_w = 2;
  if (backend->lossy_decimate(backend->context, &request) !=
          WEBP_ACCELERATOR_ERROR ||
      memcmp(&result, &result_before, sizeof(result)) != 0 ||
      memcmp(recon_y, recon_y_before, sizeof(recon_y)) != 0) {
    fprintf(stderr, "invalid decimate geometry was not transactional\n");
    return 0;
  }
  request.mb_w = 1;
  segments[0] = 4;
  if (backend->lossy_decimate(backend->context, &request) !=
          WEBP_ACCELERATOR_ERROR ||
      memcmp(&result, &result_before, sizeof(result)) != 0 ||
      memcmp(recon_y, recon_y_before, sizeof(recon_y)) != 0) {
    fprintf(stderr, "invalid decimate segment was not transactional\n");
    return 0;
  }
  segments[0] = 0;
  if (!WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS",
                                   "-1") ||
      backend->lossy_decimate(backend->context, &request) !=
          WEBP_ACCELERATOR_ERROR ||
      memcmp(&result, &result_before, sizeof(result)) != 0 ||
      memcmp(recon_y, recon_y_before, sizeof(recon_y)) != 0 ||
      !WebPBenchmarkUnsetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS")) {
    fprintf(stderr, "invalid decimate threshold was not rejected safely\n");
    return 0;
  }
  if (!WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "FaLsE") ||
      backend->lossy_decimate(backend->context, &request) !=
          WEBP_ACCELERATOR_NOT_RUN ||
      memcmp(&result, &result_before, sizeof(result)) != 0 ||
      memcmp(recon_y, recon_y_before, sizeof(recon_y)) != 0 ||
      !WebPBenchmarkUnsetEnvironment("WEBP_CUDA_LOSSY_DECIMATE")) {
    fprintf(stderr, "decimate boolean false spelling was not honored\n");
    return 0;
  }
  return 1;
}
#endif

int main(void) {
  const size_t rgba_size = (size_t)kWidth * kHeight * 4u;
  uint8_t* const rgba = (uint8_t*)malloc(rgba_size);
  int method;
  if (rgba == NULL) return 2;
  if (!WebPBenchmarkHasCUDADevice()) {
    free(rgba);
    return 77;
  }
#if defined(WEBP_CUDA_DIRECT_PRIVATE_TEST)
  WebPCUDAResetSuccessfulStages();
  if (!CheckInvalidDirectRequests()) {
    free(rgba);
    return 1;
  }
#endif
  FillRGBA(rgba, rgba_size);
  for (method = 5; method <= 6; ++method) {
    if (!CheckCase(rgba, method, 75, 1, -1, -1, kWidth, kHeight) ||
        !CheckCase(rgba, method, 99, 1, -1, -1, kWidth, kHeight) ||
        !CheckCase(rgba, method, 75, 2, -1, -1, kWidth, kHeight) ||
        !CheckCase(rgba, method, 75, 1, 3, -1, kWidth, kHeight) ||
        !CheckCase(rgba, method, 75, 1, -1, 2, kWidth, kHeight)) {
      free(rgba);
      return 1;
    }
  }
  free(rgba);
  if (!CheckBandRemainders()) return 1;
#if defined(WEBP_CUDA_DIRECT_PRIVATE_TEST)
  if ((WebPCUDAGetSuccessfulStages() &
       WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE) == 0u) {
    fprintf(stderr, "CUDA decimate telemetry was not observed\n");
    return 1;
  }
#endif
  puts("PASS: CUDA trellis, padded strides, all band remainders, and "
       "transactional fallbacks are byte-exact");
  return 0;
}
