// Copyright 2026
//
// Metal implementation of libwebp's opaque RGB/BGR to YUV420 conversion.
// The integer conversion and gamma lookup/interpolation match
// ImportYUVAFromRGBA() byte-for-byte.

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <new>

extern "C" {
#include "src/enc/metal_enc.h"
}

namespace {

// Runtime shader compilation costs roughly 25 ms on the benchmark M4 Max.
// A cold, one-shot conversion crosses over near 70 MP, so default to a
// conservative 80 MP. Persistent/batch encoders should set the threshold to 0.
constexpr size_t kDefaultMinimumPixels = 80u * 1000u * 1000u;
constexpr NSUInteger kPreferredThreads = 256;
constexpr size_t kBufferOffsetAlignment = 256u;

constexpr const char* kMetalSource = R"METAL(
#include <metal_stdlib>
using namespace metal;

constant bool kLossyBlock2x2 [[function_constant(0)]];

struct Params {
  uint width;
  uint height;
  uint step;
  uint source_stride;
  uint red_offset;
  uint green_offset;
  uint blue_offset;
  uint uv_width;
  uint y_size;
  uint uv_size;
};

inline uchar rgb_to_y(int r, int g, int b) {
  const int luma = 16839 * r + 33059 * g + 6420 * b;
  return uchar((luma + 32768 + (16 << 16)) >> 16);
}

inline uchar clip_uv(int value) {
  value = (value + (32768 << 2) + (128 << 18)) >> 18;
  return uchar(clamp(value, 0, 255));
}

inline uchar rgb_to_u(int r, int g, int b) {
  return clip_uv(-9719 * r - 19081 * g + 28800 * b);
}

inline uchar rgb_to_v(int r, int g, int b) {
  return clip_uv(28800 * r - 24116 * g - 4684 * b);
}

inline int interpolate_gamma(uint value, device const int* linear_to_gamma) {
  const uint table_position = value >> 9;
  const uint fraction = value & 511u;
  const int v0 = linear_to_gamma[table_position];
  const int v1 = linear_to_gamma[table_position + 1u];
  const int interpolated = v1 * int(fraction) +
                           v0 * int(512u - fraction);
  return (interpolated + 64) >> 7;
}

inline uint source_index(uint x, uint y, constant Params& params) {
  return y * params.source_stride + x * params.step;
}

kernel void rgb_to_yuv420(
    device const uchar* source [[buffer(0)]],
    device uchar* output [[buffer(1)]],
    device const ushort* gamma_to_linear [[buffer(2)]],
    device const int* linear_to_gamma [[buffer(3)]],
    constant Params& params [[buffer(4)]],
    uint2 position [[thread_position_in_grid]]) {
  if (kLossyBlock2x2) {
    const uint uv_x = position.x;
    const uint uv_y = position.y;
    const uint uv_height = (params.height + 1u) >> 1;
    if (uv_x >= params.uv_width || uv_y >= uv_height) return;

    const uint x0 = uv_x << 1;
    const uint y0 = uv_y << 1;
    const uint x1 = min(x0 + 1u, params.width - 1u);
    const uint y1 = min(y0 + 1u, params.height - 1u);
    const uint p00 = source_index(x0, y0, params);
    const uint p01 = source_index(x1, y0, params);
    const uint p10 = source_index(x0, y1, params);
    const uint p11 = source_index(x1, y1, params);

    const int r00 = source[p00 + params.red_offset];
    const int g00 = source[p00 + params.green_offset];
    const int b00 = source[p00 + params.blue_offset];
    const int r01 = source[p01 + params.red_offset];
    const int g01 = source[p01 + params.green_offset];
    const int b01 = source[p01 + params.blue_offset];
    const int r10 = source[p10 + params.red_offset];
    const int g10 = source[p10 + params.green_offset];
    const int b10 = source[p10 + params.blue_offset];
    const int r11 = source[p11 + params.red_offset];
    const int g11 = source[p11 + params.green_offset];
    const int b11 = source[p11 + params.blue_offset];

    output[y0 * params.width + x0] = rgb_to_y(r00, g00, b00);
    if (x1 != x0) {
      output[y0 * params.width + x1] = rgb_to_y(r01, g01, b01);
    }
    if (y1 != y0) {
      output[y1 * params.width + x0] = rgb_to_y(r10, g10, b10);
      if (x1 != x0) {
        output[y1 * params.width + x1] = rgb_to_y(r11, g11, b11);
      }
    }

    const uint red_linear = uint(gamma_to_linear[r00]) +
        uint(gamma_to_linear[r01]) + uint(gamma_to_linear[r10]) +
        uint(gamma_to_linear[r11]);
    const uint green_linear = uint(gamma_to_linear[g00]) +
        uint(gamma_to_linear[g01]) + uint(gamma_to_linear[g10]) +
        uint(gamma_to_linear[g11]);
    const uint blue_linear = uint(gamma_to_linear[b00]) +
        uint(gamma_to_linear[b01]) + uint(gamma_to_linear[b10]) +
        uint(gamma_to_linear[b11]);
    const int red = interpolate_gamma(red_linear, linear_to_gamma);
    const int green = interpolate_gamma(green_linear, linear_to_gamma);
    const int blue = interpolate_gamma(blue_linear, linear_to_gamma);
    const uint uv_index = uv_y * params.uv_width + uv_x;
    output[params.y_size + uv_index] = rgb_to_u(red, green, blue);
    output[params.y_size + params.uv_size + uv_index] =
        rgb_to_v(red, green, blue);
    return;
  }

  const uint index = position.x;
  const uint pixel_count = params.width * params.height;
  if (index < pixel_count) {
    const uint x = index % params.width;
    const uint y = index / params.width;
    const uint offset = source_index(x, y, params);
    output[index] = rgb_to_y(source[offset + params.red_offset],
                             source[offset + params.green_offset],
                             source[offset + params.blue_offset]);
  }

  const uint uv_height = (params.height + 1u) >> 1;
  const uint uv_count = params.uv_width * uv_height;
  if (index < uv_count) {
    const uint uv_x = index % params.uv_width;
    const uint uv_y = index / params.uv_width;
    const uint x0 = uv_x << 1;
    const uint y0 = uv_y << 1;
    const uint x1 = min(x0 + 1u, params.width - 1u);
    const uint y1 = min(y0 + 1u, params.height - 1u);
    const uint p00 = source_index(x0, y0, params);
    const uint p01 = source_index(x1, y0, params);
    const uint p10 = source_index(x0, y1, params);
    const uint p11 = source_index(x1, y1, params);

    const uint red_linear =
        uint(gamma_to_linear[source[p00 + params.red_offset]]) +
        uint(gamma_to_linear[source[p01 + params.red_offset]]) +
        uint(gamma_to_linear[source[p10 + params.red_offset]]) +
        uint(gamma_to_linear[source[p11 + params.red_offset]]);
    const uint green_linear =
        uint(gamma_to_linear[source[p00 + params.green_offset]]) +
        uint(gamma_to_linear[source[p01 + params.green_offset]]) +
        uint(gamma_to_linear[source[p10 + params.green_offset]]) +
        uint(gamma_to_linear[source[p11 + params.green_offset]]);
    const uint blue_linear =
        uint(gamma_to_linear[source[p00 + params.blue_offset]]) +
        uint(gamma_to_linear[source[p01 + params.blue_offset]]) +
        uint(gamma_to_linear[source[p10 + params.blue_offset]]) +
        uint(gamma_to_linear[source[p11 + params.blue_offset]]);

    const int red = interpolate_gamma(red_linear, linear_to_gamma);
    const int green = interpolate_gamma(green_linear, linear_to_gamma);
    const int blue = interpolate_gamma(blue_linear, linear_to_gamma);
    output[params.y_size + index] = rgb_to_u(red, green, blue);
    output[params.y_size + params.uv_size + index] =
        rgb_to_v(red, green, blue);
  }
}
)METAL";

