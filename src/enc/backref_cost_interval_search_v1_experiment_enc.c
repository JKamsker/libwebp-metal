// Copyright 2026
//
// Private runtime gate and optional untimed work recorder for CostManager
// interval-search v1. Recorder code is not compiled into timed candidates.

#include "src/enc/backref_cost_interval_search_v1_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

static int EnvironmentIsOne(const char* const name) {
  const char* const value = getenv(name);
  return value != NULL && strcmp(value, "1") == 0;
}

int VP8LBackrefCostIntervalSearchV1ExperimentEnabled(void) {
  return EnvironmentIsOne("WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT");
}

int VP8LBackrefCostIntervalSearchV1ExperimentInjectFallback(void) {
  return EnvironmentIsOne(
      "WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT_INJECT_FAILURE");
}

#if defined(WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_RECORDER)
static VP8LBackrefCostIntervalSearchV1Stats stats;

void VP8LBackrefCostIntervalSearchV1StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}

void VP8LBackrefCostIntervalSearchV1StatsGet(
    VP8LBackrefCostIntervalSearchV1Stats* const output) {
  if (output != NULL) *output = stats;
}

void VP8LBackrefCostIntervalSearchV1RecordActivation(void) {
  ++stats.runtime_activations;
}

void VP8LBackrefCostIntervalSearchV1RecordInjectedFallback(void) {
  ++stats.injected_fallbacks;
}

void VP8LBackrefCostIntervalSearchV1RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}

void VP8LBackrefCostIntervalSearchV1RecordCacheSegment(void) {
  ++stats.cache_segments;
}

void VP8LBackrefCostIntervalSearchV1RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}

void VP8LBackrefCostIntervalSearchV1RecordInsert(int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}

void VP8LBackrefCostIntervalSearchV1RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}

void VP8LBackrefCostIntervalSearchV1RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}

void VP8LBackrefCostIntervalSearchV1RecordTailFastPath(void) {
  ++stats.tail_fast_paths;
}

void VP8LBackrefCostIntervalSearchV1RecordUpdate(void) {
  ++stats.interval_updates;
}

void VP8LBackrefCostIntervalSearchV1RecordPop(void) {
  ++stats.interval_pops;
}

void VP8LBackrefCostIntervalSearchV1RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
