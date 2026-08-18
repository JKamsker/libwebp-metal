// Copyright 2026
//
// Internal warm-process benchmark for CUDA compile-time strategy comparisons.

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "src/enc/cuda_enc.h"
#include "src/enc/vp8li_enc.h"
#include "webp/encode.h"

typedef enum { OP_COLOR, OP_HASH, OP_NEAR_LOSSLESS, OP_LOSSLESS, OP_LOSSY }
    Operation;

typedef struct {
  Operation operation;
  const char* operation_name;
  const char* variant;
  int width;
  int height;
  int method;
  int near_lossless_quality;
  int near_lossless_quality_set;
  int verify_only;
  int warmups;
  int samples;
  uint32_t seed;
} Options;

static void Usage(const char* program) {
  fprintf(stderr,
          "Usage: %s --operation color|hash|near-lossless|lossless|lossy "
          "--variant cpu|cuda --width N --height N --method 0..6 "
          "[--quality 0..99 (near-lossless only)] "
          "[--warmups N] [--samples N] [--seed N] [--verify-only]\n",
          program);
}

static int ParseInt(const char* text, int minimum, int maximum, int* value) {
  char* end = NULL;
  long parsed;
  errno = 0;
  parsed = strtol(text, &end, 10);
  if (errno != 0 || end == text || *end != '\0' || parsed < minimum ||
      parsed > maximum) {
    return 0;
  }
  *value = (int)parsed;
  return 1;
}

static int ParseOptions(int argc, const char* const argv[], Options* options) {
  int i;
  memset(options, 0, sizeof(*options));
  options->method = 4;
  options->near_lossless_quality = 40;
  options->warmups = 2;
  options->samples = 7;
  options->seed = 1;
  for (i = 1; i < argc; ++i) {
    const char* const flag = argv[i];
    const char* value;
    if (!strcmp(flag, "--verify-only")) {
      options->verify_only = 1;
      continue;
    }
    value = i + 1 < argc ? argv[++i] : NULL;
    if (value == NULL) return 0;
    if (!strcmp(flag, "--operation")) {
      options->operation_name = value;
      if (!strcmp(value, "color"))
        options->operation = OP_COLOR;
      else if (!strcmp(value, "hash"))
        options->operation = OP_HASH;
      else if (!strcmp(value, "near-lossless")) {
#if (WEBP_NEAR_LOSSLESS == 1)
        options->operation = OP_NEAR_LOSSLESS;
#else
        return 0;
#endif
      }
      else if (!strcmp(value, "lossless"))
        options->operation = OP_LOSSLESS;
      else if (!strcmp(value, "lossy"))
        options->operation = OP_LOSSY;
      else
        return 0;
    } else if (!strcmp(flag, "--variant")) {
      if (strcmp(value, "cpu") && strcmp(value, "cuda")) return 0;
      options->variant = value;
    } else if (!strcmp(flag, "--width")) {
      if (!ParseInt(value, 1, 32768, &options->width)) return 0;
    } else if (!strcmp(flag, "--height")) {
      if (!ParseInt(value, 1, 32768, &options->height)) return 0;
    } else if (!strcmp(flag, "--method")) {
      if (!ParseInt(value, 0, 6, &options->method)) return 0;
    } else if (!strcmp(flag, "--quality")) {
      if (!ParseInt(value, 0, 99, &options->near_lossless_quality)) return 0;
      options->near_lossless_quality_set = 1;
    } else if (!strcmp(flag, "--warmups")) {
      if (!ParseInt(value, 0, 1000, &options->warmups)) return 0;
    } else if (!strcmp(flag, "--samples")) {
      if (!ParseInt(value, 1, 1000, &options->samples)) return 0;
    } else if (!strcmp(flag, "--seed")) {
      int seed;
      if (!ParseInt(value, 0, 0x7fffffff, &seed)) return 0;
      options->seed = (uint32_t)seed;
    } else {
      return 0;
    }
  }
  return options->operation_name != NULL && options->variant != NULL &&
         options->width > 0 && options->height > 0 &&
         (!options->near_lossless_quality_set ||
          options->operation == OP_NEAR_LOSSLESS);
}

static uint32_t Random32(uint32_t* state) {
  uint32_t x = *state;
  if (x == 0) x = 0x9e3779b9u;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  *state = x;
  return x;
}

static void GenerateRGBA(const Options* options, uint8_t* rgba) {
  uint32_t random = options->seed;
  int x, y;
  for (y = 0; y < options->height; ++y) {
    for (x = 0; x < options->width; ++x) {
      const size_t offset = ((size_t)y * options->width + x) * 4u;
      const uint32_t noise = Random32(&random);
      rgba[offset + 0] = (uint8_t)((x * 5 + y * 3 + noise % 17u) & 255);
      rgba[offset + 1] = (uint8_t)((x * 2 + y * 7 + (noise >> 8) % 23u) & 255);
      rgba[offset + 2] = (uint8_t)((x + y * 11 + (noise >> 16) % 29u) & 255);
      rgba[offset + 3] = 255u;
    }
  }
}

