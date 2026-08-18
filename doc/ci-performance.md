# CI and performance regression policy

This fork deliberately separates deterministic correctness gates from noisy
performance signals. A timing change never makes the portable `Correctness`
check fail. Standard GitHub-hosted `macos-14` ARM64/M1 runners are used for
build and linkage coverage, but are not presented as Metal runtime coverage.

## Workflow inventory

- `Correctness` runs on GitHub-hosted Linux and macOS. It checks static and
  shared CMake configure/build/install/external-link paths with Metal off and,
  on macOS, on; compares installed Metal-off/on headers and dylib exports; and
  checks Autotools with its explicit Metal policy. The existing lossless smoke
  test keeps runtime Metal disabled on hosted runners. This is the required
  branch-protection check.
- `Metal correctness` runs on physical Apple silicon labeled `self-hosted`,
  `macOS`, `ARM64`, and `metal`. Automatic runs are limited to relevant pushes
  to `main` and a conservative weekly replay of the current `main`; maintainers
  may also dispatch an explicitly reviewed revision. It never subscribes to or
  admits `pull_request` or `pull_request_target` events. It requires an actual
  Metal device, forces all three Metal operations, verifies pixel/bitstream
  promises, and proves that transform, hash, and lossy GPU dispatch each logged
  actual execution. It also covers odd dimensions, padded source and
  output-plane strides, supported packed RGB formats, cancellation after an
  observed transform, fallback, and a bounded forced-Metal UBSan mutation
  harness. CPU fallback cannot satisfy this gate. It is untimed functional
  coverage of the selected physical device, not a performance measurement or a
  claim about other Apple GPUs or OS versions.
- `Metal performance signal` runs on a characterized physical Mac labeled
  `self-hosted`, `macOS`, `ARM64`, `metal`, and `performance`. It provides
  weekly/manual alternating CPU/Metal measurements against the last accepted
  same-runner baseline. It is never a required correctness check.

The standard hosted `macos-14` runner identifies itself as an Apple M1 virtual
machine, but `MTLCreateSystemDefaultDevice()` returned no device in
[the attempted forced-Metal run](https://github.com/JKamsker/libwebp-metal/actions/runs/32105999492).
The gate therefore remains on physical hardware; allowing hosted CPU fallback
would create a false correctness signal. GitHub documents GPU acceleration for
[the distinct M2 `macos-14-xlarge` larger-runner tier](https://docs.github.com/en/actions/reference/runners/larger-runners#specifications-for-general-larger-runners),
which this project has not adopted or characterized.

The self-hosted runner must be project-controlled, ephemeral or dedicated, and
must not execute untrusted pull-request code. Pushes are trusted only after
landing on protected `main`; scheduled runs use the current default-branch
revision; and a manual dispatch means the operator has reviewed the selected
revision. Do not add PR-family triggers or loosen the workflow's event/ref
guard. The workflow uses no repository secret, and checkout does not persist
its read-only token.

Required self-hosted runner software is a supported macOS/Xcode command-line
toolchain, CMake, Ninja, Python 3, Git, and a Metal-capable Apple-silicon GPU.
The repository-scoped correctness runner `pandocs-agent-metal` is an Apple M4
with labels `self-hosted`, `macOS`, `ARM64`, and `metal`. Keep it dedicated,
online for the weekly replay, on AC power, awake, free of automatic OS updates
during a run, and limited to one job at a time. It is intentionally not labeled
`performance`; performance jobs remain restricted to a separately characterized
runner carrying that additional label.

Repository settings:

1. Protect `main` and require `Correctness / CMake (ubuntu-latest, Metal OFF)`
   and `Correctness / CMake (macos-14, Metal ON)`.
2. Treat `Metal correctness / Physical Metal correctness (self-hosted ARM64)`
   as the physical-device gate for relevant `main` changes and weekly drift
   detection. Dispatch only a reviewed, trusted revision. Inspect its retained
   environment and dispatch logs when triaging a failure; successful CPU
   fallback is intentionally impossible.
3. Do not require `Metal performance signal`. Subscribe maintainers to Actions
   failures so critical signals are noticed.
4. Keep Actions cache and artifact retention enabled. Raw performance artifacts
   are retained for 90 days and correctness diagnostics for 30 days.

## Measurement protocol

The weekly regression signal below is operational monitoring, not evidence for
the publication report. Publication-corpus provenance, license, canonical
hashes, and untimed verification are in
`benchmarks/publication-corpus/README.md`. A future publication experiment may
use those generated inputs only under a newly predefined protocol and new
independent experiment gates; it must not relabel an item 1--5 historical run.

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
