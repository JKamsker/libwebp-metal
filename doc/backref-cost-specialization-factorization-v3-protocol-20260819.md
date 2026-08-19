# Frozen backref-cost specialization factorization v3 protocol

## Scope and provenance

This is a fresh successor to merged default-off Factorization V2 at exact main
`96f5d1881619bd5b25404d869cbb2ac2d4b3329c`. V1 and V2 are groundwork plus
valid refusals. V2 repaired payload identity: its manifest, generator, fixture,
and sole rehearsal all agreed on SHA-256
`68358e6f43afbbd3d983f89185dd0da7694a65e5cbc8f31bdc8ef2102b1dc6d0`.
It nevertheless froze stale `/usr/bin/xcrun` SHA-256
`b3f741e4a6af192170bbb662221163e730870944b8ad29bfac455241789b8152`,
so its sole rehearsal failed before build and authority remained `NONE`. No V1,
V2, or V16 timing authority, sample, workload, or old remote path is reused or
rerun.

V16 established a content reversal for the always-specialized append hint:
photo DP improved by roughly 1.5--1.7%, graphic DP regressed by roughly
2.1--2.4%, with matching steady-state directions and smaller whole-encode
effects. Its coarse timers could not separate algorithmic hint savings from
function duplication, code placement, instruction-cache, branch, or control
layout effects. This protocol freezes the smallest credible simultaneous
factorization of that ambiguity.

Phase 1 creates code, protocol, local evidence, and authority only. It performs
no factorization timing. Phase 2 may run the frozen diagnostic exactly once if
and only if Phase 1B authority is valid. Phase 3 alone evaluates and decides the
consequence. Diagnostic validity and production promotion are separate gates.

## Frozen variants and semantic boundary

One optimized recorder-free binary contains three private noinline DP and
`PushInterval` bodies:

- B: merged original baseline DP and `PushInterval`.
- L: separately named always-specialized layout clone. It instantiates the
  exact same DP template and baseline `PushInterval` algorithm/work under its
  own symbols. It contains no append hint.
- H: merged always-specialized append-hint DP and `PushInterval`.

The exact runtime values are `B`, `L`, and `H` in
`WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V3_VARIANT`. An absent value
has B semantics inside the private build. Every other value fails closed. The
ordinary build omits the experiment entirely.

The selector is evaluated exactly once before the selected DP can mutate
`dist_array`. One closed switch invokes exactly one selected body. B, L, and H
preserve integer costs, strict comparisons and ties, interval order, update
order, allocation fallback, immutable inputs, chosen path, traceback,
materialization, pixel output, and bitstream output.

B to L estimates duplication/code-placement/control-layout cost. L to H
estimates the append-hint algorithm inside matched always-specialized structure.
B to H is the total boundary measured simultaneously. The evidence may still
support an interaction/mixed or unresolved conclusion; no factor is assumed.

## Timed and recorder build separation

The timed binary contains no work-counter storage, functions, calls, or symbols.
It serves all B/L/H timings and has one recorded SHA-256.

A separately built and separately hashed untimed recorder binary captures one
row for each case/method/variant. Its mandatory fields include:

- selector evaluations, exact activations, and B/L/H DP calls;
- `PushInterval` and short-push calls;
- cache segments, overlap scans, and disjoint-prefix scans;
- insert calls and null-hint insert calls;
- backward and forward positioning steps;
- append-hint checks, loads, start loads, fast paths, update checks, and updates;
- pop-tail checks and updates;
- interval updates, pops, maximum live intervals;
- bitstream bytes and digest.

Exactly 12 work rows are retained. B and L must have identical work. B/L/H must
have identical common algorithm work and bitstreams. B and L must have zero
hint/pop-tail activity. H must have exact hint activations and zero forward
positioning steps in every active cell. These counters never enter a timed
binary.

## Static/codegen gate

The timed binary must contain all six private symbols:

- `BackwardReferencesHashChainDistanceOnly`
- `BackwardReferencesHashChainDistanceOnlyLayoutClone`
- `BackwardReferencesHashChainDistanceOnlySpecialized`
- `PushInterval`
- `PushIntervalLayoutClone`
- `PushIntervalSpecialized`

Frozen disassembly facts record size, instruction, branch, load, and store
counts plus instruction/mnemonic digests. B and L DP mnemonic streams must be
equal, and B and L `PushInterval` mnemonic streams must be equal. H must differ
from L at `PushInterval`. The frozen link uses `-Wl,-no_deduplicate`; all six
private symbols must have distinct emitted addresses, preventing the linker
from aliasing the matched B/L bodies. Timed `nm` must contain no recorder
symbols; recorder `nm` must contain them. This establishes that L preserves B's
algorithm/work while H changes at the intended append-hint boundary.

## Pinned toolchain gate

`/usr/bin/xcrun` is not essential and is absent from required executable lists,
diagnostic commands, timed child commands, and codegen commands. V3 pins absolute
Xcode 26.3 paths for `clang`, `clang++`, `nm`, `ar`, `ranlib`, and
`llvm-objdump`. It derives SDK version `26.2`, canonical name, and display name
directly from the pinned `MacOSX26.2.sdk/SDKSettings.plist` and matching JSON.
Xcode `version.plist` and `ToolchainInfo.plist` are also frozen.

Before Phase 1A, every required executable and metadata file must have exact
path, canonical path, version identity, byte count where applicable, and
SHA-256 agreement across the manifest, actual-file recomputation, and an
independent fixture. A negative test must reject V2's stale xcrun digest. No
toolchain, selected developer directory, service, permission, or host setting
is mutated.

## Corpus, timing order, and retained rows

The corpus is the existing generated publication corpus, frozen to:

