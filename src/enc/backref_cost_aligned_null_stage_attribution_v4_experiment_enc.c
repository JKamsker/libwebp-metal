// Copyright 2026

#include "src/enc/backref_cost_aligned_null_stage_attribution_v4_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

VP8LBackrefCostAlignedNullStageAttributionV4Variant
VP8LBackrefCostAlignedNullStageAttributionV4GetVariant(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_VARIANT");
  if (value == NULL || strcmp(value, "B") == 0) {
    return WEBP_BACKREF_FACTORIZATION_VARIANT_B;
  }
  if (strcmp(value, "L") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_L;
  return WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_RECORDER)
#if defined(_MSC_VER)
#define WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_TLS __declspec(thread)
#else
#define WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_TLS __thread
#endif

static WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_TLS
    VP8LBackrefCostAlignedNullStageAttributionV4Stats stats;

void VP8LBackrefCostAlignedNullStageAttributionV4StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}
void VP8LBackrefCostAlignedNullStageAttributionV4StatsGet(
    VP8LBackrefCostAlignedNullStageAttributionV4Stats* const output) {
  if (output != NULL) *output = stats;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordSelector(void) {
  ++stats.selector_evaluations;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordDP(int variant) {
  if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_B) {
    ++stats.baseline_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_L) {
    ++stats.layout_clone_dp_calls;
  }
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordActivation(void) {
  ++stats.exact_activations;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordCacheSegment(void) {
  ++stats.cache_segments;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordInsert(
    int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordUpdate(void) {
  ++stats.interval_updates;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPop(void) {
  ++stats.interval_pops;
}
void VP8LBackrefCostAlignedNullStageAttributionV4RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
