// Copyright 2026

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#include "src/enc/lossy_decimate_fixture.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
  kLevelCostCount = 4 * 8 * 3 * 68,
  kCoeffProbaCount = 4 * 8 * 3 * 11,
  kSegmentCount = 4,
  kSerializedSegmentSize = 708,
  kSerializedResultSize = 840
};

static const uint8_t kFixtureMagic[8] = {'W', 'P', 'D', 'C', 'R', 'D', '1', '\n'};

typedef struct {
  uint8_t* bytes;
  size_t size;
  size_t capacity;
  int ok;
} FixtureWriter;

typedef struct {
  const uint8_t* bytes;
  size_t size;
  size_t pos;
  int ok;
} FixtureReader;

static void SetError(char* error, size_t error_size, const char* message) {
  if (error != NULL && error_size != 0) {
    snprintf(error, error_size, "%s", message);
  }
}

static int CheckedMul(size_t a, size_t b, size_t* out) {
  if (a != 0 && b > SIZE_MAX / a) return 0;
  *out = a * b;
  return 1;
}

static int CheckedAdd(size_t a, size_t b, size_t* out) {
  if (a > SIZE_MAX - b) return 0;
  *out = a + b;
  return 1;
}

static uint64_t FixtureHash(const uint8_t* bytes, size_t size) {
  uint64_t hash = 1469598103934665603ull;
  size_t i;
  for (i = 0; i < size; ++i) {
    hash ^= bytes[i];
    hash *= 1099511628211ull;
  }
  return hash;
}

static void WriterReserve(FixtureWriter* writer, size_t extra) {
  size_t needed;
  size_t capacity;
  uint8_t* bytes;
  if (!writer->ok || !CheckedAdd(writer->size, extra, &needed)) {
    writer->ok = 0;
    return;
  }
  if (needed <= writer->capacity) return;
  capacity = writer->capacity ? writer->capacity : 4096u;
  while (capacity < needed) {
    if (capacity > SIZE_MAX / 2u) {
      capacity = needed;
      break;
    }
    capacity *= 2u;
  }
  bytes = (uint8_t*)realloc(writer->bytes, capacity);
  if (bytes == NULL) {
    writer->ok = 0;
    return;
  }
  writer->bytes = bytes;
  writer->capacity = capacity;
}

static void PutBytes(FixtureWriter* writer, const void* bytes, size_t size) {
  WriterReserve(writer, size);
  if (!writer->ok) return;
  memcpy(writer->bytes + writer->size, bytes, size);
  writer->size += size;
}

static void PutU8(FixtureWriter* writer, uint8_t value) {
  PutBytes(writer, &value, 1);
}

static void PutU16(FixtureWriter* writer, uint16_t value) {
  uint8_t bytes[2];
  bytes[0] = (uint8_t)value;
  bytes[1] = (uint8_t)(value >> 8);
  PutBytes(writer, bytes, sizeof(bytes));
}

static void PutU32(FixtureWriter* writer, uint32_t value) {
  uint8_t bytes[4];
  bytes[0] = (uint8_t)value;
  bytes[1] = (uint8_t)(value >> 8);
  bytes[2] = (uint8_t)(value >> 16);
  bytes[3] = (uint8_t)(value >> 24);
  PutBytes(writer, bytes, sizeof(bytes));
}

static void PutU64(FixtureWriter* writer, uint64_t value) {
  uint8_t bytes[8];
  int i;
  for (i = 0; i < 8; ++i) bytes[i] = (uint8_t)(value >> (8 * i));
  PutBytes(writer, bytes, sizeof(bytes));
}

static void PutS32(FixtureWriter* writer, int32_t value) {
  PutU32(writer, (uint32_t)value);
}

static uint8_t GetU8(FixtureReader* reader) {
  if (!reader->ok || reader->pos == reader->size) {
    reader->ok = 0;
    return 0;
  }
  return reader->bytes[reader->pos++];
}

static uint16_t GetU16(FixtureReader* reader) {
  uint16_t value = GetU8(reader);
  value |= (uint16_t)GetU8(reader) << 8;
  return value;
}

static int16_t GetS16(FixtureReader* reader) {
  const uint16_t value = GetU16(reader);
  return value <= INT16_MAX
             ? (int16_t)value
             : (int16_t)(-1 - (int32_t)(UINT16_MAX - value));
}

static int8_t GetS8(FixtureReader* reader) {
  const uint8_t value = GetU8(reader);
  return value <= INT8_MAX
             ? (int8_t)value
             : (int8_t)(-1 - (int16_t)(UINT8_MAX - value));
}

