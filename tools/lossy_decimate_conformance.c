// Copyright 2026
// Standalone portable conformance runner for the lossy-decimate ABI.

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if !defined(_WIN32)
#include <unistd.h>
#else
#include <process.h>
#endif

#include "src/enc/fpga_enc.h"
#include "src/enc/lossy_decimate_fixture.h"
#if defined(WEBP_USE_CUDA)
#include "src/enc/cuda_enc.h"
#endif
#include "tools/benchmark_platform.h"

typedef enum {
  INJECT_NONE = 0,
  INJECT_DECLINE,
  INJECT_TIMEOUT,
  INJECT_ERROR
} Injection;

static const char* InjectionName(Injection injection) {
  switch (injection) {
    case INJECT_NONE:
      return "none";
    case INJECT_DECLINE:
      return "decline";
    case INJECT_TIMEOUT:
      return "timeout";
    case INJECT_ERROR:
      return "error";
  }
  return "invalid";
}

typedef struct {
  WebPAcceleratorDecimateResult* results;
  uint8_t* recon_y;
  uint8_t* recon_u;
  uint8_t* recon_v;
  size_t mb_count;
  size_t y_size;
  size_t uv_size;
} ActualOutput;

typedef struct {
  uint64_t fixture_count;
  uint64_t macroblock_count;
  uint64_t i4_count;
  uint64_t i16_count;
  uint64_t zero_nz_count;
  uint64_t nonzero_nz_count;
  uint64_t error_diffusion_count;
  uint64_t banded_count;
  uint64_t partial_edge_count;
  uint32_t segment_mask;
  uint32_t i4_mode_mask;
  uint32_t i16_mode_mask;
  uint32_t uv_mode_mask;
  uint32_t nz_union;
  int min_coefficient;
  int max_coefficient;
} Coverage;

static void PrintJSONString(const char* value) {
  const unsigned char* cursor = (const unsigned char*)value;
  putchar('"');
  while (*cursor != 0) {
    const unsigned char c = *cursor++;
    if (c == '"' || c == '\\') {
      putchar('\\');
      putchar(c);
    } else if (c == '\b') {
      fputs("\\b", stdout);
    } else if (c == '\f') {
      fputs("\\f", stdout);
    } else if (c == '\n') {
      fputs("\\n", stdout);
    } else if (c == '\r') {
      fputs("\\r", stdout);
    } else if (c == '\t') {
      fputs("\\t", stdout);
    } else if (c < 0x20) {
      printf("\\u%04x", (unsigned int)c);
    } else {
      putchar(c);
    }
  }
  putchar('"');
}

static void CoverCoefficient(Coverage* coverage, int value) {
  if (value < coverage->min_coefficient) coverage->min_coefficient = value;
  if (value > coverage->max_coefficient) coverage->max_coefficient = value;
}

static void CoverFixture(const WebPDecimateFixture* fixture,
                         Coverage* coverage) {
  const WebPAcceleratorDecimateRequest* const request = &fixture->request;
  const size_t mb_count = (size_t)request->mb_w * request->mb_h;
  size_t mb;
  ++coverage->fixture_count;
  coverage->macroblock_count += mb_count;
  coverage->error_diffusion_count += request->use_error_diffusion != 0;
  coverage->banded_count += request->band_count > 1;
  coverage->partial_edge_count +=
      (request->width & 15) != 0 || (request->height & 15) != 0;
  for (mb = 0; mb < mb_count; ++mb) {
    const WebPAcceleratorDecimateResult* const result =
        &fixture->golden_results[mb];
    int i, j;
    if (request->segments[mb] < 4) {
      coverage->segment_mask |= 1u << request->segments[mb];
    }
    if (result->is_i4) {
      ++coverage->i4_count;
      for (i = 0; i < 16; ++i) {
        if (result->modes_i4[i] < 10) {
          coverage->i4_mode_mask |= 1u << result->modes_i4[i];
        }
      }
    } else {
      ++coverage->i16_count;
      if (result->mode_i16 < 4) {
        coverage->i16_mode_mask |= 1u << result->mode_i16;
      }
    }
    if (result->mode_uv < 4) {
      coverage->uv_mode_mask |= 1u << result->mode_uv;
    }
    coverage->nz_union |= result->nz;
    if (result->nz == 0) ++coverage->zero_nz_count;
    else ++coverage->nonzero_nz_count;
    for (i = 0; i < 16; ++i) {
      CoverCoefficient(coverage, result->y_dc_levels[i]);
      for (j = 0; j < 16; ++j) {
        CoverCoefficient(coverage, result->y_ac_levels[i][j]);
      }
    }
    for (i = 0; i < 8; ++i) {
      for (j = 0; j < 16; ++j) {
        CoverCoefficient(coverage, result->uv_levels[i][j]);
      }
    }
  }
}

