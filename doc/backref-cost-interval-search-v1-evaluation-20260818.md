# Backref-cost interval-search v1 evaluation (2026-08-18)

## Decision

Production promotion is **rejected**. The single authorized remote pipeline is
complete and operationally valid, and the candidate passes correctness and the
frozen direct-work gate. It does not pass the conjunctive performance rule:
only four of eight required holdout cells meet both thresholds. All four
photo-large cells miss the required paired-median ratio of `<= 0.995`; two also
miss the p95 ratio of `<= 1.005`.

The candidate, independent gates, protocol, and raw evidence are retained
default off as negative research provenance. Retention is not promotion. No
production source path, API/ABI, default, threshold, integer/tie behavior,
traceback/cache/reference order, allocation/fallback behavior, Metal/CUDA
behavior, toolchain, host, power, or runner setting changes in this phase.

## Authority and ancestry

The audited history is strictly linear after the verified merge base:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| verified main | `568d2476afef3465294bec6a4e099d1b598135f7` | merge parents `978e1b3e...`, `0e5e6c4e...` | `cdd4ee10f6ef4a49e03ee2ecc0334d2fbb81f453` |
| Sol/high design, code, frozen protocol | `218032e2f47a3b1df84933f7cf2b08bb9c69ff64` | verified main | `7708034722b3cbf2c749b34df0b86e6046543de6` |
| Luna/max single execution | `0d75c3649973446c5ef0132fed99d05373e9ce50` | design/protocol | `1b9b4213978a397b5ce42897468a8dec58a5209b` |
| Sol/high evaluation/consequence | separate descendant containing this report | executor evidence | recorded by the evaluator commit |

The executor commit adds exactly 32 files under
`evidence/backref-cost-interval-search-v1-execution-20260818` and changes no
candidate, gate, manifest, schema, threshold, corpus, runner, or protocol file.
No result or sample from the rejected workspace candidates is referenced,
pooled, relabeled, or reused.

## Candidate semantics, gates, default omission, and ABI

The candidate changes one private boundary. `CostManager` gains a gated `tail`
pointer and activation bit. `ConnectIntervals` updates `tail` whenever the
resulting `next` link is null. `PositionOrphanInterval` starts a null-hint
insertion at `tail` only when the list is nonempty and
`current->start > tail->start`; every other case executes the baseline search.
The strict comparison excludes equal starts and therefore preserves baseline
equal-start insertion order. Empty-list insertion, tail insertion, tail pop,
single-node pop, split, recycle, free-list, and serialization paths maintain
the same ordered list and lifetime behavior.

The optimization changes no cost arithmetic, `>` cost update, `>=` interval
replacement, start/end relation, update order, live-node cap, traceback,
color-cache lookup/insertion, reconstructed-reference append order, or input
array. It introduces no candidate allocation or post-mutation failure point.
Fault injection selects the exact baseline path before dynamic programming, so
fallback is transactional. Existing allocation failures still serialize an
interval or fail initialization exactly where the baseline does.

The three independent gates are:

- `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`;
- exact runtime `WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1`.

The compile gate is mutually exclusive with all six overlapping backref-cost
experiments. Default CMake and Unix-make paths leave the build gate off and
omit the helper object, compile macro, symbols, runtime/fault strings, and
runner target. Runtime values other than `1` are inactive. The recorder macro
is accepted only with the build gate and was present only in the separate
untimed diagnostic clone. The timed candidate command has the build gate on
and no recorder macro; the timed baseline has the build gate off.

Phase-1 ABI evidence records 86 exported symbols with identical gate-off and
gate-on SHA-256
`e91d9c2b44b49d51a64208438cb07a85570b3516fa84cefaddf2f2ed3338cfb4`,
and zero public-header changes from verified main. Independent evaluator guard
and correctness builds again proved ordinary source/object/target/string
omission and no public header or API change.

## Frozen protocol and phase-1 untimed evidence

The frozen manifest SHA-256 is
`d1f768dad557d6a41969a23ed206d616eed67dbee16a3e588b15aeaea39515c3`;
the schema catalog SHA-256 is
`6cd85d69c19aac7be5048aa6a9b42c1d17cd445ccb24c43a26fca6191613e0dd`.
All 35 manifest-frozen artifacts independently match their committed hashes,
the returned source-hash record, and the exact admitted phase-1 commit.

