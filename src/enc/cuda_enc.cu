// Copyright 2026
//
// CUDA acceleration for the encoder's lossless cross-color, lossless
// hash-candidate, and opaque RGB-to-YUV stages. The adapter owns all runtime
// state behind the private accelerator ABI.

#include "src/enc/cuda_enc.h"

#include <cuda_runtime.h>

#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#define WEBP_CUDA_STRCASECMP _stricmp
typedef SRWLOCK CudaMutex;
#define WEBP_CUDA_MUTEX_INITIALIZER SRWLOCK_INIT
static void LockCudaMutex(CudaMutex* mutex) {
  AcquireSRWLockExclusive(mutex);
}
static void UnlockCudaMutex(CudaMutex* mutex) {
  ReleaseSRWLockExclusive(mutex);
}
#else
#include <pthread.h>
#include <strings.h>
#define WEBP_CUDA_STRCASECMP strcasecmp
typedef pthread_mutex_t CudaMutex;
#define WEBP_CUDA_MUTEX_INITIALIZER PTHREAD_MUTEX_INITIALIZER
static void LockCudaMutex(CudaMutex* mutex) {
  (void)pthread_mutex_lock(mutex);
}
static void UnlockCudaMutex(CudaMutex* mutex) {
  (void)pthread_mutex_unlock(mutex);
}
#endif

#include <algorithm>
#include <limits>