static int ReportCoverage(int path_count, char** paths) {
  Coverage coverage;
  int i;
  memset(&coverage, 0, sizeof(coverage));
  coverage.min_coefficient = 32767;
  coverage.max_coefficient = -32768;
  for (i = 0; i < path_count; ++i) {
    WebPDecimateFixture fixture;
    char error[256];
    memset(&fixture, 0, sizeof(fixture));
    if (!WebPDecimateFixtureLoad(paths[i], &fixture, error, sizeof(error))) {
      fprintf(stderr, "%s: %s\n", paths[i], error);
      return 0;
    }
    CoverFixture(&fixture, &coverage);
    WebPDecimateFixtureClear(&fixture);
  }
  printf("{\"schema\":\"webp-lossy-decimate-coverage\","
         "\"version\":1,\"fixtures\":%llu,\"macroblocks\":%llu,"
         "\"segments_mask\":\"0x%01x\",\"i4_modes_mask\":\"0x%03x\","
         "\"i16_modes_mask\":\"0x%01x\",\"uv_modes_mask\":\"0x%01x\","
         "\"i4_macroblocks\":%llu,\"i16_macroblocks\":%llu,"
         "\"zero_nz_macroblocks\":%llu,\"nonzero_nz_macroblocks\":%llu,"
         "\"nz_union\":\"0x%08x\",\"coefficient_min\":%d,"
         "\"coefficient_max\":%d,\"error_diffusion_fixtures\":%llu,"
         "\"banded_fixtures\":%llu,\"partial_edge_fixtures\":%llu}\n",
         (unsigned long long)coverage.fixture_count,
         (unsigned long long)coverage.macroblock_count, coverage.segment_mask,
         coverage.i4_mode_mask, coverage.i16_mode_mask,
         coverage.uv_mode_mask, (unsigned long long)coverage.i4_count,
         (unsigned long long)coverage.i16_count,
         (unsigned long long)coverage.zero_nz_count,
         (unsigned long long)coverage.nonzero_nz_count, coverage.nz_union,
         coverage.min_coefficient, coverage.max_coefficient,
         (unsigned long long)coverage.error_diffusion_count,
         (unsigned long long)coverage.banded_count,
         (unsigned long long)coverage.partial_edge_count);
  return 1;
}

static int AllocateOutput(const WebPDecimateFixture* fixture,
                          ActualOutput* output, uint8_t fill) {
  const WebPAcceleratorDecimateRequest* const request = &fixture->request;
  output->mb_count = (size_t)request->mb_w * request->mb_h;
  output->y_size = (size_t)request->recon_y_stride * request->mb_h * 16u;
  output->uv_size =
      (size_t)request->recon_uv_stride * request->mb_h * 8u;
  output->results = (WebPAcceleratorDecimateResult*)malloc(
      output->mb_count * sizeof(*output->results));
  output->recon_y = (uint8_t*)malloc(output->y_size);
  output->recon_u = (uint8_t*)malloc(output->uv_size);
  output->recon_v = (uint8_t*)malloc(output->uv_size);
  if (output->results == NULL || output->recon_y == NULL ||
      output->recon_u == NULL || output->recon_v == NULL) {
    return 0;
  }
  memset(output->results, fill,
         output->mb_count * sizeof(*output->results));
  memset(output->recon_y, fill, output->y_size);
  memset(output->recon_u, fill, output->uv_size);
  memset(output->recon_v, fill, output->uv_size);
  return 1;
}

