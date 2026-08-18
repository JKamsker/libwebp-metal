// Copyright 2026
//
// Non-installed CUDA acceleration laboratory. This intentionally lives outside
// the encoder ABI: every case has a deterministic CPU oracle and may be timed
// independently before a strategy is promoted into production code.

#include <cuda_runtime.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

constexpr int kWidth = 1024;
constexpr int kHeight = 768;
constexpr int kPixels = kWidth * kHeight;
constexpr int kTile = 16;
bool g_verify_outputs = true;

void CudaCheck(cudaError_t status, const char* operation) {
  if (status != cudaSuccess) {
    std::fprintf(stderr, "CUDA failure in %s: %s\n", operation,
                 cudaGetErrorString(status));
    std::exit(2);
  }
}

#define CUDA_CHECK(call) CudaCheck((call), #call)

uint32_t Mix(uint32_t x) {
  x ^= x >> 16;
  x *= 0x7feb352du;
  x ^= x >> 15;
  x *= 0x846ca68bu;
  return x ^ (x >> 16);
}

std::vector<uint32_t> MakePixels(int count = kPixels) {
  std::vector<uint32_t> pixels(count);
  for (int i = 0; i < count; ++i) {
    const uint32_t v = Mix(static_cast<uint32_t>(i) + 17u);
    pixels[i] = 0xff000000u | (v & 0x00ffffffu);
  }
  return pixels;
}

uint64_t Checksum(const void* data, size_t size) {
  const uint8_t* p = static_cast<const uint8_t*>(data);
  uint64_t result = 1469598103934665603ull;
  for (size_t i = 0; i < size; ++i) {
    result ^= p[i];
    result *= 1099511628211ull;
  }
  return result;
}

template <typename T>
T* DeviceAlloc(size_t count) {
  T* ptr = nullptr;
  CUDA_CHECK(cudaMalloc(&ptr, count * sizeof(*ptr)));
  return ptr;
}

template <typename T>
void DeviceFree(T* ptr) {
  CUDA_CHECK(cudaFree(ptr));
}

__device__ __host__ uint8_t Byte(uint32_t p, int shift) {
  return static_cast<uint8_t>(p >> shift);
}

__device__ __host__ uint32_t Pack(uint8_t a, uint8_t r, uint8_t g,
                                  uint8_t b) {
  return (static_cast<uint32_t>(a) << 24) |
         (static_cast<uint32_t>(r) << 16) |
         (static_cast<uint32_t>(g) << 8) | b;
}

// -----------------------------------------------------------------------------
// Cross-color search control and the retained shared-tile strategy.

__device__ __host__ uint8_t ColorResidual(uint32_t p, int coefficient) {
  const int red = Byte(p, 16);
  const int green = Byte(p, 8);
  return static_cast<uint8_t>(red - ((coefficient * green) >> 5));
}

__global__ void ColorBaselineKernel(const uint32_t* pixels, int width,
                                    int height, unsigned int* histograms) {
  const int tile_x = blockIdx.x * kTile;
  const int tile_y = blockIdx.y * kTile;
  const int local = threadIdx.x;
  const int x = tile_x + local % kTile;
  const int y = tile_y + local / kTile;
  if (x >= width || y >= height) return;
  const int tile_id = blockIdx.y * gridDim.x + blockIdx.x;
  const int coefficients[4] = {-16, 0, 16, 32};
  const uint32_t p = pixels[y * width + x];
  for (int c = 0; c < 4; ++c) {
    atomicAdd(histograms + (tile_id * 4 + c) * 256 +
                  ColorResidual(p, coefficients[c]),
              1u);
  }
}

__global__ void ColorHistogramScoreKernel(const unsigned int* histograms,
                                          int score_count,
                                          uint64_t* scores) {
  const int score = blockIdx.x * blockDim.x + threadIdx.x;
  if (score >= score_count) return;
  uint64_t sum = 0;
  for (int bin = 0; bin < 256; ++bin) {
    const unsigned int count = histograms[score * 256 + bin];
    sum += static_cast<uint64_t>(count) * count;
  }
  scores[score] = sum;
}

__global__ void ColorSharedTileKernel(const uint32_t* pixels, int width,
                                      int height, uint64_t* scores) {
  __shared__ uint32_t cache[kTile * kTile];
  __shared__ unsigned int histogram[256];
  const int local = threadIdx.x;
  const int tile_x = blockIdx.x * kTile;
  const int tile_y = blockIdx.y * kTile;
  const int x = tile_x + local % kTile;
  const int y = tile_y + local / kTile;
  cache[local] = (x < width && y < height) ? pixels[y * width + x] : 0u;
  const int coefficients[4] = {-16, 0, 16, 32};
  const int tile_id = blockIdx.y * gridDim.x + blockIdx.x;
  __syncthreads();
  for (int c = 0; c < 4; ++c) {
    histogram[local] = 0;
    __syncthreads();
    if (x < width && y < height) {
      atomicAdd(histogram + ColorResidual(cache[local], coefficients[c]),
                1u);
    }
    __syncthreads();
    if (local == 0) {
      uint64_t sum = 0;
      for (int bin = 0; bin < 256; ++bin) {
        const unsigned int count = histogram[bin];
        sum += static_cast<uint64_t>(count) * count;
      }
      scores[tile_id * 4 + c] = sum;
    }
    __syncthreads();
  }
}

