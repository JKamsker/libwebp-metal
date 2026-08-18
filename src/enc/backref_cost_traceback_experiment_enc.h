// Copyright 2026
//
// Private gate and allocation helpers for the backward-reference cost /
// traceback implementation experiment.

#ifndef WEBP_ENC_BACKREF_COST_TRACEBACK_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_TRACEBACK_EXPERIMENT_ENC_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostTracebackExperimentEnabled(void);
void* VP8LBackrefCostTracebackExperimentMalloc(size_t size);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_TRACEBACK_EXPERIMENT_ENC_H_