static void ClearOutput(ActualOutput* output) {
  free(output->results);
  free(output->recon_y);
  free(output->recon_u);
  free(output->recon_v);
  memset(output, 0, sizeof(*output));
}

static void BindOutput(WebPAcceleratorDecimateRequest* request,
                       ActualOutput* output) {
  request->results = output->results;
  request->recon_y = output->recon_y;
  request->recon_u = output->recon_u;
  request->recon_v = output->recon_v;
}

static int OutputIsFill(const ActualOutput* output, uint8_t fill) {
  const uint8_t* blocks[4];
  size_t sizes[4];
  int b;
  blocks[0] = (const uint8_t*)output->results;
  blocks[1] = output->recon_y;
  blocks[2] = output->recon_u;
  blocks[3] = output->recon_v;
  sizes[0] = output->mb_count * sizeof(*output->results);
  sizes[1] = output->y_size;
  sizes[2] = output->uv_size;
  sizes[3] = output->uv_size;
  for (b = 0; b < 4; ++b) {
    size_t i;
    for (i = 0; i < sizes[b]; ++i) {
      if (blocks[b][i] != fill) return 0;
    }
  }
  return 1;
}

static int OutputMatches(const WebPDecimateFixture* fixture,
                         const ActualOutput* output) {
  const uint8_t* expected[4];
  const uint8_t* actual[4];
  const char* names[4] = {"results", "recon_y", "recon_u", "recon_v"};
  size_t sizes[4];
  int block;
  expected[0] = (const uint8_t*)fixture->golden_results;
  expected[1] = fixture->golden_recon_y;
  expected[2] = fixture->golden_recon_u;
  expected[3] = fixture->golden_recon_v;
  actual[0] = (const uint8_t*)output->results;
  actual[1] = output->recon_y;
  actual[2] = output->recon_u;
  actual[3] = output->recon_v;
  sizes[0] = output->mb_count * sizeof(*output->results);
  sizes[1] = output->y_size;
  sizes[2] = output->uv_size;
  sizes[3] = output->uv_size;
  for (block = 0; block < 4; ++block) {
    size_t i;
    for (i = 0; i < sizes[block]; ++i) {
      if (expected[block][i] != actual[block][i]) {
        fprintf(stderr, "%s mismatch at byte %zu: expected %u, got %u\n",
                names[block], i, expected[block][i], actual[block][i]);
        if (block == 0) {
          const size_t result_index = i / sizeof(*output->results);
          const WebPAcceleratorDecimateResult* const want =
              &fixture->golden_results[result_index];
          const WebPAcceleratorDecimateResult* const got =
              &output->results[result_index];
          fprintf(stderr,
                  "result %zu: is_i4 %u/%u, mode16 %u/%u, modeuv %u/%u, "
                  "store_delta %u/%u, nz %08x/%08x, D %u/%u, max %u/%u\n",
                  result_index, want->is_i4, got->is_i4, want->mode_i16,
                  got->mode_i16, want->mode_uv, got->mode_uv,
                  want->store_max_delta, got->store_max_delta, want->nz,
                  got->nz, want->distortion, got->distortion,
                  want->max_delta, got->max_delta);
        }
        return 0;
      }
    }
  }
  return 1;
}

static WebPAcceleratorResult RunLoopback(
    const WebPDecimateFixture* fixture, Injection injection,
    ActualOutput* output) {
  if (injection == INJECT_DECLINE) return WEBP_ACCELERATOR_NOT_RUN;
  if (injection == INJECT_TIMEOUT || injection == INJECT_ERROR) {
    return WEBP_ACCELERATOR_ERROR;
  }
  memcpy(output->results, fixture->golden_results,
         output->mb_count * sizeof(*output->results));
  memcpy(output->recon_y, fixture->golden_recon_y, output->y_size);
  memcpy(output->recon_u, fixture->golden_recon_u, output->uv_size);
  memcpy(output->recon_v, fixture->golden_recon_v, output->uv_size);
  return WEBP_ACCELERATOR_SUCCESS;
}