namespace {

#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM) || \
    defined(WEBP_CUDA_ENABLE_HASH_CHAIN) || \
    defined(WEBP_CUDA_ENABLE_RGB_TO_YUV) || \
    defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
#define WEBP_CUDA_HAS_ENCODER_STAGE 1
#endif

// The batch cutoffs conservatively amortize the measured cold runtime cost
// using the batch-6 PNG/JPEG crossover. Callers can recalibrate every value
// through the corresponding environment override.
#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM) || \
    defined(WEBP_CUDA_ENABLE_HASH_CHAIN)
constexpr size_t kDefaultLosslessBatchMinimumImages = 6u;
constexpr size_t kDefaultLosslessBatchMinimumPixels = 6u * 1000u * 1000u;
#endif
#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM)
constexpr size_t kDefaultColorColdMinimumPixels = 4u * 1000u * 1000u;
constexpr size_t kDefaultColorWarmMinimumPixels = 128u * 128u;
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
constexpr uint32_t kMaximumCachedColorTileSize = 64u;
#endif
#if defined(WEBP_CUDA_ENABLE_COLOR_256_THREAD_BLOCKS)
constexpr unsigned int kColorThreadsPerBlock = 256u;
#else
constexpr unsigned int kColorThreadsPerBlock = 128u;
#endif
#endif
#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
constexpr size_t kDefaultNearLosslessColdMinimumPixels = 4096u * 4096u;
constexpr size_t kDefaultNearLosslessWarmMinimumPixels = 256u * 256u;
constexpr size_t kDefaultNearLosslessBatchMinimumImages = 5u;
constexpr size_t kDefaultNearLosslessBatchMinimumPixels =
    5u * 1000u * 1000u;
#endif
#if defined(WEBP_CUDA_ENABLE_HASH_CHAIN)
constexpr size_t kDefaultHashColdMinimumPixels = 8u * 1000u * 1000u;
constexpr size_t kDefaultHashWarmMinimumPixels = 4u * 1000u * 1000u;
constexpr size_t kDefaultHashBatchMinimumPixels = 1u * 1000u * 1000u;
#if defined(WEBP_CUDA_ENABLE_HASH_256_THREAD_BLOCKS)
constexpr unsigned int kHashThreadsPerBlock = 256u;
#else
constexpr unsigned int kHashThreadsPerBlock = 128u;
#endif
#endif
#if defined(WEBP_CUDA_ENABLE_RGB_TO_YUV)
constexpr size_t kDefaultRGBColdMinimumPixels = 80u * 1000u * 1000u;
constexpr size_t kDefaultRGBWarmMinimumPixels = 4u * 1000u * 1000u;
#if defined(WEBP_CUDA_ENABLE_RGB_256_THREAD_BLOCKS)
constexpr unsigned int kRGBThreadsPerBlock = 256u;
#else
constexpr unsigned int kRGBThreadsPerBlock = 128u;
#endif
#endif
#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
constexpr size_t kMinimumAllocation = 16u * 1024u;
#endif

#if defined(WEBP_CUDA_ENABLE_RESTRICT_POINTERS)
#define WEBP_CUDA_RESTRICT __restrict__
#else
#define WEBP_CUDA_RESTRICT
#endif

struct KernelParams {
  uint32_t width;
  uint32_t height;
  uint32_t bits;
  uint32_t quality;
  uint32_t tile_columns;
};

struct HashKernelParams {
  uint32_t size;
  uint32_t xsize;
  uint32_t iter_max;
  uint32_t window_size;
  uint32_t low_effort;
};

struct RGBKernelParams {
  uint32_t width;
  uint32_t height;
  uint32_t step;
  uint32_t source_stride;
  uint32_t red_offset;
  uint32_t green_offset;
  uint32_t blue_offset;
  uint32_t uv_width;
  uint32_t y_size;
  uint32_t uv_size;
  uint32_t packed4;
};

struct CudaState {
  bool initialization_attempted = false;
  bool available = false;
  bool quarantined = false;
  int device = 0;
  cudaStream_t stream = nullptr;
  cudaEvent_t event_start = nullptr;
  cudaEvent_t event_stop = nullptr;
  uint32_t* pixels = nullptr;
  uint32_t* transform = nullptr;
  int32_t* chain = nullptr;
  size_t pixel_capacity = 0;
  size_t transform_capacity = 0;
  size_t chain_capacity = 0;
  uint32_t* host_pixels = nullptr;
  uint32_t* host_transform = nullptr;
  int32_t* host_chain = nullptr;
  size_t host_pixel_capacity = 0;
  size_t host_transform_capacity = 0;
  size_t host_chain_capacity = 0;
  bool gamma_initialized = false;
  uint32_t successful_stages = 0;
  char device_name[256] = {0};
};

CudaState g_cuda_state;
CudaMutex g_cuda_mutex = WEBP_CUDA_MUTEX_INITIALIZER;

bool EnvironmentFlag(const char* name, bool default_value) {
  const char* const value = getenv(name);
  if (value == nullptr || value[0] == '\0') return default_value;
  return strcmp(value, "0") != 0 &&
         WEBP_CUDA_STRCASECMP(value, "false") != 0 &&
         WEBP_CUDA_STRCASECMP(value, "no") != 0;
}

#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
bool ParseEnvironmentSize(const char* name, size_t* parsed_value) {
  const char* const value = getenv(name);
  char* end = nullptr;
  unsigned long long parsed;
  if (value == nullptr || value[0] == '\0' || value[0] == '-') return false;
  errno = 0;
  parsed = strtoull(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' ||
      parsed > std::numeric_limits<size_t>::max()) {
    return false;
  }
  *parsed_value = static_cast<size_t>(parsed);
  return true;
}

size_t EnvironmentSize(const char* name, size_t default_value) {
  size_t parsed;
  return ParseEnvironmentSize(name, &parsed) ? parsed : default_value;
}

#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM) || \
    defined(WEBP_CUDA_ENABLE_HASH_CHAIN) || \
    defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
bool HasProfitableBatchHint(size_t minimum_images, size_t minimum_pixels) {
  size_t images;
  size_t pixels;
  return ParseEnvironmentSize("WEBP_CUDA_BATCH_SIZE", &images) &&
         ParseEnvironmentSize("WEBP_CUDA_BATCH_PIXELS", &pixels) &&
         images >= minimum_images && pixels >= minimum_pixels;
}
#endif

#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM) || \
    defined(WEBP_CUDA_ENABLE_HASH_CHAIN)
bool HasProfitableLosslessBatchHint(void) {
  return HasProfitableBatchHint(
      EnvironmentSize("WEBP_CUDA_BATCH_MIN_IMAGES",
                      kDefaultLosslessBatchMinimumImages),
      EnvironmentSize("WEBP_CUDA_BATCH_MIN_PIXELS",
                      kDefaultLosslessBatchMinimumPixels));
}
#endif

#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
bool HasProfitableNearLosslessBatchHint(void) {
  return HasProfitableBatchHint(
      EnvironmentSize("WEBP_CUDA_NEAR_LOSSLESS_BATCH_MIN_IMAGES",
                      kDefaultNearLosslessBatchMinimumImages),
      EnvironmentSize("WEBP_CUDA_NEAR_LOSSLESS_BATCH_MIN_PIXELS",
                      kDefaultNearLosslessBatchMinimumPixels));
}
#endif
#endif  // WEBP_CUDA_HAS_ENCODER_STAGE

#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
int EnvironmentDevice(void) {
  const char* const value = getenv("WEBP_CUDA_DEVICE");
  char* end = nullptr;
  long parsed;
  if (value == nullptr || value[0] == '\0') return 0;
  errno = 0;
  parsed = strtol(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0' || parsed < 0 ||
      parsed > std::numeric_limits<int>::max()) {
    return -1;
  }
  return static_cast<int>(parsed);
}
#endif  // WEBP_CUDA_HAS_ENCODER_STAGE

#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM)

__device__ __constant__ int kColorAxes[8][2] = {
    {0, -1}, {0, 1}, {-1, 0}, {1, 0},
    {-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
__device__ __constant__ int kColorDeltas[7] = {16, 16, 8, 4, 2, 2, 2};

__device__ __forceinline__ int SignedByte(int value) {
  const int byte_value = value & 255;
  return byte_value >= 128 ? byte_value - 256 : byte_value;
}

__device__ __forceinline__ int ColorDelta(int predictor, int color) {
  return (SignedByte(predictor) * SignedByte(color)) >> 5;
}

__device__ __forceinline__ uint32_t TransformedRed(uint32_t pixel,
                                                    int green_to_red) {
  const int green = static_cast<int>((pixel >> 8) & 255u);
  const int red = static_cast<int>((pixel >> 16) & 255u);
  return static_cast<uint32_t>(red - ColorDelta(green_to_red, green)) & 255u;
}

__device__ __forceinline__ uint32_t TransformedBlue(uint32_t pixel,
                                                     int green_to_blue,
                                                     int red_to_blue) {
  const int green = static_cast<int>((pixel >> 8) & 255u);
  const int red = static_cast<int>((pixel >> 16) & 255u);
  const int blue = static_cast<int>(pixel & 255u);
  return static_cast<uint32_t>(blue - ColorDelta(green_to_blue, green) -
                               ColorDelta(red_to_blue, red)) &
         255u;
}

__device__ __forceinline__ float SLog2(uint32_t value) {
  return value == 0u ? 0.0f : static_cast<float>(value) * log2f(value);
}

__device__ float ScoreHistogram(unsigned int* histogram, float* result) {
  __syncthreads();
  if (threadIdx.x == 0u) {
    uint32_t sum = 0u;
    float sum_slog = 0.0f;
    for (uint32_t i = 0u; i < 256u; ++i) {
      const uint32_t count = histogram[i];
      sum += count;
      sum_slog += SLog2(count);
    }
    const float entropy = 2.0f * (SLog2(sum) - sum_slog);
    float spatial = 3.0f * static_cast<float>(histogram[0]);
    float weight = 2.4f;
    for (uint32_t i = 1u; i < 16u; ++i) {
      spatial += weight *
                 static_cast<float>(histogram[i] + histogram[256u - i]);
      weight *= 0.6f;
    }
    *result = entropy - 0.1f * spatial;
  }
  __syncthreads();
  return *result;
}

__device__ void ClearHistogram(unsigned int* histogram) {
  for (uint32_t i = threadIdx.x; i < 256u; i += blockDim.x) histogram[i] = 0u;
  __syncthreads();
}

__device__ __forceinline__ uint32_t LoadColorPixel(
    const uint32_t* pixels, const uint32_t* tile_pixels, KernelParams params,
    uint32_t tile_x, uint32_t tile_y, uint32_t tile_width, uint32_t i) {
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
  (void)pixels;
  (void)params;
  (void)tile_x;
  (void)tile_y;
  (void)tile_width;
  return tile_pixels[i];
#else
  (void)tile_pixels;
  const uint32_t x = tile_x + i % tile_width;
  const uint32_t y = tile_y + i / tile_width;
  return pixels[y * params.width + x];
#endif
}

__device__ float EvaluateRed(const uint32_t* pixels,
                             const uint32_t* tile_pixels, KernelParams params,
                             uint32_t tile_x, uint32_t tile_y,
                             uint32_t tile_width, uint32_t tile_height,
                             int green_to_red, unsigned int* histogram,
                             float* histogram_score) {
  ClearHistogram(histogram);
  const uint32_t count = tile_width * tile_height;
  for (uint32_t i = threadIdx.x; i < count; i += blockDim.x) {
    const uint32_t pixel = LoadColorPixel(pixels, tile_pixels, params, tile_x,
                                          tile_y, tile_width, i);
    atomicAdd(histogram + TransformedRed(pixel, green_to_red),
              1u);
  }
  return ScoreHistogram(histogram, histogram_score);
}

__device__ float EvaluateBlue(const uint32_t* pixels,
                              const uint32_t* tile_pixels,
                              KernelParams params,
                              uint32_t tile_x, uint32_t tile_y,
                              uint32_t tile_width, uint32_t tile_height,
                              int green_to_blue, int red_to_blue,
                              unsigned int* histogram,
                              float* histogram_score) {
  ClearHistogram(histogram);
  const uint32_t count = tile_width * tile_height;
  for (uint32_t i = threadIdx.x; i < count; i += blockDim.x) {
    const uint32_t pixel = LoadColorPixel(pixels, tile_pixels, params, tile_x,
                                          tile_y, tile_width, i);
    atomicAdd(histogram +
                  TransformedBlue(pixel, green_to_blue, red_to_blue),
              1u);
  }
  return ScoreHistogram(histogram, histogram_score);
}

__global__ void ColorSpaceTransformKernel(
    uint32_t* WEBP_CUDA_RESTRICT pixels,
    uint32_t* WEBP_CUDA_RESTRICT transform_image,
                                          KernelParams params) {
  const uint32_t tile_column = blockIdx.x;
  const uint32_t tile_row = blockIdx.y;
  const uint32_t group_index = tile_row * params.tile_columns + tile_column;
  const uint32_t tile_size = 1u << params.bits;
  const uint32_t tile_x = tile_column * tile_size;
  const uint32_t tile_y = tile_row * tile_size;
  const uint32_t remaining_width = params.width - tile_x;
  const uint32_t remaining_height = params.height - tile_y;
  const uint32_t tile_width =
      tile_size < remaining_width ? tile_size : remaining_width;
  const uint32_t tile_height =
      tile_size < remaining_height ? tile_size : remaining_height;

  __shared__ unsigned int histogram[256];
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
  extern __shared__ uint32_t tile_pixels[];
#else
  const uint32_t* const tile_pixels = nullptr;
#endif
  __shared__ int best_red;
  __shared__ int best_green_blue;
  __shared__ int best_red_blue;
  __shared__ float best_score;
  __shared__ float histogram_score;

  const uint32_t count = tile_width * tile_height;
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
  for (uint32_t i = threadIdx.x; i < count; i += blockDim.x) {
    const uint32_t local_x = i % tile_width;
    const uint32_t local_y = i / tile_width;
    tile_pixels[i] =
        pixels[(tile_y + local_y) * params.width + tile_x + local_x];
  }
#endif
  if (threadIdx.x == 0u) {
    best_red = 0;
    best_green_blue = 0;
    best_red_blue = 0;
  }
  __syncthreads();

  float score = EvaluateRed(pixels, tile_pixels, params, tile_x, tile_y,
                            tile_width, tile_height, 0, histogram,
                            &histogram_score);
  if (threadIdx.x == 0u) best_score = score - 9.0f;
  __syncthreads();

  const int red_iterations = 4 + static_cast<int>((7u * params.quality) >> 8);
  for (int iteration = 0; iteration < red_iterations; ++iteration) {
    const int delta = 32 >> iteration;
    for (int sign = -1; sign <= 1; sign += 2) {
      const int candidate = best_red + sign * delta;
      score = EvaluateRed(pixels, tile_pixels, params, tile_x, tile_y,
                          tile_width, tile_height, candidate, histogram,
                          &histogram_score);
      if (threadIdx.x == 0u) {
        if ((candidate & 255) == 0) score -= 6.0f;
        if (candidate == 0) score -= 3.0f;
        if (score < best_score) {
          best_score = score;
          best_red = candidate;
        }
      }
      __syncthreads();
    }
  }

  score = EvaluateBlue(pixels, tile_pixels, params, tile_x, tile_y, tile_width,
                       tile_height, 0, 0, histogram, &histogram_score);
  if (threadIdx.x == 0u) best_score = score - 18.0f;
  __syncthreads();

  const int blue_iterations =
      params.quality < 25u ? 1 : params.quality > 50u ? 7 : 4;
  for (int iteration = 0; iteration < blue_iterations; ++iteration) {
    for (int axis = 0; axis < 8; ++axis) {
      const int candidate_green =
          best_green_blue + kColorAxes[axis][0] * kColorDeltas[iteration];
      const int candidate_red =
          best_red_blue + kColorAxes[axis][1] * kColorDeltas[iteration];
      score = EvaluateBlue(pixels, tile_pixels, params, tile_x, tile_y,
                           tile_width, tile_height, candidate_green,
                           candidate_red, histogram, &histogram_score);
      if (threadIdx.x == 0u) {
        if ((candidate_green & 255) == 0) score -= 6.0f;
        if ((candidate_red & 255) == 0) score -= 6.0f;
        if (candidate_green == 0) score -= 3.0f;
        if (candidate_red == 0) score -= 3.0f;
        if (score < best_score) {
          best_score = score;
          best_green_blue = candidate_green;
          best_red_blue = candidate_red;
        }
      }
      __syncthreads();
    }
    if (kColorDeltas[iteration] == 2 && best_green_blue == 0 &&
        best_red_blue == 0) {
      break;
    }
  }

  if (threadIdx.x == 0u) {
    transform_image[group_index] =
        0xff000000u |
        ((static_cast<uint32_t>(best_red_blue) & 255u) << 16) |
        ((static_cast<uint32_t>(best_green_blue) & 255u) << 8) |
        (static_cast<uint32_t>(best_red) & 255u);
  }

  for (uint32_t i = threadIdx.x; i < count; i += blockDim.x) {
    const uint32_t local_x = i % tile_width;
    const uint32_t local_y = i / tile_width;
    const uint32_t index =
        (tile_y + local_y) * params.width + tile_x + local_x;
    const uint32_t pixel = LoadColorPixel(pixels, tile_pixels, params, tile_x,
                                          tile_y, tile_width, i);
    const uint32_t new_red = TransformedRed(pixel, best_red);
    const uint32_t new_blue =
        TransformedBlue(pixel, best_green_blue, best_red_blue);
    pixels[index] = (pixel & 0xff00ff00u) | (new_red << 16) | new_blue;
  }
}

#endif  // WEBP_CUDA_ENABLE_COLOR_TRANSFORM

#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)

__device__ __forceinline__ uint32_t ClosestNearLosslessValue(uint32_t value,
                                                             int bits) {
  const uint32_t mask = (1u << bits) - 1u;
  const uint32_t biased = value + (mask >> 1) + ((value >> bits) & 1u);
  return biased > 255u ? 255u : biased & ~mask;
}

__device__ __forceinline__ bool NearLosslessPixelsAreNear(uint32_t a,
                                                           uint32_t b,
                                                           int limit) {
  for (int shift = 0; shift < 32; shift += 8) {
    const int delta = static_cast<int>((a >> shift) & 255u) -
                      static_cast<int>((b >> shift) & 255u);
    if (delta >= limit || delta <= -limit) return false;
  }
  return true;
}

__device__ __forceinline__ uint32_t QuantizeNearLosslessPixel(uint32_t pixel,
                                                              int bits) {
  return (ClosestNearLosslessValue(pixel >> 24, bits) << 24) |
         (ClosestNearLosslessValue((pixel >> 16) & 255u, bits) << 16) |
         (ClosestNearLosslessValue((pixel >> 8) & 255u, bits) << 8) |
         ClosestNearLosslessValue(pixel & 255u, bits);
}

__global__ void NearLosslessKernel(
    const uint32_t* WEBP_CUDA_RESTRICT source,
    uint32_t* WEBP_CUDA_RESTRICT output, uint32_t width, uint32_t height,
    int limit_bits) {
  const uint32_t x = blockIdx.x * blockDim.x + threadIdx.x;
  const uint32_t y = blockIdx.y * blockDim.y + threadIdx.y;
  if (x >= width || y >= height) return;
  const uint32_t index = y * width + x;
  const uint32_t pixel = source[index];
  if (x == 0u || y == 0u || x + 1u == width || y + 1u == height) {
    output[index] = pixel;
    return;
  }
  const int limit = 1 << limit_bits;
  const bool smooth =
      NearLosslessPixelsAreNear(pixel, source[index - 1u], limit) &&
      NearLosslessPixelsAreNear(pixel, source[index + 1u], limit) &&
      NearLosslessPixelsAreNear(pixel, source[index - width], limit) &&
      NearLosslessPixelsAreNear(pixel, source[index + width], limit);
  output[index] =
      smooth ? pixel : QuantizeNearLosslessPixel(pixel, limit_bits);
}

#endif  // WEBP_CUDA_ENABLE_NEAR_LOSSLESS

#if defined(WEBP_CUDA_ENABLE_HASH_CHAIN)

__device__ __forceinline__ uint32_t ReadHashPixel(const uint32_t* pixels,
                                                   uint32_t index) {
#if defined(WEBP_CUDA_ENABLE_READ_ONLY_CACHE)
  return __ldg(pixels + index);
#else
  return pixels[index];
#endif
}

__device__ __forceinline__ int32_t ReadHashLink(const int32_t* chain,
                                                uint32_t index) {
#if defined(WEBP_CUDA_ENABLE_READ_ONLY_CACHE)
  return __ldg(chain + index);
#else
  return chain[index];
#endif
}

__device__ uint32_t HashMatchLength(const uint32_t* pixels, uint32_t first,
                                    uint32_t second, uint32_t best_length,
                                    uint32_t max_length) {
  uint32_t length = 0u;
  if (ReadHashPixel(pixels, first + best_length) !=
      ReadHashPixel(pixels, second + best_length)) {
    return 0u;
  }
#if defined(WEBP_CUDA_ENABLE_HASH_MATCH4)
  while (length + 4u <= max_length) {
    if (ReadHashPixel(pixels, first + length) !=
        ReadHashPixel(pixels, second + length)) {
      return length;
    }
    if (ReadHashPixel(pixels, first + length + 1u) !=
        ReadHashPixel(pixels, second + length + 1u)) {
      return length + 1u;
    }
    if (ReadHashPixel(pixels, first + length + 2u) !=
        ReadHashPixel(pixels, second + length + 2u)) {
      return length + 2u;
    }
    if (ReadHashPixel(pixels, first + length + 3u) !=
        ReadHashPixel(pixels, second + length + 3u)) {
      return length + 3u;
    }
    length += 4u;
  }
#endif
  while (length < max_length &&
         ReadHashPixel(pixels, first + length) ==
             ReadHashPixel(pixels, second + length)) {
    ++length;
  }
  return length;
}

__global__ void HashChainCandidatesKernel(
    const uint32_t* WEBP_CUDA_RESTRICT pixels,
    const int32_t* WEBP_CUDA_RESTRICT chain,
    uint32_t* WEBP_CUDA_RESTRICT candidates,
                                          HashKernelParams params) {
  const uint32_t base_position = blockIdx.x * blockDim.x + threadIdx.x;
  if (base_position >= params.size) return;
  if (base_position == 0u || base_position + 1u >= params.size) {
    candidates[base_position] = 0u;
    return;
  }

  const uint32_t remaining = params.size - 1u - base_position;
  const uint32_t max_length = remaining < 4095u ? remaining : 4095u;
  const uint32_t minimum_position =
      base_position > params.window_size ? base_position - params.window_size
                                         : 0u;
  const uint32_t good_length = max_length < 256u ? max_length : 256u;
  uint32_t best_length = 0u;
  uint32_t best_distance = 0u;
  int iterations = static_cast<int>(params.iter_max);
  int position = ReadHashLink(chain, base_position);

  if (params.low_effort == 0u) {
    if (base_position >= params.xsize) {
      const uint32_t current =
          HashMatchLength(pixels, base_position - params.xsize, base_position,
                          best_length, max_length);
      if (current > best_length) {
        best_length = current;
        best_distance = params.xsize;
      }
      --iterations;
    }
    const uint32_t current =
        HashMatchLength(pixels, base_position - 1u, base_position, best_length,
                        max_length);
    if (current > best_length) {
      best_length = current;
      best_distance = 1u;
    }
    --iterations;
    if (best_length == 4095u) {
      position = static_cast<int>(minimum_position) - 1;
    }
  }

  uint32_t best_pixel = ReadHashPixel(pixels, base_position + best_length);
  while (position >= static_cast<int>(minimum_position)) {
    --iterations;
    if (iterations == 0) break;
    if (ReadHashPixel(pixels, static_cast<uint32_t>(position) + best_length) ==
        best_pixel) {
      const uint32_t current =
          HashMatchLength(pixels, static_cast<uint32_t>(position),
                          base_position, 0u, max_length);
      if (current > best_length) {
        best_length = current;
        best_distance = base_position - static_cast<uint32_t>(position);
        best_pixel = ReadHashPixel(pixels, base_position + best_length);
        if (best_length >= good_length) break;
      }
    }
    position = ReadHashLink(chain, static_cast<uint32_t>(position));
  }
  candidates[base_position] = (best_distance << 12) | best_length;
}

#endif  // WEBP_CUDA_ENABLE_HASH_CHAIN

#if defined(WEBP_CUDA_ENABLE_RGB_TO_YUV)

__device__ __constant__ uint16_t kGammaToLinear[256];
__device__ __constant__ int32_t kLinearToGamma[33];

__device__ __forceinline__ uint8_t RGBToY(int red, int green, int blue) {
  const int luma = 16839 * red + 33059 * green + 6420 * blue;
  return static_cast<uint8_t>((luma + 32768 + (16 << 16)) >> 16);
}

__device__ __forceinline__ uint8_t ClipUV(int value) {
  value = (value + (32768 << 2) + (128 << 18)) >> 18;
  value = value < 0 ? 0 : value > 255 ? 255 : value;
  return static_cast<uint8_t>(value);
}

__device__ __forceinline__ uint8_t RGBToU(int red, int green, int blue) {
  return ClipUV(-9719 * red - 19081 * green + 28800 * blue);
}

__device__ __forceinline__ uint8_t RGBToV(int red, int green, int blue) {
  return ClipUV(28800 * red - 24116 * green - 4684 * blue);
}

__device__ __forceinline__ int InterpolateGamma(uint32_t value) {
  const uint32_t table_position = value >> 9;
  const uint32_t fraction = value & 511u;
  const int v0 = kLinearToGamma[table_position];
  const int v1 = kLinearToGamma[table_position + 1u];
  return (v1 * static_cast<int>(fraction) +
          v0 * static_cast<int>(512u - fraction) + 64) >>
         7;
}

__device__ __forceinline__ void LoadRGB(const uint8_t* source,
                                        uint32_t offset,
                                        RGBKernelParams params, int* red,
                                        int* green, int* blue) {
#if defined(WEBP_CUDA_ENABLE_RGB_PACKED4_LOADS)
  if (params.packed4 != 0u) {
    const uint32_t packed =
        *reinterpret_cast<const uint32_t*>(source + offset);
    *red = static_cast<int>((packed >> (params.red_offset * 8u)) & 255u);
    *green = static_cast<int>((packed >> (params.green_offset * 8u)) & 255u);
    *blue = static_cast<int>((packed >> (params.blue_offset * 8u)) & 255u);
    return;
  }
#endif
  *red = source[offset + params.red_offset];
  *green = source[offset + params.green_offset];
  *blue = source[offset + params.blue_offset];
}

__global__ void RGBToYUV420Kernel(
    const uint8_t* WEBP_CUDA_RESTRICT source,
    uint8_t* WEBP_CUDA_RESTRICT output,
                                  RGBKernelParams params) {
#if defined(WEBP_CUDA_ENABLE_RGB_BLOCK_2X2)
  const uint32_t uv_index = blockIdx.x * blockDim.x + threadIdx.x;
  const uint32_t uv_height = (params.height + 1u) >> 1;
  const uint32_t uv_count = params.uv_width * uv_height;
  if (uv_index >= uv_count) return;
  const uint32_t uv_x = uv_index % params.uv_width;
  const uint32_t uv_y = uv_index / params.uv_width;
  const uint32_t x0 = uv_x << 1;
  const uint32_t y0 = uv_y << 1;
  const uint32_t x1 = x0 + 1u < params.width ? x0 + 1u : x0;
  const uint32_t y1 = y0 + 1u < params.height ? y0 + 1u : y0;
  const uint32_t p00 = y0 * params.source_stride + x0 * params.step;
  const uint32_t p01 = y0 * params.source_stride + x1 * params.step;
  const uint32_t p10 = y1 * params.source_stride + x0 * params.step;
  const uint32_t p11 = y1 * params.source_stride + x1 * params.step;

  int r00, g00, b00, r01, g01, b01, r10, g10, b10, r11, g11, b11;
  LoadRGB(source, p00, params, &r00, &g00, &b00);
  LoadRGB(source, p01, params, &r01, &g01, &b01);
  LoadRGB(source, p10, params, &r10, &g10, &b10);
  LoadRGB(source, p11, params, &r11, &g11, &b11);

  output[y0 * params.width + x0] = RGBToY(r00, g00, b00);
  if (x1 != x0) output[y0 * params.width + x1] = RGBToY(r01, g01, b01);
  if (y1 != y0) {
    output[y1 * params.width + x0] = RGBToY(r10, g10, b10);
    if (x1 != x0) output[y1 * params.width + x1] = RGBToY(r11, g11, b11);
  }

  const uint32_t red_linear = kGammaToLinear[r00] + kGammaToLinear[r01] +
                              kGammaToLinear[r10] + kGammaToLinear[r11];
  const uint32_t green_linear =
      kGammaToLinear[g00] + kGammaToLinear[g01] + kGammaToLinear[g10] +
      kGammaToLinear[g11];
  const uint32_t blue_linear = kGammaToLinear[b00] + kGammaToLinear[b01] +
                               kGammaToLinear[b10] + kGammaToLinear[b11];
  const int red = InterpolateGamma(red_linear);
  const int green = InterpolateGamma(green_linear);
  const int blue = InterpolateGamma(blue_linear);
  output[params.y_size + uv_index] = RGBToU(red, green, blue);
  output[params.y_size + params.uv_size + uv_index] =
      RGBToV(red, green, blue);
#else
  const uint32_t index = blockIdx.x * blockDim.x + threadIdx.x;
  const uint32_t pixel_count = params.width * params.height;
  if (index < pixel_count) {
    const uint32_t x = index % params.width;
    const uint32_t y = index / params.width;
    const uint32_t offset = y * params.source_stride + x * params.step;
    int red, green, blue;
    LoadRGB(source, offset, params, &red, &green, &blue);
    output[index] = RGBToY(red, green, blue);
  }
  const uint32_t uv_height = (params.height + 1u) >> 1;
  const uint32_t uv_count = params.uv_width * uv_height;
  if (index < uv_count) {
    const uint32_t uv_x = index % params.uv_width;
    const uint32_t uv_y = index / params.uv_width;
    const uint32_t x0 = uv_x << 1;
    const uint32_t y0 = uv_y << 1;
    const uint32_t x1 = x0 + 1u < params.width ? x0 + 1u : x0;
    const uint32_t y1 = y0 + 1u < params.height ? y0 + 1u : y0;
    const uint32_t p00 = y0 * params.source_stride + x0 * params.step;
    const uint32_t p01 = y0 * params.source_stride + x1 * params.step;
    const uint32_t p10 = y1 * params.source_stride + x0 * params.step;
    const uint32_t p11 = y1 * params.source_stride + x1 * params.step;
    int r00, g00, b00, r01, g01, b01, r10, g10, b10, r11, g11, b11;
    LoadRGB(source, p00, params, &r00, &g00, &b00);
    LoadRGB(source, p01, params, &r01, &g01, &b01);
    LoadRGB(source, p10, params, &r10, &g10, &b10);
    LoadRGB(source, p11, params, &r11, &g11, &b11);
    const uint32_t red_linear = kGammaToLinear[r00] + kGammaToLinear[r01] +
                                kGammaToLinear[r10] + kGammaToLinear[r11];
    const uint32_t green_linear =
        kGammaToLinear[g00] + kGammaToLinear[g01] + kGammaToLinear[g10] +
        kGammaToLinear[g11];
    const uint32_t blue_linear = kGammaToLinear[b00] + kGammaToLinear[b01] +
                                 kGammaToLinear[b10] + kGammaToLinear[b11];
    const int red = InterpolateGamma(red_linear);
    const int green = InterpolateGamma(green_linear);
    const int blue = InterpolateGamma(blue_linear);
    output[params.y_size + index] = RGBToU(red, green, blue);
    output[params.y_size + params.uv_size + index] = RGBToV(red, green, blue);
  }
#endif
}

#endif  // WEBP_CUDA_ENABLE_RGB_TO_YUV

#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
WebPAcceleratorResult Initialize(CudaState* state) {
  int device_count = 0;
  cudaError_t error;
  cudaDeviceProp properties;
  if (state->initialization_attempted) {
    return state->available ? WEBP_ACCELERATOR_SUCCESS
                            : WEBP_ACCELERATOR_NOT_RUN;
  }
  state->initialization_attempted = true;
  error = cudaGetDeviceCount(&device_count);
  if (error != cudaSuccess || device_count == 0) {
    if (EnvironmentFlag("WEBP_CUDA_VERBOSE", false)) {
      fprintf(stderr, "WebP-CUDA: no usable device: %s\n",
              cudaGetErrorString(error));
    }
    (void)cudaGetLastError();
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  state->device = EnvironmentDevice();
  if (state->device < 0 || state->device >= device_count) {
    if (EnvironmentFlag("WEBP_CUDA_VERBOSE", false)) {
      fprintf(stderr, "WebP-CUDA: device %d is unavailable (%d detected)\n",
              state->device, device_count);
    }
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  error = cudaSetDevice(state->device);
  if (error == cudaSuccess) {
    error = cudaStreamCreateWithFlags(&state->stream, cudaStreamNonBlocking);
  }
  if (error != cudaSuccess) {
    if (state->stream != nullptr) {
      (void)cudaStreamDestroy(state->stream);
      state->stream = nullptr;
    }
    state->quarantined = true;
    if (EnvironmentFlag("WEBP_CUDA_VERBOSE", false)) {
      fprintf(stderr, "WebP-CUDA: initialization failed: %s\n",
              cudaGetErrorString(error));
    }
    return WEBP_ACCELERATOR_ERROR;
  }
  if (cudaGetDeviceProperties(&properties, state->device) == cudaSuccess) {
    snprintf(state->device_name, sizeof(state->device_name), "%s",
             properties.name);
  } else {
    snprintf(state->device_name, sizeof(state->device_name), "%s",
             "CUDA device");
    (void)cudaGetLastError();
  }
  state->available = true;
  if (EnvironmentFlag("WEBP_CUDA_VERBOSE", false)) {
    fprintf(stderr, "WebP-CUDA: using %s (device %d)\n", state->device_name,
            state->device);
  }
  return WEBP_ACCELERATOR_SUCCESS;
}
#endif  // WEBP_CUDA_HAS_ENCODER_STAGE

#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
bool EnsureTimingEvents(CudaState* state) {
  cudaError_t error;
  if (state->event_start != nullptr && state->event_stop != nullptr) {
    return true;
  }
  error = cudaEventCreate(&state->event_start);
  if (error == cudaSuccess) error = cudaEventCreate(&state->event_stop);
  if (error == cudaSuccess) return true;
  if (state->event_stop != nullptr) {
    (void)cudaEventDestroy(state->event_stop);
    state->event_stop = nullptr;
  }
  if (state->event_start != nullptr) {
    (void)cudaEventDestroy(state->event_start);
    state->event_start = nullptr;
  }
  fprintf(stderr, "WebP-CUDA: timing events unavailable: %s\n",
          cudaGetErrorString(error));
  (void)cudaGetLastError();
  return false;
}

// All staging capacities are byte counts. The buffer templates preserve the
// typed pointer only; requested and new_capacity deliberately remain bytes.
bool RoundedCapacity(size_t requested, size_t current, size_t* capacity) {
  size_t result = current < kMinimumAllocation ? kMinimumAllocation : current;
  while (result < requested) {
    if (result > std::numeric_limits<size_t>::max() / 2u) {
      result = requested;
      break;
    }
    result *= 2u;
  }
  *capacity = result;
  return result >= requested;
}

template <typename T>
cudaError_t EnsureDeviceBuffer(T** buffer, size_t* capacity,
                               size_t requested, cudaStream_t stream) {
  T* replacement = nullptr;
  size_t new_capacity;
  cudaError_t error;
  if (requested <= *capacity) return cudaSuccess;
  if (!RoundedCapacity(requested, *capacity, &new_capacity)) {
    return cudaErrorMemoryAllocation;
  }
#if defined(WEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS)
  error = cudaMallocAsync(reinterpret_cast<void**>(&replacement), new_capacity,
                          stream);
#else
  (void)stream;
  error = cudaMalloc(reinterpret_cast<void**>(&replacement), new_capacity);
#endif
  if (error != cudaSuccess) return error;
  if (*buffer != nullptr) {
#if defined(WEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS)
    error = cudaFreeAsync(*buffer, stream);
#else
    error = cudaFree(*buffer);
#endif
    if (error != cudaSuccess) {
#if defined(WEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS)
      (void)cudaFreeAsync(replacement, stream);
#else
      (void)cudaFree(replacement);
#endif
      return error;
    }
  }
  *buffer = replacement;
  *capacity = new_capacity;
  return cudaSuccess;
}

template <typename T>
bool EnsureHostBuffer(T** buffer, size_t* capacity, size_t requested) {
  size_t new_capacity;
  void* replacement;
  if (requested <= *capacity) return true;
  if (!RoundedCapacity(requested, *capacity, &new_capacity)) return false;
#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
  if (cudaHostAlloc(&replacement, new_capacity, cudaHostAllocDefault) !=
      cudaSuccess) {
    (void)cudaGetLastError();
    return false;
  }
  if (*buffer != nullptr) (void)cudaFreeHost(*buffer);
#else
  replacement = malloc(new_capacity);
  if (replacement == nullptr) return false;
  free(*buffer);
#endif
  *buffer = static_cast<T*>(replacement);
  *capacity = new_capacity;
  return true;
}
#endif  // WEBP_CUDA_HAS_ENCODER_STAGE

template <typename T>
void FreeHostBuffer(T* buffer) {
#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
  if (buffer != nullptr) (void)cudaFreeHost(buffer);
#else
  free(buffer);
#endif
}

#if defined(WEBP_CUDA_HAS_ENCODER_STAGE)
cudaError_t UploadToDevice(void* destination, const void* source, size_t bytes,
                           cudaStream_t stream) {
  cudaError_t error = cudaMemcpyAsync(destination, source, bytes,
                                      cudaMemcpyHostToDevice, stream);
#if !defined(WEBP_CUDA_ENABLE_ASYNC_COPIES)
  if (error == cudaSuccess) error = cudaStreamSynchronize(stream);
#endif
  return error;
}

cudaError_t DownloadFromDevice(void* destination, const void* source,
                               size_t bytes, cudaStream_t stream) {
  cudaError_t error = cudaMemcpyAsync(destination, source, bytes,
                                      cudaMemcpyDeviceToHost, stream);
#if !defined(WEBP_CUDA_ENABLE_ASYNC_COPIES)
  if (error == cudaSuccess) error = cudaStreamSynchronize(stream);
#endif
  return error;
}

cudaError_t FinishDownloads(cudaStream_t stream) {
#if defined(WEBP_CUDA_ENABLE_ASYNC_COPIES)
  return cudaStreamSynchronize(stream);
#else
  (void)stream;
  return cudaSuccess;
#endif
}
#endif  // WEBP_CUDA_HAS_ENCODER_STAGE

void ReleaseStagingBuffers(CudaState* state) {
#if defined(WEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS)
  if (state->pixels != nullptr) (void)cudaFreeAsync(state->pixels, state->stream);
  if (state->transform != nullptr) {
    (void)cudaFreeAsync(state->transform, state->stream);
  }
  if (state->chain != nullptr) (void)cudaFreeAsync(state->chain, state->stream);
#else
  if (state->pixels != nullptr) (void)cudaFree(state->pixels);
  if (state->transform != nullptr) (void)cudaFree(state->transform);
  if (state->chain != nullptr) (void)cudaFree(state->chain);
#endif
  state->pixels = nullptr;
  state->transform = nullptr;
  state->chain = nullptr;
  state->pixel_capacity = 0;
  state->transform_capacity = 0;
  state->chain_capacity = 0;
  FreeHostBuffer(state->host_pixels);
  FreeHostBuffer(state->host_transform);
  FreeHostBuffer(state->host_chain);
  state->host_pixels = nullptr;
  state->host_transform = nullptr;
  state->host_chain = nullptr;
  state->host_pixel_capacity = 0;
  state->host_transform_capacity = 0;
  state->host_chain_capacity = 0;
}

WebPAcceleratorResult ReportError(CudaState* state, const char* operation,
                                  cudaError_t error, bool quarantine) {
  if (EnvironmentFlag("WEBP_CUDA_VERBOSE", false)) {
    fprintf(stderr, "WebP-CUDA: %s failed: %s\n", operation,
            cudaGetErrorString(error));
  }
  if (quarantine) state->quarantined = true;
  return WEBP_ACCELERATOR_ERROR;
}

#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM)

WebPAcceleratorResult CUDAColorTransformLocked(
    void* context, const WebPAcceleratorColorTransformRequest* request) {
  CudaState* const state = static_cast<CudaState*>(context);
  size_t pixel_count;
  size_t pixel_bytes;
  uint32_t tile_size;
  uint32_t tile_columns;
  uint32_t tile_rows;
  size_t tile_count;
  size_t transform_bytes;
  KernelParams params;
  cudaError_t error;
  float elapsed_ms = 0.0f;
  bool verbose;
  bool timing;

  if (!EnvironmentFlag("WEBP_CUDA", true) ||
      !EnvironmentFlag("WEBP_CUDA_COLOR", true)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (request == nullptr || request->argb == nullptr ||
      request->transform_image == nullptr || request->width <= 0 ||
      request->height <= 0 || request->bits < 0 || request->bits > 8 ||
      request->quality < 0 || request->quality > 100) {
    return WEBP_ACCELERATOR_ERROR;
  }
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
  if ((1u << request->bits) > kMaximumCachedColorTileSize) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
#endif
  if (static_cast<size_t>(request->width) >
      std::numeric_limits<size_t>::max() /
          static_cast<size_t>(request->height)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  pixel_count = static_cast<size_t>(request->width) * request->height;
  const bool profitable_batch = HasProfitableLosslessBatchHint();
  if (pixel_count < EnvironmentSize(
                        "WEBP_CUDA_MIN_PIXELS",
                        state->available || profitable_batch
                            ? kDefaultColorWarmMinimumPixels
                            : kDefaultColorColdMinimumPixels)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (pixel_count > std::numeric_limits<size_t>::max() / sizeof(uint32_t)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  pixel_bytes = pixel_count * sizeof(uint32_t);
  tile_size = 1u << request->bits;
  tile_columns =
      (static_cast<uint32_t>(request->width) + tile_size - 1u) >> request->bits;
  tile_rows =
      (static_cast<uint32_t>(request->height) + tile_size - 1u) >>
      request->bits;
  tile_count = static_cast<size_t>(tile_columns) * tile_rows;
  if (tile_count > std::numeric_limits<size_t>::max() / sizeof(uint32_t)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  transform_bytes = tile_count * sizeof(uint32_t);
  params = {static_cast<uint32_t>(request->width),
            static_cast<uint32_t>(request->height),
            static_cast<uint32_t>(request->bits),
            static_cast<uint32_t>(request->quality), tile_columns};

  if (state->quarantined) return WEBP_ACCELERATOR_NOT_RUN;
  const WebPAcceleratorResult initialized = Initialize(state);
  if (initialized != WEBP_ACCELERATOR_SUCCESS) return initialized;
  error = cudaSetDevice(state->device);
  if (error != cudaSuccess) {
    return ReportError(state, "select device", error, true);
  }
  error = EnsureDeviceBuffer(&state->pixels, &state->pixel_capacity,
                             pixel_bytes, state->stream);
  if (error == cudaSuccess) {
    error = EnsureDeviceBuffer(&state->transform, &state->transform_capacity,
                               transform_bytes, state->stream);
  }
  if (error != cudaSuccess) {
    return ReportError(state, "allocate staging buffers", error, false);
  }
  if (!EnsureHostBuffer(&state->host_pixels, &state->host_pixel_capacity,
                        pixel_bytes) ||
      !EnsureHostBuffer(&state->host_transform,
                        &state->host_transform_capacity, transform_bytes)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  verbose = EnvironmentFlag("WEBP_CUDA_VERBOSE", false);
  timing = verbose && EnsureTimingEvents(state);

#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
  memcpy(state->host_pixels, request->argb, pixel_bytes);
  error = UploadToDevice(state->pixels, state->host_pixels, pixel_bytes,
                         state->stream);
#else
  error = UploadToDevice(state->pixels, request->argb, pixel_bytes,
                         state->stream);
#endif
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_start, state->stream);
  }
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "upload", error, true);
  }
  (void)cudaGetLastError();
  const size_t shared_tile_bytes =
#if defined(WEBP_CUDA_ENABLE_COLOR_SHARED_TILE)
      static_cast<size_t>(tile_size) * tile_size * sizeof(uint32_t);
#else
      0u;
#endif
  ColorSpaceTransformKernel<<<dim3(tile_columns, tile_rows),
                              kColorThreadsPerBlock, shared_tile_bytes,
                              state->stream>>>(
      state->pixels, state->transform, params);
  error = cudaGetLastError();
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_stop, state->stream);
  }
  if (error == cudaSuccess) {
    error = DownloadFromDevice(state->host_pixels, state->pixels, pixel_bytes,
                               state->stream);
  }
  if (error == cudaSuccess) {
    error = DownloadFromDevice(state->host_transform, state->transform,
                               transform_bytes, state->stream);
  }
  if (error == cudaSuccess) error = FinishDownloads(state->stream);
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "transform", error, true);
  }

  memcpy(request->argb, state->host_pixels, pixel_bytes);
  memcpy(request->transform_image, state->host_transform, transform_bytes);
  if (verbose) {
    if (timing) {
      if (cudaEventElapsedTime(&elapsed_ms, state->event_start,
                               state->event_stop) != cudaSuccess) {
        elapsed_ms = 0.0f;
        (void)cudaGetLastError();
      }
    }
    fprintf(stderr, "WebP-CUDA: transformed %dx%d in %.3f ms (%zu tiles)\n",
            request->width, request->height, elapsed_ms, tile_count);
  }
#if !defined(WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS)
  ReleaseStagingBuffers(state);
#endif
  return WEBP_ACCELERATOR_SUCCESS;
}

WebPAcceleratorResult CUDAColorTransform(
    void* context, const WebPAcceleratorColorTransformRequest* request) {
  WebPAcceleratorResult result;
  LockCudaMutex(&g_cuda_mutex);
  result = CUDAColorTransformLocked(context, request);
  if (result == WEBP_ACCELERATOR_SUCCESS) {
    g_cuda_state.successful_stages |=
        WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM;
  }
  UnlockCudaMutex(&g_cuda_mutex);
  return result;
}

#endif  // WEBP_CUDA_ENABLE_COLOR_TRANSFORM

#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)

WebPAcceleratorResult CUDANearLosslessLocked(
    void* context, const WebPAcceleratorNearLosslessRequest* request) {
  CudaState* const state = static_cast<CudaState*>(context);
  size_t pixel_count;
  size_t pixel_bytes;
  cudaError_t error;
  bool verbose;
  bool timing;
  float elapsed_ms = 0.0f;

  if (!EnvironmentFlag("WEBP_CUDA", true) ||
      !EnvironmentFlag("WEBP_CUDA_NEAR_LOSSLESS", true)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (request == nullptr || request->source == nullptr ||
      request->output == nullptr || request->width <= 0 ||
      request->height < 3 || request->source_stride < request->width ||
      request->limit_bits < 1 || request->limit_bits > 5) {
    return WEBP_ACCELERATOR_ERROR;
  }
  if (static_cast<size_t>(request->width) >
      std::numeric_limits<size_t>::max() /
          static_cast<size_t>(request->height)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  pixel_count = static_cast<size_t>(request->width) * request->height;
  if (pixel_count > std::numeric_limits<uint32_t>::max()) {
    return WEBP_ACCELERATOR_ERROR;
  }
  const bool profitable_batch = HasProfitableNearLosslessBatchHint();
  // One- and two-pass CPU preprocessing remained faster than a cold CUDA
  // runtime at the largest measured size. An explicit threshold remains a
  // correctness/experimentation override for every pass count.
  size_t explicit_threshold;
  const bool has_explicit_threshold = ParseEnvironmentSize(
      "WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS", &explicit_threshold);
  if (!state->available && !profitable_batch && request->limit_bits < 3 &&
      !has_explicit_threshold) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  const size_t threshold =
      has_explicit_threshold
          ? explicit_threshold
          : state->available || profitable_batch
                ? kDefaultNearLosslessWarmMinimumPixels
                : kDefaultNearLosslessColdMinimumPixels;
  if (pixel_count < threshold) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (pixel_count > std::numeric_limits<size_t>::max() / sizeof(uint32_t)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  pixel_bytes = pixel_count * sizeof(uint32_t);
  if (state->quarantined) return WEBP_ACCELERATOR_NOT_RUN;
  const WebPAcceleratorResult initialized = Initialize(state);
  if (initialized != WEBP_ACCELERATOR_SUCCESS) return initialized;
  error = cudaSetDevice(state->device);
  if (error != cudaSuccess) {
    return ReportError(state, "select device", error, true);
  }
  error = EnsureDeviceBuffer(&state->pixels, &state->pixel_capacity,
                             pixel_bytes, state->stream);
  if (error == cudaSuccess) {
    error = EnsureDeviceBuffer(&state->transform, &state->transform_capacity,
                               pixel_bytes, state->stream);
  }
  if (error != cudaSuccess) {
    return ReportError(state, "allocate near-lossless buffers", error, false);
  }
  if (!EnsureHostBuffer(&state->host_pixels, &state->host_pixel_capacity,
                        pixel_bytes) ||
      !EnsureHostBuffer(&state->host_transform,
                        &state->host_transform_capacity, pixel_bytes)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  for (int y = 0; y < request->height; ++y) {
    memcpy(state->host_pixels + static_cast<size_t>(y) * request->width,
           request->source + static_cast<size_t>(y) * request->source_stride,
           static_cast<size_t>(request->width) * sizeof(uint32_t));
  }
  verbose = EnvironmentFlag("WEBP_CUDA_VERBOSE", false);
  timing = verbose && EnsureTimingEvents(state);
  error = UploadToDevice(state->pixels, state->host_pixels, pixel_bytes,
                         state->stream);
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_start, state->stream);
  }
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "near-lossless upload", error, true);
  }
  uint32_t* source = state->pixels;
  uint32_t* output = state->transform;
  const dim3 threads(16u, 16u);
  const dim3 blocks((static_cast<uint32_t>(request->width) + 15u) / 16u,
                    (static_cast<uint32_t>(request->height) + 15u) / 16u);
  (void)cudaGetLastError();
  for (int bits = request->limit_bits; bits > 0; --bits) {
    NearLosslessKernel<<<blocks, threads, 0, state->stream>>>(
        source, output, static_cast<uint32_t>(request->width),
        static_cast<uint32_t>(request->height), bits);
    uint32_t* const temporary = source;
    source = output;
    output = temporary;
  }
  error = cudaGetLastError();
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_stop, state->stream);
  }
  if (error == cudaSuccess) {
    error = DownloadFromDevice(state->host_transform, source, pixel_bytes,
                               state->stream);
  }
  if (error == cudaSuccess) error = FinishDownloads(state->stream);
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "near-lossless preprocess", error, true);
  }
  memcpy(request->output, state->host_transform, pixel_bytes);
  if (verbose) {
    if (timing &&
        cudaEventElapsedTime(&elapsed_ms, state->event_start,
                             state->event_stop) != cudaSuccess) {
      elapsed_ms = 0.0f;
      (void)cudaGetLastError();
    }
    fprintf(stderr,
            "WebP-CUDA: near-lossless %dx%d in %.3f ms (%d passes)\n",
            request->width, request->height, elapsed_ms,
            request->limit_bits);
  }
