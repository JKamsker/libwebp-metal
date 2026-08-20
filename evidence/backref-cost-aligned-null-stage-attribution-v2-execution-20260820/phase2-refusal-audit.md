# Phase 2 frozen executor/auditor refusal

Phase 2 is refused fail-closed for `BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V2`. The audited chain is exact main `fb297dd1097f6fc5a2f2d4d453da3c24b235d7d1` → Phase 1A `b9a26a196c65dc56e4c9eaac337c156568e855a5` → Phase 1B `d72feabc06cdd076ad858400bed8243991a185e7`, with exact trees and an additions-only Phase 1B delta of 8 added paths and 0 modifications/deletions/renames.

The frozen local/static design audits pass: expected and actual four-body receipts are byte-identical (`00a47a1e…`), with Push-B, Push-L, DP-B, DP-L, 16 KiB alignment/spacing, 32,768-byte DP-to-Push displacement, 3,600 body bytes, 46,844 padding bytes, and a 50,444-byte `__TEXT,__br_null_v2` section. The B/L-only inventory is 59 direct children, 16 correctness encodes, 32 warmups, 128 retained rows, 160 runner rows, 160 stage rows, 8 work rows, 16 pairs/statistic, and 100,000 bootstrap resamples. Local evidence records 44 PASS-labeled validation fields plus count fields, including default-off/API isolation, B/L semantics/work/codegen, recorder separation, selector/timer/ledger fixtures, CMake/Unix make, transport/admission/archive/process safety, negative matrices, and zero samples on gate failure.

The V4 premise is 11/12 domains passed; graphic-m4 whole mean was `-0.6199563389%` with CI `[-1.0795343105%, -0.2141217181%]`, while graphic-m4 DP-total and DP-steady nulls passed. The V1 premise is 13/14 gates passed, with only the stale six-body alignment-build-frozen gate failing and zero timing rows/samples. No V1/V4 rows were imported or reused.

The sole Phase 1B rehearsal reached READY once but stopped at 5/364 request chunks (`327,680/23,820,500` bytes), exited 1, returned no response archive, and supplied 21 missing success receipts plus the explicit cleanup state `unknown-after-refusal` with `remote_cleanup_absence_proved:false`. Its authorization is `REFUSED`, `phase_2_authority:NONE`, with zero workloads, leases, runner children, timing rows, retries, and reruns.

Phase 2 made zero SSH, host/device/runner/remote, ping, `nc`, benchmark, lease, cleanup, profiler, CUDA, archive/extraction, sample, or alternate/local timing contact. No Phase 3 evaluation was run. Decision: `REFUSED_ZERO_ACCEPTED_PERFORMANCE_EVIDENCE`.

Blocker: the incomplete rehearsal and absent exact-child cleanup/absence proof are immutable authority failures. One next credible lead is a future fresh Phase-1 owner producing a complete independently hashed rehearsal with response/integrity/cleanup-footer and exact-child absence proof; this Phase 2 audit must not retry or repair the transaction.

Machine-readable evidence: `phase2-refusal-audit.json`.