static uint32_t GetU32(FixtureReader* reader) {
  uint32_t value = GetU8(reader);
  value |= (uint32_t)GetU8(reader) << 8;
  value |= (uint32_t)GetU8(reader) << 16;
  value |= (uint32_t)GetU8(reader) << 24;
  return value;
}

static int32_t GetS32(FixtureReader* reader) {
  const uint32_t value = GetU32(reader);
  return value <= INT32_MAX
             ? (int32_t)value
             : (int32_t)(-1 - (int64_t)(UINT32_MAX - value));
}

static void GetBytes(FixtureReader* reader, void* bytes, size_t size) {
  if (!reader->ok || size > reader->size - reader->pos) {
    reader->ok = 0;
    return;
  }
  memcpy(bytes, reader->bytes + reader->pos, size);
  reader->pos += size;
}

static void PutMatrix(FixtureWriter* writer,
                      const WebPAcceleratorQuantMatrix* matrix) {
  int i;
  for (i = 0; i < 16; ++i) PutU16(writer, matrix->q[i]);
  for (i = 0; i < 16; ++i) PutU16(writer, matrix->iq[i]);
  for (i = 0; i < 16; ++i) PutU32(writer, matrix->bias[i]);
  for (i = 0; i < 16; ++i) PutU32(writer, matrix->zthresh[i]);
  for (i = 0; i < 16; ++i) PutU16(writer, matrix->sharpen[i]);
}

static void GetMatrix(FixtureReader* reader,
                      WebPAcceleratorQuantMatrix* matrix) {
  int i;
  for (i = 0; i < 16; ++i) matrix->q[i] = GetU16(reader);
  for (i = 0; i < 16; ++i) matrix->iq[i] = GetU16(reader);
  for (i = 0; i < 16; ++i) matrix->bias[i] = GetU32(reader);
  for (i = 0; i < 16; ++i) matrix->zthresh[i] = GetU32(reader);
  for (i = 0; i < 16; ++i) matrix->sharpen[i] = GetU16(reader);
}

static void PutSegment(FixtureWriter* writer,
                       const WebPAcceleratorDecimateSegment* segment) {
  PutMatrix(writer, &segment->y1);
  PutMatrix(writer, &segment->y2);
  PutMatrix(writer, &segment->uv);
  PutS32(writer, segment->lambda_i16);
  PutS32(writer, segment->lambda_i4);
  PutS32(writer, segment->lambda_uv);
  PutS32(writer, segment->lambda_mode);
  PutS32(writer, segment->lambda_trellis_i16);
  PutS32(writer, segment->lambda_trellis_i4);
  PutS32(writer, segment->lambda_trellis_uv);
  PutS32(writer, segment->tlambda);
  PutS32(writer, segment->min_disto);
}

static void GetSegment(FixtureReader* reader,
                       WebPAcceleratorDecimateSegment* segment) {
  GetMatrix(reader, &segment->y1);
  GetMatrix(reader, &segment->y2);
  GetMatrix(reader, &segment->uv);
  segment->lambda_i16 = GetS32(reader);
  segment->lambda_i4 = GetS32(reader);
  segment->lambda_uv = GetS32(reader);
  segment->lambda_mode = GetS32(reader);
  segment->lambda_trellis_i16 = GetS32(reader);
  segment->lambda_trellis_i4 = GetS32(reader);
  segment->lambda_trellis_uv = GetS32(reader);
  segment->tlambda = GetS32(reader);
  segment->min_disto = GetS32(reader);
}

static void PutResult(FixtureWriter* writer,
                      const WebPAcceleratorDecimateResult* result) {
  int i, j;
  for (i = 0; i < 16; ++i) PutU16(writer, (uint16_t)result->y_dc_levels[i]);
  for (i = 0; i < 16; ++i) {
    for (j = 0; j < 16; ++j) {
      PutU16(writer, (uint16_t)result->y_ac_levels[i][j]);
    }
  }
  for (i = 0; i < 8; ++i) {
    for (j = 0; j < 16; ++j) {
      PutU16(writer, (uint16_t)result->uv_levels[i][j]);
    }
  }
  PutU32(writer, result->nz);
  PutU32(writer, result->distortion);
  PutU32(writer, result->header_bits);
  PutU8(writer, result->is_i4);
  PutU8(writer, result->mode_i16);
  PutU8(writer, result->mode_uv);
  PutU8(writer, result->store_max_delta);
  for (i = 0; i < 16; ++i) PutU8(writer, result->modes_i4[i]);
  for (i = 0; i < 2; ++i) {
    for (j = 0; j < 3; ++j) PutU8(writer, (uint8_t)result->derr[i][j]);
  }
  PutU16(writer, result->max_delta);
}

