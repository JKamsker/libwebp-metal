// Copyright 2026
//
// Private diagnostic runner for the backref-cost specialization aligned null stage attribution v3 pipeline.

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "src/enc/backref_cost_aligned_null_stage_attribution_v3_experiment_enc.h"
#include "src/enc/profile_enc.h"
#include "src/webp/decode.h"
#include "src/webp/encode.h"

// The frozen remote operator sets these fields only for real pipeline runner
// children.  The child emits its own PID/PPID and blocks before encoder work
// until the retained direct parent validates the receipt and returns the exact
// creation token.  Local build/semantic tests intentionally leave the opt-in
// absent and therefore perform no handshake.
static int DirectChildAdmission(void) {
  const char* const enabled = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_DIRECT_CHILD");
  const char* const ordinal = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_ORDINAL");
  const char* const token = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_CREATION_TOKEN");
  const char* const purpose = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_PURPOSE");
  const char* const lifecycle = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_LIFECYCLE");
  const char* const variant = getenv(
      "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_VARIANT");
  const char* const case_id = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_CASE_ID");
  const char* const method = getenv("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CHILD_METHOD");
  struct timespec started;
  char authorization[192];
  char expected[192];
  if (enabled == NULL) return 1;
  if (strcmp(enabled, "1") != 0 || ordinal == NULL || token == NULL ||
      purpose == NULL || lifecycle == NULL || variant == NULL ||
      case_id == NULL || method == NULL || token[0] == '\0' ||
      strchr(token, '\n') != NULL) {
    return 0;
  }
  if (clock_gettime(CLOCK_MONOTONIC, &started) != 0) return 0;
  fprintf(stderr,
          "{\"schema\":\"libwebp-backref-cost-aligned-null-stage-attribution-v3-child-start-v1\","
          "\"ordinal\":%s,\"pid\":%ld,\"ppid_observed\":%ld,"
          "\"creation_identity\":\"%s\",\"start_token\":\"%llu\","
          "\"variant\":\"%s\",\"case_id\":\"%s\",\"method\":%s,"
          "\"lifecycle\":\"%s\",\"purpose\":\"%s\","
          "\"shell\":false,\"wrapper\":false,\"grandchild\":false}\n",
          ordinal, (long)getpid(), (long)getppid(), token,
          (unsigned long long)started.tv_sec * 1000000000ull +
              (unsigned long long)started.tv_nsec, variant,
          case_id, method, lifecycle, purpose);
  fflush(stderr);
  if (snprintf(expected, sizeof(expected), "GO %s\n", token) < 0 ||
      fgets(authorization, sizeof(authorization), stdin) == NULL ||
      strcmp(authorization, expected) != 0) {
    return 0;
  }
  return 1;
}

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

static int CompareUint64(const void* a, const void* b) {
  const uint64_t lhs = *(const uint64_t*)a;
  const uint64_t rhs = *(const uint64_t*)b;
  return (lhs > rhs) - (lhs < rhs);
}

static int VariantMatchesEnvironment(const char* const variant) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_VARIANT");
  return value != NULL && strcmp(value, variant) == 0 &&
         (strcmp(variant, "B") == 0 || strcmp(variant, "L") == 0) &&
         VP8LBackrefCostAlignedNullStageAttributionV3GetVariant() !=
             WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