static WebPAcceleratorResult RunDescriptor(
    const WebPEncoderAccelerator* backend,
    const WebPDecimateFixture* fixture, int streaming, ActualOutput* output) {
  WebPAcceleratorDecimateRequest request = fixture->request;
  WebPAcceleratorResult result;
  if (backend == NULL || backend->lossy_decimate == NULL) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  BindOutput(&request, output);
  if (!streaming) {
    request.phase = WEBP_ACCELERATOR_DECIMATE_WHOLE;
    return backend->lossy_decimate(backend->context, &request);
  }
  request.phase = WEBP_ACCELERATOR_DECIMATE_BEGIN;
  request.band_index = 0;
  result = backend->lossy_decimate(backend->context, &request);
  if (result != WEBP_ACCELERATOR_SUCCESS) return result;
  for (request.band_index = 0; request.band_index < request.band_count;
       ++request.band_index) {
    request.phase = WEBP_ACCELERATOR_DECIMATE_COLLECT;
    result = backend->lossy_decimate(backend->context, &request);
    if (result != WEBP_ACCELERATOR_SUCCESS) return result;
  }
  return WEBP_ACCELERATOR_SUCCESS;
}

static int RunFixture(const char* path, const char* backend_name,
                      Injection injection, int streaming) {
  WebPDecimateFixture fixture;
  ActualOutput output;
  WebPAcceleratorResult result = WEBP_ACCELERATOR_ERROR;
  char error[256];
  uint64_t start, load_done, backend_done, compare_done;
  uint64_t accelerator_execution_ns = 0;
  uint64_t result_transfer_ns = 0;
  int matched = 0;
  const uint8_t fill = 0xa5;
  memset(&fixture, 0, sizeof(fixture));
  memset(&output, 0, sizeof(output));
  start = WebPBenchmarkNowNanoseconds();
  if (!WebPDecimateFixtureLoad(path, &fixture, error, sizeof(error))) {
    fprintf(stderr, "%s: %s\n", path, error);
    return 0;
  }
  load_done = WebPBenchmarkNowNanoseconds();
  if (!AllocateOutput(&fixture, &output, fill)) {
    fprintf(stderr, "%s: output allocation failed\n", path);
    WebPDecimateFixtureClear(&fixture);
    ClearOutput(&output);
    return 0;
  }
  if (!strcmp(backend_name, "loopback")) {
    result = RunLoopback(&fixture, injection, &output);
  } else if (!strcmp(backend_name, "fpga")) {
    result = RunDescriptor(WebPGetFPGAEncoderAccelerator(), &fixture,
                           streaming, &output);
#if defined(WEBP_USE_CUDA)
  } else if (!strcmp(backend_name, "cuda")) {
    if (!WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "1") ||
        !WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS",
                                     "0") ||
        !WebPBenchmarkSetEnvironment("WEBP_CUDA_DECIMATE_TIMING", "1")) {
      fprintf(stderr, "cannot configure CUDA conformance environment\n");
      (void)WebPBenchmarkUnsetEnvironment("WEBP_CUDA_LOSSY_DECIMATE");
      (void)WebPBenchmarkUnsetEnvironment(
          "WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS");
      (void)WebPBenchmarkUnsetEnvironment("WEBP_CUDA_DECIMATE_TIMING");
      WebPDecimateFixtureClear(&fixture);
      ClearOutput(&output);
      return 0;
    }
    result = RunDescriptor(WebPGetCUDAEncoderAccelerator(), &fixture,
                           streaming, &output);
