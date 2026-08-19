// Copyright 2026
//
// Direct correctness and transactional-output checks for CUDA lossless
// histogram population counting.

#define _POSIX_C_SOURCE 200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dsp/lossless_common.h"
#include "src/enc/accelerator_enc.h"
#include "src/enc/cuda_enc.h"
#include "tools/benchmark_platform.h"

enum { kLiteralCount = 288, kChannelCount = 256, kDistanceCount = 40 };

typedef struct {
  uint32_t literal[kLiteralCount];
  uint32_t red[kChannelCount];
  uint32_t blue[kChannelCount];
  uint32_t alpha[kChannelCount];
  uint32_t distance[kDistanceCount];
} Counts;

static int PrefixCode(uint32_t value) {
  int code, extra_bits;
  VP8LPrefixEncodeBits((int)value, &code, &extra_bits);
  return code;
}

static void AddExpected(const WebPAcceleratorHistogramCommand* command,
                        Counts* counts) {
  if (command->mode == 0u) {
    ++counts->alpha[(command->value >> 24) & 255u];
    ++counts->red[(command->value >> 16) & 255u];
    ++counts->literal[(command->value >> 8) & 255u];
    ++counts->blue[command->value & 255u];
  } else if (command->mode == 1u) {
    ++counts->literal[256u + 24u + command->value];
  } else {
    ++counts->literal[256u + (uint32_t)PrefixCode(command->length)];
    ++counts->distance[PrefixCode(command->value)];
  }
}

static WebPAcceleratorHistogramRequest MakeRequest(
    const WebPAcceleratorHistogramSpan* spans, size_t span_count,
    size_t command_count, Counts* counts) {
  WebPAcceleratorHistogramRequest request;
  request.spans = spans;
  request.span_count = span_count;
  request.command_count = command_count;
  request.cache_bits = 3;
  request.literal = counts->literal;
  request.literal_count = kLiteralCount;
  request.red = counts->red;
  request.blue = counts->blue;
  request.alpha = counts->alpha;
  request.distance = counts->distance;
  return request;
}

static int CheckCounts(const Counts* expected, const Counts* actual,
                       const char* label) {
  if (memcmp(expected, actual, sizeof(*expected)) != 0) {
    fprintf(stderr, "%s histogram mismatch\n", label);
    return 0;
  }
  return 1;
}

static int TestExactCounts(void) {
  static const WebPAcceleratorHistogramCommand kFirst[] = {
      {0, 0, 1, 0x00112233u}, {0, 0, 1, 0xff112233u},
      {1, 0, 1, 0u},          {1, 0, 1, 7u}};
  static const WebPAcceleratorHistogramCommand kSecond[] = {
      {2, 0, 1, 1u}, {2, 0, 2, 2u}, {2, 0, 3, 3u}};
  static const WebPAcceleratorHistogramCommand kThird[] = {
      {2, 0, 4095, 1u << 20}, {0, 0, 1, 0x7f00ff80u}};
  const WebPAcceleratorHistogramSpan spans[] = {
      {kFirst, sizeof(kFirst) / sizeof(kFirst[0])},
      {kSecond, sizeof(kSecond) / sizeof(kSecond[0])},
      {kThird, sizeof(kThird) / sizeof(kThird[0])}};
  const size_t command_count = sizeof(kFirst) / sizeof(kFirst[0]) +
                               sizeof(kSecond) / sizeof(kSecond[0]) +
                               sizeof(kThird) / sizeof(kThird[0]);
  Counts expected, actual, repeat;
  WebPAcceleratorHistogramRequest request;
  size_t i;
  memset(&expected, 0, sizeof(expected));
  memset(&actual, 0, sizeof(actual));
  memset(&repeat, 0, sizeof(repeat));
  for (i = 0; i < sizeof(kFirst) / sizeof(kFirst[0]); ++i) {
    AddExpected(&kFirst[i], &expected);
  }
  for (i = 0; i < sizeof(kSecond) / sizeof(kSecond[0]); ++i) {
    AddExpected(&kSecond[i], &expected);
  }
  for (i = 0; i < sizeof(kThird) / sizeof(kThird[0]); ++i) {
    AddExpected(&kThird[i], &expected);
  }
  request = MakeRequest(spans, sizeof(spans) / sizeof(spans[0]),
                        command_count, &actual);
  if (WebPAccelerateHistogram(&request) != WEBP_ACCELERATOR_SUCCESS ||
      !CheckCounts(&expected, &actual, "CUDA")) {
    return 0;
  }
  request = MakeRequest(spans, sizeof(spans) / sizeof(spans[0]),
                        command_count, &repeat);
  return WebPAccelerateHistogram(&request) == WEBP_ACCELERATOR_SUCCESS &&
         CheckCounts(&actual, &repeat, "repeat");
}