struct KernelParams {
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
};

struct MetalState {
  id<MTLDevice> device = nil;
  id<MTLCommandQueue> queue = nil;
  id<MTLComputePipelineState> pipeline = nil;
  id<MTLBuffer> source = nil;
  id<MTLBuffer> output = nil;
  id<MTLBuffer> gamma_to_linear = nil;
  id<MTLBuffer> linear_to_gamma = nil;
  size_t source_capacity = 0;
  size_t output_capacity = 0;
  bool block_2x2 = false;
  bool write_combined_inputs = false;
  bool unretained_command_buffers = false;
  bool contiguous_copy = false;
  NSUInteger threads = kPreferredThreads;
  std::mutex mutex;

  ~MetalState() {
#if !__has_feature(objc_arc)
    [linear_to_gamma release];
    [gamma_to_linear release];
    [output release];
    [source release];
    [pipeline release];
    [queue release];
    [device release];
#endif
  }
};

bool EnvironmentFlag(const char* name, bool default_value) {
  const char* value = std::getenv(name);
  if (value == nullptr || value[0] == '\0') return default_value;
  return std::strcmp(value, "0") != 0 && strcasecmp(value, "false") != 0 &&
         strcasecmp(value, "no") != 0;
}

size_t EnvironmentSize(const char* name, size_t default_value) {
  const char* value = std::getenv(name);
  if (value == nullptr || value[0] == '\0') return default_value;
  errno = 0;
  char* end = nullptr;
  const unsigned long long parsed = std::strtoull(value, &end, 10);
  if (errno != 0 || end == value || *end != '\0') return default_value;
  return static_cast<size_t>(parsed);
}

