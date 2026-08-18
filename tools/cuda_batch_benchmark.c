// Copyright 2026
//
// Internal persistent-process benchmark for compressed-image decode + encode
// batches. This is deliberately not installed with the public tools.

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "imageio/image_dec.h"
#include "imageio/imageio_util.h"
#include "webp/decode.h"
#include "webp/encode.h"

typedef enum { MODE_LOSSY, MODE_LOSSLESS, MODE_NEAR_LOSSLESS } EncodeMode;

typedef struct {
  const char* filename;
  const uint8_t* data;
  size_t data_size;
} Input;

typedef struct {
  const char* variant;
  const char* mode_name;
  EncodeMode mode;
  int batch_size;
  int method;
  int quality;
  int near_lossless;
  int warmups;
  int samples;
  int include_file_io;
  int force_cuda;
  int verify;
  int verify_only;
  Input* inputs;
  int input_count;
} Options;

static void Usage(const char* const program) {
  fprintf(stderr,
          "Usage: %s --variant cpu|cuda --mode lossy|lossless|near-lossless "
          "--batch-size N [--method 0..6] [--quality 0..100] "
          "[--near-lossless 0..100] [--warmups N] [--samples N] "
          "[--include-file-io] [--force-cuda] [--verify|--verify-only] "
          "INPUT [INPUT ...]\n",
          program);
}

static int ParseInt(const char* const text, int minimum, int maximum,
                    int* const value) {
  char* end = NULL;
  long parsed;
  errno = 0;
  parsed = strtol(text, &end, 10);
  if (errno != 0 || end == text || *end != '\0' || parsed < minimum ||
      parsed > maximum) {
    return 0;
  }
  *value = (int)parsed;
  return 1;
}

static int ParseOptions(int argc, const char* const argv[], Options* options) {
  int i;
  memset(options, 0, sizeof(*options));
  options->method = 4;
  options->quality = 75;
  options->near_lossless = 40;
  options->warmups = 1;
  options->samples = 7;
  options->inputs = (Input*)calloc((size_t)argc, sizeof(*options->inputs));
  if (options->inputs == NULL) return 0;
  for (i = 1; i < argc; ++i) {
    const char* const flag = argv[i];
    const char* value;
    if (!strcmp(flag, "--include-file-io")) {
      options->include_file_io = 1;
      continue;
    }
    if (!strcmp(flag, "--force-cuda")) {
      options->force_cuda = 1;
      continue;
    }
    if (!strcmp(flag, "--verify")) {
      options->verify = 1;
      continue;
    }
    if (!strcmp(flag, "--verify-only")) {
      options->verify = 1;
      options->verify_only = 1;
      continue;
    }
    if (flag[0] != '-') {
      options->inputs[options->input_count++].filename = flag;
      continue;
    }
    value = i + 1 < argc ? argv[++i] : NULL;
    if (value == NULL) return 0;
    if (!strcmp(flag, "--variant")) {
      if (strcmp(value, "cpu") && strcmp(value, "cuda")) return 0;
      options->variant = value;
    } else if (!strcmp(flag, "--mode")) {
      options->mode_name = value;
      if (!strcmp(value, "lossy"))
        options->mode = MODE_LOSSY;
      else if (!strcmp(value, "lossless"))
        options->mode = MODE_LOSSLESS;
      else if (!strcmp(value, "near-lossless"))
        options->mode = MODE_NEAR_LOSSLESS;
      else
        return 0;
    } else if (!strcmp(flag, "--batch-size")) {
      if (!ParseInt(value, 1, 1000000, &options->batch_size)) return 0;
    } else if (!strcmp(flag, "--method")) {
      if (!ParseInt(value, 0, 6, &options->method)) return 0;
    } else if (!strcmp(flag, "--quality")) {
      if (!ParseInt(value, 0, 100, &options->quality)) return 0;
    } else if (!strcmp(flag, "--near-lossless")) {
      if (!ParseInt(value, 0, 100, &options->near_lossless)) return 0;
    } else if (!strcmp(flag, "--warmups")) {
      if (!ParseInt(value, 0, 1000, &options->warmups)) return 0;
    } else if (!strcmp(flag, "--samples")) {
      if (!ParseInt(value, 1, 1000, &options->samples)) return 0;
    } else {
      return 0;
    }
  }
  return options->variant != NULL && options->mode_name != NULL &&
         options->batch_size > 0 && options->input_count > 0;
}

static uint64_t NowNanoseconds(void) {
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
}

static uint64_t HashBytes(uint64_t hash, const uint8_t* data, size_t size) {
  size_t i;
  for (i = 0; i < size; ++i) {
    hash = (hash ^ data[i]) * UINT64_C(1099511628211);
  }
  return hash;
}

