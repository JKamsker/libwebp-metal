# Frozen Backref Cost Aligned Null Stage Attribution V4 protocol

## Authority and premise

Phase 1 starts from exact merged main
`92c3b59b2d178c5a03ec20b897252b358f07de81`. It designs, validates,
freezes, and performs one untimed zero-workload/zero-lease rehearsal. It
generates no timing sample. Phase 2 has no authority unless the additions-only
Phase 1B envelope grants
`ALIGNED_NULL_STAGE_ATTRIBUTION_V4_CONDITIONAL_DIAGNOSTIC_AUTHORITY`.

The committed Alignment V4 evidence is premise only. Its raw indexes and
evaluator reconstruction are audited without importing rows into V4. Eleven of
twelve B-to-L cell/metric domains passed. The sole failure was graphic-large,
method 4, whole encode: mean `-0.6199563389094708%`, paired-bootstrap 95% CI
`[-1.0795343104954225%, -0.21412171812593112%]`. Graphic-m4 DP total and DP
steady passed. V4 timers are nested descriptive intervals and do not form a
complete attribution ledger. V4 never pools, relabels, or reuses a V4 sample.

The transport premise is independently frozen before remote contact.
Successful Alignment V4/V4 rehearsals transferred 23,193,668 bytes in 354
chunks and 23,342,945 bytes in 357 chunks. Aligned Null V2 authenticated READY
and accepted its 23,820,500-byte/364-chunk declaration but acknowledged only
five chunks (327,680 bytes) before the unchanged 15-second progress deadline.
After identity normalization, all three historical engines have identical
client pump, validator, remote scheduling, stdout/stderr drain, ACK order,
deadlines, and cleanup/finally source. Therefore no deterministic V2 source or
configuration regression is established. The pre-run consequence is frozen as
fresh bounded requalification: no timeout, chunk, buffer, retry, or connection
limit changes and no claim that V2 was a fluke.

## Candidate and isolation

V4 is independently compile- and runtime-gated by
`WEBP_BUILD_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_EXPERIMENT` and
`WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_VARIANT`. Both default
off. The only accepted runtime values are `B` and `L`; absent selects B inside
the private build, and `H` or any other value fails closed. Every other
backref-cost experiment is mutually exclusive.

B is the aligned original baseline DP/PushInterval body. L is a separately
named exact source clone. The four private entries are in
`__TEXT,__br_null_v4`, each aligned to 16,384 bytes, in order Push-B, Push-L,
DP-B, DP-L. Corresponding DP-to-Push displacement is 32,768 bytes. The linker
uses `-Wl,-no_deduplicate`. The freeze records map, section, body, padding, and
binary bytes; entry modulo 16,384; distinct addresses; normalized instruction,
branch, load, store, and body-size equality. No V4 H body, append-hint
interpretation, threshold/policy change, or production candidate exists.

The selector is evaluated exactly once before `dist_array` mutation. A closed
two-case switch invokes exactly one noinline body. Public API/ABI, integer and
strict-tie semantics, update/reference order, traceback, bitstream, decoded
pixels, deterministic repeats, immutable input, allocation failure, and
transactional fallback remain unchanged.

The optimized timed runner contains no recorder symbols. A separately built,
separately hashed untimed recorder binary records selector/body/work counters.
Eight work rows are required: photo/graphic x method 4/6 x B/L. Every algorithm
and bitstream field must match B/L, only the selected body count may differ,
and all append-hint/pop-tail fields must remain zero.

## Complete whole-encode ledger

The acceptance outer interval is exactly the existing interval from the
`WebPProfileBeginSession(config, pic)` clock read at
`src/enc/webp_enc.c:355`, the start of `WebPEncodeInternal`, through the one
`WebPProfileEndSession` clock read on each possible instrumented exit at lines
370, 387, 405, 442, or 457. V4 uses
`mach_continuous_time` converted by `mach_timebase_info`. There is no sampling
profiler and no per-pixel, per-symbol, or PushInterval clock.

At each stage begin or end, one clock read first assigns the elapsed interval
since the previous read to the stage on top of a strict LIFO stack, or to
orchestration when the stack is empty. The stage transition is then applied.
The final read assigns the last interval. Consequently every nanosecond in the
outer interval belongs to exactly one top-level bucket. Existing elapsed stage
timers are retained in a separate nested object and are never summed with the
top-level ledger.

