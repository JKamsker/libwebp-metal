// Copyright 2026
//
// Recorder-free process runner for the cache-size serial-sweep A/B protocol.

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#endif

#include "src/webp/encode.h"

static uint64_t NowNs(void) {
#if defined(__APPLE__)
  static mach_timebase_info_data_t timebase;
  const uint64_t ticks = mach_continuous_time();
  if (timebase.denom == 0) mach_timebase_info(&timebase);
  return ticks * timebase.numer / timebase.denom;
#else
  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  return (uint64_t)now.tv_sec * 1000000000ULL + (uint64_t)now.tv_nsec;
#endif
}

static int ReadToken(FILE* const input, char* const token,
                     size_t token_size) {
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

int main(int argc, char** argv) {
  const char* session = getenv("WEBP_BENCHMARK_SESSION");
  const char* input_path;
  const char* case_id;
  const char* lifecycle;
  const char* variant;
  int method, warmups, measured;
  uint8_t* rgb = NULL;
  int width = 0, height = 0;
  WebPConfig config;
  WebPPicture picture;
  int iteration;
  if (argc != 8) {
    fprintf(stderr,
            "usage: %s INPUT CASE LIFECYCLE VARIANT METHOD WARMUPS MEASURED\n",
            argv[0]);
    return 2;
  }
  if (session == NULL || strcmp(session, "exclusive") != 0) {
    fprintf(stderr,
            "cache-size serial-sweep runner refuses timing without "
            "WEBP_BENCHMARK_SESSION=exclusive\n");
    return 3;
  }
  input_path = argv[1];
  case_id = argv[2];
  lifecycle = argv[3];
  variant = argv[4];
  method = atoi(argv[5]);
  warmups = atoi(argv[6]);
  measured = atoi(argv[7]);
  if ((strcmp(lifecycle, "cold") != 0 && strcmp(lifecycle, "warm") != 0) ||
      (strcmp(variant, "baseline") != 0 &&
       strcmp(variant, "candidate") != 0) ||
      (method != 4 && method != 6) || warmups < 0 || measured <= 0 ||
      (strcmp(lifecycle, "cold") == 0 && (warmups != 0 || measured != 1)) ||
      (strcmp(lifecycle, "warm") == 0 && (warmups != 1 || measured != 7))) {
    fprintf(stderr, "invalid frozen runner arguments\n");
    return 4;
  }
  if (!ReadPPM(input_path, &rgb, &width, &height)) {
    fprintf(stderr, "failed to read frozen P6 input: %s\n", input_path);
    return 5;
  }
  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) return 6;
  config.lossless = 1;
  config.exact = 1;
  config.quality = 75.f;
  config.method = method;
  config.thread_level = 0;
  picture.use_argb = 1;
  picture.width = width;
  picture.height = height;
  if (!WebPPictureImportRGB(&picture, rgb, width * 3)) {
    free(rgb);
    return 7;
  }
  free(rgb);
  for (iteration = 0; iteration < warmups + measured; ++iteration) {
    WebPMemoryWriter writer;
    uint64_t start_ns, elapsed_ns, digest;
    WebPMemoryWriterInit(&writer);
    picture.writer = WebPMemoryWrite;
    picture.custom_ptr = &writer;
    start_ns = NowNs();
    if (!WebPEncode(&config, &picture)) {
      WebPMemoryWriterClear(&writer);
      WebPPictureFree(&picture);
      return 8;
    }
    elapsed_ns = NowNs() - start_ns;
    digest = Fnv1a64(writer.mem, writer.size);
    printf("{\"schema\":\"libwebp-cache-size-serial-sweep-sample-v1\","
           "\"case_id\":\"%s\",\"lifecycle\":\"%s\","
           "\"variant\":\"%s\",\"method\":%d,\"iteration\":%d,"
           "\"sample_role\":\"%s\",\"elapsed_ns\":%llu,"
           "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\"}\n",
           case_id, lifecycle, variant, method, iteration,
           iteration < warmups ? "warmup" : lifecycle,
           (unsigned long long)elapsed_ns, (unsigned long long)writer.size,
           (unsigned long long)digest);
    WebPMemoryWriterClear(&writer);
  }
  WebPPictureFree(&picture);
  return 0;
}
