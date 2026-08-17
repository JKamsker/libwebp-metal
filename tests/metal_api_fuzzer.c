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
  width = 1 + data[0] % 17;
  height = 1 + data[1] % 13;
  format = data[2] % 6;
  channels = format < 2 ? 3 : 4;
  stride = width * channels + data[3] % 17;
  pixel_bytes = (size_t)stride * height;
  pixels = (uint8_t*)malloc(pixel_bytes);
  if (pixels == NULL) return 0;
  for (i = 0; i < pixel_bytes; ++i) pixels[i] = data[4 + i % (size - 4)];

  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) abort();
  config.lossless = data[4] & 1;
  config.quality = (float)(data[5] % 76);
  config.method = data[6] % 2;
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
  for (run = 0; run < 8; ++run) {
    const size_t size = 8 + run % (sizeof(input) - 7);
    size_t i;
    for (i = 0; i < size; ++i) {
      state ^= state << 13;
      state ^= state >> 17;
      state ^= state << 5;
      input[i] = (uint8_t)state;
    }
    input[2] = (uint8_t)(run % 6);
    // Keep the bounded sanitizer replay fast; libFuzzer mode still mutates
    // this bit and covers lossless configurations.
    input[4] &= (uint8_t)~1u;
    input[5] = 50;
    input[6] = 0;
    input[7] = (uint8_t)((input[7] & 1u) | (run == 7 ? 2u : 0u));
    LLVMFuzzerTestOneInput(input, size);
  }
  return 0;
}
#endif
