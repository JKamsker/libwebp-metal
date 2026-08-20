// Copyright 2026
//
// Private diagnostic runner for the backref-cost specialization alignment v1 pipeline.

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/backref_cost_specialization_alignment_v1_experiment_enc.h"
#include "src/enc/profile_enc.h"
#include "src/webp/decode.h"
#include "src/webp/encode.h"

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
      getenv("WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_VARIANT");
  return value != NULL && strcmp(value, variant) == 0 &&
         (strcmp(variant, "B") == 0 || strcmp(variant, "L") == 0 ||
          strcmp(variant, "H") == 0) &&
         VP8LBackrefCostSpecializationAlignmentV1GetVariant() !=
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

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_RECORDER)
static int WorkCheck(const char* const input_path, const char* const case_id,
                     int method, const char* const variant) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  VP8LBackrefCostSpecializationAlignmentV1Stats observed;
  uint64_t digest;
  uint64_t selected_dp_calls;

  if (!VariantMatchesEnvironment(variant)) return 40;
  VP8LBackrefCostSpecializationAlignmentV1StatsReset();
  if (!PreparePicture(input_path, method, &config, &picture)) {
    return 42;
  }
  if (!Encode(&config, &picture, &writer)) {
    WebPPictureFree(&picture);
    return 43;
  }
  WebPPictureFree(&picture);
  VP8LBackrefCostSpecializationAlignmentV1StatsGet(&observed);
  selected_dp_calls = observed.baseline_dp_calls + observed.layout_clone_dp_calls +
                      observed.hint_dp_calls;
  if (observed.selector_evaluations == 0 ||
      observed.selector_evaluations != selected_dp_calls ||
      observed.exact_activations != observed.selector_evaluations ||
      (strcmp(variant, "B") == 0 &&
       (observed.baseline_dp_calls != selected_dp_calls ||
        observed.layout_clone_dp_calls != 0 || observed.hint_dp_calls != 0)) ||
      (strcmp(variant, "L") == 0 &&
       (observed.layout_clone_dp_calls != selected_dp_calls ||
        observed.baseline_dp_calls != 0 || observed.hint_dp_calls != 0)) ||
      (strcmp(variant, "H") == 0 &&
       (observed.hint_dp_calls != selected_dp_calls ||
        observed.baseline_dp_calls != 0 || observed.layout_clone_dp_calls != 0))) {
    WebPMemoryWriterClear(&writer);
    return 44;
  }
  digest = Fnv1a64(writer.mem, writer.size);
  printf(
      "{\"schema\":\"libwebp-backref-cost-specialization-alignment-v1-work-v1\","
      "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
      "\"selector_evaluations\":%llu,\"baseline_dp_calls\":%llu,"
      "\"layout_clone_dp_calls\":%llu,\"hint_dp_calls\":%llu,"
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
      (unsigned long long)observed.hint_dp_calls,
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
  uint64_t first = WebPProfileClockNowForValidation();
  uint64_t previous = first;
  uint64_t minimum_delta = UINT64_MAX;
  uint64_t maximum_delta = 0;
  unsigned int positive_deltas = 0;
  unsigned int i;
  for (i = 1; i < reads; ++i) {
    const uint64_t current = WebPProfileClockNowForValidation();
    const uint64_t delta = current - previous;
    if (current < previous) return 50;
    if (delta > 0) {
      if (delta < minimum_delta) minimum_delta = delta;
      if (delta > maximum_delta) maximum_delta = delta;
      ++positive_deltas;
    }
    previous = current;
  }
  if (positive_deltas == 0 || previous <= first) return 51;
  printf(
      "{\"schema\":\"libwebp-backref-cost-specialization-alignment-v1-timer-check-v1\","
      "\"clock_reads\":%u,\"positive_deltas\":%u,"
      "\"elapsed_ns\":%llu,\"mean_read_delta_ns\":%llu,"
      "\"minimum_positive_delta_ns\":%llu,"
      "\"maximum_delta_ns\":%llu,\"monotonic\":true}\n",
      reads, positive_deltas, (unsigned long long)(previous - first),
      (unsigned long long)((previous - first) / (reads - 1)),
      (unsigned long long)minimum_delta, (unsigned long long)maximum_delta);
  return 0;
}

static int Profile(const char* const input_path, const char* const case_id,
                   int method, const char* const variant, int warmups,
                   int measured) {
  const char* const session = getenv("WEBP_BENCHMARK_SESSION");
  const char* const timers = getenv("WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_TIMERS");
  WebPConfig config;
  WebPPicture picture;
  int iteration;
  if (session == NULL || strcmp(session, "exclusive") != 0 || timers == NULL ||
      strcmp(timers, "1") != 0) {
    return 30;
  }
  if (!VariantMatchesEnvironment(variant) || warmups != 1 || measured != 4) {
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
        "{\"schema\":\"libwebp-backref-cost-specialization-alignment-v1-output-v1\","
        "\"case_id\":\"%s\",\"method\":%d,\"variant\":\"%s\","
        "\"iteration\":%d,\"sample_role\":\"%s\","
        "\"bitstream_bytes\":%llu,\"bitstream_fnv1a64\":\"%016llx\"}\n",
        case_id, method, variant, iteration,
        iteration < warmups ? "warmup" : "retained",
        (unsigned long long)writer.size, (unsigned long long)digest);
    WebPMemoryWriterClear(&writer);
  }
  WebPPictureFree(&picture);
  return 0;
}

int main(int argc, char** argv) {
  if (argc == 2 && strcmp(argv[1], "guard") == 0) {
    // This command never reads an image or invokes WebPEncode.
    printf("{\"variant\":%d}\n",
           (int)VP8LBackrefCostSpecializationAlignmentV1GetVariant());
    return 0;
  }
  if (argc == 2 && strcmp(argv[1], "timer-check") == 0) {
    return TimerCheck();
  }
#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V1_RECORDER)
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
  fputs("invalid backref-cost specialization alignment v1 runner arguments\n", stderr);
  return 2;
}