NSUInteger ThreadgroupSize(const char* name,
                           id<MTLComputePipelineState> pipeline) {
  size_t requested = EnvironmentSize(name, kPreferredThreads);
  if (requested == 0u) requested = kPreferredThreads;
  return static_cast<NSUInteger>(std::min(
      requested, static_cast<size_t>(pipeline.maxTotalThreadsPerThreadgroup)));
}

MTLResourceOptions SharedBufferOptions(bool write_combined) {
  return MTLResourceStorageModeShared |
      (write_combined ? MTLResourceCPUCacheModeWriteCombined
                      : MTLResourceCPUCacheModeDefaultCache);
}

id<MTLCommandBuffer> NewCommandBuffer(MetalState* state) {
  return state->unretained_command_buffers
      ? [state->queue commandBufferWithUnretainedReferences]
      : [state->queue commandBuffer];
}

bool AblationExperimentEnabled() {
  const char* const value = std::getenv("WEBP_METAL_ABLATION_EXPERIMENT");
#if defined(WEBP_USE_METAL_ABLATION_EXPERIMENT)
  return value != nullptr && std::strcmp(value, "1") == 0;
#else
  if (value != nullptr && std::strcmp(value, "1") == 0) {
    std::fprintf(stderr,
                 "WebP-Metal: ignoring ablation opt-in; rebuild with "
                 "WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1\n");
  }
  return false;
#endif
}

bool RoundedBufferLength(size_t length, size_t* rounded_length) {
  constexpr size_t kPage = 16u * 1024u;
  if (length > std::numeric_limits<size_t>::max() - (kPage - 1u)) {
    return false;
  }
  *rounded_length =
      std::max(kPage, (length + kPage - 1u) & ~(kPage - 1u));
  return true;
}