static void GetResult(FixtureReader* reader,
                      WebPAcceleratorDecimateResult* result) {
  int i, j;
  memset(result, 0, sizeof(*result));
  for (i = 0; i < 16; ++i) result->y_dc_levels[i] = GetS16(reader);
  for (i = 0; i < 16; ++i) {
    for (j = 0; j < 16; ++j) {
      result->y_ac_levels[i][j] = GetS16(reader);
    }
  }
  for (i = 0; i < 8; ++i) {
    for (j = 0; j < 16; ++j) {
      result->uv_levels[i][j] = GetS16(reader);
    }
  }
  result->nz = GetU32(reader);
  result->distortion = GetU32(reader);
  result->header_bits = GetU32(reader);
  result->is_i4 = GetU8(reader);
  result->mode_i16 = GetU8(reader);
  result->mode_uv = GetU8(reader);
  result->store_max_delta = GetU8(reader);
  for (i = 0; i < 16; ++i) result->modes_i4[i] = GetU8(reader);
  for (i = 0; i < 2; ++i) {
    for (j = 0; j < 3; ++j) result->derr[i][j] = GetS8(reader);
  }
  result->max_delta = GetU16(reader);
}

static int ValidateResult(const WebPAcceleratorDecimateResult* result) {
  int i, j;
  if (result->is_i4 > 1 || result->mode_i16 >= 4 || result->mode_uv >= 4 ||
      result->store_max_delta > 1 || (result->nz & ~0x01ffffffu) != 0) {
    return 0;
  }
  if (result->is_i4) {
    for (i = 0; i < 16; ++i) {
      if (result->modes_i4[i] >= 10) return 0;
    }
  }
  for (i = 0; i < 16; ++i) {
    if (result->y_dc_levels[i] < -2047 ||
        result->y_dc_levels[i] > 2047) {
      return 0;
    }
    for (j = 0; j < 16; ++j) {
      if (result->y_ac_levels[i][j] < -2047 ||
          result->y_ac_levels[i][j] > 2047) {
        return 0;
      }
    }
  }
  for (i = 0; i < 8; ++i) {
    for (j = 0; j < 16; ++j) {
      if (result->uv_levels[i][j] < -2047 ||
          result->uv_levels[i][j] > 2047) {
        return 0;
      }
    }
  }
  return 1;
}

static int ValidateGeometry(const WebPAcceleratorDecimateRequest* request,
                            size_t* mb_count, size_t* y_size,
                            size_t* uv_size) {
  size_t y_stride, uv_stride, y_height, uv_height;
  if (request == NULL || request->width <= 0 || request->height <= 0 ||
      request->width > INT_MAX - 15 || request->height > INT_MAX - 15 ||
      (size_t)request->mb_w != ((size_t)request->width + 15u) / 16u ||
      (size_t)request->mb_h != ((size_t)request->height + 15u) / 16u ||
      request->mb_w <= 0 || request->mb_h <= 0 ||
      request->y_stride < request->width ||
      request->uv_stride < (request->width + 1) / 2 ||
      !CheckedMul((size_t)request->mb_w, request->mb_h, mb_count)) {
    return 0;
  }
  if (*mb_count > INT_MAX) return 0;
  y_stride = (size_t)request->mb_w * 16u;
  uv_stride = (size_t)request->mb_w * 8u;
  return CheckedMul((size_t)request->mb_h, 16u, &y_height) &&
         CheckedMul((size_t)request->mb_h, 8u, &uv_height) &&
         CheckedMul(y_stride, y_height, y_size) &&
         CheckedMul(uv_stride, uv_height, uv_size);
}

static int ExpectedPayloadSize(size_t visible_y, size_t visible_uv,
                               size_t mb_count, size_t y_size, size_t uv_size,
                               size_t* expected) {
  size_t result_bytes;
  *expected = 0;
#define ADD_PAYLOAD(value)                          \
  do {                                              \
    if (!CheckedAdd(*expected, (value), expected)) \
      return 0;                                     \
  } while (0)
  if (!CheckedMul(mb_count, kSerializedResultSize, &result_bytes)) return 0;
  ADD_PAYLOAD(visible_y);
  ADD_PAYLOAD(visible_uv);
  ADD_PAYLOAD(visible_uv);
  ADD_PAYLOAD(mb_count);
  ADD_PAYLOAD(kSegmentCount * kSerializedSegmentSize);
  ADD_PAYLOAD(kLevelCostCount * sizeof(uint16_t));
  ADD_PAYLOAD(kCoeffProbaCount);
  ADD_PAYLOAD(result_bytes);
  ADD_PAYLOAD(y_size);
  ADD_PAYLOAD(uv_size);
  ADD_PAYLOAD(uv_size);
#undef ADD_PAYLOAD
  return 1;
}

