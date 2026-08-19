// Copyright 2026
//
// Private controls for the diagnostic-only backref-cost attribution v6 build.

#ifndef WEBP_ENC_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT_ENC_H_

#ifdef __cplusplus
extern "C" {
#endif

// Exact-value runtime opt-in. This symbol is private and is present only in
// attribution builds.
int VP8LBackrefCostAttributionV6ExperimentEnabled(void);

typedef struct {
  unsigned int selector_evaluations;
  unsigned int baseline_dp_calls;
  unsigned int candidate_dp_calls;
} VP8LBackrefCostAttributionV6Counters;

// Private diagnostic counters. They are thread-local, reset at every encoder
// profile session, and also exposed to the V6 runner for untimed structural
// validation. They are absent from ordinary builds and public headers.
void VP8LBackrefCostAttributionV6ResetCounters(void);
void VP8LBackrefCostAttributionV6RecordSelector(void);
void VP8LBackrefCostAttributionV6RecordDP(int candidate);
VP8LBackrefCostAttributionV6Counters VP8LBackrefCostAttributionV6GetCounters(
    void);

#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT)
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

#endif  // WEBP_ENC_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT_ENC_H_
