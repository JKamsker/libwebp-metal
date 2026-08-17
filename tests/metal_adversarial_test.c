// Copyright 2026
//
// Adversarial public-API coverage for the private Metal encoder backend.

#define _POSIX_C_SOURCE 200809L

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "webp/decode.h"
#include "webp/encode.h"

typedef enum {
  FORMAT_RGB,
  FORMAT_BGR,
  FORMAT_RGBA,
  FORMAT_BGRA,
  FORMAT_RGBX,
  FORMAT_BGRX
} PixelFormat;

static int ChannelCount(PixelFormat format) {
  return format == FORMAT_RGB || format == FORMAT_BGR ? 3 : 4;
}

static void FillSource(uint8_t* source, int stride, int width, int height,
                       PixelFormat format, int translucent) {
  const int channels = ChannelCount(format);
  int x, y;
  memset(source, 0xa5, (size_t)stride * height);
  for (y = 0; y < height; ++y) {
    for (x = 0; x < width; ++x) {
      const uint8_t red = (uint8_t)(17 * x + 3 * y + 11);
      const uint8_t green = (uint8_t)(5 * x + 19 * y + 23);
      const uint8_t blue = (uint8_t)(13 * x + 7 * y + 47);
      const uint8_t alpha = translucent && x == width / 2 && y == height / 2
                                ? 127
                                : 255;
      uint8_t* const pixel = source + (size_t)y * stride + x * channels;
      switch (format) {
        case FORMAT_RGB:
          pixel[0] = red;
          pixel[1] = green;
          pixel[2] = blue;
          break;
        case FORMAT_BGR:
          pixel[0] = blue;
          pixel[1] = green;
          pixel[2] = red;
          break;
        case FORMAT_RGBA:
          pixel[0] = red;
          pixel[1] = green;
          pixel[2] = blue;
          pixel[3] = alpha;
          break;
        case FORMAT_BGRA:
          pixel[0] = blue;
          pixel[1] = green;
          pixel[2] = red;
          pixel[3] = alpha;
          break;
        case FORMAT_RGBX:
          pixel[0] = red;
          pixel[1] = green;
          pixel[2] = blue;
          pixel[3] = alpha;
          break;
        case FORMAT_BGRX:
          pixel[0] = blue;
          pixel[1] = green;
          pixel[2] = red;
          pixel[3] = alpha;
          break;
      }
    }
  }
}

static int Import(WebPPicture* picture, PixelFormat format,
                  const uint8_t* source, int stride) {
  switch (format) {
    case FORMAT_RGB:
      return WebPPictureImportRGB(picture, source, stride);
    case FORMAT_BGR:
      return WebPPictureImportBGR(picture, source, stride);
    case FORMAT_RGBA:
      return WebPPictureImportRGBA(picture, source, stride);
    case FORMAT_BGRA:
      return WebPPictureImportBGRA(picture, source, stride);
    case FORMAT_RGBX:
      return WebPPictureImportRGBX(picture, source, stride);
    case FORMAT_BGRX:
      return WebPPictureImportBGRX(picture, source, stride);
  }
  return 0;
}

static int Encode(const uint8_t* source, int stride, int width, int height,
                  PixelFormat format, int lossless,
                  WebPMemoryWriter* output) {
  WebPConfig config;
  WebPPicture picture;
  int ok;
  assert(WebPConfigInit(&config));
  assert(WebPPictureInit(&picture));
  config.lossless = lossless;
  config.quality = lossless ? 100.f : 75.f;
  config.method = lossless ? 4 : 6;
  config.exact = 1;
  picture.width = width;
  picture.height = height;
  picture.use_argb = lossless;
  assert(Import(&picture, format, source, stride));
  WebPMemoryWriterInit(output);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = output;
  ok = WebPEncode(&config, &picture);
  WebPPictureFree(&picture);
  return ok;
}

static void RequireEqual(const WebPMemoryWriter* left,
                         const WebPMemoryWriter* right) {
  assert(left->size == right->size);
  assert(memcmp(left->mem, right->mem, left->size) == 0);
}

