# Frozen backref-cost workspace remote v3 protocol

## Authority and phase boundary

This protocol is the sole phase-2 input. Its immutable design parent is
`1b6f6b707e79bfcfc1d912bf1b4c916b3f7b58e5`, based on baseline
`805e5ac4341ccf0d1ef960adb9107275652c973f`. Only samples created from the
eventual clean `<FROZEN_PROTOCOL_COMMIT>` by the command below belong to this
experiment. No earlier command, path, gate, schema, refusal, or observation is
performance data for v3.

The executor must not edit criteria, counts, order, power state, services, or
remote state outside the generated v3 run child. There is no local timing
fallback, retry, or alternate host.

## Exact phase-2 command

From a clean worktree at `<FROZEN_PROTOCOL_COMMIT>`, choose a new absolute local
evidence directory and run exactly once:

```sh
WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V3_COMMIT=<FROZEN_PROTOCOL_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/execute_backref_cost_workspace_remote_v3.py run \
  /absolute/local/path/evidence/backref-cost-workspace-remote-v3
```

`ssh pandocs-agent` is the only authorized timing host. The driver and runner
both require exact `WEBP_BENCHMARK_SESSION=exclusive`; any other value refuses.
Metal is disabled and CUDA is forbidden.

## Structurally safe remote path and transfer

Before source transfer, the driver reads the process table and fails if any
`Runner.Worker`/job exists. `Runner.Listener` may remain active. No service is
stopped and no runner directory is entered, read, or changed.

The exact path-guard program discovers canonical absolute `HOME` on the remote,
creates the direct safe root
`$HOME/.libwebp-metal-backref-cost-workspace-remote-v3`, rejects a symlinked or
non-canonical root, and invokes `mktemp -d` with `run.XXXXXX` beneath it. A run
path is accepted only when its raw and real paths are identical, its dirname is
the canonical safe root, its basename matches exactly `run.[A-Za-z0-9]{6}`,
and `lstat` proves a real directory. This rejects separators, traversal,
siblings, and symlinks. Cleanup invokes that same validator, recursively removes
only the exact accepted child, and proves it no longer exists.

The driver creates a Git bundle for exact `HEAD`, hashes it locally and
remotely, creates the fixed empty bare repository `verify.git` beneath the
accepted run child, and runs `git -C ABSOLUTE_VERIFY_REPOSITORY bundle verify
ABSOLUTE_BUNDLE`. Verification outside repository context is forbidden. It
then removes the verification repository, clones only beneath the accepted run
child, checks out the expected commit detached, and proves exact commit, tree,
clean status, and critical source SHA-256 values. Returned
evidence is archived beneath the run child, SHA-256 matched before extraction,
restricted to contained regular files/directories, checked against its remote
artifact index, and indexed again locally. Lease release is mandatory before
return and cleanup. A refusal returns safely available partial evidence and
still uses exact-child cleanup.

## Fail-closed host and execution-state records

At initial preflight, immediately before timing, and immediately after timing,
the operator records and validates Darwin arm64, `Mac16,10`, Apple M4, 24 GiB
physical memory, available memory, raw/parsed disk state, compiler path/version,
SDK path/version, effective `xcode-select`, `CC`, `SDKROOT`, and `DEVELOPER_DIR`,
AC power, both Low Power Mode sources, raw thermal/performance state, and a
separate full process snapshot plus hash. The frozen Xcode clang 17 and macOS
26.2 SDK identities in the manifest must match.

Every state requires AC power, Low Power Mode off, all three no-warning thermal
lines, at least 4 GiB available memory, at least 8 GiB available disk, no
`Runner.Worker`, and no competing v3 runner, benchmark, or CUDA process. A
listener is allowed but untouched. No power setting is changed.

The nonblocking user-scoped lease is the new path
`~/.libwebp-metal-backref-cost-workspace-remote-v3.lock`. It is acquired only
after the initial process/host gates and is explicitly released in a `finally`
path before transfer or cleanup. Timed children are synchronous and serial;
their stderr is isolated in `timed-child-stderr.log`, while JSON alone enters
`records.jsonl`.

## Candidate, correctness, and fallback

The only v3 candidate identities are:

- `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT`;
- `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT=1`;
- `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT_INJECT_FAILURE=1`;
- `backref_cost_workspace_remote_v3_experiment_runner`.

