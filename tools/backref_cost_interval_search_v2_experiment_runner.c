// Copyright 2026
//
// Private runner for untimed correctness/work diagnostics and the frozen,
// recorder-free CostManager interval-search v2 A/B.

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(__APPLE__)
#include <mach/mach_time.h>
#endif

#include "src/enc/backref_cost_interval_search_v2_experiment_enc.h"
#include "src/webp/encode.h"

#if !defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
static uint64_t NowNs(void) {
#if defined(__APPLE__)
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
#endif

static int ReadToken(FILE* const input, char* const token, size_t token_size) {
  int c;
  size_t length = 0;
  do {
    c = fgetc(input);
    if (c == '#') {
      do {
        c = fgetc(input);
      } while (c != '\n' && c != EOF);
    }
  } while (c != EOF && isspace(c));
  if (c == EOF) return 0;
  do {
    if (length + 1 >= token_size) return 0;
    token[length++] = (char)c;
    c = fgetc(input);
  } while (c != EOF && !isspace(c));
  token[length] = '\0';
  return 1;
}

static int ReadPPM(const char* const path, uint8_t** const rgb,
                   int* const width, int* const height) {
  FILE* const input = fopen(path, "rb");
  char token[32];
  size_t byte_count;
  uint8_t* pixels;
  if (input == NULL) return 0;
  if (!ReadToken(input, token, sizeof(token)) || strcmp(token, "P6") != 0 ||
      !ReadToken(input, token, sizeof(token))) {
    fclose(input);
    return 0;
  }
  *width = atoi(token);
  if (!ReadToken(input, token, sizeof(token))) {
    fclose(input);
    return 0;
  }
  *height = atoi(token);
  if (!ReadToken(input, token, sizeof(token)) || atoi(token) != 255 ||
      *width <= 0 || *height <= 0) {
    fclose(input);
    return 0;
  }
  byte_count = (size_t)*width * (size_t)*height * 3u;
  pixels = (uint8_t*)malloc(byte_count);
  if (pixels == NULL || fread(pixels, 1, byte_count, input) != byte_count ||
      fgetc(input) != EOF) {
    free(pixels);
    fclose(input);
    return 0;
  }
  fclose(input);
  *rgb = pixels;
  return 1;
}

static uint64_t Fnv1a64(const uint8_t* data, size_t size) {
  uint64_t hash = 1469598103934665603ULL;
  while (size-- > 0) {
    hash ^= *data++;
    hash *= 1099511628211ULL;
  }
  return hash;
}

static int VariantMatchesEnvironment(const char* const variant) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT");
  if (strcmp(variant, "candidate") == 0) {
    return value != NULL && strcmp(value, "1") == 0;
  }
  return strcmp(variant, "baseline") == 0 && value == NULL;
}

static int PreparePicture(const char* const input_path, int method,
                          WebPConfig* const config, WebPPicture* const picture) {
  uint8_t* rgb = NULL;
  int width = 0, height = 0;
  if ((method != 4 && method != 6) ||
      !ReadPPM(input_path, &rgb, &width, &height) ||
      !WebPConfigInit(config) || !WebPPictureInit(picture)) {
    free(rgb);
    return 0;
  }
  config->lossless = 1;
  config->exact = 1;
  config->quality = 75.f;
  config->method = method;
  config->thread_level = 0;
  picture->use_argb = 1;
  picture->width = width;
  picture->height = height;
  if (!WebPPictureImportRGB(picture, rgb, width * 3)) {
    free(rgb);
    WebPPictureFree(picture);
    return 0;
  }
  free(rgb);
  return 1;
}

static int Encode(WebPConfig* const config, WebPPicture* const picture,
                  WebPMemoryWriter* const writer) {
  WebPMemoryWriterInit(writer);
  picture->writer = WebPMemoryWrite;
  picture->custom_ptr = writer;
  return WebPEncode(config, picture);
}

