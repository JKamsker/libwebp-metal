// Copyright 2026
//
// Private runtime gate and optional untimed work recorder for CostManager
// interval-search v3. Recorder code is not compiled into timed candidates.

#include "src/enc/backref_cost_interval_search_v3_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostIntervalSearchV3ExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT");
}

int VP8LBackrefCostIntervalSearchV3ExperimentInjectFallback(void) {
  return EnvironmentIsOne(
      "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT_INJECT_FAILURE");
}

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_RECORDER)
static VP8LBackrefCostIntervalSearchV3Stats stats;

void VP8LBackrefCostIntervalSearchV3StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}

void VP8LBackrefCostIntervalSearchV3StatsGet(
    VP8LBackrefCostIntervalSearchV3Stats* const output) {
  if (output != NULL) *output = stats;
}

void VP8LBackrefCostIntervalSearchV3RecordActivation(void) {
  ++stats.runtime_activations;
}

void VP8LBackrefCostIntervalSearchV3RecordInjectedFallback(void) {
  ++stats.injected_fallbacks;
}

void VP8LBackrefCostIntervalSearchV3RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}

void VP8LBackrefCostIntervalSearchV3RecordCacheSegment(void) {
  ++stats.cache_segments;
}

void VP8LBackrefCostIntervalSearchV3RecordOverlapScan(int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}

void VP8LBackrefCostIntervalSearchV3RecordInsert(int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}

void VP8LBackrefCostIntervalSearchV3RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}

void VP8LBackrefCostIntervalSearchV3RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}

void VP8LBackrefCostIntervalSearchV3RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}

void VP8LBackrefCostIntervalSearchV3RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}

void VP8LBackrefCostIntervalSearchV3RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}

void VP8LBackrefCostIntervalSearchV3RecordUpdate(void) {
  ++stats.interval_updates;
}

void VP8LBackrefCostIntervalSearchV3RecordPop(void) {
  ++stats.interval_pops;
}

void VP8LBackrefCostIntervalSearchV3RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
