# Backref-cost workspace remote A/B evaluation (2026-08-18)

## Outcome

The independent `backref_cost_workspace_ab` cycle produced no A/B performance
result. Designer commits `460a69a864bbabc2f5890ec6aea7b1c622944bca`
and `280949088c788fa0155cdda7312320da3bc898a6` prepared the default-off
candidate and froze remote protocol v1. Executor evidence commit
`d8367a128726fc431790cc50e33c1a0113fbea0a` records a fail-closed
driver refusal before source transfer, remote preflight, lease acquisition,
correctness, or timing.

The generated remote directory
`/Users/pandocs-agent-001/.cache/libwebp-metal-experiments/backref-cost-workspace-ab-v1/run.A21KcK`
was rejected as unsafe by the frozen path-depth check. The path had the required
prefix but six slash characters, while `safe_remote_path()` required at least
seven. The executor stopped and did not repair or rerun the protocol.

Promotion is **rejected for this cycle and performance remains unassessed**.
The baseline and candidate each have zero samples and zero cells. There are no
medians, p95 values, resource records, or execution-time host/isolation records.
This refusal is a protocol/execution result, not evidence of a speedup,
regression, tie, or resource characteristic.

The implementation remains independently gated, default off, and exact under
the permitted untimed checks, so it is retained as research code. Retention is
not production promotion. Production API/ABI, integer costs, strict tie and
update order, thresholds, fallback behavior, Metal policy, CUDA behavior,
runner services, power settings, host settings, and defaults are unchanged.

## Authority and ancestry

The experiment history is linear:

| Role | Commit | Parent | Tree |
|---|---|---|---|
| main base | `e7c1be7d4070103a9b41b8c30fbbc95cd18e5a5c` | prior merged history | `f52fc7cec2f5815e78733b4b2ce3dadfa27d7039` |
| design/code | `460a69a864bbabc2f5890ec6aea7b1c622944bca` | main base | `d469c6da9f4cf302e6db019ce7fb4d5a8adf82c4` |
| frozen protocol | `280949088c788fa0155cdda7312320da3bc898a6` | design/code | `1f67c36164554cdf4dae0a8f10f62c2c8de28911` |
| executor refusal | `d8367a128726fc431790cc50e33c1a0113fbea0a` | frozen protocol | `d96deccf42e468eeebdb1556b86d40caca7473ec` |
| evaluator consequence | separate descendant containing this report | executor refusal | recorded by the evaluator commit |

The executor commit adds only `executor-refusal.json` and its checksum file.
It does not alter candidate code, protocol, criteria, counts, order, or host
policy.

## Evidence and frozen-authority integrity

The committed refusal JSON is 8,713 bytes and has SHA-256
`b130693cba6808566bbf875d9d8142d69b186997fabf82cea43b5d8b288c02d9`.
The adjacent checksum verifies it exactly. The refusal record identifies the
correct base, designer, and frozen protocol commits and records the exact
one-shot command and exit code.

All 15 manifest-frozen artifacts match their recorded SHA-256 values. The
principal authorities independently recompute as:

| Authority | SHA-256 |
|---|---|
| manifest | `d2101fd5f69ec0f111c6efd2b5d3cc21a9991312f5d2923f87f96a273ae9974d` |
| schema catalog | `d2db2c631ed2258e24e38046c311c90f6edabc3181533e84ca4b6c074e36fa84` |
| remote operator | `86cf089b734499ace04ec15562a6c4f7869ee494b71908df85816c069481831d` |
| transfer driver | `3d331d5c720ab48c2924a7493c34678a6db3cbbd874a045caefd10904c23411e` |
| protocol document | `99fef25e2507e535e380a45665b9a77063ebbdc6416b4bfb9d968326d1a5a3f6` |

The catalog defines all 11 schema identifiers referenced by the manifest. No
normal protocol object was emitted, so there is no preflight, source-transfer,
lease, correctness, sample, command, evaluation, resources, artifact-index,
transfer receipt, or returned-evidence object to validate. The refusal JSON is
explicitly labeled a local refusal record, not a normal timed-protocol artifact.

The old `backref_cost_traceback` refusal establishes candidate provenance only.
Its artifacts and zero-sample refusal are not pooled, relabeled, or counted as
performance data in this cycle.

## Candidate identity, defaults, and correctness

The focused evaluator suite independently preprocesses the exact merged main
implementation under its old private macro and the current implementation
under the new private macro. It canonicalizes only private helper names and
assert source locations. The projections are byte-identical:

- preprocessed implementation boundary:
  `b571080f12fee7abe8608696269e35e6bc3184e3a9cf49286cd47075d5a34eea`;
