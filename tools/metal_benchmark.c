// Copyright 2026
//
// Internal runner for the Metal crossover experiment. This program deliberately
// owns only one matrix point. scripts/benchmark_metal.py is responsible for
// randomized pairing, cold process isolation, metadata, and analysis.

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "webp/decode.h"
#include "webp/encode.h"

#if !defined(WEBP_USE_METAL_CROSSOVER_EXPERIMENT)
#error "metal_benchmark.c requires WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT"
#endif

typedef enum { OP_TRANSFORM, OP_HASH, OP_LOSSLESS, OP_LOSSY } Operation;

typedef enum {
  CONTENT_FLAT,
  CONTENT_GRADIENT,
  CONTENT_GRAPHIC,
  CONTENT_PHOTO,
  CONTENT_TEXTURE,
  CONTENT_NOISE
} Content;

typedef struct {
  Operation operation;
  Content content;
  const char* operation_name;
  const char* content_name;
  const char* variant;
  int width;
  int height;
  int method;
  uint32_t seed;
  int warmups;
  int samples;
  int measure;
  const char* artifact_path;
} Options;

static void Usage(const char* program) {
  fprintf(stderr,
          "Usage: %s --operation transform|hash|lossless|lossy "
          "--variant cpu|metal "
          "--content flat|gradient|graphic|photo|texture|noise "
          "--width N --height N "
          "--method 0..6 --seed N [--warmups N] [--samples N] [--measure] "
          "[--artifact PATH]\n",
          program);
}

static int ParseInt(const char* value, int minimum, int maximum, int* out) {
  char* end = NULL;
  long parsed;
  errno = 0;
  parsed = strtol(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' || parsed < minimum ||
      parsed > maximum) {
    return 0;
  }
  *out = (int)parsed;
  return 1;
}

