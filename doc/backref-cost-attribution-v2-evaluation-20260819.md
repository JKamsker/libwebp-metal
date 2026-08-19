# Backref-cost attribution v2 — Phase 3 evaluation and consequence

## Decision

Phase 2 is a valid fail-closed diagnostic refusal, not accepted timing
evidence. The interval-search family is **not closed** and its performance
remains unassessed by v2. The refusal does, however, identify a sufficiently
specific defect to warrant one wholly new, independently gated attribution-v3
experiment. That proposal is diagnostic-only; it is not implemented or run in
this cycle.

There is no production-promotion authority and no end-to-end photo conclusion.
No next CPU stage is ranked. One baseline `photo-large`/method-4 process cannot
support a cross-case or cross-method ranking, and its nested DP accounting is
invalid.

## Ancestry and frozen identity

- Exact main base: `d63c9ed99e2d72e3f0aca1d375d31fad19e13455`
  (tree `d97447a4fb7f07e3879a85d6a2af725e48ddea0f`).
- Phase 1: `e42e35f155f3b91b557e21807b2e8f7b69db6e1b`
  (tree `6057b0dd97ccf9b5e7444f0405b05d7dcae51325`), whose exact parent is the
  base.
- Phase 2: `1eaa3488ceb31180298e2d97528c0a3ac7fec205`
  (tree `23b1418e9e90a516f921f10eebf228acee641b6b`), whose exact parent is
  Phase 1.
- All 25 entries in the frozen Phase-1 manifest match their SHA-256 values.
  The manifest, protocol, and Phase-1 validation SHA-256 values are respectively
  `db29b92de24a567e4e8bf99dc444ae68f3607ae53eab94b77193a32fe7fd9e1b`,
  `d983c27032d07e015c487720cd9975912cca0355bcc15fa4408222002a018ba4`,
  and `b5e05688f44d5ba59cf72d89da75f51963c8385b914f7e0f55836a4b92c7f810`.

The source checkout returned from Phase 2 is the exact Phase-1 commit and tree,
is clean, has all frozen source hashes, and came from bundle SHA-256
`0a356ed572be3486c2c576b7caefb096f5771b0d0fab8097872c4c8a5d952169`.
The bundle hash matched on both sides, was verified in repository context, and
the temporary verification repository was removed.

## Gates, surface, and semantic audit

The fresh identities are present and default-off:

- build: `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT`;
- compile: `WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT`;
- runtime: `WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT=1`.

The 22-row global experiment guard passed, including mutual exclusion from all
overlapping backref/stage experiments. The exact runtime guard accepts only
`1`; the run mode requires exact `WEBP_BENCHMARK_SESSION=exclusive`, while
validate and rehearsal require absence. A fresh ordinary CMake build omitted
v2 objects and identity strings. Public headers under `src/webp` and
`sharpyuv` do not differ from the exact base. Phase 1 records the corresponding
public symbol/export-surface check; Phase 3 did not repeat a binary ABI-pair
comparison.

The `PushIntervalSpecialized` body remains byte-identical to `673bc3fa`, and
the single optimized runner contains all required private symbols. Its SHA-256
is `f6f4a46ec1b8a14764c7ec175f0a09b2207618cf0fe72a32f93bee97a9d9e6d4`.
The realized build used Apple clang 17.0.0, SDK 26.2, and
`-O3 -g -DNDEBUG -fno-omit-frame-pointer` on Apple M4/Mac16,10, with Metal
disabled. Coarse timers use `mach_continuous_time`; external profiler
invocations are zero.

The static semantic audit found a v2-specific control-flow defect. In
`VP8LBackwardReferencesTraceBackwards`, the attribution branch executes the
runtime-selected DP body inside `dp_total`. After that preprocessor branch,
the pre-existing common baseline block also executes unconditionally. Thus
each successful traceback runs two DP bodies, but only the first is included
in `dp_total`; the second baseline result overwrites the first result. This is
consistent with every raw record reporting three `dp_total` calls but six
`setup` and six `steady` calls.