static int CopyFixtureInputs(const WebPAcceleratorDecimateRequest* request,
                             WebPDecimateFixture* fixture) {
  WebPAcceleratorDecimateRequest* dst = &fixture->request;
  size_t mb_count, y_size, uv_size, visible_y, visible_uv, bytes;
  uint8_t* y = NULL;
  uint8_t* u = NULL;
  uint8_t* v = NULL;
  uint8_t* segments = NULL;
  WebPAcceleratorDecimateSegment* segment_params = NULL;
  uint16_t* level_costs = NULL;
  uint8_t* coeff_probas = NULL;
  int row;
  if (request == NULL || request->y == NULL || request->u == NULL ||
      request->v == NULL || request->segments == NULL ||
      request->segment_params == NULL || request->level_costs == NULL ||
      request->coeff_probas == NULL ||
      !ValidateGeometry(request, &mb_count, &y_size, &uv_size) ||
      !CheckedMul((size_t)request->width, request->height, &visible_y) ||
      !CheckedMul((size_t)((request->width + 1) / 2),
                  (size_t)((request->height + 1) / 2), &visible_uv)) {
    return 0;
  }
  y = (uint8_t*)malloc(visible_y);
  u = (uint8_t*)malloc(visible_uv);
  v = (uint8_t*)malloc(visible_uv);
  segments = (uint8_t*)malloc(mb_count);
  segment_params = (WebPAcceleratorDecimateSegment*)malloc(
      kSegmentCount * sizeof(*segment_params));
  if (!CheckedMul(kLevelCostCount, sizeof(*level_costs), &bytes)) goto Error;
  level_costs = (uint16_t*)malloc(bytes);
  coeff_probas = (uint8_t*)malloc(kCoeffProbaCount);
  fixture->golden_results = (WebPAcceleratorDecimateResult*)calloc(
      mb_count, sizeof(*fixture->golden_results));
  fixture->golden_recon_y = (uint8_t*)calloc(1, y_size);
  fixture->golden_recon_u = (uint8_t*)calloc(1, uv_size);
  fixture->golden_recon_v = (uint8_t*)calloc(1, uv_size);
  if (y == NULL || u == NULL || v == NULL || segments == NULL ||
      segment_params == NULL || level_costs == NULL || coeff_probas == NULL ||
      fixture->golden_results == NULL || fixture->golden_recon_y == NULL ||
      fixture->golden_recon_u == NULL || fixture->golden_recon_v == NULL) {
    goto Error;
  }
  for (row = 0; row < request->height; ++row) {
    memcpy(y + (size_t)row * request->width,
           request->y + (size_t)row * request->y_stride, request->width);
  }
  for (row = 0; row < (request->height + 1) / 2; ++row) {
    const size_t width = (size_t)(request->width + 1) / 2u;
    memcpy(u + (size_t)row * width,
           request->u + (size_t)row * request->uv_stride, width);
    memcpy(v + (size_t)row * width,
           request->v + (size_t)row * request->uv_stride, width);
  }
  memcpy(segments, request->segments, mb_count);
  memcpy(segment_params, request->segment_params,
         kSegmentCount * sizeof(*segment_params));
  memcpy(level_costs, request->level_costs,
         kLevelCostCount * sizeof(*level_costs));
  memcpy(coeff_probas, request->coeff_probas, kCoeffProbaCount);
  *dst = *request;
  dst->phase = WEBP_ACCELERATOR_DECIMATE_WHOLE;
  dst->band_index = 0;
  dst->y = y;
  dst->u = u;
  dst->v = v;
  dst->y_stride = request->width;
  dst->uv_stride = (request->width + 1) / 2;
  dst->segments = segments;
  dst->segment_params = segment_params;
  dst->level_costs = level_costs;
  dst->coeff_probas = coeff_probas;
  dst->results = NULL;
  dst->recon_y = NULL;
  dst->recon_u = NULL;
  dst->recon_v = NULL;
  dst->recon_y_stride = request->mb_w * 16;
  dst->recon_uv_stride = request->mb_w * 8;
  return 1;

 Error:
  free(y);
  free(u);
  free(v);
  free(segments);
  free(segment_params);
  free(level_costs);
  free(coeff_probas);
  WebPDecimateFixtureClear(fixture);
  return 0;
}

