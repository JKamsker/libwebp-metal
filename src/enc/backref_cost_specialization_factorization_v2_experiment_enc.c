// Copyright 2026

#include "src/enc/backref_cost_specialization_factorization_v2_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

VP8LBackrefCostSpecializationFactorizationV2Variant
VP8LBackrefCostSpecializationFactorizationV2GetVariant(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_VARIANT");
  if (value == NULL || strcmp(value, "B") == 0) {
    return WEBP_BACKREF_FACTORIZATION_VARIANT_B;
  }
  if (strcmp(value, "L") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_L;
  if (strcmp(value, "H") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_H;
  return WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V2_RECORDER)
#if defined(_MSC_VER)
#define WEBP_FACTORIZATION_V2_TLS __declspec(thread)
#else
#define WEBP_FACTORIZATION_V2_TLS __thread
#endif

static WEBP_FACTORIZATION_V2_TLS
    VP8LBackrefCostSpecializationFactorizationV2Stats stats;

void VP8LBackrefCostSpecializationFactorizationV2StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}
void VP8LBackrefCostSpecializationFactorizationV2StatsGet(
    VP8LBackrefCostSpecializationFactorizationV2Stats* const output) {
  if (output != NULL) *output = stats;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordSelector(void) {
  ++stats.selector_evaluations;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordDP(int variant) {
  if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_B) {
    ++stats.baseline_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_L) {
    ++stats.layout_clone_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_H) {
    ++stats.hint_dp_calls;
  }
}
void VP8LBackrefCostSpecializationFactorizationV2RecordActivation(void) {
  ++stats.exact_activations;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordCacheSegment(void) {
  ++stats.cache_segments;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordInsert(
    int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordUpdate(void) {
  ++stats.interval_updates;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordPop(void) {
  ++stats.interval_pops;
}
void VP8LBackrefCostSpecializationFactorizationV2RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
