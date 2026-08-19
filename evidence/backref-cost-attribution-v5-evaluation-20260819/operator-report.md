# Backref cost attribution V5 — Phase 3 independent evaluation

## Decision

This cycle is **unassessed**. It does not close or reopen the interval family,
does not rank a next CPU boundary, and does not authorize a production
promotion. No new bounded experiment was implemented or run. Any future
experiment would require wholly new independent gates and a verified
synchronous rehearsal receipt for its exact final handoff commit.

Phase 2 correctly failed closed before invoking the frozen command. Although
the manifest and local-validation record set `timed_execution_authorized=true`,
that authorization was expressly conditioned on a committed rehearsal receipt
whose `source_commit` equals the final Phase-1 commit
`54cfa24c563d4d8ba0cf4228be9b0161ee5140c1`. No such V5 receipt is present.
The manifest instead contains the non-commit placeholder
`runtime-verified-exact-handoff-commit`. Therefore the authorization condition
was false and no Phase-2 execution authority existed.

There are no raw V5 run rows. A reconstruction from the committed V5 execution
directory finds exactly two refusal-evidence files, zero JSONL files, zero
runner rows, zero stage rows, zero retained rows, and zero performance samples.
All requested medians, shares, deltas, and repeatability results are N/A. A
zero row count is not a zero duration.

## Identity and ancestry

The committed lineage is exact and linear from frozen main:

1. main `a192d9b8562b497b03bf8cc83c2de5c7a6ea8cae`, tree
   `df06cf4a9d045ece61f808c32cad4e33d0abed88`;
2. V5 design `e366a352bd2ab7739454e1664581f2e314415867`, parent main, tree
   `ac41529e0a207cb3c85f21eeb2a750119ca9b301`;
3. transport calibration `1656a52882c09d91d6d66c0c7ed864e7bc0f5ae6`, parent design,
   tree `0471f8194e00f7fbf9be533d3cb11c892ed0dad9`;
4. bounded chunk transfer `f98105c9d604b95698ac2b1fa2e0dd0a85c67b9c`, parent
   calibration, tree `ff6b8bf661e533f50141c8878e18731058323a01`;
5. Phase 1 `54cfa24c563d4d8ba0cf4228be9b0161ee5140c1`, parent bounded
   transfer, tree `539a056cf7cae861d518e209c088694287b62878`;
6. Phase 2 refusal `c240891fbf64b78fcec357dfb3b9634f5ccf70f0`, direct parent
   Phase 1, tree `282c4b5d61524405b6871234685a23701a0d425a`.

The Phase-1 freeze commit changed five files (54 insertions, 21 deletions).
The Phase-2 refusal commit changed only its two evidence files (334 insertions).
It did not alter any frozen source, protocol, manifest, schema, production, or
gate file.

Independently recomputed identities are:

- manifest SHA-256
  `31b6ccf9ae04bad1c7d716bbb4a05a24d7a943afcf281957619b253e41703090`;
- protocol SHA-256
  `840b807798569df4634d4c095dfc70744a5b4ca44bf0c1537815b4dcb6249cad`;
- schema catalog SHA-256
  `7e23d793575f4d3802cea9c5eda319e801175d5c262e4b6487d8f278ef908882`;
- Phase-1 validation SHA-256
  `ebdeaa2deb09cad64f89770edcd0d2de7b23821c77bb9a06e485ee5e90696cd5`;
- Phase-2 command/refusal transcript SHA-256
  `b7f3d563a2d048f5bb0ca741d7d1c984307a6589c02d5ba22ab4962c7cab41cc`;
- Phase-2 refusal JSON SHA-256
  `3587a84682b09d2580b2843d010eb5a00b3d46135a16418d730dd0659b17f019`.

All 26 manifest-frozen artifact hashes match, with zero mismatches.

## Frozen command, plan, and actual counts

The sole authorized Phase-2 command would have been:

```sh
env WEBP_BENCHMARK_SESSION=exclusive WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V5_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_attribution_v5.py run "$PWD/evidence/backref-cost-attribution-v5-execution-20260819"
```

At the Phase-1 handoff its expected commit expands to
`54cfa24c563d4d8ba0cf4228be9b0161ee5140c1`. The executor did not invoke the
wrapper, so there is no exit code, stdout, or stderr from that command and no
retry, rerun, rehearsal, tuning, alternate timing, profiler, CUDA, or fallback
attempt.

| Item | Frozen plan | Actual Phase 2 |
|---|---:|---:|
| frozen wrapper invocations | 1 if authorized | 0 |
| remote admissions | 1 if authorized | 0 |
| exclusive lease attempts | 1 if admitted | 0 |
| correctness encodes | 16 | 0 |
| direct counter-check encodes | 8 | 0 |
| serial profile processes | 24 | 0 |
| profile encodes including warmups | 120 | 0 |
| all encoder encodes | 144 | 0 |
| excluded warmups | 24 | 0 |
| retained runner rows | 96 | 0 |
| total runner rows | 120 | 0 |
| total stage rows | 120 | 0 |
| timing rows / performance samples | 96 | 0 |
| process signals | 0 | 0 |
| profiler or CUDA invocations | 0 | 0 |
| production promotions | 0 | 0 |

