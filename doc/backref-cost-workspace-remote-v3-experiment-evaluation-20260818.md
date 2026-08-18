# Backref-cost workspace remote v3 evaluation (2026-08-18)

## Decision

Promotion is **rejected for this cycle and performance is unassessed**. The
committed refusal records that the one authorized v3 invocation reached
evidence return, matched the remote and local archive SHA-256 values in memory,
and then stopped because the frozen safe extractor rejected an unsafe archive
member. The archive, its digests, and the rejected member name were not
retained, so the hash-match claim cannot be independently recomputed. No
returned archive member was used as evidence, and no retry, alternate
extraction, local fallback, or follow-up experiment was run.

Committed executor counts are exactly zero: zero timed child commands, zero raw
sample rows, zero retained samples for either variant, zero warmups, zero
executor correctness cells, and zero statistical cells. There are no medians
or p95 values. The frozen `0.99` paired-median and `1.01` p95 ceilings are
therefore inapplicable to observed data and cannot pass the conjunctive
promotion rule.

The candidate remains independently gated, default off, and exact under the
permitted untimed checks, so it is retained as research code. Retention is not
promotion. The frozen protocol and drivers are retained unchanged as provenance
of this closed attempt and are not an authorized rerun path. No production
API/ABI, integer or tie semantics, threshold, fallback, Metal/CUDA behavior,
runner service, power setting, host setting, or default changes.

## Authority and ancestry

The audited history is strictly linear:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| main baseline | `805e5ac4341ccf0d1ef960adb9107275652c973f` | merged prior history | `5f6c2262337ba7f9c34cf3425508898c34d8c64b` |
| design/code | `1b6f6b707e79bfcfc1d912bf1b4c916b3f7b58e5` | main baseline | `f01a0ff85503865582195703c6b091966ffa4da7` |
| frozen protocol | `9617a720a882bef739caca019a76e45d8a9b17e6` | design/code | `34ebeeca0ea835c7f8dc874ec03a921424d1cd42` |
| executor/evidence | `61506a40775305a0723c724b8da965e277ecf5da` | frozen protocol | `a43e2472aa82d7ef47e4e6cc33d0bbd3e2031ed9` |
| evaluator consequence | separate descendant containing this report | executor/evidence | recorded by the evaluator commit |

The design commit contains the private candidate and admission implementation.
The protocol commit adds the frozen manifest, schema catalog, operator, tests,
and design-time admission rehearsal. The executor commit adds only the four
files beneath
`evidence/backref-cost-workspace-remote-v3-execution-20260818`; it does not
change the candidate or frozen protocol.

## Frozen authority, schemas, and executor artifacts

All 23 manifest-frozen artifacts independently match their SHA-256 values.
Principal authority hashes are:

| Authority | SHA-256 |
|---|---|
| frozen manifest | `86f81b75c00a6e3cb87849ccdb112c885eae8e4f230f28e284e615ba57519de5` |
| schema catalog | `d5dcc8bd8252615c31c8d6be95668508af0b94fde50f8d7f5ff421703f172398` |
| remote operator | `1bc27f6d17ed58ae16485e5133a717cdc2f4e1b206549b9e54ac6d0223dac1ef` |
| transfer driver | `605bc0b78e37338d504792095199ce795c810c11e03d0bc2cd2e1e03d529ac82` |
| admission implementation | `c61dab4bf19ccd91ecbc0553fc96d3d1a9f1e9f38064db433f6ee526b8c8e28e` |
| path guard | `963a80b757e19dde249df746fca52e6b370526e3a06d0f70a8bf3c1ba161d8b8` |
| protocol document | `2ba064a7befa115aea7e687bc5bc4ec0e6ddfe1a2942201fdc367cc6b68dcaf7` |
| executor artifact index | `81f24aaf2745979db9173f6f862c72a9d90fd40437b664e01170b23447f651e7` |

All 13 normal schema identifiers referenced by the manifest are defined by the
catalog. The schemas are required-field catalogs, not complete type or value
validators. The executor refusal uses the explicit partial-evidence identifier
`libwebp-backref-cost-workspace-remote-v3-executor-refusal-v1`; it is not a
normal-output schema and is not counted as a completed protocol record.

The executor index exactly matches the byte counts and SHA-256 values of
`driver-error.log`, `operator-report.md`, and `refusal.json`. The index itself
is the fourth file and is not self-indexed. The refusal envelope, report, and
error transcript agree on the frozen identities, one invocation, archive
rejection, zero returned inventory, missing lease and exact-cleanup receipts,
and fail-closed disposition.

No normal preflight, source-hash, lease, correctness, sample, command,
evaluation, resource, remote artifact-index, transfer/cleanup, or local
returned-evidence-index record was returned for independent validation.