#if defined(WEBP_CUDA_ENABLE_LOSSY_DECIMATE)
    if (result == WEBP_ACCELERATOR_SUCCESS) {
      accelerator_execution_ns =
          WebPCUDAGetLastDecimateExecutionNanoseconds();
      result_transfer_ns =
          WebPCUDAGetLastDecimateResultTransferNanoseconds();
    }
#endif
    (void)WebPBenchmarkUnsetEnvironment("WEBP_CUDA_LOSSY_DECIMATE");
    (void)WebPBenchmarkUnsetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS");
    (void)WebPBenchmarkUnsetEnvironment("WEBP_CUDA_DECIMATE_TIMING");
#endif
  } else {
    fprintf(stderr, "unknown or unavailable backend: %s\n", backend_name);
    WebPDecimateFixtureClear(&fixture);
    ClearOutput(&output);
    return 0;
  }
  backend_done = WebPBenchmarkNowNanoseconds();
  if (result == WEBP_ACCELERATOR_SUCCESS) {
    matched = OutputMatches(&fixture, &output);
  } else {
    matched = OutputIsFill(&output, fill);
  }
  compare_done = WebPBenchmarkNowNanoseconds();
  fputs("{\"fixture\":", stdout);
  PrintJSONString(path);
  fputs(",\"backend\":", stdout);
  PrintJSONString(backend_name);
  fputs(",\"injection\":", stdout);
  PrintJSONString(InjectionName(injection));
  printf(",\"schema\":%u,\"abi\":%u,\"streaming\":%s,"
         "\"result\":%d,\"exact\":%s,"
         "\"transport_deserialize_ns\":%llu,"
         "\"accelerator_callback_ns\":%llu,"
         "\"accelerator_execution_ns\":%llu,"
         "\"result_transfer_ns\":%llu,"
         "\"result_compare_ns\":%llu,\"cpu_replay_tokenization_ns\":0,"
         "\"total_ns\":%llu}\n",
         WEBP_DECIMATE_FIXTURE_SCHEMA_VERSION,
         WEBP_ENCODER_ACCELERATOR_ABI_VERSION,
         streaming ? "true" : "false", (int)result,
         matched ? "true" : "false",
         (unsigned long long)(load_done - start),
         (unsigned long long)(backend_done - load_done),
         (unsigned long long)accelerator_execution_ns,
         (unsigned long long)result_transfer_ns,
         (unsigned long long)(compare_done - backend_done),
         (unsigned long long)(compare_done - start));
  WebPDecimateFixtureClear(&fixture);
  ClearOutput(&output);
  if (!strcmp(backend_name, "fpga")) {
    return result == WEBP_ACCELERATOR_NOT_RUN && matched;
  }
  if (injection != INJECT_NONE) {
    return result != WEBP_ACCELERATOR_SUCCESS && matched;
  }
  return result == WEBP_ACCELERATOR_SUCCESS && matched;
}