static int ParseOptions(int argc, const char* const argv[], Options* options) {
  int i;
  int have_operation = 0, have_content = 0, have_variant = 0;
  memset(options, 0, sizeof(*options));
  options->samples = 1;
  options->method = -1;
  for (i = 1; i < argc; ++i) {
    const char* flag = argv[i];
    const char* value = (i + 1 < argc) ? argv[i + 1] : NULL;
    if (!strcmp(flag, "--measure")) {
      options->measure = 1;
    } else if (value == NULL) {
      return 0;
    } else if (!strcmp(flag, "--operation")) {
      ++i;
      options->operation_name = value;
      if (!strcmp(value, "transform"))
        options->operation = OP_TRANSFORM;
      else if (!strcmp(value, "hash"))
        options->operation = OP_HASH;
      else if (!strcmp(value, "lossless"))
        options->operation = OP_LOSSLESS;
      else if (!strcmp(value, "lossy"))
        options->operation = OP_LOSSY;
      else
        return 0;
      have_operation = 1;
    } else if (!strcmp(flag, "--variant")) {
      ++i;
      if (strcmp(value, "cpu") && strcmp(value, "metal")) return 0;
      options->variant = value;
      have_variant = 1;
    } else if (!strcmp(flag, "--content")) {
      ++i;
      options->content_name = value;
      if (!strcmp(value, "flat"))
        options->content = CONTENT_FLAT;
      else if (!strcmp(value, "gradient"))
        options->content = CONTENT_GRADIENT;
      else if (!strcmp(value, "graphic"))
        options->content = CONTENT_GRAPHIC;
      else if (!strcmp(value, "photo"))
        options->content = CONTENT_PHOTO;
      else if (!strcmp(value, "texture"))
        options->content = CONTENT_TEXTURE;
      else if (!strcmp(value, "noise"))
        options->content = CONTENT_NOISE;
      else
        return 0;
      have_content = 1;
    } else if (!strcmp(flag, "--width")) {
      ++i;
      if (!ParseInt(value, 1, 32768, &options->width)) return 0;
    } else if (!strcmp(flag, "--height")) {
      ++i;
      if (!ParseInt(value, 1, 32768, &options->height)) return 0;
    } else if (!strcmp(flag, "--method")) {
      ++i;
      if (!ParseInt(value, 0, 6, &options->method)) return 0;
    } else if (!strcmp(flag, "--seed")) {
      int parsed;
      ++i;
      if (!ParseInt(value, 0, 0x7fffffff, &parsed)) return 0;
      options->seed = (uint32_t)parsed;
    } else if (!strcmp(flag, "--warmups")) {
      ++i;
      if (!ParseInt(value, 0, 1000, &options->warmups)) return 0;
    } else if (!strcmp(flag, "--samples")) {
      ++i;
      if (!ParseInt(value, 1, 1000, &options->samples)) return 0;
    } else if (!strcmp(flag, "--artifact")) {
      ++i;
      options->artifact_path = value;
    } else {
      return 0;
    }
  }
  return have_operation && have_content && have_variant && options->width > 0 &&
         options->height > 0 && options->method >= 0;
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

static uint8_t ClampByte(int value) {
  return (uint8_t)(value < 0 ? 0 : value > 255 ? 255 : value);
}

static int MaxInt(int a, int b) { return a > b ? a : b; }

static void GeneratePixels(const Options* options, uint8_t* rgba) {
  uint32_t random_state = options->seed ^ 0xa5a5a5a5u;
  int x, y;
  for (y = 0; y < options->height; ++y) {
    uint32_t texture_state =
        (0x9e3779b9u ^ ((uint32_t)y * 0x85ebca6bu) ^ options->seed);
    for (x = 0; x < options->width; ++x) {
      uint8_t r, g, b;
      const size_t offset = ((size_t)y * options->width + x) * 4u;
      if (options->content == CONTENT_FLAT) {
        r = (uint8_t)(options->seed * 17u + 31u);
        g = (uint8_t)(options->seed * 29u + 73u);
        b = (uint8_t)(options->seed * 43u + 127u);
      } else if (options->content == CONTENT_GRADIENT) {
        r = (uint8_t)((255u * (uint32_t)x) /
                      (uint32_t)(options->width > 1 ? options->width - 1 : 1));
        g = (uint8_t)((255u * (uint32_t)y) /
                      (uint32_t)(options->height > 1 ? options->height - 1
                                                     : 1));
        b = (uint8_t)(((uint32_t)r + g + (options->seed & 255u)) / 3u);
      } else if (options->content == CONTENT_GRAPHIC) {
        static const uint8_t palette[6][3] = {{238, 238, 232}, {38, 62, 96},
                                              {225, 82, 65},   {247, 190, 66},
                                              {50, 150, 105},  {103, 78, 167}};
        unsigned index =
            ((unsigned)x / (unsigned)MaxInt(8, options->width / 12) +
             3u * ((unsigned)y / (unsigned)MaxInt(8, options->height / 9)) +
             options->seed) %
            6u;
        if (abs(x - options->width / 2) < MaxInt(2, options->width / 150) ||
            abs(y - options->height / 2) < MaxInt(2, options->height / 150)) {
          index = 1;
        }
        r = palette[index][0];
        g = palette[index][1];
        b = palette[index][2];
      } else if (options->content == CONTENT_PHOTO) {
        const int noise =
            ((x * 17 + y * 29 + ((x ^ y) * 7) + (int)options->seed * 13) & 31) -
            16;
        r = ClampByte(180 * x / MaxInt(1, options->width - 1) + 35 + noise);
        g = ClampByte(150 * y / MaxInt(1, options->height - 1) + 45 +
                      noise / 2);
        b = ClampByte(((int)r + g) / 2 + ((x / 64 + y / 64) & 15));
      } else if (options->content == CONTENT_TEXTURE) {
        texture_state ^= texture_state << 13;
        texture_state ^= texture_state >> 17;
        texture_state ^= texture_state << 5;
        r = (uint8_t)texture_state;
        g = (uint8_t)(texture_state >> 8);
        b = (uint8_t)(texture_state >> 16);
      } else {
        const uint32_t random = Random32(&random_state);
        r = (uint8_t)random;
        g = (uint8_t)(random >> 8);
        b = (uint8_t)(random >> 16);
      }
      rgba[offset + 0] = r;
      rgba[offset + 1] = g;
      rgba[offset + 2] = b;
      rgba[offset + 3] = 255u;
    }
  }
}

static uint64_t HashBytes(const uint8_t* bytes, size_t size) {
  uint64_t hash = UINT64_C(1469598103934665603);
  size_t i;
  for (i = 0; i < size; ++i) {
    hash ^= bytes[i];
    hash *= UINT64_C(1099511628211);
  }
  return hash;
}

static uint64_t MonotonicNanoseconds(void) {
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

static void ConfigureDispatch(const Options* options) {
  const int metal = !strcmp(options->variant, "metal");
  const char* maximum = "18446744073709551615";
  setenv("WEBP_METAL_VERBOSE", metal ? "1" : "0", 1);
  setenv("WEBP_METAL", "0", 1);
  setenv("WEBP_METAL_HASH", "0", 1);
  setenv("WEBP_METAL_LOSSY", "0", 1);
  setenv("WEBP_METAL_MIN_PIXELS", maximum, 1);
  setenv("WEBP_METAL_HASH_MIN_PIXELS", maximum, 1);
  setenv("WEBP_METAL_LOSSY_MIN_PIXELS", maximum, 1);
  if (!metal) return;
  if (options->operation == OP_TRANSFORM) {
    setenv("WEBP_METAL", "1", 1);
    setenv("WEBP_METAL_MIN_PIXELS", "0", 1);
  } else if (options->operation == OP_HASH) {
    // The current shared lossless Metal state compiles the transform pipeline
    // before lazily compiling the hash pipeline. A future accelerator interface
    // can remove that setup coupling without changing the harness protocol.
    setenv("WEBP_METAL", "1", 1);
    setenv("WEBP_METAL_HASH", "1", 1);
    setenv("WEBP_METAL_HASH_MIN_PIXELS", "0", 1);
  } else if (options->operation == OP_LOSSLESS) {
    setenv("WEBP_METAL", "1", 1);
    setenv("WEBP_METAL_MIN_PIXELS", "0", 1);
    setenv("WEBP_METAL_HASH", "1", 1);
    setenv("WEBP_METAL_HASH_MIN_PIXELS", "0", 1);
  } else {
    setenv("WEBP_METAL_LOSSY", "1", 1);
    setenv("WEBP_METAL_LOSSY_MIN_PIXELS", "0", 1);
  }
}

static int EncodeOnce(const Options* options, const uint8_t* rgba,
                      const char* artifact_path, uint64_t* elapsed_ns,
                      uint64_t* encoded_hash, uint64_t* decoded_hash,
                      size_t* encoded_size) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  uint8_t* decoded = NULL;
  uint64_t start = 0, end = 0;
  int decoded_width = 0, decoded_height = 0;
  int ok = 0;

  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) return 0;
  config.lossless = options->operation != OP_LOSSY;
  config.method = options->method;
  config.quality = 75.f;
  config.exact = 1;
  if (!WebPValidateConfig(&config)) return 0;
  picture.width = options->width;
  picture.height = options->height;
  picture.use_argb = config.lossless;
  WebPMemoryWriterInit(&writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = &writer;

  if (options->measure) start = MonotonicNanoseconds();
  if (!WebPPictureImportRGBA(&picture, rgba, options->width * 4) ||
      !WebPEncode(&config, &picture)) {
    goto cleanup;
  }
  if (options->measure) {
    end = MonotonicNanoseconds();
    if (start == 0 || end < start) goto cleanup;
  }

  if (artifact_path != NULL) {
    FILE* artifact = fopen(artifact_path, "wb");
    size_t written;
    int close_result;
    if (artifact == NULL) goto cleanup;
    written = fwrite(writer.mem, 1, writer.size, artifact);
    close_result = fclose(artifact);
    if (written != writer.size || close_result != 0) {
      goto cleanup;
    }
  }

  decoded =
      WebPDecodeRGBA(writer.mem, writer.size, &decoded_width, &decoded_height);
  if (decoded == NULL || decoded_width != options->width ||
      decoded_height != options->height) {
    goto cleanup;
  }
  *elapsed_ns = options->measure ? end - start : 0;
  *encoded_hash = HashBytes(writer.mem, writer.size);
  *decoded_hash =
      HashBytes(decoded, (size_t)decoded_width * decoded_height * 4u);
  *encoded_size = writer.size;
  ok = 1;

cleanup:
  WebPFree(decoded);
  WebPPictureFree(&picture);
  WebPMemoryWriterClear(&writer);
  return ok;
}

int main(int argc, const char* const argv[]) {
  Options options;
  uint8_t* rgba;
  uint64_t input_hash;
  uint64_t first_encoded_hash = 0, first_decoded_hash = 0;
  int sequence;
  if (!ParseOptions(argc, argv, &options)) {
    Usage(argv[0]);
    return 2;
  }
  if (getenv("WEBP_METAL_CROSSOVER_EXPERIMENT") == NULL ||
      strcmp(getenv("WEBP_METAL_CROSSOVER_EXPERIMENT"), "1") != 0) {
    fprintf(stderr,
            "runner requires WEBP_METAL_CROSSOVER_EXPERIMENT=1; rebuild "
            "with WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT if unavailable\n");
    return 2;
  }
  if (options.measure &&
      (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
       strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0)) {
    fprintf(stderr,
            "timed mode requires WEBP_BENCHMARK_SESSION=exclusive\n");
    return 2;
  }
  if ((size_t)options.width > SIZE_MAX / (size_t)options.height / 4u) {
    fprintf(stderr, "image dimensions overflow\n");
    return 2;
  }
  rgba = (uint8_t*)malloc((size_t)options.width * options.height * 4u);
  if (rgba == NULL) {
    fprintf(stderr, "input allocation failed\n");
    return 2;
  }
  GeneratePixels(&options, rgba);
  input_hash = HashBytes(rgba, (size_t)options.width * options.height * 4u);
  ConfigureDispatch(&options);

  for (sequence = -options.warmups; sequence < options.samples; ++sequence) {
    uint64_t elapsed_ns, encoded_hash, decoded_hash;
    size_t encoded_size;
    if (!EncodeOnce(&options, rgba,
                    sequence == 0 ? options.artifact_path : NULL, &elapsed_ns,
                    &encoded_hash, &decoded_hash, &encoded_size)) {
      fprintf(stderr, "encode failed at sequence %d\n", sequence);
      free(rgba);
      return 1;
    }
    if (options.operation != OP_LOSSY && decoded_hash != input_hash) {
      fprintf(stderr, "lossless decode mismatch at sequence %d\n", sequence);
      free(rgba);
      return 1;
    }
    if (sequence < 0) continue;
    if (sequence == 0) {
      first_encoded_hash = encoded_hash;
      first_decoded_hash = decoded_hash;
    } else if (encoded_hash != first_encoded_hash ||
               decoded_hash != first_decoded_hash) {
      fprintf(stderr, "non-deterministic output at sequence %d\n", sequence);
      free(rgba);
      return 1;
    }
    printf(
        "{\"record\":\"sample\",\"operation\":\"%s\","
        "\"variant\":\"%s\",\"content\":\"%s\",\"width\":%d,"
        "\"height\":%d,\"method\":%d,\"seed\":%" PRIu32
        ","
        "\"sequence\":%d,\"measured\":%s,\"elapsed_ns\":%" PRIu64
        ","
        "\"input_hash\":\"%016" PRIx64
        "\","
        "\"encoded_hash\":\"%016" PRIx64
        "\","
        "\"decoded_hash\":\"%016" PRIx64
        "\","
        "\"encoded_size\":%zu}\n",
        options.operation_name, options.variant, options.content_name,
        options.width, options.height, options.method, options.seed, sequence,
        options.measure ? "true" : "false", elapsed_ns, input_hash,
        encoded_hash, decoded_hash, encoded_size);
  }
  free(rgba);
  return 0;
}
