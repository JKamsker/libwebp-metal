# Experiment 3 persistent/batched Metal operator report

Operator status: **completed-valid**.

This run covered only research experiment 3 at the preserved HEAD
`64309ffce345333c1a252e54e088e696dc3018c0`. The required source base was
`18fd520d5d7faf0645d461bded27c0ba7ee4a48e`; the verified experiment-1 and
experiment-2 artifact commits were preserved. No codec algorithm, aggregate
threshold policy, default behavior, matrix, variant, repetition count, or
stopping rule was changed. No performance conclusion was made.

## Timing and phases

- Operator start/preflight: `2026-08-17T18:39:25Z`
  (`2026-08-17T20:39:25+0200`).
- Artifact validation completed: `2026-08-17T18:58:45Z`
  (`2026-08-17T20:58:45+0200`); observed pre-commit wall span from the
  second-resolution preflight timestamp: `00:19:20`.
- Clean: `0.062648 s`.
- Build: `1.399715 s`.
- Required verify-only command: `0.472460 s`.
- Independent guard/refusal validation: `0.655603 s`.
- Timed import wrapper: `2026-08-17T18:45:58Z`–`18:46:02Z`,
  `4.225574 s`.
- Timed encode wrapper: `2026-08-17T18:47:21Z`–`18:54:03Z`,
  `401.298247 s`.
- Sum of the two timed wrapper durations: `405.523821 s`.

The complete machine-readable record is
`profile-data/runs/20260817-184558-experiment-3-metal-batch/validation_summary.json`.
The preflight is
`profile-data/operators/experiment-3-metal-batch-20260817T183925Z/preflight.json`
(SHA-256
`dc04416cf291bb6a5b51f9e2fa6038df0dffc1dfa760e024bd0b9e0f333b66bb`).

## Exact commands and flags

```sh
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 WEBP_BUILD_METAL_BATCH_EXPERIMENT=1 metal-experiment
WEBP_METAL_BATCH_EXPERIMENT=1 extras/metal_encode_batch_experiment --verify-only --width=97 --height=65 --batch-size=3 --quality=75 --method=4
scripts/test_experiment_guards.py
WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_BATCH_EXPERIMENT=1 WEBP_METAL_BATCH_SIZES='1 2 4 8' WEBP_METAL_COLD_REPETITIONS=5 WEBP_METAL_WARM_ITERATIONS=20 scripts/run_metal_batch_experiment.sh extras/metal_encode_batch_experiment /private/tmp/libwebp-metal-batch-item3-b98d7i/item3-import-3000x2000.jsonl 3000 2000
WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_BATCH_EXPERIMENT=1 WEBP_METAL_BATCH_SIZES='1 2 4 8' WEBP_METAL_COLD_REPETITIONS=5 WEBP_METAL_WARM_ITERATIONS=20 WEBP_METAL_EXPERIMENT_STAGE=encode scripts/run_metal_batch_experiment.sh extras/metal_encode_batch_experiment /private/tmp/libwebp-metal-batch-item3-b98d7i/item3-encode-3000x2000.jsonl 3000 2000
```

`WEBP_ENABLE_METAL=1` was supplied as the required ordinary-Metal protocol
flag. The only experiment build flag was
`WEBP_BUILD_METAL_BATCH_EXPERIMENT=1`, which compiled the expected private
macro `WEBP_USE_METAL_BATCH_EXPERIMENT=1`. The only experiment runtime flag
was `WEBP_METAL_BATCH_EXPERIMENT=1`; every timed prefix also set
`WEBP_BENCHMARK_SESSION=exclusive`. All stage-profile, crossover, ablation,
predictor, legacy umbrella, and other checked experiment names were absent.
The harness internally set its documented `WEBP_METAL_LOSSY=1` and
`WEBP_METAL_LOSSY_MIN_PIXELS=0` settings.

The committed wrapper and harness were used unchanged. The fixed workload was
deterministic synthetic RGB at 3000×2000, quality 75, method 4, batch sizes
1/2/4/8, single and batch submissions, five independent cold processes and
twenty warm samples in one warmed process for each size/submission. Import ran
before encode and the two stages were serial.

## Mechanical validation

- Both files use schema `libwebp-metal-persistent-batch-v1`.
- Import: `200` records (`40` cold + `160` warm), all 8 size/submission
  groups, exact lifecycle/warmup and iteration coverage, zero encoded bytes,
  nonnegative numeric timings, and exact command-buffer evidence.
- Encode: `200` records (`40` cold + `160` warm), all 8 groups, exact
  lifecycle/warmup and iteration coverage, positive aggregate output bytes,
  nonnegative numeric timings, and exact command-buffer evidence.
- For every single record, `metal_command_buffers == batch_size`; for every
  batch record, `metal_command_buffers == 1`.
- The verify-only harness passed CPU, batched Metal, and unchanged single Metal
  final WebP bitstream equality for 3 images and its transactional rejection
  check. Two identical untimed verify-only invocations both passed with
  identical output.
- Aggregate encoded-byte output was constant within each fixed encode group;
  this is the available repeated-output evidence in the timed schema, which
  does not retain final bitstreams.
- `scripts/test_experiment_guards.py` passed:
  `PASS: five independent build/runtime guards and fail-closed leases`.
- No failed experiment prerequisite occurred. Two preliminary operator gate
  shells exited before timing because bare system commands were unavailable
  and then because a scan matched its own shell command text. Neither created
  an output file or ran a timed sample; the final gate passed using absolute
  system paths and PID/parent-PID self-exclusion.

## Machine and contention preconditions

The sanitized preflight records macOS 26.5.1 on arm64 MacBook Pro Mac16,7,
Apple M4 Pro, 14 logical CPUs, 24 GB memory, integrated 20-core Metal 4 GPU,
AC power with a charged 100% battery, no thermal/performance/CPU-power
warning, 77% system-wide free memory at preflight (76% at each timed gate),
active idle-system/display sleep prevention, and no competing experiment
operator/process. No serial number, UUID, or other sensitive machine
identifier was committed.

## Original and committed raw outputs

The original output directory was retained and not modified:
`/private/tmp/libwebp-metal-batch-item3-b98d7i`.

| Stage | Original path | Committed path | Original SHA-256 | Committed SHA-256 |
|---|---|---|---|---|
| import | `/private/tmp/libwebp-metal-batch-item3-b98d7i/item3-import-3000x2000.jsonl` | `profile-data/runs/20260817-184558-experiment-3-metal-batch/item3-import-3000x2000.jsonl` | `1c7719b075b2fa371c4b109692f56bf43e83be425b5508eee44e8f0edcf325dd` | `1c7719b075b2fa371c4b109692f56bf43e83be425b5508eee44e8f0edcf325dd` |
| encode | `/private/tmp/libwebp-metal-batch-item3-b98d7i/item3-encode-3000x2000.jsonl` | `profile-data/runs/20260817-184558-experiment-3-metal-batch/item3-encode-3000x2000.jsonl` | `693a881a4c0035b4bed48f9421ec3b8c1959912396172ae291c8f2f12ab2d405` | `693a881a4c0035b4bed48f9421ec3b8c1959912396172ae291c8f2f12ab2d405` |

The committed raw files contain only sample records; path and sensitive
metadata scans passed. Sol owns all later inspection and interpretation of the
raw timing values. This operator made no performance or policy decision.