This defect is confined to the default-off diagnostic build, but it defeats
v2's single-selected-DP semantic boundary. The passing bitstream and decoded
RGB checks establish that the produced files are correct and deterministic;
because the second baseline DP overwrites the first, they do not independently
establish a clean candidate execution path.

## Exact Phase-2 authorization and execution boundary

The sole frozen command was:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V2_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v2.py run \
  "$PWD/evidence/backref-cost-attribution-v2-execution-20260819"
```

At authorization time `HEAD` was the Phase-1 commit. The returned source
commit/tree, exclusive-session records, run-mode status, and one command log
are consistent with that invocation. The Phase-2 handoff states it was invoked
once; no separate local shell transcript is committed, so the outer invocation
count is not independently recoverable from the archive. No retry, fallback,
profiler, or alternate performance command is evidenced or authorized.

The plan contains 24 serial profile processes in the frozen case/method/order.
Only `p00-photo-large-m4-baseline-r0` ran. Its runner exited zero and emitted
five output plus five stage records: one warmup and four retained records. The
operator then refused before a post-profile process snapshot, any candidate
timing, another profile, profile completeness, repeat stability, stage-share
stability, aggregate, or median.

## Correctness and raw timer evidence

Before timing, all four case/method cells completed two baseline and two
candidate correctness encodes: 16/16 files. For every cell, baseline/candidate
bytes match, both repeats match, and the runner decoded RGB and compared it to
the input. The summary SHA-256 is
`a45ddd943a55f2d24f292d6f67d387cb1e8fb13fcd197ca60543c7327ec26870`.

The four retained timer records contain these raw values; they are shown only
to demonstrate the refusal and must not be aggregated as performance results.

| Encode | DP total ns | Setup ns | Steady ns | Setup + steady ns | Excess ns | Calls total/setup/steady |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 30,405,000 | 2,382,833 | 58,373,207 | 60,756,040 | 30,351,040 | 3 / 6 / 6 |
| 2 | 31,231,625 | 2,489,458 | 59,111,833 | 61,601,291 | 30,369,666 | 3 / 6 / 6 |
| 3 | 31,249,167 | 2,444,417 | 59,821,333 | 62,265,750 | 31,016,583 | 3 / 6 / 6 |
| 4 | 30,932,541 | 2,438,835 | 59,243,958 | 61,682,793 | 30,750,252 | 3 / 6 / 6 |

All five stage records, including the warmup, violate
`setup + steady <= dp_total`. Raw timers therefore exist, but there are zero
accepted timer records, zero accepted profiles, zero accepted aggregates, and
zero accepted medians. The raw stage and runner SHA-256 values are
`aabb9c408a89807d32dd0477b5bc54cd659764996a2a100d28c18e965fba2c20`
and `357c9edaa6501e6a53ff2539d27fcf1541a5c967021d5c3fb8c88460071eaef0`.
The refusal record SHA-256 is
`443ef4d0fca499918c67b70965360fbd4ab1d772b28572de35c695ccb52a0094`.

## Ownership, resources, return, and cleanup

Admission and pre-profile checks recorded AC power, low-power mode off, no
thermal/performance warning, more than 10 GiB available memory, more than
17 GiB available disk, no benchmark/CUDA conflict, no `Runner.Worker`, and an
allowed `Runner.Listener`. Process discovery was observe-only. Workload-free
Phase-3 tests confirm that discovered PIDs cannot enter a signaling API and
preserve the attribution-v1 remediation guard.

The exclusive lease was acquired once and released. Its independently
transferred SHA-256 is
`84408caa33956236e00ac37a23b56eaff8d03b8db33258e03e31fbaaa539b95a`.
The controlled refusal archive has 39 members and 2,272,835 bytes, with
archive SHA-256
`a04d8ddd9deab2151404d030109df3ce1f0716d024c9cc9de8721edeb78b320e`
and inventory SHA-256
`89773b8edf8ca981fd3eb6ed023d9de9ca2342dca495d20d36219232c64badd0`.
Transfer hashes, inventory, extraction, and the 43-entry returned index all
verify. Exact-child cleanup removed only the validated
`run.bV1QRB` directory and proved absence. No installed runner directory,
host, service, power, authentication, permission, or toolchain setting was
changed.

## Research consequence: one bounded v3 diagnostic

The evidence warrants a new attribution-v3 diagnostic, not a v2 rerun. It must
be designed and frozen in a separate phase with wholly new identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT`;
- exact runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT=1`;
- a new manifest/schema/evidence root, remote safe root, and exclusive lease.

Its exact source boundary must execute exactly one selected DP implementation
per `VP8LBackwardReferencesTraceBackwards` call. The selector is evaluated once
before mutation. `dp_total` starts immediately before that one call and ends
after its cleanup; `setup` covers allocation through successful
`CostManagerInit`; `steady` covers only the pixel DP loop; traceback and chosen
path materialization remain after DP and separately timed. There may be no
clock in `PushInterval` or another per-pixel operation. An independent
invocation counter must require
`selected_dp_calls == dp_total.calls == setup.calls == steady.calls` on every
successful encode, as well as `setup + steady <= dp_total`.

The bounded run may use the same two immutable 3000x2000 corpus cases, methods
4 and 6, three paired repetitions, one warmup and four retained encodes per
process: at most 24 serial profile processes, 24 warmups, 96 retained records,
and 120 total records. Before timing it must repeat all 16 correctness encodes,
including decoded RGB, deterministic bytes, input immutability, exact runtime
fallback, and a test proving the baseline/candidate branch cannot fall through
to a second DP call. It must retain the original repeatability and nesting
gates and compute medians only after all profiles pass.

Safety requirements are unchanged and independently re-proved: a no-workload
rehearsal; exact clean source/toolchain/corpus hashes; optimized same-binary
identity and API/ABI/default-off omission; one noninteractive command and no
retry; one serial directly owned child; observe-only process discovery; no
discovered-PID signal path; no external profiler or attach permission; AC/LPM/
thermal/memory/disk gates; one new exclusive lease; indexed archive/transfer/
extraction; exact-child cleanup and absence proof; and zero host, runner,
service, power, authentication, permission, or toolchain mutation.

Even a successful v3 remains diagnostic-only. It may assess coarse DP and
whole-encoder deltas by case and method, but it cannot claim `PushInterval`
self time, cache/layout causality, or production benefit without separate
evidence.

## Limitations

- Only 1/24 planned profiles ran: baseline, `photo-large`, method 4,
  repetition 0. There is no timed candidate, method-6, graphic, or second/
  third repetition.
- All 5 raw timer records are unusable for accepted attribution because the
  DP nesting/accounting invariant fails. No aggregate or median exists.
- Correctness is strong for produced bytes and decoded RGB, but the duplicate
  baseline DP call means it does not prove a clean candidate-only DP path.
- Coarse clocks cannot provide internal call-stack, per-interval, layout,
  branch-predictor, or cache attribution. External profiler samples are zero.
- No post-profile process snapshot exists for the refused profile; returned
  pretransfer isolation and exact-child cleanup evidence are present.
- The archive does not contain a separate local shell transcript for the
  outer Phase-2 invocation.
- Phase 3 performed no encoder/profiler workload, rerun, retry, parameter fit,
  sanitizer run, or binary ABI-pair rebuild. The default-off source and public
  header checks passed, and Phase 1's ABI/export result remains the recorded
  binary check.

Machine-readable criteria, raw counts, hashes, limitations, and the v3 proposal
are in
`evidence/backref-cost-attribution-v2-evaluation-20260819/phase3-audit.json`.
