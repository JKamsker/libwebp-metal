// Copyright 2026
//
// Private controls and untimed work counters for the independent CostManager
// interval-search v1 experiment.

#ifndef WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int VP8LBackrefCostIntervalSearchV1ExperimentEnabled(void);
int VP8LBackrefCostIntervalSearchV1ExperimentInjectFallback(void);

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_RECORDER)
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
  uint64_t tail_fast_paths;
  uint64_t interval_updates;
  uint64_t interval_pops;
  uint64_t max_live_intervals;
} VP8LBackrefCostIntervalSearchV1Stats;

void VP8LBackrefCostIntervalSearchV1StatsReset(void);
void VP8LBackrefCostIntervalSearchV1StatsGet(
    VP8LBackrefCostIntervalSearchV1Stats* stats);
void VP8LBackrefCostIntervalSearchV1RecordActivation(void);
void VP8LBackrefCostIntervalSearchV1RecordInjectedFallback(void);
void VP8LBackrefCostIntervalSearchV1RecordPush(int is_short);
void VP8LBackrefCostIntervalSearchV1RecordCacheSegment(void);
void VP8LBackrefCostIntervalSearchV1RecordOverlapScan(int is_disjoint_prefix);
void VP8LBackrefCostIntervalSearchV1RecordInsert(int has_null_hint);
void VP8LBackrefCostIntervalSearchV1RecordPositionBackwardStep(void);
void VP8LBackrefCostIntervalSearchV1RecordPositionForwardStep(void);
void VP8LBackrefCostIntervalSearchV1RecordTailFastPath(void);
void VP8LBackrefCostIntervalSearchV1RecordUpdate(void);
void VP8LBackrefCostIntervalSearchV1RecordPop(void);
void VP8LBackrefCostIntervalSearchV1RecordLiveIntervals(int count);
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT_ENC_H_
