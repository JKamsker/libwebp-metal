// Copyright 2026

#include "src/enc/backref_cost_specialization_alignment_v2_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

VP8LBackrefCostSpecializationAlignmentV2Variant
VP8LBackrefCostSpecializationAlignmentV2GetVariant(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_VARIANT");
  if (value == NULL || strcmp(value, "B") == 0) {
    return WEBP_BACKREF_FACTORIZATION_VARIANT_B;
  }
  if (strcmp(value, "L") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_L;
  if (strcmp(value, "H") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_H;
  return WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_RECORDER)
#if defined(_MSC_VER)
#define WEBP_ALIGNMENT_V2_TLS __declspec(thread)
#else
#define WEBP_ALIGNMENT_V2_TLS __thread
#endif

static WEBP_ALIGNMENT_V2_TLS
    VP8LBackrefCostSpecializationAlignmentV2Stats stats;

void VP8LBackrefCostSpecializationAlignmentV2StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}
void VP8LBackrefCostSpecializationAlignmentV2StatsGet(
    VP8LBackrefCostSpecializationAlignmentV2Stats* const output) {
  if (output != NULL) *output = stats;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordSelector(void) {
  ++stats.selector_evaluations;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordDP(int variant) {
  if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_B) {
    ++stats.baseline_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_L) {
    ++stats.layout_clone_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_H) {
    ++stats.hint_dp_calls;
  }
}
void VP8LBackrefCostSpecializationAlignmentV2RecordActivation(void) {
  ++stats.exact_activations;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordCacheSegment(void) {
  ++stats.cache_segments;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordInsert(
    int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordUpdate(void) {
  ++stats.interval_updates;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordPop(void) {
  ++stats.interval_pops;
}
void VP8LBackrefCostSpecializationAlignmentV2RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
