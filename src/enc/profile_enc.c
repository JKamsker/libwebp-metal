// Copyright 2026
//
// Internal, independently guarded encoder stage profiling experiment.

#if !defined(WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT) &&       \
    !defined(WEBP_BACKREF_COST_ATTRIBUTION_V1_MARKERS) &&        \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT) && \
    !defined(                                                      \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT) && \
    !defined(                                                      \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_EXPERIMENT) && \
    !defined(                                                      \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_EXPERIMENT) && \
    !defined(                                                      \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT) && \
    !defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT)
#define WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT 1
#endif
#include "src/enc/profile_enc.h"

#if defined(WEBP_BACKREF_COST_ATTRIBUTION_V1_MARKERS)
#include "src/enc/backref_cost_attribution_v1_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v2_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v3_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v4_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v5_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v6_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v7_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v8_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v9_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v10_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v11_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v12_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v13_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v14_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v15_experiment_enc.h"
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
#include "src/enc/backref_cost_attribution_v16_experiment_enc.h"
#elif defined(                                                          \
    WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT)
#include "src/enc/backref_cost_specialization_factorization_v1_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_SAMPLE_SET"
#elif defined(                                                          \
    WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_EXPERIMENT)
#include "src/enc/backref_cost_specialization_factorization_v2_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_SAMPLE_SET"
#elif defined(                                                          \
    WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_EXPERIMENT)
#include "src/enc/backref_cost_specialization_factorization_v3_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_SAMPLE_SET"
#elif defined(                                                          \
    WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT)
#include "src/enc/backref_cost_specialization_factorization_v4_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_SAMPLE_SET"
#elif defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_EXPERIMENT)
#include "src/enc/backref_cost_specialization_alignment_v1_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_SAMPLE_SET"
#elif defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT)
#include "src/enc/backref_cost_specialization_alignment_v2_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_SAMPLE_SET"
#elif defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT)
#include "src/enc/backref_cost_specialization_alignment_v3_experiment_enc.h"
#define WEBP_FACTORIZATION_VARIANT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_VARIANT"
#define WEBP_FACTORIZATION_TIMERS_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_TIMERS"
#define WEBP_FACTORIZATION_STAGE_OUTPUT_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_STAGE_OUTPUT"
#define WEBP_FACTORIZATION_RUN_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_RUN_ID"
#define WEBP_FACTORIZATION_CASE_ID_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_CASE_ID"
#define WEBP_FACTORIZATION_SAMPLE_SET_ENV \
  "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_SAMPLE_SET"
#endif

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
    "backref_cost_dp_total",
    "backref_cost_dp_setup",
    "backref_cost_dp_steady",
    "backref_cost_traceback",
    "backref_cost_materialize",
    "metal_init",
    "metal_cross_color_dispatch",
    "metal_hash_pipeline_init",
    "metal_hash_dispatch",
    "lossy_import",
    "lossy_encoder_init",
    "lossy_analyze",
    "lossy_stat_loop",
    "lossy_encode_loop",
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

#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT) || \
    defined(                                                       \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT) || \
    defined(                                                       \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_EXPERIMENT) || \
    defined(                                                       \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_EXPERIMENT) || \
    defined(                                                       \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT)
uint64_t WebPProfileClockNowForValidation(void) { return ProfileNowNs(); }
#endif

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
#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT)
  VP8LBackrefCostAttributionV3ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT)
  VP8LBackrefCostAttributionV4ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT)
  VP8LBackrefCostAttributionV5ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
  VP8LBackrefCostAttributionV6ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT)
  VP8LBackrefCostAttributionV7ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT)
  VP8LBackrefCostAttributionV8ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT)
  VP8LBackrefCostAttributionV9ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT)
  VP8LBackrefCostAttributionV10ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT)
  VP8LBackrefCostAttributionV11ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT)
  VP8LBackrefCostAttributionV12ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT)
  VP8LBackrefCostAttributionV13ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
  VP8LBackrefCostAttributionV14ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT)
  VP8LBackrefCostAttributionV15ResetCounters();
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
  VP8LBackrefCostAttributionV16ResetCounters();
#endif
#if defined(WEBP_BACKREF_COST_ATTRIBUTION_V1_MARKERS)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V1_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V2_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V3_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V4_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V5_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V6_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V7_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V8_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V9_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V10_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V11_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V12_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V13_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V14_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V15_TIMERS")) return;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT") &&
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT") != NULL) {
    return;
  }
  if (!EnvironmentOptIn("WEBP_BACKREF_COST_ATTRIBUTION_V16_TIMERS")) return;
#elif defined(                                                          \
          WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT)
  {
    const char* const variant = getenv(WEBP_FACTORIZATION_VARIANT_ENV);
    if (variant == NULL ||
        (strcmp(variant, "B") != 0 && strcmp(variant, "L") != 0 &&
         strcmp(variant, "H") != 0)) {
      return;
    }
  }
  if (!EnvironmentOptIn(WEBP_FACTORIZATION_TIMERS_ENV)) {
    return;
  }
#else
  if (!EnvironmentOptIn("WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT")) return;
#endif
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
#if defined(WEBP_BACKREF_COST_ATTRIBUTION_V1_MARKERS)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V1_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V1_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V1_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV1ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V1_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV2ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V3_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V3_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V3_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV3ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V3_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V4_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V4_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V4_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV4ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V4_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V5_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V5_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V5_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV5ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V5_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V6_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V6_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V6_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV6ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V6_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V7_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V7_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V7_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV7ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V7_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V8_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V8_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V8_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV8ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V8_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V9_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V9_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V9_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV9ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V9_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V10_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V10_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V10_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV10ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V10_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V11_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V11_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V11_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV11ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V11_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV12ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V13_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V13_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V13_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV13ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V13_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V14_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V14_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V14_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV14ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V14_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V15_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V15_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V15_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV15ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V15_SAMPLE_SET");
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
  const char* const output_path =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_STAGE_OUTPUT");
  const char* const run_id = getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_RUN_ID");
  const char* const case_id =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_CASE_ID");
  const char* const backend = VP8LBackrefCostAttributionV16ExperimentEnabled()
                                  ? "candidate"
                                  : "baseline";
  const char* const sample_set =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_SAMPLE_SET");
