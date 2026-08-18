// Copyright 2026
//
// Private runtime gate for the independent v2 recorder-free remote
// backward-reference cost workspace experiment.

#include "src/enc/backref_cost_workspace_remote_v2_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

#include "src/utils/utils.h"

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostWorkspaceRemoteV2ExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT");
}

void* VP8LBackrefCostWorkspaceRemoteV2ExperimentMalloc(size_t size) {
  if (EnvironmentIsOne(
          "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT_INJECT_FAILURE")) {
    return NULL;
  }
  return WebPSafeMalloc(1ULL, size);
}
