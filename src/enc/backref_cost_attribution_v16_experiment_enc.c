// Copyright 2026
//
// Private exact-value runtime control for attribution-only profiling.

#include "src/enc/backref_cost_attribution_v16_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

#if defined(_MSC_VER)
#define WEBP_ATTRIBUTION_V16_TLS __declspec(thread)
#else
#define WEBP_ATTRIBUTION_V16_TLS __thread
#endif

static WEBP_ATTRIBUTION_V16_TLS VP8LBackrefCostAttributionV16Counters counters;

int VP8LBackrefCostAttributionV16ExperimentEnabled(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT");
  return value != NULL && strcmp(value, "1") == 0;
}

void VP8LBackrefCostAttributionV16ResetCounters(void) {
  memset(&counters, 0, sizeof(counters));
}

void VP8LBackrefCostAttributionV16RecordSelector(void) {
  ++counters.selector_evaluations;
}

void VP8LBackrefCostAttributionV16RecordDP(int candidate) {
  if (candidate) {
    ++counters.candidate_dp_calls;
  } else {
    ++counters.baseline_dp_calls;
  }
}

VP8LBackrefCostAttributionV16Counters VP8LBackrefCostAttributionV16GetCounters(
    void) {
  return counters;
}