static int TestDeclinePreservesOutput(void) {
  const WebPAcceleratorHistogramCommand command = {0, 0, 1, 0xff112233u};
  const WebPAcceleratorHistogramSpan span = {&command, 1};
  Counts actual, before;
  WebPAcceleratorHistogramRequest request;
  memset(&actual, 0xa5, sizeof(actual));
  before = actual;
  WebPBenchmarkSetEnvironment("WEBP_CUDA_HISTOGRAM_MIN_COMMANDS", "18446744073709551615");
  request = MakeRequest(&span, 1, 1, &actual);
  if (WebPAccelerateHistogram(&request) != WEBP_ACCELERATOR_NOT_RUN ||
      memcmp(&actual, &before, sizeof(actual)) != 0) {
    fprintf(stderr, "declined histogram request modified output\n");
    return 0;
  }
  WebPBenchmarkSetEnvironment("WEBP_CUDA_HISTOGRAM_MIN_COMMANDS", "0");
  return 1;
}

static int TestInvalidPreservesOutput(void) {
  const WebPAcceleratorHistogramCommand command = {99, 0, 1, 0u};
  const WebPAcceleratorHistogramSpan span = {&command, 1};
  Counts actual, before;
  WebPAcceleratorHistogramRequest request;
  memset(&actual, 0x5a, sizeof(actual));
  before = actual;
  request = MakeRequest(&span, 1, 1, &actual);
  if (WebPAccelerateHistogram(&request) != WEBP_ACCELERATOR_ERROR ||
      memcmp(&actual, &before, sizeof(actual)) != 0) {
    fprintf(stderr, "invalid histogram request was not transactional\n");
    return 0;
  }
  return 1;
}

static int TestInvalidHashChainPreservesOutput(void) {
  const uint32_t pixels[4] = {1u, 2u, 3u, 4u};
  const int32_t chain[4] = {-1, 4, -1, -1};
  uint32_t candidates[4];
  uint32_t before[4];
  WebPAcceleratorHashChainRequest request;
  memset(candidates, 0xa5, sizeof(candidates));
  memcpy(before, candidates, sizeof(before));
  memset(&request, 0, sizeof(request));
  request.pixels = pixels;
  request.chain = chain;
  request.size = 4;
  request.xsize = 2;
  request.iter_max = 8;
  request.window_size = 32;
  request.candidates = candidates;
  if (WebPAccelerateHashChain(&request) != WEBP_ACCELERATOR_ERROR ||
      memcmp(candidates, before, sizeof(candidates)) != 0) {
    fprintf(stderr, "invalid hash predecessor was not transactional\n");
    return 0;
  }
  request.window_size = 1u << 20;
  if (WebPAccelerateHashChain(&request) != WEBP_ACCELERATOR_ERROR ||
      memcmp(candidates, before, sizeof(candidates)) != 0) {
    fprintf(stderr, "unrepresentable hash window was accepted\n");
    return 0;
  }
  return 1;
}

static int TestParallelCacheSearchOverride(void) {
  if (!WebPBenchmarkSetEnvironment("WEBP_CUDA_PARALLEL_CACHE_SEARCH", "0") ||
      WebPCUDAParallelCacheSearchEnabled()) {
    fprintf(stderr, "parallel cache-search disable override failed\n");
    return 0;
  }
  if (!WebPBenchmarkSetEnvironment("WEBP_CUDA_PARALLEL_CACHE_SEARCH", "1") ||
      !WebPCUDAParallelCacheSearchEnabled()) {
    fprintf(stderr, "parallel cache-search force override failed\n");
    return 0;
  }
  return WebPBenchmarkUnsetEnvironment("WEBP_CUDA_PARALLEL_CACHE_SEARCH");
}

int main(void) {
  if (!WebPBenchmarkHasCUDADevice()) return 77;
  if (!TestParallelCacheSearchOverride()) return 1;
  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "cuda");
  WebPBenchmarkSetEnvironment("WEBP_CUDA", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_HISTOGRAM", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_HISTOGRAM_MIN_COMMANDS", "0");
  WebPCUDAResetSuccessfulStages();
  if (!TestDeclinePreservesOutput() || !TestExactCounts() ||
      !TestInvalidPreservesOutput() ||
      !TestInvalidHashChainPreservesOutput()) {
    return 1;
  }
  if ((WebPCUDAGetSuccessfulStages() &
       WEBP_ACCELERATOR_STAGE_LOSSLESS_HISTOGRAM) == 0u) {
    fprintf(stderr, "CUDA histogram stage was not observed\n");
    return 1;
  }
  puts("PASS: exact CUDA histogram counts, spans, boundaries, fallback, and "
       "parallel cache-search override");
  return 0;
}
