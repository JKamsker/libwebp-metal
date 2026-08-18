// Copyright 2026
//
// Compare the exact CPU and CUDA near-lossless preprocessors directly. This
// avoids depending on the lossless encoder's content-dependent transform
// selection to reach the preprocessing call site.

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/accelerator_enc.h"
#include "src/enc/vp8li_enc.h"
#include "tools/benchmark_platform.h"
#include "webp/encode.h"

typedef struct {
  int width;
  int height;
} Dimensions;

static uint32_t Random32(uint32_t* state) {
  uint32_t value = *state;
  value ^= value << 13;
  value ^= value >> 17;
  value ^= value << 5;
  *state = value;
  return value;
}

static void FillSource(uint32_t* source, int stride, int width, int height) {
  uint32_t random = 0x12345678u;
  int x, y;
  for (y = 0; y < height; ++y) {
    for (x = 0; x < stride; ++x) {
      const uint32_t noise = Random32(&random);
      if (x >= width) {
        source[(size_t)y * stride + x] = noise;
      } else if (x < width / 3) {
        const uint32_t base = (uint32_t)((x / 8 + y / 8) * 7) & 255u;
        source[(size_t)y * stride + x] =
            0xff000000u | (base << 16) | ((base + 2u) << 8) | (base + 4u);
      } else if (x < 2 * width / 3) {
        source[(size_t)y * stride + x] =
            ((noise & 255u) << 24) | (((uint32_t)x * 11u & 255u) << 16) |
            (((uint32_t)y * 17u & 255u) << 8) | ((x + y) & 255u);
      } else {
        source[(size_t)y * stride + x] = noise;
      }
    }
  }
}

static int Compare(const uint32_t* expected, const uint32_t* actual,
                   int width, int height, int bits, const char* label) {
  const size_t count = (size_t)width * height;
  size_t i;
  for (i = 0; i < count; ++i) {
    if (expected[i] != actual[i]) {
      fprintf(stderr,
              "%s mismatch for %dx%d bits=%d at (%zu,%zu): "
              "%08x != %08x\n",
              label, width, height, bits, i % (size_t)width,
              i / (size_t)width, expected[i], actual[i]);
      return 0;
    }
  }
  return 1;
}

static int RunCase(Dimensions dimensions, int bits, int require_cuda) {
  const int stride = dimensions.width + 5;
  const size_t source_count = (size_t)stride * dimensions.height;
  const size_t output_count =
      (size_t)dimensions.width * dimensions.height;
  uint32_t* const source =
      (uint32_t*)malloc(source_count * sizeof(*source));
  uint32_t* const cpu = (uint32_t*)malloc(output_count * sizeof(*cpu));
  uint32_t* const gpu = (uint32_t*)malloc(output_count * sizeof(*gpu));
  uint32_t* const repeat = (uint32_t*)malloc(output_count * sizeof(*repeat));
  WebPPicture picture;
  WebPAcceleratorNearLosslessRequest request;
  WebPAcceleratorResult result;
  int ok = 0;
  if (source == NULL || cpu == NULL || gpu == NULL || repeat == NULL ||
      !WebPPictureInit(&picture)) {
    fprintf(stderr, "allocation or picture initialization failed\n");
    goto cleanup;
  }
  FillSource(source, stride, dimensions.width, dimensions.height);
  picture.width = dimensions.width;
  picture.height = dimensions.height;
  picture.argb = source;
  picture.argb_stride = stride;

  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "none");
  if (!VP8ApplyNearLossless(&picture, (5 - bits) * 20, cpu)) {
    fprintf(stderr, "CPU near-lossless preprocessing failed\n");
    goto cleanup;
  }

  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "cuda");
  WebPBenchmarkSetEnvironment("WEBP_CUDA", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS", "0");
  request.source = source;
  request.source_stride = stride;
  request.width = dimensions.width;
  request.height = dimensions.height;
  request.limit_bits = bits;
  request.output = gpu;
  result = WebPAccelerateNearLossless(&request);
  if (result == WEBP_ACCELERATOR_NOT_RUN && !require_cuda) {
    if (!VP8ApplyNearLossless(&picture, (5 - bits) * 20, gpu)) {
      fprintf(stderr, "near-lossless fallback failed\n");
      goto cleanup;
    }
  } else if (result != WEBP_ACCELERATOR_SUCCESS) {
    fprintf(stderr, "CUDA near-lossless returned %d for %dx%d bits=%d\n",
            (int)result, dimensions.width, dimensions.height, bits);
    goto cleanup;
  }
  if (!Compare(cpu, gpu, dimensions.width, dimensions.height, bits,
               "CPU/CUDA")) {
    goto cleanup;
  }

  if (result == WEBP_ACCELERATOR_SUCCESS) {
    request.output = repeat;
    if (WebPAccelerateNearLossless(&request) != WEBP_ACCELERATOR_SUCCESS ||
        !Compare(gpu, repeat, dimensions.width, dimensions.height, bits,
                 "CUDA repeat")) {
      goto cleanup;
    }
  }
  ok = 1;

cleanup:
  free(repeat);
  free(gpu);
  free(cpu);
  free(source);
  return ok;
}

