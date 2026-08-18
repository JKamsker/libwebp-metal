# Independent evaluation and consequence

The final-stage independent audit is recorded in
[`doc/cache-size-serial-sweep-experiment-evaluation-20260818.md`](../../doc/cache-size-serial-sweep-experiment-evaluation-20260818.md).

Disposition: **reject**. All 18 correctness cells pass, but all eight
performance cells fail the frozen paired-median and p95 limits. The candidate
remains default off as negative research code. Production defaults, public
ABI/API, cache semantics, thresholds, and fallback behavior are unchanged.

The evaluator ran untimed validation only. No additional timed experiment and
no CUDA command occurred. The next lead is a wholly independent-gate,
single-pass contiguous cache-state layout; it was recorded but not run.