The frozen order reconstructs as photo-large before graphic-large, method 4
before method 6, and repetitions ordered baseline/candidate,
candidate/baseline, baseline/candidate. None of the 24 planned profile commands
executed.

For photo-large method 4, photo-large method 6, graphic-large method 4, and
graphic-large method 6, both baseline and candidate row counts are zero. Thus
whole encode, backward references, selected-DP total/setup/steady, traceback,
materialization, analyze, hash-chain, histogram, Huffman, and serialization
statistics are all N/A.

## Source, correctness, order, and timer audit

The V5 diagnostic has fresh default-off build, compile, and exact-value runtime
gates. The local truth table enables the candidate only for exact value `1`.
Predecessor experiment gates are mutually excluded, ordinary builds omit V5,
and public API/ABI checks pass.

Source inspection confirms that the selector is evaluated once before DP
mutation and a closed `if/else` calls exactly one baseline or specialized DP
body. The predecessor fallthrough chain is in the opposite preprocessor branch.
Thread-local counters separately record selector, baseline-body, and
candidate-body entries and support explicit zero reset.

The timer boundaries match the frozen contract: `dp_total` surrounds the sole
selected body through cleanup; `dp_setup` covers allocation through successful
`CostManagerInit`; `dp_steady` covers the initial literal and pixel DP loop;
traceback and materialization are separate. No timer is inside `PushInterval`
or another per-pixel helper. The runner enforces

`selected_dp_calls == selector_evaluations == dp_total.calls ==
dp_setup.calls == dp_steady.calls`,

with exactly the selected body nonzero, `setup + steady <= dp_total`, and
`dp_total + traceback + materialize <= lossless_backward_refs`.

Untimed final validation passed protocol, admission, archive, ownership,
experiment, and 25-guard tests. It performed 16 correctness encodes, four
case/method counter cells, two sanitizer configurations, and 16 boundary
fixtures. Baseline/candidate bitstreams and decoded RGB matched, repeats were
deterministic, inputs remained immutable, opposite-body calls were zero, and
counter reset returned zero. The 4,096-read monotonic clock check observed
1,465 positive deltas, 14 ns mean read delta, 41 ns minimum positive delta, and
167 ns maximum delta. These untimed checks establish local structural and
correctness properties only; they are not Phase-2 performance rows.

An ordinary Metal-disabled Release build with AppleClang
`17.0.0.17000604` produced `cwebp` and `dwebp`, and the lossless round-trip
smoke test passed. Local driver `validate` passed at Phase-2 commit with no
lease attempt and no timed binary invocation.

## Device, resources, ownership, and evidence return

The manifest freezes a target of Darwin arm64, Mac16,10 / Apple M4, 24 GiB,
Apple clang 17.0.0, and SDK 26.2. It also freezes one exclusive lease, AC power,
Low Power Mode off, no thermal warning, at least 4 GiB free memory, at least
8 GiB free disk, one serial directly owned child, and no discovered-PID
control. None of those realized remote source, toolchain, device, resource,
lease, correctness, process-order, or timer states was observed in Phase 2,
because refusal occurred before remote admission.

The Phase-1 record contains pre-final transport calibration claims, including a
4,230,194-byte representative transfer over nine 512 KiB ranges in 8.135333
seconds and derived 20-second per-range / 60-second total bounds. Those claims
do not constitute the missing exact-final-commit rehearsal receipt and were not
re-exercised here.

For Phase 2, control-plane receipts obtained are zero; archive builds and bulk
transfers attempted are zero; archive hash/size/inventory verifications are
zero; extractions attempted are zero; and cleanup attempts/receipts/absence
proofs are zero. This does not indicate failed cleanup: no remote exact child
was created by the executor, so cleanup is N/A and no remote absence claim is
made. Local archive tests independently passed safe inventory, hash,
all-or-nothing extraction, and malicious-member rejection contracts, but they
are not run-return receipts.

Process discovery was not performed in Phase 2. No pre-existing or discovered
PID was signaled, interrupted, killed, or otherwise touched. No host, runner,
service, authentication, permission, privacy, power, or toolchain state was
mutated.

## Consequence and limitations

V5 may be locally credible as a default-off diagnostic, but its timed objective
was never admitted. No evidence supports closing or reopening the interval
family, attributing photo/graphic behavior, or ranking any CPU boundary. Coarse
timers would in any case be unable to establish `PushInterval` self time,
call-stack, code-layout, branch-predictor, or cache causality.

The exact consequence is no production promotion and an unassessed interval
family. Any future experiment must be a new independently gated cycle with an
exact-final-commit rehearsal receipt; it must not be run as part of this Phase
3 evaluation.

The machine-readable reconstruction is in `phase3-audit.json`; untimed command
results are in `phase3-local-validation.json`.