void ColorOracle(const std::vector<uint32_t>& pixels,
                 std::vector<uint64_t>* scores) {
  const int tiles_x = (kWidth + kTile - 1) / kTile;
  const int tiles_y = (kHeight + kTile - 1) / kTile;
  scores->assign(tiles_x * tiles_y * 4, 0);
  const int coefficients[4] = {-16, 0, 16, 32};
  for (int ty = 0; ty < tiles_y; ++ty) {
    for (int tx = 0; tx < tiles_x; ++tx) {
      for (int c = 0; c < 4; ++c) {
        uint32_t hist[256] = {0};
        for (int y = ty * kTile; y < std::min((ty + 1) * kTile, kHeight); ++y)
          for (int x = tx * kTile; x < std::min((tx + 1) * kTile, kWidth); ++x)
            ++hist[ColorResidual(pixels[y * kWidth + x], coefficients[c])];
        uint64_t score = 0;
        for (int i = 0; i < 256; ++i) score += uint64_t{hist[i]} * hist[i];
        (*scores)[(ty * tiles_x + tx) * 4 + c] = score;
      }
    }
  }
}

enum ColorVariant {
  kColorHistogramThroughput,
  kColorBaseline,
  kColorTileCache
};

uint64_t RunColor(ColorVariant variant, int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  const int tiles = ((kWidth + 15) / 16) * ((kHeight + 15) / 16);
  uint32_t* d_input = DeviceAlloc<uint32_t>(input.size());
  uint64_t* d_scores = DeviceAlloc<uint64_t>(tiles * 4);
  unsigned int* d_hist = nullptr;
  CUDA_CHECK(cudaMemcpy(d_input, input.data(), input.size() * sizeof(uint32_t),
                        cudaMemcpyHostToDevice));
  const dim3 grid((kWidth + 15) / 16, (kHeight + 15) / 16);
  for (int iter = 0; iter < iterations; ++iter) {
    if (variant != kColorTileCache) {
      if (d_hist == nullptr) d_hist = DeviceAlloc<unsigned int>(tiles * 4 * 256);
      CUDA_CHECK(cudaMemset(d_hist, 0, tiles * 4 * 256 * sizeof(unsigned int)));
      ColorBaselineKernel<<<grid, 256>>>(d_input, kWidth, kHeight, d_hist);
      if (variant == kColorBaseline) {
        ColorHistogramScoreKernel<<<(tiles * 4 + 127) / 128, 128>>>(
            d_hist, tiles * 4, d_scores);
      }
    } else {
      ColorSharedTileKernel<<<grid, 256>>>(d_input, kWidth, kHeight,
                                           d_scores);
    }
  }
  CUDA_CHECK(cudaGetLastError());
  CUDA_CHECK(cudaDeviceSynchronize());
  uint64_t checksum = 0;
  if (variant == kColorHistogramThroughput) {
    std::vector<unsigned int> got(tiles * 4 * 256);
    CUDA_CHECK(cudaMemcpy(got.data(), d_hist, got.size() * sizeof(got[0]),
                          cudaMemcpyDeviceToHost));
    std::vector<uint64_t> reduced(tiles * 4);
    for (int i = 0; i < tiles * 4; ++i)
      for (int b = 0; b < 256; ++b)
        reduced[i] += uint64_t{got[i * 256 + b]} * got[i * 256 + b];
    if (g_verify_outputs) {
      std::vector<uint64_t> expected;
      ColorOracle(input, &expected);
      *valid = reduced == expected;
    } else {
      *valid = true;
    }
    checksum = Checksum(got.data(), got.size() * sizeof(got[0]));
  } else {
    std::vector<uint64_t> got(tiles * 4);
    CUDA_CHECK(cudaMemcpy(got.data(), d_scores, got.size() * sizeof(got[0]),
                          cudaMemcpyDeviceToHost));
    if (g_verify_outputs) {
      std::vector<uint64_t> expected;
      ColorOracle(input, &expected);
      *valid = got == expected;
    } else {
      *valid = true;
    }
    checksum = Checksum(got.data(), got.size() * sizeof(got[0]));
  }
  DeviceFree(d_hist);
  DeviceFree(d_scores);
  DeviceFree(d_input);
  return checksum;
}

// -----------------------------------------------------------------------------
// Shared pixel transforms used by the context-pool and resident-pipeline cases.

__global__ void SubtractGreenKernel(uint32_t* pixels, int count) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i >= count) return;
  const uint32_t p = pixels[i];
  pixels[i] = Pack(Byte(p, 24), Byte(p, 16) - Byte(p, 8), Byte(p, 8),
                   Byte(p, 0) - Byte(p, 8));
}

__global__ void FixedColorKernel(uint32_t* pixels, int count) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i >= count) return;
  const uint32_t p = pixels[i];
  pixels[i] = Pack(Byte(p, 24), Byte(p, 16) - (Byte(p, 8) >> 1), Byte(p, 8),
                   Byte(p, 0) - (Byte(p, 16) >> 2));
}

uint32_t TransformOracle(uint32_t p) {
  p = Pack(Byte(p, 24), Byte(p, 16) - Byte(p, 8), Byte(p, 8),
           Byte(p, 0) - Byte(p, 8));
  return Pack(Byte(p, 24), Byte(p, 16) - (Byte(p, 8) >> 1), Byte(p, 8),
              Byte(p, 0) - (Byte(p, 16) >> 2));
}

// -----------------------------------------------------------------------------
// Predictor selection and residual generation.

__device__ __host__ uint32_t AveragePixel(uint32_t a, uint32_t b) {
  return (((a ^ b) & 0xfefefefeu) >> 1) + (a & b);
}