The frozen correctness matrix is 13 case/quality rows by methods 4 and 6. The
timed matrix separates tune (`photo-medium`, `graphic-medium`) from holdout
(`photo-large`, `graphic-large`), evaluates methods 4 and 6 and cold/warm
lifecycles independently, and fixes tune before holdout, photo before graphic,
method 4 before 6, cold before warm, and alternating baseline/candidate order.
Cold uses 11 process pairs, no warmup, and one retained encode. Warm uses six
process pairs, two discarded warmups, and nine retained encodes. Tune is
descriptive. Every holdout cell must have paired process-median ratio
`<= 0.995` and nearest-rank raw p95 ratio `<= 1.005`.

Phase-1 recorder evidence has 36 rows across all nine publication cases and
both methods: 12 active and six inactive case/method pairs. Baseline positioning
performed 5,585,685 forward and 53,769 backward steps; candidate positioning
performed zero forward and the same 53,769 backward steps, with 1,062,260 tail
fast paths and 37 runtime activations. Bitstreams and all non-search counters
match, and no timing field was recorded.

The untimed live-return validation passed canonical path generation, indexed
building, six-member representative extraction, three builder rejections,
five malicious-archive rejections, zero partial extractions, eight verified
transfers, independent cleanup, and exact-child absence. The admitted remote
Unix-make rehearsal ran 10 exact build commands, 26 correctness cells, and 16
work rows with zero benchmark leases, timed commands, or timed samples. Missing
and wrong toolchain fixtures refused; an indexed early refusal returned four
members, an independent lease record, and cleanup proof. A stalled malformed
transfer fixture also removed only its validated child and proved the safe
root empty. The phase-1 returned-evidence index contains 27 verified artifacts.

Independent local evaluator execution repeated the complete 26-cell publication
matrix, candidate-off, invalid-runtime, predecessor-gate, deterministic repeat,
fault fallback, decoded-pixel, and default-build-with-runtime-environment checks.
It also passed undefined/integer and array-bounds/pointer-overflow sanitizer
builds over photo-small plus 16 generated boundary cases (eight dimensions per
sanitizer). Archive, admission, schema/protocol, default omission, gate
isolation, and fail-closed runner checks passed.

## Phase-2 source, toolchain, host, build, and resources

Remote repository-context admission accepted exact source commit
`218032e2f47a3b1df84933f7cf2b08bb9c69ff64`, tree
`7708034722b3cbf2c749b34df0b86e6046543de6`, clean status, and every frozen
source hash. The local/remote bundle SHA-256 is
`ee6b2a40e2e591d3f35e25f80b8a799bc3686ee15a3371f49939ec80d86321ba`;
bundle verification ran in an empty scoped bare repository, which was removed.
The canonical path was direct child `run.6lozEb` of the v1 safe root.

Toolchain admission matches the frozen noninteractive environment and exact
paths/hashes for `/usr/bin/xcrun`, GNU Make 3.81, Apple clang/clang++ 17.0.0,
Apple ar/ranlib, Apple Git 2.50.1, Python 3.9.6, and shasum 6.02. Effective
Xcode is 26.3 and the explicit arm64 SDK is macOS 26.2. The compiler/SDK probe
passed. CMake and Homebrew were not used, and neither host settings nor global
PATH changed.

Ten returned build commands create three clean detached clones: default
baseline, recorder-free candidate, and untimed recorder candidate. All use
explicit Apple tools, `-arch arm64`, the exact SDK, deterministic Unix make,
and Metal off. The diagnostic binary supplied the work metrics and was not a
timing executable. Timed command paths reference only the independent baseline
and recorder-free candidate runners.

Preflight, immediately-pre-timing, and immediately-post-timing records all
match Darwin arm64, `Mac16,10`, Apple M4, 24 GiB physical memory, AC power,
Low Power Mode off by both authorities, and no thermal, performance, or CPU
power warning. All three process checks contain no `Runner.Worker`, competing
benchmark, or CUDA process; permitted `Runner.Listener` remains present.

Resources pass all frozen limits: 527.475893 seconds total (`<= 3000`),
269,533,184 bytes maximum child RSS (`<= 4 GiB`), 1,131,821 output bytes before
index (`<= 2 GiB`), at least 11,448,893,440 available memory (`>= 4 GiB`), and
at least 18,923,749,376 available disk (`>= 8 GiB`). The largest command wall
duration is 13.381637 seconds (`<= 300`). Exactly one synchronous timed child
ran at a time.

## Correctness, raw inventory, and work reduction

All 26 remote correctness rows pass stream identity, decoded-pixel equality,
candidate determinism, injected pre-DP baseline fallback, gate isolation,
default-build independence, and immutable corpus input hashes. Raw timing has
eight invariant bitstream signatures, one for every timed case/method stratum,
across all 1,232 rows.

