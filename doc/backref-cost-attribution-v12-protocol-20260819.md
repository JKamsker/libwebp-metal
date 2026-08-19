# Frozen backref-cost attribution V12 protocol

Phase 1 starts from exact main commit
`6e6fa6905b67c65a10b3a0e80111fd93d9a82552`. It carries forward the merged
V11 single-selected-DP/timer semantics, structural PID/PPID ancestry with
deny-only identities, integrated single-session cleanup, two-plane evidence,
and non-circular two-commit Phase-1 authority unchanged. V12 repairs only
V11's local transport and frozen bounds: the whole-buffer `communicate()` path
deadlocked under simultaneous framed request/response pressure and timed out
after 7,200 seconds during a declared 5,276,453-byte archive.
It neither promotes the interval
specialization nor changes production behavior. No V1/V2/V3 timing sample,
specialization sample, threshold, or authorization is reused.

## Audited evidence and V12 boundary

Interval-search V3 and specialization V1 established an approximately 99%
reduction in interval-positioning work and graphic wins, while photo
end-to-end holdouts failed. Attribution V1 established the process-ownership
incident safeguards. Attribution V2 selected in-process coarse timers but its
first profile proved an invalid implementation: the selected DP body ran
inside `dp_total`, then the common baseline body ran again. The raw
`dp_total/setup/steady` call counts were 3/6/6 and the baseline result
overwrote candidate output. Those rows are refusal evidence, never timing
evidence.

Attribution V3 then proved the selector-once closed `if/else`, opposite-body
zero counts, no overwrite/fallthrough, and correct nested coarse timers. Its
timing remained unauthorized because a successful no-workload rehearsal
unconditionally tried to SCP `evidence/lease-record.json` although rehearsal
never acquired or attempted a lease. That directly owned child reached the
1,200-second default transfer timeout. V3 independently cleaned its exact
remote child and proved it absent; none of that cycle is timing evidence.

Attribution V7 froze the correct algorithm, timers, three-state lease return,
archive verification, single-session cleanup, and Phase-1A/Phase-1B authority.
Its sole rehearsal admitted exact source and returned an integrated cleanup
and absence footer, but the operator refused before using the representative
payload because its command-line substring scan matched its own transport
ancestor's embedded source. V7 correctly authorized no timing. V12 does not
contact or inspect that V7 child or any prior-cycle path.

Attribution V8 replaced argv scanning with exact PID/PPID/comm identity and
correctly preserved observe-only refusal and in-session cleanup. Its sole
rehearsal then refused before source admission because slashless kernel `comm`
was misclassified as an ambiguous relative path. V8 authorized no timing and
left no reusable remote child. V12 does not contact the V8 safe root or any
prior-cycle path.

Attribution V9 corrected the slashless V8 case and preserved exact identity
matching, but its parser still rejected every slash-bearing raw `comm`. The
sole no-workload rehearsal therefore refused before source admission, returned
the integrated cleanup/absence footer, and completed no representative archive
calibration. Phase 1B froze `timed_execution_authorized=false`; Phase 2 did not
invoke its command; Phase 3 left the family unassessed. A post-cycle fixture
remediation recorded a second host-dependent `realpath` defect without changing
V9 authority.

Attribution V10 preserved the corrected opaque parser and denied exact raw or
lexical-basename identities, but also required every self-to-PID1 ancestor to
match a positive Python/SSH/shell/launchd identity set. Its sole no-workload
rehearsal refused an otherwise structurally valid ancestor before source
admission. Cleanup and absence were proved, but no representative archive was
calibrated and the refusal frame omitted the identity. V10 correctly forbade
Phase 2.

Attribution V11 removed the positive ancestor allowlist while preserving a
complete acyclic self-to-PID1 structural proof and bounded identity-only
diagnostics. Its sole rehearsal passed ownership, source admission, and the
zero-workload operator, then declared a 5,276,453-byte archive. That exceeded
both its frozen 4 MiB expected-run bound and 5 MiB representative payload.
The local `communicate()` transport wrote the request without concurrently
draining output and timed out during the fourth bulk chunk; integrity and
cleanup footers were absent and cleanup remained unknown. V11 correctly
authorized no timing. V12 does not contact, inspect, clean, or reuse the V11
remote path, child, authority, or evidence.

