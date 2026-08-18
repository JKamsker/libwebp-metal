// Copyright 2026
//
// Untimed exact-equivalence tests for the backref cost/traceback workspace.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/dsp/lossless.h"
#include "src/enc/backref_cost_traceback_experiment_enc.h"
#include "src/enc/backward_references_enc.h"
#include "src/utils/utils.h"

#define CHECK(condition)                                                 \
  do {                                                                   \
    if (!(condition)) {                                                  \
      fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, \
              #condition);                                               \
      abort();                                                           \
    }                                                                    \
  } while (0)

extern void VP8LBackwardRefsCursorAdd(VP8LBackwardRefs* const refs,
                                      PixOrCopy v);
extern int VP8LBackwardReferencesTraceBackwards(
    int xsize, int ysize, const uint32_t* const argb, int cache_bits,
    const VP8LHashChain* const hash_chain,
    const VP8LBackwardRefs* const refs_src, VP8LBackwardRefs* const refs_dst);

static uint32_t NextRandom(uint32_t* const state) {
  *state = (uint32_t)((uint64_t)*state * 1664525u + 1013904223u);
  return *state;
}

static WEBP_UBSAN_IGNORE_UNSIGNED_OVERFLOW uint64_t
HashBytes(const void* const data, size_t size) {
  const uint8_t* bytes = (const uint8_t*)data;
  uint64_t hash = 1469598103934665603ULL;
  while (size-- > 0) {
    hash ^= *bytes++;
    hash *= 1099511628211ULL;
  }
  return hash;
}

static int RefsEqual(const VP8LBackwardRefs* const a,
                     const VP8LBackwardRefs* const b) {
  VP8LRefsCursor ca = VP8LRefsCursorInit(a);
  VP8LRefsCursor cb = VP8LRefsCursorInit(b);
  while (VP8LRefsCursorOk(&ca) && VP8LRefsCursorOk(&cb)) {
    if (ca.cur_pos->mode != cb.cur_pos->mode ||
        ca.cur_pos->len != cb.cur_pos->len ||
        ca.cur_pos->argb_or_distance != cb.cur_pos->argb_or_distance) {
      return 0;
    }
    VP8LRefsCursorNext(&ca);
    VP8LRefsCursorNext(&cb);
  }
  return VP8LRefsCursorOk(&ca) == VP8LRefsCursorOk(&cb);
}

static void FillCase(uint32_t* const argb, int pixel_count, int pattern) {
  uint32_t state =
      0x9e3779b9u ^ (uint32_t)pixel_count ^ ((uint32_t)pattern << 24);
  int i;
  for (i = 0; i < pixel_count; ++i) {
    switch (pattern) {
      case 0:
        argb[i] = NextRandom(&state);
        break;
      case 1:
        argb[i] = 0xff000000u | ((uint32_t)(i % 7) * 0x00010101u);
        break;
      case 2:
        argb[i] = (i / 19) & 1 ? 0xff123456u : 0xffabcdefu;
        break;
      default:
        argb[i] = 0xff010203u;
        break;
    }
  }
}

static void AddSourceRefs(VP8LBackwardRefs* const refs,
                          const uint32_t* const argb, int pixel_count,
                          int pattern) {
  int i = 0;
  while (i < pixel_count) {
    if (pattern >= 2 && i > 0 && argb[i] == argb[i - 1]) {
      int len = 1;
      while (i + len < pixel_count && len < MAX_LENGTH &&
             argb[i + len] == argb[i + len - 1]) {
        ++len;
      }
      if (len >= 2) {
        VP8LBackwardRefsCursorAdd(refs, PixOrCopyCreateCopy(1, (uint16_t)len));
        i += len;
        continue;
      }
    }
    VP8LBackwardRefsCursorAdd(refs, PixOrCopyCreateLiteral(argb[i++]));
  }
  CHECK(!refs->error);
}

