# Backref-cost workspace remote v5 evaluation (2026-08-18)

## Decision

Promotion is **rejected**. The one authorized remote v5 pipeline is complete,
internally consistent, and suitable for deciding the frozen question, but none
of the 12 required holdout cells meets the paired-median ceiling of `0.99`.
Nine of 12 holdout p95 ratios meet the separate `1.01` ceiling; zero cells meet
both limits. Because acceptance is conjunctive, the unchanged exact-sized
`CostManager` workspace is not a production candidate.

The candidate, v5 gates, safe return machinery, frozen protocol, and evidence
are retained default off as a reproducible negative result and provenance.
Retention is not promotion. Ordinary production source selection, behavior,
API/ABI, allocation, integer/tie semantics, fallback, Metal/CUDA policy, and
host/runner policy are unchanged.

## Authority and ancestry

The audited history is strictly linear:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| verified main | `978e1b3e12e710c25f465fe1c8a68c359a38004e` | `c66e0264cd7af4df7678a5b9af60c6fecbd8329d` | `b9082f2445b4e64f39d1ab0148cc18b3dbfbf8d6` |
| design/code/frozen protocol | `13374003895d81f4e85b6cf77ad82a48f9fc5bc4` | verified main | `d51be627b566e77cfccd59a262b3ba4904c3343b` |
| single executor evidence | `32f48560198dba36c81e1e52d80d90502f6c71d0` | design/protocol | `c7819d5bffbb844fd9d7e703f66c59271f0045f3` |
| evaluator consequence | separate descendant containing this report | executor evidence | recorded by the evaluator commit |

The executor commit adds exactly 30 files under
`evidence/backref-cost-workspace-remote-v5-execution-20260818` and changes no
candidate, manifest, schema, protocol, threshold, corpus, runner, or operator.
No v4 sample is referenced or pooled.

## Frozen identity, gates, default omission, and ABI

Independent preprocessing and helper normalization reproduce the frozen v3/v4
candidate identity exactly:

- boundary projection SHA-256:
  `77d14bb905980dfe53f75886b4270a6bfdd9d2ff46874aa0cea3aa480bedd533`;
- normalized helper body SHA-256:
  `3128cbcef3b3f000926d69a117d5d7b79a68c59f0658fe5738eddbfeed33fdfd`.

Only private gate/helper names and assertion locations differ. The candidate
still uses one exact-sized workspace for costs, cached-cost intervals, and 490
non-inline nodes after the ten inline nodes. Integer costs, strict comparisons
and ties, update order, traceback, reference/cache order, and transactional
allocation-failure fallback are unchanged.

The v5 build, compile, and exact runtime gates are independent:

- `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT`;
- `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT=1`.

Guard tests prove mutual exclusion with all predecessors. Default CMake and
Unix-make paths leave v5 off and omit its source, compile macro, symbols,
runtime/fault strings, and runner target. No public or installed header changed
from verified main. Separate minimal default and v5 shared-library installs had
identical installed headers and exported symbol sets.

## Frozen authority and source admission

The frozen manifest SHA-256 is
`892c185be44d9773f5a8a30aac4fdb6c8865786ff8578746adacd6fbd47c86e3`;
the schema catalog SHA-256 is
`a27cb4587ed86a9d39e7f1b85be0802890f625fffb82a0b3e62a39e32fe0a573`.
Every manifest-frozen artifact matches both its hash in commit `13374003` and
the returned source-hash record. All schemas used by JSON and JSONL records are
catalogued and contain their frozen required fields.

The source bundle SHA-256 matches locally and remotely at
`53e8fa968a1b625c00c2288ff0efb6238e59163d38eafa6e56a81bed383ec7c4`.
The remote admission initialized an empty scoped bare repository, ran `git
bundle verify` in that repository context, removed the verification repository,
and checked out the exact detached commit and tree with clean status and exact
source hashes. The canonical path receipt admits only direct child
`run.3XLdC7` beneath the exact v5 safe root. Pre-transfer and post-admission
process checks contain no `Runner.Worker`, benchmark, or CUDA conflict; the
installed runner directory was not touched.

## Toolchain, build, host state, and resources

Toolchain admission passed before the lease and timing. The returned record
matches the frozen noninteractive environment and exact paths/hashes for
`/usr/bin/xcrun`, GNU Make 3.81, Apple clang/clang++ 17.0.0, Apple ar/ranlib,
Apple Git 2.50.1, Python 3.9.6, and shasum 6.02. The effective developer
directory is Xcode 26.3 and the explicit arm64 SDK is macOS 26.2. The compiler
SDK probe passed. CMake and Homebrew were not used, and no host or global PATH
was changed.

The seven returned build commands exactly reconstruct two clean detached
clones, baseline flag `0`, candidate flag `1`, explicit `-arch arm64` and
`-isysroot` compile/link flags, deterministic make mode, and a default runner
linked from baseline static archives. Metal is explicitly disabled, CUDA is
absent, and the two timed variants use the same admitted toolchain.