V12 has independent default-off identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT`;
- exact runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT=1`.

All predecessor build and compile gates are mutually exclusive. Ordinary
objects, targets, symbols, and strings omit V12. Public API/ABI, installed
headers, bitstreams, decoded pixels, integer costs, strict comparisons, tie
behavior, update/reference/cache order, immutable inputs, deterministic
output, and transactional failure behavior remain unchanged.

Inside each `VP8LBackwardReferencesTraceBackwards` call, V12 evaluates the
selector once before DP mutation. A closed `if/else` then invokes exactly one
baseline or specialized DP body. The predecessor common fallthrough chain is
under the opposite preprocessor branch and cannot execute in V12. Private
thread-local counters independently record selector evaluations and actual
baseline/candidate body entries. Untimed runtime tests require the selected
body count to be positive, the opposite body count to be zero, candidate and
baseline bytes to match, and explicit reset to return every counter to zero.

## Coarse timer boundary

The sole diagnostic is the existing monotonic in-process timer. Darwin uses
`mach_continuous_time` with `mach_timebase_info`. A 4,096-read validation must
be monotonic, contain positive deltas, and have mean consecutive-read delta at
most 10,000 ns. `/usr/bin/sample`, `xctrace`, external profilers, attach
rights, and per-pixel clocks are excluded.

`dp_total` begins immediately before the one selected DP call and ends after
that call's cleanup. `dp_setup` begins before CostModel/CostManager allocation
and ends after successful `CostManagerInit`. `dp_steady` contains only the
initial literal and pixel DP loop. Traceback and chosen-path materialization
are separate. There is no clock in `PushInterval`, insertion, or another
per-pixel helper.

Every successful timer row must satisfy:

`selected_dp_calls == selector_evaluations == dp_total.calls ==
dp_setup.calls == dp_steady.calls`, with exactly the selected body's call
count nonzero. It must also satisfy `setup + steady <= dp_total` and
`dp_total + traceback + materialize <= lossless_backward_refs`.

These timers can bound cost within coarse stages. They cannot establish
`PushInterval` self time, call-stack, code-layout, branch-predictor, or cache
causality.

## Correctness and untimed prerequisites

Before timing, the pipeline performs exactly 16 correctness encodes: two
baseline and two candidate encodes for each photo-large/graphic-large and
method-4/method-6 cell. Encoded bytes, repeat determinism, decoded RGB, and
input hashes must agree. Exact runtime truth-table fallback, four direct
baseline/candidate counter cells, sanitizer builds, interval boundaries,
public export/header equality, default omission, gate isolation, source and
toolchain identity, ownership tests, and timer reset/overhead tests must pass.

The one synchronous remote rehearsal keeps `WEBP_BENCHMARK_SESSION` absent, attempts no lease,
and runs no encoder correctness/profile workload. It admits exact source,
builds the optimized Metal-disabled runner, validates private symbols and the
clock without an encoder or profiler workload, constructs all commands, and
transfers a deterministic incompressible 16 MiB SHA-256-counter payload through
framed stdin. The expected-run archive bound is exactly 8 MiB: 3,112,155 bytes
(58.98%) above V11's observed 5,276,453-byte archive and over 3.6 times the
prior 2,272,835-byte attribution execution archive. The protocol cap is exactly
32 MiB, leaving about 50% headroom around the representative archive. The 16
MiB payload hash is exactly
`d90bd85e521c276ce14b448ac05e57b6775fcf9dfcb37d9f90719a3d5b5d1904`.
Two deterministic local tar+gzip builds were byte-identical at exactly
16,782,794 bytes with SHA-256
`8bc5094b750b977492798bde16cf9fba2f3c29cd32de27b7da320d78ba1d10d1`,
leaving a 1.9993352715882706 cap ratio. The 16 correctness checks retain
independent raw input/decoded-pixel evidence and
compact WebP size/hash/equality results, not redundant WebP payload copies.
Local fixtures exercise at least 16 MiB in each transport direction,
simultaneous duplex pressure, a silent bounded operator followed by streaming,
partial-chunk stall, success, remote/control-only refusal, malformed/truncated
frames, oversized declaration, missing cleanup, and archive corruption.
The live session proves all-or-nothing extraction, exact-child cleanup, and
exact-child absence. It emits an explicit `not-attempted`
lease-transfer record and never requests, copies, or waits for a lease receipt.

