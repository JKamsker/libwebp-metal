# Backref Cost Aligned Null Stage Attribution V3 — Phase 3 Evaluation

## Decision

The graphic-large method 4 drift remains **unaccounted/inconclusive**. This is
not a fresh non-replication and not a stage localization. Phase 1B authority is
`NONE`, Phase 2 correctly refused all host contact and benchmark work, and
there are zero fresh V3 timing or stage rows and zero fresh pairs. The frozen
primary reproduction test therefore cannot be applied. No nested timing is
treated as causal, no threshold is changed, H is not interpreted, and
production promotion remains forbidden.

The transport question did advance: the sole fresh bounded requalification
completed all 365 request chunks and ACKs, including chunk 6, with 23,869,976
payload bytes and 23,934,714 wire bytes in one SSH session and no retry. That
rules in a successful fresh bounded transfer; it does not establish that V2's
five-ACK failure was a fluke or identify a deterministic defect.

The exact blocker is the immutable `alignment build frozen` gate. The rehearsal
timed binary was 653,712 bytes rather than the frozen 643,024 bytes, and its
binary, linker-map, linker-extract and instruction/codegen hashes differed.
The four addresses and section/body/padding geometry still matched, but partial
identity is not authority.

The sole future lead is a new independently gated Phase 1 that freezes a newly
generated Unix-make timed-binary/codegen identity and obtains exactly one fresh
fully hashed zero-workload rehearsal matching that identity byte-for-byte
before any later Phase 2 authority is reconsidered. It was not run.

## Exact ancestry and immutable handoffs

The independently verified chain is linear and exact:

1. main `92c3b59b2d178c5a03ec20b897252b358f07de81`, tree
   `6bf2a478b733d5e80ac2656448fe48c8c0964d9a`;
2. Phase 1A `3b81544df3305601e8c0817e554833f0824ad634`, parent main, tree
   `5e51c6925729f994dcc9987c583a9f1d02acb721`;
3. Phase 1B `b2bca487bdab0d996e03ee9def8dce1d11e7cd0e`, parent Phase 1A,
   tree `bd96b57638cfd2ae3fa4ae741aa9c5f5ca3bd4a9`;
4. Phase 2 `989ef333e4019807f3b8fd4f954078e681448f38`, parent Phase 1B,
   tree `8729d4d63ebf964bc678c950fdbb2b4bc9425ba8`.

Phase 1A changed 52 paths: 45 additions and seven modifications. Phase 1B is
exactly 30 additions, and Phase 2 is exactly two additions. Neither handoff
modified, deleted, or renamed an earlier path.

All 71 manifest-frozen artifacts and all 28 Phase 1B indexed rehearsal files
(644,419 bytes) independently match their recorded SHA-256 and sizes. The
source-admission map has 72 sorted entries, hash
`f62396024aaf3b7449212b3dc2dbdb0356eca6966f11d9bb6cbc6bbbda166e15`,
and zero current-file mismatches. The schema catalog has protocol version 1 and
49 unique entries; all 19 manifest schema IDs are present.

Key hashes are:

| Artifact | SHA-256 |
| --- | --- |
| Manifest | `c3067e6506fb642f6afac48f1ce1549875066ad7dbfdf4302fa55b620bcaf426` |
| Protocol | `e21257f4aa4f9e4f9f0a8bee35aafdacf0c8f6402a18a4565232d9368747fa6b` |
| Schema catalog | `0e2263476886040acfd4cabbfd8d85ebc104720205dd65f46c8b472ef7c2588a` |
| Transport source | `68f401540130cea715e4cd58c901592c0ddcda919d08dc53181cdf53bafdf1a1` |
| Phase 1B authority | `c769d839a484467959555785753b0d81d97351328e188974abb3c51ad10139b7` |
| Phase 2 machine audit | `64b82dc40560defb40680dd63159000b05a065a7d14923d255a13327aaea4e0c` |
| Phase 2 human audit | `e6577a7ed4e03ec38629fa60d2a622105ce9fc229d0f1bc2ace7a2c57df5dba4` |

## Transport comparison and fresh bounded requalification

The frozen transport comparison found no deterministic V2 source or
configuration regression. Alignment V3 completed 354/354 chunks and
23,193,668 request bytes; Alignment V4 completed 357/357 and 23,342,945 bytes;
Aligned Null V2 acknowledged 5/364 chunks and 327,680 of 23,820,500 bytes.
The one source difference identified in Alignment V3 affected only post-timeout
child-stop eligibility, not request writes, reads, ACKs, draining, scheduling,
or deadline extension.

The pre-run consequence was therefore frozen as `fresh-bounded-requalification`.
There were no timeout, chunk, buffer, retry, or connection-count changes.
Request chunks remained 65,536 bytes and the request-progress deadline remained
15 seconds.

