// Copyright 2026
//
// Internal, independently guarded encoder stage profiling experiment.

#if !defined(WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT)
#define WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT 1
#endif
#include "src/enc/profile_enc.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(_WIN32)
#include <process.h>
#include <windows.h>
#define WEBP_PROFILE_GETPID _getpid
#elif defined(__APPLE__)
#include <mach/mach_time.h>
#include <unistd.h>
#define WEBP_PROFILE_GETPID getpid
#else
#include <unistd.h>
#define WEBP_PROFILE_GETPID getpid
#endif

#if defined(_MSC_VER)
#define WEBP_PROFILE_TLS __declspec(thread)
#else
#define WEBP_PROFILE_TLS __thread
#endif

typedef struct {
  int active;
  int method;
  float quality;
  int lossless;
  int exact;
  int thread_level;
  int width;
  int height;
  int encode_index;
  int metal_cross_color;
  int metal_hash;
  size_t output_size;
  uint64_t total_start_ns;
  uint64_t elapsed_ns[WEBP_PROFILE_STAGE_COUNT];
  uint32_t calls[WEBP_PROFILE_STAGE_COUNT];
} WebPProfileContext;

static WEBP_PROFILE_TLS WebPProfileContext profile_context;
static WEBP_PROFILE_TLS int process_encode_index;

static const char* const kStageNames[WEBP_PROFILE_STAGE_COUNT] = {
    "lossless_prepare",
    "lossless_container_setup",
    "lossless_analyze",
    "lossless_encoder_init",
    "lossless_palette",
    "lossless_input_copy",
    "lossless_subtract_green",
    "lossless_predictor",
    "lossless_cross_color",
    "lossless_hash_chain",
    "lossless_backward_refs",
    "lossless_histogram",
    "lossless_huffman",
    "lossless_bitstream",
    "lossless_stream_finalize",
    "lossless_riff_write",
    "metal_init",
    "metal_cross_color_dispatch",
    "metal_hash_pipeline_init",
    "metal_hash_dispatch",
    "lossy_import",
    "lossy_encoder_init",
    "lossy_analyze",
    "lossy_stat_loop",
    "lossy_encode_loop",
    "lossy_decimate",
    "lossy_record_tokens",
    "lossy_alpha",
    "lossy_write"};