- `photo-large.ppm`, 3000x2000, SHA-256
  `b18f3f3e0b3324ae5c8e42f5eac831a8ba350e64c181340aa65410649b2e4612`;
- `graphic-large.ppm`, 3000x2000, SHA-256
  `26d81b74583a1b379282c6cf45bb8eeb2b352958b221a5ebf7ea8421c575e5cc`.

Case order is photo then graphic. Method order is 4 then 6. There are three
repetitions with variant orders `B,L,H`, `H,L,B`, and `L,B,H`. This balances
every variant once in every serial position. Every process imports once, runs
one excluded warmup, runs four retained encodes, then exits.

The exact inventory is 36 strictly serial directly spawned profile processes,
36 warmups, 144 retained timing rows, 180 runner rows, and 180 stage rows. No
retry, rerun, tuning, alternate timing, pooling, parallel benchmark, CUDA, or
external profiler is permitted.

Before timing, the timed binary performs exactly two correctness encodes for
each B/L/H case/method combination: 24 total. All bitstreams, decoded RGB,
repeat outputs, and inputs must match. The untimed recorder then performs the
12 work encodes. Correctness and work occur under the same one exclusive lease
as timing, but are never timing samples.

The primary timers are `mach_continuous_time` coarse stages. Every row retains
whole encode, DP total, DP setup, DP steady, traceback, materialization, and the
required encoder stages. There is no per-pixel or per-`PushInterval` clock.

## Frozen statistics and interpretation

Within every photo/graphic method-4/method-6 cell and repetition, retained
ordinal 0 through 3 aligns B/L/H. For each aligned pair, percent change is
`100 * (Y - X) / X`; negative is faster.

For B to L, L to H, and B to H, the evaluator independently recomputes all 12
paired percentages for DP total, DP steady, and whole encode. It reports the
arithmetic mean, median, sample standard deviation, minimum, maximum, sign
counts, and a deterministic 100,000-resample paired-bootstrap 95% percentile
interval for the mean. Seeds derive from `0x424c4801` and frozen cell/metric/pair
indices. Setup remains retained and auditable but is not a primary causal
decision metric. No threshold may be fitted after results.

Per cell and metric:

- below 0.10% absolute B-to-H is `indeterminate-small`;
- opposite-signed B-to-L and L-to-H is `interaction-mixed-opposite-sign`;
- layout is dominant only when its absolute component is at least 60% of the
  absolute total and the hint component is below 60%;
- hint dominance uses the symmetric rule;
- everything else is `interaction-mixed`.

Repeatability requires the maximum/minimum ratio of the three repetition
whole-encode medians for each case/method/variant to be at most 2.0 and the
range of every required stage's median share of whole encode across those
three repetitions to be at most 0.10 absolute.

Diagnostic success requires exact source, build, toolchain, device, process,
lease, order, count, schema, hash, correctness, work, codegen, timer,
repeatability, archive, extraction, and cleanup gates. It does not require a
production winner.

H is production-eligible for review only if B-to-H DP steady and whole-encode
mean are negative in all four required cells, every upper 95% bootstrap bound
is nonpositive, no paired row regresses by more than +0.50%, and every
correctness/work gate passes. Otherwise the consequence is no production
promotion, even if the causal diagnostic is valid.

## Phase 1 authority and process safety

Phase 1A freezes all source and hashes first. Then exactly one synchronous
untimed remote transport rehearsal runs on `pandocs-agent` with
`WEBP_BENCHMARK_SESSION` absent. It constructs the full plan and exercises
source, pinned toolchain, device/resource/process, two-build, timer, framed
transport, archive, integrity, extraction, cleanup, and absence admission, but
performs zero encoder workloads, zero timing samples, and zero benchmark-lease
attempts. There is no retry, rerun, alternate route, or post-transaction SSH.
Phase 1B grants diagnostic authority only if every frozen gate and receipt
passes; otherwise it records authority `NONE`.

Discovered and pre-existing PIDs are observe-only and are never passed to a
signal API. Only a retained directly spawned `Popen` creation identity may be
stopped on its own timeout. Cleanup may remove only the exact validated
cycle-owned `run.XXXXXX` child beneath
`~/.libwebp-metal-backref-cost-specialization-factorization-v3`, with a receipt
and absence proof in the same transaction. Prior-cycle paths are forbidden.

Any failed rehearsal, source admission, integrity footer, cleanup footer,
absence proof, process gate, archive gate, receipt, or missing remote identity
yields authority `NONE`.
Phase 1B is additions-only rehearsal evidence and an authorization/refusal
envelope. It cannot change frozen source or protocol bytes.

If authorized, Phase 2 runs exactly once with
`WEBP_BENCHMARK_SESSION=exclusive`, one exclusive lease, and all variants
strictly serial. If authority is `NONE`, it makes no host contact.

## Compact return protocol

The proven compact framed transport is retained with fresh identities. The
archive cap is 786,432 bytes and the total framed stdout must be strictly below
1,048,576 bytes. Control payloads are at most 8,192 bytes and bulk chunks are
262,144 bytes. The complete response is constructed and cap-checked before its
first byte is emitted.

The compact archive retains raw runner/stage rows, commands, correctness,
work rows, codegen facts, build identity, resources, lease, status, and exact
hash indexes. Redundant request payload, process tables, full build logs, full
`nm`, and full disassembly are represented by exact counts/digests. Cleanup is
complete before response emission, and `cleanup-footer` is last. No follow-up
SSH/SCP cleanup operation exists.

Frozen commands are recorded in the manifest. The rehearsal command must run
at exact Phase 1A; the Phase 2 command must run at exact additions-only Phase
1B. Publication, push, PR creation, CI waiting, and production consequence are
outside Phase 1.
