# Backref-cost attribution v4 — Phase 3 evaluation and consequence

## Decision

The single permitted Phase-2 invocation is a valid fail-closed refusal, not
timing evidence. The remote operator returned zero, but the subsequent SCP of
`evidence.tar.gz` exceeded the frozen 30-second transfer bound. The archive,
lease receipt, correctness records, runner rows, and stage rows were therefore
not returned. There are **zero usable timing rows**, so every median, share,
delta, repeatability measure, case/method attribution, and CPU-stage ranking is
N/A. No values are inferred or pooled.

The interval-search family remains unassessed by v4; it neither closes nor
reopens. The protocol failure supports at most one wholly independent v5
diagnostic that repairs and rehearses bulk-return state preservation before
any timing authorization. It is not implemented or run here. There is no
production promotion or production semantic change.

## Exact ancestry and frozen identity

- Main base `d8e015e8395a1ae3d5d17637cacf8b99bd084901` has tree
  `23f0084230dad6932432be80027a462b2109117f`.
- Phase 1 `615b42b4766a6aad17e74707dd69f3925cb4ce3b` has tree
  `cedbffc7436a600f3941d2e28a1bb449fe428851` and exact parent main.
- Phase 2 `de1d9f94f01403dfc58149cfd5b33649b0a4b95c` has tree
  `43229241e2c7a50e9b76d95e5651c13644c7a678` and exact parent Phase 1.
- All 25 frozen manifest artifacts match their SHA-256 values. The manifest,
  protocol, and Phase-1 local-validation hashes are respectively
  `06919ccc231f92aa8bc6fee0e88794784e4e74a449e47f79cec2e7991f90dd79`,
  `34e4a91c1c9ce770690628f29ca88125af82b59285c352a98e0a874f21bb14e5`,
  and `1afbb47fb739d7a1ce5ea7ec65d341f684f16e9d515827c37e414a993eb682e7`.

Returned admission evidence verifies a clean remote source checkout at the
exact Phase-1 commit/tree, all frozen source hashes, matching local/remote
bundle SHA-256
`efd576691d1a0615f645a0c3bcc2f2f908db2ae04dced7ad17241ba88483d654`,
repository-context bundle verification, and removal of the temporary
verification repository.

## Code, gates, and timer semantics

V4 uses fresh, default-off identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT`;
- exact opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT=1`.

The build systems and source guards mutually exclude v4 from predecessors and
other overlapping experiments. Ordinary targets, objects, strings, public
headers, and ABI omit v4. The v4 private selector/counter source is v3's code
with identities renamed. Static inspection confirms the selector is read once
before mutation, one closed baseline/candidate `if/else` owns exactly one DP
call, and the predecessor fallthrough branch is excluded. `dp_total` surrounds
that selected body through cleanup; setup starts before allocation and ends
after successful `CostManagerInit`; steady contains the initial literal and
pixel loop; traceback and materialization are separately timed; there is no
per-pixel clock. The untimed tests re-proved exact fallback, opposite-body
zero, no overwrite, reset, call-count/nesting contracts, 16 correctness
encodes, 16 boundary fixtures under two sanitizer configurations, input
immutability, deterministic bytes/pixels, ABI equality, and default omission.

## Phase-2 execution and return audit

The frozen command was recorded as invoked exactly once by the Phase-2
handoff. The repository contains one run-mode receipt with
`timed_binary_invoked=true`, one remote child `run.44yTUf`, and no retry,
alternate command, profiler, CUDA, or local fallback evidence. There is no
independent outer-shell transcript, so an external invocation count cannot be
reconstructed beyond that handoff and the single receipt.

The returned facts are:

- source admission passed; remote pipeline exit code was 0;
- the evidence archive SCP timed out after exactly 30 seconds;
- six protocol artifacts totaling 772 bytes were indexed and returned;
- no archive, archive inventory, archive digest, extracted operator status,
  lease receipt, correctness result, counter result, runner row, or stage row
  was returned;
- both pipeline streams are empty;
- process snapshots after admission and before transfer found no benchmark or
  CUDA conflict and no `Runner.Worker`; the allowed `Runner.Listener` remained;
- exact-child cleanup removed only validated child `run.44yTUf` and
  independently proved it absent.

