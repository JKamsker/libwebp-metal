// Copyright 2026

#include "src/enc/backref_cost_specialization_factorization_v4_experiment_enc.h"

#include <stdlib.h>
#include <string.h>

VP8LBackrefCostSpecializationFactorizationV4Variant
VP8LBackrefCostSpecializationFactorizationV4GetVariant(void) {
  const char* const value =
      getenv("WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_VARIANT");
  if (value == NULL || strcmp(value, "B") == 0) {
    return WEBP_BACKREF_FACTORIZATION_VARIANT_B;
  }
  if (strcmp(value, "L") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_L;
  if (strcmp(value, "H") == 0) return WEBP_BACKREF_FACTORIZATION_VARIANT_H;
  return WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID;
}

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_RECORDER)
#if defined(_MSC_VER)
#define WEBP_FACTORIZATION_V4_TLS __declspec(thread)
#else
#define WEBP_FACTORIZATION_V4_TLS __thread
#endif

static WEBP_FACTORIZATION_V4_TLS
    VP8LBackrefCostSpecializationFactorizationV4Stats stats;

void VP8LBackrefCostSpecializationFactorizationV4StatsReset(void) {
  memset(&stats, 0, sizeof(stats));
}
void VP8LBackrefCostSpecializationFactorizationV4StatsGet(
    VP8LBackrefCostSpecializationFactorizationV4Stats* const output) {
  if (output != NULL) *output = stats;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordSelector(void) {
  ++stats.selector_evaluations;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordDP(int variant) {
  if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_B) {
    ++stats.baseline_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_L) {
    ++stats.layout_clone_dp_calls;
  } else if (variant == WEBP_BACKREF_FACTORIZATION_VARIANT_H) {
    ++stats.hint_dp_calls;
  }
}
void VP8LBackrefCostSpecializationFactorizationV4RecordActivation(void) {
  ++stats.exact_activations;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPush(int is_short) {
  ++stats.push_calls;
  if (is_short) ++stats.short_push_calls;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordCacheSegment(void) {
  ++stats.cache_segments;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordOverlapScan(
    int is_disjoint_prefix) {
  ++stats.overlap_scans;
  if (is_disjoint_prefix) ++stats.disjoint_prefix_scans;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordInsert(
    int has_null_hint) {
  ++stats.insert_calls;
  if (has_null_hint) ++stats.null_hint_insert_calls;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPositionBackwardStep(void) {
  ++stats.position_backward_steps;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPositionForwardStep(void) {
  ++stats.position_forward_steps;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintFastPath(void) {
  ++stats.append_hint_fast_paths;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintBranchCheck(void) {
  ++stats.append_hint_branch_checks;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintLoad(void) {
  ++stats.append_hint_loads;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintStartLoad(void) {
  ++stats.append_hint_start_loads;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintUpdateCheck(void) {
  ++stats.append_hint_update_checks;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordAppendHintUpdate(void) {
  ++stats.append_hint_updates;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPopTailBranchCheck(void) {
  ++stats.pop_tail_branch_checks;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPopTailUpdate(void) {
  ++stats.pop_tail_updates;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordUpdate(void) {
  ++stats.interval_updates;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordPop(void) {
  ++stats.interval_pops;
}
void VP8LBackrefCostSpecializationFactorizationV4RecordLiveIntervals(int count) {
  if (count > 0 && (uint64_t)count > stats.max_live_intervals) {
    stats.max_live_intervals = (uint64_t)count;
  }
}
#endif
