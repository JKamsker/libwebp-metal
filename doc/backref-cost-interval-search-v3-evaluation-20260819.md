# Backref-cost interval-search v3 independent evaluation

## Decision and consequence

Production promotion is rejected. The frozen contract is conjunctive: every
photo-large and graphic-large method/lifecycle cell must satisfy paired median
ratio `<= 0.995` and raw nearest-rank p95 ratio `<= 1.005`. All four graphic
holdouts pass, but all four photo holdouts fail the median ceiling and three
also fail p95. Content-specific or partial promotion is forbidden.

The v3 experiment and its evidence are retained, wholly default-off. All
identity, semantics, correctness, work, API/ABI, operational, and evidence
return gates pass, so removal is not supported. No production path, public
interface, candidate, protocol, corpus, threshold, host, toolchain, power
state, Metal/CUDA path, or old experiment is changed. No v1/v2 sample is
pooled or relabeled. This evaluation ran no benchmark.

## Ancestry and frozen identity

The exact history before this evaluation is:

- verified base `c472599ce8d3aee1e4f5bcf70b56b9c354351660`, tree
  `bdc5031514b6695ed4cf472fcf37407ad5af6c76`;
- Phase 1 `a3ebde3d12f1be7f5bb3dc8dd7969383595cf68e`, direct parent the base,
  tree `5911207050ff446281c4941c94c69a225e8c32a1`;
- Phase 2 `b781fa2ac1a288801ddc5a93bafe51c209e66d5b`, direct parent Phase 1,
  tree `63c75ce917d73d12d5760c27e5c2f8b9ebd406cf`.

Phase 2 adds only the v3 raw execution evidence directory. The phase-1 source
tree equals the remotely admitted tree. All frozen artifact hashes match the
phase-1 files and the returned source-hash map. Key hashes are:

- manifest `ba1d460ffd1a9b301472fa1886b0da00b2ed79b0de62352394284982933d5bc2`;
- schema catalog `48a7b79dbeaf2f642cd41f8f7606359ba045e7b7a61c111fc282709e2b4bb9d0`;
- freeze receipt `b526c4c58718faecd194f5345368744d9e0966b92c2272d896b766bf81b639ae`;
- raw samples `869c25b99733f02432eab647c1c4bcdf8dd65de959b7266d2e0b71d31e17279a`;
- command records `d8a388c21c7bfd739ad7ec10bd187e1221ac786bc5d16f5e54f882e47e874dac`;
- work records `63ae29c35a0c3a470172a6d1b1d823b6eb867e6f18f3b52bc7a9d6879536eca8`.

Fresh source normalization confirms v3 is exactly v2's PushInterval-local,
scan-derived append hint after private names are removed. A fresh Apple-clang
`-O3 -DNDEBUG` assembly rebuild gives equal 67,593-byte v2/v3 outputs after
normalization, both SHA-256
`7c75943dd1e7287d69f7b77b596ccf7f034c11baeee4253e7dc762ea13953215`.
`CostManager` is 33,224 bytes for baseline, v2, and v3. The hint has one-call
lifetime, equal starts use baseline positioning, and there is no manager field,
persistent tail bookkeeping, allocation, or semantic change to integer costs,
ties, updates, traceback, cache/reference order, lifetime, input ownership, or
transactional fallback.

The independent build, compile, runtime, and recorder gates remain disjoint.
Default builds omit v3 source/object/symbol/runtime strings and the runner.
Recorder code requires the separate v3-only guard and timed binaries contain
no recorder calls. Public headers are unchanged and gate-off/on public symbol
sets match.

## Receipt and mode contracts

The run receipt is version 1 and uses only the authoritative top-level
`source_bundle_sha256` plus nested `admission.bundle_sha256`. Both are strings
and equal the locally/remote recorded bundle SHA-256
`e8fde6753675533903a2675d9b780bfcabcd88a973190fef0ff8f3da595f7eb0`.
Repository-context bundle verification, clean detached source, exact
commit/tree/source hashes, and verification-repository removal all pass.

