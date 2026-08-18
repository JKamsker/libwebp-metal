// Copyright 2026
//
// Untimed equivalence tests for the cache-size serial-sweep candidate.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dsp/lossless.h"
#include "src/enc/backward_references_enc.h"
#include "src/enc/cache_size_serial_sweep_enc.h"

#define CHECK(condition)                                                     \
  do {                                                                       \
    if (!(condition)) {                                                      \
      fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__,    \
              #condition);                                                   \
      abort();                                                               \
    }                                                                        \
  } while (0)

extern void VP8LBackwardRefsCursorAdd(VP8LBackwardRefs* const refs,
                                      PixOrCopy v);

static uint32_t NextRandom(uint32_t* const state) {
  *state = (uint32_t)((uint64_t)*state * 1664525u + 1013904223u);
  return *state;
}

static uint64_t RefsHash(const VP8LBackwardRefs* const refs) {
  VP8LRefsCursor c = VP8LRefsCursorInit(refs);
  uint64_t hash = 0;
  while (VP8LRefsCursorOk(&c)) {
    const PixOrCopy* const v = c.cur_pos;
    hash += v->mode;
    hash += (uint64_t)v->len * 3u;
    hash += (uint64_t)v->argb_or_distance * 17u;
    VP8LRefsCursorNext(&c);
  }
  return hash;
}

static void RequireEquivalent(const uint32_t* const argb, int pixel_count,
                              const VP8LBackwardRefs* const refs, int quality,
                              int cache_bits_max) {
  const uint64_t refs_hash = RefsHash(refs);
  uint64_t argb_hash = 0;
  int baseline_bits = -1;
  int candidate_bits = -1;
  int i;
  for (i = 0; i < pixel_count; ++i) {
    argb_hash += (uint64_t)argb[i] * (uint64_t)(i + 1);
  }
  CHECK(VP8LCompareCacheSizeSearchForTest(
      argb, quality, refs, cache_bits_max, &baseline_bits, &candidate_bits));
  CHECK(baseline_bits == candidate_bits);
  CHECK(RefsHash(refs) == refs_hash);
  {
    uint64_t after_hash = 0;
    for (i = 0; i < pixel_count; ++i) {
      after_hash += (uint64_t)argb[i] * (uint64_t)(i + 1);
    }
    CHECK(after_hash == argb_hash);
  }
}

static void AddLiteralRefs(VP8LBackwardRefs* const refs,
                           const uint32_t* const argb, int pixel_count) {
  int i;
  for (i = 0; i < pixel_count; ++i) {
    VP8LBackwardRefsCursorAdd(refs, PixOrCopyCreateLiteral(argb[i]));
  }
  CHECK(!refs->error);
}

static void TestExhaustiveBinaryLiterals(void) {
  uint32_t argb[10];
  int length;
  for (length = 0; length <= 10; ++length) {
    const uint32_t sequence_count = (uint32_t)1u << length;
    uint32_t sequence;
    for (sequence = 0; sequence < sequence_count; ++sequence) {
      VP8LBackwardRefs refs;
      int i, cache_bits;
      for (i = 0; i < length; ++i) {
        argb[i] = ((sequence >> i) & 1u) ? 0xff123456u : 0u;
      }
      VP8LBackwardRefsInit(&refs, 1);
      AddLiteralRefs(&refs, argb, length);
      for (cache_bits = 0; cache_bits <= MAX_COLOR_CACHE_BITS; ++cache_bits) {
        RequireEquivalent(argb, length, &refs, 26, cache_bits);
      }
      VP8LBackwardRefsClear(&refs);
    }
  }
}

static void MakeMixedRefs(VP8LBackwardRefs* const refs,
                          const uint32_t* const argb, int pixel_count,
                          uint32_t seed, int pattern) {
  int pos = 0;
  while (pos < pixel_count) {
    const int remaining = pixel_count - pos;
    int len = 1 + (int)(NextRandom(&seed) % 31u);
    if (len > remaining) len = remaining;
    if (pattern != 0 && ((pos + pattern + (int)(seed & 7u)) % 5) <= 1) {
      VP8LBackwardRefsCursorAdd(
          refs, PixOrCopyCreateCopy((uint32_t)(1 + pos % 120), (uint16_t)len));
      pos += len;
    } else {
      VP8LBackwardRefsCursorAdd(refs, PixOrCopyCreateLiteral(argb[pos]));
      ++pos;
    }
  }
  CHECK(!refs->error);
}

