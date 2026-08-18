# Backref-cost workspace remote A/B design report (untimed)

## Scope and provenance

This independent cycle starts at main commit
`e7c1be7d4070103a9b41b8c30fbbc95cd18e5a5c`. The prior
`backref_cost_traceback` cycle is closed refusal provenance only: Low Power Mode
was enabled on the local MacBook, no timed child was launched, and none of its
artifacts is a performance sample. Its old build, compile, runtime, fault,
schema, lease, operator, and target names are not used by this cycle.

No correctness defect was found in the retained research candidate. The new
experiment therefore preserves the exact one-allocation `CostManager`
workspace, 490 workspace interval nodes after the ten inline nodes, allocation
failure fallback, integer costs, strict comparisons and ties, update order,
traceback, reference sequence, cache choices, bitstream, decoded pixels, and
public API/ABI. It does not tune parameters, thresholds, Metal policy, or CUDA.

## Independent gates and omission

The only new gates are:

- build: `WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT`;
- private compile: `WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT`;
- exact runtime activation: `WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1`;
- private untimed fault injection:
  `WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_INJECT_FAILURE=1`.

The old and new compile macros are mutually exclusive. Default CMake and Unix
make builds omit the new helper source, symbols, runner target, compile macro,
runtime string, and fault string. The runner refuses before input or timing
unless `WEBP_BENCHMARK_SESSION=exclusive` is exact.

## Candidate identity proof

`scripts/test_backref_cost_workspace_ab_experiment.py` preprocesses the merged
research implementation from the exact base commit under the old private macro,
preprocesses the current shared implementation under the new private macro,
canonicalizes only the two private helper symbol names, and requires byte-for-
byte equality. It reports the common SHA-256 projection. The helper bodies are
unchanged except for independent symbol and environment names.

The frozen canonical hashes are:

- preprocessed implementation boundary:
  `b571080f12fee7abe8608696269e35e6bc3184e3a9cf49286cd47075d5a34eea`;
- normalized helper body:
  `28c03ce78195d02baa69dde46ecc043d2b641489188a48c592172140fa3cacd0`.

The same untimed test requires all publication correctness cells at methods 4
and 6 to produce identical baseline, candidate-off, candidate, repeat,
injected-fallback, old-gate-only, and default-build-with-new-environment streams;
checks exact decoded pixels and immutable corpus hashes; checks default omission
and missing-session refusal; and runs undefined/integer plus array-bounds/
pointer-overflow sanitizer activation and fallback smoke tests.

Timed work is expressly outside this design commit. The separately committed
remote protocol is the sole authority for host preflight, transfer, lease,
timing, evidence return, cleanup, criteria, and inventory.
