// Copyright 2026
//
// Private runtime gate for the independently frozen, recorder-free remote
// backward-reference cost workspace A/B experiment.

#include "src/enc/backref_cost_workspace_ab_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

#include "src/utils/utils.h"

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostWorkspaceABExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT");
}

void* VP8LBackrefCostWorkspaceABExperimentMalloc(size_t size) {
  if (EnvironmentIsOne(
          "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_INJECT_FAILURE")) {
    return NULL;
  }
  return WebPSafeMalloc(1ULL, size);
}
