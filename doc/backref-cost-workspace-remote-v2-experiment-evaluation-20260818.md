# Backref-cost workspace remote v2 evaluation (2026-08-18)

## Decision

Promotion is **rejected for this cycle and performance is unassessed**. The one
authorized v2 invocation stopped in the frozen transfer driver before remote
source checkout, operator validation, host admission, lease acquisition,
correctness, or timing. There are exactly zero timed child processes, zero raw
samples, zero samples for each variant, zero correctness cells, zero
statistical cells, and therefore no medians or p95 values.

The failure is infrastructure, not a protocol admission refusal and not a
performance result. The driver invoked `git bundle verify` from a remote
directory that was not a Git repository, and Git returned
`error: need a repository to verify a bundle`. The executor did not repair or
rerun the frozen protocol.

The candidate remains independently gated, default off, exact under the
permitted untimed checks, and useful for source-level reproduction, so it is
retained as research code. Retention is not promotion. The frozen driver and
protocol are also retained unchanged as provenance of the closed attempt, not
as an authorized rerun path. No production API/ABI, integer or tie semantics,
threshold, fallback, Metal/CUDA behavior, runner service, power setting, host
setting, or default changes.

## Authority and ancestry

The audited history is strictly linear:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| original main baseline | `d12036f790cce1dd4bef9fe3c963b0ef294d4c4a` | prior merged history | `8d7a9f7b755f78a2a1a0ed0d64beabfac3fa7665` |
| design/code | `66c5bca06e4371923ebd038e0776524b7c78bb9e` | original main baseline | `81144cd74b9798ca0c5fe3a3535923b10b767b8a` |
| frozen protocol | `7d56c91bbb4cb6e7e785ac23908b0c4e4da032ec` | design/code | `f0b447221c0a24e715a99b18e218049f2e4c032d` |
| executor/evidence | `fd884951344a64f6b9613b2f51e652aaa4441cb2` | frozen protocol | `8b449daff7af3da31e307a5641d1bbdbf5e8cdbe` |
| evaluator consequence | separate descendant containing this report | executor/evidence | recorded by the evaluator commit |

The design commit contains the private candidate and its untimed gates. The
protocol commit adds only the frozen protocol machinery and design-time path
record. The executor commit adds only the five evidence files beneath
`evidence/backref-cost-workspace-remote-v2-20260818-executor`; it does not
change the candidate or frozen protocol.

## Frozen authority, schemas, and evidence integrity

All 21 manifest-frozen artifacts independently match their recorded SHA-256
values. Principal authority hashes are:

| Authority | SHA-256 |
|---|---|
| frozen manifest | `f31fba930b44fd5f55b1fc90505402af0a5a234c9970ed7320fa6352427e599b` |
| schema catalog | `098eaa582c4b645317338c40e29dc7d202d86a8147e92ad361574dd396e4e0e1` |
| remote operator | `a7e14691ef801e057a601758206603851765872998e5e262041c97cd86886f59` |
| transfer driver | `8c27da47b3bb0d4dc0e68408101be8c4dc84ef495e863c6d373e350e31158911` |
| path guard | `8ed9626bed6e97e31698cc059d990902d6960124350d49374274d2d1f628ebef` |
| protocol document | `ace0d2ddedd99e9e445c9b2368cdb1f713d40e7b3c594c27f5e70f479950f373` |
| executor artifact index | `ed54e58db44064f31d6cbffd86e0a33ed2e6ef6bfe34036ccfa2a026a205606e` |

Every one of the 12 schema identifiers referenced by the manifest is defined
by the frozen catalog. No normal protocol object was emitted. In particular,
there is no frozen-schema preflight, source-hash, lease, correctness, sample,
command, evaluation, resource, remote artifact-index, transfer/cleanup, or
returned-evidence-index record to validate.

The executor's three JSON envelopes use explicit partial-evidence identifiers:

- `libwebp-backref-cost-workspace-remote-v2-executor-blocker-v1`;
- `libwebp-backref-cost-workspace-remote-v2-exact-cleanup-check-v1`;
- `libwebp-backref-cost-workspace-remote-v2-executor-artifact-hashes-v1`.