Independent parsing reconstructed the frozen command order and every command
chunk, sequence, pair, variant, iteration, lifecycle, and sample role:

| Record class | Frozen | Observed |
|---|---:|---:|
| command processes | 272 | 272 |
| cold retained samples | 176 | 176 |
| discarded warmups | 192 | 192 |
| warm retained samples | 864 | 864 |
| total retained samples | 1,040 | 1,040 |
| retained per variant | 520 | baseline 520; candidate 520 |
| correctness cells | 26 | 26 |
| work rows | 16 | 16 |
| evaluation cells | 16 | 16 |
| required holdout cells | 8 | 8 |

Every active work cell passes the `<= 10%` positioning-step requirement,
positive activation and fast-path requirements, equal backward steps, equal
bitstream signatures, and exact non-search counters:

| Role/case | Method | Baseline steps | Candidate steps | Ratio | Activations | Tail fast paths |
|---|---:|---:|---:|---:|---:|---:|
| tune/photo-medium | 4 | 437,118 | 4,574 | 0.010464 | 2 | 95,259 |
| tune/photo-medium | 6 | 440,525 | 4,753 | 0.010789 | 3 | 96,002 |
| tune/graphic-medium | 4 | 146,275 | 160 | 0.001094 | 2 | 7,994 |
| tune/graphic-medium | 6 | 146,275 | 160 | 0.001094 | 2 | 7,994 |
| holdout/photo-large | 4 | 1,667,044 | 19,903 | 0.011939 | 3 | 379,197 |
| holdout/photo-large | 6 | 1,677,987 | 20,519 | 0.012228 | 3 | 380,116 |
| holdout/graphic-large | 4 | 427,671 | 73 | 0.000171 | 2 | 22,260 |
| holdout/graphic-large | 6 | 427,671 | 73 | 0.000171 | 2 | 22,260 |

In total, positioning steps fall from 5,370,566 to 50,215, a ratio of
0.009350 and a 99.065% reduction. The candidate removes 5,320,351 forward
steps, takes 1,011,082 tail fast paths, and records 19 activations.

## Independent timing statistics

Statistics below were recomputed directly from raw nanoseconds. A cell's
`median` is the median of paired candidate-process/baseline-process medians;
`p95` is the candidate/baseline ratio of nearest-rank raw p95 values. No prior
experiment, category, case, method, lifecycle, process, or tune/holdout stratum
is pooled. Lower is favorable.

| Role/case | Method | Lifecycle | Pairs | Samples/variant | Median ratio | p95 ratio | Both pass |
|---|---:|---|---:|---:|---:|---:|---|
| tune/photo-medium | 4 | cold | 11 | 11 | 0.998455 | 0.996620 | no |
| tune/photo-medium | 4 | warm | 6 | 54 | 0.999768 | 1.004662 | no |
| tune/photo-medium | 6 | cold | 11 | 11 | 1.005532 | 0.996352 | no |
| tune/photo-medium | 6 | warm | 6 | 54 | 1.004419 | 1.004865 | no |
| tune/graphic-medium | 4 | cold | 11 | 11 | 1.005916 | 1.011385 | no |
| tune/graphic-medium | 4 | warm | 6 | 54 | 1.001473 | 1.014107 | no |
| tune/graphic-medium | 6 | cold | 11 | 11 | 0.998080 | 0.996783 | no |
| tune/graphic-medium | 6 | warm | 6 | 54 | 1.006486 | 1.005753 | no |
| holdout/photo-large | 4 | cold | 11 | 11 | 1.002919 | 1.005261 | no |
| holdout/photo-large | 4 | warm | 6 | 54 | 1.001805 | 0.999951 | no |
| holdout/photo-large | 6 | cold | 11 | 11 | 1.000839 | 1.002378 | no |
| holdout/photo-large | 6 | warm | 6 | 54 | 1.004328 | 1.007622 | no |
| holdout/graphic-large | 4 | cold | 11 | 11 | 0.993769 | 0.997115 | yes |
| holdout/graphic-large | 4 | warm | 6 | 54 | 0.989879 | 0.998185 | yes |
| holdout/graphic-large | 6 | cold | 11 | 11 | 0.991879 | 0.986618 | yes |
| holdout/graphic-large | 6 | warm | 6 | 54 | 0.991842 | 0.996286 | yes |

All 16 independently recomputed ratio pairs exactly equal the committed raw
evaluation values without rounding. Tune is descriptive and has zero of eight
conjunctive passes. In holdout, four of eight medians pass, six of eight p95s
pass, and only four of eight cells pass both. The photo-large/method-4/cold p95
miss is narrow (`1.005261` versus `1.005`) but immutable; the other photo
median misses independently reject promotion. Exact raw min/median/p95/max
nanoseconds for both variants and every cell are retained in the machine
record cited below.

