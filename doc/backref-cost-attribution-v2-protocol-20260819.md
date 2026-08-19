# Frozen backref-cost attribution v2 protocol

This phase is design and untimed validation only. It starts at exact main
commit `d63c9ed99e2d72e3f0aca1d375d31fad19e13455`, audits attribution v1 and its
process-ownership incident, and does not run an encoder or profiler workload.
V2 cannot promote the rejected specialization or alter production behavior.

## Diagnostic choice

The sole diagnostic is the existing in-process coarse monotonic stage timer.
On Darwin it reads `mach_continuous_time` and converts ticks with
`mach_timebase_info`. `/usr/bin/sample` is rejected because PID attachment and
task-port permission add unnecessary ownership risk. `xctrace` is rejected
because attribution v1 never established noninteractive launch permission and
rehearsal must not provoke authentication or privacy UI. Coarse timers require
no attach rights, profiler process, prompt, service change, or discovered PID.

The timer is deliberately bounded to whole encoder stages and CostManager DP
setup, steady computation, traceback, and chosen-path materialization. There
is no clock read in `PushInterval`, interval insertion, or another per-pixel
operation. Results may bound a regression to DP steady work but cannot claim
PushInterval self time, call-stack attribution, code-layout, or cache causes.

## Gates and semantic boundary

V2 has exactly three fresh gates:

- build: `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT`;
- compile: `WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT`;
- runtime: `WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT=1`.

They are default-off and mutually exclusive with attribution v1, stage
profiling, traceback, workspace, interval-search, and specialization builds.
Ordinary plans, objects, binaries, and strings omit v2. Runtime values other
than exact `1` select the baseline or suppress timer activation. Run mode also
requires exact `WEBP_BENCHMARK_SESSION=exclusive`; validate and rehearse require
the variable to be absent, including empty values.

The candidate is the byte-identical `PushIntervalSpecialized` body frozen at
`673bc3fa`. The selector is evaluated outside the two DP bodies. V2 preserves
public API/ABI, integer costs, strict comparisons and ties, interval and update
order, traceback, reference/cache choice, immutable inputs, allocation
fallback, bitstreams, and decoded RGB. Both variants use one optimized CPU-only
binary. Timers are diagnostic perturbation and never promotion evidence.

## Frozen Phase-2 command

The only authorized command, once the machine manifest says
`timed_execution_authorized=true`, is:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V2_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v2.py run \
  "$PWD/evidence/backref-cost-attribution-v2-execution-20260819"
```

No alternate command, retry, pooled predecessor sample, or production
promotion is authorized.

## Corpus, order, and counts

The generated corpus order is `photo-large`, then `graphic-large`; method order
is 4, then 6. Each case/method has three repetitions with variant order
baseline/candidate, candidate/baseline, baseline/candidate. Every directly
spawned process imports once, performs one excluded warmup and four retained
encodes, then exits. The inventory is 24 serial processes, 24 warmups, 96
retained encodes, 120 runner output records, and 120 stage records under one
exclusive lease.

Before timing, Phase 2 performs two baseline and two candidate correctness
encodes for each case/method cell. Encoded bytes, decoded RGB, repeat
determinism, and input hashes must agree exactly. Each timed process requires
exact output/stage schemas, five records, four retained records, positive
required calls, `setup+steady <= DP total`, and
`DP total+traceback+materialize <= backward references`. Three-repeat total
median max/min must be at most 1.25 and each major stage-share range at most
0.10 absolute; otherwise the diagnostic is inconclusive.

## Process, lease, transfer, and cleanup safety

Process discovery is observe-only. A discovered SSH, runner, profiler, editor,
shell, service, benchmark, or CUDA process can only cause refusal. No PID from
`ps` enters a signaling API. Generic termination commands and PID-oriented
signal APIs are denied. A timeout may act only through the retained `Popen`
handle, PID, and creation identity of the exact child spawned by repository
driver code; it never authorizes descendant or discovered-process cleanup.

SSH is bounded, noninteractive, and uses `BatchMode=yes` plus
`ConnectTimeout=10`. Rehearsal keeps `WEBP_BENCHMARK_SESSION` absent, attempts
no lease, and invokes neither the runner's correctness/profile modes nor any
profiler. It validates exact commit/tree/source hashes, toolchain identity,
corpus hashes, optimized build and private symbols, all 24 command shapes,
controlled indexed refusal, archive construction, transfer hashes, extraction,
independent lease receipt, and cleanup.

Remote state is confined to the canonical `run.XXXXXX` child generated under
the v2 safe root. Cleanup may remove only that independently validated exact
child and must return both a removal receipt and an exact-child absence proof.
No host, runner, service, power, authentication, privacy, or toolchain setting
may be changed.

## Evidence interpretation

V2 reports total and coarse-stage medians/shares independently for each case
and method. It may bound candidate effects within DP total and steady work and
rank measured coarse stages. It must label internal call-stack, layout, cache,
or per-interval causes unresolved. It cannot reuse v1-v3 timing samples,
specialization samples, fitted thresholds, content-only paths, Metal, or CUDA.
The implementation remains default-off and diagnostic-only regardless of the
Phase-2 outcome.