static uint64_t HashBytes(const uint8_t* data, size_t size) {
  uint64_t hash = UINT64_C(1469598103934665603);
  size_t i;
  for (i = 0; i < size; ++i) {
    hash = (hash ^ data[i]) * UINT64_C(1099511628211);
  }
  return hash;
}

static uint64_t NowNanoseconds(void) {
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

static void ConfigureDispatch(const Options* options) {
  const int cuda = !strcmp(options->variant, "cuda");
  setenv("WEBP_ACCELERATOR", cuda ? "cuda" : "none", 1);
  setenv("WEBP_CUDA", cuda ? "1" : "0", 1);
  setenv("WEBP_CUDA_COLOR",
         cuda && (options->operation == OP_COLOR ||
                  options->operation == OP_LOSSLESS)
             ? "1"
             : "0",
         1);
  setenv("WEBP_CUDA_HASH",
         cuda && (options->operation == OP_HASH ||
                  options->operation == OP_LOSSLESS)
             ? "1"
             : "0",
         1);
  setenv("WEBP_CUDA_LOSSY",
         cuda && options->operation == OP_LOSSY ? "1" : "0", 1);
  setenv("WEBP_CUDA_NEAR_LOSSLESS",
         cuda && options->operation == OP_NEAR_LOSSLESS ? "1" : "0", 1);
  setenv("WEBP_CUDA_LOSSY_ANALYSIS",
         cuda && options->operation == OP_LOSSY ? "1" : "0", 1);
  setenv("WEBP_CUDA_RESIDENT_LOSSLESS",
         cuda && options->operation == OP_LOSSLESS ? "1" : "0", 1);
  setenv("WEBP_CUDA_MIN_PIXELS", "0", 1);
  setenv("WEBP_CUDA_HASH_MIN_PIXELS", "0", 1);
  setenv("WEBP_CUDA_LOSSY_MIN_PIXELS", "0", 1);
  setenv("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS", "0", 1);
  setenv("WEBP_CUDA_LOSSY_ANALYSIS_MIN_MACROBLOCKS", "0", 1);
}

static int Encode(const Options* options, const uint8_t* rgba,
                  uint64_t* elapsed_ns, uint64_t* output_hash,
                  size_t* output_size) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  uint64_t begin, end;
  int ok = 0;
  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) return 0;
  config.lossless = options->operation != OP_LOSSY;
  config.exact = 1;
  config.method = options->method;
  config.quality = 75.f;
  if (!WebPValidateConfig(&config)) return 0;
  picture.width = options->width;
  picture.height = options->height;
  picture.use_argb = config.lossless;
  WebPMemoryWriterInit(&writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = &writer;
  begin = NowNanoseconds();
  if (!WebPPictureImportRGBA(&picture, rgba, options->width * 4) ||
      !WebPEncode(&config, &picture)) {
    goto cleanup;
  }
  end = NowNanoseconds();
  if (begin == 0 || end <= begin) goto cleanup;
  *elapsed_ns = end - begin;
  *output_hash = HashBytes(writer.mem, writer.size);
  *output_size = writer.size;
  ok = 1;
cleanup:
  WebPPictureFree(&picture);
  WebPMemoryWriterClear(&writer);
  return ok;
}

#if (WEBP_NEAR_LOSSLESS == 1)
static int PreprocessNearLossless(const Options* options, const uint8_t* rgba,
                                  uint64_t* elapsed_ns,
                                  uint64_t* output_hash,
                                  size_t* output_size) {
  WebPPicture picture;
  uint32_t* output = NULL;
  const size_t pixel_count = (size_t)options->width * options->height;
  uint64_t begin, end;
  int ok = 0;
  if (!WebPPictureInit(&picture)) return 0;
  picture.width = options->width;
  picture.height = options->height;
  picture.use_argb = 1;
  output = (uint32_t*)malloc(pixel_count * sizeof(*output));
  if (output == NULL ||
      !WebPPictureImportRGBA(&picture, rgba, options->width * 4)) {
    goto cleanup;
  }
  begin = NowNanoseconds();
  if (!VP8ApplyNearLossless(&picture, options->near_lossless_quality, output)) {
    goto cleanup;
  }
  end = NowNanoseconds();
  if (begin == 0 || end <= begin) goto cleanup;
  *elapsed_ns = end - begin;
  *output_size = pixel_count * sizeof(*output);
  *output_hash = HashBytes((const uint8_t*)output, *output_size);
  ok = 1;
cleanup:
  free(output);
  WebPPictureFree(&picture);
  return ok;
}
#endif

