// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// aligned null stage attribution v4. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1
} VP8LBackrefCostAlignedNullStageAttributionV4Variant;

VP8LBackrefCostAlignedNullStageAttributionV4Variant
VP8LBackrefCostAlignedNullStageAttributionV4GetVariant(void);

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_RECORDER)
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
} VP8LBackrefCostAlignedNullStageAttributionV4Stats;

void VP8LBackrefCostAlignedNullStageAttributionV4StatsReset(void);
void VP8LBackrefCostAlignedNullStageAttributionV4StatsGet(
    VP8LBackrefCostAlignedNullStageAttributionV4Stats* stats);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordSelector(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordDP(int variant);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordActivation(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPush(int is_short);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordCacheSegment(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordInsert(int has_null_hint);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionBackwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionForwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintFastPath(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintStartLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordPop(void);
void VP8LBackrefCostAlignedNullStageAttributionV4RecordLiveIntervals(int count);
#endif

// Keep the already-audited factorization call sites structurally identical
// while selecting fresh B/L-only recorder/control symbols.
#define VP8LBackrefCostSpecializationFactorizationV1Variant \
  VP8LBackrefCostAlignedNullStageAttributionV4Variant
#define VP8LBackrefCostSpecializationFactorizationV1GetVariant \
  VP8LBackrefCostAlignedNullStageAttributionV4GetVariant
#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_RECORDER)
#define VP8LBackrefCostSpecializationFactorizationV1RecordSelector \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordSelector
#define VP8LBackrefCostSpecializationFactorizationV1RecordDP \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordDP
#define VP8LBackrefCostSpecializationFactorizationV1RecordActivation \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordActivation
#define VP8LBackrefCostSpecializationFactorizationV1RecordPush \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPush
#define VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordCacheSegment
#define VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordOverlapScan
#define VP8LBackrefCostSpecializationFactorizationV1RecordInsert \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordInsert
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionBackwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPositionForwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintFastPath
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintStartLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdateCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordAppendHintUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPopTailUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPop \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordPop
#define VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals \
  VP8LBackrefCostAlignedNullStageAttributionV4RecordLiveIntervals
#endif

#if defined(WEBP_USE_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_EXPERIMENT)
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
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY                                  \
  __attribute__((noinline, used,                                         \
                 section("__TEXT,__br_null_v4,regular,pure_instructions"), \
                 aligned(16384)))
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY                                  \
  __attribute__((noinline, used, section(".text.__br_null_v4"),        \
                 aligned(16384)))
#elif defined(_MSC_VER)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY __declspec(noinline)
#else
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_EXPERIMENT_ENC_H_