Those identifiers are not normal-output schemas in the frozen catalog and are
not counted as completed protocol records. They parse, agree on the exact
commits, path, failure stage, zero inventory, unacquired lease, and cleanup,
and the artifact index matches all four indexed files by path, byte count, and
SHA-256. The index itself is the fifth file and is not self-indexed.

The older row-11 and row-12 refusals are candidate provenance only. They are
not pooled, relabeled, or counted as v2 correctness or performance data.

## Candidate identity, default-off guard, and correctness

The independent evaluator projection preprocesses the exact merged algorithm
at original main under its prior private gate and the v2 implementation under
the new private gate. It canonicalizes only private helper/gate names and
assert source locations. The results exactly match the manifest:

- preprocessed boundary projection:
  `e4d32a2968b0fc3922e63b627c07dc6b41aa2d95b44c62b3f446d92e2258e9fd`;
- normalized helper body:
  `cf4c3784dfafdd7f6e699524c2277cd626ac84d80a2573f700b56ee4681ce068`.

The retained implementation therefore has the same single exact-sized
allocation, 490 workspace interval nodes after ten inline nodes, integer cost
arithmetic, strict comparisons and ties, update and reference order,
traceback, cache choice, and transactional allocation-failure fallback as the
merged exact workspace algorithm. No installed/public header or Metal/CUDA
source changed in the design commit.

Default CMake and Unix make builds leave
`WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT` off and omit the v2
source, private macro, symbols, runtime/fault strings, and runner target. The
private build gate is mutually exclusive with both predecessor workspace
gates. Activation additionally requires exact runtime value `1`; prior or
invalid values do not activate it. The runner checks exact
`WEBP_BENCHMARK_SESSION=exclusive` before reading an input, and both launchers
fail closed without that value.

The evaluator's untimed suite passed all 26 publication-corpus case/quality ×
method 4/6 cells. Baseline, candidate-off, candidate, repeat, injected
fallback, prior-gate-only, and default-build-with-v2-environment streams were
identical; candidate output decoded to exact source pixels; corpus bytes were
immutable; and undefined/integer plus array-bounds/pointer-overflow sanitizer
smoke checks passed. These results support safe default-off retention only.
The mandatory executor correctness matrix remains absent.

## Remote source, admission, isolation, and refusal semantics

The exact invocation was made once from clean frozen protocol commit
`7d56c91bbb4cb6e7e785ac23908b0c4e4da032ec`, with the required expected-commit
and exclusive-session variables, against only `ssh pandocs-agent`. The local
bundle was created and copied to the generated direct-HOME safe child. The
driver compared local and remote bundle hashes in memory and advanced, but did
not persist those hashes before its temporary local transfer directory was
removed.

The next compound remote command ran `git bundle verify` before cloning or
changing into a repository. Git requires repository context for bundle
verification and returned status 1 with the recorded error. The evaluator
reproduced the same status and error with an untimed local bundle outside a
repository, while verification of that bundle from the current repository
succeeded. This establishes the frozen driver defect without changing it or
running the experiment.

The remote operator was never launched. Consequently, there is no executor
record for Darwin/arm64, `Mac16,10`, Apple M4, 24 GiB memory, available memory
or disk, Xcode clang 17, macOS 26.2 SDK, effective developer variables, AC
power, Low Power Mode, thermal/performance warnings, immediately-pre-timing or
post-timing process isolation, or serial timed execution. The pretransfer
`Runner.Worker` guard did run and advance, but its process-table hash was not
emitted before failure. It cannot be reconstructed as executor evidence.

The outcome is therefore correctly classified as one infrastructure blocker,
zero protocol refusals, and admission not reached. Current live state and the
earlier design-time path record are safety corroboration, not substitutes for
the three required execution-time states.

## Transfer, lease, path, and cleanup

Source transfer did not complete because bundle verification failed before
clone, checkout, exact-HEAD, and clean-worktree validation. No evidence archive
was created or returned, so there are no archive hashes, contained extraction,
remote artifact-index verification, or returned-evidence hashes. Mandatory
source and evidence transfer-integrity gates are unsatisfied.

The operator never started, so the scoped lease was never opened or acquired
and no lease record exists. Release is not applicable to an unacquired lease,
but the completed-run acquisition/release evidence gate is absent. At
`2026-08-18T16:39:33Z`, an untimed read-only live check found no holder of the
v2 lease path.

