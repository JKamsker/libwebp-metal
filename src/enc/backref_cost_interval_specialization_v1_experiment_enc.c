// Copyright 2026
//
// Private runtime gate and optional untimed work recorder for CostManager
// interval-specialization v1. Recorder code is not compiled into timed candidates.

#include "src/enc/backref_cost_interval_specialization_v1_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostIntervalSpecializationV1ExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT");
}

int VP8LBackrefCostIntervalSpecializationV1ExperimentInjectFallback(void) {
  return EnvironmentIsOne(
      "WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT_INJECT_FAILURE");
}

#if defined(WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER)
static VP8LBackrefCostIntervalSpecializationV1Stats stats;

void VP8LBackrefCostIntervalSpecializationV1StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}

void VP8LBackrefCostIntervalSpecializationV1StatsGet(
    VP8LBackrefCostIntervalSpecializationV1Stats* const output) {
  if (output != NULL) *output = stats;
}

void VP8LBackrefCostIntervalSpecializationV1RecordActivation(void) {
  ++stats.runtime_activations;
}

void VP8LBackrefCostIntervalSpecializationV1RecordInjectedFallback(void) {
  ++stats.injected_fallbacks;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}

void VP8LBackrefCostIntervalSpecializationV1RecordCacheSegment(void) {
  ++stats.cache_segments;
}

void VP8LBackrefCostIntervalSpecializationV1RecordOverlapScan(int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}

void VP8LBackrefCostIntervalSpecializationV1RecordInsert(int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}

void VP8LBackrefCostIntervalSpecializationV1RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}

void VP8LBackrefCostIntervalSpecializationV1RecordUpdate(void) {
  ++stats.interval_updates;
}

void VP8LBackrefCostIntervalSpecializationV1RecordPop(void) {
  ++stats.interval_pops;
}

void VP8LBackrefCostIntervalSpecializationV1RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