All preflight, immediately-pre-timing, and immediately-post-timing records
match Darwin arm64, `Mac16,10`, Apple M4, 24 GiB physical memory, Xcode clang
17, SDK 26.2, AC power, Low Power Mode off by both authorities, no thermal or
performance warning, sufficient memory/disk, and no `Runner.Worker`, benchmark,
or CUDA process. `Runner.Listener` remains present as permitted. Timing is
serial; all 408 child stderr entries are empty apart from their command heading.

Observed resources pass every frozen ceiling: 681.320090 seconds total,
281,722,880 bytes maximum child RSS, 1,373,679 evidence bytes before indexing,
and at least 18,950,467,584 bytes available disk across the three gates. The
largest individual command wall duration is 13.349970 seconds, below 300.

## Correctness and corpus

All 26 frozen correctness cells pass. Baseline, candidate-off, candidate,
repeat, injected allocation-failure fallback, predecessor-gate-only, and
default-build-with-v5-environment streams are exact as required. Candidate
repeats are deterministic, fallback is transactional and exact, and all
decoded pixels equal immutable input bytes. The untimed evaluator suite
independently repeats these checks and passes undefined/integer plus
array-bounds/pointer-overflow sanitizer builds.

The six timed corpus hashes match the frozen publication corpus. Raw timing has
12 invariant bitstream signatures, one per timed case/method combination,
across all 1,848 rows. The frozen order is exact: tune then holdout; photo,
graphic, texture; method 4 then 6; cold then warm; alternating pair order.

## Raw inventory and independent statistics

Independent parsing of `commands.jsonl` and `records.jsonl` reconstructs every
command and sample field, sequence, pair, variant, iteration, and sample role:

| Record class | Frozen | Observed |
|---|---:|---:|
| command processes | 408 | 408 |
| cold retained samples | 264 | 264 |
| discarded warmups | 288 | 288 |
| warm retained samples | 1,296 | 1,296 |
| total retained samples | 1,560 | 1,560 |
| retained per variant | 780 | baseline 780; candidate 780 |
| correctness cells | 26 | 26 |
| evaluation cells | 24 | 24 |
| required holdout cells | 12 | 12 |

The following ratios were recomputed directly from raw nanoseconds. `median`
is the median of paired candidate/baseline process medians; `p95` is the
candidate/baseline ratio of nearest-rank raw p95 values. Lower is favorable.

| Role/case | Method | Lifecycle | Pairs | Median ratio | p95 ratio | Both pass |
|---|---:|---|---:|---:|---:|---|
| tune/photo-medium | 4 | cold | 11 | 1.003160 | 0.992909 | no |
| tune/photo-medium | 4 | warm | 6 | 1.002265 | 0.997928 | no |
| tune/photo-medium | 6 | cold | 11 | 1.002503 | 1.012336 | no |
| tune/photo-medium | 6 | warm | 6 | 1.006404 | 1.008251 | no |
| tune/graphic-medium | 4 | cold | 11 | 0.995919 | 1.003861 | no |
| tune/graphic-medium | 4 | warm | 6 | 0.992470 | 0.996166 | no |
| tune/graphic-medium | 6 | cold | 11 | 0.996120 | 1.003782 | no |
| tune/graphic-medium | 6 | warm | 6 | 0.997722 | 0.995305 | no |
| tune/texture-medium | 4 | cold | 11 | 1.002388 | 0.987115 | no |
| tune/texture-medium | 4 | warm | 6 | 1.028182 | 1.228303 | no |
| tune/texture-medium | 6 | cold | 11 | 0.993207 | 1.004444 | no |
| tune/texture-medium | 6 | warm | 6 | 1.001701 | 1.010503 | no |
| holdout/photo-large | 4 | cold | 11 | 1.004812 | 1.020720 | no |
| holdout/photo-large | 4 | warm | 6 | 1.002807 | 1.002787 | no |
| holdout/photo-large | 6 | cold | 11 | 1.002581 | 1.003729 | no |
| holdout/photo-large | 6 | warm | 6 | 1.001849 | 1.001345 | no |
| holdout/graphic-large | 4 | cold | 11 | 0.996780 | 1.038328 | no |
| holdout/graphic-large | 4 | warm | 6 | 0.997301 | 1.011375 | no |
| holdout/graphic-large | 6 | cold | 11 | 0.991385 | 0.997166 | no |
| holdout/graphic-large | 6 | warm | 6 | 1.004241 | 1.003151 | no |
| holdout/texture-large | 4 | cold | 11 | 0.999440 | 0.995372 | no |
| holdout/texture-large | 4 | warm | 6 | 1.000315 | 1.002327 | no |
| holdout/texture-large | 6 | cold | 11 | 0.992694 | 0.870087 | no |
| holdout/texture-large | 6 | warm | 6 | 1.000126 | 0.997221 | no |

All 24 independently recomputed ratio pairs exactly equal the committed raw
evaluation values, without rounding. Tune is descriptive. In holdout, zero of
12 medians pass `<= 0.99`; nine of 12 p95 ratios pass `<= 1.01`; zero of 12
cells pass both. The three p95 failures are photo-large/method-4/cold,
graphic-large/method-4/cold, and graphic-large/method-4/warm. No aggregation,
threshold fit, pooling, retry, or relabeling is used.