#if !defined(WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS)
  ReleaseStagingBuffers(state);
#endif
  return WEBP_ACCELERATOR_SUCCESS;
}

WebPAcceleratorResult CUDANearLossless(
    void* context, const WebPAcceleratorNearLosslessRequest* request) {
  WebPAcceleratorResult result;
  LockCudaMutex(&g_cuda_mutex);
  result = CUDANearLosslessLocked(context, request);
  if (result == WEBP_ACCELERATOR_SUCCESS) {
    g_cuda_state.successful_stages |= WEBP_ACCELERATOR_STAGE_NEAR_LOSSLESS;
  }
  UnlockCudaMutex(&g_cuda_mutex);
  return result;
}

#endif  // WEBP_CUDA_ENABLE_NEAR_LOSSLESS

#if defined(WEBP_CUDA_ENABLE_HASH_CHAIN)

WebPAcceleratorResult CUDAHashChainLocked(
    void* context, const WebPAcceleratorHashChainRequest* request) {
  CudaState* const state = static_cast<CudaState*>(context);
  size_t bytes;
  HashKernelParams params;
  cudaError_t error;
  float elapsed_ms = 0.0f;
  bool verbose;
  bool timing;

  if (!EnvironmentFlag("WEBP_CUDA", true) ||
      !EnvironmentFlag("WEBP_CUDA_HASH", true)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (request == nullptr || request->pixels == nullptr ||
      request->chain == nullptr || request->candidates == nullptr ||
      request->size <= 2 || request->xsize <= 0 || request->iter_max <= 0) {
    return WEBP_ACCELERATOR_ERROR;
  }
  const bool profitable_batch = HasProfitableLosslessBatchHint();
  if (static_cast<size_t>(request->size) <
      EnvironmentSize(
          "WEBP_CUDA_HASH_MIN_PIXELS",
          profitable_batch
              ? EnvironmentSize("WEBP_CUDA_HASH_BATCH_MIN_PIXELS",
                                kDefaultHashBatchMinimumPixels)
              : state->available ? kDefaultHashWarmMinimumPixels
                                 : kDefaultHashColdMinimumPixels)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (static_cast<size_t>(request->size) >
      std::numeric_limits<size_t>::max() / sizeof(uint32_t)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  bytes = static_cast<size_t>(request->size) * sizeof(uint32_t);
  params = {static_cast<uint32_t>(request->size),
            static_cast<uint32_t>(request->xsize),
            static_cast<uint32_t>(request->iter_max), request->window_size,
            static_cast<uint32_t>(request->low_effort != 0)};

  if (state->quarantined) return WEBP_ACCELERATOR_NOT_RUN;
  const WebPAcceleratorResult initialized = Initialize(state);
  if (initialized != WEBP_ACCELERATOR_SUCCESS) return initialized;
  error = cudaSetDevice(state->device);
  if (error != cudaSuccess) {
    return ReportError(state, "select device", error, true);
  }
  error = EnsureDeviceBuffer(&state->pixels, &state->pixel_capacity, bytes,
                             state->stream);
  if (error == cudaSuccess) {
    error = EnsureDeviceBuffer(&state->chain, &state->chain_capacity, bytes,
                               state->stream);
  }
  if (error == cudaSuccess) {
    error = EnsureDeviceBuffer(&state->transform, &state->transform_capacity,
                               bytes, state->stream);
  }
  if (error != cudaSuccess) {
    return ReportError(state, "allocate hash staging buffers", error, false);
  }
  if (!EnsureHostBuffer(&state->host_transform,
                        &state->host_transform_capacity, bytes)
#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
      || !EnsureHostBuffer(&state->host_pixels, &state->host_pixel_capacity,
                           bytes) ||
      !EnsureHostBuffer(&state->host_chain, &state->host_chain_capacity, bytes)
#endif
  ) {
    return WEBP_ACCELERATOR_ERROR;
  }
  verbose = EnvironmentFlag("WEBP_CUDA_VERBOSE", false);
  timing = verbose && EnsureTimingEvents(state);

#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
  memcpy(state->host_pixels, request->pixels, bytes);
  memcpy(state->host_chain, request->chain, bytes);
  error = UploadToDevice(state->pixels, state->host_pixels, bytes,
                         state->stream);
  if (error == cudaSuccess) {
    error = UploadToDevice(state->chain, state->host_chain, bytes,
                           state->stream);
  }
#else
  error = UploadToDevice(state->pixels, request->pixels, bytes, state->stream);
  if (error == cudaSuccess) {
    error = UploadToDevice(state->chain, request->chain, bytes, state->stream);
  }
#endif
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_start, state->stream);
  }
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "hash upload", error, true);
  }
  (void)cudaGetLastError();
  const uint32_t blocks =
      (static_cast<uint32_t>(request->size) + kHashThreadsPerBlock - 1u) /
      kHashThreadsPerBlock;
  HashChainCandidatesKernel<<<blocks, kHashThreadsPerBlock, 0, state->stream>>>(
      state->pixels, state->chain, state->transform, params);
  error = cudaGetLastError();
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_stop, state->stream);
  }
  if (error == cudaSuccess) {
    error = DownloadFromDevice(state->host_transform, state->transform, bytes,
                               state->stream);
  }
  if (error == cudaSuccess) error = FinishDownloads(state->stream);
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "hash candidates", error, true);
  }
  memcpy(request->candidates, state->host_transform, bytes);
  if (verbose) {
    if (timing && cudaEventElapsedTime(&elapsed_ms, state->event_start,
                                       state->event_stop) != cudaSuccess) {
      elapsed_ms = 0.0f;
      (void)cudaGetLastError();
    }
    fprintf(stderr,
            "WebP-CUDA: hash candidates for %d pixels in %.3f ms\n",
            request->size, elapsed_ms);
  }