static int PreparePicture(const char* const input_path, int method,
                          WebPConfig* const config,
                          WebPPicture* const picture) {
  uint8_t* rgb = NULL;
  int width = 0, height = 0;
  if ((method != 4 && method != 6) ||
      !ReadPPM(input_path, &rgb, &width, &height) || !WebPConfigInit(config) ||
      !WebPPictureInit(picture)) {
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
                       const char* const variant, const char* const output) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  uint8_t* expected = NULL;
  uint8_t* decoded = NULL;
  int expected_width = 0, expected_height = 0;
  int decoded_width = 0, decoded_height = 0;
  size_t expected_size;
  FILE* file;
  int ok;
  if (!VariantMatchesEnvironment(variant)) return 20;
  if (!ReadPPM(input_path, &expected, &expected_width, &expected_height) ||
      !PreparePicture(input_path, method, &config, &picture)) {
    free(expected);
    return 21;
  }
  ok = Encode(&config, &picture, &writer);
  WebPPictureFree(&picture);
  if (!ok) {
    free(expected);
    return 22;
  }
  decoded =
      WebPDecodeRGB(writer.mem, writer.size, &decoded_width, &decoded_height);
  expected_size = (size_t)expected_width * expected_height * 3u;
  if (decoded == NULL || decoded_width != expected_width ||
      decoded_height != expected_height ||
      memcmp(decoded, expected, expected_size) != 0) {
    WebPFree(decoded);
    free(expected);
    WebPMemoryWriterClear(&writer);
    return 24;
  }
  WebPFree(decoded);
  free(expected);
  file = fopen(output, "wb");
  if (file == NULL) {
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  if (fwrite(writer.mem, 1, writer.size, file) != writer.size) {
    fclose(file);
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  if (fclose(file) != 0) {
    WebPMemoryWriterClear(&writer);
    return 23;
  }
  WebPMemoryWriterClear(&writer);
  return 0;
}

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
// Untimed schema fixtures exercise legitimate skips/repeats and failed outer
// sessions without encoding pixels. They are available only in the separate
// audit binary and therefore cannot enter the timed workload.
static int LedgerFixture(const char* const name) {
  WebPConfig config;
  WebPPicture picture;
  uint64_t start;
  int ok = 0;
  int error_code = VP8_ENC_ERROR_BAD_DIMENSION;
  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) return 70;
  config.lossless = 1;
  config.method = 4;
  picture.width = 0;
  picture.height = 0;
  WebPProfileBeginSession(&config, &picture);
  if (strcmp(name, "early-return") == 0) {
    // No stage is entered.
  } else if (strcmp(name, "allocation-failure") == 0) {
    start = WebPProfileStageBegin(WEBP_PROFILE_LOSSLESS_PREPARE);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSLESS_PREPARE, start);
    error_code = VP8_ENC_ERROR_OUT_OF_MEMORY;
  } else if (strcmp(name, "empty-input") == 0) {
    start = WebPProfileStageBegin(WEBP_PROFILE_LOSSLESS_CONTAINER_SETUP);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSLESS_CONTAINER_SETUP, start);
  } else if (strcmp(name, "tiny-skip") == 0) {
    start = WebPProfileStageBegin(WEBP_PROFILE_LOSSLESS_PREPARE);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSLESS_PREPARE, start);
    start = WebPProfileStageBegin(WEBP_PROFILE_LOSSLESS_STREAM_FINALIZE);
    WebPProfileStageEnd(WEBP_PROFILE_LOSSLESS_STREAM_FINALIZE, start);
    ok = 1;
    error_code = VP8_ENC_OK;
  } else if (strcmp(name, "repeated-stage") == 0) {
    int repeat;
    for (repeat = 0; repeat < 2; ++repeat) {
      start = WebPProfileStageBegin(WEBP_PROFILE_LOSSLESS_PREPARE);
      WebPProfileStageEnd(WEBP_PROFILE_LOSSLESS_PREPARE, start);
    }
    ok = 1;
    error_code = VP8_ENC_OK;
  } else {
    WebPProfileEndSession(0, VP8_ENC_ERROR_INVALID_CONFIGURATION);
    return 71;
  }
  WebPProfileEndSession(ok, error_code);
  return 0;
}

