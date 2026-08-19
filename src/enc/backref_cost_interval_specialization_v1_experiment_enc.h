// Copyright 2026
//
// Private controls and untimed work counters for the independent CostManager
// interval-specialization v1 experiment.

#ifndef WEBP_ENC_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostIntervalSpecializationV1ExperimentEnabled(void);
int VP8LBackrefCostIntervalSpecializationV1ExperimentInjectFallback(void);

#if defined(WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER)
typedef struct {
  uint64_t runtime_activations;
  uint64_t injected_fallbacks;
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
} VP8LBackrefCostIntervalSpecializationV1Stats;

void VP8LBackrefCostIntervalSpecializationV1StatsReset(void);
void VP8LBackrefCostIntervalSpecializationV1StatsGet(
    VP8LBackrefCostIntervalSpecializationV1Stats* stats);
void VP8LBackrefCostIntervalSpecializationV1RecordActivation(void);
void VP8LBackrefCostIntervalSpecializationV1RecordInjectedFallback(void);
void VP8LBackrefCostIntervalSpecializationV1RecordPush(int is_short);
void VP8LBackrefCostIntervalSpecializationV1RecordCacheSegment(void);
void VP8LBackrefCostIntervalSpecializationV1RecordOverlapScan(int is_disjoint_prefix);
void VP8LBackrefCostIntervalSpecializationV1RecordInsert(int has_null_hint);
void VP8LBackrefCostIntervalSpecializationV1RecordPositionBackwardStep(void);
void VP8LBackrefCostIntervalSpecializationV1RecordPositionForwardStep(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintFastPath(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintBranchCheck(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintLoad(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintStartLoad(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintUpdate(void);
void VP8LBackrefCostIntervalSpecializationV1RecordPopTailBranchCheck(void);
void VP8LBackrefCostIntervalSpecializationV1RecordPopTailUpdate(void);
void VP8LBackrefCostIntervalSpecializationV1RecordUpdate(void);
void VP8LBackrefCostIntervalSpecializationV1RecordPop(void);
void VP8LBackrefCostIntervalSpecializationV1RecordLiveIntervals(int count);
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT_ENC_H_
