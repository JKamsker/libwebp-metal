// Copyright 2026
//
// Opt-in research prototype for applying a selected WebP lossless predictor
// map on Metal. Predictor selection remains on the CPU. The source and result
// use distinct shared buffers so a failed command never partially mutates the
// encoder's input.

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <algorithm>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>

extern "C" {
#include "src/dsp/lossless.h"
#include "src/enc/predictor_enc_metal.h"
}

#if !defined(WEBP_USE_METAL_PREDICTOR_EXPERIMENT)
#error "predictor_enc_metal.mm requires WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT"
#endif

namespace {

constexpr size_t kDefaultMinimumPixels = 1024u * 1024u;
constexpr NSUInteger kPreferredThreads = 256;

constexpr const char* kPredictorMetalSource = R"METAL(
#include <metal_stdlib>
using namespace metal;

struct PredictorParams {
  uint width;
  uint height;
  uint bits;
  uint tiles_per_row;
};

inline uint average2(uint a, uint b) {
  return (((a ^ b) & 0xfefefefeu) >> 1) + (a & b);
}

inline uint average3(uint a, uint b, uint c) {
  return average2(average2(a, c), b);
}

inline uint average4(uint a, uint b, uint c, uint d) {
  return average2(average2(a, b), average2(c, d));
}

inline uint channel_byte(uint pixel, uint shift) {
  return (pixel >> shift) & 255u;
}

inline uint pack_components(int a, int r, int g, int b) {
  return (uint(clamp(a, 0, 255)) << 24) |
         (uint(clamp(r, 0, 255)) << 16) |
         (uint(clamp(g, 0, 255)) << 8) |
         uint(clamp(b, 0, 255));
}

inline uint clamped_add_subtract_full(uint a, uint b, uint c) {
  return pack_components(
      int(channel_byte(a, 24)) + int(channel_byte(b, 24)) -
          int(channel_byte(c, 24)),
      int(channel_byte(a, 16)) + int(channel_byte(b, 16)) -
          int(channel_byte(c, 16)),
      int(channel_byte(a, 8)) + int(channel_byte(b, 8)) -
          int(channel_byte(c, 8)),
      int(channel_byte(a, 0)) + int(channel_byte(b, 0)) -
          int(channel_byte(c, 0)));
}

inline int add_subtract_half(int a, int b) {
  // Metal and C integer division both truncate toward zero.
  return a + (a - b) / 2;
}

inline uint clamped_add_subtract_half(uint a, uint b, uint c) {
  const uint ave = average2(a, b);
  return pack_components(
      add_subtract_half(int(channel_byte(ave, 24)), int(channel_byte(c, 24))),
      add_subtract_half(int(channel_byte(ave, 16)), int(channel_byte(c, 16))),
      add_subtract_half(int(channel_byte(ave, 8)), int(channel_byte(c, 8))),
      add_subtract_half(int(channel_byte(ave, 0)), int(channel_byte(c, 0))));
}

inline int sub3(int a, int b, int c) {
  return abs(b - c) - abs(a - c);
}

inline uint select_pixel(uint a, uint b, uint c) {
  const int score =
      sub3(int(channel_byte(a, 24)), int(channel_byte(b, 24)),
           int(channel_byte(c, 24))) +
      sub3(int(channel_byte(a, 16)), int(channel_byte(b, 16)),
           int(channel_byte(c, 16))) +
      sub3(int(channel_byte(a, 8)), int(channel_byte(b, 8)),
           int(channel_byte(c, 8))) +
      sub3(int(channel_byte(a, 0)), int(channel_byte(b, 0)),
           int(channel_byte(c, 0)));
  return score <= 0 ? a : b;
}

inline uint subtract_pixels(uint a, uint b) {
  const uint alpha_green =
      0x00ff00ffu + (a & 0xff00ff00u) - (b & 0xff00ff00u);
  const uint red_blue =
      0xff00ff00u + (a & 0x00ff00ffu) - (b & 0x00ff00ffu);
  return (alpha_green & 0xff00ff00u) | (red_blue & 0x00ff00ffu);
}

inline uint predictor(uint mode, uint left, uint top_left, uint top,
                      uint top_right) {
  switch (mode) {
    case 0u: return 0xff000000u;
    case 1u: return left;
    case 2u: return top;
    case 3u: return top_right;
    case 4u: return top_left;
    case 5u: return average3(left, top, top_right);
    case 6u: return average2(left, top_left);
    case 7u: return average2(left, top);
    case 8u: return average2(top_left, top);
    case 9u: return average2(top, top_right);
    case 10u: return average4(left, top_left, top, top_right);
    case 11u: return select_pixel(top, left, top_left);
    case 12u: return clamped_add_subtract_full(left, top, top_left);
    case 13u: return clamped_add_subtract_half(left, top, top_left);
    default: return 0xff000000u;
  }
}

kernel void predictor_residuals(
    device const uint* source [[buffer(0)]],
    device const uint* modes [[buffer(1)]],
    device uint* residuals [[buffer(2)]],
    constant PredictorParams& params [[buffer(3)]],
    uint index [[thread_position_in_grid]]) {
  const uint pixel_count = params.width * params.height;
  if (index >= pixel_count) return;
  const uint x = index % params.width;
  const uint y = index / params.width;
  uint prediction;
  if (y == 0u) {
    prediction = x == 0u ? 0xff000000u : source[index - 1u];
  } else if (x == 0u) {
    prediction = source[index - params.width];
  } else {
    const uint tile_index = (y >> params.bits) * params.tiles_per_row +
                            (x >> params.bits);
    const uint mode = (modes[tile_index] >> 8) & 255u;
    const uint top_right = x + 1u < params.width
        ? source[index - params.width + 1u]
        : source[y * params.width];
    prediction = predictor(mode, source[index - 1u],
                           source[index - params.width - 1u],
                           source[index - params.width], top_right);
  }
  residuals[index] = subtract_pixels(source[index], prediction);
}
)METAL";

