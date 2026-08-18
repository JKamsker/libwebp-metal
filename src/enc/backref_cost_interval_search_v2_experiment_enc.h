// Copyright 2026
//
// Private controls and untimed work counters for the independent CostManager
// interval-search v2 experiment.

#ifndef WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostIntervalSearchV2ExperimentEnabled(void);
int VP8LBackrefCostIntervalSearchV2ExperimentInjectFallback(void);

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
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
} VP8LBackrefCostIntervalSearchV2Stats;

void VP8LBackrefCostIntervalSearchV2StatsReset(void);
void VP8LBackrefCostIntervalSearchV2StatsGet(
    VP8LBackrefCostIntervalSearchV2Stats* stats);
void VP8LBackrefCostIntervalSearchV2RecordActivation(void);
void VP8LBackrefCostIntervalSearchV2RecordInjectedFallback(void);
void VP8LBackrefCostIntervalSearchV2RecordPush(int is_short);
void VP8LBackrefCostIntervalSearchV2RecordCacheSegment(void);
void VP8LBackrefCostIntervalSearchV2RecordOverlapScan(int is_disjoint_prefix);
void VP8LBackrefCostIntervalSearchV2RecordInsert(int has_null_hint);
void VP8LBackrefCostIntervalSearchV2RecordPositionBackwardStep(void);
void VP8LBackrefCostIntervalSearchV2RecordPositionForwardStep(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintFastPath(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintBranchCheck(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintLoad(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintStartLoad(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostIntervalSearchV2RecordAppendHintUpdate(void);
void VP8LBackrefCostIntervalSearchV2RecordPopTailBranchCheck(void);
void VP8LBackrefCostIntervalSearchV2RecordPopTailUpdate(void);
void VP8LBackrefCostIntervalSearchV2RecordUpdate(void);
void VP8LBackrefCostIntervalSearchV2RecordPop(void);
void VP8LBackrefCostIntervalSearchV2RecordLiveIntervals(int count);
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT_ENC_H_