static int BuildSelftestFixture(WebPDecimateFixture* fixture) {
  WebPAcceleratorDecimateRequest* const request = &fixture->request;
  const int width = 17, height = 13, mb_w = 2, mb_h = 1;
  const size_t mb_count = 2;
  size_t i;
  memset(fixture, 0, sizeof(*fixture));
  request->width = width;
  request->height = height;
  request->mb_w = mb_w;
  request->mb_h = mb_h;
  request->phase = WEBP_ACCELERATOR_DECIMATE_WHOLE;
  request->band_count = 1;
  request->y_stride = width;
  request->uv_stride = (width + 1) / 2;
  request->rd_opt_level = 1;
  request->max_i4_header_bits = 12345;
  request->use_error_diffusion = 1;
  request->recon_y_stride = mb_w * 16;
  request->recon_uv_stride = mb_w * 8;
  request->y = (uint8_t*)malloc((size_t)width * height);
  request->u = (uint8_t*)malloc((size_t)request->uv_stride * ((height + 1) / 2));
  request->v = (uint8_t*)malloc((size_t)request->uv_stride * ((height + 1) / 2));
  request->segments = (uint8_t*)malloc(mb_count);
  request->segment_params = (WebPAcceleratorDecimateSegment*)calloc(
      4, sizeof(WebPAcceleratorDecimateSegment));
  request->level_costs = (uint16_t*)malloc(4 * 8 * 3 * 68 * sizeof(uint16_t));
  request->coeff_probas = (uint8_t*)malloc(4 * 8 * 3 * 11);
  fixture->golden_results = (WebPAcceleratorDecimateResult*)calloc(
      mb_count, sizeof(*fixture->golden_results));
  fixture->golden_recon_y = (uint8_t*)malloc((size_t)mb_w * 16 * mb_h * 16);
  fixture->golden_recon_u = (uint8_t*)malloc((size_t)mb_w * 8 * mb_h * 8);
  fixture->golden_recon_v = (uint8_t*)malloc((size_t)mb_w * 8 * mb_h * 8);
  if (request->y == NULL || request->u == NULL || request->v == NULL ||
      request->segments == NULL || request->segment_params == NULL ||
      request->level_costs == NULL || request->coeff_probas == NULL ||
      fixture->golden_results == NULL || fixture->golden_recon_y == NULL ||
      fixture->golden_recon_u == NULL || fixture->golden_recon_v == NULL) {
    WebPDecimateFixtureClear(fixture);
    return 0;
  }
  for (i = 0; i < (size_t)width * height; ++i) {
    ((uint8_t*)request->y)[i] = (uint8_t)(i * 17u);
  }
  for (i = 0; i < (size_t)request->uv_stride * ((height + 1) / 2); ++i) {
    ((uint8_t*)request->u)[i] = (uint8_t)(i * 29u);
    ((uint8_t*)request->v)[i] = (uint8_t)(255u - i * 11u);
  }
  ((uint8_t*)request->segments)[0] = 0;
  ((uint8_t*)request->segments)[1] = 3;
  for (i = 0; i < 4 * 8 * 3 * 68; ++i) {
    ((uint16_t*)request->level_costs)[i] = (uint16_t)(i * 7u);
  }
  for (i = 0; i < 4 * 8 * 3 * 11; ++i) {
    ((uint8_t*)request->coeff_probas)[i] = (uint8_t)(i * 13u);
  }
  fixture->golden_results[0].is_i4 = 1;
  fixture->golden_results[0].nz = 0x123456u;
  fixture->golden_results[1].mode_i16 = 3;
  fixture->golden_results[1].y_ac_levels[15][15] = -2047;
  for (i = 0; i < (size_t)mb_w * 16 * mb_h * 16; ++i) {
    fixture->golden_recon_y[i] = (uint8_t)(i * 5u);
  }
  for (i = 0; i < (size_t)mb_w * 8 * mb_h * 8; ++i) {
    fixture->golden_recon_u[i] = (uint8_t)(i * 3u);
    fixture->golden_recon_v[i] = (uint8_t)(i * 19u);
  }
  return 1;
}