Contract tests fail closed for missing, renamed, wrong-type, unequal,
wrong-local-hash, and unexpected-version receipts. The full mode/session table
passes: `validate` and `rehearse` accept only an absent benchmark-session
variable; `run` accepts only exact `exclusive`. The exact frozen invocation was:

```sh
env WEBP_BENCHMARK_SESSION=exclusive WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V3_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_interval_search_v3.py run /Users/jonaskamsker/.codex/worktrees/f379/libwebp-metal/evidence/backref-cost-interval-search-v3-execution-20260819
```

## Frozen matrix and raw inventory

The independent traversal consumes every record in the frozen order: tune
before holdout, photo before graphic, method 4 before 6, cold before warm, and
the frozen alternating pair order. It finds 272 command processes and 1,232
sample rows. Exactly 192 warmups are excluded, leaving 1,040 retained samples:
176 cold and 864 warm, split 520/520 between baseline and candidate. Cold has
11 process pairs and one retained sample per process. Warm has six process
pairs and nine retained samples after two excluded warmups per process. All
rows use the v3 sample schema; no old-cycle sample enters the matrix.

For each warm process, the process location is the median of its nine retained
encodes. Paired location is the median of candidate-process/baseline-process
ratios. Tail is nearest-rank p95 over retained raw samples within each variant
stratum, candidate divided by baseline. The independent recomputation exactly
matches the frozen operator's 16-cell summary.

## Complete holdout matrix

| Holdout | Method | Lifecycle | Median ratio (`<=0.995`) | p95 ratio (`<=1.005`) | Result |
| --- | ---: | --- | ---: | ---: | --- |
| photo-large | 4 | cold | 1.0050163268 | 1.0232215633 | fail median, fail p95 |
| photo-large | 4 | warm | 1.0047657522 | 1.0294745293 | fail median, fail p95 |
| photo-large | 6 | cold | 1.0013144143 | 1.0249478668 | fail median, fail p95 |
| photo-large | 6 | warm | 1.0007538358 | 0.9997817593 | fail median, pass p95 |
| graphic-large | 4 | cold | 0.9775355285 | 0.9858545171 | pass |
| graphic-large | 4 | warm | 0.9811490892 | 0.9782817228 | pass |
| graphic-large | 6 | cold | 0.9794553808 | 0.9848364179 | pass |
| graphic-large | 6 | warm | 0.9776733439 | 0.9752984464 | pass |

Photo is 0/4, graphic is 4/4, and the required conjunctive result is failure.
Tune statistics are recorded in the raw recomputation artifact and remain
descriptive only.

## Correctness and work audit

The returned correctness file has the exact 26 frozen cells. Every row reports
candidate determinism, default-build independence, exact transactional
fallback, identical decoded pixels, and immutable input identity. Fresh local
validation repeats all 26 cells and exercises undefined/integer plus
array-bounds/pointer-overflow sanitizer configurations and 16 fuzzed interval
boundaries.

The phase-1 local 36-row work file independently recomputes to 5,585,685 to
zero forward steps, unchanged 53,769 backward steps, 1,062,260 fast paths,
37 activations, and 99.046557% total positioning reduction. Its SHA-256 is
`d5b16a2122d967b30d415d81b17308165673c982d7aa7d89c6165c0a364b33c2`.
The remote rehearsal and Phase-2 run each contain the same deterministic
16-row untimed work diagnostics for the frozen tune/holdout corpus.

The independently recomputed 16-row work file has eight baseline/candidate
cells. All preserve bitstreams, backward steps, and every frozen non-search
counter. Totals are:

| Counter | Baseline | Candidate |
| --- | ---: | ---: |
| Forward positioning steps | 5,320,351 | 0 |
| Backward positioning steps | 50,215 | 50,215 |
| Total positioning steps | 5,370,566 | 50,215 |
| Append-hint fast paths | 0 | 1,011,082 |
| Append branch checks / loads | 0 | 1,069,280 / 1,069,280 |
| Append start loads | 0 | 1,011,082 |
| Append update checks / updates | 0 | 110,228 / 1,069,658 |
| Pop-tail checks / updates | 0 | 35,248 / 14,398 |
| Runtime activations | 0 | 19 |

