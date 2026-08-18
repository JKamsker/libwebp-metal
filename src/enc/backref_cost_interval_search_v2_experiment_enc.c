// Copyright 2026
//
// Private runtime gate and optional untimed work recorder for CostManager
// interval-search v2. Recorder code is not compiled into timed candidates.

#include "src/enc/backref_cost_interval_search_v2_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostIntervalSearchV2ExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT");
}

int VP8LBackrefCostIntervalSearchV2ExperimentInjectFallback(void) {
  return EnvironmentIsOne(
      "WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT_INJECT_FAILURE");
}

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER)
static VP8LBackrefCostIntervalSearchV2Stats stats;

void VP8LBackrefCostIntervalSearchV2StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}

void VP8LBackrefCostIntervalSearchV2StatsGet(
    VP8LBackrefCostIntervalSearchV2Stats* const output) {
  if (output != NULL) *output = stats;
}

void VP8LBackrefCostIntervalSearchV2RecordActivation(void) {
  ++stats.runtime_activations;
}

void VP8LBackrefCostIntervalSearchV2RecordInjectedFallback(void) {
  ++stats.injected_fallbacks;
}

void VP8LBackrefCostIntervalSearchV2RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}

void VP8LBackrefCostIntervalSearchV2RecordCacheSegment(void) {
  ++stats.cache_segments;
}

void VP8LBackrefCostIntervalSearchV2RecordOverlapScan(int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}

void VP8LBackrefCostIntervalSearchV2RecordInsert(int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}

void VP8LBackrefCostIntervalSearchV2RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}

void VP8LBackrefCostIntervalSearchV2RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}

void VP8LBackrefCostIntervalSearchV2RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}

void VP8LBackrefCostIntervalSearchV2RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}

void VP8LBackrefCostIntervalSearchV2RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}

void VP8LBackrefCostIntervalSearchV2RecordUpdate(void) {
  ++stats.interval_updates;
}

void VP8LBackrefCostIntervalSearchV2RecordPop(void) {
  ++stats.interval_pops;
}

void VP8LBackrefCostIntervalSearchV2RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