static int Selftest(void) {
  const WebPEncoderAccelerator* const fpga = WebPGetFPGAEncoderAccelerator();
  WebPDecimateFixture fixture;
  char path[512];
  char error[256];
  FILE* file;
  int byte;
#if defined(_WIN32)
  const int pid = _getpid();
  const char* const temporary_directory = getenv("TEMP");
#else
  const int pid = (int)getpid();
  const char* const temporary_directory = getenv("TMPDIR");
#endif
  snprintf(path, sizeof(path), "%s%clibwebp-decimate-conformance-%d.wpd",
           (temporary_directory != NULL && temporary_directory[0] != '\0')
               ? temporary_directory
#if defined(_WIN32)
               : ".",
#else
               : "/tmp",
#endif
#if defined(_WIN32)
           '\\',
#else
           '/',
#endif
           pid);
  if (fpga == NULL || fpga->abi_version != WEBP_ENCODER_ACCELERATOR_ABI_VERSION ||
      fpga->struct_size != sizeof(*fpga) || strcmp(fpga->name, "fpga") != 0 ||
      (fpga->stages & WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE) == 0 ||
      (fpga->properties & WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT) ==
          0 ||
      fpga->lossy_decimate == NULL) {
    fprintf(stderr, "invalid FPGA skeleton descriptor\n");
    return 0;
  }
  // Exercise the portable environment helpers in CPU-only builds too.
  if (!WebPBenchmarkSetEnvironment("WEBP_DECIMATE_SELFTEST", "1") ||
      !WebPBenchmarkUnsetEnvironment("WEBP_DECIMATE_SELFTEST")) {
    return 0;
  }
  if (!BuildSelftestFixture(&fixture)) return 0;
  if (!WebPDecimateFixtureWrite(path, &fixture, error, sizeof(error))) {
    fprintf(stderr, "selftest fixture write: %s\n", error);
    WebPDecimateFixtureClear(&fixture);
    return 0;
  }
  WebPDecimateFixtureClear(&fixture);
  if (!RunFixture(path, "loopback", INJECT_NONE, 0) ||
      !RunFixture(path, "loopback", INJECT_DECLINE, 0) ||
      !RunFixture(path, "loopback", INJECT_TIMEOUT, 0) ||
      !RunFixture(path, "loopback", INJECT_ERROR, 0) ||
      !RunFixture(path, "fpga", INJECT_NONE, 0)) {
    remove(path);
    return 0;
  }
  file = fopen(path, "r+b");
  if (file == NULL || fseek(file, 24, SEEK_SET) != 0 ||
      (byte = fgetc(file)) == EOF || fseek(file, 24, SEEK_SET) != 0 ||
      fputc(byte ^ 1, file) == EOF) {
    if (file != NULL) (void)fclose(file);
    remove(path);
    return 0;
  }
  if (fclose(file) != 0) {
    remove(path);
    return 0;
  }
  if (WebPDecimateFixtureLoad(path, &fixture, error, sizeof(error))) {
    WebPDecimateFixtureClear(&fixture);
    remove(path);
    fprintf(stderr, "corrupt fixture passed checksum validation\n");
    return 0;
  }
  remove(path);
  puts("PASS: lossy-decimate schema, transport, decline, timeout, error, "
       "transactionality, and FPGA skeleton");
  return 1;
}

static void Usage(const char* program) {
  fprintf(stderr,
          "Usage: %s --selftest\n"
          "       %s --coverage FIXTURE...\n"
          "       %s [--backend loopback|cuda|fpga] [--streaming] "
          "[--inject decline|timeout|error] FIXTURE...\n",
          program, program, program);
}

int main(int argc, char** argv) {
  const char* backend = "loopback";
  Injection injection = INJECT_NONE;
  int streaming = 0;
  int first_fixture = 1;
  int ok = 1;
  int i;
  if (argc == 2 && !strcmp(argv[1], "--selftest")) return Selftest() ? 0 : 1;
  if (argc >= 3 && !strcmp(argv[1], "--coverage")) {
    return ReportCoverage(argc - 2, argv + 2) ? 0 : 1;
  }
  for (i = 1; i < argc; ++i) {
    if (!strcmp(argv[i], "--backend") && i + 1 < argc) {
      backend = argv[++i];
    } else if (!strcmp(argv[i], "--streaming")) {
      streaming = 1;
    } else if (!strcmp(argv[i], "--inject") && i + 1 < argc) {
      const char* const value = argv[++i];
      if (!strcmp(value, "decline")) injection = INJECT_DECLINE;
      else if (!strcmp(value, "timeout")) injection = INJECT_TIMEOUT;
      else if (!strcmp(value, "error")) injection = INJECT_ERROR;
      else {
        Usage(argv[0]);
        return 2;
      }
    } else if (argv[i][0] == '-') {
      Usage(argv[0]);
      return 2;
    } else {
      first_fixture = 0;
      ok &= RunFixture(argv[i], backend, injection, streaming);
    }
  }
  if (first_fixture) {
    Usage(argv[0]);
    return 2;
  }
  return ok ? 0 : 1;
}