void WebPDecimateFixtureClear(WebPDecimateFixture* fixture) {
  if (fixture == NULL) return;
  free((void*)fixture->request.y);
  free((void*)fixture->request.u);
  free((void*)fixture->request.v);
  free((void*)fixture->request.segments);
  free((void*)fixture->request.segment_params);
  free((void*)fixture->request.level_costs);
  free((void*)fixture->request.coeff_probas);
  free(fixture->golden_results);
  free(fixture->golden_recon_y);
  free(fixture->golden_recon_u);
  free(fixture->golden_recon_v);
  memset(fixture, 0, sizeof(*fixture));
}

static void PutPlane(FixtureWriter* writer, const uint8_t* plane, int width,
                     int height, int stride) {
  int row;
  for (row = 0; row < height; ++row) {
    PutBytes(writer, plane + (size_t)row * stride, (size_t)width);
  }
}

int WebPDecimateFixtureWrite(const char* path,
                             const WebPDecimateFixture* fixture,
                             char* error, size_t error_size) {
  FixtureWriter writer = {NULL, 0, 0, 1};
  const WebPAcceleratorDecimateRequest* request;
  size_t mb_count, y_size, uv_size;
  uint64_t hash;
  FILE* file = NULL;
  char* temporary = NULL;
  size_t path_size;
  int i;
  if (path == NULL || fixture == NULL) {
    SetError(error, error_size, "missing fixture path or data");
    return 0;
  }
  request = &fixture->request;
  if (request->y == NULL || request->u == NULL || request->v == NULL ||
      request->segments == NULL || request->segment_params == NULL ||
      request->level_costs == NULL || request->coeff_probas == NULL ||
      !ValidateGeometry(request, &mb_count, &y_size, &uv_size) ||
      (request->use_error_diffusion != 0 &&
       request->use_error_diffusion != 1) ||
      request->rd_opt_level < 1 || request->rd_opt_level > 3 ||
      request->band_count < 1 || request->band_count > 8 ||
      fixture->golden_results == NULL || fixture->golden_recon_y == NULL ||
      fixture->golden_recon_u == NULL || fixture->golden_recon_v == NULL) {
    SetError(error, error_size, "invalid fixture geometry or golden output");
    return 0;
  }
  for (i = 0; i < (int)mb_count; ++i) {
    if (request->segments[i] >= kSegmentCount ||
        !ValidateResult(&fixture->golden_results[i])) {
      SetError(error, error_size, "invalid fixture segment or result");
      return 0;
    }
  }
  PutBytes(&writer, kFixtureMagic, sizeof(kFixtureMagic));
  PutU32(&writer, WEBP_DECIMATE_FIXTURE_SCHEMA_VERSION);
  PutU32(&writer, WEBP_ENCODER_ACCELERATOR_ABI_VERSION);
  PutU32(&writer, request->use_error_diffusion ? 1u : 0u);
  PutU32(&writer, (uint32_t)request->width);
  PutU32(&writer, (uint32_t)request->height);
  PutU32(&writer, (uint32_t)request->mb_w);
  PutU32(&writer, (uint32_t)request->mb_h);
  PutS32(&writer, request->rd_opt_level);
  PutS32(&writer, request->max_i4_header_bits);
  PutU32(&writer, (uint32_t)(request->band_count > 0 ? request->band_count : 1));
  PutU32(&writer, 0);
  PutPlane(&writer, request->y, request->width, request->height,
           request->y_stride);
  PutPlane(&writer, request->u, (request->width + 1) / 2,
           (request->height + 1) / 2, request->uv_stride);
  PutPlane(&writer, request->v, (request->width + 1) / 2,
           (request->height + 1) / 2, request->uv_stride);
  PutBytes(&writer, request->segments, mb_count);
  for (i = 0; i < kSegmentCount; ++i) {
    PutSegment(&writer, &request->segment_params[i]);
  }
  for (i = 0; i < kLevelCostCount; ++i) PutU16(&writer, request->level_costs[i]);
  PutBytes(&writer, request->coeff_probas, kCoeffProbaCount);
  for (i = 0; i < (int)mb_count; ++i) {
    PutResult(&writer, &fixture->golden_results[i]);
  }
  PutBytes(&writer, fixture->golden_recon_y, y_size);
  PutBytes(&writer, fixture->golden_recon_u, uv_size);
  PutBytes(&writer, fixture->golden_recon_v, uv_size);
  if (!writer.ok) {
    free(writer.bytes);
    SetError(error, error_size, "fixture serialization allocation failed");
    return 0;
  }
  hash = FixtureHash(writer.bytes, writer.size);
  PutU64(&writer, hash);
  if (!writer.ok || !CheckedAdd(strlen(path), 5u, &path_size)) {
    free(writer.bytes);
    SetError(error, error_size, "fixture path is too long");
    return 0;
  }
  temporary = (char*)malloc(path_size);
  if (temporary == NULL) {
    free(writer.bytes);
    SetError(error, error_size, "temporary path allocation failed");
    return 0;
  }
  snprintf(temporary, path_size, "%s.tmp", path);
  file = fopen(temporary, "wb");
  if (file == NULL || fwrite(writer.bytes, 1, writer.size, file) != writer.size) {
    if (file != NULL) (void)fclose(file);
    remove(temporary);
    free(temporary);
    free(writer.bytes);
    SetError(error, error_size, "fixture write failed");
    return 0;
  }
  if (fclose(file) != 0) {
    remove(temporary);
    free(temporary);
    free(writer.bytes);
    SetError(error, error_size, "fixture write close failed");
    return 0;
  }
  file = NULL;
  if (rename(temporary, path) != 0) {
    remove(temporary);
    free(temporary);
    free(writer.bytes);
    SetError(error, error_size, "fixture commit rename failed");
    return 0;
  }
  free(temporary);
  free(writer.bytes);
  return 1;
}