static int Correctness(const char* const input_path, int method,
                       const char* const output_path) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  FILE* output;
  int ok;
  if (!PreparePicture(input_path, method, &config, &picture)) return 10;
  ok = Encode(&config, &picture, &writer);
  WebPPictureFree(&picture);
  if (!ok) return 11;
  output = fopen(output_path, "wb");
  if (output == NULL) {
    WebPMemoryWriterClear(&writer);
    return 12;
  }
  if (fwrite(writer.mem, 1, writer.size, output) != writer.size) {
    fclose(output);
    WebPMemoryWriterClear(&writer);
    return 12;
  }
  if (fclose(output) != 0) {
    WebPMemoryWriterClear(&writer);
    return 12;
  }
  WebPMemoryWriterClear(&writer);
  return 0;
}

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
static int Diagnostic(const char* const input_path, const char* const case_id,
                      int method, const char* const variant) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  VP8LBackrefCostIntervalSearchV2Stats stats;
  uint64_t digest;
  if (!VariantMatchesEnvironment(variant)) return 20;
  if (!PreparePicture(input_path, method, &config, &picture)) return 21;
  VP8LBackrefCostIntervalSearchV2StatsReset();
  if (!Encode(&config, &picture, &writer)) {
    WebPPictureFree(&picture);
    return 22;
  }
  VP8LBackrefCostIntervalSearchV2StatsGet(&stats);
  digest = Fnv1a64(writer.mem, writer.size);
  printf(
      "{\"schema\":\"libwebp-backref-cost-interval-search-v2-work-v1\","
      "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
      "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\","
      "\"runtime_activations\":%llu,\"injected_fallbacks\":%llu,"
      "\"push_calls\":%llu,\"short_push_calls\":%llu,"
      "\"cache_segments\":%llu,\"overlap_scans\":%llu,"
      "\"disjoint_prefix_scans\":%llu,\"insert_calls\":%llu,"
      "\"null_hint_insert_calls\":%llu,"
      "\"position_backward_steps\":%llu,"
      "\"position_forward_steps\":%llu,"
      "\"append_hint_fast_paths\":%llu,"
      "\"append_hint_branch_checks\":%llu,"
      "\"append_hint_loads\":%llu,"
      "\"append_hint_start_loads\":%llu,"
      "\"append_hint_update_checks\":%llu,"
      "\"append_hint_updates\":%llu,"
      "\"pop_tail_branch_checks\":%llu,"
      "\"pop_tail_updates\":%llu,"
      "\"interval_updates\":%llu,\"interval_pops\":%llu,"
      "\"max_live_intervals\":%llu}\n",
      case_id, method, variant, (unsigned long long)writer.size,
      (unsigned long long)digest,
      (unsigned long long)stats.runtime_activations,
      (unsigned long long)stats.injected_fallbacks,
      (unsigned long long)stats.push_calls,
      (unsigned long long)stats.short_push_calls,
      (unsigned long long)stats.cache_segments,
      (unsigned long long)stats.overlap_scans,
      (unsigned long long)stats.disjoint_prefix_scans,
      (unsigned long long)stats.insert_calls,
      (unsigned long long)stats.null_hint_insert_calls,
      (unsigned long long)stats.position_backward_steps,
      (unsigned long long)stats.position_forward_steps,
      (unsigned long long)stats.append_hint_fast_paths,
      (unsigned long long)stats.append_hint_branch_checks,
      (unsigned long long)stats.append_hint_loads,
      (unsigned long long)stats.append_hint_start_loads,
      (unsigned long long)stats.append_hint_update_checks,
      (unsigned long long)stats.append_hint_updates,
      (unsigned long long)stats.pop_tail_branch_checks,
      (unsigned long long)stats.pop_tail_updates,
      (unsigned long long)stats.interval_updates,
      (unsigned long long)stats.interval_pops,
      (unsigned long long)stats.max_live_intervals);
  WebPMemoryWriterClear(&writer);
  WebPPictureFree(&picture);
  return 0;
}
#endif

static int Sample(const char* const input_path, const char* const case_id,
                  const char* const lifecycle, const char* const variant,
                  int method, int warmups, int measured) {
#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
  (void)input_path;
  (void)case_id;
  (void)lifecycle;
  (void)variant;
  (void)method;
  (void)warmups;
  (void)measured;
  fputs("recorder build refuses timed samples\n", stderr);
  return 30;
#else
  const char* const session = getenv("WEBP_BENCHMARK_SESSION");
  WebPConfig config;
  WebPPicture picture;
  int iteration;
  if (session == NULL || strcmp(session, "exclusive") != 0) return 31;
  if (!VariantMatchesEnvironment(variant) ||
      (strcmp(lifecycle, "cold") != 0 && strcmp(lifecycle, "warm") != 0) ||
      warmups < 0 || measured <= 0 ||
      (strcmp(lifecycle, "cold") == 0 && (warmups != 0 || measured != 1)) ||
      (strcmp(lifecycle, "warm") == 0 && (warmups != 2 || measured != 9))) {
    return 32;
  }
  if (!PreparePicture(input_path, method, &config, &picture)) return 33;
  for (iteration = 0; iteration < warmups + measured; ++iteration) {
    WebPMemoryWriter writer;
    uint64_t start_ns, elapsed_ns, digest;
    start_ns = NowNs();
    if (!Encode(&config, &picture, &writer)) {
      WebPPictureFree(&picture);
      return 34;
    }
    elapsed_ns = NowNs() - start_ns;
    digest = Fnv1a64(writer.mem, writer.size);
    printf(
        "{\"schema\":\"libwebp-backref-cost-interval-search-v2-sample-v1\","
        "\"case_id\":\"%s\",\"lifecycle\":\"%s\","
        "\"variant\":\"%s\",\"method\":%d,\"iteration\":%d,"
        "\"sample_role\":\"%s\",\"elapsed_ns\":%llu,"
        "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\"}\n",
        case_id, lifecycle, variant, method, iteration,
        iteration < warmups ? "warmup" : lifecycle,
        (unsigned long long)elapsed_ns, (unsigned long long)writer.size,
        (unsigned long long)digest);
    WebPMemoryWriterClear(&writer);
  }
  WebPPictureFree(&picture);
  return 0;
#endif
}

int main(int argc, char** argv) {
  // Frozen remote form: INPUT CASE LIFECYCLE VARIANT METHOD WARMUPS MEASURED.
  if (argc == 8) {
    return Sample(argv[1], argv[2], argv[3], argv[4], atoi(argv[5]),
                  atoi(argv[6]), atoi(argv[7]));
  }
  if (argc == 5 && strcmp(argv[1], "correctness") == 0) {
    return Correctness(argv[2], atoi(argv[3]), argv[4]);
  }
#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
  if (argc == 6 && strcmp(argv[1], "diagnostic") == 0) {
    return Diagnostic(argv[2], argv[3], atoi(argv[4]), argv[5]);
  }
#endif
  if (argc == 9 && strcmp(argv[1], "sample") == 0) {
    return Sample(argv[2], argv[3], argv[4], argv[5], atoi(argv[6]),
                  atoi(argv[7]), atoi(argv[8]));
  }
  fputs("invalid interval-search v2 runner arguments\n", stderr);
  return 2;
}