#if !defined(WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS)
  ReleaseStagingBuffers(state);
#endif
  return WEBP_ACCELERATOR_SUCCESS;
}

WebPAcceleratorResult CUDAHashChain(
    void* context, const WebPAcceleratorHashChainRequest* request) {
  WebPAcceleratorResult result;
  LockCudaMutex(&g_cuda_mutex);
  result = CUDAHashChainLocked(context, request);
  if (result == WEBP_ACCELERATOR_SUCCESS) {
    g_cuda_state.successful_stages |=
        WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN;
  }
  UnlockCudaMutex(&g_cuda_mutex);
  return result;
}

#endif  // WEBP_CUDA_ENABLE_HASH_CHAIN

#if defined(WEBP_CUDA_ENABLE_RGB_TO_YUV)

cudaError_t EnsureGammaTables(CudaState* state) {
  uint16_t gamma_to_linear[256];
  int32_t linear_to_gamma[33];
  cudaError_t error;
  if (state->gamma_initialized) return cudaSuccess;
  constexpr double kGamma = 0.80;
  constexpr int kGammaScale = (1 << 12) - 1;
  const double scale = static_cast<double>(1 << 7) / kGammaScale;
  for (int value = 0; value <= 255; ++value) {
    gamma_to_linear[value] = static_cast<uint16_t>(
        pow(value / 255.0, kGamma) * kGammaScale + 0.5);
  }
  for (int value = 0; value <= 32; ++value) {
    linear_to_gamma[value] = static_cast<int32_t>(
        255.0 * pow(scale * value, 1.0 / kGamma) + 0.5);
  }
  error = cudaMemcpyToSymbolAsync(kGammaToLinear, gamma_to_linear,
                                  sizeof(gamma_to_linear), 0,
                                  cudaMemcpyHostToDevice, state->stream);
  if (error == cudaSuccess) {
    error = cudaMemcpyToSymbolAsync(kLinearToGamma, linear_to_gamma,
                                    sizeof(linear_to_gamma), 0,
                                    cudaMemcpyHostToDevice, state->stream);
  }
  if (error == cudaSuccess) error = cudaStreamSynchronize(state->stream);
  if (error != cudaSuccess) return error;
  state->gamma_initialized = true;
  return cudaSuccess;
}

