# Backref-cost attribution v1 — Phase 3 evaluation

> **Safety remediation (2026-08-19):** the root Codex session audit established
> that Phase 1 sent SIGTERM to unrelated user-owned interactive SSH PID `28860`.
> This was an unauthorized external-session termination, not valid experiment
> cleanup. The [root incident audit](backref-cost-attribution-v1-incident-audit-20260819.md)
> and its [machine-readable record](../evidence/backref-cost-attribution-v1-remediation-20260819/incident.json)
> supersede this document's incomplete safety interpretation. Frozen Phase 1,
> 2, and 3 evidence is unchanged.

## Decision

The diagnostic is inconclusive because Phase 2 stopped at the frozen local
authorization gate before remote admission. It produced zero profiles, zero
samples, and zero stage records. The attribution question is therefore
unresolved: this cycle does not support closing the interval-search family,
reopening it, assigning a dominant CPU stage, or naming a quantified next
internal boundary. No follow-up experiment is proposed or run here.

This is a protocol/code validation result, not performance evidence and never
production-promotion authority.

## Ancestry and frozen identity

- Base `db1d9e8e66055ff943f57664733316df83b0a965` is the exact parent of Phase 1
  `454946a800124781296cd5d3a34772d4228103be`.
- Phase 1 is the exact parent of Phase 2
  `ebfac68393959fd79e60039eb3d911fcad0181ad`.
- All 23 frozen artifact hashes in
  `scripts/backref_cost_attribution_v1_manifest.json` match.
- The Phase 3 protocol test independently confirms that the current
  `PushIntervalSpecialized` body is byte-for-byte identical to the body in
  `673bc3fa`, that attribution selects the exact specialized distance-only DP
  behind the fresh runtime identity, and that the attribution selector has no
  fallback fault injection.

## Code and protocol audit

The fresh identities are present and default-off:

- build: `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT`;
- compile: `WEBP_USE_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT`;
- runtime: `WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT=1`;
- markers: `WEBP_BACKREF_COST_ATTRIBUTION_V1_MARKERS`.

The 21-row static guard suite passed. Attribution objects, markers, and runner
are absent from the ordinary make plan, the CMake option defaults to `OFF`, the
make option defaults to `0`, and build logic refuses every frozen overlapping
backref/stage experiment. No public header or export-control file differs from
the base commit. Phase 1 records a passing public-header/linker-map comparison;
Phase 3 did not rebuild the ABI.

The frozen plan itself is coherent and remains unexecuted: `photo-large` then
`graphic-large`, methods 4 then 6, three profiles per variant and cell, variant
orders B/C, C/B, B/C, one warmup and four retained encodes per profile. That is
24 strictly serial profiles, 120 timer records, 24 warmups, and 96 retained
records under one lease. The contract test reconstructed all 24 commands in
the frozen order without invoking a profiler or encoder.

Phase 1's read-only facility inventory records macOS 26.2/arm64, Xcode 26.3.0,
`xctrace` 26.0, Apple clang 17, the macOS 26.2 SDK, tool executable hashes, and
the frozen `-O3 -g -DNDEBUG -fno-omit-frame-pointer` policy. Those are frozen
inspection claims only. The noninteractive remote rehearsal did not complete,
so no remote attribution runner SHA-256, Mach-O/dSYM UUID pair, realized
compiler/SDK/build identity, or trace symbolization was established for Phase
2.

## Phase 2 evidence and acceptance

Phase 2 invoked this command exactly once:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V1_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v1.py run \
  "$PWD/evidence/backref-cost-attribution-v1-execution-20260819"
```

The expected commit expanded to
`454946a800124781296cd5d3a34772d4228103be`. The command returned 1 with:

```text
ERROR: phase-1 handoff rejected timing; see frozen blocker evidence
```

The refusal occurred before `prepare_remote`: no remote admission, correctness
encode, lease attempt, profiler invocation, workload, archive, transfer, or
extraction occurred. The local post-refusal check recorded that the execution
output was absent and found no prohibited profiler/runner process. Remote
cleanup and lease release were not applicable because no remote or lease state
was touched.

Accordingly, completed-diagnostic acceptance is not met:

- profiles: 0/24; raw traces: 0/24; TOCs/exports: 0;
- usable symbolized samples: 0; symbol and unsymbolized-share checks are not
  evaluable;
- timer records: 0/120; retained records: 0/96;
- correctness encodes: 0/16; bitstream, decoded RGB, determinism, and runtime
  fallback behavior are not evaluable;
- timer nesting, positive calls, three-repeat stability, and stage-share
  stability are not evaluable;
- remote toolchain/build/symbol, power/thermal/resource/process, lease, and
  archive-return criteria are not met for an executed diagnostic.

The fail-closed refusal is correct behavior, but it is not a substitute for the
frozen performance evidence.

## Attribution by case and method

| Case | Method | Profiles B/C | Retained records B/C | Total/stage delta | Interval share | Status |
|---|---:|---:|---:|---|---|---|
| photo-large | 4 | 0/0 of 3/3 | 0/0 of 12/12 | unavailable | unavailable | not determinable |
| photo-large | 6 | 0/0 of 3/3 | 0/0 of 12/12 | unavailable | unavailable | not determinable |
| graphic-large | 4 | 0/0 of 3/3 | 0/0 of 12/12 | unavailable | unavailable | not determinable |
| graphic-large | 6 | 0/0 of 3/3 | 0/0 of 12/12 | unavailable | unavailable | not determinable |

No percentages are computed from an empty sample set. Total encode, lossless
analysis/backward references, hash-chain/search, CostManager DP, PushInterval,
insertion/update, setup/steady computation, traceback, histogram, Huffman, and
serialization attribution all remain unavailable. Code-layout, I-cache, or
control-overhead explanations likewise remain unresolved.

## Research consequence and evidence limit

The frozen close-family rule requires a measured baseline interval share below
5% of total CPU or a sampled bound showing no consistent recoverable total
win. Neither quantity exists. The interval-search family therefore receives no
new close/reopen decision from this run. The dominant stages for methods 4 and
6 are both **not determinable from this run**, and there is no
evidence-supported quantified boundary for a new independently gated
experiment.

The only blocker is the Phase 1 `BLOCKED_REMOTE_REHEARSAL` decision with
`timed_execution_authorized=false`. Additional Phase 1 limitations are the two
interrupted non-encoding sanitizer guard hangs and the unavailable optional
make `dwebp` dependency (`jerror.h`); neither produced encoder performance
evidence.

Machine-readable details, criterion-by-criterion status, exact evidence hashes,
and null attribution fields are in
`evidence/backref-cost-attribution-v1-evaluation-20260819/phase3-audit.json`.