struct PredictorParams {
  uint32_t width;
  uint32_t height;
  uint32_t bits;
  uint32_t tiles_per_row;
};

struct PredictorMetalState {
  id<MTLDevice> device = nil;
  id<MTLCommandQueue> queue = nil;
  id<MTLComputePipelineState> pipeline = nil;
  id<MTLBuffer> source = nil;
  id<MTLBuffer> modes = nil;
  id<MTLBuffer> output = nil;
  size_t source_capacity = 0;
  size_t modes_capacity = 0;
  size_t output_capacity = 0;
  size_t minimum_pixels = kDefaultMinimumPixels;
  bool validate = false;
  bool verbose = false;
  std::mutex operation_mutex;
};

PredictorMetalState* g_state = nullptr;

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

size_t RoundedBufferLength(size_t length) {
  constexpr size_t kPage = 16u * 1024u;
  return std::max(kPage, (length + kPage - 1u) & ~(kPage - 1u));
}

bool GrowBuffer(id<MTLDevice> device, size_t required, id<MTLBuffer>* buffer,
                size_t* capacity) {
  if (required <= *capacity) return true;
  const size_t next_capacity = RoundedBufferLength(required);
  id<MTLBuffer> next = [device newBufferWithLength:next_capacity
      options:MTLResourceStorageModeShared];
  if (next == nil) return false;
  *buffer = next;
  *capacity = next_capacity;
  return true;
}