__device__ __host__ uint32_t PixelResidual(uint32_t p, uint32_t predictor) {
  return Pack(Byte(p, 24) - Byte(predictor, 24),
              Byte(p, 16) - Byte(predictor, 16),
              Byte(p, 8) - Byte(predictor, 8), Byte(p, 0) - Byte(predictor, 0));
}

__device__ __host__ unsigned int PixelSad(uint32_t p, uint32_t predictor) {
  int sum = 0;
  for (int shift = 0; shift < 32; shift += 8) {
    int d = int(Byte(p, shift)) - int(Byte(predictor, shift));
    sum += d < 0 ? -d : d;
  }
  return sum;
}

__global__ void PredictorKernel(const uint32_t* input, int width, int height,
                                uint8_t* modes, uint32_t* residuals) {
  __shared__ unsigned int costs[3];
  const int tile_x = blockIdx.x * kTile;
  const int tile_y = blockIdx.y * kTile;
  const int local = threadIdx.x;
  const int x = tile_x + local % kTile;
  const int y = tile_y + local / kTile;
  if (local < 3) costs[local] = 0;
  __syncthreads();
  uint32_t p = 0, pred[3] = {0xff000000u, 0xff000000u, 0xff000000u};
  if (x < width && y < height) {
    p = input[y * width + x];
    if (x > 0) pred[0] = input[y * width + x - 1];
    if (y > 0) pred[1] = input[(y - 1) * width + x];
    pred[2] = AveragePixel(pred[0], pred[1]);
    for (int m = 0; m < 3; ++m) atomicAdd(costs + m, PixelSad(p, pred[m]));
  }
  __syncthreads();
  int mode = 0;
  if (costs[1] < costs[mode]) mode = 1;
  if (costs[2] < costs[mode]) mode = 2;
  if (local == 0) modes[blockIdx.y * gridDim.x + blockIdx.x] = mode;
  if (x < width && y < height) residuals[y * width + x] = PixelResidual(p, pred[mode]);
}

void PredictorOracle(const std::vector<uint32_t>& input,
                     std::vector<uint8_t>* modes,
                     std::vector<uint32_t>* residuals) {
  const int tiles_x = (kWidth + 15) / 16, tiles_y = (kHeight + 15) / 16;
  modes->assign(tiles_x * tiles_y, 0);
  residuals->resize(input.size());
  for (int ty = 0; ty < tiles_y; ++ty) for (int tx = 0; tx < tiles_x; ++tx) {
    uint64_t costs[3] = {0, 0, 0};
    for (int y = ty * 16; y < std::min(ty * 16 + 16, kHeight); ++y)
      for (int x = tx * 16; x < std::min(tx * 16 + 16, kWidth); ++x) {
        const uint32_t p = input[y * kWidth + x];
        const uint32_t left = x ? input[y * kWidth + x - 1] : 0xff000000u;
        const uint32_t top = y ? input[(y - 1) * kWidth + x] : 0xff000000u;
        const uint32_t pred[3] = {left, top, AveragePixel(left, top)};
        for (int m = 0; m < 3; ++m) costs[m] += PixelSad(p, pred[m]);
      }
    int mode = 0;
    if (costs[1] < costs[mode]) mode = 1;
    if (costs[2] < costs[mode]) mode = 2;
    (*modes)[ty * tiles_x + tx] = mode;
    for (int y = ty * 16; y < std::min(ty * 16 + 16, kHeight); ++y)
      for (int x = tx * 16; x < std::min(tx * 16 + 16, kWidth); ++x) {
        const uint32_t p = input[y * kWidth + x];
        const uint32_t left = x ? input[y * kWidth + x - 1] : 0xff000000u;
        const uint32_t top = y ? input[(y - 1) * kWidth + x] : 0xff000000u;
        const uint32_t pred[3] = {left, top, AveragePixel(left, top)};
        (*residuals)[y * kWidth + x] = PixelResidual(p, pred[mode]);
      }
  }
}

uint64_t RunPredictorCPU(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  std::vector<uint32_t> residuals;
  std::vector<uint8_t> modes;
  for (int iter = 0; iter < iterations; ++iter)
    PredictorOracle(input, &modes, &residuals);
  *valid = !residuals.empty() && !modes.empty();
  return Checksum(residuals.data(), residuals.size() * sizeof(residuals[0])) ^
         Checksum(modes.data(), modes.size());
}