## Candidate identity, default omission, correctness, and fallback

The evaluator independently preprocessed the exact merged algorithm through
the predecessor private gate and the v3 gate, canonicalizing only private
helper/gate names and assert source locations. The values exactly match the
manifest:

- preprocessed boundary projection:
  `5950bd122c5affc30585568c938815db316f7e89b01f38613d8634dcb33eb21f`;
- normalized helper body:
  `78d176a6828c205102e69ad801a97a7546beaac481da2b8044fa42829f3860fc`.

The retained candidate therefore preserves the validated single exact-sized
allocation, 490 workspace interval nodes after ten inline nodes, integer cost
arithmetic, strict comparisons and ties, update and reference order,
traceback, cache choice, and transactional allocation-failure fallback. The
design commit changes no installed/public header and no Metal or CUDA source.

Default CMake and Unix make builds leave
`WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT` off and omit the v3
source, private macro, symbols, runtime/fault strings, and runner target. The
private build gate is mutually exclusive with all predecessor workspace gates.
Activation additionally requires exact runtime value `1`; the runner checks
exact `WEBP_BENCHMARK_SESSION=exclusive` before input loading.

The evaluator's local untimed suite passed all 13 publication-corpus
case/quality rows by methods 4 and 6, for 26 correctness cells. Baseline,
candidate-off, candidate, repeat, injected fallback, prior-gate-only, and
default-build-with-v3-environment streams were identical; candidate output
decoded to exact source pixels; corpus bytes were immutable; and
undefined/integer plus array-bounds/pointer-overflow sanitizer smoke checks
passed. These checks support safe default-off retention only. The mandatory
executor correctness matrix remains absent.

## Admission, remote identity, and execution-state evidence

The frozen canonical path guard accepts only a real, canonical direct child
matching `run.[A-Za-z0-9]{6}` beneath the exact direct-HOME v3 safe root. The
same validator authorizes recursive removal only after revalidating that exact
child. Local unit tests reject malformed, sibling, nested, traversal, and
symlink fixtures and prove exact-child absence after cleanup.

The frozen design-time admission rehearsal is valid provenance for commit
`1b6f6b707e79bfcfc1d912bf1b4c916b3f7b58e5` and tree
`f01a0ff85503865582195703c6b091966ffa4da7`. It records matching local/remote
bundle SHA-256
`580aba4ce6e0c076002d88ba207f6c491dc03c3d262977f67422a66dc3b16390`,
verification from the scoped empty bare repository, removal of that repository,
exact detached checkout/tree/clean/source identities, separately hash-matched
malformed rejection, absence of malformed verification/clone state, no
`Runner.Worker`, an untouched listener, and exact cleanup of `run.RaTDMU`.
That rehearsal acquired no lease and invoked no timed binary.

The timed driver can reach evidence retrieval only after its shared admission
function returns, but the run-specific admission object and source bundle hash
were not persisted or returned. Control-flow inspection and the earlier
rehearsal do not replace the required timed-run receipt. Exact remote checkout,
tree, clean status, source hashes, and source-transfer hash criteria are
therefore unsatisfied for the executor cycle.

Likewise, none of the required execution-time Darwin/arm64, `Mac16,10`, Apple
M4, 24 GiB memory, available memory/disk, Xcode clang 17, macOS 26.2 SDK,
effective developer variables, AC power, Low Power Mode, thermal/performance,
preflight/pre-timing/post-timing process isolation, sole serial execution, or
child-stderr records was returned. These criteria are absent and unassessed.
Current or design-time state cannot reconstruct them.

## Evidence return integrity

The frozen extractor allows only contained regular files and directories below
the top-level `evidence` member and writes no rejected member. It correctly
failed closed before moving an output directory into place. The executor's
only retained assertion is that the remote and local archive hashes matched
before extraction. Neither digest, the archive, its member inventory, the
pipeline exit status/output, nor the offending member name was retained, so the
archive cannot be independently inspected and the cause cannot be narrowed
beyond an unsafe returned member.

No remote artifact index was extracted or verified. In addition, source
inspection finds a frozen protocol defect independent of this refusal: the
manifest and protocol require a local
`returned-evidence-hashes.json`, but the v3 driver has no code that creates it.
Even a clean extraction would not satisfy that conjunctive criterion. Any
repair requires wholly new gates and a newly frozen protocol; it is not run in
this cycle.

Because retrieval raised before `transfer-cleanup.json` was assembled, the
driver's `finally` cleanup path discarded the cleanup return value. Thus no
pipeline receipt, evidence-transfer digest pair, lease-release value, exact
timed-child path, or exact-child cleanup proof survives.

## Lease and cleanup