static int LoadFile(const char* path, uint8_t** bytes, size_t* size) {
  FILE* file = fopen(path, "rb");
  long length;
  if (file == NULL || fseek(file, 0, SEEK_END) != 0 ||
      (length = ftell(file)) < 0 || fseek(file, 0, SEEK_SET) != 0) {
    if (file != NULL) fclose(file);
    return 0;
  }
  *bytes = (uint8_t*)malloc((size_t)length);
  if (*bytes == NULL ||
      fread(*bytes, 1, (size_t)length, file) != (size_t)length) {
    (void)fclose(file);
    free(*bytes);
    *bytes = NULL;
    return 0;
  }
  if (fclose(file) != 0) {
    free(*bytes);
    *bytes = NULL;
    return 0;
  }
  *size = (size_t)length;
  return 1;
}

int WebPDecimateFixtureLoad(const char* path, WebPDecimateFixture* fixture,
                            char* error, size_t error_size) {
  uint8_t* bytes = NULL;
  size_t size = 0, mb_count, y_size, uv_size, visible_y, visible_uv;
  size_t expected_payload;
  FixtureReader reader;
  WebPAcceleratorDecimateRequest metadata;
  uint32_t flags, width, height, mb_w, mb_h, band_count, reserved;
  uint64_t expected_hash, actual_hash;
  int i;
  if (fixture == NULL || path == NULL) {
    SetError(error, error_size, "missing fixture destination or path");
    return 0;
  }
  memset(fixture, 0, sizeof(*fixture));
  if (!LoadFile(path, &bytes, &size) || size < sizeof(kFixtureMagic) + 8u) {
    free(bytes);
    SetError(error, error_size, "cannot read fixture");
    return 0;
  }
  expected_hash = 0;
  for (i = 0; i < 8; ++i) expected_hash |= (uint64_t)bytes[size - 8u + i] << (8 * i);
  actual_hash = FixtureHash(bytes, size - 8u);
  if (expected_hash != actual_hash) {
    free(bytes);
    SetError(error, error_size, "fixture checksum mismatch");
    return 0;
  }
  reader.bytes = bytes;
  reader.size = size - 8u;
  reader.pos = 0;
  reader.ok = 1;
  {
    uint8_t magic[8];
    GetBytes(&reader, magic, sizeof(magic));
    if (!reader.ok || memcmp(magic, kFixtureMagic, sizeof(magic)) != 0 ||
        GetU32(&reader) != WEBP_DECIMATE_FIXTURE_SCHEMA_VERSION ||
        GetU32(&reader) != WEBP_ENCODER_ACCELERATOR_ABI_VERSION) {
      free(bytes);
      SetError(error, error_size, "unsupported fixture schema or ABI");
      return 0;
    }
  }
  memset(&metadata, 0, sizeof(metadata));
  flags = GetU32(&reader);
  metadata.use_error_diffusion = (flags & 1u) != 0;
  width = GetU32(&reader);
  height = GetU32(&reader);
  mb_w = GetU32(&reader);
  mb_h = GetU32(&reader);
  if (width > INT_MAX || height > INT_MAX || mb_w > INT_MAX ||
      mb_h > INT_MAX) {
    reader.ok = 0;
  }
  metadata.width = reader.ok ? (int)width : 0;
  metadata.height = reader.ok ? (int)height : 0;
  metadata.mb_w = reader.ok ? (int)mb_w : 0;
  metadata.mb_h = reader.ok ? (int)mb_h : 0;
  metadata.rd_opt_level = GetS32(&reader);
  metadata.max_i4_header_bits = GetS32(&reader);
  band_count = GetU32(&reader);
  if (band_count > INT_MAX) reader.ok = 0;
  metadata.band_count = reader.ok ? (int)band_count : 0;
  reserved = GetU32(&reader);
  if ((flags & ~1u) != 0 || reserved != 0) reader.ok = 0;
  metadata.y_stride = metadata.width;
  metadata.uv_stride = (metadata.width + 1) / 2;
  metadata.phase = WEBP_ACCELERATOR_DECIMATE_WHOLE;
  if (!ValidateGeometry(&metadata, &mb_count, &y_size, &uv_size) ||
      metadata.rd_opt_level < 1 || metadata.rd_opt_level > 3 ||
      metadata.band_count < 1 || metadata.band_count > 8 ||
      !CheckedMul((size_t)metadata.width, metadata.height, &visible_y) ||
      !CheckedMul((size_t)metadata.uv_stride,
                  ((size_t)metadata.height + 1u) / 2u, &visible_uv) ||
      !ExpectedPayloadSize(visible_y, visible_uv, mb_count, y_size, uv_size,
                           &expected_payload) ||
      expected_payload != reader.size - reader.pos) {
    free(bytes);
    SetError(error, error_size, "invalid fixture geometry");
    return 0;
  }
  fixture->request = metadata;
  fixture->request.y = (uint8_t*)malloc(visible_y);
  fixture->request.u = (uint8_t*)malloc(visible_uv);
  fixture->request.v = (uint8_t*)malloc(visible_uv);
  fixture->request.segments = (uint8_t*)malloc(mb_count);
  fixture->request.segment_params =
      (WebPAcceleratorDecimateSegment*)calloc(kSegmentCount,
                                               sizeof(WebPAcceleratorDecimateSegment));
  fixture->request.level_costs =
      (uint16_t*)malloc(kLevelCostCount * sizeof(uint16_t));
  fixture->request.coeff_probas = (uint8_t*)malloc(kCoeffProbaCount);
  fixture->golden_results = (WebPAcceleratorDecimateResult*)calloc(
      mb_count, sizeof(*fixture->golden_results));
  fixture->golden_recon_y = (uint8_t*)malloc(y_size);
  fixture->golden_recon_u = (uint8_t*)malloc(uv_size);
  fixture->golden_recon_v = (uint8_t*)malloc(uv_size);
  if (fixture->request.y == NULL || fixture->request.u == NULL ||
      fixture->request.v == NULL || fixture->request.segments == NULL ||
      fixture->request.segment_params == NULL ||
      fixture->request.level_costs == NULL ||
      fixture->request.coeff_probas == NULL ||
      fixture->golden_results == NULL || fixture->golden_recon_y == NULL ||
      fixture->golden_recon_u == NULL || fixture->golden_recon_v == NULL) {
    free(bytes);
    WebPDecimateFixtureClear(fixture);
    SetError(error, error_size, "fixture allocation failed");
    return 0;
  }
  GetBytes(&reader, (void*)fixture->request.y, visible_y);
  GetBytes(&reader, (void*)fixture->request.u, visible_uv);
  GetBytes(&reader, (void*)fixture->request.v, visible_uv);
  GetBytes(&reader, (void*)fixture->request.segments, mb_count);
  for (i = 0; i < (int)mb_count; ++i) {
    if (fixture->request.segments[i] >= kSegmentCount) reader.ok = 0;
  }
  for (i = 0; i < kSegmentCount; ++i) {
    GetSegment(&reader,
               &((WebPAcceleratorDecimateSegment*)fixture->request.segment_params)[i]);
  }
  for (i = 0; i < kLevelCostCount; ++i) {
    ((uint16_t*)fixture->request.level_costs)[i] = GetU16(&reader);
  }
  GetBytes(&reader, (void*)fixture->request.coeff_probas, kCoeffProbaCount);
  for (i = 0; i < (int)mb_count; ++i) {
    GetResult(&reader, &fixture->golden_results[i]);
    if (!ValidateResult(&fixture->golden_results[i])) reader.ok = 0;
  }
  GetBytes(&reader, fixture->golden_recon_y, y_size);
  GetBytes(&reader, fixture->golden_recon_u, uv_size);
  GetBytes(&reader, fixture->golden_recon_v, uv_size);
  free(bytes);
  if (!reader.ok || reader.pos != reader.size) {
    WebPDecimateFixtureClear(fixture);
    SetError(error, error_size, "truncated or trailing fixture payload");
    return 0;
  }
  fixture->request.recon_y_stride = fixture->request.mb_w * 16;
  fixture->request.recon_uv_stride = fixture->request.mb_w * 8;
  return 1;
}