uint64_t RunPredictor(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  const int tiles = ((kWidth + 15) / 16) * ((kHeight + 15) / 16);
  uint32_t* d_input = DeviceAlloc<uint32_t>(input.size());
  uint32_t* d_residual = DeviceAlloc<uint32_t>(input.size());
  uint8_t* d_modes = DeviceAlloc<uint8_t>(tiles);
  CUDA_CHECK(cudaMemcpy(d_input, input.data(), input.size() * sizeof(uint32_t),
                        cudaMemcpyHostToDevice));
  for (int i = 0; i < iterations; ++i)
    PredictorKernel<<<dim3((kWidth + 15) / 16, (kHeight + 15) / 16), 256>>>(
        d_input, kWidth, kHeight, d_modes, d_residual);
  CUDA_CHECK(cudaDeviceSynchronize());
  std::vector<uint32_t> got(input.size());
  std::vector<uint8_t> modes(tiles);
  CUDA_CHECK(cudaMemcpy(got.data(), d_residual, got.size() * sizeof(got[0]),
                        cudaMemcpyDeviceToHost));
  CUDA_CHECK(cudaMemcpy(modes.data(), d_modes, modes.size(), cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<uint32_t> expected;
    std::vector<uint8_t> expected_modes;
    PredictorOracle(input, &expected_modes, &expected);
    *valid = got == expected && modes == expected_modes;
  } else {
    *valid = true;
  }
  const uint64_t result = Checksum(got.data(), got.size() * sizeof(got[0])) ^
                          Checksum(modes.data(), modes.size());
  DeviceFree(d_modes); DeviceFree(d_residual); DeviceFree(d_input);
  return result;
}

// -----------------------------------------------------------------------------
// Iterative SharpYUV-style 2x2 chroma correction. Fixed-point arithmetic keeps
// the CPU and GPU experiment bit-exact while preserving the iterative workload.

__device__ __host__ int Clamp8(int v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

__global__ void SharpYUVKernel(const uint32_t* rgb, int width, int height,
                               uint8_t* y_plane, uint8_t* u_plane,
                               uint8_t* v_plane) {
  const int bx = blockIdx.x * blockDim.x + threadIdx.x;
  const int by = blockIdx.y * blockDim.y + threadIdx.y;
  if (bx * 2 >= width || by * 2 >= height) return;
  int u = 0, v = 0;
  int target_r = 0, target_b = 0;
  for (int dy = 0; dy < 2; ++dy) for (int dx = 0; dx < 2; ++dx) {
    const int x = bx * 2 + dx, y = by * 2 + dy;
    const uint32_t p = rgb[y * width + x];
    const int r = Byte(p, 16), g = Byte(p, 8), b = Byte(p, 0);
    const int yy = (77 * r + 150 * g + 29 * b + 128) >> 8;
    y_plane[y * width + x] = yy;
    u += b - yy; v += r - yy; target_r += r; target_b += b;
  }
  u /= 4; v /= 4;
  for (int iter = 0; iter < 4; ++iter) {
    int recon_r = 0, recon_b = 0;
    for (int dy = 0; dy < 2; ++dy) for (int dx = 0; dx < 2; ++dx) {
      const int yy = y_plane[(by * 2 + dy) * width + bx * 2 + dx];
      recon_r += Clamp8(yy + v); recon_b += Clamp8(yy + u);
    }
    u += (target_b - recon_b) / 8;
    v += (target_r - recon_r) / 8;
  }
  const int uv_width = (width + 1) / 2;
  u_plane[by * uv_width + bx] = Clamp8(u + 128);
  v_plane[by * uv_width + bx] = Clamp8(v + 128);
}

void SharpYUVOracle(const std::vector<uint32_t>& input,
                    std::vector<uint8_t>* y, std::vector<uint8_t>* u,
                    std::vector<uint8_t>* v) {
  const int uv_width = (kWidth + 1) / 2;
  const int uv_height = (kHeight + 1) / 2;
  y->assign(input.size(), 0);
  u->assign(uv_width * uv_height, 0);
  v->assign(uv_width * uv_height, 0);
  for (int by = 0; by < kHeight / 2; ++by) {
    for (int bx = 0; bx < kWidth / 2; ++bx) {
      int uu = 0, vv = 0, target_r = 0, target_b = 0;
      for (int dy = 0; dy < 2; ++dy) {
        for (int dx = 0; dx < 2; ++dx) {
          const int pos = (by * 2 + dy) * kWidth + bx * 2 + dx;
          const uint32_t p = input[pos];
          const int r = Byte(p, 16), g = Byte(p, 8), b = Byte(p, 0);
          (*y)[pos] = (77 * r + 150 * g + 29 * b + 128) >> 8;
          uu += b - (*y)[pos];
          vv += r - (*y)[pos];
          target_r += r;
          target_b += b;
        }
      }
      uu /= 4;
      vv /= 4;
      for (int iter = 0; iter < 4; ++iter) {
        int recon_r = 0, recon_b = 0;
        for (int dy = 0; dy < 2; ++dy) {
          for (int dx = 0; dx < 2; ++dx) {
            const int yy = (*y)[(by * 2 + dy) * kWidth + bx * 2 + dx];
            recon_r += Clamp8(yy + vv);
            recon_b += Clamp8(yy + uu);
          }
        }
        uu += (target_b - recon_b) / 8;
        vv += (target_r - recon_r) / 8;
      }
      (*u)[by * uv_width + bx] = Clamp8(uu + 128);
      (*v)[by * uv_width + bx] = Clamp8(vv + 128);
    }
  }
}

uint64_t RunSharpYUVCPU(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  std::vector<uint8_t> y, u, v;
  for (int iter = 0; iter < iterations; ++iter) {
    SharpYUVOracle(input, &y, &u, &v);
  }
  *valid = !y.empty() && !u.empty() && !v.empty();
  return Checksum(y.data(), y.size()) ^ Checksum(u.data(), u.size()) ^
         Checksum(v.data(), v.size());
}

uint64_t RunSharpYUV(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  const int uv_size = ((kWidth + 1) / 2) * ((kHeight + 1) / 2);
  uint32_t* d_input = DeviceAlloc<uint32_t>(input.size());
  uint8_t* d_y = DeviceAlloc<uint8_t>(input.size());
  uint8_t* d_u = DeviceAlloc<uint8_t>(uv_size);
  uint8_t* d_v = DeviceAlloc<uint8_t>(uv_size);
  CUDA_CHECK(cudaMemcpy(d_input, input.data(), input.size() * sizeof(input[0]), cudaMemcpyHostToDevice));
  for (int i = 0; i < iterations; ++i)
    SharpYUVKernel<<<dim3((kWidth + 31) / 32, (kHeight + 15) / 16), dim3(16, 8)>>>(
        d_input, kWidth, kHeight, d_y, d_u, d_v);
  CUDA_CHECK(cudaDeviceSynchronize());
  std::vector<uint8_t> y(input.size()), u(uv_size), v(uv_size);
  CUDA_CHECK(cudaMemcpy(y.data(), d_y, y.size(), cudaMemcpyDeviceToHost));
  CUDA_CHECK(cudaMemcpy(u.data(), d_u, u.size(), cudaMemcpyDeviceToHost));
  CUDA_CHECK(cudaMemcpy(v.data(), d_v, v.size(), cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<uint8_t> ey, eu, ev;
    SharpYUVOracle(input, &ey, &eu, &ev);
    *valid = y == ey && u == eu && v == ev;
  } else {
    *valid = true;
  }
  const uint64_t result = Checksum(y.data(), y.size()) ^ Checksum(u.data(), u.size()) ^ Checksum(v.data(), v.size());
  DeviceFree(d_v); DeviceFree(d_u); DeviceFree(d_y); DeviceFree(d_input); return result;
}

// -----------------------------------------------------------------------------
// Near-lossless preprocessing: repeated four-neighbor stencil.

__device__ __host__ uint8_t QuantizeNear(uint8_t value, int step) {
  return static_cast<uint8_t>(Clamp8(((int(value) + step / 2) / step) * step));
}

__global__ void NearLosslessKernel(const uint32_t* src, uint32_t* dst,
                                   int width, int height, int step) {
  const int x = blockIdx.x * blockDim.x + threadIdx.x;
  const int y = blockIdx.y * blockDim.y + threadIdx.y;
  if (x >= width || y >= height) return;
  const int pos = y * width + x;
  if (x == 0 || y == 0 || x + 1 == width || y + 1 == height) { dst[pos] = src[pos]; return; }
  const uint32_t p = src[pos], n[4] = {src[pos - 1], src[pos + 1], src[pos - width], src[pos + width]};
  uint8_t channels[4];
  for (int c = 0; c < 4; ++c) {
    const int shift = c * 8; bool smooth = true;
    for (int j = 0; j < 4; ++j) {
      int d = int(Byte(p, shift)) - int(Byte(n[j], shift)); if (d < 0) d = -d;
      if (d > step) smooth = false;
    }
    channels[c] = smooth ? QuantizeNear(Byte(p, shift), step) : Byte(p, shift);
  }
  dst[pos] = Pack(channels[3], channels[2], channels[1], channels[0]);
}

void NearOracle(std::vector<uint32_t>* pixels) {
  std::vector<uint32_t> next(pixels->size());
  for (int pass = 0; pass < 3; ++pass) {
    for (int y = 0; y < kHeight; ++y) for (int x = 0; x < kWidth; ++x) {
      const int pos = y * kWidth + x;
      if (x == 0 || y == 0 || x + 1 == kWidth || y + 1 == kHeight) { next[pos] = (*pixels)[pos]; continue; }
      const uint32_t p = (*pixels)[pos], n[4] = {(*pixels)[pos - 1], (*pixels)[pos + 1], (*pixels)[pos - kWidth], (*pixels)[pos + kWidth]};
      uint8_t ch[4];
      for (int c = 0; c < 4; ++c) { bool smooth = true;
        for (int j = 0; j < 4; ++j) { int d = int(Byte(p, c * 8)) - int(Byte(n[j], c * 8)); if (d < 0) d = -d; if (d > 8) smooth = false; }
        ch[c] = smooth ? QuantizeNear(Byte(p, c * 8), 8) : Byte(p, c * 8);
      }
      next[pos] = Pack(ch[3], ch[2], ch[1], ch[0]);
    }
    pixels->swap(next);
  }
}

uint64_t RunNearLosslessCPU(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  std::vector<uint32_t> output;
  for (int iter = 0; iter < iterations; ++iter) {
    output = input;
    NearOracle(&output);
  }
  *valid = !output.empty();
  return Checksum(output.data(), output.size() * sizeof(output[0]));
}

uint64_t RunNearLossless(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  uint32_t* a = DeviceAlloc<uint32_t>(input.size()), *b = DeviceAlloc<uint32_t>(input.size());
  for (int iter = 0; iter < iterations; ++iter) {
    CUDA_CHECK(cudaMemcpy(a, input.data(), input.size() * sizeof(input[0]), cudaMemcpyHostToDevice));
    for (int pass = 0; pass < 3; ++pass) { NearLosslessKernel<<<dim3((kWidth + 15) / 16, (kHeight + 15) / 16), dim3(16, 16)>>>(a, b, kWidth, kHeight, 8); std::swap(a, b); }
  }
  CUDA_CHECK(cudaDeviceSynchronize());
  std::vector<uint32_t> got(input.size());
  CUDA_CHECK(cudaMemcpy(got.data(), a, got.size() * sizeof(got[0]), cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<uint32_t> expected = input;
    NearOracle(&expected);
    *valid = got == expected;
  } else {
    *valid = true;
  }
  const uint64_t result = Checksum(got.data(), got.size() * sizeof(got[0]));
  DeviceFree(b); DeviceFree(a); return result;
}

// -----------------------------------------------------------------------------
// Lossless token histogram construction.

struct Token { uint16_t literal, red, blue, alpha, distance; };

std::vector<Token> MakeTokens(int count) {
  std::vector<Token> tokens(count);
  for (int i = 0; i < count; ++i) {
    const uint32_t v = Mix(i);
    tokens[i] = {uint16_t(v & 255), uint16_t(v >> 8 & 255),
                 uint16_t(v >> 16 & 255), uint16_t(v >> 24),
                 uint16_t(v % 256)};
  }
  return tokens;
}

__global__ void HistogramKernel(const Token* tokens, int count, uint32_t* hist) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x; if (i >= count) return;
  const Token t = tokens[i];
  atomicAdd(hist + t.literal, 1u); atomicAdd(hist + 256 + t.red, 1u);
  atomicAdd(hist + 512 + t.blue, 1u); atomicAdd(hist + 768 + t.alpha, 1u);
  atomicAdd(hist + 1024 + t.distance, 1u);
}

uint64_t RunHistogram(int iterations, bool* valid) {
  constexpr int count = 1 << 20, bins = 1280;
  const std::vector<Token> tokens = MakeTokens(count);
  Token* d_tokens = DeviceAlloc<Token>(count); uint32_t* d_hist = DeviceAlloc<uint32_t>(bins);
  CUDA_CHECK(cudaMemcpy(d_tokens, tokens.data(), tokens.size() * sizeof(tokens[0]), cudaMemcpyHostToDevice));
  for (int iter = 0; iter < iterations; ++iter) { CUDA_CHECK(cudaMemset(d_hist, 0, bins * sizeof(uint32_t))); HistogramKernel<<<(count + 255) / 256, 256>>>(d_tokens, count, d_hist); }
  CUDA_CHECK(cudaDeviceSynchronize()); std::vector<uint32_t> got(bins);
  CUDA_CHECK(cudaMemcpy(got.data(), d_hist, bins * sizeof(uint32_t), cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<uint32_t> expected(bins);
    for (const Token& t : tokens) { ++expected[t.literal]; ++expected[256 + t.red]; ++expected[512 + t.blue]; ++expected[768 + t.alpha]; ++expected[1024 + t.distance]; }
    *valid = got == expected;
  } else {
    *valid = true;
  }
  const uint64_t result = Checksum(got.data(), got.size() * sizeof(got[0])); DeviceFree(d_hist); DeviceFree(d_tokens); return result;
}

uint64_t RunHistogramCPU(int iterations, bool* valid) {
  constexpr int count = 1 << 20, bins = 1280;
  const std::vector<Token> tokens = MakeTokens(count);
  std::vector<uint32_t> histogram(bins);
  for (int iter = 0; iter < iterations; ++iter) {
    std::fill(histogram.begin(), histogram.end(), 0u);
    for (const Token& t : tokens) {
      ++histogram[t.literal];
      ++histogram[256 + t.red];
      ++histogram[512 + t.blue];
      ++histogram[768 + t.alpha];
      ++histogram[1024 + t.distance];
    }
  }
  *valid = !histogram.empty();
  return Checksum(histogram.data(), histogram.size() * sizeof(histogram[0]));
}

// -----------------------------------------------------------------------------
// Batched lossy intra16 candidate scoring.

__global__ void LossyScoreKernel(const uint8_t* y, int width, int height,
                                 unsigned long long* scores) {
  __shared__ unsigned long long local[4];
  const int tx = threadIdx.x & 15, ty = threadIdx.x >> 4;
  const int x = blockIdx.x * 16 + tx, py = blockIdx.y * 16 + ty;
  if (threadIdx.x < 4) local[threadIdx.x] = 0; __syncthreads();
  if (x < width && py < height) {
    const int actual = y[py * width + x];
    const int top = blockIdx.y ? y[(blockIdx.y * 16 - 1) * width + x] : 127;
    const int left = blockIdx.x ? y[py * width + blockIdx.x * 16 - 1] : 127;
    const int dc = (top + left) / 2;
    const int pred[4] = {dc, top, left, Clamp8(top + left - 127)};
    for (int m = 0; m < 4; ++m) { const int d = actual - pred[m]; atomicAdd(local + m, static_cast<unsigned long long>(d * d)); }
  }
  __syncthreads(); if (threadIdx.x < 4) scores[(blockIdx.y * gridDim.x + blockIdx.x) * 4 + threadIdx.x] = local[threadIdx.x];
}

std::vector<uint8_t> MakeLuma() {
  std::vector<uint8_t> y(kPixels);
  for (int i = 0; i < kPixels; ++i) y[i] = Mix(i) & 255;
  return y;
}

void LossyScoreOracle(const std::vector<uint8_t>& y,
                      std::vector<unsigned long long>* scores) {
  const int blocks_x = (kWidth + 15) / 16;
  const int blocks_y = (kHeight + 15) / 16;
  scores->assign(blocks_x * blocks_y * 4, 0);
  for (int my = 0; my < blocks_y; ++my) {
    for (int mx = 0; mx < blocks_x; ++mx) {
      for (int yy = 0; yy < 16; ++yy) {
        for (int xx = 0; xx < 16; ++xx) {
          const int x = mx * 16 + xx, py = my * 16 + yy;
          if (x >= kWidth || py >= kHeight) continue;
          const int actual = y[py * kWidth + x];
          const int top =
              my ? y[(my * 16 - 1) * kWidth + x] : 127;
          const int left =
              mx ? y[py * kWidth + mx * 16 - 1] : 127;
          const int dc = (top + left) / 2;
          const int pred[4] = {dc, top, left, Clamp8(top + left - 127)};
          for (int mode = 0; mode < 4; ++mode) {
            const int delta = actual - pred[mode];
            (*scores)[(my * blocks_x + mx) * 4 + mode] += delta * delta;
          }
        }
      }
    }
  }
}

uint64_t RunLossyScoreCPU(int iterations, bool* valid) {
  const std::vector<uint8_t> y = MakeLuma();
  std::vector<unsigned long long> scores;
  for (int iter = 0; iter < iterations; ++iter) {
    LossyScoreOracle(y, &scores);
  }
  *valid = !scores.empty();
  return Checksum(scores.data(), scores.size() * sizeof(scores[0]));
}

uint64_t RunLossyScore(int iterations, bool* valid) {
  const std::vector<uint8_t> y = MakeLuma();
  const int bx = (kWidth + 15) / 16;
  const int by = (kHeight + 15) / 16;
  const int count = bx * by * 4;
  uint8_t* d_y = DeviceAlloc<uint8_t>(y.size());
  unsigned long long* d_scores =
      DeviceAlloc<unsigned long long>(count);
  CUDA_CHECK(cudaMemcpy(d_y, y.data(), y.size(), cudaMemcpyHostToDevice));
  for (int i = 0; i < iterations; ++i) {
    LossyScoreKernel<<<dim3(bx, by), 256>>>(d_y, kWidth, kHeight,
                                            d_scores);
  }
  CUDA_CHECK(cudaDeviceSynchronize());
  std::vector<unsigned long long> got(count);
  CUDA_CHECK(cudaMemcpy(got.data(), d_scores, count * sizeof(got[0]),
                        cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<unsigned long long> expected;
    LossyScoreOracle(y, &expected);
    *valid = got == expected;
  } else {
    *valid = true;
  }
  const uint64_t result =
      Checksum(got.data(), got.size() * sizeof(got[0]));
  DeviceFree(d_scores);
  DeviceFree(d_y);
  return result;
}

// -----------------------------------------------------------------------------
// Device-resident lossless pipeline. Only the initial upload and final download
// cross PCIe; predictor, transforms, and candidate signature stay on device.

__global__ void PredictorResidualFixedKernel(const uint32_t* input,
                                             uint32_t* residuals, int width,
                                             int count) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x; if (i >= count) return;
  const uint32_t predictor = (i % width) ? input[i - 1] : 0xff000000u;
  residuals[i] = PixelResidual(input[i], predictor);
}

__global__ void SignatureKernel(const uint32_t* pixels, int count, uint32_t* signatures) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x; if (i >= count) return;
  const uint32_t previous = i ? pixels[i - 1] : 0; signatures[i] = (pixels[i] * 0x1e35a7bdu) ^ previous;
}

uint64_t RunResidentPipeline(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  uint32_t* d_input = DeviceAlloc<uint32_t>(input.size());
  uint32_t* d_pixels = DeviceAlloc<uint32_t>(input.size());
  uint32_t* d_sig = DeviceAlloc<uint32_t>(input.size());
  for (int iter = 0; iter < iterations; ++iter) {
    CUDA_CHECK(cudaMemcpy(d_input, input.data(), input.size() * sizeof(input[0]), cudaMemcpyHostToDevice));
    PredictorResidualFixedKernel<<<(kPixels + 255) / 256, 256>>>(d_input, d_pixels, kWidth, kPixels);
    SubtractGreenKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels);
    FixedColorKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels);
    SignatureKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels, d_sig);
  }
  CUDA_CHECK(cudaDeviceSynchronize()); std::vector<uint32_t> got(input.size());
  CUDA_CHECK(cudaMemcpy(got.data(), d_sig, got.size() * sizeof(got[0]), cudaMemcpyDeviceToHost));
  if (g_verify_outputs) {
    std::vector<uint32_t> expected(input.size()), transformed(input.size());
    for (int i = 0; i < kPixels; ++i) { const uint32_t pred = (i % kWidth) ? input[i - 1] : 0xff000000u; transformed[i] = TransformOracle(PixelResidual(input[i], pred)); expected[i] = transformed[i] * 0x1e35a7bdu ^ (i ? transformed[i - 1] : 0); }
    *valid = got == expected;
  } else {
    *valid = true;
  }
  const uint64_t result = Checksum(got.data(), got.size() * sizeof(got[0])); DeviceFree(d_sig); DeviceFree(d_pixels); DeviceFree(d_input); return result;
}