There is no rehearsal retry, rerun, pool, unplanned fallback, encoder workload,
profiler workload, or lease acquisition. The deterministic SHA-256-counter
payload is incompressible and at least the conservative maximum run archive.

Lease transfer has exactly three states: `not-attempted`,
`unavailable-after-attempt`, and `verified`. A lease receipt is mandatory only
after acquisition was attempted. One directly owned `ssh -T` Popen uses
`BatchMode=yes`, `NumberOfPasswordPrompts=0`, `ConnectTimeout=10`,
`ServerAliveInterval=15`, and `ServerAliveCountMax=3`. A nonblocking selector
pump writes request frames incrementally while concurrently draining stdout and
stderr into raw files with online SHA-256 and byte counts, then half-closes
stdin. The absolute transaction bound is 1,800 seconds. After request EOF, up
to 900 silent seconds cover build/operator work; after the first framed response
byte, every output byte must renew a 15-second progress deadline, with the phase
reported specifically as bulk progress after bulk declaration. The 900-second bound
uses prior roughly 0.94–1.22 second representative encode evidence plus ample
build/correctness margin for the exact 120 encodes. The 15-second bound is more
than seven times the approximately 0.51-second 256 KiB cadence implied by the
prior measured 519,977 B/s transfer. Only that retained Popen handle and
creation identity may be stopped after a deadline. Timeout or truncation marks
cleanup unknown and forbids reconnect or follow-up cleanup.

Evidence remains two-plane inside that one stdout frame stream. Four compact
control frames—source admission, operator status, archive build, and lease
state—precede optional bulk. The data-plane declaration freezes archive hash,
byte size, 512 KiB chunk count, compression, and full member inventory before
ordered chunks. The online parser identifies declaration start, rejects an
archive over 32 MiB before materialization, and incrementally verifies frame and
archive hashes/counts. Extraction occurs only after complete declaration,
chunk, inventory, integrity-footer, cleanup-footer, and raw-stream verification.
An integrity footer follows bulk. In the remote `finally`, the
session revalidates and removes only its own exact V12 child, proves absence,
and emits the mandatory cleanup footer as the last frame. Normal success is
impossible without that footer. No SSH, SCP, or cleanup command follows the
session.

## Two-commit Phase-1 identity and freeze

Phase 1A is the immutable source/protocol commit. It contains every code path,
default-off V12 gate, manifest, schema, exact rehearsal/Phase-2 command, corpus,
order, count, timeout, fixture, and local validation. The one remote rehearsal
runs synchronously against exact 1A with `WEBP_BENCHMARK_SESSION` unset. Its
source-admission, operator, rehearsal, and transfer receipts record the 1A
commit and tree.

Phase 1B is a direct single-parent child of 1A. It adds only raw rehearsal
evidence below `evidence/backref-cost-attribution-v12-design/rehearsal/`, one
hash index for every raw file, and
`evidence/backref-cost-attribution-v12-design/phase1b-authorization.json`.
The envelope records exact 1A source commit/tree,
manifest/protocol/schema hashes from 1A, rehearsal receipt hashes, observed
transport calibration, and `timed_execution_authorized`. No 1A file may be
modified in 1B. The 1B identity is the commit containing that envelope; it is
passed dynamically as `EXPECTED_FREEZE_COMMIT`, avoiding any self-hash cycle.

