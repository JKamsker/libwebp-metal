// Copyright 2026
//
// Portable malformed/container/fallback policy coverage for CUDA transcoders.

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "tools/cuda_transcode_common.h"

static void PutLE32(uint8_t* p, uint32_t value) {
  p[0] = (uint8_t)value;
  p[1] = (uint8_t)(value >> 8);
  p[2] = (uint8_t)(value >> 16);
  p[3] = (uint8_t)(value >> 24);
}

static size_t AddChunk(uint8_t* data, size_t offset, const char fourcc[4],
                       const uint8_t* payload, size_t size) {
  memcpy(data + offset, fourcc, 4);
  PutLE32(data + offset + 4, (uint32_t)size);
  memcpy(data + offset + 8, payload, size);
  if (size & 1u) data[offset + 8 + size] = 0;
  return offset + 8 + size + (size & 1u);
}

static size_t FinishRiff(uint8_t* data, size_t size) {
  memcpy(data, "RIFF", 4);
  PutLE32(data + 4, (uint32_t)size - 8u);
  memcpy(data + 8, "WEBP", 4);
  return size;
}

static int Expect(const uint8_t* data, size_t size,
                  WebPTranscodeInputStatus status, int parse_ok) {
  WebPTranscodeInput input;
  const int ok = WebPTranscodeParseInput(data, size, &input);
  if (ok != parse_ok || (ok && input.status != status)) {
    fprintf(stderr, "policy mismatch: parse=%d status=%s\n", ok,
            ok ? input.reason : "parse-error");
    return 0;
  }
  return 1;
}

int main(void) {
  uint8_t data[256] = {0};
  const uint8_t vp8[] = {0x10, 0, 0, 0x9d, 0x01, 0x2a,
                         0x21, 0, 0x1f, 0};  // 33x31 key frame.
  const uint8_t metadata[] = {1, 2, 3};
  const uint8_t alpha[] = {0};
  const uint8_t vp8l[] = {0x2f, 0, 0, 0, 0};
  const uint8_t anim[] = {0, 0, 0, 0, 0, 0};
  uint8_t vp8x[10] = {0};
  size_t size = AddChunk(data, 12, "VP8 ", vp8, sizeof(vp8));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE, 1) ||
      !Expect(data, size - 1, WEBP_TRANSCODE_INPUT_MALFORMED, 0)) {
    return 1;
  }

  memset(data, 0, sizeof(data));
  size = AddChunk(data, 12, "ICCP", metadata, sizeof(metadata));
  size = AddChunk(data, size, "EXIF", metadata, sizeof(metadata));
  size = AddChunk(data, size, "XMP ", metadata, sizeof(metadata));
  size = AddChunk(data, size, "VP8 ", vp8, sizeof(vp8));
  size = FinishRiff(data, size);
  {
    WebPTranscodeInput input;
    if (!WebPTranscodeParseInput(data, size, &input) ||
        input.status != WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE ||
        input.width != 33 || input.height != 31 || input.iccp.size != 3u ||
        input.exif.size != 3u || input.xmp.size != 3u) {
      return 1;
    }
  }

  memset(data, 0, sizeof(data));
  size = AddChunk(data, 12, "ALPH", alpha, sizeof(alpha));
  size = AddChunk(data, size, "VP8 ", vp8, sizeof(vp8));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_ALPHA, 1)) return 1;

  memset(data, 0, sizeof(data));
  size = AddChunk(data, 12, "VP8L", vp8l, sizeof(vp8l));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_LOSSLESS, 1)) return 1;

  memset(data, 0, sizeof(data));
  size = AddChunk(data, 12, "ANIM", anim, sizeof(anim));
  size = AddChunk(data, size, "ANMF", anim, sizeof(anim));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_ANIMATION, 1)) return 1;

  memset(data, 0, sizeof(data));
  size = AddChunk(data, 12, "VP8 ", vp8, sizeof(vp8));
  size = AddChunk(data, size, "VP8 ", vp8, sizeof(vp8));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_MULTIPLE_IMAGES, 1)) return 1;

  memset(data, 0, sizeof(data));
  vp8x[0] = 0x80;  // Reserved VP8X flag.
  size = AddChunk(data, 12, "VP8X", vp8x, sizeof(vp8x));
  size = AddChunk(data, size, "VP8 ", vp8, sizeof(vp8));
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_MALFORMED, 0)) return 1;

  memset(data, 0, sizeof(data));
  {
    uint8_t invalid_vp8[sizeof(vp8)];
    memcpy(invalid_vp8, vp8, sizeof(vp8));
    invalid_vp8[2] = 0xff;  // First-partition length exceeds the payload.
    size = AddChunk(data, 12, "VP8 ", invalid_vp8, sizeof(invalid_vp8));
  }
  size = FinishRiff(data, size);
  if (!Expect(data, size, WEBP_TRANSCODE_INPUT_MALFORMED, 0)) return 1;

  puts("PASS: CUDA transcoder RIFF policy, metadata, odd dimensions, and "
       "transactional decline reasons");
  return 0;
}