static int WorkCheck(const char* const input_path, const char* const case_id,
                     int method, const char* const variant) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  VP8LBackrefCostAlignedNullStageAttributionV3Stats observed;
  uint64_t digest;
  uint64_t selected_dp_calls;

  if (!VariantMatchesEnvironment(variant)) return 40;
  VP8LBackrefCostAlignedNullStageAttributionV3StatsReset();
  if (!PreparePicture(input_path, method, &config, &picture)) {
    return 42;
  }
  if (!Encode(&config, &picture, &writer)) {
    WebPPictureFree(&picture);
    return 43;
  }
  WebPPictureFree(&picture);
  VP8LBackrefCostAlignedNullStageAttributionV3StatsGet(&observed);
  selected_dp_calls = observed.baseline_dp_calls + observed.layout_clone_dp_calls;
  if (observed.selector_evaluations == 0 ||
      observed.selector_evaluations != selected_dp_calls ||
      observed.exact_activations != observed.selector_evaluations ||
      (strcmp(variant, "B") == 0 &&
       (observed.baseline_dp_calls != selected_dp_calls ||
        observed.layout_clone_dp_calls != 0)) ||
      (strcmp(variant, "L") == 0 &&
       (observed.layout_clone_dp_calls != selected_dp_calls ||
        observed.baseline_dp_calls != 0))) {
    WebPMemoryWriterClear(&writer);
    return 44;
  }
  digest = Fnv1a64(writer.mem, writer.size);
  printf(
      "{\"schema\":\"libwebp-backref-cost-aligned-null-stage-attribution-v3-work-v1\","
      "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
      "\"selector_evaluations\":%llu,\"baseline_dp_calls\":%llu,"
      "\"layout_clone_dp_calls\":%llu,"
      "\"exact_activations\":%llu,\"push_calls\":%llu,"
      "\"short_push_calls\":%llu,\"cache_segments\":%llu,"
      "\"overlap_scans\":%llu,\"disjoint_prefix_scans\":%llu,"
      "\"insert_calls\":%llu,\"null_hint_insert_calls\":%llu,"
      "\"position_backward_steps\":%llu,\"position_forward_steps\":%llu,"
      "\"append_hint_fast_paths\":%llu,\"append_hint_branch_checks\":%llu,"
      "\"append_hint_loads\":%llu,\"append_hint_start_loads\":%llu,"
      "\"append_hint_update_checks\":%llu,\"append_hint_updates\":%llu,"
      "\"pop_tail_branch_checks\":%llu,\"pop_tail_updates\":%llu,"
      "\"interval_updates\":%llu,\"interval_pops\":%llu,"
      "\"max_live_intervals\":%llu,\"bitstream_bytes\":%llu,"
      "\"bitstream_fnv1a64\":\"%016llx\"}\n",
      case_id, method, variant,
      (unsigned long long)observed.selector_evaluations,
      (unsigned long long)observed.baseline_dp_calls,
      (unsigned long long)observed.layout_clone_dp_calls,
      (unsigned long long)observed.exact_activations,
      (unsigned long long)observed.push_calls,
      (unsigned long long)observed.short_push_calls,
      (unsigned long long)observed.cache_segments,
      (unsigned long long)observed.overlap_scans,
      (unsigned long long)observed.disjoint_prefix_scans,
      (unsigned long long)observed.insert_calls,
      (unsigned long long)observed.null_hint_insert_calls,
      (unsigned long long)observed.position_backward_steps,
      (unsigned long long)observed.position_forward_steps,
      (unsigned long long)observed.append_hint_fast_paths,
      (unsigned long long)observed.append_hint_branch_checks,
      (unsigned long long)observed.append_hint_loads,
      (unsigned long long)observed.append_hint_start_loads,
      (unsigned long long)observed.append_hint_update_checks,
      (unsigned long long)observed.append_hint_updates,
      (unsigned long long)observed.pop_tail_branch_checks,
      (unsigned long long)observed.pop_tail_updates,
      (unsigned long long)observed.interval_updates,
      (unsigned long long)observed.interval_pops,
      (unsigned long long)observed.max_live_intervals,
      (unsigned long long)writer.size, (unsigned long long)digest);
  WebPMemoryWriterClear(&writer);
  return 0;
}
#endif

static int TimerCheck(void) {
  const unsigned int reads = 4096;
  uint64_t deltas[4095];
  uint64_t first = WebPProfileClockNowForValidation();
  uint64_t previous = first;
  uint64_t minimum_delta = UINT64_MAX;
  uint64_t maximum_delta = 0;
  unsigned int positive_deltas = 0;
  unsigned int i;
  for (i = 1; i < reads; ++i) {
    const uint64_t current = WebPProfileClockNowForValidation();
    const uint64_t delta = current - previous;
    deltas[i - 1] = delta;
    if (current < previous) return 50;
    if (delta > 0) {
      if (delta < minimum_delta) minimum_delta = delta;
      if (delta > maximum_delta) maximum_delta = delta;
      ++positive_deltas;
    }
    previous = current;
  }
  if (positive_deltas == 0 || previous <= first) return 51;
  qsort(deltas, reads - 1, sizeof(deltas[0]), CompareUint64);
  printf(
      "{\"schema\":\"libwebp-backref-cost-aligned-null-stage-attribution-v3-timer-check-v1\","
      "\"clock_reads\":%u,\"positive_deltas\":%u,"
      "\"elapsed_ns\":%llu,\"mean_read_delta_ns\":%llu,"
      "\"minimum_positive_delta_ns\":%llu,"
      "\"p50_read_delta_ns\":%llu,\"p95_read_delta_ns\":%llu,"
      "\"p99_read_delta_ns\":%llu,"
      "\"maximum_delta_ns\":%llu,\"monotonic\":true}\n",
      reads, positive_deltas, (unsigned long long)(previous - first),
      (unsigned long long)((previous - first) / (reads - 1)),
      (unsigned long long)minimum_delta,
      (unsigned long long)deltas[(reads - 1) * 50 / 100],
      (unsigned long long)deltas[(reads - 1) * 95 / 100],
      (unsigned long long)deltas[(reads - 1) * 99 / 100],
      (unsigned long long)maximum_delta);
  return 0;
}