static int RunOperation(const Options* options, const uint8_t* rgba,
                        uint64_t* elapsed_ns, uint64_t* output_hash,
                        size_t* output_size) {
#if (WEBP_NEAR_LOSSLESS == 1)
  if (options->operation == OP_NEAR_LOSSLESS) {
    return PreprocessNearLossless(options, rgba, elapsed_ns, output_hash,
                                  output_size);
  }
#endif
  return Encode(options, rgba, elapsed_ns, output_hash, output_size);
}

static uint32_t RequiredCUDAStages(Operation operation) {
  switch (operation) {
    case OP_COLOR:
      return WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM;
    case OP_HASH:
      return WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN;
    case OP_NEAR_LOSSLESS:
      return WEBP_ACCELERATOR_STAGE_NEAR_LOSSLESS;
    case OP_LOSSLESS:
      return WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM |
             WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN;
    case OP_LOSSY:
      return WEBP_ACCELERATOR_STAGE_RGB_TO_YUV |
             WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS;
  }
  return 0;
}

int main(int argc, const char* const argv[]) {
  Options options;
  uint8_t* rgba;
  char near_lossless_quality[16];
  uint64_t reference_hash = 0;
  int sequence;
  if (!ParseOptions(argc, argv, &options)) {
    Usage(argv[0]);
    return 2;
  }
  if ((size_t)options.width > SIZE_MAX / (size_t)options.height / 4u) {
    fprintf(stderr, "image dimensions overflow\n");
    return 2;
  }
  rgba = (uint8_t*)malloc((size_t)options.width * options.height * 4u);
  if (rgba == NULL) return 2;
  GenerateRGBA(&options, rgba);
  if (options.operation == OP_NEAR_LOSSLESS) {
    snprintf(near_lossless_quality, sizeof(near_lossless_quality), "%d",
             options.near_lossless_quality);
  } else {
    snprintf(near_lossless_quality, sizeof(near_lossless_quality), "null");
  }
  ConfigureDispatch(&options);
  if (!strcmp(options.variant, "cuda")) {
    uint64_t elapsed_ns, output_hash;
    size_t output_size;
    const uint32_t required = RequiredCUDAStages(options.operation);
    uint32_t observed;
    WebPCUDAResetSuccessfulStages();
    if (!RunOperation(&options, rgba, &elapsed_ns, &output_hash,
                      &output_size)) {
      fprintf(stderr, "CUDA stage preflight failed\n");
      free(rgba);
      return 1;
    }
    observed = WebPCUDAGetSuccessfulStages();
    if ((observed & required) != required) {
      fprintf(stderr,
              "CUDA stage preflight fell back: required=0x%08x "
              "observed=0x%08x\n",
              required, observed);
      free(rgba);
      return 1;
    }
  }
  if (options.verify_only) {
    if (!strcmp(options.variant, "cpu")) {
      uint64_t elapsed_ns, output_hash;
      size_t output_size;
      if (!RunOperation(&options, rgba, &elapsed_ns, &output_hash,
                        &output_size)) {
        fprintf(stderr, "CPU verification failed\n");
        free(rgba);
        return 1;
      }
    }
    fprintf(stderr, "verified %s %s operation\n", options.variant,
            options.operation_name);
    free(rgba);
    return 0;
  }
  for (sequence = -options.warmups; sequence < options.samples; ++sequence) {
    uint64_t elapsed_ns, output_hash;
    size_t output_size;
    const int ok = RunOperation(&options, rgba, &elapsed_ns, &output_hash,
                                &output_size);
    if (!ok) {
      fprintf(stderr, "%s failed at sequence %d\n",
              options.operation == OP_NEAR_LOSSLESS ? "preprocessing"
                                                    : "encode",
              sequence);
      free(rgba);
      return 1;
    }
    if (sequence < 0) continue;
    if (sequence == 0) reference_hash = output_hash;
    if (output_hash != reference_hash) {
      fprintf(stderr, "non-deterministic output at sequence %d\n", sequence);
      free(rgba);
      return 1;
    }
    printf("{\"operation\":\"%s\",\"variant\":\"%s\","
           "\"width\":%d,\"height\":%d,\"method\":%d,"
           "\"encoder_quality\":75,\"near_lossless_quality\":%s,"
           "\"sequence\":%d,\"elapsed_ns\":%" PRIu64 ","
           "\"output_hash\":\"%016" PRIx64 "\",\"output_size\":%zu}\n",
           options.operation_name, options.variant, options.width,
           options.height, options.method, near_lossless_quality,
           sequence, elapsed_ns, output_hash, output_size);
  }
  free(rgba);
  return 0;
}