static void CheckDimensionsStridesAndFormats(void) {
  static const int dimensions[][2] = {{1, 1}, {2, 3}, {17, 9}, {97, 65}};
  size_t dimension_index;
  int format;
  for (dimension_index = 0;
       dimension_index < sizeof(dimensions) / sizeof(dimensions[0]);
       ++dimension_index) {
    const int width = dimensions[dimension_index][0];
    const int height = dimensions[dimension_index][1];
    for (format = FORMAT_RGB; format <= FORMAT_BGRX; ++format) {
      const int stride = width * ChannelCount((PixelFormat)format) + 7;
      uint8_t* const source = (uint8_t*)malloc((size_t)stride * height);
      WebPMemoryWriter cpu;
      WebPMemoryWriter metal;
      assert(source != NULL);
      FillSource(source, stride, width, height, (PixelFormat)format, 0);

      assert(setenv("WEBP_ACCELERATOR", "none", 1) == 0);
      assert(Encode(source, stride, width, height, (PixelFormat)format, 1,
                    &cpu));
      assert(setenv("WEBP_ACCELERATOR", "metal", 1) == 0);
      assert(setenv("WEBP_METAL", "1", 1) == 0);
      assert(setenv("WEBP_METAL_MIN_PIXELS", "18446744073709551615", 1) ==
             0);
      assert(setenv("WEBP_METAL_HASH", "1", 1) == 0);
      assert(setenv("WEBP_METAL_HASH_MIN_PIXELS", "0", 1) == 0);
      assert(Encode(source, stride, width, height, (PixelFormat)format, 1,
                    &metal));
      RequireEqual(&cpu, &metal);
      WebPMemoryWriterClear(&cpu);
      WebPMemoryWriterClear(&metal);

      assert(setenv("WEBP_ACCELERATOR", "none", 1) == 0);
      assert(Encode(source, stride, width, height, (PixelFormat)format, 0,
                    &cpu));
      assert(setenv("WEBP_ACCELERATOR", "metal", 1) == 0);
      assert(setenv("WEBP_METAL_LOSSY", "1", 1) == 0);
      assert(setenv("WEBP_METAL_LOSSY_MIN_PIXELS", "0", 1) == 0);
      assert(Encode(source, stride, width, height, (PixelFormat)format, 0,
                    &metal));
      RequireEqual(&cpu, &metal);
      WebPMemoryWriterClear(&cpu);
      WebPMemoryWriterClear(&metal);
      free(source);
    }
  }
}

static void CheckTransformDecodeFidelity(void) {
  const int width = 17;
  const int height = 9;
  const int stride = width * 4 + 11;
  uint8_t* const source = (uint8_t*)malloc((size_t)stride * height);
  uint8_t* decoded;
  int decoded_width = 0;
  int decoded_height = 0;
  int x, y;
  WebPMemoryWriter metal;
  assert(source != NULL);
  FillSource(source, stride, width, height, FORMAT_RGBA, 0);
  assert(setenv("WEBP_ACCELERATOR", "metal", 1) == 0);
  assert(setenv("WEBP_METAL", "1", 1) == 0);
  assert(setenv("WEBP_METAL_MIN_PIXELS", "0", 1) == 0);
  assert(setenv("WEBP_METAL_HASH", "0", 1) == 0);
  assert(Encode(source, stride, width, height, FORMAT_RGBA, 1, &metal));
  decoded = WebPDecodeRGBA(metal.mem, metal.size, &decoded_width,
                           &decoded_height);
  assert(decoded != NULL && decoded_width == width && decoded_height == height);
  for (y = 0; y < height; ++y) {
    for (x = 0; x < width; ++x) {
      assert(memcmp(decoded + ((size_t)y * width + x) * 4,
                    source + (size_t)y * stride + x * 4, 4) == 0);
    }
  }
  WebPFree(decoded);
  WebPMemoryWriterClear(&metal);
  free(source);
}

static int AbortAfterMetal(int percent, const WebPPicture* picture) {
  (void)picture;
  return percent < 50;
}

static void CheckCancellationAndFallback(void) {
  const int width = 257;
  const int height = 129;
  const int stride = width * 4 + 3;
  uint8_t* const source = (uint8_t*)malloc((size_t)stride * height);
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter output;
  assert(source != NULL);
  FillSource(source, stride, width, height, FORMAT_RGBA, 1);
  assert(WebPConfigInit(&config));
  assert(WebPPictureInit(&picture));
  config.lossless = 1;
  config.method = 6;
  config.exact = 1;
  picture.width = width;
  picture.height = height;
  picture.use_argb = 1;
  assert(Import(&picture, FORMAT_RGBA, source, stride));
  WebPMemoryWriterInit(&output);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = &output;
  picture.progress_hook = AbortAfterMetal;
  assert(setenv("WEBP_ACCELERATOR", "metal", 1) == 0);
  assert(setenv("WEBP_METAL", "1", 1) == 0);
  assert(setenv("WEBP_METAL_MIN_PIXELS", "0", 1) == 0);
  assert(!WebPEncode(&config, &picture));
  assert(picture.error_code == VP8_ENC_ERROR_USER_ABORT);
  WebPMemoryWriterClear(&output);
  WebPPictureFree(&picture);

  assert(WebPPictureInit(&picture));
  picture.width = WEBP_MAX_DIMENSION + 1;
  picture.height = 1;
  picture.use_argb = 1;
  assert(!WebPEncode(&config, &picture));
  assert(picture.error_code == VP8_ENC_ERROR_BAD_DIMENSION);
  WebPPictureFree(&picture);
  free(source);
}

int main(int argc, char** argv) {
  assert(setenv("WEBP_METAL_VERBOSE", "1", 1) == 0);
  if (argc != 2) {
    fprintf(stderr, "usage: %s matrix|transform|cancellation\n", argv[0]);
    return 2;
  }
  if (strcmp(argv[1], "matrix") == 0) {
    CheckDimensionsStridesAndFormats();
  } else if (strcmp(argv[1], "transform") == 0) {
    CheckTransformDecodeFidelity();
  } else if (strcmp(argv[1], "cancellation") == 0) {
    CheckCancellationAndFallback();
  } else {
    return 2;
  }
  printf("PASS: Metal adversarial %s\n", argv[1]);
  return 0;
}
