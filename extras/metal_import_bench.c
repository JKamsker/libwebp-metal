// Copyright 2026
//
// Isolated RGB-to-YUV import benchmark driver for the Metal ablation matrix.
// This program reports individual samples; aggregation belongs in the harness.

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "webp/encode.h"

static double SecondsBetween(const struct timespec* const start,
                             const struct timespec* const end) {
  return (double)(end->tv_sec - start->tv_sec) +
         (double)(end->tv_nsec - start->tv_nsec) / 1000000000.0;
}

static int ParsePositiveInt(const char* const text, int* const value) {
  char* end = NULL;
  long parsed;
  errno = 0;
  parsed = strtol(text, &end, 10);
  if (errno != 0 || end == text || *end != '\0' || parsed <= 0 ||
      parsed > 1000000) {
    return 0;
  }
  *value = (int)parsed;
  return 1;
}

static void FillRGB(uint8_t* const rgb, size_t size) {
  uint32_t state = 0x6d2b79f5u;
  size_t i;
  for (i = 0; i < size; ++i) {
    state = state * 1664525u + 1013904223u;
    rgb[i] = (uint8_t)(state >> 24);
  }
}

static uint32_t SampleChecksum(const WebPPicture* const picture) {
  const int uv_width = (picture->width + 1) >> 1;
  const int uv_height = (picture->height + 1) >> 1;
  const size_t y_last = (size_t)(picture->height - 1) * picture->y_stride +
                        (picture->width - 1);
  const size_t uv_last = (size_t)(uv_height - 1) * picture->uv_stride +
                         (uv_width - 1);
  return (uint32_t)picture->y[0] | (uint32_t)picture->y[y_last] << 8 |
         (uint32_t)picture->u[uv_last] << 16 |
         (uint32_t)picture->v[uv_last] << 24;
}

int main(int argc, const char* argv[]) {
  int width = 3000;
  int height = 2000;
  int iterations = 50;
  int warmups = 1;
  size_t pixel_count;
  size_t rgb_size;
  uint8_t* rgb;
  int sample;

  if ((argc > 1 && !ParsePositiveInt(argv[1], &width)) ||
      (argc > 2 && !ParsePositiveInt(argv[2], &height)) ||
      (argc > 3 && !ParsePositiveInt(argv[3], &iterations)) ||
      (argc > 4 && !ParsePositiveInt(argv[4], &warmups)) || argc > 5) {
    fprintf(stderr, "usage: %s [width height iterations warmups]\n", argv[0]);
    return 2;
  }
  if (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
      strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0) {
    fprintf(stderr,
            "timed mode requires WEBP_BENCHMARK_SESSION=exclusive\n");
    return 2;
  }
  pixel_count = (size_t)width * (size_t)height;
  if (pixel_count > SIZE_MAX / 3u) {
    fprintf(stderr, "image dimensions overflow\n");
    return 2;
  }
  rgb_size = pixel_count * 3u;
  rgb = (uint8_t*)malloc(rgb_size);
  if (rgb == NULL) {
    fprintf(stderr, "RGB allocation failed\n");
    return 1;
  }
  FillRGB(rgb, rgb_size);

  printf("phase\tsample\tseconds\tchecksum\n");
  for (sample = -warmups; sample < iterations; ++sample) {
    WebPPicture picture;
    struct timespec start;
    struct timespec end;
    double seconds;
    uint32_t checksum;
    if (!WebPPictureInit(&picture)) {
      fprintf(stderr, "WebPPictureInit failed\n");
      free(rgb);
      return 1;
    }
    picture.width = width;
    picture.height = height;
    clock_gettime(CLOCK_MONOTONIC, &start);
    if (!WebPPictureImportRGB(&picture, rgb, width * 3)) {
      fprintf(stderr, "WebPPictureImportRGB failed: %d\n", picture.error_code);
      WebPPictureFree(&picture);
      free(rgb);
      return 1;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    seconds = SecondsBetween(&start, &end);
    checksum = SampleChecksum(&picture);
    printf("%s\t%d\t%.9f\t%08" PRIx32 "\n",
           sample < 0 ? "warmup" : "measure", sample, seconds, checksum);
    WebPPictureFree(&picture);
  }
  free(rgb);
  return 0;
}