PredictorMetalState* InitializeState() {
  const char* const predictor_opt_in = std::getenv("WEBP_METAL_PREDICTOR");
  if (!EnvironmentFlag("WEBP_METAL", true) || predictor_opt_in == nullptr ||
      std::strcmp(predictor_opt_in, "1") != 0) {
    return nullptr;
  }
  @autoreleasepool {
    auto* state = new PredictorMetalState();
    state->minimum_pixels = EnvironmentSize(
        "WEBP_METAL_PREDICTOR_MIN_PIXELS", kDefaultMinimumPixels);
    state->validate = EnvironmentFlag("WEBP_METAL_PREDICTOR_VALIDATE", false);
    state->verbose = EnvironmentFlag("WEBP_METAL_VERBOSE", false);
    state->device = MTLCreateSystemDefaultDevice();
    if (state->device == nil) {
      delete state;
      return nullptr;
    }
    NSError* error = nil;
    id<MTLLibrary> library = [state->device
        newLibraryWithSource:[NSString stringWithUTF8String:kPredictorMetalSource]
                     options:nil
                       error:&error];
    if (library == nil) {
      if (state->verbose) {
        std::fprintf(stderr,
                     "WebP-Metal experiment: predictor library failed: %s\n",
                     error.localizedDescription.UTF8String);
      }
      delete state;
      return nullptr;
    }
    id<MTLFunction> function =
        [library newFunctionWithName:@"predictor_residuals"];
    if (function != nil) {
      state->pipeline =
          [state->device newComputePipelineStateWithFunction:function
                                                       error:&error];
    }
    state->queue = [state->device newCommandQueue];
    if (state->pipeline == nil || state->queue == nil) {
      if (state->verbose) {
        std::fprintf(stderr,
                     "WebP-Metal experiment: predictor pipeline failed: %s\n",
                     error.localizedDescription.UTF8String);
      }
      delete state;
      return nullptr;
    }
    if (state->verbose) {
      std::fprintf(stderr,
                   "WebP-Metal experiment: predictor residuals enabled on %s "
                   "(minimum %zu pixels, validation %s)\n",
                   state->device.name.UTF8String, state->minimum_pixels,
                   state->validate ? "on" : "off");
    }
    return state;
  }
}

PredictorMetalState* GetState() {
  static dispatch_once_t once_token;
  dispatch_once(&once_token, ^{ g_state = InitializeState(); });
  return g_state;
}

bool HasFullyTransparentPixel(const uint32_t* argb, size_t count) {
  for (size_t i = 0; i < count; ++i) {
    if ((argb[i] >> 24) == 0u) return true;
  }
  return false;
}

bool ModesAreValid(const uint32_t* modes, size_t count) {
  for (size_t i = 0; i < count; ++i) {
    if (((modes[i] >> 8) & 0xffu) >= 14u) return false;
  }
  return true;
}

void BuildCpuReference(int width, int height, int bits,
                       const uint32_t* modes, const uint32_t* source,
                       uint32_t* residuals) {
  const int tile_size = 1 << bits;
  const int tiles_per_row = (width + tile_size - 1) >> bits;
  VP8LPredictorsSub_C[0](source, nullptr, 1, residuals);
  if (width > 1) {
    VP8LPredictorsSub_C[1](source + 1, nullptr, width - 1, residuals + 1);
  }
  for (int y = 1; y < height; ++y) {
    const int row = y * width;
    int x = 0;
    VP8LPredictorsSub_C[2](source + row, source + row - width, 1,
                           residuals + row);
    x = 1;
    while (x < width) {
      const int mode =
          (modes[(y >> bits) * tiles_per_row + (x >> bits)] >> 8) & 0xff;
      int x_end = ((x >> bits) + 1) << bits;
      if (x_end > width) x_end = width;
      VP8LPredictorsSub_C[mode](source + row + x,
                                source + row - width + x, x_end - x,
                                residuals + row + x);
      x = x_end;
    }
  }
}

}  // namespace

