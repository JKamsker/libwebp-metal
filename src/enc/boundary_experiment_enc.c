// Copyright 2026
//
// Measurement recorder shared by two independently compiled experiments.

#include "src/enc/boundary_experiment_enc.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#include <unistd.h>
#define WEBP_BOUNDARY_GETPID getpid
#elif defined(_WIN32)
#include <process.h>
#include <windows.h>
#define WEBP_BOUNDARY_GETPID _getpid
#else
#include <unistd.h>
#define WEBP_BOUNDARY_GETPID getpid
#endif

#if defined(_MSC_VER)
#define WEBP_BOUNDARY_TLS __declspec(thread)
#else
#define WEBP_BOUNDARY_TLS __thread
#endif

typedef struct {
  int active;
  int control;
  int inject_record_failure;
  int method;
  int width;
  int height;
  int encode_index;
  uint64_t total_start_ns;
  uint64_t elapsed_ns[WEBP_BACKREF_EXACT_STAGE_COUNT];
  uint32_t calls[WEBP_BACKREF_EXACT_STAGE_COUNT];
} WebPBoundaryContext;

static uint64_t BoundaryNowNs(void) {
#if defined(__APPLE__)
  static mach_timebase_info_data_t timebase;
  const uint64_t ticks = mach_continuous_time();
  if (timebase.denom == 0) mach_timebase_info(&timebase);
  return ticks * timebase.numer / timebase.denom;
#elif defined(_WIN32)
  LARGE_INTEGER counter, frequency;
  QueryPerformanceCounter(&counter);
  QueryPerformanceFrequency(&frequency);
  return (uint64_t)((counter.QuadPart * 1000000000ULL) / frequency.QuadPart);
#else
  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  return (uint64_t)now.tv_sec * 1000000000ULL + (uint64_t)now.tv_nsec;
#endif
}

