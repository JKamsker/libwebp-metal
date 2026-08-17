// Copyright 2026
//
// Experimental same-process and batched Metal encoder harness. This is not a
// public libwebp API or an installed tool.

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "src/enc/metal_enc.h"
#include "src/webp/encode.h"

typedef enum Lifecycle { LIFECYCLE_COLD, LIFECYCLE_WARM } Lifecycle;
typedef enum Submission { SUBMISSION_SINGLE, SUBMISSION_BATCH } Submission;
typedef enum Stage { STAGE_IMPORT, STAGE_ENCODE } Stage;

typedef struct Options {
  int width;
  int height;
  int batch_size;
  int iterations;
  int quality;
  int method;
  int verify_only;
  Lifecycle lifecycle;
  Submission submission;
  Stage stage;
} Options;

typedef struct Workload {
  uint8_t* source;
  size_t source_size;
  WebPPicture* pictures;
  WebPAcceleratorRGBToYUVRequest* requests;
  int batch_size;
  WebPConfig config;
} Workload;

static void PrintUsage(const char* program) {
  fprintf(stderr,
          "Usage: %s [options]\n"
          "  --lifecycle=cold|warm  first-use or primed process state\n"
          "  --submission=single|batch\n"
          "  --stage=import|encode  time conversion only or full encode\n"
          "  --width=N --height=N --batch-size=N --iterations=N\n"
          "  --quality=N --method=N\n"
          "  --verify-only           compare CPU, single, and batch streams\n",
          program);
}