uint64_t RunStagedLosslessPipeline(int iterations, bool* valid) {
  const std::vector<uint32_t> input = MakePixels();
  std::vector<uint32_t> staging(input.size()), got(input.size());
  uint32_t* d_input = DeviceAlloc<uint32_t>(input.size());
  uint32_t* d_pixels = DeviceAlloc<uint32_t>(input.size());
  uint32_t* d_sig = DeviceAlloc<uint32_t>(input.size());
  const size_t bytes = input.size() * sizeof(input[0]);
  for (int iter = 0; iter < iterations; ++iter) {
    CUDA_CHECK(cudaMemcpy(d_input, input.data(), bytes, cudaMemcpyHostToDevice));
    PredictorResidualFixedKernel<<<(kPixels + 255) / 256, 256>>>(
        d_input, d_pixels, kWidth, kPixels);
    CUDA_CHECK(cudaMemcpy(staging.data(), d_pixels, bytes,
                          cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(d_pixels, staging.data(), bytes,
                          cudaMemcpyHostToDevice));
    SubtractGreenKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels);
    CUDA_CHECK(cudaMemcpy(staging.data(), d_pixels, bytes,
                          cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(d_pixels, staging.data(), bytes,
                          cudaMemcpyHostToDevice));
    FixedColorKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels);
    CUDA_CHECK(cudaMemcpy(staging.data(), d_pixels, bytes,
                          cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(d_pixels, staging.data(), bytes,
                          cudaMemcpyHostToDevice));
    SignatureKernel<<<(kPixels + 255) / 256, 256>>>(d_pixels, kPixels, d_sig);
    CUDA_CHECK(cudaMemcpy(got.data(), d_sig, bytes, cudaMemcpyDeviceToHost));
  }
  *valid = true;
  if (g_verify_outputs) {
    std::vector<uint32_t> expected(input.size()), transformed(input.size());
    for (int i = 0; i < kPixels; ++i) {
      const uint32_t pred =
          (i % kWidth) ? input[i - 1] : 0xff000000u;
      transformed[i] = TransformOracle(PixelResidual(input[i], pred));
      expected[i] = transformed[i] * 0x1e35a7bdu ^
                    (i ? transformed[i - 1] : 0);
    }
    *valid = got == expected;
  }
  const uint64_t result =
      Checksum(got.data(), got.size() * sizeof(got[0]));
  DeviceFree(d_sig);
  DeviceFree(d_pixels);
  DeviceFree(d_input);
  return result;
}

struct Experiment {
  const char* name;
  uint64_t (*run)(int, bool*);
};

uint64_t ColorHistogramThroughput(int n, bool* ok) {
  return RunColor(kColorHistogramThroughput, n, ok);
}
uint64_t ColorBaseline(int n, bool* ok) {
  return RunColor(kColorBaseline, n, ok);
}
uint64_t ColorTile(int n, bool* ok) {
  return RunColor(kColorTileCache, n, ok);
}

const Experiment kExperiments[] = {
    {"color_histogram_throughput", ColorHistogramThroughput},
    {"color_baseline", ColorBaseline},
    {"color_shared_tile", ColorTile},
    {"staged_lossless_pipeline", RunStagedLosslessPipeline},
    {"resident_lossless_pipeline", RunResidentPipeline},
    {"predictor_search_residual_cpu", RunPredictorCPU},
    {"predictor_search_residual", RunPredictor},
    {"sharpyuv_iterative_cpu", RunSharpYUVCPU},
    {"sharpyuv_iterative", RunSharpYUV},
    {"near_lossless_stencil_cpu", RunNearLosslessCPU},
    {"near_lossless_stencil", RunNearLossless},
    {"lossless_histogram_cpu", RunHistogramCPU},
    {"lossless_histogram", RunHistogram},
    {"lossy_macroblock_scoring_cpu", RunLossyScoreCPU},
    {"lossy_macroblock_scoring", RunLossyScore},
};

}  // namespace