Independent raw parsing of the V3 channel found 371 ordered frames: one READY,
366 request-ACK frames (one declaration plus 365 chunks), one request-complete,
one response declaration, one response chunk, and one response completion. All
frame sequence numbers and payload hashes pass.

The progress-chain JSON contains exactly 365 rows under a fixed cap of 512. For
every row, Phase 3 recomputed the raw ACK digest, prior-ACK link, ordinal, byte
range, cumulative bytes, remote receipt sequence, write/ACK timestamp order,
and ACK latency. There are zero chain, range, order, digest, sequence, or
timestamp failures. The last fully acknowledged chunk is 365 at cumulative
byte 23,869,976, with ACK digest
`16a26c38b9ee1efd367726a4f34f3eb8ef93b1e01813f3d20f058c91a8d46766`.
Observed ACK latency ranges from 46,666,542 to 154,921,833 ns and is transport
evidence only; it enters no performance statistic.

The complete raw counts are:

| Item | Count |
| --- | ---: |
| Rehearsal attempts / SSH sessions / retries | 1 / 1 / 0 |
| Request payload bytes | 23,869,976 |
| Request wire bytes | 23,934,714 |
| Request chunks written / acknowledged | 365 / 365 |
| Channel stdout / stderr bytes | 214,981 / 0 |
| Framed response bytes | 18,659 |
| Returned archive bytes | 14,265 |

The raw response independently parses as eight ordered frames. Its one archive
chunk hashes to
`9033f14cc8350fbcdc81eccdaf072b295f99d79189539812ede9553e6a2510ac`.
All ten tar members are regular evidence files and are byte-identical to the
persisted extracted files. Integrity is complete; the cleanup footer is final,
records removal of the exact validated transaction child, and proves absence.

## Source, toolchain, device, resource, process and lease evidence

The rehearsal source receipt identifies Phase 1A commit
`3b81544df3305601e8c0817e554833f0824ad634` and tree
`5e51c6925729f994dcc9987c583a9f1d02acb721`. Its repository-context bundle hash
is `394bb7e363c2ebebc6f4ee3211ba565656dbb66b5075c9750b4f3b7f1c32bef6`.
The compact and indexed 72-entry source receipts agree.

The frozen toolchain receipt is Xcode 26.3 with macOS SDK 26.2, eight required
executables, four metadata files, no `xcrun` dependency, and canonical identity
hash `5a64994e69486825c949aba78c4c688e546279f27137bd329d204c824a840adb`.
Payload and toolchain predecessor negatives were rejected by the independent
fixtures.

The zero-workload device was Mac16,10 / Apple M4 with 25,769,803,776 physical
bytes, 10,764,828,672 available memory bytes, and 18,921,299,968 available disk
bytes. It was on AC power, low-power mode was off, no thermal warning was
recorded, settings were unchanged, Metal was disabled, and CUDA workloads were
zero.

Process isolation is `verified`: discovered PID signals are zero, exact
identity conflicts are empty, argument text was not collected, and resolved
path APIs were not used. The lease was not attempted, no runner child or direct
child receipt exists, and the rehearsal invoked no timed binary. Operator exit
was zero; source admission, response/archive/index/integrity/extraction,
cleanup, and exact-child absence individually pass.

## Four-body B/L identity and local scientific gates

The canonical generated body list is exactly B/L PushInterval followed by B/L
DP. Expected and actual receipts are byte-identical, each SHA-256
`4f9462508d4f02b4e141d55d5944a2ba9778f3a98740520b4b4e8bb52c9a4951`.

| Ordinal | Variant | Role | Symbol | Address | Size |
| ---: | --- | --- | --- | --- | ---: |
| 0 | B | Push | `PushInterval` | `0000000100064000` | 508 |
| 1 | L | Push | `PushIntervalLayoutClone` | `0000000100068000` | 508 |
| 2 | B | DP | `BackwardReferencesHashChainDistanceOnly` | `000000010006c000` | 1,292 |
| 3 | L | DP | `BackwardReferencesHashChainDistanceOnlyLayoutClone` | `0000000100070000` | 1,292 |

All addresses are distinct and zero modulo 16,384. Inter-entry spacing is
16,384 bytes and DP-to-corresponding-Push displacement is 32,768 bytes. The
executable `__TEXT,__br_null_v3` section is 50,444 bytes; bodies total 3,600
bytes and padding totals 46,844 bytes. `-no_deduplicate` is present.
Corresponding B/L canonical instructions, instruction/branch/load/store
counts, mnemonics, and code sizes agree. Normalized semantic hash is
`8a434e0b87a4bfb63eaa95eb615d3ed2113b2a4f2949f7dc806b35ccaf57599b`;
normalized work hash is
`2191c66b70ce05335fe5138bf3ef938409ef0837b1c38934eb5e17ccf68eebb0`.
Append-hint and pop-tail counters are zero. H is absent.