WebPAcceleratorResult CUDARGBToYUVLocked(
    void* context, const WebPAcceleratorRGBToYUVRequest* request) {
  CudaState* const state = static_cast<CudaState*>(context);
  uintptr_t red;
  uintptr_t green;
  uintptr_t blue;
  uintptr_t base;
  uintptr_t red_offset;
  uintptr_t green_offset;
  uintptr_t blue_offset;
  size_t source_size;
  size_t pixel_count;
  size_t uv_size;
  size_t output_size;
  uint32_t uv_width;
  uint32_t uv_height;
  RGBKernelParams params;
  cudaError_t error;
  float elapsed_ms = 0.0f;
  bool verbose;
  bool timing;

  if (!EnvironmentFlag("WEBP_CUDA", true) ||
      !EnvironmentFlag("WEBP_CUDA_LOSSY", false)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  if (request == nullptr || request->red == nullptr ||
      request->green == nullptr || request->blue == nullptr ||
      request->y == nullptr || request->u == nullptr || request->v == nullptr ||
      (request->step != 3 && request->step != 4) ||
      request->source_stride <= 0 || request->width <= 0 ||
      request->height <= 0 || request->y_stride < request->width) {
    return WEBP_ACCELERATOR_ERROR;
  }
  red = reinterpret_cast<uintptr_t>(request->red);
  green = reinterpret_cast<uintptr_t>(request->green);
  blue = reinterpret_cast<uintptr_t>(request->blue);
  base = red < green ? (red < blue ? red : blue)
                     : (green < blue ? green : blue);
  red_offset = red - base;
  green_offset = green - base;
  blue_offset = blue - base;
  if (red_offset >= static_cast<uintptr_t>(request->step) ||
      green_offset >= static_cast<uintptr_t>(request->step) ||
      blue_offset >= static_cast<uintptr_t>(request->step)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  uv_width = (static_cast<uint32_t>(request->width) + 1u) >> 1;
  uv_height = (static_cast<uint32_t>(request->height) + 1u) >> 1;
  if (request->uv_stride < static_cast<int>(uv_width)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  if (static_cast<size_t>(request->width) >
      std::numeric_limits<size_t>::max() /
          static_cast<size_t>(request->height)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  pixel_count = static_cast<size_t>(request->width) * request->height;
  if (pixel_count < EnvironmentSize(
                        "WEBP_CUDA_LOSSY_MIN_PIXELS",
                        state->available ? kDefaultRGBWarmMinimumPixels
                                         : kDefaultRGBColdMinimumPixels)) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  uv_size = static_cast<size_t>(uv_width) * uv_height;
  if (pixel_count > std::numeric_limits<uint32_t>::max() ||
      uv_size > std::numeric_limits<uint32_t>::max() ||
      uv_size > (std::numeric_limits<size_t>::max() - pixel_count) / 2u) {
    return WEBP_ACCELERATOR_ERROR;
  }
  output_size = pixel_count + 2u * uv_size;
  const size_t maximum_channel_offset =
      std::max(red_offset, std::max(green_offset, blue_offset));
  const size_t last_row_extent =
      static_cast<size_t>(request->width - 1) * request->step +
      maximum_channel_offset + 1u;
  if (static_cast<size_t>(request->source_stride) < last_row_extent ||
      static_cast<size_t>(request->height - 1) >
          (std::numeric_limits<size_t>::max() - last_row_extent) /
              static_cast<size_t>(request->source_stride)) {
    return WEBP_ACCELERATOR_ERROR;
  }
  source_size = static_cast<size_t>(request->height - 1) *
                    request->source_stride +
                last_row_extent;
  if (source_size > std::numeric_limits<uint32_t>::max()) {
    return WEBP_ACCELERATOR_NOT_RUN;
  }
  params = {static_cast<uint32_t>(request->width),
            static_cast<uint32_t>(request->height),
            static_cast<uint32_t>(request->step),
            static_cast<uint32_t>(request->source_stride),
            static_cast<uint32_t>(red_offset),
            static_cast<uint32_t>(green_offset),
            static_cast<uint32_t>(blue_offset), uv_width,
            static_cast<uint32_t>(pixel_count),
            static_cast<uint32_t>(uv_size),
            static_cast<uint32_t>(request->step == 4 &&
                                  request->source_stride % 4 == 0 &&
                                  maximum_channel_offset + 1u ==
                                      static_cast<size_t>(request->step))};

  if (state->quarantined) return WEBP_ACCELERATOR_NOT_RUN;
  const WebPAcceleratorResult initialized = Initialize(state);
  if (initialized != WEBP_ACCELERATOR_SUCCESS) return initialized;
  error = cudaSetDevice(state->device);
  if (error != cudaSuccess) {
    return ReportError(state, "select device", error, true);
  }
  error = EnsureGammaTables(state);
  if (error != cudaSuccess) {
    return ReportError(state, "initialize gamma tables", error, true);
  }
  error = EnsureDeviceBuffer(&state->pixels, &state->pixel_capacity,
                             source_size, state->stream);
  if (error == cudaSuccess) {
    error = EnsureDeviceBuffer(&state->transform, &state->transform_capacity,
                               output_size, state->stream);
  }
  if (error != cudaSuccess) {
    return ReportError(state, "allocate RGB staging buffers", error, false);
  }
  if (!EnsureHostBuffer(&state->host_transform,
                        &state->host_transform_capacity, output_size)
#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
      || !EnsureHostBuffer(&state->host_pixels, &state->host_pixel_capacity,
                           source_size)
#endif
  ) {
    return WEBP_ACCELERATOR_ERROR;
  }
  verbose = EnvironmentFlag("WEBP_CUDA_VERBOSE", false);
  timing = verbose && EnsureTimingEvents(state);

#if defined(WEBP_CUDA_ENABLE_PINNED_HOST_MEMORY)
  memcpy(state->host_pixels, reinterpret_cast<const void*>(base), source_size);
  error = UploadToDevice(state->pixels, state->host_pixels, source_size,
                         state->stream);
#else
  error = UploadToDevice(state->pixels, reinterpret_cast<const void*>(base),
                         source_size, state->stream);
#endif
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_start, state->stream);
  }
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "RGB upload", error, true);
  }
  const uint32_t work_items =
#if defined(WEBP_CUDA_ENABLE_RGB_BLOCK_2X2)
      static_cast<uint32_t>(uv_size);
#else
      static_cast<uint32_t>(pixel_count);
#endif
  const uint32_t blocks =
      (work_items + kRGBThreadsPerBlock - 1u) / kRGBThreadsPerBlock;
  (void)cudaGetLastError();
  RGBToYUV420Kernel<<<blocks, kRGBThreadsPerBlock, 0, state->stream>>>(
      reinterpret_cast<const uint8_t*>(state->pixels),
      reinterpret_cast<uint8_t*>(state->transform), params);
  error = cudaGetLastError();
  if (error == cudaSuccess && timing) {
    error = cudaEventRecord(state->event_stop, state->stream);
  }
  if (error == cudaSuccess) {
    error = DownloadFromDevice(state->host_transform, state->transform,
                               output_size, state->stream);
  }
  if (error == cudaSuccess) error = FinishDownloads(state->stream);
  if (error != cudaSuccess) {
    (void)cudaStreamSynchronize(state->stream);
    return ReportError(state, "RGB-to-YUV", error, true);
  }

  const uint8_t* const output =
      reinterpret_cast<const uint8_t*>(state->host_transform);
  for (int row = 0; row < request->height; ++row) {
    memcpy(request->y + static_cast<size_t>(row) * request->y_stride,
           output + static_cast<size_t>(row) * request->width,
           request->width);
  }
  const uint8_t* const output_u = output + pixel_count;
  const uint8_t* const output_v = output_u + uv_size;
  for (uint32_t row = 0; row < uv_height; ++row) {
    memcpy(request->u + static_cast<size_t>(row) * request->uv_stride,
           output_u + static_cast<size_t>(row) * uv_width, uv_width);
    memcpy(request->v + static_cast<size_t>(row) * request->uv_stride,
           output_v + static_cast<size_t>(row) * uv_width, uv_width);
  }
  if (verbose) {
    if (timing && cudaEventElapsedTime(&elapsed_ms, state->event_start,
                                       state->event_stop) != cudaSuccess) {
      elapsed_ms = 0.0f;
      (void)cudaGetLastError();
    }
    fprintf(stderr, "WebP-CUDA: lossy RGB->YUV %dx%d in %.3f ms\n",
            request->width, request->height, elapsed_ms);
  }
#if !defined(WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS)
  ReleaseStagingBuffers(state);
#endif
  return WEBP_ACCELERATOR_SUCCESS;
}

