# Backref cost attribution V7 — Phase 3 independent consequence report

## Decision

This cycle is **unassessed**. It neither closes nor reopens the interval
family, does not select or run a new bounded experiment, does not rank a next
CPU stage, and does not authorize production promotion. No V7 timed rows
exist. Every requested performance median, share, delta, and repeatability
result is therefore N/A; an empty raw-row set is not a zero-duration result.

The sole permitted Phase-1 rehearsal used one noninteractive SSH transaction
and successfully returned source admission, a structurally complete framed
control/bulk stream, and the final same-session exact-child cleanup and absence
footer. The operator nevertheless refused before corpus generation, runner
build, representative-payload admission, lease acquisition, or any encoder or
profiler workload. Its observe-only process guard matched the ancestor
transport command itself because that command embeds the frozen source text
containing `_experiment_runner`. Phase 1B consequently records
`authorization_status=REFUSED`, `timed_execution_authorized=false`, and
`phase_2_authority=NONE`.

Phase 2 invoked the exact frozen command once. Local authority validation
failed closed on the first absent successful-rehearsal receipt,
`return-protocol/source-admission.json`, before constructing or starting an SSH
transport. It made no lease, workload, cleanup, profiler, CUDA, retry, rerun,
fallback, or signal attempt.

Production disposition is an explicit **NO-GO**. V7 remains default-off and
diagnostic-only; no evidence from this cycle supports promotion.

## Evidence inventory and raw-stat reconstruction

The complete committed V7 evidence inventory before this evaluation contains
eight files totaling 48,311 bytes:

| Evidence | Bytes | Consequence |
|---|---:|---|
| `phase1-local-validation.json` | 2,635 | frozen local design validation; not a timed sample |
| `phase1b-authorization.json` | 3,219 | explicit refusal and no Phase-2 authority |
| `phase1b-rehearsal-hashes.json` | 594 | complete index of three raw rehearsal files |
| `rehearsal-invocation.json` | 2,513 | one remote rehearsal; zero workloads; verified in-session cleanup |
| `return-protocol/framed-stdout.bin` | 31,671 | raw eight-frame refusal stream with a 24,145-byte archive |
| `return-protocol/transport-stderr.bin` | 0 | empty transport stderr |
| `phase2-command-and-refusal.txt` | 2,313 | exact command and first local failure |
| `phase2-refusal-observation.json` | 5,366 | Phase-2 authority and safety reconstruction |

There are no V7 JSONL runner or stage files, retained rows, warmups, timed
commands, correctness receipts from Phase 2, timer-accounting receipts from
Phase 2, lease receipts, build identities from Phase 2, or performance
samples. Older experiment rows were not pooled, relabeled, or reused.

For each of photo-large/method 4, photo-large/method 6,
graphic-large/method 4, and graphic-large/method 6, baseline and candidate raw
row counts are both zero. Whole encode, backward-reference generation,
selected-DP total/setup/steady, traceback, materialization, histogram,
Huffman, and bitstream/downstream values are all N/A. Shares,
baseline-to-candidate deltas, medians, and repeatability are also N/A.

## Ancestry and immutable identity

The independently resolved pre-evaluation lineage is exact and linear:

1. frozen main `567e48ddfeacfaa65fb11a1611fba7aa7f5590a5`, tree
   `4b87a36bf671fe05789c81b3fac1580cc6aba2c6`;
2. Phase 1A `7ad55d44e5a78f3b8ef197c2a26cd4c78dd7bbba`, direct parent main,
   tree `3e6fde30702fefe9c01432255263efc1760d0980`;
3. Phase 1B `193bc6bee12acfc2140799d90b58f1f6bc79bb89`, direct parent Phase 1A,
   tree `8aa3d6c58b5e557021f9935185fe751018cad483`;
4. Phase 2 refusal `ff9d7b4fc9692853dab11d61458e9d0fd27a483a`, direct parent Phase 1B,
   tree `1a2938106e454be5751f43cb2e41cac577c05e00`.

Phase 1A changed 25 files (4,545 insertions, 24 deletions). Phase 1B added
exactly five files (120 insertion lines) under the predeclared rehearsal,
hash-index, and authorization-envelope locations. It modified no Phase-1A
artifact. Phase 2 added exactly two refusal-evidence files (215 insertion
lines) and modified neither Phase-1 frozen artifact nor rehearsal evidence.

The immutable set is the manifest plus its 27 enumerated frozen artifacts: 28
artifacts total. All 28 are byte-identical at Phase 1A, Phase 1B, Phase 2, and
this evaluation's pre-report source state. All recomputed SHA-256 values match
the manifest declarations. Core identities are:

- manifest `3b888a952009fe0e8b3c82379b7128f7c7d6574b4ebfae4b6cd5dde87cf8117e`;
- protocol `49e0fe6c9612c8ec5e1170b1e93c5e6d01ce5bfff42e4860427c1a78218edc04`;
- schema catalog `9c6244495556d5a3865fdd6723d58949d391efe636aaac3a3a3444c176d31bb7`;
- transport `ef8b8d4429da42528d40652b7cd67afe3d6fce8bd93f2f12360a094221e97da0`;
- Phase-1 local validation `354967a6ec49a8b357304f45e5638b28e83d47aad9477fbcbce2a94ecf0d4bb3`;
- Phase-1B hash index `08460cc31852bd93ea5130e909af78a447c838518bf6e3b80983516eded7c61c`;
- raw framed stdout `c27491f8341bf6981d1f6460ae3c7be7b81bd6844ecb25dee5ee3131b42fcbd8`.

