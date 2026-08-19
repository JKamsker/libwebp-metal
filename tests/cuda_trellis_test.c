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

#include "tools/benchmark_platform.h"
#include "webp/encode.h"

enum { kWidth = 513, kHeight = 517 };

static int ConfigureBackend(int use_cuda, int fail_collect_band) {
  char fail_band[16];
  int ok = 1;
  ok &= WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR",
                                    use_cuda ? "cuda" : "none");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA", use_cuda ? "1" : "0");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "1");
  ok &= WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS", "0");
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
  return ok;
}

static int Encode(const uint8_t* rgba, int method, int quality, int passes,
                  int use_cuda, int fail_collect_band,
                  WebPMemoryWriter* writer) {
  WebPConfig config;
  WebPPicture picture;
  int ok = 0;
  if (!ConfigureBackend(use_cuda, fail_collect_band) ||
      !WebPConfigInit(&config) || !WebPPictureInit(&picture)) {
    return 0;
  }
  config.method = method;
  config.quality = (float)quality;
  config.pass = passes;
  config.exact = 1;
  picture.width = kWidth;
  picture.height = kHeight;
  picture.use_argb = 1;
  WebPMemoryWriterInit(writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = writer;
  if (WebPPictureImportRGBA(&picture, rgba, kWidth * 4) &&
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
                     int fail_collect_band) {
  WebPMemoryWriter cpu, cuda;
  int ok;
  if (!Encode(rgba, method, quality, passes, 0, -1, &cpu)) return 0;
  if (!Encode(rgba, method, quality, passes, 1, fail_collect_band, &cuda)) {
    WebPMemoryWriterClear(&cpu);
    return 0;
  }
  ok = cpu.size == cuda.size && !memcmp(cpu.mem, cuda.mem, cpu.size);
  if (!ok) {
    fprintf(stderr,
            "CPU/CUDA trellis mismatch (method=%d quality=%d pass=%d "
            "fail_band=%d bytes=%zu/%zu)\n",
            method, quality, passes, fail_collect_band, cpu.size, cuda.size);
  }
  WebPMemoryWriterClear(&cpu);
  WebPMemoryWriterClear(&cuda);
  return ok;
}

int main(void) {
  const size_t rgba_size = (size_t)kWidth * kHeight * 4u;
  uint8_t* const rgba = (uint8_t*)malloc(rgba_size);
  size_t i;
  int method;
  if (rgba == NULL) return 2;
  for (i = 0; i < rgba_size; i += 4) {
    const uint32_t pixel = (uint32_t)(i >> 2);
    rgba[i + 0] = (uint8_t)(pixel * 37u + pixel / 11u);
    rgba[i + 1] = (uint8_t)(pixel * 17u + pixel / 29u);
    rgba[i + 2] = (uint8_t)(pixel * 53u + pixel / 7u);
    rgba[i + 3] = (uint8_t)((pixel % 19u) ? 255u : (pixel * 13u));
  }
  for (method = 5; method <= 6; ++method) {
    if (!CheckCase(rgba, method, 75, 1, -1) ||
        !CheckCase(rgba, method, 99, 1, -1) ||
        !CheckCase(rgba, method, 75, 2, -1) ||
        !CheckCase(rgba, method, 75, 1, 3)) {
      free(rgba);
      return 1;
    }
  }
  free(rgba);
  puts("PASS: CUDA method-5/6 trellis and collect fallback are byte-exact");
  return 0;
}