static void TestTargetedMixedAndEdges(int maximum_size) {
  static const int kSizes[] = {1, 2, 3, 7, 15, 31, 255, 256, 257,
                               1023, 4095, 4097, 65537};
  static const int kQualities[] = {0, 25, 26, 75, 100};
  uint32_t* const argb = (uint32_t*)malloc(65537u * sizeof(*argb));
  size_t size_index;
  CHECK(argb != NULL);
  for (size_index = 0; size_index < sizeof(kSizes) / sizeof(kSizes[0]);
       ++size_index) {
    const int pixel_count = kSizes[size_index];
    int pattern;
    if (pixel_count > maximum_size) continue;
    for (pattern = 0; pattern < 5; ++pattern) {
      VP8LBackwardRefs refs;
      uint32_t state = 0x9e3779b9u ^ (uint32_t)pixel_count ^
                       ((uint32_t)pattern << 24);
      int i;
      for (i = 0; i < pixel_count; ++i) {
        const uint32_t random = NextRandom(&state);
        switch (pattern) {
          case 0:
            argb[i] = random;
            break;
          case 1:
            argb[i] = (i & 1) ? 0u : 0xffffffffu;
            break;
          case 2:
            argb[i] = 0xff000000u | ((uint32_t)(i % 17) * 0x010101u);
            break;
          case 3:
            argb[i] = 0u;
            break;
          default:
            argb[i] = (random & 0xff00ff00u) | (uint32_t)(i & 0xff);
            break;
        }
      }
      VP8LBackwardRefsInit(&refs, pixel_count / 17);
      MakeMixedRefs(&refs, argb, pixel_count, state, pattern);
      for (i = 0; i < (int)(sizeof(kQualities) / sizeof(kQualities[0])); ++i) {
        int cache_bits;
        for (cache_bits = 0; cache_bits <= MAX_COLOR_CACHE_BITS;
             ++cache_bits) {
          RequireEquivalent(argb, pixel_count, &refs, kQualities[i],
                            cache_bits);
        }
      }
      VP8LBackwardRefsClear(&refs);
    }
  }
  free(argb);
}

static void TestSanitizerSmoke(void) {
  uint32_t argb[257];
  VP8LBackwardRefs refs;
  uint32_t state = 0x12345678u;
  int i;
  for (i = 0; i < 257; ++i) {
    argb[i] = NextRandom(&state) ^ ((uint32_t)(i % 13) * 0x01010101u);
  }
  VP8LBackwardRefsInit(&refs, 17);
  MakeMixedRefs(&refs, argb, 257, state, 4);
  RequireEquivalent(argb, 257, &refs, 25, MAX_COLOR_CACHE_BITS);
  RequireEquivalent(argb, 257, &refs, 26, 0);
  RequireEquivalent(argb, 257, &refs, 26, 1);
  RequireEquivalent(argb, 257, &refs, 26, MAX_COLOR_CACHE_BITS);
  RequireEquivalent(argb, 257, &refs, 100, MAX_COLOR_CACHE_BITS);
  VP8LBackwardRefsClear(&refs);
}

int main(int argc, char** argv) {
  const int sanitizer_smoke =
      argc == 2 && strcmp(argv[1], "--sanitizer-smoke") == 0;
  CHECK(argc == 1 || sanitizer_smoke);
  VP8LEncDspInit();
  if (sanitizer_smoke) {
    TestSanitizerSmoke();
  } else {
    TestExhaustiveBinaryLiterals();
    TestTargetedMixedAndEdges(65537);
  }
  puts("PASS: cache-size serial sweep exact chosen-bit equivalence");
  return 0;
}