## Lease, archive, transfer, extraction, and cleanup

The exclusive v5 lease was attempted, acquired, and released. Its independent
pre-extraction transfer matches remote/local SHA-256
`9e139dd0843b0fff6867be68a1b1c9b782d2585f0f831356786ee795f97dfaa8`.

The remote artifact index has 20 exact files and SHA-256
`f9f1f0f40429a6b05c93eec2864036d3cf78051840126b5ff3f41b86395741e5`.
The safe builder accepted 21 canonical regular members, including the index.
The remote and local archive SHA-256 values match at
`d9b3945d68464fafaaa742844751c7b09bb7cd806ce93e74425c8cf21e4c5ecf`;
the complete remote/local inventory SHA-256 values match at
`c7c7cad2eb9bad44067f591a900ab6a2cf47bbd16373643c0225cfc59ca6be4f`.
Builder, inventory inspection, and all-or-nothing extraction accepted with no
offending member. The 28-file returned index is exact and has SHA-256
`780683883af61d18dbf05929ce0f6c5fdacf6e0ce5e9b4ae6bdd1cb9b0bec8e2`;
it explicitly excludes only the later transfer/cleanup envelope.

Untimed archive tests independently reject traversal, absolute paths,
symlinks, hardlinks, FIFOs/devices, non-normal names, Apple metadata/xattrs,
unknown or unindexed files, and containment escapes with no partial extraction.
The returned successful inventory contains only canonical indexed regular
files.

After lease and archive return, the driver revalidated and removed only
`/Users/pandocs-agent-001/.libwebp-metal-backref-cost-workspace-remote-v5/run.3XLdC7`.
The independent cleanup receipt validates the token and safe root and proves
the exact child absent; its SHA-256 is
`05ebc24ed735442148cbffe5ac178333a5dee5eb7e974d6cdc8c19634d908db3`.

## Frozen criteria

| Criterion | Outcome |
|---|---|
| exact ancestry and executor-only raw-evidence commit | pass |
| frozen manifest, schema linkage, artifact/source hashes | pass |
| v3/v4 candidate identity and unchanged semantics | pass |
| independent mutually exclusive v5 gates and default omission | pass |
| installed headers and exported ABI | pass; unchanged |
| corpus, order, pair counts, cold/warm policy | pass |
| source bundle, repository-context verify, exact commit/tree/clean hashes | pass |
| toolchain admission, exact build commands, compiler/SDK | pass |
| device, AC/LPM/thermal, process isolation | pass |
| correctness, streams, decoded pixels, repeats, fallback, immutable inputs | pass; 26/26 |
| resources and one synchronous timed child | pass |
| lease acquire/release and independent hash return | pass |
| archive inventory/hash/transfer/extraction security | pass |
| remote artifact index and local returned index | pass |
| exact-child cleanup and absence proof | pass |
| commands/warmups/retained sample inventory | pass |
| all 12 holdout medians `<= 0.99` | **fail; 0/12** |
| all 12 holdout p95 ratios `<= 1.01` | **fail; 9/12 pass** |
| all 12 holdout cells pass both | **fail; 0/12** |
| frozen all-gate promotion rule | **reject** |

## Untimed evaluator checks

No benchmark, remote command, lease, CUDA command, recorder, local timed
fallback, protocol edit, threshold edit, corpus edit, or follow-up experiment
was run. The evaluator used only read-only evidence recomputation and local
untimed validation:

```sh
python3 -m py_compile scripts/*remote_v5*.py
python3 scripts/test_backref_cost_workspace_remote_v5_archive.py
python3 scripts/test_backref_cost_workspace_remote_v5_admission.py
python3 scripts/test_backref_cost_workspace_remote_v5_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_workspace_remote_v5_experiment.py
```

All passed. A separate minimal shared-library build/install comparison passed
installed-header and exported-symbol equality and proved v5 absent from the
default compile graph, library strings, and target list.

## Production consequence and no-run lead

Do not promote the exact-sized workspace. Retain the default-off candidate and
all v5 protocol/evidence files as negative research provenance. No production
source path, public API/ABI, default, threshold, allocation behavior,
integer/tie rule, fallback rule, Metal/CUDA behavior, host setting, power
setting, or runner service changes.

The complete matrix rejects another admission-only rerun of this unchanged
allocation-topology hypothesis. A later authorized cycle should first design a
different algorithmic boundary that reduces `PushInterval` interval-search or
update work while preserving exact ordering, integer/tie, traceback, cache,
reference, and transactional-fallback semantics. The proposal-only independent
gates are
`WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`,
`WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`, and exact runtime
`WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1`. No such code, protocol,
build, correctness run, or timing run exists in this cycle; fresh profiling and
a newly frozen protocol would be prerequisites.

The machine-readable Phase 3 consequence is
`evidence/backref-cost-workspace-remote-v5-evaluation-20260818/evaluation-consequence.json`.

