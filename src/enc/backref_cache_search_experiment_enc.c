// Copyright 2026
//
// Low-distortion recorder for one independently gated cache-search boundary.

#include "src/enc/backref_cache_search_experiment_enc.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#include <unistd.h>
#define WEBP_CACHE_SEARCH_GETPID getpid
#elif defined(_WIN32)
#include <process.h>
#include <windows.h>
#define WEBP_CACHE_SEARCH_GETPID _getpid
#else
#include <unistd.h>
#define WEBP_CACHE_SEARCH_GETPID getpid
#endif

#if defined(_MSC_VER)
#define WEBP_CACHE_SEARCH_TLS __declspec(thread)
#else
#define WEBP_CACHE_SEARCH_TLS __thread
#endif

typedef struct {
  int active;
  int control;
  int inject_record_failure;
  int method;
  int width;
  int height;
  int encode_index;
  uint64_t encode_start_ns;
  uint64_t backref_total_ns;
  uint64_t cache_search_ns;
  uint32_t backref_total_calls;
  uint32_t cache_search_calls;
} WebPBackrefCacheSearchContext;

static WEBP_CACHE_SEARCH_TLS WebPBackrefCacheSearchContext context;
static WEBP_CACHE_SEARCH_TLS int process_encode_index;

static uint64_t CacheSearchNowNs(void) {
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

void WebPBackrefCacheSearchBegin(const WebPConfig* config,
                                 const WebPPicture* picture) {
  const char* const opt_in =
      getenv("WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT");
  memset(&context, 0, sizeof(context));
  if (opt_in == NULL) return;
  if (strcmp(opt_in, "1") != 0) {
    fprintf(stderr,
            "backref-cache-search experiment refuses invalid "
            "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT (expected exact value 1)\n");
    return;
  }
  if (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
      strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0) {
    fprintf(stderr,
            "backref-cache-search experiment refuses timing without "
            "WEBP_BENCHMARK_SESSION=exclusive\n");
    return;
  }
  context.active = 1;
  context.control =
      ExactEnvironmentFlag("WEBP_BACKREF_CACHE_SEARCH_CONTROL");
  context.inject_record_failure = ExactEnvironmentFlag(
      "WEBP_BACKREF_CACHE_SEARCH_INJECT_RECORD_FAILURE");
  context.method = config != NULL ? config->method : -1;
  context.width = picture != NULL ? picture->width : 0;
  context.height = picture != NULL ? picture->height : 0;
  context.encode_index = process_encode_index++;
  context.encode_start_ns = CacheSearchNowNs();
}

static uint64_t StageBegin(void) {
  return (!context.active || context.control) ? 0 : CacheSearchNowNs();
}

uint64_t WebPBackrefCacheSearchTotalBegin(void) { return StageBegin(); }

void WebPBackrefCacheSearchTotalEnd(uint64_t start_ns) {
  if (!context.active || context.control || start_ns == 0) return;
  context.backref_total_ns += CacheSearchNowNs() - start_ns;
  ++context.backref_total_calls;
}

uint64_t WebPBackrefCacheSearchStageBegin(void) { return StageBegin(); }

void WebPBackrefCacheSearchStageEnd(uint64_t start_ns) {
  if (!context.active || context.control || start_ns == 0) return;
  context.cache_search_ns += CacheSearchNowNs() - start_ns;
  ++context.cache_search_calls;
}

void WebPBackrefCacheSearchEnd(int ok, int error_code) {
  const uint64_t total_ns =
      context.active ? CacheSearchNowNs() - context.encode_start_ns : 0;
  const char* const output_path =
      getenv("WEBP_BACKREF_CACHE_SEARCH_OUTPUT");
  const char* const lifecycle =
      getenv("WEBP_BACKREF_CACHE_SEARCH_LIFECYCLE");
  const char* const run_id = getenv("WEBP_BACKREF_CACHE_SEARCH_RUN_ID");
  const char* const case_id = getenv("WEBP_BACKREF_CACHE_SEARCH_CASE_ID");
  const char* sample_role;
  FILE* out;
  if (!context.active) return;
  context.active = 0;
  if (context.inject_record_failure) return;
  sample_role = lifecycle != NULL && strcmp(lifecycle, "warm") == 0
                    ? (context.encode_index == 0 ? "warmup" : "warm")
                    : "cold";
  out = output_path == NULL || output_path[0] == '\0'
            ? stderr
            : fopen(output_path, "a");
  if (out == NULL) return;
  fputs("{\"schema\":\"libwebp-backref-cache-search-v1\",\"run_id\":", out);
  PrintJsonString(out, run_id);
  fputs(",\"case_id\":", out);
  PrintJsonString(out, case_id);
  fprintf(out,
          ",\"pid\":%ld,\"encode_index\":%d,\"sample_role\":\"%s\","
          "\"variant\":\"%s\",\"method\":%d,\"width\":%d,\"height\":%d,"
          "\"pixels\":%llu,\"ok\":%s,\"error_code\":%d,\"total_ns\":%llu,"
          "\"stages\":{\"backref_total\":{\"elapsed_ns\":%llu,\"calls\":%u},"
          "\"cache_search\":{\"elapsed_ns\":%llu,\"calls\":%u}}}\n",
          (long)WEBP_CACHE_SEARCH_GETPID(), context.encode_index, sample_role,
          context.control ? "control" : "record", context.method,
          context.width, context.height,
          (unsigned long long)context.width * (unsigned)context.height,
          ok ? "true" : "false", error_code, (unsigned long long)total_ns,
          (unsigned long long)context.backref_total_ns,
          context.backref_total_calls,
          (unsigned long long)context.cache_search_ns,
          context.cache_search_calls);
  if (out != stderr) fclose(out);
}