#if defined(WEBP_DECIMATE_FIXTURE_CAPTURE)

#if defined(_MSC_VER)
#define WEBP_FIXTURE_TLS __declspec(thread)
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_FIXTURE_TLS __thread
#else
#define WEBP_FIXTURE_TLS _Thread_local
#endif

typedef struct {
  WebPDecimateFixture fixture;
  size_t expected;
  size_t recorded;
  unsigned int sequence;
  int active;
  int max_delta_seen;
  uint16_t max_delta;
} FixtureCapture;

static WEBP_FIXTURE_TLS FixtureCapture g_capture;

void WebPDecimateFixtureCaptureBegin(
    const WebPAcceleratorDecimateRequest* request) {
  const char* const path = getenv("WEBP_DECIMATE_FIXTURE_PATH");
  const unsigned int sequence = g_capture.sequence;
  if (g_capture.active) WebPDecimateFixtureClear(&g_capture.fixture);
  memset(&g_capture, 0, sizeof(g_capture));
  g_capture.sequence = sequence;
  if (path == NULL || path[0] == '\0') return;
  if (!CopyFixtureInputs(request, &g_capture.fixture)) return;
  g_capture.expected =
      (size_t)request->mb_w * (size_t)request->mb_h;
  g_capture.active = 1;
}