## Semantics, order, counts, and timers

Source inspection and untimed tests confirm independent default-off V7 build,
compile, and exact-value runtime gates. The candidate activates only with
`WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT=1`; predecessor gates are
isolated, ordinary objects/targets/symbols/strings omit V7, and local public
API/ABI surfaces match.

The specialized `PushInterval` body remains semantically identical to frozen
`673bc3fa`. The selector is evaluated once before DP mutation, and one closed
baseline/candidate `if/else` invokes exactly one DP body. The predecessor
fallthrough path is excluded. Local tests observed only the selected body,
equal encoded bytes and decoded pixels, immutable inputs, deterministic output,
and explicit counter reset. Integer costs, strict comparisons, ties, update
order, traceback/reference/cache order, and transactional fallback remain
unchanged.

Timer boundaries match the frozen contract: `dp_total` surrounds exactly one
selected DP call through cleanup; setup runs from before allocation through
successful `CostManagerInit`; steady contains only the initial literal and
pixel loop; traceback and materialization are separately timed; and no clock
is placed in `PushInterval`, insertion, or another per-pixel helper. The
required accounting invariant remains selected body/selector/DP
total/setup/steady call equality, `setup+steady <= dp_total`, and
`dp_total+traceback+materialize <= backward_refs`.

The frozen plan is photo-large then graphic-large, method 4 then method 6,
with three paired repetitions ordered baseline/candidate,
candidate/baseline, baseline/candidate. It permits exactly 24 serial direct
profile processes, 24 excluded warmups, 96 retained rows, and 120 total runner
and stage rows, after 16 correctness encodes. Actual Phase-2 counts for every
item are zero. No planned order or count was realized.

The Phase-3 local timer check read `mach_continuous_time` 4,096 times and
passed monotonicity with 14 ns mean consecutive-read delta and 83 ns maximum
delta. This validates clock mechanics only and is not case/method timing.

## Source, toolchain, device, resources, ownership, and return

The rehearsal's source-admission frame verifies exact Phase-1A commit/tree, a
clean repository-context bundle, all frozen source hashes, and removal of the
temporary verification repository. The returned diagnostic-admission artifact
records Apple clang 17.0.0, target arm64 Darwin 25.2.0, SDK 26.2, the frozen
Xcode developer directory, and exact `clang`, `nm`, and `xcrun` hashes. The
operator reached its resource process guard only after the frozen hardware,
memory, disk, AC-power, Low-Power-Mode, thermal, toolchain, and diagnostic
checks had passed. Because the guard raised before `resource-admission` was
written, exact observed free-memory/disk values and a completed device/resource
receipt are unavailable. Corpus generation, runner build, symbol validation,
timer validation, and command construction were not reached remotely.

Ownership remains safe. Process discovery was observe-only. The rehearsal
reported zero discovered-PID signals, no lease attempt, no encoder/profiler
workload, one directly owned noninteractive SSH transaction, and zero
post-run SSH/SCP cleanup operations. Phase 2 started no remote transaction and
created no remote child; accordingly it made no Phase-2 cleanup or absence
claim.

Offline parsing of the raw rehearsal stream found exactly these ordered frame
kinds: source admission, operator status, archive build, lease state, bulk
declaration, one bulk chunk, integrity footer, and cleanup footer. Frame
payload hashes, sequence, declared archive size/hash/chunk count, five-member
inventory, embedded four-artifact hash index, and all indexed member hashes
recompute exactly. The integrity/operator state is `refused`, not success.
Lease state is correctly `not-attempted`.

The cleanup footer is the final frame. It reports `status=complete`, removal
of the exact validated V7 child, and an absence proof after 10,843,368,416 ns.
This proves the rehearsal's same-session cleanup. No second remote cleanup was
used. The representative 5 MiB calibration payload was never admitted, so the
observed margin is zero; the 24,145-byte refusal archive and nominal 2,226
bytes/s transaction rate are refusal-transport observations only and cannot
validate capacity for a timed archive.

Local archive fixtures pass safe-member validation, normalized inventory,
declared size/hash checks, all-or-nothing extraction, corruption rejection,
and no-partial-extraction behavior. The raw archive itself was audited
read-only in memory; no remote or prior-cycle path was contacted or inspected.

## Local Phase-3 validation and consequence

Untimed local protocol, admission, archive, ownership, all 27 experiment-guard,
correctness, counter, sanitizer, boundary, API/ABI, omission, runtime-truth,
and timer suites pass. The executor's local `validate` command refuses with
exit 1 because the successful-rehearsal `source-admission.json` receipt is
absent. This confirms the authority gate remains fail-closed without remote
contact or a timed invocation.

The final consequence is: **interval family unassessed; no next CPU-stage
ranking; no new bounded experiment; no production promotion**. Any future
proposal would require new authority and is neither selected nor run here.

The machine-readable reconstruction is in `phase3-audit.json`; untimed command
outcomes are in `phase3-local-validation.json`.