static int TestDeclinePreservesOutput(void) {
  enum { kWidth = 65, kHeight = 67, kStride = 70 };
  uint32_t* const source =
      (uint32_t*)malloc((size_t)kStride * kHeight * sizeof(*source));
  uint32_t* const output =
      (uint32_t*)malloc((size_t)kWidth * kHeight * sizeof(*output));
  WebPAcceleratorNearLosslessRequest request;
  size_t i;
  int ok = 0;
  if (source == NULL || output == NULL) goto cleanup;
  FillSource(source, kStride, kWidth, kHeight);
  for (i = 0; i < (size_t)kWidth * kHeight; ++i) output[i] = 0xdeadbeefu;
  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "cuda");
  WebPBenchmarkSetEnvironment("WEBP_CUDA", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS",
                              "18446744073709551615");
  request.source = source;
  request.source_stride = kStride;
  request.width = kWidth;
  request.height = kHeight;
  request.limit_bits = 3;
  request.output = output;
  if (WebPAccelerateNearLossless(&request) != WEBP_ACCELERATOR_NOT_RUN) {
    fprintf(stderr, "thresholded near-lossless request did not decline\n");
    goto cleanup;
  }
  for (i = 0; i < (size_t)kWidth * kHeight; ++i) {
    if (output[i] != 0xdeadbeefu) {
      fprintf(stderr, "declined request modified output at %zu\n", i);
      goto cleanup;
    }
  }
  ok = 1;
cleanup:
  free(output);
  free(source);
  return ok;
}

static int TestOversizedKernelExtents(int require_near_lossless) {
  uint32_t near_source = 0xff123456u;
  uint32_t near_output = 0xdeadbeefu;
  uint8_t rgb_source[3] = {1, 2, 3};
  uint8_t y[4] = {0xaa, 0xaa, 0xaa, 0xaa};
  uint8_t u[2] = {0xbb, 0xbb};
  uint8_t v[2] = {0xcc, 0xcc};
  WebPAcceleratorNearLosslessRequest near_request;
  WebPAcceleratorRGBToYUVRequest rgb_request;
  WebPAcceleratorResult result;

  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "cuda");
  WebPBenchmarkSetEnvironment("WEBP_CUDA", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS", "0");
  near_request.source = &near_source;
  near_request.source_stride = INT_MAX;
  near_request.width = INT_MAX;
  near_request.height = 3;
  near_request.limit_bits = 3;
  near_request.output = &near_output;
  result = WebPAccelerateNearLossless(&near_request);
  if ((require_near_lossless && result != WEBP_ACCELERATOR_ERROR) ||
      (!require_near_lossless && result != WEBP_ACCELERATOR_NOT_RUN) ||
      near_output != 0xdeadbeefu) {
    fprintf(stderr, "oversized near-lossless extent returned %d\n",
            (int)result);
    return 0;
  }

  WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_MIN_PIXELS", "0");
  rgb_request.red = rgb_source;
  rgb_request.green = rgb_source + 1;
  rgb_request.blue = rgb_source + 2;
  rgb_request.step = 3;
  rgb_request.source_stride = INT_MAX;
  rgb_request.width = 1;
  rgb_request.height = 4;
  rgb_request.y = y;
  rgb_request.u = u;
  rgb_request.v = v;
  rgb_request.y_stride = 1;
  rgb_request.uv_stride = 1;
  result = WebPAccelerateRGBToYUV(&rgb_request);
  if (result != WEBP_ACCELERATOR_NOT_RUN || y[0] != 0xaa || u[0] != 0xbb ||
      v[0] != 0xcc) {
    fprintf(stderr, "oversized RGB source extent returned %d\n", (int)result);
    return 0;
  }
  return 1;
}

int main(int argc, const char* const argv[]) {
  static const Dimensions kDimensions[] = {
      {64, 3}, {65, 67}, {257, 129}, {1024, 768}};
  int require_cuda = 1;
  size_t i;
  int bits;
  if (argc == 2 && !strcmp(argv[1], "--allow-fallback")) {
    require_cuda = 0;
  } else if (argc != 1) {
    fprintf(stderr, "Usage: %s [--allow-fallback]\n", argv[0]);
    return 2;
  }
  if (!TestDeclinePreservesOutput()) return 1;
  if (!TestOversizedKernelExtents(require_cuda)) return 1;
  for (i = 0; i < sizeof(kDimensions) / sizeof(kDimensions[0]); ++i) {
    for (bits = 1; bits <= 5; ++bits) {
      if (!RunCase(kDimensions[i], bits, require_cuda)) return 1;
    }
  }
  printf("PASS: exact near-lossless CPU/%s parity across 20 cases\n",
         require_cuda ? "CUDA" : "fallback");
  return 0;
}
