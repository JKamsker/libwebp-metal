# Frozen backref-cost attribution V14 protocol

Phase 1 starts from exact main commit
`e690603a84aa90448e7c6d44ebfc303920b806b3`. It carries forward the merged
V13 single-selected-DP/timer semantics, structural PID/PPID ancestry with
deny-only identities, integrated single-session cleanup, two-plane evidence,
and non-circular two-commit Phase-1 authority unchanged. V14 repairs only the
response volume: V11 and V13 stopped at the same effective SSH channel-window
boundary despite V13's full-duplex draining and correct deadline transitions.
V14 therefore compacts returned evidence and freezes caps below that boundary;
it does not extend another timeout or select an unowned alternate data plane.
It neither promotes the interval
specialization nor changes production behavior. No V1/V2/V3 timing sample,
specialization sample, threshold, or authorization is reused.

## Audited evidence and V14 boundary

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
ancestor's embedded source. V7 correctly authorized no timing. V14 does not
contact or inspect that V7 child or any prior-cycle path.

Attribution V8 replaced argv scanning with exact PID/PPID/comm identity and
correctly preserved observe-only refusal and in-session cleanup. Its sole
rehearsal then refused before source admission because slashless kernel `comm`
was misclassified as an ambiguous relative path. V8 authorized no timing and
left no reusable remote child. V14 does not contact the V8 safe root or any
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
authorized no timing. V14 does not contact, inspect, clean, or reuse the V11
remote path, child, authority, or evidence.

Attribution V12 replaced the whole-buffer client with one retained incremental
full-duplex SSH child, preserved online raw-stream hashes/counts and the 32 MiB
cap, and calibrated the 16 MiB representative archive with integrated cleanup.
Its port was otherwise correct, but `pump_owned_full_duplex()` selected
`response-progress` whenever `stdout_count` was nonzero after stdin half-close.
Because `remote_main()` writes and flushes `MAGIC` immediately, the exact
magic-only response entered the 15-second path while admission/build/operator
silence was still valid. V14 does not contact, inspect, clean, or reuse the V12
safe root, child, authority, or evidence.

Attribution V13 correctly separated REQUEST_WRITE, SILENT_OPERATOR,
BULK_STREAM, and FOOTERS and drained stdout/stderr incrementally. Its sole
rehearsal nevertheless returned exactly 1,942,116 stdout bytes: four controls,
a declaration, three complete 524,288-byte chunks, and exactly 359,772 bytes
of chunk four. V11 stopped at the same partial-fourth-chunk offset (its framing
made the total 1,941,990 bytes). V13 therefore proves that timeout tuning is
not the credible repair. The authoritative raw streams remain at
`evidence/backref-cost-attribution-v11-design/rehearsal/return-protocol/framed-stdout.bin`
and
`evidence/backref-cost-attribution-v13-design/rehearsal/return-protocol/framed-stdout.bin`;
V14 reads them locally only and never contacts either remote path.

V14 has independent default-off identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT`;
- exact runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT=1`.

All predecessor build and compile gates are mutually exclusive. Ordinary
objects, targets, symbols, and strings omit V14. Public API/ABI, installed
headers, bitstreams, decoded pixels, integer costs, strict comparisons, tie
behavior, update/reference/cache order, immutable inputs, deterministic
output, and transactional failure behavior remain unchanged.

Inside each `VP8LBackwardReferencesTraceBackwards` call, V14 evaluates the
selector once before DP mutation. A closed `if/else` then invokes exactly one
baseline or specialized DP body. The predecessor common fallthrough chain is
under the opposite preprocessor branch and cannot execute in V14. Private
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
streams a deterministic incompressible 2 MiB SHA-256-counter payload through
framed stdin. Its SHA-256 is
`255841fa98da45217a8a01b545325778d8d7b735d1bca0e9faa6e77a3c0950dc`.
Remote admission verifies those request bytes but returns only exact byte-count
and digest. The expected compact run archive bound is 512 KiB, the hard archive
cap is 768 KiB, every non-bulk payload is at most 8 KiB, chunks are 256 KiB,
and the complete framed stdout stream is at most 1 MiB. The 16 correctness
checks retain independent raw input/decoded-pixel evidence and
compact WebP size/hash/equality results, not redundant WebP payload copies.
Local fixtures independently exercise a request larger than the full response
cap and a representative response below the archive cap,
simultaneous duplex pressure, magic then long bounded silence, partial and
complete controls then silence, partial declaration then silence, complete
valid declaration then a 15-second stall, chunk progress resets, footer stall,
refusal before bulk, cleanup-last, retained-child-only timeout, malformed and
truncated frames, oversized declaration, missing cleanup, and corruption.
The live session proves all-or-nothing extraction, exact-child cleanup, and
exact-child absence. It emits an explicit `not-attempted`
lease-transfer record and never requests, copies, or waits for a lease receipt.

There is no rehearsal retry, rerun, pool, unplanned fallback, encoder workload,
profiler workload, or lease acquisition. The deterministic SHA-256-counter
payload is incompressible and four times the conservative compact run archive.

