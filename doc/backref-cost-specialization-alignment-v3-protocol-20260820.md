# Frozen backref-cost specialization alignment v3 protocol

## Scope and authority

This default-off diagnostic starts exactly at merged main
`c208d6ed33b0ee5e84ba02e78696879266658e7e`. Phase 1 designs, implements,
freezes, and rehearses the protocol. It performs no encoder timing. Phase 2 is
unauthorized unless the additions-only Phase 1B envelope proves every frozen
gate and the sole rehearsal succeeds. Phase 3 is outside this cycle.

Factorization V4 is merged evidence, not an experiment to rerun. The audit in
`evidence/backref-cost-specialization-alignment-v3-design/phase1-prior-evidence-audit.json`
recomputes all 123 archive-index and 133 return-index hashes, cross-checks local
and remote codegen, reads the committed raw timing rows through the frozen V4
evaluation, and reconstructs a static linker map by building—but never
executing—the V4 runner from exact commit `adf680e…`. No V4 sample, workload,
remote path, threshold, or authority is reused or pooled.

The V4 map reproduces these entry addresses: DP B/L/H at `0x1000361c0`,
`0x1000366cc`, `0x100036bd8`, and Push B/L/H at `0x1000381e0`,
`0x10003883c`, `0x100038a38`. B/L cache-line offsets differ for both families.
This is consistent with placement sensitivity but is not a production claim.

## Alignment-normalized diagnostic

One optimized recorder-free Mach-O contains six private, noinline, used,
non-deduplicated functions:

- B: original baseline DP and `PushInterval`.
- L: separately named exact-work baseline clone.
- H: append-hint DP and `PushInterval` specialization.

All six functions are emitted into executable/pure-instructions Mach-O section
`__TEXT,__br_align_v3`. Each entry has 16,384-byte alignment, matching the
Apple Silicon VM page granule and therefore normalizing every smaller
power-of-two cache-line offset. Frozen order is Push B, Push L, Push H, DP B,
DP L, DP H. Every adjacent entry is one page apart, and each DP is exactly
49,152 bytes after its corresponding Push body, preserving equal relative call
placement across variants.

The Phase 1 local link freezes section address, offset, `2^14` alignment,
`0x1450c`/83,212-byte extent, 5,624 bytes of real bodies, 77,588 bytes of
inter-entry NOP padding, linker-map bytes/hash, runner bytes/hash, symbol order,
and all six zero mod-16,384 entry offsets. `-Wl,-no_deduplicate` is mandatory.

For every body, the gate freezes size and instruction/branch/load/store counts,
mnemonic digest, raw instruction-word digest, and canonical instruction digest.
Canonicalization removes only printed absolute PC addresses and maps the L
symbol names to their corresponding B names. B/L canonical instruction streams
must be exactly equal for both DP and Push. Their raw branch encodings remain
individually frozen because calls from different pages necessarily have
different PC-relative immediates. H must retain the common DP shape and differ
at the larger append-hint Push boundary.

If any entry modulo, section flag/order/extent, spacing, relative displacement,
padding, symbol distinction, B/L canonical identity, or H distinction fails,
the design is rejected before timing. The independently gated fallback is B and
a sham label invoking the exact same baseline symbol, plus aligned H; it is not
activated while the preferred six-body gate passes.

## Compile, runtime, recorder, and semantic gates

The compile gate is
`WEBP_BUILD_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT`; ordinary
builds omit the source and runner. Runtime selector
`WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_VARIANT` accepts exact `B`, `L`,
or `H`; absent means B inside the private build and every other value fails
closed. The selector is read once before selected DP mutation, and one closed
switch invokes exactly one body.

The timed binary is recorder-free and serves all variants. A separately built,
separately hashed untimed recorder captures selector/body calls, interval work,
positioning, hint/pop-tail activity, bitstream bytes, and bitstream digest.
Exactly 12 work rows are required. B/L work must be identical; common B/L/H
work and bitstreams must match; only H may have hint/pop-tail activity and H
must have zero forward-position steps.

Local gates preserve exact bitstream and decoded RGB pixels, repeat
determinism, immutable input, fallback behavior, integer costs, strict ties,
update order, reference order, traceback, and public ABI. Two sanitizer builds
cover undefined/integer and array-bounds/pointer-overflow checks. Timers remain
coarse stage timers; there is no per-pixel or per-`PushInterval` clock.

