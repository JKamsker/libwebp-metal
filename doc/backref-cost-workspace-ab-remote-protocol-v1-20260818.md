# Frozen remote backref-cost workspace A/B protocol v1

## Authority and immutable start

The executor starts only at the protocol commit handed off by the designer,
whose parent design/code commit is
`460a69a864bbabc2f5890ec6aea7b1c622944bca` and whose base is main
`e7c1be7d4070103a9b41b8c30fbbc95cd18e5a5c`. The executor runs the single
command below once. It must not edit code, criteria, order, counts, host power,
runner services, or remote state outside the generated per-run directory.

The closed `backref_cost_traceback` refusal is provenance only. It had zero
timed samples because the local MacBook had Low Power Mode enabled. Neither its
old gates nor its schemas, lease, samples, ratios, or operator may be rerun,
pooled, relabeled, or counted.

## Exact executor command

From a clean worktree at `<FROZEN_PROTOCOL_COMMIT>`, choose a new absolute local
evidence directory and run exactly:

```sh
WEBP_EXPECTED_BACKREF_COST_WORKSPACE_AB_COMMIT=<FROZEN_PROTOCOL_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/execute_backref_cost_workspace_ab_remote_v1.py \
  /absolute/local/path/evidence/backref-cost-workspace-ab-remote-v1
```

No local timed fallback exists. `ssh pandocs-agent` is the only timing host.
The driver creates an exact Git bundle, verifies its SHA-256 remotely, clones it
under
`$HOME/.cache/libwebp-metal-experiments/backref-cost-workspace-ab-v1/run.XXXXXX`,
checks out the exact commit, validates frozen hashes, invokes the timed remote
operator once, returns a SHA-256-verified evidence archive, verifies every
artifact, confirms lease release, and deletes only that validated temporary
directory. It never enters or changes `$HOME/github-runners`, Forgejo runner
state, GitHub runner state, service settings, power settings, or unrelated
files. A failed safety gate ends the run; there is no retry or improvisation.

## Fail-closed remote preflight and isolation

The remote operator requires Darwin arm64, `Mac16,10`, Apple M4, 24 GiB
physical memory, at least 4 GiB available memory, and at least 8 GiB available
disk. It freezes the exact Xcode clang 17.0.0 path/version and macOS 26.2 SDK
path/version from the manifest. It records `uname`, `sw_vers`, model, CPU,
memory, disk, compiler, SDK, `pmset -g batt`, `pmset -g custom`,
`pmset -g therm`, JSON `system_profiler SPPowerDataType`, and the process table.

AC power, `lowpowermode 0`, JSON `LowPowerMode: No`, and all three no-warning
thermal/performance lines are mandatory. Any `Runner.Worker` means an active
GitHub Actions job and fails closed. A `Runner.Listener` may remain running and
must not be stopped or modified. Any other frozen runner, benchmark, CUDA,
`nvcc`, or `nvidia-smi` process fails closed. The same complete preflight is
repeated after correctness and immediately before timing, and again after
timing. No power setting is changed.

The operator acquires the nonblocking user-scoped lease
`~/.cache/libwebp-metal-experiments/leases/backref-cost-workspace-ab-v1.lock`
before builds and releases it before evidence transfer/cleanup. Timed children
run synchronously, one at a time, with encoder `thread_level=0`. Child stderr is
captured separately in `timed-child-stderr.log`; JSON samples alone go to
`records.jsonl`.

## Candidate, builds, correctness, and fault behavior

The independent gates are exactly:

- `WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT`;
- `WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1`;
- private fault injection
  `WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_INJECT_FAILURE=1`.

Default builds omit all new source, symbols, targets, compile definitions, and
runtime strings. Metal is off and CUDA is forbidden. Baseline and candidate use
the same static Release configuration, arm64 SDK, compiler, runner source,
lossless exact mode, quality 75, method, and thread setting; only the candidate
build option differs.

Before timing, all 26 deterministic publication cells (13 case/quality entries
times methods 4 and 6) require exact baseline/candidate/repeat/fault-fallback/
default-environment bitstreams, exact decoded source pixels, immutable corpus
hashes, deterministic repeats, default independence, and transactional fallback.
The candidate source-equivalence hashes against merged main are frozen in the
manifest. Any mismatch fails before timing.

## Frozen timing order, raw inventory, and statistics

The six timed cases are deterministic and SHA-256 frozen: three tune medium
cases, then three holdout large cases; within each group order is photo,
graphic, texture. For each case, method 4 precedes method 6 and cold precedes
warm.

Cold uses 11 process pairs, one retained encode per process and no warmup. Warm
uses six process pairs, two discarded warmups and nine retained encodes per
process. Pair process order alternates baseline-candidate then
candidate-baseline, beginning and ending baseline-candidate for cold; warm uses
the first six entries. Every process is synchronous. The exact inventory is
408 child processes, 264 cold measured samples, 288 discarded warmups, 1,296
warm measured samples, 1,560 measured samples total, 780 measured samples per
variant, 26 correctness cells, 24 evaluation cells, and 12 required holdout
cells.

For warm, each process reduces its nine retained samples by the median. The
paired location statistic is the median of candidate-process / baseline-process
ratios. Tail is nearest-rank p95 over each raw retained variant stratum, then
candidate p95 / baseline p95. No pooling across category, case, method,
lifecycle, tune/holdout, or process is allowed. Tune is descriptive only.

Every holdout case × method 4/6 × cold/warm cell must have paired median ratio
at most `0.99` and p95 ratio at most `1.01`. Promotion additionally requires
every correctness, source identity, host/power/thermal/process isolation,
compiler/SDK, lease, resource, inventory, transfer, and cleanup gate. Maximum
timed child wall time is 300 seconds, total lease duration 3,600 seconds, child
RSS 4 GiB, and evidence size 2 GiB.

## Evidence and evaluator consequence

Expected returned artifacts include preflight/pre-timing/post-timing state,
three process snapshots, source and candidate-equivalence hashes, build log,
correctness records, raw samples and command order, separate timed stderr,
lease record, automated evaluation, resources, operator report, remote artifact
index, transfer/cleanup receipt, and final returned-evidence index.

The evaluator starts only after lease release, evidence return, and cleanup. It
independently validates every hash, schema, count, order, source/candidate
identity, host and runner isolation fact, exactness/fallback fact, statistic,
resource ceiling, and transfer/cleanup record. It promotes only if every frozen
gate passes. Otherwise the candidate remains default-off research code or is
rejected/removed. No API/ABI, integer/tie, threshold, fallback, Metal, CUDA,
runner, or power-setting change is authorized. Any follow-up receives wholly
new gates and is not run in this cycle.

## Untimed designer commands

The designer may run only these non-timed checks:

```sh
python3 -m py_compile \
  scripts/run_backref_cost_workspace_ab_experiment.py \
  scripts/execute_backref_cost_workspace_ab_remote_v1.py

WEBP_EXPECTED_BACKREF_COST_WORKSPACE_AB_COMMIT=<FROZEN_PROTOCOL_COMMIT> \
python3 scripts/run_backref_cost_workspace_ab_experiment.py validate

python3 scripts/test_backref_cost_workspace_ab_experiment.py
python3 scripts/test_experiment_guards.py
```

Missing `WEBP_BENCHMARK_SESSION=exclusive`, wrong source commit, dirty source,
held lease, unsupported host, wrong compiler/SDK, power/thermal failure,
`Runner.Worker`, competing benchmark/CUDA process, insufficient memory/disk,
existing output, or any hash/schema/count mismatch must refuse before timing.
