# Backref-cost workspace remote v4 evaluation (2026-08-18)

## Decision

Promotion is **rejected for this cycle and performance is unassessed**. The one
authorized v4 pipeline completed source admission, acquired the exclusive
lease, and then failed closed before correctness or timing because `cmake` was
not available on `pandocs-agent`. It released the lease and independently
returned a hash-verified lease record. The driver then independently removed
the exact canonical run child and returned an absence-proving cleanup receipt.
There was no rerun, local timed fallback, new experiment, or production change.

The archive builder correctly refused because the failed operator had not
created `evidence/artifact-hashes.json`. Consequently, no archive existed,
there were zero archive members, extraction was not attempted, and no rejected
content was written. This is a pre-archive refusal, so quarantine requirements
for a rejected extractor archive do not apply.

Executor counts are exactly one pipeline, one lease acquired and released,
zero timed workloads, zero timed command processes, zero warmups, zero retained
samples, zero executor correctness cells, zero evaluation cells, and zero
holdout cells. No paired medians or p95 ratios exist. The frozen `0.99`
paired-median and `1.01` p95 ceilings therefore cannot pass the conjunctive
promotion rule.

The valid v4 evidence-return repair and unchanged CostManager candidate are
retained as default-off research code. Retention is not promotion. Ordinary
builds and production behavior remain unchanged.

## Authority and ancestry

The audited ancestry is linear:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| verified main | `c66e0264cd7af4df7678a5b9af60c6fecbd8329d` | `933cb1898832494e937c4aafe90e622f570ca15d` | `7c22723d070d0ebab7ae4153cf3e431bce2648bc` |
| design/code/frozen protocol | `6900c5448473d8070737e2c03ab98d39b853d970` | verified main | `1e35986b512353c1822aa6592665fe91dd442424` |
| single executor evidence | `373f9b868b3dd4c1296a20665533fba5df728c70` | design/protocol | `da3a20278bfe0102642cf369a4f9347931978bf6` |

The executor commit adds only nine files below
`evidence/backref-cost-workspace-remote-v4-execution-20260818`; it changes no
candidate, gate, protocol, threshold, host policy, or runner implementation.

## Candidate identity and independent gates

Independent preprocessing and normalization exactly reproduce the frozen
candidate identity:

- boundary projection SHA-256:
  `77d14bb905980dfe53f75886b4270a6bfdd9d2ff46874aa0cea3aa480bedd533`;
- normalized helper body SHA-256:
  `3128cbcef3b3f000926d69a117d5d7b79a68c59f0658fe5738eddbfeed33fdfd`.

The v4 candidate is therefore the recorder-free v3 candidate modulo private
v4 names. Integer costs, strict comparisons and ties, update order, ten inline
plus 490 allocated nodes, traceback, reference/cache ordering, and
transactional allocation-failure fallback are unchanged. V3's canonical path
validation and empty-repository-context `git bundle verify` behavior are
preserved under v4 identities.

The build, compile, and exact runtime gates are wholly independent:

- `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT`;
- `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT=1`.

They are default off, mutually exclusive with predecessor workspace gates, and
absent from ordinary objects, binaries, and targets. No public or installed
header, exported API/ABI, Metal/CUDA source, or production default changed.

## Frozen authority, schemas, corpus, and counts

The frozen manifest SHA-256 is
`a7b54fb4a8c3779997cfacaccc421c8ddbf4a12e40aff317f6df7b95c3c29c3f`.
All 36 listed artifacts match their byte hashes. The schema catalog SHA-256 is
`809f5a5b9241883b0de2765612a5f07de95c24806c0c446af499424c5b6c069b`;
all 17 catalog definitions are present and all 16 manifest record links resolve
to catalog definitions. The additional catalog definition is the design-only
live-return-validation record.

The frozen order and counts reconstruct exactly: 13 correctness rows by
methods 4 and 6 produce 26 cells; medium photo/graphic/texture tune precedes
large photo/graphic/texture holdout; method 4 precedes 6; cold precedes warm.
Cold has 11 alternating process pairs with one retained encode. Warm has six
alternating process pairs with two discarded and nine retained encodes. This
requires 408 command processes, 264 cold measurements, 288 warmups, 1,296 warm
measurements, 1,560 measured samples, 780 per variant, 24 evaluation cells,
and 12 required holdout cells. Tune is descriptive. Every holdout paired median
must be at most `0.99` and every holdout p95 ratio at most `1.01`, in addition
to every correctness, identity, host, lease, resource, archive/hash/index, and
cleanup gate.

The design-only live roundtrip also remains internally valid: six archive
members, eight hash-verified transfers, three builder refusals, five malicious
extractor refusals, zero partial extractions, a verified artifact index and
local returned index, and exact-child cleanup with absence proof. It is not
executor correctness or performance evidence.

## Single pipeline and returned evidence

