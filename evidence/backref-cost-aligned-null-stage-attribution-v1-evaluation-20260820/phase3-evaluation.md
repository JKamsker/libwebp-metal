# Backref Cost Aligned Null Stage Attribution V1 — Phase 3 Evaluation

## Decision

The fresh graphic-large method 4 whole-encode reproduction test is
**unavailable/inconclusive**, not a non-replication. Phase 2 correctly made zero
host contact because Phase 1B authority was `NONE`, so V1 has zero retained
timing rows and zero fresh pairs. There is no causal stage attribution, no
inference from overlapping nested timers, no H interpretation, and no
production promotion.

The cycle is blocked by the frozen `alignment build frozen` gate. That gate
retained predecessor six-body expectations despite a valid V1 four-body
receipt. The stale gate requires six distinct private addresses and
section/body/padding sizes `83,212/5,624/77,588` bytes; the valid V1 receipt has
four distinct 16-KiB-aligned bodies and `50,444/3,600/46,844` bytes. Fail-closed
authority `NONE` was therefore mandatory.

The sole research-only next lead is a fresh, independently gated Phase 1
refreeze correcting that frozen alignment-build identity/expectation mismatch
before any timing execution. It was not run.

## Provenance and frozen identities

The exact linear chain is:

1. main `5de7b3848adfdb5d1058a061979535f05f976e5b`, tree
   `a5b2e958b3e89d3e1bf5fd5ecd6f92b2bc9622e6`;
2. Phase 1A `c674c815c65d0424f75f8391e09064da4364d04e`, whose sole parent is
   main and whose tree is `0974b8310e69ce1e1a9a0bfa1ed8eecc1b037239`;
3. Phase 1B `75ba4d7f001307becee11828f321f9f041ad64a6`, whose sole parent is
   Phase 1A and whose tree is `a782f65b147073f45596b485c9c2ca5bfff904d0`;
4. Phase 2 `1bc8222e0fadcce6e446c3579762f895c6e49f85`, whose sole parent is
   Phase 1B and whose tree is `0b322e31c5720898b22ad5a7cc01dfd4a8693af3`.

Phase 1A changed 46 files relative to main: 39 additions and 7
modifications. Phase 1B added 29 files and changed no Phase 1A file. Phase 2
added its two refusal-audit files and changed no earlier file.

Independent SHA-256 verification passed for all 65 manifest-frozen artifacts,
all 27 Phase 1B indexed rehearsal files (364,350 bytes), both nested indexes
(9/9 and 25/25 files), and all 66 source-admission map entries. There were zero
hash or size mismatches. The principal identities are:

| Identity | SHA-256 |
| --- | --- |
| Frozen manifest | `b38602331821dc2e6f17d1aa82e974891697109e9d9011c724173bf55ae26439` |
| Protocol | `4dc75a93005fba3a85ccb8eb353ad9c944d379d9603d9c0a75b05fde4033196d` |
| Schema catalog | `e32aea4c674690431b470944476efe9abce959fe89d3d5e02f618246a10b7156` |
| Phase 1B authority | `83c2bd6a30921090448bf20e8e77b3b2b04c0b3367cf475e17cdabcf5c9669df` |
| Phase 2 machine audit | `4e40a51313d44ae6eb6323777d23e367b019f8723934b361f3bb33dab3d47005` |
| Phase 2 human audit | `a16bb30d900b5402c583235807f383949ec8598e5b18e08b250b657e9d2d61fa` |

The frozen schema catalog has 45 distinct entries at protocol version 1. The
32-row rehearsal profile plan has contiguous ordinals 0–31 and exactly matches
the frozen case/method/repetition order: photo then graphic; method 4 then 6;
and `B,L`, `L,B`, `B,L`, `L,B` across repetitions 0–3. That plan is a static
plan, not executed timing evidence.

## Premise and candidate audit

The V4 premise reconstructs exactly as 11 of 12 cell-by-metric domains passing.
The sole failure was graphic-m4 whole encode: mean
`-0.6199563389094708%`, paired-bootstrap 95% CI
`[-1.0795343104954225%, -0.21412171812593112%]`; graphic-m4 DP total and DP
steady passed. V4 supplied no complete mutually exclusive whole-encode ledger,
so its nested/overlapping timers are unsuitable for causal attribution. Phase 3
loaded zero V4 timing rows into V1 statistics and did not pool, reuse, relabel,
or substitute any V4 sample.

The static B/L candidate evidence passes. There is no H body. Push B/L and DP
B/L are four distinct symbols, all entry addresses are zero modulo 16,384,
with 16,384-byte entry spacing and 32,768-byte corresponding DP-to-Push
displacement. Corresponding canonical instructions and branch/load/store counts
match, linker deduplication is disabled, and the timed binary is recorder-free.
The frozen Phase 1 validation also records public API/ABI equality, ordinary
default omission, CMake and Unix-make integration, 45 mutual-exclusion guards,
the exact runtime truth table, selector-before-mutation, fallback,
determinism, immutability, two local correctness encodes, 24 sanitizer boundary
encodes, two timer-accounting fixture rows, and five early/fault/skip/repeat
fixtures as passing.

These are static/local and rehearsal facts. Dynamic B/L work-counter,
bitstream, decoded-pixel, and correctness equality is unavailable because
Phase 2 produced zero work and correctness rows.

## Frozen versus observed inventory