extern "C" int VP8LResidualImageMetalExperimental(
    int width, int height, int bits, const uint32_t* modes, int exact,
    uint32_t* argb) {
  PredictorMetalState* const state = GetState();
  if (state == nullptr || width <= 0 || height <= 0 || bits < 0 || bits > 8 ||
      modes == nullptr || argb == nullptr) {
    return 0;
  }
  const size_t pixel_count = static_cast<size_t>(width) * height;
  const uint32_t tile_size = 1u << bits;
  const uint32_t tiles_per_row =
      (static_cast<uint32_t>(width) + tile_size - 1u) >> bits;
  const uint32_t tiles_per_col =
      (static_cast<uint32_t>(height) + tile_size - 1u) >> bits;
  const size_t mode_count =
      static_cast<size_t>(tiles_per_row) * tiles_per_col;
  if (pixel_count < state->minimum_pixels ||
      (!exact && HasFullyTransparentPixel(argb, pixel_count)) ||
      !ModesAreValid(modes, mode_count)) {
    return 0;
  }

  const size_t pixel_bytes = pixel_count * sizeof(uint32_t);
  const size_t mode_bytes = mode_count * sizeof(uint32_t);
  const PredictorParams params = {
      static_cast<uint32_t>(width), static_cast<uint32_t>(height),
      static_cast<uint32_t>(bits), tiles_per_row};

  std::lock_guard<std::mutex> lock(state->operation_mutex);
  @autoreleasepool {
    if (!GrowBuffer(state->device, pixel_bytes, &state->source,
                    &state->source_capacity) ||
        !GrowBuffer(state->device, mode_bytes, &state->modes,
                    &state->modes_capacity) ||
        !GrowBuffer(state->device, pixel_bytes, &state->output,
                    &state->output_capacity)) {
      return 0;
    }
    std::memcpy(state->source.contents, argb, pixel_bytes);
    std::memcpy(state->modes.contents, modes, mode_bytes);

    id<MTLCommandBuffer> command = [state->queue commandBuffer];
    id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
    if (command == nil || encoder == nil) return 0;
    [encoder setComputePipelineState:state->pipeline];
    [encoder setBuffer:state->source offset:0 atIndex:0];
    [encoder setBuffer:state->modes offset:0 atIndex:1];
    [encoder setBuffer:state->output offset:0 atIndex:2];
    [encoder setBytes:&params length:sizeof(params) atIndex:3];
    const NSUInteger threads = std::min(
        kPreferredThreads, state->pipeline.maxTotalThreadsPerThreadgroup);
    [encoder dispatchThreads:MTLSizeMake(pixel_count, 1, 1)
        threadsPerThreadgroup:MTLSizeMake(threads, 1, 1)];
    [encoder endEncoding];
    [command commit];
    [command waitUntilCompleted];
    if (command.status != MTLCommandBufferStatusCompleted) {
      if (state->verbose) {
        std::fprintf(stderr,
                     "WebP-Metal experiment: predictor command failed: %s\n",
                     command.error.localizedDescription.UTF8String);
      }
      return 0;
    }

    if (state->validate) {
      uint32_t* const reference =
          static_cast<uint32_t*>(std::malloc(pixel_bytes));
      if (reference == nullptr) return 0;
      BuildCpuReference(width, height, bits, modes,
                        static_cast<const uint32_t*>(state->source.contents),
                        reference);
      const uint32_t* const output =
          static_cast<const uint32_t*>(state->output.contents);
      for (size_t i = 0; i < pixel_count; ++i) {
        if (reference[i] != output[i]) {
          std::fprintf(stderr,
                       "WebP-Metal experiment: predictor validation mismatch "
                       "at pixel %zu: CPU=%08x Metal=%08x\n",
                       i, reference[i], output[i]);
          std::free(reference);
          return 0;
        }
      }
      std::free(reference);
    }

    // Failure injection verifies that completed-but-uncommitted device work
    // leaves caller buffers untouched and the CPU fallback remains safe.
    if (EnvironmentFlag("WEBP_METAL_PREDICTOR_FAIL_AFTER_DISPATCH", false)) {
      if (state->verbose) {
        std::fprintf(stderr,
                     "WebP-Metal experiment: injected post-dispatch failure\n");
      }
      return 0;
    }
    std::memcpy(argb, state->output.contents, pixel_bytes);
    if (state->verbose) {
      std::fprintf(stderr,
                   "WebP-Metal experiment: applied predictor residuals to "
                   "%dx%d (%zu modes)\n",
                   width, height, mode_count);
    }
    return 1;
  }
}