void BuildGammaTables(uint16_t gamma_to_linear[256],
                      int32_t linear_to_gamma[33]) {
  constexpr double kGamma = 0.80;
  constexpr int kGammaFix = 12;
  constexpr int kGammaTabFix = 7;
  constexpr int kGammaScale = (1 << kGammaFix) - 1;
  constexpr int kGammaTabSize = 1 << (kGammaFix - kGammaTabFix);
  const double scale = static_cast<double>(1 << kGammaTabFix) / kGammaScale;
  for (int value = 0; value <= 255; ++value) {
    gamma_to_linear[value] = static_cast<uint16_t>(
        std::pow(value / 255.0, kGamma) * kGammaScale + 0.5);
  }
  for (int value = 0; value <= kGammaTabSize; ++value) {
    linear_to_gamma[value] = static_cast<int32_t>(
        255.0 * std::pow(scale * value, 1.0 / kGamma) + 0.5);
  }
}

MetalState* InitializeState() {
  if (!EnvironmentFlag("WEBP_METAL_LOSSY", true)) return nullptr;
  @autoreleasepool {
    auto* state = new MetalState();
    const bool ablation_experiment = AblationExperimentEnabled();
    if (ablation_experiment) {
      state->block_2x2 = EnvironmentFlag("WEBP_METAL_LOSSY_BLOCK_2X2", false);
      state->write_combined_inputs = EnvironmentFlag(
          "WEBP_METAL_WRITE_COMBINED_INPUTS", false);
      state->unretained_command_buffers = EnvironmentFlag(
          "WEBP_METAL_LOSSY_UNRETAINED_COMMAND_BUFFERS", false);
      state->contiguous_copy = EnvironmentFlag(
          "WEBP_METAL_LOSSY_CONTIGUOUS_COPY", false);
    }
    state->device = MTLCreateSystemDefaultDevice();
    if (state->device == nil) {
      delete state;
      return nullptr;
    }
    NSError* error = nil;
    id<MTLLibrary> library = [state->device
        newLibraryWithSource:[NSString stringWithUTF8String:kMetalSource]
                     options:nil error:&error];
    if (library == nil) {
      if (EnvironmentFlag("WEBP_METAL_VERBOSE", false)) {
        std::fprintf(stderr, "WebP-Metal: lossy library failed: %s\n",
                     error.localizedDescription.UTF8String);
      }
      delete state;
      return nullptr;
    }
    MTLFunctionConstantValues* constants =
        [[MTLFunctionConstantValues alloc] init];
    bool block_2x2 = state->block_2x2;
    [constants setConstantValue:&block_2x2 type:MTLDataTypeBool atIndex:0];
    id<MTLFunction> function = [library
        newFunctionWithName:@"rgb_to_yuv420"
             constantValues:constants error:&error];
#if !__has_feature(objc_arc)
    [constants release];
#endif
    if (function == nil) {
      if (EnvironmentFlag("WEBP_METAL_VERBOSE", false)) {
        std::fprintf(stderr, "WebP-Metal: lossy function not found\n");
      }
#if !__has_feature(objc_arc)
      [library release];
#endif
      delete state;
      return nullptr;
    }
    state->pipeline = [state->device newComputePipelineStateWithFunction:
        function error:&error];
    state->queue = [state->device newCommandQueue];
#if !__has_feature(objc_arc)
    [function release];
    [library release];
#endif
    if (state->pipeline == nil || state->queue == nil) {
      if (EnvironmentFlag("WEBP_METAL_VERBOSE", false)) {
        std::fprintf(stderr, "WebP-Metal: lossy pipeline failed: %s\n",
                     error.localizedDescription.UTF8String);
      }
      delete state;
      return nullptr;
    }
    state->threads = ablation_experiment
        ? ThreadgroupSize("WEBP_METAL_LOSSY_THREADS", state->pipeline)
        : std::min(kPreferredThreads,
                   state->pipeline.maxTotalThreadsPerThreadgroup);

    uint16_t gamma_to_linear[256];
    int32_t linear_to_gamma[33];
    BuildGammaTables(gamma_to_linear, linear_to_gamma);
    state->gamma_to_linear = [state->device
        newBufferWithBytes:gamma_to_linear length:sizeof(gamma_to_linear)
                   options:MTLResourceStorageModeShared];
    state->linear_to_gamma = [state->device
        newBufferWithBytes:linear_to_gamma length:sizeof(linear_to_gamma)
                   options:MTLResourceStorageModeShared];
    if (state->gamma_to_linear == nil || state->linear_to_gamma == nil) {
      delete state;
      return nullptr;
    }
    return state;
  }
}