The driver's `finally` path used the same canonical validator to remove only
`/Users/pandocs-agent-001/.libwebp-metal-backref-cost-workspace-remote-v2/run.ucrqiS`.
The committed cleanup record proves that exact child absent at
`2026-08-18T16:28:56Z`; the evaluator independently confirmed it still absent.
Source inspection shows no access to an installed runner directory or service.

The required untimed live path round trip also passed during evaluation. It
accepted generated direct child `run.vHof56`, rejected malformed, sibling,
symlink, and traversal fixtures, removed only that validated child, and proved
absence. Its process guard found no `Runner.Worker`; `Runner.Listener` remained
present and untouched. No timed binary ran and no lease was acquired.

## Inventory, statistics, resources, and frozen gates

The frozen order and inventory reconstruct exactly from the manifest: tune
before holdout; photo, graphic, texture; method 4 before 6; cold before warm;
11 alternating cold pairs and six alternating warm pairs. Observed executor
inventory is:

| Record class | Frozen requirement | Executor evidence |
|---|---:|---:|
| timed child command processes | 408 | 0 |
| cold retained samples | 264 | 0 |
| discarded warmups | 288 | 0 |
| warm retained samples | 1,296 | 0 |
| total retained samples | 1,560 | 0 |
| retained samples per variant | 780 | baseline 0; candidate 0 |
| executor correctness cells | 26 | 0 |
| statistical cells | 24 | 0 |
| required holdout cells | 12 | 0 |

There are no paired median ratios and no nearest-rank p95 ratios. Nothing can
be compared with the required `0.99` median or `1.01` p95 ceilings. There is
also no child RSS, total lease duration, timed-child wall duration, evidence
size, or execution-time memory/disk record. No speedup, regression, tie,
resource-bound, or production-readiness inference is supported.

| Frozen promotion criterion | Outcome |
|---|---|
| exact ancestry, frozen hashes, schema linkage, partial-evidence hashes | pass |
| candidate identity, private gates, default omission | pass in source and untimed tests |
| integer/tie semantics and transactional fallback | unchanged; untimed tests pass |
| safe path validation and exact cleanup/absence | pass |
| exact remote checkout and source-transfer record | fail: checkout blocked and record absent |
| required host/process/compiler/SDK admission states | absent; unassessed |
| executor correctness/fallback matrix | absent; 0 of 26 |
| command/sample/statistical inventory | absent; zero samples |
| all 12 holdout medians at most `0.99` | absent; unassessed |
| all 12 holdout p95 ratios at most `1.01` | absent; unassessed |
| resource ceilings and evidence transfer integrity | absent; unassessed |
| lease acquisition/release record | never acquired; completed-run gate absent |
| frozen all-gate promotion rule | **cannot pass; reject promotion for this cycle** |

## Untimed evaluator validation

No timing, CUDA command, follow-up experiment, host-setting change, service
change, or lease acquisition was performed. The evaluator ran only the frozen
compile, path, protocol, guard, equivalence, correctness, fallback, sanitizer,
and live path checks:

```sh
python3 -m py_compile \
  scripts/backref_cost_workspace_remote_v2_paths.py \
  scripts/run_backref_cost_workspace_remote_v2_experiment.py \
  scripts/execute_backref_cost_workspace_remote_v2.py

python3 scripts/test_backref_cost_workspace_remote_v2_paths.py
python3 scripts/test_backref_cost_workspace_remote_v2_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_workspace_remote_v2_experiment.py
python3 scripts/execute_backref_cost_workspace_remote_v2.py path-round-trip
```

All passed. A final frozen-source `validate` check is run from the clean
consequence tree before delivery; it validates hashes and source identity only
and does not enter admission, acquire the lease, or invoke timing.

## Production consequence and limitations

The final consequence is **do not promote; retain all v2 files as default-off
research/provenance material**. No candidate, protocol, evidence, runner,
driver, or path file is removed. Ordinary production builds and behavior are
unchanged.

This cycle proves source identity, default omission, untimed exactness and
fallback, path safety, and exact cleanup. It proves no execution-time host or
resource state and no performance direction. The sole blocker is the frozen
driver's pre-operator bundle-verification context, which prevented every
mandatory admission and measurement gate. This cycle is closed: any repair or
follow-up requires wholly new gates and a newly frozen protocol and is not run
here.
