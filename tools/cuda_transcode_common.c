// Copyright 2026
//
// Strict simple-image WebP container policy for private CUDA transcoders.

#include "tools/cuda_transcode_common.h"

#include <limits.h>
#include <string.h>

static uint32_t ReadLE32(const uint8_t* p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) |
         ((uint32_t)p[3] << 24);
}

static int FourCCEquals(const uint8_t* p, const char fourcc[4]) {
  return !memcmp(p, fourcc, 4);
}

static int ParseVP8Header(const uint8_t* data, size_t size, int* width,
                          int* height) {
  uint32_t frame_tag;
  uint16_t raw_width, raw_height;
  if (size < 10u) return 0;
  frame_tag = (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
              ((uint32_t)data[2] << 16);
  if ((frame_tag & 1u) != 0u || (frame_tag & 0x10u) == 0u ||
      ((frame_tag >> 1) & 7u) > 3u ||
      (uint64_t)(frame_tag >> 5) + 10u > (uint64_t)size ||
      data[3] != 0x9d || data[4] != 0x01 || data[5] != 0x2a) {
    return 0;
  }
  raw_width = (uint16_t)((uint16_t)data[6] | ((uint16_t)data[7] << 8));
  raw_height = (uint16_t)((uint16_t)data[8] | ((uint16_t)data[9] << 8));
  if ((raw_width & 0xc000u) != 0u || (raw_height & 0xc000u) != 0u) return 0;
  *width = raw_width;
  *height = raw_height;
  return *width > 0 && *height > 0;
}

const char* WebPTranscodeInputStatusName(WebPTranscodeInputStatus status) {
  switch (status) {
    case WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE:
      return "eligible";
    case WEBP_TRANSCODE_INPUT_MALFORMED:
      return "malformed-or-truncated-riff";
    case WEBP_TRANSCODE_INPUT_LOSSLESS:
      return "lossless-vp8l";
    case WEBP_TRANSCODE_INPUT_ALPHA:
      return "alpha";
    case WEBP_TRANSCODE_INPUT_ANIMATION:
      return "animation";
    case WEBP_TRANSCODE_INPUT_MULTIPLE_IMAGES:
      return "multiple-image-chunks";
  }
  return "unknown";
}

static void SetStatus(WebPTranscodeInput* input,
                      WebPTranscodeInputStatus status) {
  input->status = status;
  input->reason = WebPTranscodeInputStatusName(status);
}

int WebPTranscodeParseInput(const uint8_t* data, size_t size,
                            WebPTranscodeInput* input) {
  size_t offset;
  uint32_t riff_size;
  int image_chunks = 0;
  int vp8x_width = 0, vp8x_height = 0;
  int vp8x_alpha = 0, vp8x_animation = 0;
  int saw_vp8x = 0;
  int saw_alpha = 0, saw_animation = 0, saw_lossless = 0;
  if (input == NULL) return 0;
  memset(input, 0, sizeof(*input));
  SetStatus(input, WEBP_TRANSCODE_INPUT_MALFORMED);
  if (data == NULL || size < 12u || !FourCCEquals(data, "RIFF") ||
      !FourCCEquals(data + 8, "WEBP")) {
    return 0;
  }
  riff_size = ReadLE32(data + 4);
  if (riff_size < 4u || (uint64_t)riff_size + 8u != (uint64_t)size) return 0;
  offset = 12u;
  while (offset < size) {
    uint32_t chunk_size;
    size_t payload, next;
    if (size - offset < 8u) return 0;
    chunk_size = ReadLE32(data + offset + 4u);
    payload = offset + 8u;
    if ((uint64_t)payload + chunk_size > (uint64_t)size) return 0;
    next = payload + (size_t)chunk_size + (chunk_size & 1u);
    if (next > size) return 0;
    if (FourCCEquals(data + offset, "VP8X")) {
      uint32_t w_minus_one, h_minus_one;
      if (chunk_size != 10u || saw_vp8x || (data[payload] & 0xc1u) != 0u ||
          data[payload + 1u] != 0 || data[payload + 2u] != 0 ||
          data[payload + 3u] != 0) {
        return 0;
      }
      saw_vp8x = 1;
      vp8x_alpha |= (data[payload] & 0x10u) != 0;
      vp8x_animation |= (data[payload] & 0x02u) != 0;
      w_minus_one = (uint32_t)data[payload + 4u] |
                    ((uint32_t)data[payload + 5u] << 8) |
                    ((uint32_t)data[payload + 6u] << 16);
      h_minus_one = (uint32_t)data[payload + 7u] |
                    ((uint32_t)data[payload + 8u] << 8) |
                    ((uint32_t)data[payload + 9u] << 16);
      if (w_minus_one >= INT_MAX || h_minus_one >= INT_MAX) return 0;
      vp8x_width = (int)w_minus_one + 1;
      vp8x_height = (int)h_minus_one + 1;
    } else if (FourCCEquals(data + offset, "VP8 ")) {
      ++image_chunks;
      input->vp8.bytes = data + payload;
      input->vp8.size = chunk_size;
    } else if (FourCCEquals(data + offset, "VP8L")) {
      ++image_chunks;
      saw_lossless = 1;
    } else if (FourCCEquals(data + offset, "ALPH")) {
      saw_alpha = 1;
    } else if (FourCCEquals(data + offset, "ANIM") ||
               FourCCEquals(data + offset, "ANMF")) {
      saw_animation = 1;
    } else if (FourCCEquals(data + offset, "ICCP")) {
      input->iccp.bytes = data + payload;
      input->iccp.size = chunk_size;
    } else if (FourCCEquals(data + offset, "EXIF")) {
      input->exif.bytes = data + payload;
      input->exif.size = chunk_size;
    } else if (FourCCEquals(data + offset, "XMP ")) {
      input->xmp.bytes = data + payload;
      input->xmp.size = chunk_size;
    }
    offset = next;
  }
  if (offset != size) return 0;
  if (saw_animation || vp8x_animation) {
    SetStatus(input, WEBP_TRANSCODE_INPUT_ANIMATION);
    return 1;
  }
  if (image_chunks == 0) return 0;
  if (saw_alpha || vp8x_alpha) {
    SetStatus(input, WEBP_TRANSCODE_INPUT_ALPHA);
    return 1;
  }
  if (saw_lossless) {
    SetStatus(input, WEBP_TRANSCODE_INPUT_LOSSLESS);
    return 1;
  }
  if (image_chunks != 1 || input->vp8.bytes == NULL) {
    SetStatus(input, WEBP_TRANSCODE_INPUT_MULTIPLE_IMAGES);
    return 1;
  }
  if (!ParseVP8Header(input->vp8.bytes, input->vp8.size, &input->width,
                      &input->height)) {
    return 0;
  }
  if ((vp8x_width != 0 && vp8x_width != input->width) ||
      (vp8x_height != 0 && vp8x_height != input->height)) {
    return 0;
  }
  SetStatus(input, WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE);
  return 1;
}
