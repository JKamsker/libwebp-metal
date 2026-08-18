// Copyright 2026
//
// Private gate and allocation helpers for the independent v4 remote
// backward-reference cost workspace experiment.

#ifndef WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT_ENC_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostWorkspaceRemoteV4ExperimentEnabled(void);
void* VP8LBackrefCostWorkspaceRemoteV4ExperimentMalloc(size_t size);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT_ENC_H_
