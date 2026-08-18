// Copyright 2026
//
// Private runtime gate for the recorder-free backward-reference cost /
// traceback workspace experiment.

#include "src/enc/backref_cost_traceback_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

#include "src/utils/utils.h"

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostTracebackExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT");
}

void* VP8LBackrefCostTracebackExperimentMalloc(size_t size) {
  if (EnvironmentIsOne(
          "WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE")) {
    return NULL;
  }
  return WebPSafeMalloc(1ULL, size);
}