WebPAcceleratorResult CUDARGBToYUV(
    void* context, const WebPAcceleratorRGBToYUVRequest* request) {
  WebPAcceleratorResult result;
  LockCudaMutex(&g_cuda_mutex);
  result = CUDARGBToYUVLocked(context, request);
  if (result == WEBP_ACCELERATOR_SUCCESS) {
    g_cuda_state.successful_stages |= WEBP_ACCELERATOR_STAGE_RGB_TO_YUV;
  }
  UnlockCudaMutex(&g_cuda_mutex);
  return result;
}

#endif  // WEBP_CUDA_ENABLE_RGB_TO_YUV

WebPAcceleratorResult CUDAFlush(void* context) {
  CudaState* const state = static_cast<CudaState*>(context);
  WebPAcceleratorResult result;
  LockCudaMutex(&g_cuda_mutex);
  if (!state->available || state->quarantined) {
    result = WEBP_ACCELERATOR_NOT_RUN;
  } else {
    cudaError_t error = cudaSetDevice(state->device);
    if (error == cudaSuccess) error = cudaStreamSynchronize(state->stream);
    result = error == cudaSuccess
                 ? WEBP_ACCELERATOR_SUCCESS
                 : ReportError(state, "flush", error, true);
  }
  UnlockCudaMutex(&g_cuda_mutex);
  return result;
}