int main(int argc, char** argv) {
  bool benchmark = false, list = false;
  int iterations = 20;
  std::string selected = "all";
  for (int i = 1; i < argc; ++i) {
    if (!std::strcmp(argv[i], "--benchmark")) benchmark = true;
    else if (!std::strcmp(argv[i], "--verify")) benchmark = false;
    else if (!std::strcmp(argv[i], "--list")) list = true;
    else if (!std::strcmp(argv[i], "--experiment") && i + 1 < argc) selected = argv[++i];
    else if (!std::strcmp(argv[i], "--iterations") && i + 1 < argc) iterations = std::max(1, std::atoi(argv[++i]));
    else { std::fprintf(stderr, "usage: %s [--verify|--benchmark] [--experiment NAME|all] [--iterations N] [--list]\n", argv[0]); return 2; }
  }
  if (list) { for (const Experiment& experiment : kExperiments) std::puts(experiment.name); return 0; }
  cudaDeviceProp properties;
  CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));
  std::fprintf(stderr, "device=%s mode=%s iterations=%d\n", properties.name, benchmark ? "benchmark" : "verify", benchmark ? iterations : 1);
  if (benchmark) std::puts("experiment,iterations,total_ms,ms_per_iteration,checksum");
  bool any = false, all_valid = true;
  for (const Experiment& experiment : kExperiments) {
    if (selected != "all" && selected != experiment.name) continue;
    any = true; bool valid = false;
    if (benchmark) {
      g_verify_outputs = true;
      (void)experiment.run(1, &valid);
      if (!valid) {
        std::fprintf(stderr, "correctness preflight failed: %s\n",
                     experiment.name);
        all_valid = false;
        continue;
      }
      g_verify_outputs = false;
    }
    const auto start = std::chrono::steady_clock::now();
    const uint64_t checksum = experiment.run(benchmark ? iterations : 1, &valid);
    const auto stop = std::chrono::steady_clock::now();
    const double milliseconds = std::chrono::duration<double, std::milli>(stop - start).count();
    if (benchmark) std::printf("%s,%d,%.6f,%.6f,%016llx\n", experiment.name, iterations, milliseconds, milliseconds / iterations, static_cast<unsigned long long>(checksum));
    else std::printf("%-31s %s checksum=%016llx\n", experiment.name, valid ? "PASS" : "FAIL", static_cast<unsigned long long>(checksum));
    if (!valid) all_valid = false;
  }
  g_verify_outputs = true;
  if (!any) { std::fprintf(stderr, "unknown experiment: %s\n", selected.c_str()); return 2; }
  return all_valid ? 0 : 1;
}
