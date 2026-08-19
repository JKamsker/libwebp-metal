// Copyright 2026

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/utils/bit_writer_utils.h"

enum { kTokenCount = 65536, kProbaCount = 16384 };

static int allocation_count;
static int fail_allocation_at;

#define CHECK(condition)                                                     \
  do {                                                                       \
    if (!(condition)) {                                                      \
      fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__,   \
              #condition);                                                   \
      abort();                                                               \
    }                                                                        \
  } while (0)

// Standalone allocator shims for compiling the production bit writer directly
// into this focused test.
void* WebPSafeMalloc(uint64_t nmemb, size_t size) {
  if (nmemb == 0 || size == 0 || nmemb > SIZE_MAX / size) return NULL;
  if (fail_allocation_at > 0 && ++allocation_count == fail_allocation_at) {
    return NULL;
  }
  return malloc((size_t)nmemb * size);
}

void WebPSafeFree(void* ptr) { free(ptr); }

static uint32_t NextRandom(uint32_t* state) {
  *state = *state * 1664525u + 1013904223u;
  return *state;
}

static void CheckEqual(const VP8BitWriter* a, const VP8BitWriter* b) {
  CHECK(a->range == b->range);
  CHECK(a->value == b->value);
  CHECK(a->run == b->run);
  CHECK(a->nb_bits == b->nb_bits);
  CHECK(a->pos == b->pos);
  CHECK(a->max_pos == b->max_pos);
  CHECK(a->error == b->error);
  CHECK(a->pos == 0 || memcmp(a->buf, b->buf, a->pos) == 0);
}

static void PutReferencePage(VP8BitWriter* bw, const uint16_t* tokens,
                             int num_tokens, int first_token,
                             const uint8_t* probas) {
  while (num_tokens-- > first_token) {
    const uint16_t token = tokens[num_tokens];
    const int bit = (token >> 15) & 1;
    const int prob = (token & (1u << 14))
                         ? token & 0xffu
                         : probas[token & 0x3fffu];
    VP8PutBit(bw, bit, prob);
  }
}

int main(void) {
  uint16_t* const tokens =
      (uint16_t*)malloc(kTokenCount * sizeof(*tokens));
  uint8_t* const probas = (uint8_t*)malloc(kProbaCount * sizeof(*probas));
  VP8BitWriter page_writer, reference_writer;
  VP8BitWriter failed_page_writer, failed_reference_writer;
  uint32_t random = 0x6d2b79f5u;
  int offset = 0;
  int page = 0;
  CHECK(tokens != NULL && probas != NULL);

  for (int i = 0; i < kProbaCount; ++i) {
    probas[i] = (uint8_t)(1 + NextRandom(&random) % 254u);
  }
  for (int i = 0; i < kTokenCount; ++i) {
    const uint32_t value = NextRandom(&random);
    const uint16_t bit = (uint16_t)((value & 1u) << 15);
    if (value & 2u) {
      tokens[i] = bit | (1u << 14) |
                  (uint16_t)(1 + ((value >> 8) % 254u));
    } else {
      tokens[i] = bit | (uint16_t)((value >> 8) & 0x3fffu);
    }
  }

  CHECK(VP8BitWriterInit(&page_writer, 1));
  CHECK(VP8BitWriterInit(&reference_writer, 1));
  while (offset < kTokenCount) {
    int count = 257 + (int)(NextRandom(&random) % 4096u);
    const int first = (page % 4 == 0) ? page % 17 : 0;
    if (count > kTokenCount - offset) count = kTokenCount - offset;
    VP8PutTokenPage(&page_writer, tokens + offset, count,
                    first < count ? first : 0, probas);
    PutReferencePage(&reference_writer, tokens + offset, count,
                     first < count ? first : 0, probas);
    CheckEqual(&page_writer, &reference_writer);
    offset += count;
    ++page;
  }

  // The one-byte initial request grows to 1024 bytes; this proves the test
  // crossed several capacity boundaries and exercised the unchanged slow path.
  CHECK(page_writer.max_pos > 1024);
  CHECK(VP8BitWriterFinish(&page_writer) != NULL);
  CHECK(VP8BitWriterFinish(&reference_writer) != NULL);
  CheckEqual(&page_writer, &reference_writer);

  VP8BitWriterWipeOut(&page_writer);
  VP8BitWriterWipeOut(&reference_writer);

  // Force the second growth allocation to fail in each implementation. The
  // fast path must reach the original Flush/BitWriterResize path at the same
  // byte and retain its exact error state and partial output.
  allocation_count = 0;
  fail_allocation_at = 3;
  CHECK(VP8BitWriterInit(&failed_page_writer, 1));
  VP8PutTokenPage(&failed_page_writer, tokens, kTokenCount, 0, probas);
  allocation_count = 0;
  CHECK(VP8BitWriterInit(&failed_reference_writer, 1));
  PutReferencePage(&failed_reference_writer, tokens, kTokenCount, 0, probas);
  CHECK(failed_page_writer.error);
  CheckEqual(&failed_page_writer, &failed_reference_writer);
  fail_allocation_at = 0;
  VP8BitWriterWipeOut(&failed_page_writer);
  VP8BitWriterWipeOut(&failed_reference_writer);

  free(probas);
  free(tokens);
  return 0;
}
