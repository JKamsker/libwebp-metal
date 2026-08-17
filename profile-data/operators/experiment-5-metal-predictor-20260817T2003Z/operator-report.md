# Experiment 5 operator report

Status: **completed-valid**.

This report covers only the predictor-residual Metal prototype. The required
source base was `18fd520d5d7faf0645d461bded27c0ba7ee4a48e`; the pre-timing HEAD
was `12d2c86b9dc6c270611f7b9209dee2edf5c0f4c9`, preserving the verified
experiment-1 through experiment-4 artifact commits. No codec algorithm or
harness source was changed.

## Timing and phases

The recorded run began at `2026-08-17T19:58:23Z` and the timed protocol ended
at `2026-08-17T20:11:40Z`, an elapsed wall interval of 797 seconds. The timed
benchmark itself ran from `2026-08-17T20:08:24Z` through
`2026-08-17T20:11:40Z` (196 seconds). The correctness gate ran from
`2026-08-17T19:59:02Z` through `2026-08-17T20:02:46Z` (224 seconds), and the
independent guard check ran at `2026-08-17T20:02:58Z`.

The initial build make completed successfully. A wrapper attempted to assign
the zsh read-only variable `status` after make; the exact build command was
then re-run successfully at `2026-08-17T19:58:49Z` and was up to date. This did
not affect the build result or start a timed workload.

## Commands and flags

The exact command forms were:

```text
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 examples/cwebp examples/dwebp
WEBP_METAL_PREDICTOR=1 scripts/test_predictor_metal_experiment.sh <CANONICAL_INPUT_DIR>/mitski.png <CANONICAL_INPUT_DIR>/corgi.jpeg <CANONICAL_INPUT_DIR>/siamese.jpg
scripts/test_experiment_guards.py
WEBP_METAL_PREDICTOR=1 WEBP_BENCHMARK_SESSION=exclusive RUNS=7 scripts/benchmark_predictor_metal_experiment.sh <NEW_OUTPUT_DIRECTORY>/predictor-cold.csv <CANONICAL_INPUT_DIR>/mitski.png <CANONICAL_INPUT_DIR>/corgi.jpeg <CANONICAL_INPUT_DIR>/siamese.jpg
```

The committed copy redacts the corpus directory while retaining the fixed
identities `mitski.png`, `corgi.jpeg`, and `siamese.jpg`. The build enabled only
`WEBP_ENABLE_METAL=1` and
`WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1`. The correctness runtime enabled
only `WEBP_METAL_PREDICTOR=1`. The timed runtime enabled only
`WEBP_METAL_PREDICTOR=1`, `WEBP_BENCHMARK_SESSION=exclusive`, and `RUNS=7`.
The dry-run macro isolation check passed, and all other experiment and legacy
benchmark flags were absent.

The harness-internal controls were retained exactly: existing transform/hash
paths disabled, predictor minimum pixels set to zero, validation enabled for
correctness and the probe, validation disabled for timing, and the documented
post-dispatch failure injection used by the correctness script.

## Gate and contract results

The exact correctness script passed for every fixed input and methods 0 through
6. Its enforced checks all passed:

- CPU reference equality for every successful predictor dispatch;
- byte-identical CPU and accelerated streams;
- three fresh-process repetitions with deterministic identical streams;
- decoded CPU/accelerated equality;
- injected post-dispatch failure with byte-identical CPU fallback; and
- observed predictor dispatch for `mitski.png`, `corgi.jpeg`, and
  `siamese.jpg`.

The decline/transactional-output contract is enforceable by the committed
source and harness. The committed correctness run exercised the injected
failure fallback; it did not add an improvised decline case. The independent
guard/refusal validation passed default-off and independent build checks,
omitted-target refusals, runtime-opt-in refusals, and exclusive-lease refusals.

## Timed CSV validation

The original, non-overwriting output was:

`/tmp/libwebp-metal-experiment-5-20260817T2003Z.Ak0u74/predictor-cold.csv`

It contains the exact header and 84 data rows. The breakdown is 28 rows per
input, 42 per method, 42 per variant, and two variant rows per input/method/run.
Methods are exactly 4 and 6; runs are exactly 1 through 7; each input/method/run
has one `cpu` and one `predictor_metal` row; odd runs are CPU-first and even
runs are predictor-first. All 84 `real_seconds` fields are positive numeric
values, with zero missing and zero duplicate rows.

The original CSV SHA-256 is
`63911fe077d49ef6c0605c9c5c93c1aec64a40522642484b01ba3b240094d9d9`.
The sanitized committed CSV SHA-256 is
`b8f0d259ad841079f926693b79dd0ca2571c0d0473eee053bc161870e142f149`.
The row-by-row check confirmed that sanitization changed only the absolute
input prefixes to the fixed basenames; all other fields and order are
unchanged.

No speedup, ratio, ranking, or other performance interpretation was computed.

## Machine and contention preconditions

The pre-timing snapshot recorded macOS 26.5.1 build 25F80 on arm64, 14 logical
CPUs, and 24 GiB physical memory. The machine was on AC power with the
internal battery at 100% and charged. No thermal, performance, or CPU power
warning was recorded. System-wide free memory was 76% and CPU idle was 86.76%.
The repository volume had 344 GiB available at 22% used. A no-sleep assertion
was active and no power or sleep settings were changed. The experiment process
scan found no other experiment operator or process.

## Committed artifacts

- `preflight.json`: pre-timing state, flags, fixed matrix, lease, contracts,
  and machine preconditions;
- `predictor-cold.csv`: sanitized raw observations;
- `validation-summary.json`: machine-readable gate and CSV validation result;
- `operator-report.md`: this handoff.

Sol remains responsible for later interpretation of the raw observations. This
operator report makes no performance conclusion.
