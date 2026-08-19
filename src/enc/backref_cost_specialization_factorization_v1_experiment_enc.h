// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// factorization v1. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_H = 2
} VP8LBackrefCostSpecializationFactorizationV1Variant;

VP8LBackrefCostSpecializationFactorizationV1Variant
VP8LBackrefCostSpecializationFactorizationV1GetVariant(void);

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_RECORDER)
typedef struct {
  uint64_t selector_evaluations;
  uint64_t baseline_dp_calls;
  uint64_t layout_clone_dp_calls;
  uint64_t hint_dp_calls;
  uint64_t exact_activations;
  uint64_t push_calls;
  uint64_t short_push_calls;
  uint64_t cache_segments;
  uint64_t overlap_scans;
  uint64_t disjoint_prefix_scans;
  uint64_t insert_calls;
  uint64_t null_hint_insert_calls;
  uint64_t position_backward_steps;
  uint64_t position_forward_steps;
  uint64_t append_hint_fast_paths;
  uint64_t append_hint_branch_checks;
  uint64_t append_hint_loads;
  uint64_t append_hint_start_loads;
  uint64_t append_hint_update_checks;
  uint64_t append_hint_updates;
  uint64_t pop_tail_branch_checks;
  uint64_t pop_tail_updates;
  uint64_t interval_updates;
  uint64_t interval_pops;
  uint64_t max_live_intervals;
} VP8LBackrefCostSpecializationFactorizationV1Stats;

void VP8LBackrefCostSpecializationFactorizationV1StatsReset(void);
void VP8LBackrefCostSpecializationFactorizationV1StatsGet(
    VP8LBackrefCostSpecializationFactorizationV1Stats* stats);
void VP8LBackrefCostSpecializationFactorizationV1RecordSelector(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordDP(int variant);
void VP8LBackrefCostSpecializationFactorizationV1RecordActivation(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordPush(int is_short);
void VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostSpecializationFactorizationV1RecordInsert(int has_null_hint);
void VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordUpdate(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordPop(void);
void VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals(int count);
#endif

#if defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT)
#if defined(_MSC_VER)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __attribute__((noinline))
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V1_EXPERIMENT_ENC_H_