Source admission verified a matching local/remote bundle SHA-256
`d60bf374a97e524dcfefa7376d02688e234b8b0d0e15d3ff01bfe2071ef1b778`,
repository-context bundle verification, detached source commit
`6900c5448473d8070737e2c03ab98d39b853d970`, source tree
`1e35986b512353c1822aa6592665fe91dd442424`, clean status, and all recorded
source hashes. The scoped verification repository was removed. Pretransfer and
post-admission process records contain no `Runner.Worker`, benchmark, or CUDA
matches; `Runner.Listener` remained present and untouched.

The lease record reports acquisition and release at `2026-08-18T18:20:37Z`.
Its independently returned remote and local SHA-256 values both equal
`3651a9437556381994380f81901e412508a5280cf71ed2627e8f3c4e28099830`.
Pipeline stderr is exactly the missing-`cmake` refusal and has SHA-256
`f314e5174ed16249189a3b5be9331c81152485cf2c2e8ce2e22627345352d1be`.

The archive return records builder exit 1 because the normal remote artifact
index does not exist. The extraction record says rejected before extraction,
has no member inventory, and proves no content extracted. The cleanup receipt
validates and removes only
`/Users/pandocs-agent-001/.libwebp-metal-backref-cost-workspace-remote-v4/run.0LaIs9`
and proves it absent.

The local returned-evidence index has SHA-256
`98be2575c1298faaec4eb6582de1a6d62d0e4625ee5a942fdf08bc9b2af2c287`.
All seven indexed protocol files match their byte counts and hashes. It
explicitly excludes the later `transfer-cleanup.json`, whose SHA-256 is
`af8d7d58d602026d032e62d79b3ee501fbb5dc87e1cabe8e9f37b53816c264bd`.

No normal preflight, correctness, command, sample, evaluation, resource, or
artifact-index record survived because the operator stopped before producing
normal evidence. Therefore execution-time hardware, compiler/effective SDK,
AC/LPM/thermal state, memory/disk, child RSS, and pre/post timing state are
unassessed. Control-flow progress to the missing `cmake` call does not replace
the required records.

## Frozen criteria audit

| Criterion | Outcome |
|---|---|
| ancestry, manifest, artifact hashes, schemas, frozen order/counts | pass |
| candidate equivalence, integer/tie behavior, fallback, private default-off gates | pass in source and untimed checks |
| v3 canonical path and repository-context admission behavior | preserved; untimed checks pass |
| source bundle, exact commit/tree/clean/source hashes | pass |
| `Runner.Worker`/benchmark/CUDA absence at returned driver checks | pass |
| executor host/compiler/SDK/power/thermal/resource records | absent; unassessed |
| independent lease acquisition/release transfer | pass |
| archive/member/artifact-index/extraction | no archive; stopped safely before extraction |
| local returned protocol-file index | pass for all seven indexed partial records |
| exact-child cleanup and absence proof | pass |
| executor correctness/fallback matrix | absent; 0 of 26 |
| command/sample/evaluation inventory | absent; 0 of 408 commands and 0 of 1,560 measurements |
| 12 holdout paired medians at most `0.99` | absent; no ratios |
| 12 holdout p95 ratios at most `1.01` | absent; no ratios |
| conjunctive promotion decision | **cannot pass; reject promotion** |

## Untimed evaluator checks

No remote rerun, timing, local timed fallback, CUDA command, recorder, lease,
host/power change, runner service/directory access, threshold change, or new
experiment was performed. The evaluator ran:

```sh
python3 -m py_compile scripts/*remote_v4*.py
python3 scripts/test_backref_cost_workspace_remote_v4_archive.py
python3 scripts/test_backref_cost_workspace_remote_v4_admission.py
python3 scripts/test_backref_cost_workspace_remote_v4_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_workspace_remote_v4_experiment.py
```

All passed. The candidate test passed 26 cells covering bitstream identity,
decoded pixels, repeat determinism, injected transactional fallback, default
omission, predecessor-gate isolation, immutable inputs, undefined/integer
sanitizers, array bounds, and pointer overflow.

Separate minimal default and v4 shared-library builds and installations passed
installed-header and exported-symbol ABI equality. A broader optional-tool
build also exposed the pre-existing `gif2webp` include failure for
`sharpyuv/sharpyuv.h`; the v4 library and runner had already compiled, the
failure is outside the files changed by v4, and no unrelated repair is included
in this focused consequence.

## Production consequence

Do not promote. Retain the v4 candidate, safe evidence builder/extractor,
independent lease/cleanup return channels, protocol, and evidence as default-off
research/provenance material. The missing remote `cmake` is an infrastructure
blocker, not a performance result and not a reason to discard the validated
evidence-return repair. This cycle is closed, and its zero-sample evidence must
not be relabeled or pooled into a future experiment.

The machine-readable consequence is
`evidence/backref-cost-workspace-remote-v4-execution-20260818/evaluation.json`,
SHA-256
`f9d36a4e929411d595217eff6977e4a16ed4e9c4b1cb64750a42f0d354d83de8`.