Phase 2 fails closed unless `HEAD == EXPECTED_FREEZE_COMMIT == 1B`, 1B has
exactly one parent equal to recorded `SOURCE_COMMIT == 1A`, all hashes and
receipt commit/tree identities match, and every 1A..1B path is an addition in
the three predeclared evidence/envelope locations. Rejection fixtures cover a
wrong parent, modified frozen artifact, stale receipt, wrong tree/hash, missing
envelope, and extra Phase-1B path. The remote source bundle may contain 1B for
reachability, but remote admission checks out and hashes only 1A.

## Frozen Phase-2 pipeline

The immutable case order is photo-large then graphic-large; method order is 4
then 6. Each cell has three paired repetitions with variant order
baseline/candidate, candidate/baseline, baseline/candidate. Each direct runner
process imports once, performs one excluded warmup and four retained encodes,
then exits. The maximum and exact admitted inventory is 24 serial processes,
24 warmups, 96 retained records, and 120 total runner plus 120 total stage
records. There is no retry, rerun, tuning, pooling, parallel workload,
profiler, CUDA, or local fallback.

The only Phase-2 command, once the Phase-1B envelope records
`timed_execution_authorized=true`, is:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v12.py run \
  "$PWD/evidence/backref-cost-attribution-v12-execution-20260819"
```

It requires one exclusive lease on one physical Apple host. Any gate failure
is terminal and retains raw refusal evidence; it grants no retry authority.

## Ownership, admission, and consequence

Process discovery is observe-only and can only refuse. No discovered PID can
enter a signal API. Generic termination commands and PID-oriented signaling
are forbidden. Only the repository driver's retained `Popen` handle, retained
PID, and verified object creation identity can bound its directly spawned
child. SSH is noninteractive with `BatchMode=yes` and `ConnectTimeout=10`.

V12 freezes one `/bin/ps -axo pid=,ppid=,comm=` snapshot per guard and parses
PID, PPID, and the complete remaining `comm` field structurally. `raw_comm` is
a nonempty exact opaque process-table string. Slashless, slash-bearing,
space-bearing, and path-like values are valid; V12 never calls `realpath`,
`resolve`, `stat`, normalization, absolute-path checks, or any filesystem API
for `comm`. If matching needs it, `lexical_basename` is recorded separately and
derived only as the final slash component. V12 defines no resolved-path API.
It never requests or inspects argv, source, or payload text. Exact frozen
`raw_comm` or exact lexical-basename deny identities refuse even with benign
argv; prefixes, suffixes, and lookalikes pass.

The transaction's own self-to-PID-1 chain must be complete and acyclic, with
exact PPID edges and a well-formed nonempty opaque identity at every ancestor.
Self-parent edges, missing parents, and non-PID1 `ppid=0` fail closed. No
positive ancestor executable set exists: arbitrary non-denied ancestor names,
paths, spaces, slash tokens, and benign lexical collisions pass. Every process
row, ancestor or not, refuses on exact frozen raw or lexical-basename deny-set
membership. `Runner.Listener` remains explicitly non-denied.

Every process refusal places one bounded identity-only object in the integrity
footer and hashes its canonical JSON. Its fixed schema contains only failure
code, PID, PPID, opaque `raw_comm`, lexical basename, and ancestor/conflict
booleans. It never contains argv, environment, source, payload, command text,
or filesystem identity. This diagnostic is evidence only and cannot authorize
execution.

Invalid UTF-8, truncation, malformed PID/PPID/remaining-field structure,
control-bearing or empty raw identity, duplicate PIDs, missing parents, cycles,
empty lexical basenames, and absent self PID fail closed.

Remote state is one canonical exact child under the distinct V12 safe root.
The same session owns child creation, validation, operator execution, evidence
streaming, final removal, and absence proof. It never contacts a V1-V11 root or
any prior-cycle path. No host, runner, service, power, Low Power Mode,
authentication, permission, privacy, or toolchain setting may change.

Even accepted data is diagnostic-only. Phase 3 must independently reconstruct
all rows and statistics by case/method for whole encode, backward-reference
generation, selected DP total/setup/steady, traceback/materialization, and
recorded histogram/Huffman/serialization stages. It may close/reopen the
interval family or name one evidence-supported next CPU boundary. Any future
experiment needs wholly new gates and is not run by this cycle.