#elif defined(                                                          \
          WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_EXPERIMENT) || \
    defined(                                                            \
        WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT)
  const char* const output_path = getenv(WEBP_FACTORIZATION_STAGE_OUTPUT_ENV);
  const char* const run_id = getenv(WEBP_FACTORIZATION_RUN_ID_ENV);
  const char* const case_id = getenv(WEBP_FACTORIZATION_CASE_ID_ENV);
  const char* const backend = getenv(WEBP_FACTORIZATION_VARIANT_ENV);
  const char* const sample_set = getenv(WEBP_FACTORIZATION_SAMPLE_SET_ENV);
#else
  const char* const output_path = getenv("WEBP_STAGE_PROFILE_OUTPUT");
  const char* const run_id = getenv("WEBP_STAGE_PROFILE_RUN_ID");
  const char* const case_id = getenv("WEBP_STAGE_PROFILE_CASE_ID");
  const char* const backend = getenv("WEBP_STAGE_PROFILE_BACKEND");
  const char* const sample_set = getenv("WEBP_STAGE_PROFILE_SAMPLE_SET");
#endif
  const uint64_t total_ns =
      ctx->active ? ProfileNowNs() - ctx->total_start_ns : 0;
  const char* sample_role;
#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT)
  const VP8LBackrefCostAttributionV3Counters attribution_counters =
      VP8LBackrefCostAttributionV3GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT)
  const VP8LBackrefCostAttributionV4Counters attribution_counters =
      VP8LBackrefCostAttributionV4GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT)
  const VP8LBackrefCostAttributionV5Counters attribution_counters =
      VP8LBackrefCostAttributionV5GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
  const VP8LBackrefCostAttributionV6Counters attribution_counters =
      VP8LBackrefCostAttributionV6GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT)
  const VP8LBackrefCostAttributionV7Counters attribution_counters =
      VP8LBackrefCostAttributionV7GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT)
  const VP8LBackrefCostAttributionV8Counters attribution_counters =
      VP8LBackrefCostAttributionV8GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT)
  const VP8LBackrefCostAttributionV9Counters attribution_counters =
      VP8LBackrefCostAttributionV9GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT)
  const VP8LBackrefCostAttributionV10Counters attribution_counters =
      VP8LBackrefCostAttributionV10GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT)
  const VP8LBackrefCostAttributionV11Counters attribution_counters =
      VP8LBackrefCostAttributionV11GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT)
  const VP8LBackrefCostAttributionV12Counters attribution_counters =
      VP8LBackrefCostAttributionV12GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT)
  const VP8LBackrefCostAttributionV13Counters attribution_counters =
      VP8LBackrefCostAttributionV13GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
  const VP8LBackrefCostAttributionV14Counters attribution_counters =
      VP8LBackrefCostAttributionV14GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT)
  const VP8LBackrefCostAttributionV15Counters attribution_counters =
      VP8LBackrefCostAttributionV15GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
  const VP8LBackrefCostAttributionV16Counters attribution_counters =
      VP8LBackrefCostAttributionV16GetCounters();
  const unsigned int selected_dp_calls =
      attribution_counters.baseline_dp_calls +
      attribution_counters.candidate_dp_calls;
#endif
  FILE* out;
  int i;
  if (!ctx->active) return;
  ctx->active = 0;
  if (sample_set != NULL && (strcmp(sample_set, "warm") == 0 ||
                             strcmp(sample_set, "warm-dominant") == 0)) {
    sample_role = (ctx->encode_index == 0) ? "warmup" : "warm";
  } else {
    sample_role = "cold";
  }
  out = (output_path == NULL || output_path[0] == '\0')
            ? stderr
            : fopen(output_path, "a");
  if (out == NULL) return;
  fputs("{\"schema\":\"libwebp-encoder-stage-v1\",\"record_type\":\"encode\",",
        out);
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
          "\"metal_hash\":%s,\"total_ns\":%llu,"
#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
          "\"selector_evaluations\":%u,\"selected_dp_calls\":%u,"
          "\"baseline_dp_calls\":%u,\"candidate_dp_calls\":%u,"
#endif
          "\"stages\":{",
          (long)WEBP_PROFILE_GETPID(), ctx->encode_index, sample_role,
          ctx->method, ctx->quality, ctx->lossless ? "true" : "false",
          ctx->exact ? "true" : "false", ctx->thread_level, ctx->width,
          ctx->height, (unsigned long long)ctx->width * ctx->height,
          ok ? "true" : "false", error_code,
          (unsigned long long)ctx->output_size,
          ctx->metal_cross_color ? "true" : "false",
          ctx->metal_hash ? "true" : "false", (unsigned long long)total_ns
#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT) || \
    defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)
          ,
          attribution_counters.selector_evaluations, selected_dp_calls,
          attribution_counters.baseline_dp_calls,
          attribution_counters.candidate_dp_calls
#endif
  );
  {
    int first = 1;
    for (i = 0; i < WEBP_PROFILE_STAGE_COUNT; ++i) {
      if (ctx->calls[i] == 0) continue;
      fprintf(out, "%s\"%s\":{\"ns\":%llu,\"calls\":%u}", first ? "" : ",",
              kStageNames[i], (unsigned long long)ctx->elapsed_ns[i],
              ctx->calls[i]);
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