void CUDATrim(void* context) {
  CudaState* const state = static_cast<CudaState*>(context);
  LockCudaMutex(&g_cuda_mutex);
  if (state->available && cudaSetDevice(state->device) == cudaSuccess) {
    ReleaseStagingBuffers(state);
#if defined(WEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS)
    (void)cudaStreamSynchronize(state->stream);
#endif
  }
  UnlockCudaMutex(&g_cuda_mutex);
}

constexpr uint32_t kCUDAStages =
    0u
#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM)
    | WEBP_ACCELERATOR_STAGE_LOSSLESS_COLOR_TRANSFORM
#endif
#if defined(WEBP_CUDA_ENABLE_HASH_CHAIN)
    | WEBP_ACCELERATOR_STAGE_LOSSLESS_HASH_CHAIN
#endif
#if defined(WEBP_CUDA_ENABLE_RGB_TO_YUV)
    | WEBP_ACCELERATOR_STAGE_RGB_TO_YUV
#endif
#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
    | WEBP_ACCELERATOR_STAGE_NEAR_LOSSLESS
#endif
    ;

constexpr uint32_t kCUDAProperties =
    WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |
    WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT |
    WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC |
    WEBP_ACCELERATOR_PROPERTY_SERIALIZED
#if defined(WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS)
    | WEBP_ACCELERATOR_PROPERTY_PERSISTENT_RESOURCES
