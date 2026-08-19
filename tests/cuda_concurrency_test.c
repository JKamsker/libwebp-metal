// Copyright 2026
//
// Stress the serialized CUDA descriptor from independent public encoder calls.

#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <process.h>
#include <windows.h>
#else
#include <pthread.h>
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/enc/accelerator_enc.h"
#include "tools/benchmark_platform.h"
#include "webp/encode.h"

enum { kWidth = 257, kHeight = 259, kThreadCount = 4, kIterations = 3 };

typedef struct {
  const uint8_t* rgba;
  uint64_t expected_lossless;
  uint64_t expected_lossy;
  uint64_t actual_lossless;
  uint64_t actual_lossy;
  int lossless_ok;
  int lossy_ok;
  int failed_iteration;
  int ok;
} Worker;

#if defined(_WIN32)
typedef HANDLE BenchmarkThread;
#else
typedef pthread_t BenchmarkThread;
#endif

static uint64_t HashBytes(const uint8_t* data, size_t size) {
  uint64_t hash = UINT64_C(1469598103934665603);
  size_t i;
  for (i = 0; i < size; ++i) {
    hash = (hash ^ data[i]) * UINT64_C(1099511628211);
  }
  return hash;
}

static int Encode(const uint8_t* rgba, int lossless, uint64_t* hash) {
  WebPConfig config;
  WebPPicture picture;
  WebPMemoryWriter writer;
  int ok = 0;
  if (!WebPConfigInit(&config) || !WebPPictureInit(&picture)) return 0;
  config.lossless = lossless;
  config.exact = 1;
  config.method = 4;
  config.quality = 75.f;
  picture.width = kWidth;
  picture.height = kHeight;
  picture.use_argb = lossless;
  WebPMemoryWriterInit(&writer);
  picture.writer = WebPMemoryWrite;
  picture.custom_ptr = &writer;
  if (WebPPictureImportRGBA(&picture, rgba, kWidth * 4) &&
      WebPEncode(&config, &picture)) {
    *hash = HashBytes(writer.mem, writer.size);
    ok = 1;
  }
  WebPPictureFree(&picture);
  WebPMemoryWriterClear(&writer);
  return ok;
}

#if defined(_WIN32)
static unsigned __stdcall RunWorker(void* opaque) {
#else
static void* RunWorker(void* opaque) {
#endif
  Worker* const worker = (Worker*)opaque;
  int iteration;
  worker->ok = 1;
  worker->failed_iteration = -1;
  for (iteration = 0; iteration < kIterations; ++iteration) {
    uint64_t lossless = 0, lossy = 0;
    worker->lossless_ok = Encode(worker->rgba, 1, &lossless);
    worker->lossy_ok = Encode(worker->rgba, 0, &lossy);
    if (!worker->lossless_ok || !worker->lossy_ok ||
        lossless != worker->expected_lossless || lossy != worker->expected_lossy) {
      worker->actual_lossless = lossless;
      worker->actual_lossy = lossy;
      worker->failed_iteration = iteration;
      worker->ok = 0;
      break;
    }
  }
#if defined(_WIN32)
  return 0;
#else
  return NULL;
#endif
}

int main(void) {
  const size_t rgba_size = (size_t)kWidth * kHeight * 4u;
  uint8_t* const rgba = (uint8_t*)malloc(rgba_size);
  if (!WebPBenchmarkHasCUDADevice()) {
    free(rgba);
    return 77;
  }
  BenchmarkThread threads[kThreadCount];
  Worker workers[kThreadCount];
  uint64_t expected_lossless, expected_lossy;
  size_t i;
  int created = 0;
  if (rgba == NULL) return 2;
  for (i = 0; i < rgba_size; ++i) rgba[i] = (uint8_t)(i * 37u + i / 17u);
  for (i = 3; i < rgba_size; i += 4) rgba[i] = 255u;
  WebPBenchmarkSetEnvironment("WEBP_ACCELERATOR", "cuda");
  WebPBenchmarkSetEnvironment("WEBP_CUDA", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_DEVICE", "2147483647");
  if (WebPAcceleratorLossyAnalysisEnabled()) {
    fprintf(stderr, "lossy-analysis probe accepted an unavailable device\n");
    free(rgba);
    return 1;
  }
  WebPBenchmarkSetEnvironment("WEBP_CUDA_DEVICE", "0");
  if (!WebPAcceleratorLossyAnalysisEnabled()) {
    fprintf(stderr, "lossy-analysis probe rejected the available device\n");
    free(rgba);
    return 1;
  }
  WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS", "0");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_MIN_PIXELS", "0");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_PREDICTOR_MIN_PIXELS", "0");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_PREDICTOR", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_RESIDENT_LOSSLESS", "1");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_HASH_MIN_PIXELS", "0");
  WebPBenchmarkSetEnvironment("WEBP_CUDA_LOSSY_MIN_PIXELS", "0");
  if (!Encode(rgba, 1, &expected_lossless) ||
      !Encode(rgba, 0, &expected_lossy)) {
    free(rgba);
    return 1;
  }
  memset(workers, 0, sizeof(workers));
  for (i = 0; i < kThreadCount; ++i) {
    workers[i].rgba = rgba;
    workers[i].expected_lossless = expected_lossless;
    workers[i].expected_lossy = expected_lossy;
#if defined(_WIN32)
    threads[i] = (HANDLE)_beginthreadex(NULL, 0, RunWorker, &workers[i], 0,
                                         NULL);
    if (threads[i] == NULL) break;
#else
    if (pthread_create(&threads[i], NULL, RunWorker, &workers[i]) != 0) break;
#endif
    ++created;
  }
  for (i = 0; i < (size_t)created; ++i) {
#if defined(_WIN32)
    WaitForSingleObject(threads[i], INFINITE);
    CloseHandle(threads[i]);
#else
    pthread_join(threads[i], NULL);
#endif
  }
  for (i = 0; i < (size_t)created; ++i) {
    if (!workers[i].ok) break;
  }
  free(rgba);
  if (created != kThreadCount || i != (size_t)created) {
    if (i < (size_t)created) {
      fprintf(stderr,
              "concurrent CUDA encode mismatch: worker %zu iteration %d "
              "lossless=%d:%016llx/%016llx lossy=%d:%016llx/%016llx\n",
              i, workers[i].failed_iteration,
              workers[i].lossless_ok,
              (unsigned long long)workers[i].actual_lossless,
              (unsigned long long)workers[i].expected_lossless,
              workers[i].lossy_ok,
              (unsigned long long)workers[i].actual_lossy,
              (unsigned long long)workers[i].expected_lossy);
    } else {
      fprintf(stderr, "could only create %d CUDA test threads\n", created);
    }
    return 1;
  }
  puts("PASS: concurrent CUDA encoder calls are deterministic");
  return 0;
}
