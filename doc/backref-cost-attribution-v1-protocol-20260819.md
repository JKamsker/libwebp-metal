# Frozen backref-cost attribution v1 protocol

> **Superseding safety consequence (2026-08-19):** Phase 1's SIGTERM of PID
> `28860` was an unauthorized termination of an unrelated user-owned
> interactive SSH session, not protocol cleanup. See the
> [root incident audit](backref-cost-attribution-v1-incident-audit-20260819.md)
> and [machine-readable incident record](../evidence/backref-cost-attribution-v1-remediation-20260819/incident.json).
> Process observations are refusal-only and never signaling authority.

This cycle is diagnostic attribution only. It cannot promote the rejected
branch-free specialization, revive any interval-search candidate, set a
content threshold, or justify a graphic-only production path.

Phase 1 is frozen fail-closed. The read-only profiler inventory completed, but
the required noninteractive remote rehearsal did not: an interactive
`ssh pandocs-agent-001@100.85.234.14` process remained alive for 19:16:45 and
was terminated with SIGTERM before any workload or profiler invocation. The
manifest therefore sets `timed_execution_authorized` to false. The command
below is frozen for audit only and must not be executed from this handoff.

## Sole Phase-2 authority

If a later, separately authorized handoff clears the blocker, its sole command
shape would be:

```sh
env WEBP_BENCHMARK_SESSION=exclusive \
  WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V1_COMMIT="$(git rev-parse HEAD)" \
  python3 scripts/execute_backref_cost_attribution_v1.py run \
  "$PWD/evidence/backref-cost-attribution-v1-execution-20260819"
```

`validate` and `rehearse` require `WEBP_BENCHMARK_SESSION` to be absent.
`rehearse` may admit source, generate/verify the corpus, compile the optimized
runner and dSYM, verify UUIDs/stable symbols, construct all commands, and
exercise indexed refusal/return/cleanup. It must not invoke `xctrace record`,
`sample`, the runner's `correctness` or `profile` commands, or any encoder
workload. Phase 2 performs correctness under the exclusive lease before the
first profile. Any failed prerequisite returns controlled indexed evidence and
is not retry authority.

## Profiler and build identity

The primary and only profiler is Xcode 26.0 Time Profiler through
`/usr/bin/xcrun`. Every process uses `--launch --no-prompt`; attach rights are
never assumed. Authentication UI, privacy UI, task-port denial, incomplete
trace export, or absent symbols fails closed. `/usr/bin/sample` was inspected
as a possible textual 1 ms sampler but is not a fallback, because mixing
formats would weaken the frozen comparison.

One CPU-only Mach-O is compiled with Apple clang 17 and the macOS 26.2 SDK,
`-O3 -g -DNDEBUG -fno-omit-frame-pointer`. Its matching dSYM UUID, binary
SHA-256, symbols, compiler, SDK and flags apply to both variants. Baseline has
the fresh runtime variable absent. Candidate sets exactly
`WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT=1`. This selector aliases the
exact branch-free specialization body introduced at `673bc3fa`; no old gate,
sample, runner, result, or acceptance limit is reused.

For each profile the literal command shape is:

```sh
/usr/bin/xcrun xctrace record --no-prompt --template 'Time Profiler' \
  --output PROFILE.trace --target-stdout RUNNER.jsonl \
  --target-stderr RUNNER.stderr --launch -- \
  /usr/bin/env FROZEN_ENV... RUNNER profile INPUT CASE METHOD VARIANT 1 4
/usr/bin/xcrun xctrace export --input PROFILE.trace --toc --output TOC.xml
/usr/bin/xcrun xctrace export --input PROFILE.trace \
  --xpath "/trace-toc/run/data/table[@schema='DISCOVERED_SAMPLE_SCHEMA']" \
  --output EXPORT.xml
```

The operator records each fully expanded command. No two runner/profiler
children overlap.

## Corpus and order

The bounded corpus is the repository-generated `photo-large` then
`graphic-large`, each 3000x2000, at methods 4 then 6. Each
case/method/variant gets three process profiles. A process imports once, runs
one warmup and four retained encodes, then exits. Time Profiler spans all five
encodes (warm-dominant call-stack attribution); timer evaluation discards the
first record. Repetition orders are baseline/candidate,
candidate/baseline, baseline/candidate. Total inventory is 24 serial traces,
120 timer records, 24 warmups and 96 retained records under one exclusive
lease. This design emphasizes repeatable stage share and stack attribution,
not cold-launch performance.

Before the first trace, Phase 2 runs two baseline and two candidate
correctness encodes for each of four case/method cells. Encoded bytes,
in-process decoded RGB pixels and repeat determinism must match exactly.

## Instrumentation and diagnostic acceptance

Existing whole lossless-stage call sites are activated under the additional
attribution-only marker guard. New coarse monotonic clocks cover CostManager
DP total, allocation/setup, steady pixel computation, traceback and chosen-path
materialization. Stable no-inline names expose baseline/candidate DP,
PushInterval, InsertInterval/update, setup, hash-chain, backward-reference,
histogram, Huffman and serialization boundaries. There is no clock call in
PushInterval or any per-pixel interval operation. Timers perturb the measured
binary and can never be used for a production speedup claim.

All 24 profiles require raw trace, TOC, every discovered sample/profile XML
table, zero profiler/export errors, at least 500 usable symbolized samples (the
operator conservatively also requires 500 exported rows), no more than 5%
unsymbolized weight, every frozen required symbol, five timer records and four
retained records. Setup+steady must not exceed DP total; DP total plus
traceback plus materialization must not exceed backward-reference time. Every
required stage has positive calls. The three per-cell retained-total medians
must have max/min <=1.25 and each major stage-share range must be <=0.10
absolute. Failure is an inconclusive diagnostic, not a speed result.

Source/toolchain/device/power/process/resource identity, AC power, LPM off,
thermal state, one-child isolation, lease acquire/release, corpus hashes,
correctness, archive/index/transfer/extraction and exact cleanup are mandatory.
Runner.Worker, another benchmark/profiler, CUDA, unsafe paths, less than 4 GiB
free memory or 8 GiB disk, or over 2 GiB evidence fails closed.

## Frozen interpretation

The evaluator recomputes total and per-stage attribution by case and method,
including baseline/candidate deltas and inclusive/self shares for DP,
PushInterval, insertion/update, hash-chain, traceback, histogram, Huffman and
serialization. It estimates interval materiality as baseline interval CPU
share of total encode and DP. Code-layout/I-cache/control overhead may be named
only when DP stacks shift consistently while outside-DP times do not;
otherwise that cause remains unresolved.

Close the interval-search family if baseline interval work is below 5% of
total CPU or if the sampled upper bound leaves no consistent recoverable total
win. Then rank the next dominant CPU stage separately for methods 4 and 6. If
exactly one internal sub-boundary dominates consistently, propose one wholly
new independently gated experiment, but do not implement or run it here.
No old sample pooling, relabeling, interval algorithm, fitted threshold,
production promotion, API/ABI change, Metal, CUDA or host/toolchain change is
permitted.
