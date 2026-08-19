// Copyright 2026
//
// Private controls for the diagnostic-only backref-cost attribution v14 build.

#ifndef WEBP_ENC_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT_ENC_H_

#ifdef __cplusplus
extern "C" {
#endif

// Exact-value runtime opt-in. This symbol is private and is present only in
// attribution builds.
int VP8LBackrefCostAttributionV14ExperimentEnabled(void);

typedef struct {
  unsigned int selector_evaluations;
  unsigned int baseline_dp_calls;
  unsigned int candidate_dp_calls;
} VP8LBackrefCostAttributionV14Counters;

// Private diagnostic counters. They are thread-local, reset at every encoder
// profile session, and also exposed to the V14 runner for untimed structural
// validation. They are absent from ordinary builds and public headers.
void VP8LBackrefCostAttributionV14ResetCounters(void);
void VP8LBackrefCostAttributionV14RecordSelector(void);
void VP8LBackrefCostAttributionV14RecordDP(int candidate);
VP8LBackrefCostAttributionV14Counters VP8LBackrefCostAttributionV14GetCounters(
    void);

#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT)
#if defined(_MSC_VER)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE __attribute__((noinline))
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#endif
#else
#define WEBP_BACKREF_ATTRIBUTION_NOINLINE
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT_ENC_H_