## Frozen cells, order, rows, and statistics

Corpus order is `photo-large` then `graphic-large`, both 3000×2000 generated
publication fixtures with manifest-frozen SHA-256. Method order is 4 then 6.
Variants are B/L/H. There are three repetitions with serial orders `B,L,H`,
`H,L,B`, and `L,B,H`, placing each variant once in every serial position.

Every profile process imports once, runs one excluded warmup, runs four retained
encodes, then exits. The exact Phase 2 inventory, if later authorized, is 36
direct profile processes, 36 warmups, 144 retained rows, 180 runner rows, and
180 stage rows. Correctness runs exactly 24 encodes before timing (two per
case/method/variant). The untimed recorder runs exactly 12 work encodes.
Everything is strictly serial under one exclusive lease with no retry, rerun,
tuning, pooling, parallel benchmark, external profiler, Metal, or CUDA.

Within each case/method/repetition, retained ordinals 0–3 pair B/L/H. Percent
change is `100 * (Y - X) / X`, negative faster. For B→L, L→H, and B→H, each
cell and each of DP total, DP steady, and whole encode reports all 12 paired
percentages, mean, median, sample standard deviation, minimum, maximum, sign
counts, and a deterministic 100,000-resample paired-bootstrap 95% percentile
interval. Seeds derive from `0x424c4801` plus frozen indices.

B→L is the mandatory null-control gate. In every cell and primary metric:

- absolute mean must be at most 0.75%;
- the paired-bootstrap 95% interval must contain zero;
- both interval endpoints must be within ±1.50%;
- every paired row must be within ±3.00%.

Failure invalidates the entire causal diagnostic; L→H and B→H must not be
interpreted. These bounds were fixed before timing. V4's unnormalized B→L DP
means ranged from -0.77% to +4.20%; the tighter hierarchy demands removal of
that scale while remaining well above coarse-clock quantization and allowing
ordinary process-pair noise. Effects below 0.10% absolute mean are
`indeterminate-small`; an effect is resolved only when its bootstrap interval
excludes zero.

Repeatability additionally requires each repetition-median max/min ratio to be
at most 2.0 and every required stage-share range to be strictly below 0.10
absolute.
The historical production-review gate remains separate: all four B→H DP-steady
and whole-encode means negative, all upper intervals nonpositive, and no paired
row above +0.50%. Phase 1 neither evaluates nor relaxes any bound and makes no
production consequence.

## Payload, toolchain, transport, and process safety

The fresh exact-domain 2,097,152-byte rehearsal payload is generated by
SHA-256 blocks over
`libwebp-backref-cost-specialization-alignment-v3-rehearsal\0`; manifest,
generator, fixture, and agreement must match. Negative tests reject stale V2,
V3, and V4 payload identities.

The no-`xcrun` toolchain envelope pins absolute Xcode 26.3 / macOS 26.2 paths
and identities for clang, clang++, nm, ar, ranlib, llvm-objdump, ld, and otool,
plus Xcode/toolchain/SDK metadata. Manifest, actual recomputation, and fixture
must agree. Negative tests reject stale V2 xcrun and V3/V4 toolchain envelopes.
No developer directory, toolchain, host setting, permission, or system state is
mutated.

Exactly one noninteractive `/usr/bin/ssh -T` process is created with
`BatchMode=yes`, `NumberOfPasswordPrompts=0`, `ConnectionAttempts=1`,
`ConnectTimeout=30`, `ServerAliveInterval=15`, `ServerAliveCountMax=3`, and
`RequestTTY=no`. Its command embeds only the bounded, hash-bound V3 bootstrap;
it does not embed or pre-write the source bundle or business request. There is
no preliminary contact, retry, reconnect, SCP, ping, `nc`, or second cleanup
session.

The bootstrap first emits the channel magic and one schema-, nonce-, bootstrap-,
request-declaration-, and channel-binding-authenticated READY frame. READY
includes its direct PID/PPID and proves zero request bytes read and zero files
created before readiness. The client drains stdout and stderr from process
creation but does not register or write stdin until the complete READY validates.
Only then it writes one ≤8,192-byte canonical request declaration and fixed
65,536-byte request chunks. The remote side ACKs the declaration and every chunk
with exact ordered cumulative byte/chunk counts, then emits a request-complete
digest receipt. Each next chunk is withheld until its predecessor ACK validates.
The client half-closes stdin only after the last complete chunk write.

