// Copyright 2026
//
// Private exact-value runtime control for attribution-only profiling.

#include "src/enc/backref_cost_attribution_v2_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

int VP8LBackrefCostAttributionV2ExperimentEnabled(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT");
  return value != NULL && strcmp(value, "1") == 0;
}