static void ConfigureDispatch(const char* const variant, const int force_cuda) {
  const int cuda = !strcmp(variant, "cuda");
  setenv("WEBP_ACCELERATOR", cuda ? "cuda" : "none", 1);
  setenv("WEBP_CUDA", cuda ? "1" : "0", 1);
  setenv("WEBP_CUDA_COLOR", "1", 1);
  setenv("WEBP_CUDA_HASH", "1", 1);
  setenv("WEBP_CUDA_LOSSY", "1", 1);
  setenv("WEBP_CUDA_NEAR_LOSSLESS", "1", 1);
  if (force_cuda) {
    setenv("WEBP_CUDA_MIN_PIXELS", "0", 1);
    setenv("WEBP_CUDA_HASH_MIN_PIXELS", "0", 1);
    setenv("WEBP_CUDA_LOSSY_MIN_PIXELS", "0", 1);
    setenv("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS", "0", 1);
  } else {
    unsetenv("WEBP_CUDA_MIN_PIXELS");
    unsetenv("WEBP_CUDA_HASH_MIN_PIXELS");
    unsetenv("WEBP_CUDA_LOSSY_MIN_PIXELS");
    unsetenv("WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS");
  }
}

static int LoadInputs(Options* const options) {
  int i;
  for (i = 0; i < options->input_count; ++i) {
    Input* const input = &options->inputs[i];
    if (!ImgIoUtilReadFile(input->filename, &input->data, &input->data_size)) {
      fprintf(stderr, "failed to read %s\n", input->filename);
      return 0;
    }
    if (WebPGuessImageType(input->data, input->data_size) ==
        WEBP_UNSUPPORTED_FORMAT) {
      fprintf(stderr, "unsupported input format: %s (enabled: %s)\n",
              input->filename, WebPGetEnabledInputFileFormats());
      return 0;
    }
  }
  return 1;
}

static void FreeInputs(Options* const options) {
  int i;
  if (options->inputs == NULL) return;
  for (i = 0; i < options->input_count; ++i) {
    WebPFree((void*)options->inputs[i].data);
  }
  free(options->inputs);
  options->inputs = NULL;
}

static int InitConfig(const Options* const options, WebPConfig* const config) {
  if (!WebPConfigInit(config)) return 0;
  config->lossless = options->mode != MODE_LOSSY;
  config->exact = 1;
  config->method = options->method;
  config->quality = (float)options->quality;
  if (options->mode == MODE_NEAR_LOSSLESS) {
    config->near_lossless = options->near_lossless;
  }
  return WebPValidateConfig(config);
}

