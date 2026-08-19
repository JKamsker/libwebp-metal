# Frozen backref-cost attribution V7 protocol

Phase 1 starts from exact main commit
`567e48ddfeacfaa65fb11a1611fba7aa7f5590a5`. It carries forward the merged
V6 single-selected-DP/timer semantics, two-plane evidence, and non-circular
two-commit Phase-1 authority unchanged. V7 repairs only V6's dependence on a
second SSH operation for cleanup after the first remote interaction.
It neither promotes the interval
specialization nor changes production behavior. No V1/V2/V3 timing sample,
specialization sample, threshold, or authorization is reused.

## Audited evidence and V7 boundary

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

Attribution V6 froze the correct algorithm, timers, three-state lease return,
archive verification, and Phase-1A/Phase-1B authority. Its sole rehearsal
failed before operator invocation when the follow-up SSH cleanup connection
timed out. V6 correctly made no cleanup claim and authorized no timing. V7
does not contact or inspect that V6 child or any prior-cycle path.

V7 has independent default-off identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT`;
- exact runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT=1`.

All predecessor build and compile gates are mutually exclusive. Ordinary
objects, targets, symbols, and strings omit V7. Public API/ABI, installed
headers, bitstreams, decoded pixels, integer costs, strict comparisons, tie
behavior, update/reference/cache order, immutable inputs, deterministic
output, and transactional failure behavior remain unchanged.

Inside each `VP8LBackwardReferencesTraceBackwards` call, V7 evaluates the
selector once before DP mutation. A closed `if/else` then invokes exactly one
baseline or specialized DP body. The predecessor common fallthrough chain is
under the opposite preprocessor branch and cannot execute in V7. Private
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
transfers a deterministic 5 MiB SHA-256-counter payload through framed stdin,
which is 1.25 times the conservative 4 MiB maximum expected run archive. Local
fixtures exercise success, remote/control-only refusal, malformed and
truncated frames, missing footer, archive corruption, and transport timeout.
The live session proves all-or-nothing extraction, exact-child cleanup, and
exact-child absence. It emits an explicit `not-attempted`
lease-transfer record and never requests, copies, or waits for a lease receipt.

There is no rehearsal retry, rerun, pool, unplanned fallback, encoder workload,
profiler workload, or lease acquisition. The deterministic SHA-256-counter
payload is incompressible and at least the conservative maximum run archive.

Lease transfer has exactly three states: `not-attempted`,
`unavailable-after-attempt`, and `verified`. A lease receipt is mandatory only
after acquisition was attempted. One directly owned `ssh -T` Popen uses
`BatchMode=yes`, `NumberOfPasswordPrompts=0`, and a ten-second connect bound.
Its complete admission/build/operator/return/finally transaction has a frozen
7,200-second bound. Only that retained Popen handle and creation identity may
be stopped after timeout. Timeout or truncation leaves cleanup unknown and
forbids a reconnect or post-run cleanup attempt.

Evidence remains two-plane inside that one stdout frame stream. Four compact
control frames—source admission, operator status, archive build, and lease
state—precede optional bulk. The data-plane declaration freezes archive hash,
byte size, 512 KiB chunk count, compression, and full member inventory before
ordered chunks. An integrity footer follows bulk. In the remote `finally`, the
session revalidates and removes only its own exact V7 child, proves absence,
and emits the mandatory cleanup footer as the last frame. Normal success is
impossible without that footer. No SSH, SCP, or cleanup command follows the
session.

## Two-commit Phase-1 identity and freeze

Phase 1A is the immutable source/protocol commit. It contains every code path,
default-off V7 gate, manifest, schema, exact rehearsal/Phase-2 command, corpus,
order, count, timeout, fixture, and local validation. The one remote rehearsal
runs synchronously against exact 1A with `WEBP_BENCHMARK_SESSION` unset. Its
source-admission, operator, rehearsal, and transfer receipts record the 1A
commit and tree.

Phase 1B is a direct single-parent child of 1A. It adds only raw rehearsal
evidence below `evidence/backref-cost-attribution-v7-design/rehearsal/`, one
hash index for every raw file, and
`evidence/backref-cost-attribution-v7-design/phase1b-authorization.json`.
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
  python3 scripts/execute_backref_cost_attribution_v7.py run \
  "$PWD/evidence/backref-cost-attribution-v7-execution-20260819"
```

It requires one exclusive lease on one physical Apple host. Any gate failure
is terminal and retains raw refusal evidence; it grants no retry authority.

## Ownership, admission, and consequence

Process discovery is observe-only and can only refuse. No discovered PID can
enter a signal API. Generic termination commands and PID-oriented signaling
are forbidden. Only the repository driver's retained `Popen` handle, retained
PID, and verified object creation identity can bound its directly spawned
child. SSH is noninteractive with `BatchMode=yes` and `ConnectTimeout=10`.

Remote state is one canonical exact child under the distinct V7 safe root.
The same session owns child creation, validation, operator execution, evidence
streaming, final removal, and absence proof. It never contacts the V6 root or
any prior-cycle path. No host, runner, service, power, Low Power Mode,
authentication, permission, privacy, or toolchain setting may change.

Even accepted data is diagnostic-only. Phase 3 must independently reconstruct
all rows and statistics by case/method for whole encode, backward-reference
generation, selected DP total/setup/steady, traceback/materialization, and
recorded histogram/Huffman/serialization stages. It may close/reopen the
interval family or name one evidence-supported next CPU boundary. Any future
experiment needs wholly new gates and is not run by this cycle.
