// Copyright 2026
//
// Private diagnostic runner for the backref-cost attribution v2 pipeline.

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/backref_cost_attribution_v2_experiment_enc.h"
#include "src/webp/decode.h"
#include "src/webp/encode.h"

static int ReadToken(FILE* const input, char* const token, size_t token_size) {
  int c;
  size_t length = 0;
  do {
    c = fgetc(input);
    if (c == '#') {
      do {
        c = fgetc(input);
      } while (c != '\n' && c != EOF);
    }
  } while (c != EOF && isspace(c));
  if (c == EOF) return 0;
  do {
    if (length + 1 >= token_size) return 0;
    token[length++] = (char)c;
    c = fgetc(input);
  } while (c != EOF && !isspace(c));
  token[length] = '\0';
  return 1;
}

static int ReadPPM(const char* const path, uint8_t** const rgb,
                   int* const width, int* const height) {
  FILE* const input = fopen(path, "rb");
  char token[32];
  size_t byte_count;
  uint8_t* pixels;
  if (input == NULL) return 0;
  if (!ReadToken(input, token, sizeof(token)) || strcmp(token, "P6") != 0 ||
      !ReadToken(input, token, sizeof(token))) {
    fclose(input);
    return 0;
  }
  *width = atoi(token);
  if (!ReadToken(input, token, sizeof(token))) {
    fclose(input);
    return 0;
  }
  *height = atoi(token);
  if (!ReadToken(input, token, sizeof(token)) || atoi(token) != 255 ||
      *width <= 0 || *height <= 0) {
    fclose(input);
    return 0;
  }
  byte_count = (size_t)*width * (size_t)*height * 3u;
  pixels = (uint8_t*)malloc(byte_count);
  if (pixels == NULL || fread(pixels, 1, byte_count, input) != byte_count ||
      fgetc(input) != EOF) {
    free(pixels);
    fclose(input);
    return 0;
  }
  fclose(input);
  *rgb = pixels;
  return 1;
}

static uint64_t Fnv1a64(const uint8_t* data, size_t size) {
  uint64_t hash = 1469598103934665603ULL;
  while (size-- > 0) {
    hash ^= *data++;
    hash *= 1099511628211ULL;
  }
  return hash;
}

static int VariantMatchesEnvironment(const char* const variant) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT");
  if (strcmp(variant, "candidate") == 0) {
    return value != NULL && strcmp(value, "1") == 0 &&
           VP8LBackrefCostAttributionV2ExperimentEnabled();
  }
  return strcmp(variant, "baseline") == 0 && value == NULL &&
         !VP8LBackrefCostAttributionV2ExperimentEnabled();
}

static int PreparePicture(const char* const input_path, int method,
                          WebPConfig* const config,
                          WebPPicture* const picture) {
  uint8_t* rgb = NULL;
  int width = 0, height = 0;
  if ((method != 4 && method != 6) ||
      !ReadPPM(input_path, &rgb, &width, &height) ||
      !WebPConfigInit(config) || !WebPPictureInit(picture)) {
    free(rgb);
    return 0;
  }
  config->lossless = 1;
  config->exact = 1;
  config->quality = 75.f;
  config->method = method;
  config->thread_level = 0;
  picture->use_argb = 1;
  picture->width = width;
  picture->height = height;
  if (!WebPPictureImportRGB(picture, rgb, width * 3)) {
    free(rgb);
    WebPPictureFree(picture);
    return 0;
  }
  free(rgb);
  return 1;
}

static int Encode(WebPConfig* const config, WebPPicture* const picture,
                  WebPMemoryWriter* const writer) {
  WebPMemoryWriterInit(writer);
  picture->writer = WebPMemoryWrite;
  picture->custom_ptr = writer;
  return WebPEncode(config, picture);
}

static int Correctness(const char* const input_path, int method,
                       const char* const variant, const char* const output) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  uint8_t* expected = NULL;
  uint8_t* decoded = NULL;
  int expected_width = 0, expected_height = 0;
  int decoded_width = 0, decoded_height = 0;
  size_t expected_size;
  FILE* file;
  int ok;
  if (!VariantMatchesEnvironment(variant)) return 20;
  if (!ReadPPM(input_path, &expected, &expected_width, &expected_height) ||
      !PreparePicture(input_path, method, &config, &picture)) {
    free(expected);
    return 21;
  }
  ok = Encode(&config, &picture, &writer);
  WebPPictureFree(&picture);
  if (!ok) {
    free(expected);
    return 22;
  }
  decoded = WebPDecodeRGB(writer.mem, writer.size, &decoded_width,
                          &decoded_height);
  expected_size = (size_t)expected_width * expected_height * 3u;
  if (decoded == NULL || decoded_width != expected_width ||
      decoded_height != expected_height ||
      memcmp(decoded, expected, expected_size) != 0) {
    WebPFree(decoded);
    free(expected);
    WebPMemoryWriterClear(&writer);
    return 24;
  }
  WebPFree(decoded);
  free(expected);
  file = fopen(output, "wb");
  if (file == NULL) {
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  if (fwrite(writer.mem, 1, writer.size, file) != writer.size) {
    fclose(file);
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  if (fclose(file) != 0) {
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  WebPMemoryWriterClear(&writer);
  return 0;
}

static int Profile(const char* const input_path, const char* const case_id,
                   int method, const char* const variant, int warmups,
                   int measured) {
  const char* const session = getenv("WEBP_BENCHMARK_SESSION");
  const char* const timers =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_TIMERS");
  WebPConfig config;
  WebPPicture picture;
  int iteration;
  if (session == NULL || strcmp(session, "exclusive") != 0 ||
      timers == NULL || strcmp(timers, "1") != 0) {
    return 30;
  }
  if (!VariantMatchesEnvironment(variant) || warmups != 1 || measured != 4) {
    return 31;
  }
  if (!PreparePicture(input_path, method, &config, &picture)) return 32;
  for (iteration = 0; iteration < warmups + measured; ++iteration) {
    WebPMemoryWriter writer;
    uint64_t digest;
    if (!Encode(&config, &picture, &writer)) {
      WebPPictureFree(&picture);
      return 33;
    }
    digest = Fnv1a64(writer.mem, writer.size);
    printf("{\"schema\":\"libwebp-backref-cost-attribution-v2-output-v1\","
           "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
           "\"iteration\":%d,\"sample_role\":\"%s\","
           "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\"}\n",
           case_id, method, variant, iteration,
           iteration < warmups ? "warmup" : "retained",
           (unsigned long long)writer.size, (unsigned long long)digest);
    WebPMemoryWriterClear(&writer);
  }
  WebPPictureFree(&picture);
  return 0;
}

int main(int argc, char** argv) {
  if (argc == 2 && strcmp(argv[1], "guard") == 0) {
    // This command never reads an image or invokes WebPEncode.
    printf("{\"enabled\":%s}\n",
           VP8LBackrefCostAttributionV2ExperimentEnabled() ? "true" :
                                                             "false");
    return 0;
  }
  if (argc == 6 && strcmp(argv[1], "correctness") == 0) {
    return Correctness(argv[2], atoi(argv[3]), argv[4], argv[5]);
  }
  if (argc == 8 && strcmp(argv[1], "profile") == 0) {
    return Profile(argv[2], argv[3], atoi(argv[4]), argv[5], atoi(argv[6]),
                   atoi(argv[7]));
  }
  fputs("invalid backref-cost attribution v2 runner arguments\n", stderr);
  return 2;
}