static int EncodeInput(const Options* const options, const Input* const input,
                       WebPMemoryWriter* const writer) {
  const uint8_t* data = input->data;
  size_t data_size = input->data_size;
  int owns_data = 0;
  WebPConfig config;
  WebPPicture picture;
  WebPImageReader reader;
  int ok = 0;
  if (options->include_file_io) {
    if (!ImgIoUtilReadFile(input->filename, &data, &data_size)) return 0;
    owns_data = 1;
  }
  if (!InitConfig(options, &config) || !WebPPictureInit(&picture)) goto end;
  picture.use_argb = config.lossless;
  reader = WebPGuessImageReader(data, data_size);
  if (!reader(data, data_size, &picture, 1, NULL)) {
    fprintf(stderr, "failed to decode %s (enabled: %s)\n", input->filename,
            WebPGetEnabledInputFileFormats());
    goto free_picture;
  }
  WebPMemoryWriterInit(writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = writer;
  if (!WebPEncode(&config, &picture)) {
    fprintf(stderr, "failed to encode %s: error %d\n", input->filename,
            picture.error_code);
    WebPMemoryWriterClear(writer);
    goto free_picture;
  }
  ok = 1;
free_picture:
  WebPPictureFree(&picture);
end:
  if (owns_data) WebPFree((void*)data);
  return ok;
}

static int DecodedOutputsEqual(const WebPMemoryWriter* const left,
                               const WebPMemoryWriter* const right) {
  int left_width, left_height, right_width, right_height;
  uint8_t* const left_rgba =
      WebPDecodeRGBA(left->mem, left->size, &left_width, &left_height);
  uint8_t* const right_rgba =
      WebPDecodeRGBA(right->mem, right->size, &right_width, &right_height);
  int equal = 0;
  if (left_rgba != NULL && right_rgba != NULL && left_width == right_width &&
      left_height == right_height) {
    const size_t size = (size_t)left_width * left_height * 4u;
    equal = !memcmp(left_rgba, right_rgba, size);
  }
  WebPFree(left_rgba);
  WebPFree(right_rgba);
  return equal;
}

static int Verify(const Options* const options) {
  int i;
  for (i = 0; i < options->input_count; ++i) {
    WebPMemoryWriter cpu, cuda;
    Options preflight = *options;
    preflight.include_file_io = 0;
    ConfigureDispatch("cpu", options->force_cuda);
    if (!EncodeInput(&preflight, &options->inputs[i], &cpu)) return 0;
    ConfigureDispatch("cuda", options->force_cuda);
    if (!EncodeInput(&preflight, &options->inputs[i], &cuda)) {
      WebPMemoryWriterClear(&cpu);
      return 0;
    }
    if (!DecodedOutputsEqual(&cpu, &cuda)) {
      fprintf(stderr, "CPU/CUDA decoded output mismatch for %s\n",
              options->inputs[i].filename);
      WebPMemoryWriterClear(&cpu);
      WebPMemoryWriterClear(&cuda);
      return 0;
    }
    WebPMemoryWriterClear(&cpu);
    WebPMemoryWriterClear(&cuda);
  }
  fprintf(stderr, "verified CPU/CUDA decoded parity for %d input(s)\n",
          options->input_count);
  return 1;
}

static int RunBatch(const Options* const options, uint64_t* const elapsed_ns,
                    uint64_t* const output_hash,
                    uint64_t* const output_bytes) {
  uint64_t begin, end;
  uint64_t hash = UINT64_C(1469598103934665603);
  uint64_t bytes = 0;
  int i;
  begin = NowNanoseconds();
  for (i = 0; i < options->batch_size; ++i) {
    const Input* const input = &options->inputs[i % options->input_count];
    WebPMemoryWriter writer;
    if (!EncodeInput(options, input, &writer)) return 0;
    hash = HashBytes(hash, writer.mem, writer.size);
    hash = HashBytes(hash, (const uint8_t*)&writer.size, sizeof(writer.size));
    bytes += writer.size;
    WebPMemoryWriterClear(&writer);
  }
  end = NowNanoseconds();
  if (begin == 0 || end < begin) return 0;
  *elapsed_ns = end - begin;
  *output_hash = hash;
  *output_bytes = bytes;
  return 1;
}

int main(int argc, const char* const argv[]) {
  Options options;
  uint64_t reference_hash = 0;
  int sequence;
  if (!ParseOptions(argc, argv, &options)) {
    Usage(argv[0]);
    FreeInputs(&options);
    return 2;
  }
  if (!LoadInputs(&options)) {
    FreeInputs(&options);
    return 2;
  }
  if (options.verify && !Verify(&options)) {
    FreeInputs(&options);
    return 1;
  }
  if (options.verify_only) {
    FreeInputs(&options);
    return 0;
  }
  ConfigureDispatch(options.variant, options.force_cuda);
  for (sequence = -options.warmups; sequence < options.samples; ++sequence) {
    uint64_t elapsed_ns, output_hash, output_bytes;
    if (!RunBatch(&options, &elapsed_ns, &output_hash, &output_bytes)) {
      fprintf(stderr, "batch failed at sequence %d\n", sequence);
      FreeInputs(&options);
      return 1;
    }
    if (sequence < 0) continue;
    if (sequence == 0) reference_hash = output_hash;
    if (output_hash != reference_hash) {
      fprintf(stderr, "non-deterministic output at sequence %d\n", sequence);
      FreeInputs(&options);
      return 1;
    }
    printf("{\"operation\":\"decode_encode_batch\","
           "\"variant\":\"%s\",\"mode\":\"%s\","
           "\"batch_size\":%d,\"input_count\":%d,"
           "\"include_file_io\":%s,\"force_cuda\":%s,"
           "\"method\":%d,\"quality\":%d,"
           "\"near_lossless\":%d,\"sequence\":%d,"
           "\"elapsed_ns\":%" PRIu64 ",\"ns_per_image\":%.3f,"
           "\"images_per_second\":%.6f,"
           "\"output_hash\":\"%016" PRIx64 "\","
           "\"output_bytes\":%" PRIu64 "}\n",
           options.variant, options.mode_name, options.batch_size,
           options.input_count, options.include_file_io ? "true" : "false",
           options.force_cuda ? "true" : "false",
           options.method, options.quality, options.near_lossless, sequence,
           elapsed_ns, (double)elapsed_ns / options.batch_size,
           1e9 * options.batch_size / elapsed_ns, output_hash, output_bytes);
  }
  FreeInputs(&options);
  return 0;
}