static void RunEquivalenceCase(int pixel_count, int pattern, int cache_bits) {
  uint32_t* const argb = (uint32_t*)malloc((size_t)pixel_count * sizeof(*argb));
  VP8LHashChain hash_chain = {NULL, 0};
  VP8LBackwardRefs source, baseline, candidate, repeated, fallback, invalid;
  WebPPicture picture;
  const int block_size = (pixel_count + 15) / 16;
  int percent = 0;
  uint64_t pixels_hash;
  uint64_t chain_hash;
  CHECK(argb != NULL && VP8LHashChainInit(&hash_chain, pixel_count));
  CHECK(WebPPictureInit(&picture));
  picture.width = pixel_count;
  picture.height = 1;
  FillCase(argb, pixel_count, pattern);
  CHECK(VP8LHashChainFill(&hash_chain, 75, argb, pixel_count, 1,
                          /*low_effort=*/0, &picture, /*percent_range=*/0,
                          &percent));
  pixels_hash = HashBytes(argb, (size_t)pixel_count * sizeof(*argb));
  chain_hash =
      HashBytes(hash_chain.offset_length,
                (size_t)pixel_count * sizeof(*hash_chain.offset_length));
  VP8LBackwardRefsInit(&source, block_size);
  VP8LBackwardRefsInit(&baseline, block_size);
  VP8LBackwardRefsInit(&candidate, block_size);
  VP8LBackwardRefsInit(&repeated, block_size);
  VP8LBackwardRefsInit(&fallback, block_size);
  VP8LBackwardRefsInit(&invalid, block_size);
  AddSourceRefs(&source, argb, pixel_count, pattern);

  CHECK(unsetenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT") == 0);
  CHECK(VP8LBackwardReferencesTraceBackwards(pixel_count, 1, argb, cache_bits,
                                             &hash_chain, &source, &baseline));
  CHECK(setenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT", "1", 1) == 0);
  CHECK(VP8LBackrefCostTracebackExperimentEnabled());
  CHECK(VP8LBackwardReferencesTraceBackwards(pixel_count, 1, argb, cache_bits,
                                             &hash_chain, &source, &candidate));
  CHECK(VP8LBackwardReferencesTraceBackwards(pixel_count, 1, argb, cache_bits,
                                             &hash_chain, &source, &repeated));
  CHECK(setenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE", "1",
               1) == 0);
  CHECK(VP8LBackwardReferencesTraceBackwards(pixel_count, 1, argb, cache_bits,
                                             &hash_chain, &source, &fallback));
  CHECK(unsetenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE") == 0);
  CHECK(setenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT", "01", 1) == 0);
  CHECK(!VP8LBackrefCostTracebackExperimentEnabled());
  CHECK(VP8LBackwardReferencesTraceBackwards(pixel_count, 1, argb, cache_bits,
                                             &hash_chain, &source, &invalid));

  CHECK(RefsEqual(&baseline, &candidate));
  CHECK(RefsEqual(&baseline, &repeated));
  CHECK(RefsEqual(&baseline, &fallback));
  CHECK(RefsEqual(&baseline, &invalid));
  CHECK(HashBytes(argb, (size_t)pixel_count * sizeof(*argb)) == pixels_hash);
  CHECK(HashBytes(hash_chain.offset_length,
                  (size_t)pixel_count * sizeof(*hash_chain.offset_length)) ==
        chain_hash);

  CHECK(unsetenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT") == 0);
  VP8LBackwardRefsClear(&invalid);
  VP8LBackwardRefsClear(&fallback);
  VP8LBackwardRefsClear(&repeated);
  VP8LBackwardRefsClear(&candidate);
  VP8LBackwardRefsClear(&baseline);
  VP8LBackwardRefsClear(&source);
  VP8LHashChainClear(&hash_chain);
  free(argb);
}

static void TestWorkspaceFaultHook(void) {
  void* workspace;
  CHECK(setenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE", "1",
               1) == 0);
  CHECK(VP8LBackrefCostTracebackExperimentMalloc(64) == NULL);
  CHECK(unsetenv("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE") == 0);
  workspace = VP8LBackrefCostTracebackExperimentMalloc(64);
  CHECK(workspace != NULL);
  WebPSafeFree(workspace);
}

int main(int argc, char** argv) {
  static const int kSizes[] = {1, 2, 3, 11, 257, 4097, 65537};
  static const int kCacheBits[] = {0, 1, 5, MAX_COLOR_CACHE_BITS};
  const int sanitizer_smoke =
      argc == 2 && strcmp(argv[1], "--sanitizer-smoke") == 0;
  size_t size_index;
  CHECK(argc == 1 || sanitizer_smoke);
  VP8LEncDspInit();
  TestWorkspaceFaultHook();
  for (size_index = 0; size_index < sizeof(kSizes) / sizeof(kSizes[0]);
       ++size_index) {
    int pattern;
    if (sanitizer_smoke && kSizes[size_index] > 4097) break;
    for (pattern = 0; pattern < 4; ++pattern) {
      size_t cache_index;
      for (cache_index = 0;
           cache_index < sizeof(kCacheBits) / sizeof(kCacheBits[0]);
           ++cache_index) {
        RunEquivalenceCase(kSizes[size_index], pattern,
                           kCacheBits[cache_index]);
      }
    }
  }
  puts("PASS: backref cost/traceback exact equivalence and fallback");
  return 0;
}
