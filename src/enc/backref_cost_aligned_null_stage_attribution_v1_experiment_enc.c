// Copyright 2026

#include "src/enc/backref_cost_aligned_null_stage_attribution_v1_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

VP8LBackrefCostAlignedNullStageAttributionV1Variant
VP8LBackrefCostAlignedNullStageAttributionV1GetVariant(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_VARIANT");
  if (value == NULL || strcmp(value, "B") == 0) {
    return WEBP_BACKREF_FACTORIZATION_VARIANT_B;
  }
  if (strcmp(value, "L") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_L;
  return WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_RECORDER)
#if defined(_MSC_VER)
#define WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_TLS __declspec(thread)
#else
#define WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_TLS __thread
#endif

static WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_TLS
    VP8LBackrefCostAlignedNullStageAttributionV1Stats stats;

void VP8LBackrefCostAlignedNullStageAttributionV1StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}
void VP8LBackrefCostAlignedNullStageAttributionV1StatsGet(
    VP8LBackrefCostAlignedNullStageAttributionV1Stats* const output) {
  if (output != NULL) *output = stats;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordSelector(void) {
  ++stats.selector_evaluations;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordDP(int variant) {
  if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_B) {
    ++stats.baseline_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_L) {
    ++stats.layout_clone_dp_calls;
  }
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordActivation(void) {
  ++stats.exact_activations;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordCacheSegment(void) {
  ++stats.cache_segments;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordInsert(
    int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordUpdate(void) {
  ++stats.interval_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPop(void) {
  ++stats.interval_pops;
}
void VP8LBackrefCostAlignedNullStageAttributionV1RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
