// Copyright 2026
//
// Private gate and allocation helpers for the independently frozen remote
// backward-reference cost workspace A/B experiment.

#ifndef WEBP_ENC_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_ENC_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostWorkspaceABExperimentEnabled(void);
void* VP8LBackrefCostWorkspaceABExperimentMalloc(size_t size);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_ENC_H_