#endif
    ;

}  // namespace

static const WebPEncoderAccelerator kCUDAEncoderAccelerator = {
    WEBP_ENCODER_ACCELERATOR_ABI_VERSION,
    sizeof(WebPEncoderAccelerator),
    "cuda",
    kCUDAStages,
    kCUDAProperties,
    &g_cuda_state,
#if defined(WEBP_CUDA_ENABLE_COLOR_TRANSFORM)
    CUDAColorTransform,
#else
    nullptr,
#endif
#if defined(WEBP_CUDA_ENABLE_HASH_CHAIN)
    CUDAHashChain,
#else
    nullptr,
#endif
#if defined(WEBP_CUDA_ENABLE_RGB_TO_YUV)
    CUDARGBToYUV,
#else
    nullptr,
#endif
#if defined(WEBP_CUDA_ENABLE_NEAR_LOSSLESS)
    CUDANearLossless,
#else
    nullptr,
#endif
    CUDAFlush,
    CUDATrim};

extern "C" const WebPEncoderAccelerator* WebPGetCUDAEncoderAccelerator(void) {
  return &kCUDAEncoderAccelerator;
}

extern "C" void WebPCUDAResetSuccessfulStages(void) {
  LockCudaMutex(&g_cuda_mutex);
  g_cuda_state.successful_stages = 0;
  UnlockCudaMutex(&g_cuda_mutex);
}

extern "C" uint32_t WebPCUDAGetSuccessfulStages(void) {
  uint32_t stages;
  LockCudaMutex(&g_cuda_mutex);
  stages = g_cuda_state.successful_stages;
  UnlockCudaMutex(&g_cuda_mutex);
  return stages;
}
