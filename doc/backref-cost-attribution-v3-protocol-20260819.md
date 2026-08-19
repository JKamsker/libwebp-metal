# Frozen backref-cost attribution V3 protocol

Phase 1 starts from exact main commit
`086059436a46f1d5cd48d401fc06e2f96bbf095b`. It repairs only attribution
V2's diagnostic control-flow defect. It neither promotes the interval
specialization nor changes production behavior. No V1/V2 timing sample,
specialization sample, threshold, or authorization is reused.

## Audited evidence and V3 boundary

Interval-search V3 and specialization V1 established an approximately 99%
reduction in interval-positioning work and graphic wins, while photo
end-to-end holdouts failed. Attribution V1 established the process-ownership
incident safeguards. Attribution V2 selected in-process coarse timers but its
first profile proved an invalid implementation: the selected DP body ran
inside `dp_total`, then the common baseline body ran again. The raw
`dp_total/setup/steady` call counts were 3/6/6 and the baseline result
overwrote candidate output. Those rows are refusal evidence, never timing
evidence.

V3 has independent default-off identities:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT`;
- exact runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT=1`.

All predecessor build and compile gates are mutually exclusive. Ordinary
objects, targets, symbols, and strings omit V3. Public API/ABI, installed
headers, bitstreams, decoded pixels, integer costs, strict comparisons, tie
behavior, update/reference/cache order, immutable inputs, deterministic
output, and transactional failure behavior remain unchanged.

Inside each `VP8LBackwardReferencesTraceBackwards` call, V3 evaluates the
selector once before DP mutation. A closed `if/else` then invokes exactly one
baseline or specialized DP body. The predecessor common fallthrough chain is
under the opposite preprocessor branch and cannot execute in V3. Private
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

The remote rehearsal keeps `WEBP_BENCHMARK_SESSION` absent, attempts no lease,
and runs no encoder correctness/profile workload. It admits exact source,
builds the optimized Metal-disabled runner, validates private symbols and the
clock without an encoder, constructs all commands, exercises controlled
refusal, and proves archive, transfer, all-or-nothing extraction, independent
lease receipt, exact-child cleanup, and exact-child absence.

## Frozen Phase-2 pipeline

The immutable case order is photo-large then graphic-large; method order is 4
then 6. Each cell has three paired repetitions with variant order
baseline/candidate, candidate/baseline, baseline/candidate. Each direct runner
process imports once, performs one excluded warmup and four retained encodes,
then exits. The maximum and exact admitted inventory is 24 serial processes,
24 warmups, 96 retained records, and 120 total runner plus 120 total stage
records. There is no retry, rerun, tuning, pooling, parallel workload,
profiler, CUDA, or local fallback.

The only Phase-2 command, once the manifest records
`timed_execution_authorized=true`, is:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V3_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v3.py run \
  "$PWD/evidence/backref-cost-attribution-v3-execution-20260819"
```

It requires one exclusive lease on one physical Apple host. Any gate failure
is terminal and retains raw refusal evidence; it grants no retry authority.

## Ownership, admission, and consequence

Process discovery is observe-only and can only refuse. No discovered PID can
enter a signal API. Generic termination commands and PID-oriented signaling
are forbidden. Only the repository driver's retained `Popen` handle, retained
PID, and verified object creation identity can bound its directly spawned
child. SSH is noninteractive with `BatchMode=yes` and `ConnectTimeout=10`.

Remote state is one canonical `run.XXXXXX` exact child under the V3 safe root.
Cleanup requires independent validation, a removal receipt, and an exact-child
absence proof. No host, runner, service, power, Low Power Mode,
authentication, permission, privacy, or toolchain setting may change.

Even accepted data is diagnostic-only. Phase 3 must independently reconstruct
all rows and statistics by case/method for whole encode, backward-reference
generation, selected DP total/setup/steady, traceback/materialization, and
recorded histogram/Huffman/serialization stages. It may close/reopen the
interval family or name one evidence-supported next CPU boundary. Any future
experiment needs wholly new gates and is not run by this cycle.