| Frozen top-level bucket | Exact begin/end sites | Nesting and inclusion/exclusion | Successful-path calls | Downstream consumer |
| --- | --- | --- | --- | --- |
| `pre_lossless_setup_input` | `webp_enc.c:438/441,452` prepare; `vp8l_enc.c:1928/1930,1953,1961,1965` container; `1773/1775,1779` init; `1614/1617,1623,1628,1636` palette; `1642/1644,1647` input copy | Top-level mapping; includes setup/input work inside those intervals; excludes empty-stack allocation/free gaps | prepare/container/init normally 1; palette/input copy 0..N | attribution |
| `analysis_transforms` | `vp8l_enc.c:1765/1768,1772` analyze; `1655/1657`, `1661/1667,1670`, `1676/1681,1684` transforms | Top-level mapping; includes analyze/subtract-green/predictor/cross-color only | analyze normally 1; transforms 0..N | attribution |
| `backward_reference_generation` | `vp8l_enc.c:774/777,780`, `781/787,790`, `906/909,912`, `936/941,944`; nested DP sites below | Top-level mapping; includes hash/backref and all nested DP/trace/materialize time; nested values are descriptive and never added | hash/backref 1..N | attribution |
| `histogram_construction` | `vp8l_enc.c:800/804` and `967/972,975` | Top-level mapping; histogram intervals only | 1..N | attribution |
| `entropy_huffman_preparation` | `vp8l_enc.c:807/810,838`, `977/987,991`, `1035/1056` | Top-level mapping; Huffman/entropy preparation only | 1..N | attribution |
| `bitstream_serialization` | `vp8l_enc.c:841/844,847` and `1059/1062,1065` | Top-level mapping around image serialization; excludes final container/RIFF writes | 1..N | attribution |
| `container_output_finalization` | `vp8l_enc.c:1894/1898` stream finalize and `1975/1977,1980` RIFF write | Top-level mapping; includes output finalization only | stream finalize 1; RIFF 0..1 | attribution |
| `allocation_cleanup_orchestration` | Every gap between outer lines 355 and 370/387/405/442/457 while the stack is empty | Completes the partition; includes allocations, frees, progress, errors, and orchestration outside mapped intervals; excludes every named stage | one accumulated bucket composed of 1..N gaps | attribution |
| `residual_unattributed` | `profile_enc.c` final `whole_ns - sum(eight buckets)` after the selected outer end | Computed, never timed or nested; excluded from the eight-bucket sum | exactly 1 | accounting first; attribution only after reproduction |

Nested descriptive timers are:

| Timer | Exact begin/end sites | Nesting/inclusion and exclusion | Successful-path calls | Downstream consumer |
| --- | --- | --- | --- | --- |
| `lossless_hash_chain` | `vp8l_enc.c:774/777,780` and `906/909,912` around `VP8LHashChainFill` | Child of top-level backref; excludes backward-ref calls; non-additive | positive, method/content dependent | descriptive audit |
| `lossless_backward_refs` | `vp8l_enc.c:781/787,790` and `936/941,944` around `VP8LGetBackwardReferences` | Child of top-level backref and parent of DP/trace/materialize | positive | parent consistency gate |
| `backref_cost_dp_total` | `backward_references_cost_enc.c:2243/2271` around the one selected B/L body (predecessor-only guarded sites at 1957..2221 are compiled out for V4) | Child of backward refs; parent of setup/steady; excludes traceback/materialization | equals setup and steady calls, positive | parent/child gate and descriptive report |
| `backref_cost_dp_setup` | `backward_references_cost_distance_only_enc.inc:30/47` from allocation through successful `CostManagerInit` | Child of DP total; excludes pixel loop | equals DP total calls | parent/child gate and descriptive report |
| `backref_cost_dp_steady` | `backward_references_cost_distance_only_enc.inc:52/104` around initial literal and pixel DP loop | Child of DP total; excludes setup | equals DP total calls | parent/child gate and descriptive report |
| `backref_cost_traceback` | `backward_references_cost_enc.c:2382/2385` around `TraceBackwards` | Child of backward refs, outside DP total/materialization | positive when DP succeeds | parent/child gate and descriptive report |
| `backref_cost_materialize` | `backward_references_cost_enc.c:2389/2393,2397` around chosen-path materialization | Child of backward refs, outside DP total/traceback | positive when DP succeeds | parent/child gate and descriptive report |

The ledger fails closed for a non-LIFO end, stack overflow/underflow, missing
close, backward clock, negative residual, ledger sum exceeding whole, nonzero
residual, missing required successful-path timer, duplicate/unexpected stage,
inconsistent DP parent/child totals, or unexpected clock count. Clock count is
not fitted from results: it must equal `2 + 2 * sum(all emitted stage calls)`
(outer begin/end plus one read at every nested begin/end). Successful retained
rows require residual exactly zero. Early return, allocation failure, empty and
tiny input, method 4/6, and legitimate skip/repeat fixtures use the same rule;
optional stages may be zero, repeated image-attempt stages may be N, and every
opened stage must close before the outer end.

Clock overhead is measured independently by one untimed 4,096-read child,
reporting all-read mean, minimum positive, p50, p95, p99, and maximum
consecutive-read deltas. Rows are raw and uncorrected. Their conservative
overhead bound is `clock_reads * measured p99 consecutive-read delta`; no
post-hoc correction or fit is permitted. The exact transition construction
still requires arithmetic reconciliation to zero.

## Frozen fresh inventory