static int ParseInt(const char* text, int minimum, int maximum, int* value) {
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

static int ParseOptions(int argc, char** argv, Options* options) {
  int i;
  options->width = 640;
  options->height = 480;
  options->batch_size = 4;
  options->iterations = 1;
  options->quality = 75;
  options->method = 4;
  options->verify_only = 0;
  options->lifecycle = LIFECYCLE_COLD;
  options->submission = SUBMISSION_BATCH;
  options->stage = STAGE_IMPORT;

  for (i = 1; i < argc; ++i) {
    const char* const argument = argv[i];
    if (!strcmp(argument, "--help") || !strcmp(argument, "-h")) {
      PrintUsage(argv[0]);
      exit(0);
    } else if (!strcmp(argument, "--verify-only")) {
      options->verify_only = 1;
    } else if (!strncmp(argument, "--lifecycle=", 12)) {
      const char* const value = argument + 12;
      if (!strcmp(value, "cold")) {
        options->lifecycle = LIFECYCLE_COLD;
      } else if (!strcmp(value, "warm")) {
        options->lifecycle = LIFECYCLE_WARM;
      } else {
        return 0;
      }
    } else if (!strncmp(argument, "--submission=", 13)) {
      const char* const value = argument + 13;
      if (!strcmp(value, "single")) {
        options->submission = SUBMISSION_SINGLE;
      } else if (!strcmp(value, "batch")) {
        options->submission = SUBMISSION_BATCH;
      } else {
        return 0;
      }
    } else if (!strncmp(argument, "--stage=", 8)) {
      const char* const value = argument + 8;
      if (!strcmp(value, "import")) {
        options->stage = STAGE_IMPORT;
      } else if (!strcmp(value, "encode")) {
        options->stage = STAGE_ENCODE;
      } else {
        return 0;
      }
    } else if (!strncmp(argument, "--width=", 8)) {
      if (!ParseInt(argument + 8, 1, 16383, &options->width)) return 0;
    } else if (!strncmp(argument, "--height=", 9)) {
      if (!ParseInt(argument + 9, 1, 16383, &options->height)) return 0;
    } else if (!strncmp(argument, "--batch-size=", 13)) {
      if (!ParseInt(argument + 13, 1, 1024, &options->batch_size)) return 0;
    } else if (!strncmp(argument, "--iterations=", 13)) {
      if (!ParseInt(argument + 13, 1, 1000000, &options->iterations)) return 0;
    } else if (!strncmp(argument, "--quality=", 10)) {
      if (!ParseInt(argument + 10, 0, 100, &options->quality)) return 0;
    } else if (!strncmp(argument, "--method=", 9)) {
      if (!ParseInt(argument + 9, 0, 6, &options->method)) return 0;
    } else {
      return 0;
    }
  }
  if (!options->verify_only && options->lifecycle == LIFECYCLE_COLD &&
      options->iterations != 1) {
    fprintf(stderr,
            "cold measurements require --iterations=1; use new processes "
            "for independent cold samples\n");
    return 0;
  }
  return 1;
}

static uint8_t PatternByte(int x, int y, int channel, int image) {
  uint32_t value = (uint32_t)(x + 1) * 0x45d9f3bu;
  value ^= (uint32_t)(y + 7) * 0x119de1f3u;
  value ^= (uint32_t)(channel + 11) * 0x3449u;
  value ^= (uint32_t)(image + 17) * 0x27d4eb2du;
  value ^= value >> 16;
  return (uint8_t)value;
}

static int MonotonicNanoseconds(uint64_t* nanoseconds) {
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
  *nanoseconds = (uint64_t)now.tv_sec * UINT64_C(1000000000) +
                 (uint64_t)now.tv_nsec;
  return 1;
}

static void FreeWorkload(Workload* workload) {
  int i;
  if (workload->pictures != NULL) {
    for (i = 0; i < workload->batch_size; ++i) {
      WebPPictureFree(&workload->pictures[i]);
    }
  }
  free(workload->requests);
  free(workload->pictures);
  free(workload->source);
  memset(workload, 0, sizeof(*workload));
}

static int InitWorkload(const Options* options, Workload* workload) {
  size_t pixels;
  size_t bytes_per_image;
  size_t total_bytes;
  int i;
  int x;
  int y;
  memset(workload, 0, sizeof(*workload));
  workload->batch_size = options->batch_size;
  pixels = (size_t)options->width * (size_t)options->height;
  if (pixels > SIZE_MAX / 3u) return 0;
  bytes_per_image = pixels * 3u;
  if ((size_t)options->batch_size > SIZE_MAX / bytes_per_image) return 0;
  total_bytes = (size_t)options->batch_size * bytes_per_image;
  workload->source = (uint8_t*)malloc(total_bytes);
  workload->pictures =
      (WebPPicture*)calloc((size_t)options->batch_size, sizeof(WebPPicture));
  workload->requests = (WebPAcceleratorRGBToYUVRequest*)calloc(
      (size_t)options->batch_size,
      sizeof(WebPAcceleratorRGBToYUVRequest));
  if (workload->source == NULL || workload->pictures == NULL ||
      workload->requests == NULL ||
      !WebPConfigInit(&workload->config)) {
    FreeWorkload(workload);
    return 0;
  }
  workload->source_size = total_bytes;
  workload->config.quality = (float)options->quality;
  workload->config.method = options->method;

  for (i = 0; i < options->batch_size; ++i) {
    uint8_t* const source = workload->source + (size_t)i * bytes_per_image;
    WebPPicture* const picture = &workload->pictures[i];
    if (!WebPPictureInit(picture)) {
      FreeWorkload(workload);
      return 0;
    }
    picture->width = options->width;
    picture->height = options->height;
    picture->use_argb = 0;
    picture->colorspace = WEBP_YUV420;
    if (!WebPPictureAlloc(picture)) {
      FreeWorkload(workload);
      return 0;
    }
    for (y = 0; y < options->height; ++y) {
      for (x = 0; x < options->width; ++x) {
        int channel;
        for (channel = 0; channel < 3; ++channel) {
          source[((size_t)y * options->width + x) * 3u + channel] =
              PatternByte(x, y, channel, i);
        }
      }
    }
    workload->requests[i].red = source;
    workload->requests[i].green = source + 1;
    workload->requests[i].blue = source + 2;
    workload->requests[i].step = 3;
    workload->requests[i].source_stride = options->width * 3;
    workload->requests[i].width = picture->width;
    workload->requests[i].height = picture->height;
    workload->requests[i].y = picture->y;
    workload->requests[i].u = picture->u;
    workload->requests[i].v = picture->v;
    workload->requests[i].y_stride = picture->y_stride;
    workload->requests[i].uv_stride = picture->uv_stride;
  }
  return 1;
}

static int ImportWorkload(Workload* workload, Submission submission) {
  int i;
  if (submission == SUBMISSION_BATCH) {
    return WebPImportRGBToYUVAMetalBatch(workload->requests,
                                         (size_t)workload->batch_size);
  }
  for (i = 0; i < workload->batch_size; ++i) {
    const WebPAcceleratorRGBToYUVRequest* const request =
        &workload->requests[i];
    if (!WebPImportRGBToYUVAMetal(
            request->red, request->green, request->blue, request->step,
            request->source_stride, request->width, request->height,
            request->y, request->u, request->v, request->y_stride,
            request->uv_stride)) {
      return 0;
    }
  }
  return 1;
}

static int EncodePicture(const WebPConfig* config, WebPPicture* picture,
                         uint8_t** bytes, size_t* size) {
  WebPMemoryWriter writer;
  WebPMemoryWriterInit(&writer);
  picture->writer = WebPMemoryWrite;
  picture->custom_ptr = &writer;
  if (!WebPEncode(config, picture)) {
    WebPMemoryWriterClear(&writer);
    return 0;
  }
  *bytes = writer.mem;
  *size = writer.size;
  return 1;
}

static int RunWorkload(Workload* workload, const Options* options,
                       size_t* encoded_bytes) {
  int i;
  *encoded_bytes = 0;
  if (!ImportWorkload(workload, options->submission)) return 0;
  if (options->stage == STAGE_IMPORT) return 1;
  for (i = 0; i < workload->batch_size; ++i) {
    uint8_t* bytes = NULL;
    size_t size = 0;
    if (!EncodePicture(&workload->config, &workload->pictures[i], &bytes,
                       &size)) {
      return 0;
    }
    *encoded_bytes += size;
    WebPFree(bytes);
  }
  return 1;
}

static int EncodeCPUReference(const Options* options, const uint8_t* source,
                              uint8_t** bytes, size_t* size) {
  WebPPicture picture;
  WebPConfig config;
  int ok;
  if (!WebPPictureInit(&picture) || !WebPConfigInit(&config)) return 0;
  picture.width = options->width;
  picture.height = options->height;
  picture.use_argb = 0;
  config.quality = (float)options->quality;
  config.method = options->method;
  ok = WebPPictureImportRGB(&picture, source, options->width * 3) &&
       EncodePicture(&config, &picture, bytes, size);
  WebPPictureFree(&picture);
  return ok;
}

static int VerifyBatch(const Options* options, Workload* workload) {
  uint8_t** expected_bytes = NULL;
  size_t* expected_sizes = NULL;
  const size_t bytes_per_image =
      (size_t)options->width * (size_t)options->height * 3u;
  int i;
  int ok = 0;
  expected_bytes =
      (uint8_t**)calloc((size_t)options->batch_size, sizeof(uint8_t*));
  expected_sizes =
      (size_t*)calloc((size_t)options->batch_size, sizeof(size_t));
  if (expected_bytes == NULL || expected_sizes == NULL) goto End;

  setenv("WEBP_METAL_LOSSY", "0", 1);
  for (i = 0; i < options->batch_size; ++i) {
    if (!EncodeCPUReference(options,
                            workload->source + (size_t)i * bytes_per_image,
                            &expected_bytes[i], &expected_sizes[i])) {
      goto End;
    }
  }

  setenv("WEBP_METAL_LOSSY", "1", 1);
  setenv("WEBP_METAL_LOSSY_MIN_PIXELS", "0", 1);
  if (!WebPImportRGBToYUVAMetalBatch(workload->requests,
                                      (size_t)options->batch_size)) {
    goto End;
  }
  for (i = 0; i < options->batch_size; ++i) {
    uint8_t* actual_bytes = NULL;
    size_t actual_size = 0;
    if (!EncodePicture(&workload->config, &workload->pictures[i],
                       &actual_bytes, &actual_size) ||
        actual_size != expected_sizes[i] ||
        memcmp(actual_bytes, expected_bytes[i], actual_size) != 0) {
      WebPFree(actual_bytes);
      goto End;
    }
    WebPFree(actual_bytes);
  }

  // Exercise the unchanged single-image entry point after the batched call.
  if (!WebPImportRGBToYUVAMetal(
          workload->requests[0].red, workload->requests[0].green,
          workload->requests[0].blue, workload->requests[0].step,
          workload->requests[0].source_stride, workload->requests[0].width,
          workload->requests[0].height, workload->requests[0].y,
          workload->requests[0].u, workload->requests[0].v,
          workload->requests[0].y_stride,
          workload->requests[0].uv_stride)) {
    goto End;
  }
  {
    uint8_t* actual_bytes = NULL;
    size_t actual_size = 0;
    if (!EncodePicture(&workload->config, &workload->pictures[0],
                       &actual_bytes, &actual_size) ||
        actual_size != expected_sizes[0] ||
        memcmp(actual_bytes, expected_bytes[0], actual_size) != 0) {
      WebPFree(actual_bytes);
      goto End;
    }
    WebPFree(actual_bytes);
  }

  // A rejected batch must not partially update any caller-owned plane.
  {
    const size_t last = (size_t)options->batch_size - 1u;
    const int saved_step = workload->requests[last].step;
    workload->pictures[0].y[0] = 0x12;
    workload->pictures[0].u[0] = 0x34;
    workload->pictures[0].v[0] = 0x56;
    workload->requests[last].step = 2;
    if (WebPImportRGBToYUVAMetalBatch(workload->requests,
                                      (size_t)options->batch_size) ||
        workload->pictures[0].y[0] != 0x12 ||
        workload->pictures[0].u[0] != 0x34 ||
        workload->pictures[0].v[0] != 0x56) {
      workload->requests[last].step = saved_step;
      goto End;
    }
    workload->requests[last].step = saved_step;
  }
  ok = 1;

 End:
  if (expected_bytes != NULL) {
    for (i = 0; i < options->batch_size; ++i) WebPFree(expected_bytes[i]);
  }
  free(expected_sizes);
  free(expected_bytes);
  return ok;
}

int main(int argc, char** argv) {
  Options options;
  Workload workload;
  int iteration;
  if (!ParseOptions(argc, argv, &options)) {
    PrintUsage(argv[0]);
    return 2;
  }
  setenv("WEBP_METAL_BATCH_EXPERIMENT", "1", 1);
  if (!InitWorkload(&options, &workload)) {
    fprintf(stderr, "failed to allocate the experiment workload\n");
    return 1;
  }
  if (options.verify_only) {
    const int ok = VerifyBatch(&options, &workload);
    FreeWorkload(&workload);
    if (!ok) {
      fprintf(stderr, "Metal batch verification failed\n");
      return 1;
    }
    printf("PASS: Metal batch and single streams match CPU for %d images\n",
           options.batch_size);
    return 0;
  }

  if (getenv("WEBP_BENCHMARK_SESSION") == NULL ||
      strcmp(getenv("WEBP_BENCHMARK_SESSION"), "exclusive") != 0) {
    fprintf(stderr,
            "timed mode requires WEBP_BENCHMARK_SESSION=exclusive\n");
    FreeWorkload(&workload);
    return 2;
  }

  setenv("WEBP_METAL_LOSSY", "1", 1);
  setenv("WEBP_METAL_LOSSY_MIN_PIXELS", "0", 1);
  if (options.lifecycle == LIFECYCLE_WARM) {
    size_t ignored_bytes;
    if (!RunWorkload(&workload, &options, &ignored_bytes)) {
      fprintf(stderr, "Metal warm-up failed\n");
      FreeWorkload(&workload);
      return 1;
    }
  }
  for (iteration = 0; iteration < options.iterations; ++iteration) {
    uint64_t start;
    uint64_t end;
    size_t encoded_bytes;
    if (!MonotonicNanoseconds(&start) ||
        !RunWorkload(&workload, &options, &encoded_bytes) ||
        !MonotonicNanoseconds(&end)) {
      fprintf(stderr, "Metal experiment iteration failed\n");
      FreeWorkload(&workload);
      return 1;
    }
    printf("{\"schema\":\"libwebp-metal-persistent-batch-v1\","
           "\"lifecycle\":\"%s\",\"submission\":\"%s\","
           "\"stage\":\"%s\",\"width\":%d,\"height\":%d,"
           "\"batch_size\":%d,\"iteration\":%d,"
           "\"elapsed_ns\":%" PRIu64 ",\"ns_per_image\":%.3f,"
           "\"encoded_bytes\":%zu,\"metal_command_buffers\":%d,"
           "\"warmup_batches\":%d}\n",
           options.lifecycle == LIFECYCLE_COLD ? "cold" : "warm",
           options.submission == SUBMISSION_SINGLE ? "single" : "batch",
           options.stage == STAGE_IMPORT ? "import" : "encode",
           options.width, options.height, options.batch_size, iteration,
           end - start, (double)(end - start) / options.batch_size,
           encoded_bytes,
           options.submission == SUBMISSION_SINGLE ? options.batch_size : 1,
           options.lifecycle == LIFECYCLE_WARM ? 1 : 0);
    fflush(stdout);
  }
  FreeWorkload(&workload);
  return 0;
}
