// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// aligned null stage attribution v1. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1
} VP8LBackrefCostAlignedNullStageAttributionV1Variant;

VP8LBackrefCostAlignedNullStageAttributionV1Variant
VP8LBackrefCostAlignedNullStageAttributionV1GetVariant(void);

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_RECORDER)
typedef struct {
  uint64_t selector_evaluations;
  uint64_t baseline_dp_calls;
  uint64_t layout_clone_dp_calls;
  uint64_t exact_activations;
  uint64_t push_calls;
  uint64_t short_push_calls;
  uint64_t cache_segments;
  uint64_t overlap_scans;
  uint64_t disjoint_prefix_scans;
  uint64_t insert_calls;
  uint64_t null_hint_insert_calls;
  uint64_t position_backward_steps;
  uint64_t position_forward_steps;
  uint64_t append_hint_fast_paths;
  uint64_t append_hint_branch_checks;
  uint64_t append_hint_loads;
  uint64_t append_hint_start_loads;
  uint64_t append_hint_update_checks;
  uint64_t append_hint_updates;
  uint64_t pop_tail_branch_checks;
  uint64_t pop_tail_updates;
  uint64_t interval_updates;
  uint64_t interval_pops;
  uint64_t max_live_intervals;
} VP8LBackrefCostAlignedNullStageAttributionV1Stats;

void VP8LBackrefCostAlignedNullStageAttributionV1StatsReset(void);
void VP8LBackrefCostAlignedNullStageAttributionV1StatsGet(
    VP8LBackrefCostAlignedNullStageAttributionV1Stats* stats);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordSelector(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordDP(int variant);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordActivation(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPush(int is_short);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordCacheSegment(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordInsert(int has_null_hint);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionBackwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionForwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintFastPath(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintStartLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordPop(void);
void VP8LBackrefCostAlignedNullStageAttributionV1RecordLiveIntervals(int count);
#endif

// Keep the already-audited factorization call sites structurally identical
// while selecting fresh B/L-only recorder/control symbols.
#define VP8LBackrefCostSpecializationFactorizationV1Variant \
  VP8LBackrefCostAlignedNullStageAttributionV1Variant
#define VP8LBackrefCostSpecializationFactorizationV1GetVariant \
  VP8LBackrefCostAlignedNullStageAttributionV1GetVariant
#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_RECORDER)
#define VP8LBackrefCostSpecializationFactorizationV1RecordSelector \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordSelector
#define VP8LBackrefCostSpecializationFactorizationV1RecordDP \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordDP
#define VP8LBackrefCostSpecializationFactorizationV1RecordActivation \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordActivation
#define VP8LBackrefCostSpecializationFactorizationV1RecordPush \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPush
#define VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordCacheSegment
#define VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordOverlapScan
#define VP8LBackrefCostSpecializationFactorizationV1RecordInsert \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordInsert
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionBackwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPositionForwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintFastPath
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintStartLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdateCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordAppendHintUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPopTailUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPop \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordPop
#define VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals \
  VP8LBackrefCostAlignedNullStageAttributionV1RecordLiveIntervals
#endif

#if defined(WEBP_USE_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_EXPERIMENT)
#if defined(_MSC_VER)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __attribute__((noinline))
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#endif

// Apple Silicon uses a 16 KiB VM page.  Keeping every diagnostic entry at the
// start of a 16 KiB page normalizes both its page offset and every smaller
// power-of-two I-cache-line offset.  The dedicated executable section makes
// linker order and padding independently auditable.  Non-Apple support is
// compile-only; the frozen diagnostic admits Darwin arm64 only.
#if defined(__APPLE__) && (defined(__GNUC__) || defined(__clang__))
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_ENTRY                                  \
  __attribute__((noinline, used,                                         \
                 section("__TEXT,__br_null_v1,regular,pure_instructions"), \
                 aligned(16384)))
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_ENTRY                                  \
  __attribute__((noinline, used, section(".text.__br_null_v1"),        \
                 aligned(16384)))
#elif defined(_MSC_VER)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_ENTRY __declspec(noinline)
#else
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_ENTRY
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_ENTRY
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_EXPERIMENT_ENC_H_