void WebPDecimateFixtureCaptureResetDecision(void) {
  g_capture.max_delta_seen = 0;
  g_capture.max_delta = 0;
}

void WebPDecimateFixtureCaptureNoteMaxDelta(int max_delta) {
  if (!g_capture.active) return;
  g_capture.max_delta_seen = 1;
  g_capture.max_delta = (uint16_t)max_delta;
}

int WebPDecimateFixtureCaptureTakeMaxDelta(uint16_t* max_delta) {
  const int seen = g_capture.max_delta_seen;
  if (seen && max_delta != NULL) *max_delta = g_capture.max_delta;
  g_capture.max_delta_seen = 0;
  g_capture.max_delta = 0;
  return seen;
}

void WebPDecimateFixtureCaptureRecord(
    int mb_index, const WebPAcceleratorDecimateResult* result,
    const uint8_t* recon_y, const uint8_t* recon_u, const uint8_t* recon_v,
    int recon_stride) {
  const int mb_w = g_capture.fixture.request.mb_w;
  const int x = mb_index % mb_w;
  const int y = mb_index / mb_w;
  int row;
  if (!g_capture.active || result == NULL || mb_index < 0 ||
      (size_t)mb_index >= g_capture.expected || recon_y == NULL ||
      recon_u == NULL || recon_v == NULL || recon_stride < 32) {
    return;
  }
  g_capture.fixture.golden_results[mb_index] = *result;
  for (row = 0; row < 16; ++row) {
    memcpy(g_capture.fixture.golden_recon_y +
               (size_t)(y * 16 + row) * mb_w * 16 + x * 16,
           recon_y + (size_t)row * recon_stride, 16);
  }
  for (row = 0; row < 8; ++row) {
    memcpy(g_capture.fixture.golden_recon_u +
               (size_t)(y * 8 + row) * mb_w * 8 + x * 8,
           recon_u + (size_t)row * recon_stride, 8);
    memcpy(g_capture.fixture.golden_recon_v +
               (size_t)(y * 8 + row) * mb_w * 8 + x * 8,
           recon_v + (size_t)row * recon_stride, 8);
  }
  ++g_capture.recorded;
}

void WebPDecimateFixtureCaptureFinish(int success) {
  const char* const base = getenv("WEBP_DECIMATE_FIXTURE_PATH");
  char path[4096];
  char error[256];
  if (!g_capture.active) return;
  if (success && base != NULL && g_capture.recorded == g_capture.expected) {
    int path_length;
    if (g_capture.sequence == 0) {
      path_length = snprintf(path, sizeof(path), "%s", base);
    } else {
      path_length = snprintf(path, sizeof(path), "%s.%u", base,
                             g_capture.sequence);
    }
    if (path_length < 0 || (size_t)path_length >= sizeof(path)) {
      fprintf(stderr, "WebP decimate fixture: output path is too long\n");
    } else if (!WebPDecimateFixtureWrite(path, &g_capture.fixture, error,
                                         sizeof(error))) {
      fprintf(stderr, "WebP decimate fixture: %s\n", error);
    }
    ++g_capture.sequence;
  }
  {
    const unsigned int sequence = g_capture.sequence;
    WebPDecimateFixtureClear(&g_capture.fixture);
    memset(&g_capture, 0, sizeof(g_capture));
    g_capture.sequence = sequence;
  }
}

#endif  // WEBP_DECIMATE_FIXTURE_CAPTURE
