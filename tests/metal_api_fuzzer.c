// Copyright 2026
//
// Bounded libFuzzer entry point for forced-Metal public encoder API coverage.

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#include "webp/decode.h"
#include "webp/encode.h"

static int AbortImmediately(int percent, const WebPPicture* picture) {
  (void)percent;
  (void)picture;
  return 0;
}

static void FillStructuredPixels(uint8_t* pixels, int stride, int width,
                                 int height, int format) {
  const int channels = format < 2 ? 3 : 4;
  int x, y;
  for (y = 0; y < height; ++y) {
    for (x = 0; x < width; ++x) {
      const uint8_t red = (uint8_t)(17 * x + 3 * y + 11);
      const uint8_t green = (uint8_t)(5 * x + 19 * y + 23);
      const uint8_t blue = (uint8_t)(13 * x + 7 * y + 47);
      uint8_t* const pixel = pixels + (size_t)y * stride + x * channels;
      if (format == 1 || format == 3 || format == 5) {
        pixel[0] = blue;
        pixel[1] = green;
        pixel[2] = red;
      } else {
        pixel[0] = red;
        pixel[1] = green;
        pixel[2] = blue;
      }
      if (channels == 4) pixel[3] = 255;
    }
  }
}

int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter output;
  uint8_t* pixels;
  uint8_t* decoded;
  int decoded_width = 0;
  int decoded_height = 0;
  int width, height, format, channels, stride;
  size_t pixel_bytes, i;
  int imported = 0;

  if (size < 8) return 0;
  width = 1 + data[0] % 33;
  height = 1 + data[1] % 25;
  format = data[2] % 6;
  channels = format < 2 ? 3 : 4;
  stride = width * channels + data[3] % 17;
  pixel_bytes = (size_t)stride * height;
  pixels = (uint8_t*)malloc(pixel_bytes);
  if (pixels == NULL) return 0;
  for (i = 0; i < pixel_bytes; ++i) pixels[i] = data[4 + i % (size - 4)];
  if (size > 8 && data[8] == 0x4d) {
    FillStructuredPixels(pixels, stride, width, height, format);
  }

  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) abort();
  config.lossless = data[4] & 1;
  config.quality = (float)(data[5] % 101);
  config.method = data[6] % 5;
  config.exact = data[7] & 1;
  picture.width = width;
  picture.height = height;
  picture.use_argb = config.lossless;
  switch (format) {
    case 0:
      imported = WebPPictureImportRGB(&picture, pixels, stride);
      break;
    case 1:
      imported = WebPPictureImportBGR(&picture, pixels, stride);
      break;
    case 2:
      imported = WebPPictureImportRGBA(&picture, pixels, stride);
      break;
    case 3:
      imported = WebPPictureImportBGRA(&picture, pixels, stride);
      break;
    case 4:
      imported = WebPPictureImportRGBX(&picture, pixels, stride);
      break;
    case 5:
      imported = WebPPictureImportBGRX(&picture, pixels, stride);
      break;
  }
  free(pixels);
  if (!imported) {
    WebPPictureFree(&picture);
    return 0;
  }

  WebPMemoryWriterInit(&output);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = &output;
  if (data[7] & 2) picture.progress_hook = AbortImmediately;
  if (!WebPEncode(&config, &picture)) {
    const WebPEncodingError error = picture.error_code;
    WebPMemoryWriterClear(&output);
    WebPPictureFree(&picture);
    if (error != VP8_ENC_ERROR_USER_ABORT &&
        error != VP8_ENC_ERROR_OUT_OF_MEMORY) {
      abort();
    }
    return 0;
  }

  decoded = WebPDecodeRGBA(output.mem, output.size, &decoded_width,
                           &decoded_height);
  if (decoded == NULL || decoded_width != width || decoded_height != height) {
    abort();
  }
  WebPFree(decoded);
  WebPMemoryWriterClear(&output);
  WebPPictureFree(&picture);
  return 0;
}

#if defined(WEBP_FUZZ_STANDALONE)
int main(void) {
  uint32_t state = 0x6d2b79f5u;
  uint8_t input[512];
  size_t run;
  for (run = 0; run < 3; ++run) {
    const size_t size = sizeof(input);
    size_t i;
    for (i = 0; i < size; ++i) {
      state ^= state << 13;
      state ^= state >> 17;
      state ^= state << 5;
      input[i] = (uint8_t)state;
    }
    // Curated, non-palette-like samples: two lossless imports reach transform
    // and hash dispatch, and one lossy import reaches RGB-to-YUV dispatch.
    input[0] = 32;  // width = 33, enough pixels to avoid palette bypass
    input[1] = 24;  // height = 25
    input[2] = (uint8_t)(run == 1 ? 2 : 0);
    input[3] = 7;
    input[4] = (uint8_t)(run < 2 ? 1 : 0);
    input[5] = (uint8_t)(run < 2 ? 100 : 75);
    input[6] = 4;
    input[7] = 1;
    input[8] = 0x4d;
    LLVMFuzzerTestOneInput(input, size);
  }
  return 0;
}
#endif