MetalState* GetState() {
  static std::unique_ptr<MetalState> state(InitializeState());
  return state.get();
}

bool EnsureBuffers(MetalState* state, size_t source_size, size_t output_size) {
  if (source_size > state->source_capacity) {
    size_t capacity;
    if (!RoundedBufferLength(source_size, &capacity)) return false;
    id<MTLBuffer> source = [state->device newBufferWithLength:capacity
        options:SharedBufferOptions(state->write_combined_inputs)];
    if (source == nil) return false;
#if !__has_feature(objc_arc)
    [state->source release];
#endif
    state->source = source;
    state->source_capacity = capacity;
  }
  if (output_size > state->output_capacity) {
    size_t capacity;
    if (!RoundedBufferLength(output_size, &capacity)) return false;
    id<MTLBuffer> output = [state->device newBufferWithLength:capacity
        options:SharedBufferOptions(false)];
    if (output == nil) return false;
#if !__has_feature(objc_arc)
    [state->output release];
#endif
    state->output = output;
    state->output_capacity = capacity;
  }
  return state->source != nil && state->output != nil;
}

bool AddSize(size_t value, size_t* total) {
  if (value > std::numeric_limits<size_t>::max() - *total) return false;
  *total += value;
  return true;
}

bool AlignSize(size_t* value) {
  const size_t remainder = *value % kBufferOffsetAlignment;
  return remainder == 0 ||
         AddSize(kBufferOffsetAlignment - remainder, value);
}

struct BatchItem {
  const uint8_t* source;
  uint8_t* y;
  uint8_t* u;
  uint8_t* v;
  int width;
  int height;
  int y_stride;
  int uv_stride;
  size_t source_size;
  size_t source_offset;
  size_t output_offset;
  size_t y_size;
  size_t uv_size;
  uint32_t uv_width;
  uint32_t uv_height;
  KernelParams params;
};

