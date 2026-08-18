// Copyright 2026
//
// Private gate and allocation helpers for the independent v3 remote
// backward-reference cost workspace experiment.

#ifndef WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT_ENC_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostWorkspaceRemoteV3ExperimentEnabled(void);
void* VP8LBackrefCostWorkspaceRemoteV3ExperimentMalloc(size_t size);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT_ENC_H_
