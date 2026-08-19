// Copyright 2026
//
// Private exact-value runtime control for attribution-only profiling.

#include "src/enc/backref_cost_attribution_v12_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

#if defined(_MSC_VER)
#define WEBP_ATTRIBUTION_V12_TLS __declspec(thread)
#else
#define WEBP_ATTRIBUTION_V12_TLS __thread
#endif

static WEBP_ATTRIBUTION_V12_TLS VP8LBackrefCostAttributionV12Counters counters;

int VP8LBackrefCostAttributionV12ExperimentEnabled(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT");
  return value != NULL && strcmp(value, "1") == 0;
}

void VP8LBackrefCostAttributionV12ResetCounters(void) {
  memset(&counters, 0, sizeof(counters));
}

void VP8LBackrefCostAttributionV12RecordSelector(void) {
  ++counters.selector_evaluations;
}

void VP8LBackrefCostAttributionV12RecordDP(int candidate) {
  if (candidate) {
    ++counters.candidate_dp_calls;
  } else {
    ++counters.baseline_dp_calls;
  }
}

VP8LBackrefCostAttributionV12Counters VP8LBackrefCostAttributionV12GetCounters(
    void) {
  return counters;
}