| Record or action | Frozen | Phase 2 observed |
| --- | ---: | ---: |
| Direct runner children | 59 | 0 |
| Correctness children/encodes | 16 | 0 |
| Clock-overhead children | 1 | 0 |
| Clock-overhead reads | 4,096 | 0 |
| Timer-accounting children/rows | 2 / 2 | 0 / 0 |
| Untimed work rows | 8 | 0 |
| Profile processes | 32 | 0 |
| Excluded warmups | 32 | 0 |
| Retained timing rows | 128 | 0 |
| Total runner rows | 160 | 0 |
| Total stage rows | 160 | 0 |
| Retained stage rows | 128 | 0 |
| Fresh paired rows per cell/metric | 16 | 0 |
| Bootstrap resamples per statistic | 100,000 | 0 executed |

The frozen 59-child breakdown is 16 correctness, one clock, two timer
accounting, eight work, and 32 profile children. All were required to be direct,
strictly serial children under one exclusive lease. No Phase 2 child or child
receipt exists, so dynamic correctness, timer/accounting/reconciliation, and
online serial-ownership gates are `NOT RUN / UNAVAILABLE`, not passes. The
zero-sample-on-gate-failure rule passed.

## Ledger and unavailable statistics

The frozen outer interval begins at `WebPProfileBeginSession` at the start of
`WebPEncodeInternal` and ends at `WebPProfileEndSession` on every instrumented
exit. It uses coarse `mach_continuous_time` boundaries. The eight measured
top-level buckets are mutually exclusive; residual is whole minus their sum.
Successful retained rows require residual exactly zero and
`clock_reads == 2 + 2 * sum(all emitted stage calls)`. The independently
measured 4,096-read distribution supplies a p99 overhead bound; raw rows are
not post-hoc fitted. Nested timers are descriptive and non-additive.

No dynamic ledger row exists. Therefore every requested statistic below has
pair count 0, mean/median/delta/CI/share/repeatability unavailable, and the same
exact reason: Phase 2 had authority `NONE` and produced zero fresh V1 retained
rows.

| Kind | Field | Phase 3 result |
| --- | --- | --- |
| Outer | `whole_encode` | unavailable/inconclusive |
| Top level | `pre_lossless_setup_input` | unavailable |
| Top level | `analysis_transforms` | unavailable |
| Top level | `backward_reference_generation` | unavailable |
| Top level | `histogram_construction` | unavailable |
| Top level | `entropy_huffman_preparation` | unavailable |
| Top level | `bitstream_serialization` | unavailable |
| Top level | `container_output_finalization` | unavailable |
| Top level | `allocation_cleanup_orchestration` | unavailable |
| Residual | `residual_unattributed` | unavailable |
| Nested, non-additive | `lossless_analyze` | unavailable |
| Nested, non-additive | `lossless_hash_chain` | unavailable |
| Nested, non-additive | `lossless_backward_refs` | unavailable |
| Nested, non-additive | `lossless_histogram` | unavailable |
| Nested, non-additive | `lossless_huffman` | unavailable |
| Nested, non-additive | `lossless_bitstream` | unavailable |
| Nested, non-additive | `backref_cost_dp_total` | unavailable |
| Nested, non-additive | `backref_cost_dp_setup` | unavailable |
| Nested, non-additive | `backref_cost_dp_steady` | unavailable |
| Nested, non-additive | `backref_cost_traceback` | unavailable |
| Nested, non-additive | `backref_cost_materialize` | unavailable |

There were zero raw V1 timing files, timing rows, stage rows, work rows,
correctness rows, direct-child receipts, fresh pairs, recomputable paired
statistics, or executed bootstrap resamples in Phase 2.

## Device, resource, transport, archive, and cleanup distinction

The sole Phase 1 rehearsal remains reference-only. It used one SSH session and
one attempt, exited 0, acknowledged 23,673,635 request bytes in 362/362 chunks,
returned 18,240 framed-response bytes and a 13,846-byte accepted archive, and
had zero stderr. Its receipts identify Apple M4 / Mac16,10, AC power, low-power
mode off, no thermal warning, 10,699,292,672 available memory bytes, and
18,937,614,336 available disk bytes. Process isolation passed with zero signals
to discovered PIDs and zero exact identity conflicts; source admission,
integrity, indexed extraction, exact-child cleanup, and absence passed. It made
zero lease attempts and ran zero runner, encoder, timer, or profiler workloads.

Phase 2 performed zero remote or external host commands: zero SSH/READY,
lease acquisition or release, transaction, child, device/resource/process
checks, archive creation/extraction/integrity checks, cleanup, and absence
proofs. Those Phase 2 run-specific states are unavailable by correct
fail-closed refusal; no rehearsal fact is relabeled as a dynamic Phase 2 fact.

## Frozen decision tree

The primary graphic-m4 whole-encode reproduction test comes first and requires
16 fresh pairs. Its unchanged bounds are absolute mean at most 0.75%, a 95% CI
containing zero with endpoints inside ±1.50%, and every pair inside ±3.00%.
With zero fresh pairs, the test cannot pass or fail and is
`UNAVAILABLE_INCONCLUSIVE`. It is explicitly not classified as “V4 failure not
replicated.”

Because reproduction itself is unavailable, the attribution branch is not
entered. No nine-bucket Bonferroni test, direction-consistency test, effect or
whole-delta-fraction test, accounting gate, or repeatability gate can be
applied. The research consequence is therefore
`UNACCOUNTED_INCONCLUSIVE_WITHOUT_EXECUTION`, with no stage localization and no
production consequence.