bool PrepareBatchItem(const WebPAcceleratorRGBToYUVRequest& request,
                      BatchItem* item) {
  if (request.red == nullptr || request.green == nullptr ||
      request.blue == nullptr || request.y == nullptr ||
      request.u == nullptr || request.v == nullptr ||
      (request.step != 3 && request.step != 4) ||
      request.source_stride <= 0 || request.width <= 0 ||
      request.height <= 0 || request.y_stride < request.width) {
    return false;
  }

  const uintptr_t red = reinterpret_cast<uintptr_t>(request.red);
  const uintptr_t green = reinterpret_cast<uintptr_t>(request.green);
  const uintptr_t blue = reinterpret_cast<uintptr_t>(request.blue);
  const uintptr_t base = std::min(red, std::min(green, blue));
  const uintptr_t red_offset = red - base;
  const uintptr_t green_offset = green - base;
  const uintptr_t blue_offset = blue - base;
  if (red_offset >= static_cast<uintptr_t>(request.step) ||
      green_offset >= static_cast<uintptr_t>(request.step) ||
      blue_offset >= static_cast<uintptr_t>(request.step)) {
    return false;
  }

  const uint32_t width = static_cast<uint32_t>(request.width);
  const uint32_t height = static_cast<uint32_t>(request.height);
  const uint32_t uv_width = (width + 1u) >> 1;
  const uint32_t uv_height = (height + 1u) >> 1;
  if (request.uv_stride < static_cast<int>(uv_width)) return false;

  const size_t pixel_count = static_cast<size_t>(width) * height;
  const size_t uv_size = static_cast<size_t>(uv_width) * uv_height;
  const size_t last_row_size = static_cast<size_t>(width) * request.step;
  if (static_cast<size_t>(request.source_stride) < last_row_size) return false;
  const size_t source_rows = static_cast<size_t>(height - 1u);
  if (source_rows >
      (std::numeric_limits<size_t>::max() - last_row_size) /
          static_cast<size_t>(request.source_stride)) {
    return false;
  }
  const size_t source_size =
      source_rows * static_cast<size_t>(request.source_stride) +
      last_row_size;
  if (pixel_count > std::numeric_limits<uint32_t>::max() ||
      uv_size > std::numeric_limits<uint32_t>::max() ||
      uv_size > (std::numeric_limits<size_t>::max() - pixel_count) / 2u) {
    return false;
  }

  item->source = reinterpret_cast<const uint8_t*>(base);
  item->y = request.y;
  item->u = request.u;
  item->v = request.v;
  item->width = request.width;
  item->height = request.height;
  item->y_stride = request.y_stride;
  item->uv_stride = request.uv_stride;
  item->source_size = source_size;
  item->y_size = pixel_count;
  item->uv_size = uv_size;
  item->uv_width = uv_width;
  item->uv_height = uv_height;
  item->params = {
      width, height, static_cast<uint32_t>(request.step),
      static_cast<uint32_t>(request.source_stride),
      static_cast<uint32_t>(red_offset),
      static_cast<uint32_t>(green_offset),
      static_cast<uint32_t>(blue_offset), uv_width,
      static_cast<uint32_t>(pixel_count), static_cast<uint32_t>(uv_size)};
  return true;
}

}  // namespace

