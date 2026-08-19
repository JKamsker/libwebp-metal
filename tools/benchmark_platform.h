// Copyright 2026
//
// Small platform layer shared by the CUDA benchmark tools and their tests.

#ifndef WEBP_TOOLS_BENCHMARK_PLATFORM_H_
#define WEBP_TOOLS_BENCHMARK_PLATFORM_H_

#include <stdint.h>
#include <stdlib.h>

#if defined(WEBP_CUDA_TESTING)
#include <cuda_runtime_api.h>

static int WebPBenchmarkHasCUDADevice(void) {
  int count = 0;
  const cudaError_t error = cudaGetDeviceCount(&count);
  if (error != cudaSuccess) (void)cudaGetLastError();
  return error == cudaSuccess && count > 0;
}
#endif

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <time.h>
#endif

static int WebPBenchmarkSetEnvironment(const char* const name,
                                       const char* const value) {
#if defined(_WIN32)
  return _putenv_s(name, value) == 0;
#else
  return setenv(name, value, 1) == 0;
#endif
}

static int WebPBenchmarkUnsetEnvironment(const char* const name) {
#if defined(_WIN32)
  // _putenv_s removes the variable when it is assigned an empty value.
  return _putenv_s(name, "") == 0;
#else
  return unsetenv(name) == 0;
#endif
}

static uint64_t WebPBenchmarkNowNanoseconds(void) {
#if defined(_WIN32)
  LARGE_INTEGER frequency;
  LARGE_INTEGER counter;
  uint64_t ticks;
  uint64_t ticks_per_second;
  uint64_t whole_seconds;
  uint64_t remainder;
  if (!QueryPerformanceFrequency(&frequency) ||
      !QueryPerformanceCounter(&counter) || frequency.QuadPart <= 0 ||
      counter.QuadPart < 0) {
    return 0;
  }
  ticks = (uint64_t)counter.QuadPart;
  ticks_per_second = (uint64_t)frequency.QuadPart;
  whole_seconds = ticks / ticks_per_second;
  remainder = ticks % ticks_per_second;
  return whole_seconds * UINT64_C(1000000000) +
         remainder * UINT64_C(1000000000) / ticks_per_second;
#else
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
  return (uint64_t)now.tv_sec * UINT64_C(1000000000) +
         (uint64_t)now.tv_nsec;
#endif
}

#endif  // WEBP_TOOLS_BENCHMARK_PLATFORM_H_