- normalized helper body:
  `28c03ce78195d02baa69dde46ecc043d2b641489188a48c592172140fa3cacd0`.

The retained candidate therefore preserves the merged research algorithm: one
exact-sized workspace allocation, 490 workspace interval nodes after ten
inline nodes, integer costs, strict comparisons and ties, update and reference
order, traceback, cache choice, and transactional allocation-failure fallback.
No public header or Metal/CUDA source changed in the design commit.

Ordinary CMake and Unix make builds leave
`WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT` off. They omit the new helper
source, symbols, runner target, private compile definition, runtime string, and
fault-injection string. The candidate build requires the separate private
compile gate and exact runtime value
`WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1`. The timed runner and driver both
refuse without exact `WEBP_BENCHMARK_SESSION=exclusive`.

The untimed suite passed all 26 deterministic method-4/method-6 publication
cells. Baseline, candidate-off, candidate, repeat, injected fallback,
old-gate-only, and default-build-with-new-environment streams were identical;
decoded pixels matched; corpus bytes remained immutable; and undefined/integer
plus array-bounds/pointer-overflow sanitizer smoke checks passed. These checks
support safe default-off retention, not a performance conclusion.

## Refusal, isolation, transfer, and cleanup

The driver created the scoped remote directory and immediately rejected it
before bundle transfer. The directory was empty, held zero bytes, and was
removed by the driver's exact path-checked cleanup. A read-only evaluator check
confirmed the exact path remains absent. The installed runner directory and
unrelated runner, Forgejo, GitHub, power, and host state were not touched.

Because remote preflight was never reached, there is no executor-time evidence
for AC power, Low Power Mode, thermal state, available memory/disk, exact
compiler/SDK, `Runner.Worker` absence, competing-process absence, or synchronous
timed execution. Designer remote validation is provenance and cannot substitute
for the required immediate-before-timing records. The lease was never acquired,
so release is not applicable.

No source bundle was transferred and no evidence archive was created or
returned. Archive transfer integrity is therefore not applicable. Local refusal
integrity is established by the committed blob and checksum; it must not be
misdescribed as returned remote timing evidence.

## Frozen inventory and criteria

The declared order and inventory reconstruct exactly from the manifest: tune
before holdout; photo, graphic, texture; method 4 before 6; cold before warm;
and alternating baseline/candidate process order. The observed refusal counts
are:

| Record class | Frozen requirement | Observed |
|---|---:|---:|
| child command processes | 408 | 0 |
| cold measured samples | 264 | 0 |
| discarded warmups | 288 | 0 |
| warm measured samples | 1,296 | 0 |
| total measured samples | 1,560 | 0 |
| measured samples per variant | 780 | baseline 0; candidate 0 |
| executor correctness cells | 26 | 0 |
| evaluation cells | 24 | 0 |
| required holdout cells | 12 | 0 |

Every required holdout paired-median ratio at most `0.99` and p95 ratio at
most `1.01` is absent and unassessed. Resource ceilings, exact execution-time
host/process isolation, transfer, and complete-cleanup protocol records are also
mandatory promotion gates and were not emitted. The frozen all-gate promotion
rule therefore cannot pass.

## Untimed evaluator checks

The evaluator ran no timing, changed no remote setting, and acquired no remote
lease. These checks passed:

```sh
python3 -m py_compile \
  scripts/run_backref_cost_workspace_ab_experiment.py \
  scripts/execute_backref_cost_workspace_ab_remote_v1.py

WEBP_EXPECTED_BACKREF_COST_WORKSPACE_AB_COMMIT=d8367a128726fc431790cc50e33c1a0113fbea0a \
  python3 scripts/run_backref_cost_workspace_ab_experiment.py validate

python3 scripts/test_backref_cost_workspace_ab_protocol.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_workspace_ab_experiment.py
```

The validator reproduced the frozen manifest and operator hashes. The protocol
suite passed schema linkage, inventory, frozen hashes, cleanup scope, and
missing-session refusals. The shared guard suite passed twelve independent
build/runtime guards and fail-closed leases. The focused suite returned the two
candidate-equivalence hashes above and `status: PASS`.

## Consequence and next lead

The final decision is **do not promote; retain default-off research code**.
There is no A/B result and no supported production consequence. No code,
protocol path, criterion, order, count, threshold, API/ABI, integer/tie
semantic, fallback, Metal policy, CUDA policy, runner service, power setting,
or host setting is changed by evaluation.

This cycle is closed. The next lead is a wholly new independent experiment with
new gates and a newly frozen protocol whose temporary-path safety predicate is
validated against the path it generates. That repair and any execution are
outside this cycle.