## Lease, archive, transfer, extraction, and cleanup

The sole exclusive v1 lease was attempted, acquired at
`2026-08-18T21:15:13Z`, released at `2026-08-18T21:24:01Z`, and independently
returned before extraction. Its remote/local SHA-256 is
`11e1d45e29c0d1763c3de344b826d0d03cd991183b4e3311ea845120b497e47b`.

The remote artifact index contains 22 exact artifacts and has SHA-256
`c73d034d0e516ef5aa8a69fbcd7c1f4939a14f04a84d078b5ec012246a9e29cd`.
The safe archive contains 23 canonical regular members. Remote/local archive
SHA-256 matches at
`6146ebb19ff9a2793c4ca2eaaa2a26fe731b0d2de480d74c57c798e7565cc715`;
full inventory SHA-256 matches at
`7e8fae6e096aacc859a8007c0fc71359236771cc1447c0b4b2e582f6f562de8c`.
Builder, full inventory, and all-or-nothing extraction accepted with no
offending member.

All 22 remote-indexed and all 30 returned-indexed artifacts independently
match byte counts and SHA-256. The returned index itself has SHA-256
`b5cccaffdf0dda0158a5fb427febcfac4426d64582da8e16b4666ee4fdc6deb2`
and excludes only the later transfer/cleanup envelope. That envelope has
SHA-256
`163615ec7cc1d0de0cb7d4370d5d8c3d668bf3f36a0dd57e7c41b5c2dd16f977`.

After archive return, the driver revalidated and removed only
`/Users/pandocs-agent-001/.libwebp-metal-backref-cost-interval-search-v1/run.6lozEb`.
The independent receipt validates the token and safe root, records exact-child
removal, and proves absence; its SHA-256 is
`b61f538bd37ea70e1282f7ffa0ad25d1e516be81a381550043c0e207f3cc8b5f`.
No runner directory or service was touched.

## Frozen criteria and consequence

| Criterion | Outcome |
|---|---|
| strict ancestry and separate phase commits | pass |
| frozen manifest, schemas, source/artifact hashes | pass |
| candidate semantics, ordering, ties, lifetime, fallback | pass |
| independent gates, mutual exclusion, default omission | pass |
| public API/ABI/header equality | pass |
| phase-1 correctness, sanitizer/boundary, admission/security/cleanup | pass |
| source/toolchain/build admission | pass |
| corpus, order, lifecycle, command/sample inventory | pass |
| device, AC/LPM/thermal, process isolation | pass |
| remote correctness and immutable inputs | pass; 26/26 |
| work reduction | pass; 8/8 active cells |
| resources and one synchronous timed child | pass |
| lease/release and independent return | pass |
| archive/index/hash/transfer/extraction/cleanup | pass |
| all holdout medians `<= 0.995` | **fail; 4/8 pass** |
| all holdout p95 ratios `<= 1.005` | **fail; 6/8 pass** |
| all holdout cells pass both | **fail; 4/8 pass** |
| frozen all-gate production promotion | **reject** |

The evidence supports retaining the isolated, default-off implementation and
its protocol as a reproducible negative result. It does not support production
promotion, broadening to only graphic inputs, threshold adjustment, a partial
default, or any rerun. No follow-up experiment is proposed or run in this
phase.

## Untimed evaluator validation

No benchmark, remote command, lease, recorder run, local timing fallback,
protocol edit, threshold edit, corpus edit, CUDA command, or new experiment was
run. The evaluator used committed evidence recomputation and these untimed
local checks:

```sh
python3 -m py_compile scripts/backref_cost_interval_search_v1_*.py \
  scripts/collect_backref_cost_interval_search_v1_work.py \
  scripts/execute_backref_cost_interval_search_v1.py \
  scripts/run_backref_cost_interval_search_v1_experiment.py \
  scripts/test_backref_cost_interval_search_v1_*.py \
  scripts/validate_backref_cost_interval_search_v1_evidence_return.py
python3 scripts/test_backref_cost_interval_search_v1_archive.py
python3 scripts/test_backref_cost_interval_search_v1_admission.py
python3 scripts/test_backref_cost_interval_search_v1_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_interval_search_v1_experiment.py
```

All passed. The machine-readable raw-stat recomputation and consequence record
is `evidence/backref-cost-interval-search-v1-evaluation-20260818/evaluation-consequence.json`.