static int ExactEnvironmentFlag(const char* name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

static void PrintJsonString(FILE* out, const char* value) {
  const unsigned char* p =
      (const unsigned char*)(value != NULL ? value : "");
  fputc('"', out);
  for (; *p != '\0'; ++p) {
    if (*p == '"' || *p == '\\') {
      fputc('\\', out);
      fputc(*p, out);
    } else if (*p == '\n') {
      fputs("\\n", out);
    } else if (*p >= 0x20) {
      fputc(*p, out);
    }
  }
  fputc('"', out);
}

static int BeginContext(WebPBoundaryContext* ctx, int* process_encode_index,
                        const char* runtime_flag, const char* control_flag,
                        const char* failure_flag, const char* label,
                        const WebPConfig* config,
                        const WebPPicture* picture) {
  const char* const opt_in = getenv(runtime_flag);
  memset(ctx, 0, sizeof(*ctx));
  if (opt_in == NULL) return 0;
  if (strcmp(opt_in, "1") != 0) {
    fprintf(stderr, "%s refuses invalid %s (expected exact value 1)\n", label,
            runtime_flag);
    return 0;
  }
  if (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
      strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0) {
    fprintf(stderr,
            "%s refuses timing without WEBP_BENCHMARK_SESSION=exclusive\n",
            label);
    return 0;
  }
  ctx->active = 1;
  ctx->control = ExactEnvironmentFlag(control_flag);
  ctx->inject_record_failure = ExactEnvironmentFlag(failure_flag);
  ctx->method = config != NULL ? config->method : -1;
  ctx->width = picture != NULL ? picture->width : 0;
  ctx->height = picture != NULL ? picture->height : 0;
  ctx->encode_index = (*process_encode_index)++;
  ctx->total_start_ns = BoundaryNowNs();
  return 1;
}

static uint64_t StageBegin(WebPBoundaryContext* ctx, int stage,
                           int stage_count) {
  if (!ctx->active || ctx->control || stage < 0 || stage >= stage_count) {
    return 0;
  }
  return BoundaryNowNs();
}

static void StageEnd(WebPBoundaryContext* ctx, int stage, int stage_count,
                     uint64_t start_ns) {
  if (!ctx->active || ctx->control || start_ns == 0 || stage < 0 ||
      stage >= stage_count) {
    return;
  }
  ctx->elapsed_ns[stage] += BoundaryNowNs() - start_ns;
  ++ctx->calls[stage];
}

static void EndContext(WebPBoundaryContext* ctx, const char* schema,
                       const char* output_flag, const char* const* stage_names,
                       int stage_count, int ok, int error_code) {
  const uint64_t total_ns =
      ctx->active ? BoundaryNowNs() - ctx->total_start_ns : 0;
  const char* const output_path = getenv(output_flag);
  const char* const lifecycle = getenv("WEBP_BOUNDARY_LIFECYCLE");
  const char* const run_id = getenv("WEBP_BOUNDARY_RUN_ID");
  const char* const case_id = getenv("WEBP_BOUNDARY_CASE_ID");
  const char* sample_role;
  FILE* out;
  int i;
  if (!ctx->active) return;
  ctx->active = 0;
  if (ctx->inject_record_failure) return;
  sample_role = lifecycle != NULL && strcmp(lifecycle, "warm") == 0
                    ? (ctx->encode_index == 0 ? "warmup" : "warm")
                    : "cold";
  out = output_path == NULL || output_path[0] == '\0'
            ? stderr
            : fopen(output_path, "a");
  if (out == NULL) return;
  fputs("{\"schema\":", out);
  PrintJsonString(out, schema);
  fputs(",\"run_id\":", out);
  PrintJsonString(out, run_id);
  fputs(",\"case_id\":", out);
  PrintJsonString(out, case_id);
  fprintf(out,
          ",\"pid\":%ld,\"encode_index\":%d,\"sample_role\":\"%s\","
          "\"variant\":\"%s\",\"method\":%d,\"width\":%d,\"height\":%d,"
          "\"pixels\":%llu,\"ok\":%s,\"error_code\":%d,\"total_ns\":%llu,"
          "\"stages\":{",
          (long)WEBP_BOUNDARY_GETPID(), ctx->encode_index, sample_role,
          ctx->control ? "control" : "record", ctx->method, ctx->width,
          ctx->height, (unsigned long long)ctx->width * (unsigned)ctx->height,
          ok ? "true" : "false", error_code, (unsigned long long)total_ns);
  for (i = 0; i < stage_count; ++i) {
    if (i != 0) fputc(',', out);
    PrintJsonString(out, stage_names[i]);
    fprintf(out, ":{\"elapsed_ns\":%llu,\"calls\":%u}",
            (unsigned long long)ctx->elapsed_ns[i], ctx->calls[i]);
  }
  fputs("}}\n", out);
  if (out != stderr) fclose(out);
}

#if defined(WEBP_USE_PREDICTOR_BOUNDARY_EXPERIMENT)
static WEBP_BOUNDARY_TLS WebPBoundaryContext predictor_context;
static WEBP_BOUNDARY_TLS int predictor_encode_index;
static const char* const kPredictorStageNames[] = {
    "selector_search", "residual_apply", "predictor_map_encode"};

void WebPPredictorBoundaryBegin(const WebPConfig* config,
                                const WebPPicture* picture) {
  BeginContext(&predictor_context, &predictor_encode_index,
               "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT",
               "WEBP_PREDICTOR_BOUNDARY_CONTROL",
               "WEBP_PREDICTOR_BOUNDARY_INJECT_RECORD_FAILURE",
               "predictor-boundary experiment", config, picture);
}

void WebPPredictorBoundaryEnd(int ok, int error_code) {
  EndContext(&predictor_context, "libwebp-predictor-boundary-v1",
             "WEBP_PREDICTOR_BOUNDARY_OUTPUT", kPredictorStageNames,
             WEBP_PREDICTOR_BOUNDARY_STAGE_COUNT, ok, error_code);
}

uint64_t WebPPredictorBoundaryStageBegin(WebPPredictorBoundaryStage stage) {
  return StageBegin(&predictor_context, stage,
                    WEBP_PREDICTOR_BOUNDARY_STAGE_COUNT);
}

void WebPPredictorBoundaryStageEnd(WebPPredictorBoundaryStage stage,
                                   uint64_t start_ns) {
  StageEnd(&predictor_context, stage, WEBP_PREDICTOR_BOUNDARY_STAGE_COUNT,
           start_ns);
}
#endif

#if defined(WEBP_USE_BACKREF_EXACT_EXPERIMENT)
static WEBP_BOUNDARY_TLS WebPBoundaryContext backref_context;
static WEBP_BOUNDARY_TLS int backref_encode_index;
static const char* const kBackrefStageNames[] = {
    "backref_total",       "standard_lz77", "rle", "box",
    "cache_search",        "cache_rewrite", "trace_back",
    "cost_evaluation"};

void WebPBackrefExactBegin(const WebPConfig* config,
                           const WebPPicture* picture) {
  BeginContext(&backref_context, &backref_encode_index,
               "WEBP_BACKREF_EXACT_EXPERIMENT", "WEBP_BACKREF_EXACT_CONTROL",
               "WEBP_BACKREF_EXACT_INJECT_RECORD_FAILURE",
               "backref-exact experiment", config, picture);
}

void WebPBackrefExactEnd(int ok, int error_code) {
  EndContext(&backref_context, "libwebp-backref-exact-v1",
             "WEBP_BACKREF_EXACT_OUTPUT", kBackrefStageNames,
             WEBP_BACKREF_EXACT_STAGE_COUNT, ok, error_code);
}

uint64_t WebPBackrefExactStageBegin(WebPBackrefExactStage stage) {
  return StageBegin(&backref_context, stage, WEBP_BACKREF_EXACT_STAGE_COUNT);
}

void WebPBackrefExactStageEnd(WebPBackrefExactStage stage,
                              uint64_t start_ns) {
  StageEnd(&backref_context, stage, WEBP_BACKREF_EXACT_STAGE_COUNT, start_ns);
}
#endif