Required controls are photo-large and graphic-large, methods 4 and 6. The
predeclared primary cell is graphic-large method 4. A process imports once,
runs one excluded warmup, retains four encodes, and exits. Four repetitions are
used because B/L requires an even repetition count for exact position balance
and four gives 16 pairs, at least V4's 12, without adaptive stopping. Orders
are `B,L`, `L,B`, `B,L`, `L,B`; each variant appears first and second twice.

If authorized, exact counts are 32 profile direct children, 32 warmups, 128
retained rows, 160 runner rows, and 160 stage rows. Before timing there are 16
correctness encodes, one clock child, two timer-ledger validation encodes, and
eight work rows. Total direct runner children are 59. Everything is strictly
serial under one exclusive lease.

Each cell has 16 paired B-to-L percentages. Every statistic reports raw pairs,
mean, median, sample standard deviation, min/max, signs, mean nanosecond delta,
and deterministic paired-bootstrap intervals with 100,000 resamples and base
seed `0x4e554c33`. There is no adaptive stopping.

## Frozen reproduction and attribution decision

The primary reproduction test applies unchanged V4 null bounds to fresh
graphic-m4 whole encode: absolute mean <=0.75%, 95% CI contains zero, CI
endpoints within +/-1.50%, and every pair within +/-3.00%. If all pass, the V4
whole failure is `not replicated`; no stage cause may be claimed. If any fails,
the drift is `reproduced` and only then may attribution be considered.

Attribution requires valid accounting and repeatability (four-repetition whole
median ratio <=2.0 and every top-level stage-share range <0.10). Nine
top-level/residual buckets receive Bonferroni-adjusted intervals controlling a
95% family-wise error rate. A bucket qualifies only if all are true:

- mean nanosecond delta has the same sign as whole;
- adjusted interval excludes zero;
- absolute mean percentage is at least 0.20%;
- absolute mean bucket delta is at least 20% of absolute mean whole delta;
- at least three of four repetition mean deltas have the whole direction.

Multiplicity is across the frozen nine buckets only. Controls cannot fit a
threshold. If whole reproduces but no bucket qualifies, or accounting or
repeatability fails, the result is `unaccounted/inconclusive`. Overlapping
nested timers are reported descriptively and never used as additive causal
evidence. H and production benefit are forbidden under every outcome.

## Remote transaction and process safety

The sole rehearsal and any later authorized run reuse the proven V4 lifecycle
under fresh identities: one `/usr/bin/ssh -T` Popen, authenticated READY before
request bytes, <=8,192-byte declaration, ordered 65,536-byte request chunks
with ACKs, full-duplex draining, compact source commitment plus indexed full
map, payload/toolchain triple agreement, pinned Xcode paths with no `xcrun`,
one indexed archive, integrity/extraction, and cleanup/absence receipts.

Every request-chunk ACK commits transaction nonce, one-based ordinal, exact
half-open byte range and size, cumulative bytes, chunk SHA-256, prior-ACK
digest, remote monotonic receipt sequence, and ACK digest. The client
independently reconstructs this chain and records write-start, write-complete,
ACK-received, and derived ACK-latency monotonic timestamps outside timed
children. The frozen cap is 512 rows. These transport timestamps are forbidden
from encoder statistics. Only schema-bound new request bytes consumed or
response bytes produced extend progress deadlines; SSH keepalive is not data
progress. Refusals retain raw stdout/stderr, partial frames, the exact last
fully acknowledged chunk, and a classification distinguishing client write
stall, remote ACK stall, response progress stall, process exit/local refusal,
protocol corruption, and absolute timeout.

Rehearsal has zero encoder workloads, zero runner children, zero performance
samples, and zero lease attempts. A Phase 2 invocation must pass correctness,
timer/ledger validation, and direct serial ownership before its first warmup.
Any failure accepts zero performance evidence and forbids retry.

Discovery is observe-only. Discovered/user/runner/unrelated PIDs are never
signaled, stopped, suspended, or cleaned. Only the retained directly spawned
SSH Popen identity may be stopped on its own bounded timeout. Remote cleanup is
limited to the exact canonical V4 transaction child proved by its receipt,
followed by absence proof. Prior-cycle paths are never contacted or inspected.
No host, service, authentication, power, LPM, PATH, package, toolchain, Metal,
or CUDA state is mutated.

## Phase 1 freeze and rehearsal

Phase 1A commits source, protocol, manifest, fresh fixtures, hashes, maps, and
local validation. Then exactly one synchronous command is permitted:

`env -u WEBP_BENCHMARK_SESSION EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_aligned_null_stage_attribution_v4.py rehearse "$PWD/evidence/backref-cost-aligned-null-stage-attribution-v4-design/rehearsal"`

There is no retry, preliminary contact, ping, `nc`, SCP, second SSH, or
follow-up cleanup session. Phase 1B is additions-only: rehearsal evidence, its
hash index, and authority/refusal envelope. Any failed receipt, source,
toolchain, alignment, process, archive, integrity, cleanup, or absence gate
leaves Phase 2 authority `NONE`.
