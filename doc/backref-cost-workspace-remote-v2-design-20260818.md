# Backref-cost workspace remote v2 design (untimed)

## Base and candidate identity

This serial cycle starts from clean main commit
`d12036f790cce1dd4bef9fe3c963b0ef294d4c4a`. Inspection found no correctness
defect in the validated `CostManager` workspace candidate, so the implementation
boundary is unchanged. The v2 projection preserves its single exact-sized
allocation, 490 workspace interval nodes after the ten inline nodes,
integer arithmetic, strict comparisons and tie-breaking, update and traceback
order, cache/reference choices, and transactional allocation-failure fallback.
No threshold, algorithm, Metal policy, or CUDA path is changed.

The untimed identity test preprocesses the main candidate under its validated
private gate and the v2 candidate under the new private gate. It canonicalizes
only private helper names and source assertion locations, then requires exact
text equality. It separately requires the normalized helper body to match main.

## Independent v2 gates

The v2 identities are wholly new:

- build: `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT`;
- private compile: `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT`;
- runtime: `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT=1`;
- untimed fallback injection:
  `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT_INJECT_FAILURE=1`;
- non-installed runner:
  `backref_cost_workspace_remote_v2_experiment_runner`.

All backref workspace compile gates are mutually exclusive. Default CMake and
Unix make builds omit the v2 helper source, symbol, target, compile definition,
runtime string, and fault string. The runner's session check precedes input
loading and refuses timed use unless `WEBP_BENCHMARK_SESSION=exclusive` is
exact. The design validation does not invoke that runner.

## Untimed correctness scope

The deterministic publication corpus is regenerated and hash-verified. All 13
case/quality rows at methods 4 and 6 require identical baseline, candidate-off,
candidate, repeat, injected-fallback, prior-gate-only, and
default-build-with-v2-environment bitstreams. Candidate output must decode to
the exact source pixels. Undefined/integer and array-bounds/pointer-overflow
sanitizer smoke checks cover both active workspace and fallback paths.

No benchmark lease, timing command, recorder, timed runner, performance sample,
or performance evidence is used by the design commit. The separate protocol
commit is the sole authority for transfer, remote path safety, execution order,
counts, records, statistics, criteria, lease release, evidence return, and
cleanup.