The operator source acquires the user-scoped nonblocking lease only after
initial host/process preflight and releases it in an inner `finally` before
return. Its outer `finally` writes the lease record. Those source properties do
not prove what happened in the executor run: no lease record was returned, so
acquisition and release are both unverified and the mandatory release receipt
is missing.

The driver cleanup source revalidates the canonical exact child before removal,
and the executor refusal says its `finally` path ran. A current-state remote
check found canonical HOME `/Users/pandocs-agent-001`, the canonical v3 safe
root with no children, an existing lease file, and no process reported by
`lsof` as holding that file. This corroborates a clear current safe root and no
current lease holder; it does not prove historical release or exact timed-child
cleanup because the exact child and receipts are absent.

The first current-state check was read-only. During a second lease-holder check,
the evaluator mistakenly redirected `lsof` output to `/tmp/should-not-write`
and immediately removed that temporary file. This was a procedural deviation
from the read-only-only remote-check constraint. It did not touch the safe
root, lease file, runner directories/services, host settings, or power state,
and it is not treated as protocol evidence.

## Inventory, statistics, resources, and criteria

The frozen order reconstructs exactly: tune before holdout; photo, graphic,
texture; method 4 before 6; cold before warm; 11 alternating cold process pairs
and six alternating warm process pairs. Cold retains one encode per process;
warm discards two and retains nine. The expected and returned inventories are:

| Record class | Frozen requirement | Returned executor evidence |
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

Warm process medians, paired candidate/baseline median ratios, and nearest-rank
p95 ratios cannot be computed. There is also no child RSS, total lease
duration, timed-child wall duration, evidence size, or execution-time
memory/disk record. No speedup, regression, tie, resource-bound, host-state, or
production-readiness inference is supported.

| Frozen promotion criterion | Outcome |
|---|---|
| exact ancestry, frozen hashes, schema linkage, executor artifact hashes | pass |
| candidate identity, private gates, default omission | pass in source and untimed tests |
| integer/tie semantics and transactional fallback | unchanged; untimed tests pass |
| canonical path validation and malformed cleanup design | pass in source, rehearsal, and untimed tests |
| timed-run exact remote checkout/source-transfer receipt | absent; unassessed |
| required host/process/compiler/SDK states and child stderr | absent; unassessed |
| executor correctness/fallback matrix | absent; 0 of 26 |
| command/sample/statistical inventory | absent; zero returned samples |
| all 12 holdout medians at most `0.99` | inapplicable; no values |
| all 12 holdout p95 ratios at most `1.01` | inapplicable; no values |
| resource ceilings | absent; unassessed |
| remote archive safety and artifact-index verification | fail: unsafe member; no extracted index |
| local returned-evidence index | fail: absent and frozen driver never creates it |
| lease acquisition/release receipt | absent; mandatory release unverified |
| exact timed-child cleanup receipt | absent; current safe root is clear only |
| frozen all-gate promotion rule | **cannot pass; reject promotion for this cycle** |

## Untimed evaluator validation

No timing, rerun, remote benchmark, CUDA command, local fallback, recorder,
lease acquisition, runner service/directory access, power/LPM change, host
setting change, or follow-up experiment was performed. The evaluator ran only
local syntax, static protocol, admission-unit, build-gate, equivalence,
correctness, fallback, omission, and sanitizer checks:

```sh
python3 -m py_compile \
  scripts/backref_cost_workspace_remote_v3_paths.py \
  scripts/backref_cost_workspace_remote_v3_admission.py \
  scripts/run_backref_cost_workspace_remote_v3_experiment.py \
  scripts/execute_backref_cost_workspace_remote_v3.py

python3 scripts/test_backref_cost_workspace_remote_v3_admission.py
python3 scripts/test_backref_cost_workspace_remote_v3_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_workspace_remote_v3_experiment.py
```

All passed. The live path-round-trip command was deliberately not rerun because
it creates and removes a remote child; only current-state corroboration was
needed after the executor's returned refusal artifacts.

## Production consequence and limitations

The final consequence is **do not promote; retain all v3 files as default-off
research/provenance material**. No candidate, protocol, evidence, runner,
driver, or path file is removed. There is no unsafe production-facing change:
ordinary production builds omit every v3 source, symbol, target, macro, and
runtime/fault string, and ordinary behavior is unchanged.

This cycle proves frozen local identity, default omission, untimed exactness and
fallback, design-time admission behavior, conservative archive refusal, and a
clear current remote safe root. It proves no execution-time host/resource
state, no run-specific source/admission receipt, no lease acquisition/release,
no exact timed-child cleanup receipt, no correctness matrix, and no performance
direction. The blockers are the unsafe returned archive member with
non-retained diagnostics/evidence and the frozen driver's missing local
returned-evidence index. This cycle is closed; any follow-up requires wholly
new gates and must not reuse or relabel this cycle's zero-sample evidence.