static int Profile(const char* const input_path, const char* const case_id,
                   int method, const char* const variant, int warmups,
                   int measured) {
  const char* const session = getenv("WEBP_BENCHMARK_SESSION");
  const char* const timers = getenv("WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_TIMERS");
  WebPConfig config;
  WebPPicture picture;
  int iteration;
  if (session == NULL || strcmp(session, "exclusive") != 0 || timers == NULL ||
      strcmp(timers, "1") != 0) {
    return 30;
  }
  if (!VariantMatchesEnvironment(variant) ||
      !((warmups == 1 && measured == 4) ||
        (warmups == 0 && measured == 1 &&
         getenv("WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_SAMPLE_SET") !=
             NULL &&
         strcmp(getenv(
                    "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_SAMPLE_SET"),
                "timer-validation") == 0))) {
    return 31;
  }
  if (!PreparePicture(input_path, method, &config, &picture)) return 32;
  for (iteration = 0; iteration < warmups + measured; ++iteration) {
    WebPMemoryWriter writer;
    uint64_t digest;
    if (!Encode(&config, &picture, &writer)) {
      WebPPictureFree(&picture);
      return 33;
    }
    digest = Fnv1a64(writer.mem, writer.size);
    printf(
        "{\"schema\":\"libwebp-backref-cost-aligned-null-stage-attribution-v3-output-v1\","
        "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
        "\"iteration\":%d,\"sample_role\":\"%s\","
        "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\"}\n",
        case_id, method, variant, iteration,
        (warmups == 0) ? "timer-validation" :
        (iteration < warmups ? "warmup" : "retained"),
        (unsigned long long)writer.size, (unsigned long long)digest);
    WebPMemoryWriterClear(&writer);
  }
  WebPPictureFree(&picture);
  return 0;
}

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
static int TimerAccountingCheck(const char* const input_path,
                                const char* const case_id, int method,
                                const char* const variant) {
  VP8LBackrefCostAlignedNullStageAttributionV3Stats observed;
  uint64_t selected;
  int result;
  VP8LBackrefCostAlignedNullStageAttributionV3StatsReset();
  result = Profile(input_path, case_id, method, variant, 0, 1);
  if (result != 0) return result;
  VP8LBackrefCostAlignedNullStageAttributionV3StatsGet(&observed);
  selected = observed.baseline_dp_calls + observed.layout_clone_dp_calls;
  if (selected == 0 || observed.selector_evaluations != selected ||
      observed.exact_activations != selected ||
      (strcmp(variant, "B") == 0 &&
      (observed.baseline_dp_calls != selected ||
        observed.layout_clone_dp_calls != 0)) ||
      (strcmp(variant, "L") == 0 &&
       (observed.layout_clone_dp_calls != selected ||
        observed.baseline_dp_calls != 0))) {
    return 61;
  }
  printf(
      "{\"schema\":\"libwebp-backref-cost-aligned-null-stage-attribution-v3-timer-accounting-output-v1\","
      "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
      "\"selector_evaluations\":%llu,\"baseline_dp_calls\":%llu,"
      "\"layout_clone_dp_calls\":%llu,"
      "\"selected_dp_calls\":%llu,\"exact_activations\":%llu,"
      "\"reset_scope\":\"one-encode\",\"per_pixel_clock_calls\":0}\n",
      case_id, method, variant,
      (unsigned long long)observed.selector_evaluations,
      (unsigned long long)observed.baseline_dp_calls,
      (unsigned long long)observed.layout_clone_dp_calls,
      (unsigned long long)selected,
      (unsigned long long)observed.exact_activations);
  return 0;
}
#endif

int main(int argc, char** argv) {
  if (!DirectChildAdmission()) return 60;
  if (argc == 2 && strcmp(argv[1], "guard") == 0) {
    // This command never reads an image or invokes WebPEncode.
    printf("{\"variant\":%d}\n",
           (int)VP8LBackrefCostAlignedNullStageAttributionV3GetVariant());
    return 0;
  }
  if (argc == 2 && strcmp(argv[1], "timer-check") == 0) {
    return TimerCheck();
  }
#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
  if (argc == 3 && strcmp(argv[1], "ledger-fixture") == 0) {
    return LedgerFixture(argv[2]);
  }
  if (argc == 6 && strcmp(argv[1], "work") == 0) {
    return WorkCheck(argv[2], argv[3], atoi(argv[4]), argv[5]);
  }
#endif
  if (argc == 6 && strcmp(argv[1], "correctness") == 0) {
    return Correctness(argv[2], atoi(argv[3]), argv[4], argv[5]);
  }
  if (argc == 8 && strcmp(argv[1], "profile") == 0) {
    return Profile(argv[2], argv[3], atoi(argv[4]), argv[5], atoi(argv[6]),
                   atoi(argv[7]));
  }
#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
  if (argc == 6 && strcmp(argv[1], "timer-accounting-check") == 0) {
    return TimerAccountingCheck(argv[2], argv[3], atoi(argv[4]), argv[5]);
  }
#endif
  fputs("invalid backref-cost specialization aligned null stage attribution v3 runner arguments\n", stderr);
  return 2;
}