static int EnvironmentOptIn(const char* name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

static uint64_t ProfileNowNs(void) {
#if defined(_WIN32)
  LARGE_INTEGER counter, frequency;
  QueryPerformanceCounter(&counter);
  QueryPerformanceFrequency(&frequency);
  return (uint64_t)((counter.QuadPart * 1000000000ULL) / frequency.QuadPart);
#elif defined(__APPLE__)
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

static void PrintJsonString(FILE* out, const char* value) {
  const unsigned char* p = (const unsigned char*)(value != NULL ? value : "");
  fputc('"', out);
  for (; *p != '\0'; ++p) {
    if (*p == '"' || *p == '\\') {
      fputc('\\', out);
      fputc(*p, out);
    } else if (*p == '\n') {
      fputs("\\n", out);
    } else if (*p == '\r') {
      fputs("\\r", out);
    } else if (*p == '\t') {
      fputs("\\t", out);
    } else if (*p < 0x20) {
      fprintf(out, "\\u%04x", *p);
    } else {
      fputc(*p, out);
    }
  }
  fputc('"', out);
}

void WebPProfileBeginSession(const WebPConfig* config,
                             const WebPPicture* picture) {
  WebPProfileContext* const ctx = &profile_context;
  memset(ctx, 0, sizeof(*ctx));
  if (!EnvironmentOptIn("WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT")) return;
  if (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
      strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0) {
    fprintf(stderr,
            "encoder stage profiling requires "
            "WEBP_BENCHMARK_SESSION=exclusive\n");
    return;
  }
  ctx->active = 1;
  ctx->method = config != NULL ? config->method : -1;
  ctx->quality = config != NULL ? config->quality : -1.f;
  ctx->lossless = config != NULL ? config->lossless : -1;
  ctx->exact = config != NULL ? config->exact : -1;
  ctx->thread_level = config != NULL ? config->thread_level : -1;
  ctx->width = picture != NULL ? picture->width : 0;
  ctx->height = picture != NULL ? picture->height : 0;
  ctx->encode_index = process_encode_index++;
  ctx->total_start_ns = ProfileNowNs();
}

void WebPProfileEndSession(int ok, int error_code) {
  WebPProfileContext* const ctx = &profile_context;
  const char* const output_path = getenv("WEBP_STAGE_PROFILE_OUTPUT");
  const char* const run_id = getenv("WEBP_STAGE_PROFILE_RUN_ID");
  const char* const case_id = getenv("WEBP_STAGE_PROFILE_CASE_ID");
  const char* const backend = getenv("WEBP_STAGE_PROFILE_BACKEND");
  const char* const sample_set = getenv("WEBP_STAGE_PROFILE_SAMPLE_SET");
  const uint64_t total_ns = ctx->active ? ProfileNowNs() - ctx->total_start_ns : 0;
  const char* sample_role;
  FILE* out;
  int i;
  if (!ctx->active) return;
  ctx->active = 0;
  if (sample_set != NULL && strcmp(sample_set, "warm") == 0) {
    sample_role = (ctx->encode_index == 0) ? "warmup" : "warm";
  } else {
    sample_role = "cold";
  }
  out = (output_path == NULL || output_path[0] == '\0')
            ? stderr
            : fopen(output_path, "a");
  if (out == NULL) return;
  fputs("{\"schema\":\"libwebp-encoder-stage-v1\",\"record_type\":\"encode\",", out);
  fputs("\"run_id\":", out);
  PrintJsonString(out, run_id);
  fputs(",\"case_id\":", out);
  PrintJsonString(out, case_id);
  fputs(",\"backend\":", out);
  PrintJsonString(out, backend);
  fprintf(out,
          ",\"pid\":%ld,\"encode_index\":%d,\"sample_role\":\"%s\","
          "\"method\":%d,\"quality\":%.3f,\"lossless\":%s,"
          "\"exact\":%s,\"thread_level\":%d,\"width\":%d,\"height\":%d,"
          "\"pixels\":%llu,\"ok\":%s,\"error_code\":%d,"
          "\"output_bytes\":%llu,\"metal_cross_color\":%s,"
          "\"metal_hash\":%s,\"total_ns\":%llu,\"stages\":{",
          (long)WEBP_PROFILE_GETPID(), ctx->encode_index, sample_role,
          ctx->method, ctx->quality, ctx->lossless ? "true" : "false",
          ctx->exact ? "true" : "false", ctx->thread_level, ctx->width,
          ctx->height, (unsigned long long)ctx->width * ctx->height,
          ok ? "true" : "false", error_code,
          (unsigned long long)ctx->output_size,
          ctx->metal_cross_color ? "true" : "false",
          ctx->metal_hash ? "true" : "false",
          (unsigned long long)total_ns);
  {
    int first = 1;
    for (i = 0; i < WEBP_PROFILE_STAGE_COUNT; ++i) {
      if (ctx->calls[i] == 0) continue;
      fprintf(out, "%s\"%s\":{\"ns\":%llu,\"calls\":%u}",
              first ? "" : ",", kStageNames[i],
              (unsigned long long)ctx->elapsed_ns[i], ctx->calls[i]);
      first = 0;
    }
  }
  fputs("}}\n", out);
  if (out != stderr) fclose(out);
}

uint64_t WebPProfileStageBegin(WebPProfileStage stage) {
  (void)stage;
  return profile_context.active ? ProfileNowNs() : 0;
}

void WebPProfileStageEnd(WebPProfileStage stage, uint64_t start_ns) {
  WebPProfileContext* const ctx = &profile_context;
  if (!ctx->active || start_ns == 0 || stage < 0 ||
      stage >= WEBP_PROFILE_STAGE_COUNT) {
    return;
  }
  ctx->elapsed_ns[stage] += ProfileNowNs() - start_ns;
  ++ctx->calls[stage];
}

void WebPProfileSetOutputSize(size_t output_size) {
  if (profile_context.active) profile_context.output_size = output_size;
}

void WebPProfileMarkMetalCrossColor(void) {
  if (profile_context.active) profile_context.metal_cross_color = 1;
}

void WebPProfileMarkMetalHash(void) {
  if (profile_context.active) profile_context.metal_hash = 1;
}