static int ImportRGBToYUVAMetalBatchImpl(
    const WebPAcceleratorRGBToYUVRequest* requests, size_t request_count) {
  if (requests == nullptr || request_count == 0 ||
      request_count > std::numeric_limits<size_t>::max() / sizeof(BatchItem) ||
      !EnvironmentFlag("WEBP_METAL_LOSSY", true)) {
    return 0;
  }
  std::unique_ptr<BatchItem[]> items(
      new (std::nothrow) BatchItem[request_count]);
  if (items == nullptr) return 0;
  size_t total_source_size = 0;
  size_t total_output_size = 0;
  for (size_t i = 0; i < request_count; ++i) {
    BatchItem& item = items[i];
    if (!PrepareBatchItem(requests[i], &item) ||
        !AlignSize(&total_source_size) || !AlignSize(&total_output_size)) {
      return 0;
    }
    item.source_offset = total_source_size;
    item.output_offset = total_output_size;
    if (!AddSize(item.source_size, &total_source_size) ||
        !AddSize(item.y_size, &total_output_size) ||
        !AddSize(2u * item.uv_size, &total_output_size)) {
      return 0;
    }
  }
  MetalState* state = GetState();
  if (state == nullptr) return 0;

  std::lock_guard<std::mutex> lock(state->mutex);
  @autoreleasepool {
    if (!EnsureBuffers(state, total_source_size, total_output_size)) return 0;
    uint8_t* const source = static_cast<uint8_t*>(state->source.contents);
    for (size_t i = 0; i < request_count; ++i) {
      const BatchItem& item = items[i];
      std::memcpy(source + item.source_offset, item.source, item.source_size);
    }

    id<MTLCommandBuffer> command = NewCommandBuffer(state);
    id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
    if (command == nil || encoder == nil) return 0;
    [encoder setComputePipelineState:state->pipeline];
    [encoder setBuffer:state->gamma_to_linear offset:0 atIndex:2];
    [encoder setBuffer:state->linear_to_gamma offset:0 atIndex:3];
    for (size_t i = 0; i < request_count; ++i) {
      const BatchItem& item = items[i];
      [encoder setBuffer:state->source
                  offset:static_cast<NSUInteger>(item.source_offset)
                 atIndex:0];
      [encoder setBuffer:state->output
                  offset:static_cast<NSUInteger>(item.output_offset)
                 atIndex:1];
      [encoder setBytes:&item.params length:sizeof(item.params) atIndex:4];
      const MTLSize grid = state->block_2x2
          ? MTLSizeMake(item.uv_width, item.uv_height, 1)
          : MTLSizeMake(item.y_size, 1, 1);
      [encoder dispatchThreads:grid
          threadsPerThreadgroup:MTLSizeMake(state->threads, 1, 1)];
    }
    [encoder endEncoding];
    const CFAbsoluteTime start = CFAbsoluteTimeGetCurrent();
    [command commit];
    [command waitUntilCompleted];
    if (command.status != MTLCommandBufferStatusCompleted) return 0;

    const uint8_t* const output =
        static_cast<const uint8_t*>(state->output.contents);
    for (size_t i = 0; i < request_count; ++i) {
      const BatchItem& item = items[i];
      const uint8_t* const item_output = output + item.output_offset;
      const bool contiguous =
          item.y_stride == item.width &&
          item.uv_stride == static_cast<int>(item.uv_width) &&
          item.u == item.y + item.y_size &&
          item.v == item.u + item.uv_size;
      if (state->contiguous_copy && contiguous) {
        std::memcpy(item.y, item_output,
                    item.y_size + 2u * item.uv_size);
      } else {
        for (int y = 0; y < item.height; ++y) {
          std::memcpy(item.y + static_cast<size_t>(y) * item.y_stride,
                      item_output + static_cast<size_t>(y) * item.width,
                      item.width);
        }
        const uint8_t* const u = item_output + item.y_size;
        const uint8_t* const v = u + item.uv_size;
        for (uint32_t y = 0; y < item.uv_height; ++y) {
          std::memcpy(item.u + static_cast<size_t>(y) * item.uv_stride,
                      u + static_cast<size_t>(y) * item.uv_width,
                      item.uv_width);
          std::memcpy(item.v + static_cast<size_t>(y) * item.uv_stride,
                      v + static_cast<size_t>(y) * item.uv_width,
                      item.uv_width);
        }
      }
    }
    if (EnvironmentFlag("WEBP_METAL_VERBOSE", false)) {
      std::fprintf(stderr,
                   "WebP-Metal: lossy RGB->YUV batch of %zu in %.3f ms\n",
                   request_count,
                   (CFAbsoluteTimeGetCurrent() - start) * 1000.0);
    }
  }
  return 1;
}

#if defined(WEBP_USE_METAL_BATCH_EXPERIMENT)
extern "C" int WebPImportRGBToYUVAMetalBatch(
    const WebPAcceleratorRGBToYUVRequest* requests, size_t request_count) {
  const char* const opt_in = std::getenv("WEBP_METAL_BATCH_EXPERIMENT");
  if (opt_in == nullptr || std::strcmp(opt_in, "1") != 0) return 0;
  return ImportRGBToYUVAMetalBatchImpl(requests, request_count);
}
#endif

extern "C" int WebPImportRGBToYUVAMetal(
    const uint8_t* red, const uint8_t* green, const uint8_t* blue, int step,
    int source_stride, int width, int height, uint8_t* y, uint8_t* u,
    uint8_t* v, int y_stride, int uv_stride) {
  if (width <= 0 || height <= 0) {
    return 0;
  }
  const size_t pixel_count = static_cast<size_t>(width) * height;
  if (pixel_count < EnvironmentSize("WEBP_METAL_LOSSY_MIN_PIXELS",
                                     kDefaultMinimumPixels)) {
    return 0;
  }
  const WebPAcceleratorRGBToYUVRequest request = {
      red, green, blue, step, source_stride, width, height,
      y, u, v, y_stride, uv_stride};
  return ImportRGBToYUVAMetalBatchImpl(&request, 1);
}
