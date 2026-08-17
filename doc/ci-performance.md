# CI and performance regression policy

This fork deliberately separates deterministic correctness gates from noisy
performance signals. A timing change never makes the portable `Correctness`
check fail, and a generic hosted macOS runner is never presented as Metal
runtime coverage.

## Workflow inventory

- `Correctness` runs on GitHub-hosted Linux and macOS. It checks a CMake
  Metal-off build, a Metal-on compile/link, and a lossless smoke test with
  runtime Metal disabled. This is the required branch-protection check.
- `Metal correctness` runs on physical Apple silicon labeled `self-hosted`,
  `macOS`, `ARM64`, and `metal`. It forces all three Metal operations, verifies
  pixel/bitstream promises, and proves that each GPU operation logged actual
  execution. It is a trusted-branch, scheduled, and manual release gate.
- `Metal performance signal` runs on the same class of physical Mac with an
  additional `performance` label. It provides weekly/manual alternating
  CPU/Metal measurements against the last accepted same-runner baseline. It is
  never a required correctness check.

The self-hosted runner must be project-controlled, ephemeral or dedicated, and
must not be attached to a public repository if it executes untrusted pull
requests. The workflow uses no repository secret. The built-in checkout token
has read-only contents permission.

Required runner software is a supported macOS/Xcode command-line toolchain,
CMake, Ninja, Python 3, Git, and a Metal-capable Apple-silicon GPU. Give the
runner the custom labels `metal` and, only if its power/thermal configuration
is controlled, `performance`. Disable sleep and automatic OS updates during a
run; keep the machine on AC power; avoid concurrent jobs. Do not apply
`performance` to an ordinary developer laptop or a hosted VM.

Repository settings:

1. Protect `main` and require `Correctness / CMake (ubuntu-latest, Metal OFF)`
   and `Correctness / CMake (macos-14, Metal ON)`.
2. Treat `Metal correctness / real-metal` as a weekly and release gate. Before
   merging a Metal-affecting change, push the reviewed commit to a trusted fork
   branch and dispatch it manually. The committed workflow intentionally does
   not execute pull-request code on the self-hosted machine.
3. Do not require `Metal performance signal`. Subscribe maintainers to Actions
   failures so critical signals are noticed.
4. Keep Actions cache and artifact retention enabled. Raw performance artifacts
   are retained for 90 days and correctness diagnostics for 30 days.

## Measurement protocol

`generate_performance_corpus.py` creates two deterministic 2560x1920 PPM
inputs and records byte hashes in `manifest.json`; no external corpus or secret
path is assumed. `run_performance.py` records end-to-end cold-process cases for
lossless methods 4 and 6, isolated hash acceleration, and lossy method 4. Each
case has one untimed warm-up and at least nine timed observations by default.
CPU/baseline and accelerated order alternates on every observation to balance
monotonic drift.

Timed collection also requires `WEBP_BENCHMARK_SESSION=exclusive`. The
performance workflow supplies it only on the dedicated, serialized runner;
direct invocations without that acknowledgement fail before writing samples.

The collector also requires the expected verbose Metal marker in every
accelerated sample, so a silent CPU fallback cannot be recorded as a GPU
measurement. Every run uploads:

- every raw timing, command, accelerator environment, output size, and output
  hash as JSON Lines;
- the corpus manifest and generated inputs;
- commit, UTC time, runner identity, hardware model, architecture, compiler,
  CMake/Xcode versions, macOS version, power source, and thermal report;
- machine-readable and Markdown comparisons.

The accepted baseline is scoped by runner name and is compatible only when
runner architecture, hardware model, corpus hash, benchmark-protocol hash, and
schema match. A missing or incompatible baseline starts a new series. Passing
runs advance the
baseline; warning and critical runs do not, preventing a regression from
silently becoming normal. If a toolchain or OS upgrade intentionally changes
performance, run twice, inspect both raw artifacts, and manually clear the old
`metal-perf-v1-<runner>` Actions caches to start a documented series.

## Statistical and alert policy

Analysis uses medians and deterministic 10,000-resample bootstrap 95%
confidence intervals. It tracks both accelerated wall time versus the accepted
baseline and relative CPU-to-Metal speedup, because either can reveal a
regression while the other hides machine-wide drift.

A case is a **warning** when either condition holds:

- accelerated median is at least 5% slower and the interval's lower bound is
  above 2% slower; or
- relative speedup falls at least 7% and the interval's upper bound remains
  below a 3% loss.

A case is **critical** when either condition holds:

- accelerated median is at least 10% slower and the interval's lower bound is
  above 5% slower; or
- relative speedup falls at least 12% and the interval's upper bound remains
  below a 5% loss.

Warnings annotate the Actions summary and keep the previous baseline.
Criticals also fail the performance-only workflow to trigger normal Actions
notifications. Neither result affects the portable correctness workflow. A
maintainer triages a signal by checking power/thermal metadata, rerunning on
the same idle runner, and opening an issue only if two consecutive compatible
runs show the same warning or one rerun remains critical. Bisect only after
that confirmation. Close as noise with links to both artifacts when it does not
reproduce.

When profiling establishes more representative dominant stages, add cases
without deleting old case identifiers in the same schema. The integrated
backend-neutral selector should remain the top-level CPU/accelerator switch;
stage-specific Metal knobs may isolate an operation. Preserve the JSON field
names and keep `baseline`/`accelerated` variants so existing series remain
readable.
