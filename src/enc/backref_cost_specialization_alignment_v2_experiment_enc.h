// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// alignment v2. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_H = 2
} VP8LBackrefCostSpecializationAlignmentV2Variant;

VP8LBackrefCostSpecializationAlignmentV2Variant
VP8LBackrefCostSpecializationAlignmentV2GetVariant(void);

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_RECORDER)
typedef struct {
  uint64_t selector_evaluations;
  uint64_t baseline_dp_calls;
  uint64_t layout_clone_dp_calls;
  uint64_t hint_dp_calls;
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
} VP8LBackrefCostSpecializationAlignmentV2Stats;

void VP8LBackrefCostSpecializationAlignmentV2StatsReset(void);
void VP8LBackrefCostSpecializationAlignmentV2StatsGet(
    VP8LBackrefCostSpecializationAlignmentV2Stats* stats);
void VP8LBackrefCostSpecializationAlignmentV2RecordSelector(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordDP(int variant);
void VP8LBackrefCostSpecializationAlignmentV2RecordActivation(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordPush(int is_short);
void VP8LBackrefCostSpecializationAlignmentV2RecordCacheSegment(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostSpecializationAlignmentV2RecordInsert(int has_null_hint);
void VP8LBackrefCostSpecializationAlignmentV2RecordPositionBackwardStep(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordPositionForwardStep(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintFastPath(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintBranchCheck(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintLoad(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintStartLoad(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordPopTailBranchCheck(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordPopTailUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordPop(void);
void VP8LBackrefCostSpecializationAlignmentV2RecordLiveIntervals(int count);
#endif

// Keep the already-audited factorization call sites structurally identical
// while selecting fresh alignment-v2 recorder/control symbols.
#define VP8LBackrefCostSpecializationFactorizationV1Variant \
  VP8LBackrefCostSpecializationAlignmentV2Variant
#define VP8LBackrefCostSpecializationFactorizationV1GetVariant \
  VP8LBackrefCostSpecializationAlignmentV2GetVariant
#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_RECORDER)
#define VP8LBackrefCostSpecializationFactorizationV1RecordSelector \
  VP8LBackrefCostSpecializationAlignmentV2RecordSelector
#define VP8LBackrefCostSpecializationFactorizationV1RecordDP \
  VP8LBackrefCostSpecializationAlignmentV2RecordDP
#define VP8LBackrefCostSpecializationFactorizationV1RecordActivation \
  VP8LBackrefCostSpecializationAlignmentV2RecordActivation
#define VP8LBackrefCostSpecializationFactorizationV1RecordPush \
  VP8LBackrefCostSpecializationAlignmentV2RecordPush
#define VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment \
  VP8LBackrefCostSpecializationAlignmentV2RecordCacheSegment
#define VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan \
  VP8LBackrefCostSpecializationAlignmentV2RecordOverlapScan
#define VP8LBackrefCostSpecializationFactorizationV1RecordInsert \
  VP8LBackrefCostSpecializationAlignmentV2RecordInsert
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep \
  VP8LBackrefCostSpecializationAlignmentV2RecordPositionBackwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep \
  VP8LBackrefCostSpecializationAlignmentV2RecordPositionForwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintFastPath
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintStartLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdateCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate \
  VP8LBackrefCostSpecializationAlignmentV2RecordAppendHintUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck \
  VP8LBackrefCostSpecializationAlignmentV2RecordPopTailBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate \
  VP8LBackrefCostSpecializationAlignmentV2RecordPopTailUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordUpdate \
  VP8LBackrefCostSpecializationAlignmentV2RecordUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPop \
  VP8LBackrefCostSpecializationAlignmentV2RecordPop
#define VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals \
  VP8LBackrefCostSpecializationAlignmentV2RecordLiveIntervals
#endif

#if defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT)
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
#define WEBP_BACKREF_ALIGNMENT_V2_ENTRY                                  \
  __attribute__((noinline, used,                                         \
                 section("__TEXT,__br_align_v2,regular,pure_instructions"), \
                 aligned(16384)))
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ALIGNMENT_V2_ENTRY                                  \
  __attribute__((noinline, used, section(".text.__br_align_v2"),        \
                 aligned(16384)))
#elif defined(_MSC_VER)
#define WEBP_BACKREF_ALIGNMENT_V2_ENTRY __declspec(noinline)
#else
#define WEBP_BACKREF_ALIGNMENT_V2_ENTRY
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#define WEBP_BACKREF_ALIGNMENT_V2_ENTRY
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V2_EXPERIMENT_ENC_H_
