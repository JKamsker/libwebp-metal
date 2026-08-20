// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// aligned null stage attribution v3. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1
} VP8LBackrefCostAlignedNullStageAttributionV3Variant;

VP8LBackrefCostAlignedNullStageAttributionV3Variant
VP8LBackrefCostAlignedNullStageAttributionV3GetVariant(void);

#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
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
} VP8LBackrefCostAlignedNullStageAttributionV3Stats;

void VP8LBackrefCostAlignedNullStageAttributionV3StatsReset(void);
void VP8LBackrefCostAlignedNullStageAttributionV3StatsGet(
    VP8LBackrefCostAlignedNullStageAttributionV3Stats* stats);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordSelector(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordDP(int variant);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordActivation(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPush(int is_short);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordCacheSegment(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordInsert(int has_null_hint);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPositionBackwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPositionForwardStep(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintFastPath(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintStartLoad(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPopTailBranchCheck(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPopTailUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordUpdate(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordPop(void);
void VP8LBackrefCostAlignedNullStageAttributionV3RecordLiveIntervals(int count);
#endif

// Keep the already-audited factorization call sites structurally identical
// while selecting fresh B/L-only recorder/control symbols.
#define VP8LBackrefCostSpecializationFactorizationV1Variant \
  VP8LBackrefCostAlignedNullStageAttributionV3Variant
#define VP8LBackrefCostSpecializationFactorizationV1GetVariant \
  VP8LBackrefCostAlignedNullStageAttributionV3GetVariant
#if defined(WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER)
#define VP8LBackrefCostSpecializationFactorizationV1RecordSelector \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordSelector
#define VP8LBackrefCostSpecializationFactorizationV1RecordDP \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordDP
#define VP8LBackrefCostSpecializationFactorizationV1RecordActivation \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordActivation
#define VP8LBackrefCostSpecializationFactorizationV1RecordPush \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPush
#define VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordCacheSegment
#define VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordOverlapScan
#define VP8LBackrefCostSpecializationFactorizationV1RecordInsert \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordInsert
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPositionBackwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPositionForwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintFastPath
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintStartLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintUpdateCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordAppendHintUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPopTailBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPopTailUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordUpdate \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPop \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordPop
#define VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals \
  VP8LBackrefCostAlignedNullStageAttributionV3RecordLiveIntervals
#endif

#if defined(WEBP_USE_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT)
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
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_ENTRY                                  \
  __attribute__((noinline, used,                                         \
                 section("__TEXT,__br_null_v3,regular,pure_instructions"), \
                 aligned(16384)))
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_ENTRY                                  \
  __attribute__((noinline, used, section(".text.__br_null_v3"),        \
                 aligned(16384)))
#elif defined(_MSC_VER)
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_ENTRY __declspec(noinline)
#else
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_ENTRY
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#define WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_ENTRY
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT_ENC_H_