Lease transfer has exactly three states: `not-attempted`,
`unavailable-after-attempt`, and `verified`. A lease receipt is mandatory only
after acquisition was attempted. One directly owned `ssh -T` Popen uses
`BatchMode=yes`, `NumberOfPasswordPrompts=0`, `ConnectTimeout=10`,
`ServerAliveInterval=15`, and `ServerAliveCountMax=3`. A nonblocking selector
pump writes request frames incrementally while concurrently draining stdout and
stderr into raw files with online SHA-256 and byte counts, then half-closes
stdin. `REQUEST_WRITE` lasts until that half-close and has concurrent read/write,
15-second request progress, and the 1,800-second absolute bound. Half-close is
the frozen start of `SILENT_OPERATOR`: up to 900 seconds cover magic, partial or
complete source admission, operator status, archive build, lease state, every
other control frame, and a partial bulk declaration. Those bytes remain
persisted and hashed but never arm or reset the 15-second bulk deadline.
`BULK_STREAM` begins only after the complete declaration frame has passed frame
digest, JSON/schema, archive-size (at most 786,432), chunk-shape, compression,
and inventory validation. Every bulk byte renews its 15-second deadline until
all declared chunks complete. `FOOTERS` then has a separate finite 15-second
progress deadline for integrity and cleanup; cleanup is mandatory and last. A
complete integrity/refusal footer before bulk enters `FOOTERS` immediately, so
control-only refusal cannot wait out the silent bound. The 900-second bound
uses prior roughly 0.94–1.22 second representative encode evidence plus ample
build/correctness margin for the exact 120 encodes. The 15-second bound is more
than seven times the approximately 0.51-second 256 KiB cadence implied by the
prior measured 519,977 B/s transfer. Only that retained Popen handle and
creation identity may be stopped after a deadline. Timeout or truncation marks
cleanup unknown and forbids reconnect or follow-up cleanup.

Evidence remains two-plane inside that one stdout frame stream. Four compact
control frames—source admission, operator status, archive build, and lease
state—precede optional bulk. The data-plane declaration freezes archive hash,
byte size, 256 KiB chunk count, compression, member count, and a digest of the
full member inventory before ordered chunks. The artifact hash index inside the
archive remains complete. The online parser validates the declaration before
state transition and rejects an archive over 768 KiB, a control over 8 KiB, or
a total response over 1 MiB before extraction. It incrementally verifies frame
and archive hashes/counts. Extraction occurs only after complete declaration,
chunk, full-inventory-digest, integrity-footer, cleanup-footer, and raw-stream
verification.
An integrity footer follows bulk. In the remote `finally`, the
session revalidates and removes only its own exact V14 child, proves absence,
and emits the mandatory cleanup footer as the last frame. Normal success is
impossible without that footer. No SSH, SCP, or cleanup command follows the
session.

## Two-commit Phase-1 identity and freeze

Phase 1A is this immutable source/protocol commit. It contains every code path,
default-off V14 gate, manifest, schema, exact rehearsal/Phase-2 command, corpus,
order, count, timeout, fixture, and local validation. Phase 2 must first run the
one synchronous, untimed zero-encoder/profiler/lease rehearsal against exact 1A
with `WEBP_BENCHMARK_SESSION` unset, using the frozen rehearsal command. Its
source-admission, operator, rehearsal, and transfer receipts record the 1A
commit and tree.

Phase 1B is a direct single-parent child of 1A. It adds only raw rehearsal
evidence below `evidence/backref-cost-attribution-v14-design/rehearsal/`, one
hash index for every raw file, and
`evidence/backref-cost-attribution-v14-design/phase1b-authorization.json`.
The envelope records exact 1A source commit/tree,
manifest/protocol/schema hashes from 1A, rehearsal receipt hashes, observed
transport calibration, and `timed_execution_authorized`. No 1A file may be
modified in 1B. The 1B identity is the commit containing that envelope; it is
passed dynamically as `EXPECTED_FREEZE_COMMIT`, avoiding any self-hash cycle.
Phase 2 must verify full archive declaration/inventory/hash/count integrity,
online raw stdout/stderr persistence hashes/counts, cleanup-last plus exact-child
absence, safe extraction after complete verification, representative-payload
and cap margin/calibration, and zero post-session cleanup operations before
writing `timed_execution_authorized=true`. A refusal or incomplete calibration
requires a false authorization and no production command.

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
  python3 scripts/execute_backref_cost_attribution_v14.py run \
  "$PWD/evidence/backref-cost-attribution-v14-execution-20260819"
```

It requires one exclusive lease on one physical Apple host. Any gate failure
is terminal and retains raw refusal evidence; it grants no retry authority.

## Ownership, admission, and consequence

Process discovery is observe-only and can only refuse. No discovered PID can
enter a signal API. Generic termination commands and PID-oriented signaling
are forbidden. Only the repository driver's retained `Popen` handle, retained
PID, and verified object creation identity can bound its directly spawned
child. SSH is noninteractive with `BatchMode=yes` and `ConnectTimeout=10`.

V14 freezes one `/bin/ps -axo pid=,ppid=,comm=` snapshot per guard and parses
PID, PPID, and the complete remaining `comm` field structurally. `raw_comm` is
a nonempty exact opaque process-table string. Slashless, slash-bearing,
space-bearing, and path-like values are valid; V14 never calls `realpath`,
`resolve`, `stat`, normalization, absolute-path checks, or any filesystem API
for `comm`. If matching needs it, `lexical_basename` is recorded separately and
derived only as the final slash component. V14 defines no resolved-path API.
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

Remote state is one canonical exact child under the distinct V14 safe root.
The same session owns child creation, validation, operator execution, evidence
streaming, final removal, and absence proof. It never contacts a V1-V13 root or
any prior-cycle path. No host, runner, service, power, Low Power Mode,
authentication, permission, privacy, or toolchain setting may change.

Even accepted data is diagnostic-only. Phase 3 must independently reconstruct
all rows and statistics by case/method for whole encode, backward-reference
generation, selected DP total/setup/steady, traceback/materialization, and
recorded histogram/Huffman/serialization stages. It may close/reopen the
interval family or name one evidence-supported next CPU boundary. Any future
experiment needs wholly new gates and is not run by this cycle.