Candidate positioning is 0.935004% of baseline, a 99.064996% reduction. Every
active cell is below the frozen 10% ceiling with activation and fast-path
evidence. No work record contains timing fields.

## Operational and return audit

The exact phase-1 commit/tree/source hashes and the frozen noninteractive
Apple clang 17 / macOS 26.2 SDK / Unix-make toolchain were admitted. Remote
CMake and Homebrew use are false, global/host `PATH` change is false, and the
pipeline records no install, download, runner/service, directory, power, LPM,
Metal, or CUDA change.

Preflight, pre-timing, and post-timing snapshots all show the frozen M4 host,
AC power, Low Power Mode off, no thermal/performance warning, sufficient disk
and memory, no Runner.Worker, and no competing benchmark/CUDA process. Exactly
one benchmark lease was acquired and released. Timed parallelism is one.
Elapsed workload time is 528.055 seconds under the 3,000-second limit, maximum
child RSS is 269,516,800 bytes under 4 GiB, and indexed output is 1,136,937
bytes under 2 GiB.

The 23-member safe archive has matching remote/local SHA-256
`4fcd9aa2027ec78368d30b364c7c2285def228eb9f59f40518f301b6a0586dc4`.
Its full inventory and all-or-nothing extraction are accepted. The lease was
returned independently and hash-verified before extraction. Every entry in
the 22-artifact remote index and 30-entry returned index independently matches
local bytes and SHA-256. The cleanup receipt proves validated deletion of only
`run.VTORJl` and post-delete absence. Pipeline exit is zero with empty wrapper
stdout/stderr.

## Gate checklist

| Frozen gate | Result |
| --- | --- |
| Exact ancestry and phase ownership | pass |
| Exact v2/v3 source, codegen, layout, and semantic boundary | pass |
| Default omission, gate isolation, recorder absence, API/ABI | pass |
| Receipt schema/hash and mode/session truth tables | pass |
| Frozen source/schema/manifest/corpus/order/counts | pass |
| Source/toolchain admission | pass |
| Correctness, determinism, immutable inputs, fallback | pass |
| Sanitizers and fuzzed boundaries | pass |
| Positioning reduction and counter consistency | pass |
| Device, power, process, resource, thermal | pass |
| Exclusive lease acquire/release | pass |
| Archive, index, transfer, extraction, cleanup | pass |
| Raw command/sample traversal and statistics | pass |
| Graphic holdout median and p95, 4/4 | pass |
| Photo holdout median and p95, 0/4 | fail |
| Conjunctive production promotion | fail |

## Untimed Phase-3 validation

The following commands passed:

```sh
python3 scripts/test_backref_cost_interval_search_v3_experiment.py
python3 scripts/test_backref_cost_interval_search_v3_admission.py
python3 scripts/test_backref_cost_interval_search_v3_archive.py
python3 scripts/test_backref_cost_interval_search_v3_protocol.py
python3 scripts/test_experiment_guards.py
```

The implementation test includes clean default/candidate CMake builds for
local validation only, API/ABI and omission checks, all correctness cells,
sanitizers, and boundaries. A separate untimed assembly audit used
`/usr/bin/cc -S -O3 -DNDEBUG` with each v2/v3 compile gate and compared outputs
after private identity normalization. No command invoked the run/timing mode.

The terminal blocker to promotion is evidentiary and algorithmic performance,
not infrastructure: the exact v2 algorithm materially regresses the frozen
photo holdouts despite eliminating forward positioning work. A credible next
lead requires a newly gated experiment that explains or avoids the
photo-specific end-to-end overhead without changing the accepted semantic
boundary; it must not reuse these samples as a new cycle.