Eight Phase 3 synthetic fixture suites passed without remote or benchmark
work. They rechecked six generated-domain negatives, thirteen receipt
negatives, the stale six-body identity, six payload predecessor identities,
six toolchain/xcrun predecessor identities, 27 transport failure cases,
process ownership, archive/extraction malicious cases, source admission,
single-session protocol order, and authority separation.

The frozen local evidence records two correctness encodes, 24 boundary encodes
under two sanitizer configurations, public API/ABI equality, default-build
omission, deterministic bitstreams and decoded pixels, immutable inputs,
transactional fallback, exact selector/body ownership, and a recorder-free
timed runner. The local runtime map is absent/B = B, L = L, while H and all
other values are invalid.

The whole-encode ledger has eight disjoint measured buckets plus explicit
residual. Seven nested timers are descriptive and non-additive. Both frozen
timer-accounting rows reconcile: 68 actual and expected clock reads, zero
residual, and zero reconciliation delta. The formula is
`2 + 2 * sum(all emitted stage calls)` using `mach_continuous_time`; five
early/fault/skip/repeat fixtures also obey it.

These local facts do not substitute for Phase 2 dynamic gates. Dynamic
correctness-before-timing, timer/accounting/reconciliation, online direct
serial child ownership, exclusive lease, and the timed pipeline are all
`NOT RUN / NOT ATTEMPTED` under authority `NONE`.

## Frozen build mismatch and Phase 2 refusal

Fourteen of fifteen Phase 1B gate outcomes pass. The sole failure is
`alignment build frozen`:

| Receipt | Frozen Phase 1A | Rehearsal |
| --- | --- | --- |
| Timed runner bytes | 643,024 | 653,712 |
| Timed runner SHA-256 | `262f23ba84c979fbb62d868f534feca20c428063aaab4804990f01311e04ae42` | `1ca731d0411a15eb2626e02adb7bca789a628f4d0d9c6c57e3fa4352a958a920` |
| Linker map bytes | 69,697 | 69,803 |
| Linker map SHA-256 | `cb7969b484a94b88781ed7fc74dad8caf0c8bbc559d8a35376b2e4ec3663e849` | `a057f30e69ddf0d0e9336142275b36c86952a89b1589d2007d5c4f422c4814b8` |
| Linker extract SHA-256 | `c03ddb8450a8c29d122aeda275cca60bec2dc86eab7c7ed0446b49a5fa34494b` | `22c341b93a3a2f32b8f0b3ea2b2bfff2a1cc6fb70c2fe8dc714e9f7cff52c791` |

Instruction-word and DP canonical hashes also differ across builds, even
though within each build B/L identity and all four geometry facts pass. The
10,688-byte binary-size delta and hash mismatches cannot be waived.

Phase 2 therefore made zero host contacts, SSH sessions, request declarations,
request chunks, request bytes, lease attempts, correctness encodes, timer
children, work rows, runner children, timed workloads, runner rows, stage rows,
timing rows, performance samples, profiler invocations, CUDA workloads,
retries, and reruns. It changed no code, protocol, threshold, or manifest.

## Zero statistical result and consequence

| Record | Frozen | Phase 2 observed |
| --- | ---: | ---: |
| Direct runner children | 59 | 0 |
| Correctness encodes | 16 | 0 |
| Clock children / reads | 1 / 4,096 | 0 / 0 |
| Timer-accounting children / rows | 2 / 2 | 0 / 0 |
| Untimed work rows | 8 | 0 |
| Profile processes | 32 | 0 |
| Excluded warmups | 32 | 0 |
| Retained timing rows | 128 | 0 |
| Runner rows | 160 | 0 |
| Stage rows | 160 | 0 |
| Fresh pairs per cell/metric | 16 | 0 |
| Bootstrap resamples per statistic | 100,000 | 0 executed |

No V1, V2, V4, or other prior row was loaded, pooled, reused, relabeled, or
ingested. Across four cells and 17 planned metrics there would have been 68
paired statistics, but zero are computable and no bootstrap was executed.

The primary graphic-m4 whole-encode decision requires 16 fresh valid pairs.
With zero pairs it can neither reproduce nor freshly fail to reproduce the
earlier drift. The exact decision is
`INCONCLUSIVE_REFUSED_AUTHORITY_NO_FRESH_REPRODUCTION_NO_STAGE_ATTRIBUTION`,
classified **unaccounted/inconclusive**.

Phase 3 did not push. No local origin ref exists for the V3 branch, no PR was
opened, and no CI status is known.
