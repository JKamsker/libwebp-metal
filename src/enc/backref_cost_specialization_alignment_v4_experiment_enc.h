// Copyright 2026
//
// Private controls and untimed work recorder for backref-cost specialization
// alignment v4. Recorder declarations are absent from timed builds.

#ifndef WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_EXPERIMENT_ENC_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  WEBP_BACKREF_FACTORIZATION_VARIANT_INVALID = -1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_B = 0,
  WEBP_BACKREF_FACTORIZATION_VARIANT_L = 1,
  WEBP_BACKREF_FACTORIZATION_VARIANT_H = 2
} VP8LBackrefCostSpecializationAlignmentV4Variant;

VP8LBackrefCostSpecializationAlignmentV4Variant
VP8LBackrefCostSpecializationAlignmentV4GetVariant(void);

#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_RECORDER)
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
} VP8LBackrefCostSpecializationAlignmentV4Stats;

void VP8LBackrefCostSpecializationAlignmentV4StatsReset(void);
void VP8LBackrefCostSpecializationAlignmentV4StatsGet(
    VP8LBackrefCostSpecializationAlignmentV4Stats* stats);
void VP8LBackrefCostSpecializationAlignmentV4RecordSelector(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordDP(int variant);
void VP8LBackrefCostSpecializationAlignmentV4RecordActivation(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordPush(int is_short);
void VP8LBackrefCostSpecializationAlignmentV4RecordCacheSegment(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordOverlapScan(
    int is_disjoint_prefix);
void VP8LBackrefCostSpecializationAlignmentV4RecordInsert(int has_null_hint);
void VP8LBackrefCostSpecializationAlignmentV4RecordPositionBackwardStep(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordPositionForwardStep(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintFastPath(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintBranchCheck(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintLoad(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintStartLoad(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintUpdateCheck(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordPopTailBranchCheck(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordPopTailUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordUpdate(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordPop(void);
void VP8LBackrefCostSpecializationAlignmentV4RecordLiveIntervals(int count);
#endif

// Keep the already-audited factorization call sites structurally identical
// while selecting fresh alignment-v4 recorder/control symbols.
#define VP8LBackrefCostSpecializationFactorizationV1Variant \
  VP8LBackrefCostSpecializationAlignmentV4Variant
#define VP8LBackrefCostSpecializationFactorizationV1GetVariant \
  VP8LBackrefCostSpecializationAlignmentV4GetVariant
#if defined(WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_RECORDER)
#define VP8LBackrefCostSpecializationFactorizationV1RecordSelector \
  VP8LBackrefCostSpecializationAlignmentV4RecordSelector
#define VP8LBackrefCostSpecializationFactorizationV1RecordDP \
  VP8LBackrefCostSpecializationAlignmentV4RecordDP
#define VP8LBackrefCostSpecializationFactorizationV1RecordActivation \
  VP8LBackrefCostSpecializationAlignmentV4RecordActivation
#define VP8LBackrefCostSpecializationFactorizationV1RecordPush \
  VP8LBackrefCostSpecializationAlignmentV4RecordPush
#define VP8LBackrefCostSpecializationFactorizationV1RecordCacheSegment \
  VP8LBackrefCostSpecializationAlignmentV4RecordCacheSegment
#define VP8LBackrefCostSpecializationFactorizationV1RecordOverlapScan \
  VP8LBackrefCostSpecializationAlignmentV4RecordOverlapScan
#define VP8LBackrefCostSpecializationFactorizationV1RecordInsert \
  VP8LBackrefCostSpecializationAlignmentV4RecordInsert
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionBackwardStep \
  VP8LBackrefCostSpecializationAlignmentV4RecordPositionBackwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordPositionForwardStep \
  VP8LBackrefCostSpecializationAlignmentV4RecordPositionForwardStep
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintFastPath \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintFastPath
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintBranchCheck \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintLoad \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintStartLoad \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintStartLoad
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdateCheck \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintUpdateCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordAppendHintUpdate \
  VP8LBackrefCostSpecializationAlignmentV4RecordAppendHintUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailBranchCheck \
  VP8LBackrefCostSpecializationAlignmentV4RecordPopTailBranchCheck
#define VP8LBackrefCostSpecializationFactorizationV1RecordPopTailUpdate \
  VP8LBackrefCostSpecializationAlignmentV4RecordPopTailUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordUpdate \
  VP8LBackrefCostSpecializationAlignmentV4RecordUpdate
#define VP8LBackrefCostSpecializationFactorizationV1RecordPop \
  VP8LBackrefCostSpecializationAlignmentV4RecordPop
#define VP8LBackrefCostSpecializationFactorizationV1RecordLiveIntervals \
  VP8LBackrefCostSpecializationAlignmentV4RecordLiveIntervals
#endif

#if defined(WEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_EXPERIMENT)
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
#define WEBP_BACKREF_ALIGNMENT_V4_ENTRY                                  \
  __attribute__((noinline, used,                                         \
                 section("__TEXT,__br_align_v4,regular,pure_instructions"), \
                 aligned(16384)))
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ALIGNMENT_V4_ENTRY                                  \
  __attribute__((noinline, used, section(".text.__br_align_v4"),        \
                 aligned(16384)))
#elif defined(_MSC_VER)
#define WEBP_BACKREF_ALIGNMENT_V4_ENTRY __declspec(noinline)
#else
#define WEBP_BACKREF_ALIGNMENT_V4_ENTRY
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#define WEBP_BACKREF_ALIGNMENT_V4_ENTRY
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V4_EXPERIMENT_ENC_H_