The outer request is <32 MiB, with exact component caps of 256 KiB transport
source, 64 KiB payload source, <31 MiB business request, and a 28 MiB source
bundle. The 32 MiB outer cap narrows V2's 64 MiB per-frame ceiling; it is not a
timeout or result-threshold relaxation. The production serializer freezes exact
worst-case declaration, request, wire, ACK, response, and cap margins in
`request-channel-size-freeze.json`, including the measured exact-main git bundle.

After request completion the bootstrap executes the hash-bound transport and
payload modules in memory. It declares the exact business response and streams
fixed 262,144-byte response chunks while both client output pipes continue to be
drained, followed by a response-complete digest receipt. Business transport caps
remain archive ≤786,432 bytes, total response <1,048,576 bytes, and each control
≤8,192 bytes. Connect/READY (45 s), each request progress (15 s), silent
operator (900 s), each response progress (15 s), and absolute transaction
(1,800 s) have independent frozen deadlines.

Partial, malformed, duplicate, or out-of-order READY/ACK frames; wrong identity,
digest, count, or size; early response payload; request stall; stdout/stderr
backpressure overflow; response corruption/truncation/oversize; missing business
integrity; and missing cleanup/absence all refuse authority. Deterministic fixtures
cover delayed/no/partial READY, READY then request stall, simultaneous large
request and stdout/stderr pressure, partial and reordered ACK, source-admission
refusal, response backpressure, exact timeout boundaries, corruption/truncation,
and integrated exact-child cleanup.

Source admission verifies every requested path and SHA-256 remotely. Its
control receipt contains only fixed identity/status fields plus the exact
sorted source-map entry count and the SHA-256 of canonical sorted
`[{path,sha256},...]` rows. The complete ordered map is returned only as the
indexed `source-admission-details.json` archive member. The local client first
checks the compact count/digest against its exact request, then—after archive
integrity and extraction—independently requires the full detail to equal both
the request and compact receipt. Malformed schema/count/digest, unordered or
colliding maps, missing detail, archive mismatch, and control/detail
disagreement fail closed. The Phase 1A control freeze uses the production
serializer and encoder with every frozen identity path, records exact payload
bytes and cap margin, and includes a negative Alignment V1 full-map fixture.

Process discovery is observe-only: `/bin/ps -axo pid=,ppid=,comm=` rows are
validated without argv or filesystem resolution, and discovered PIDs never
enter a signal API. Only the retained directly spawned `Popen` creation
identity may be stopped on its own timeout. Cleanup may remove only the exact
validated cycle-owned `run.XXXXXX` child under
`~/.libwebp-metal-backref-cost-specialization-alignment-v3`, then must prove
absence. Prior-cycle paths are forbidden. An attempted SSH process is never
reported as an established remote contact: only a complete valid READY remote
identity receipt establishes the channel. Alignment V2 reached `REQUEST_WRITE`
immediately, persisted zero stdout and zero stderr, and timed out on request
progress; therefore its sole attempt established zero scientifically evidenced
remote contacts and produced no timing.

## Sole Phase 1 rehearsal and authorization

After committing Phase 1A, execute exactly one synchronous SSH attempt to
`pandocs-agent` with `ConnectionAttempts=1`, `ConnectTimeout=30`, no benchmark
session, zero encoder workloads, zero timing samples, and zero lease attempts:

`env -u WEBP_BENCHMARK_SESSION EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_specialization_alignment_v3.py rehearse "$PWD/evidence/backref-cost-specialization-alignment-v3-design/rehearsal"`

There is no retry, ping, `nc`, second SSH, SCP, background keepalive, or
post-transaction host contact. Phase 1B may add only rehearsal evidence, its
hash index, and an authorization/refusal envelope. It cannot alter source,
protocol, manifest, acceptance, payload, toolchain, corpus, order, or counts.
Any failed authority, source, toolchain, alignment, process, archive, integrity,
cleanup, absence, or receipt gate records Phase 2 authority `NONE`.