The bulk-return exception exposes a second return-state defect. The remote
operator can return zero in run mode only after setting lease acquisition
attempted, acquiring the lock, completing its gated workload, and executing
the release `finally`. Nevertheless, because the archive exception occurs
before extraction, the local executor leaves its initialized
`acquisition_attempted=false` value unchanged and emits lease state
`not-attempted`. That classification is not credible for this run. The
evidence-supported classification is **unavailable-after-attempt**: a lease
receipt is mandatory but was not returned, and release is not independently
verified. Similarly, reaching the archive SCP proves that the remote archive
builder and prior existence/hash probe completed, but the exception discarded
their in-memory transfer record; archive hash, size, inventory, extraction,
and payload integrity remain unavailable.

The returned admission receipt verifies source and observe-only process
isolation. Actual toolchain binary identity, compiler/SDK realization, Apple
device/model, AC/LPM/thermal/memory/disk gates, correctness outcomes, frozen
profile order/counts, timer counters/nesting, and lease receipt all reside in
the unavailable archive and are therefore not independently verified. Frozen
manifest expectations are not substituted for observed Phase-2 evidence.

## Raw counts and statistics

| Case | Method | Returned profiles B/C | Returned retained rows B/C | Whole/backref/DP/setup/steady/trace/materialize/downstream | Medians/shares/deltas/repeatability |
|---|---:|---:|---:|---|---|
| photo-large | 4 | 0/0 of 3/3 | 0/0 of 12/12 | N/A | N/A |
| photo-large | 6 | 0/0 of 3/3 | 0/0 of 12/12 | N/A | N/A |
| graphic-large | 4 | 0/0 of 3/3 | 0/0 of 12/12 | N/A | N/A |
| graphic-large | 6 | 0/0 of 3/3 | 0/0 of 12/12 | N/A | N/A |

Returned raw counts are: 0 correctness records, 0 counter records, 0 profile
records, 0 runner records of 120 planned, 0 stage records of 120 planned, 0
warmups of 24 planned, 0 retained rows of 96 planned, 0 accepted statistics,
and 0 external profiler samples. A zero remote pipeline exit is control-flow
evidence that the operator reached normal completion; it is not raw data and
does not authorize reconstructing the missing counts, order, values, or
statistics.

The Phase-2 transfer-cleanup and returned-index SHA-256 values are
`bb700155d68a55e91f5e6f90e6d420e346945f9e2e76e22eccc4fb339b3c1ae2`
and `b161d8b91ac32b3fceefdf83b2157d078cdb8124e3f1c7ca9e461c4052302564`.
The cleanup receipt hash is
`85fa98c4a8d28f278c7d0be2dd6f4682a3d1fc0ad277a5a88226d46379b03365`.

## Consequence and next action

No CPU stage can be ranked and no interval-search performance claim is
supported. If work continues, v5 must use wholly new build/compile/runtime
gates:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT`;
- `WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT=1`.

It must also use a new manifest/schema/evidence root/safe root/lease and retain
small independent operator, lease, archive-build, and cleanup receipts before
bulk transfer. Every exception path must derive lease state from a receipt
available independently of the bulk archive and preserve successful builder
and preliminary-transfer records. A no-workload rehearsal must naturally
exercise a representative bulk transfer within a justified frozen bound plus
success, refusal, and timeout/missing-artifact paths. This v4 cycle grants no
authority to implement or run v5.

Machine-readable criteria, null statistics, raw hashes/counts, validation, and
limitations are in
`evidence/backref-cost-attribution-v4-evaluation-20260819/phase3-audit.json`.

## Limitations

- No bulk archive or raw workload row returned; all performance quantities are
  N/A.
- The remote pipeline's zero exit supports normal operator completion but does
  not replace independently returned correctness, order, counter, resource,
  timer, lease, or archive evidence.
- The executor's `not-attempted` lease state and archive `not-attempted` status
  are stale initialized values after an uncaught transfer timeout, not reliable
  descriptions of remote activity.
- Source/tool admission and exact-child cleanup are verified; realized
  toolchain/device/resources and lease release are not.
- Coarse timers, even if they had returned, could not establish
  `PushInterval` self time, call-stack, code-layout, branch-predictor, or cache
  causality.
- Phase 3 ran only untimed local validation. It performed no remote command,
  encoder benchmark, retry, profiler, CUDA use, production promotion, host
  mutation, or process signaling.
