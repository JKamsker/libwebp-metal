// Copyright 2026
//
// Private hooks for the independently gated dominant-boundary experiments.

#ifndef WEBP_ENC_BOUNDARY_EXPERIMENT_ENC_H_
#define WEBP_ENC_BOUNDARY_EXPERIMENT_ENC_H_

#include <stdint.h>

#include "src/webp/encode.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_PREDICTOR_BOUNDARY_SELECT = 0,
  WEBP_PREDICTOR_BOUNDARY_APPLY,
  WEBP_PREDICTOR_BOUNDARY_MAP_ENCODE,
  WEBP_PREDICTOR_BOUNDARY_STAGE_COUNT
} WebPPredictorBoundaryStage;

typedef enum {
  WEBP_BACKREF_EXACT_TOTAL = 0,
  WEBP_BACKREF_EXACT_STANDARD_LZ77,
  WEBP_BACKREF_EXACT_RLE,
  WEBP_BACKREF_EXACT_BOX,
  WEBP_BACKREF_EXACT_CACHE_SEARCH,
  WEBP_BACKREF_EXACT_CACHE_REWRITE,
  WEBP_BACKREF_EXACT_TRACE_BACK,
  WEBP_BACKREF_EXACT_COST_EVALUATION,
  WEBP_BACKREF_EXACT_STAGE_COUNT
} WebPBackrefExactStage;

#if defined(WEBP_USE_PREDICTOR_BOUNDARY_EXPERIMENT)
void WebPPredictorBoundaryBegin(const WebPConfig* config,
                                const WebPPicture* picture);
void WebPPredictorBoundaryEnd(int ok, int error_code);
uint64_t WebPPredictorBoundaryStageBegin(WebPPredictorBoundaryStage stage);
void WebPPredictorBoundaryStageEnd(WebPPredictorBoundaryStage stage,
                                   uint64_t start_ns);
#else
#define WebPPredictorBoundaryBegin(config, picture) \
  ((void)(config), (void)(picture))
#define WebPPredictorBoundaryEnd(ok, error_code) \
  ((void)(ok), (void)(error_code))
#define WebPPredictorBoundaryStageBegin(stage) ((void)(stage), (uint64_t)0)
#define WebPPredictorBoundaryStageEnd(stage, start_ns) \
  ((void)(stage), (void)(start_ns))
#endif

#if defined(WEBP_USE_BACKREF_EXACT_EXPERIMENT)
void WebPBackrefExactBegin(const WebPConfig* config,
                           const WebPPicture* picture);
void WebPBackrefExactEnd(int ok, int error_code);
uint64_t WebPBackrefExactStageBegin(WebPBackrefExactStage stage);
void WebPBackrefExactStageEnd(WebPBackrefExactStage stage,
                              uint64_t start_ns);
#else
#define WebPBackrefExactBegin(config, picture) \
  ((void)(config), (void)(picture))
#define WebPBackrefExactEnd(ok, error_code) \
  ((void)(ok), (void)(error_code))
#define WebPBackrefExactStageBegin(stage) ((void)(stage), (uint64_t)0)
#define WebPBackrefExactStageEnd(stage, start_ns) \
  ((void)(stage), (void)(start_ns))
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BOUNDARY_EXPERIMENT_ENC_H_