Default builds omit every v3 source, symbol, target, compile definition,
runtime string, and fault string. The manifest freezes the exact preprocessed
candidate and normalized-helper hashes from main. No integer arithmetic,
comparison, tie, update order, traceback, cache/reference choice, allocation
layout, or fallback behavior may differ.

Before timing, the deterministic publication corpus is regenerated and
hash-verified. All 13 case/quality rows × methods 4 and 6 (26 cells) require
identical baseline, candidate-off, candidate, repeat, injected-fallback, and
default-build-with-v3-environment bitstreams, exact decoded source pixels,
immutable inputs, determinism, and transactional fallback.

## Newly justified recorder-free matrix

The candidate affects lossless backref-cost construction used by applicable
methods 4 and 6. Three medium tune categories and three larger holdout
categories test category and scale transfer. Cold and warm lifecycles separate
process-start from steady-process behavior. Alternating process order controls
drift without a recorder.

Order is tune before holdout; photo, graphic, texture; method 4 before 6; cold
before warm. Cold uses 11 process pairs with one retained encode and no warmup.
Warm uses six process pairs with two discarded warmups and nine retained
encodes. Pair order alternates baseline-candidate and candidate-baseline,
starting baseline-candidate; cold ends baseline-candidate and warm uses the
first six entries.

The exact inventory is 408 child processes, 264 cold retained samples, 288
discarded warmups, 1,296 warm retained samples, 1,560 retained samples total,
780 retained samples per variant, 26 correctness cells, 24 statistical cells,
and 12 required holdout cells.

Warm process reduction is the median of nine retained encodes. The location
statistic is the median of paired candidate-process/baseline-process medians.
Tail is nearest-rank p95 in each raw retained variant stratum followed by
candidate/baseline division. Pooling across category, case, method, lifecycle,
tune/holdout, or process is forbidden. Tune cells are descriptive only.

Every holdout case × method × lifecycle must have paired median ratio at most
`0.99` and p95 ratio at most `1.01`. Pass additionally requires every identity,
default-omission, correctness/fallback, host-state, process-isolation,
compiler/SDK, inventory, resource, lease-release, transfer-hash, evidence-hash,
and exact cleanup gate. Limits are 300 seconds per timed child, 3,600 seconds
total lease interval, 4 GiB child RSS, and 2 GiB returned evidence.

## Required evidence

Required records are the three host-state JSON files; three separate process
tables; source/manifest/candidate hashes; build log; correctness records; raw
sample and exact command-order JSONL; separate child stderr; lease record;
evaluation; resource record; operator report; remote artifact hashes;
transfer/path/cleanup proof; and returned-evidence hashes.

## Phase-1 untimed validation commands

These commands do not acquire the lease or invoke the timed matrix:

```sh
python3 -m py_compile \
  scripts/backref_cost_workspace_remote_v3_paths.py \
  scripts/backref_cost_workspace_remote_v3_admission.py \
  scripts/run_backref_cost_workspace_remote_v3_experiment.py \
  scripts/execute_backref_cost_workspace_remote_v3.py

python3 scripts/test_backref_cost_workspace_remote_v3_admission.py
python3 scripts/test_backref_cost_workspace_remote_v3_experiment.py
python3 scripts/test_backref_cost_workspace_remote_v3_protocol.py

env -u WEBP_BENCHMARK_SESSION \
python3 scripts/execute_backref_cost_workspace_remote_v3.py path-round-trip
```

The last command is the required untimed/unleased live `pandocs-agent` path
round trip. Missing session, expected commit, clean source, host state, lease,
hash, schema, count, transfer, or cleanup proof fails closed.

Before this freeze, admission-only mode from exact design commit
`1b6f6b707e79bfcfc1d912bf1b4c916b3f7b58e5` passed against canonical HOME
`/Users/pandocs-agent-001`. It created `run.RaTDMU`, matched transfer SHA-256,
verified the valid bundle through its scoped bare repository, removed that
repository, cloned and proved commit/tree/clean/source identity, rejected a
separately hash-matched malformed bundle, proved malformed verification/clone
absence, removed only the validated run child, and proved remote absence again
from the driver. The process guard found no `Runner.Worker` or competing
benchmark/CUDA process; the listener remained present and untouched. No lease
was attempted and no timed binary ran. The exact record is frozen at
`evidence/backref-cost-workspace-remote-v3-design/admission-rehearsal.json`.
