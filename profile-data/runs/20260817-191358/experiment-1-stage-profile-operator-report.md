# Experiment 1 operator report

Operator status: `completed-valid`.

This report covers only encoder stage profiling at the committed revision. No
codec algorithm, threshold, matrix, repetition count, or stopping rule was
changed. No performance conclusion is made here.

## Revision and timing

- Required starting commit: `18fd520d5d7faf0645d461bded27c0ba7ee4a48e`.
- HEAD before the timed run: `18fd520d5d7faf0645d461bded27c0ba7ee4a48e`.
- Tracked worktree before the timed run: clean.
- Operator start: `2026-08-17T19:06:20.516196+02:00`.
- Timed invocation start: `2026-08-17T19:13:51.769288+02:00`.
- Timed invocation end: `2026-08-17T19:14:39.760550+02:00` (derived from the two tool wall intervals).
- Timed invocation elapsed: `47.991262 s`.
- Report/validation completion before commit: `2026-08-17T19:22:36.274745+02:00`; elapsed from operator start: `975.758549 s`.

Measured phase wall times:

- Clean build phase: `1.311015 s` total (`make clean` was `0.000004 s`; optimized build was `1.311011 s`).
- Required untimed pipeline checks: Metal correctness `1.705939 s`; dataset preparation `14.725609 s`.
- Post-run untimed correctness/refusal checks: output validator `18.288111 s`; guard/refusal suite `0.494320 s`; summarize command completed successfully.
- The initial guard-suite wall time was not captured separately.

## Exact commands and flags

The prescribed commands were run exactly:

```sh
make -f makefile.unix -j8 clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=1 CFLAGS='-O3 -DNDEBUG' CXXFLAGS='-O3 -DNDEBUG' ex
scripts/test_metal.sh examples/test_ref.ppm
python3 scripts/encoder_stage_profile.py prepare --dataset-dir profile-data/dataset
WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 WEBP_BENCHMARK_SESSION=exclusive python3 scripts/encoder_stage_profile.py run --encoder examples/cwebp --dataset-dir profile-data/dataset --output-dir profile-data/runs --methods 4 6 --backends cpu metal --quality 75 --cold-repetitions 3 --warm-repetitions 3
```

Post-run committed validation commands:

```sh
python3 scripts/validate_stage_profile_outputs.py --manifest profile-data/runs/20260817-191358/dataset_manifest.json --encoder examples/cwebp --decoder examples/dwebp --output profile-data/runs/20260817-191358/output_validation.json --methods 4 6 --quality 75
python3 scripts/test_experiment_guards.py
python3 scripts/encoder_stage_profile.py summarize profile-data/runs/20260817-191358/records.jsonl --output profile-data/runs/20260817-191358/baseline.json
```

Effective build flags were `WEBP_ENABLE_METAL=1`,
`WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=1`, `CFLAGS=-O3 -DNDEBUG`, and
`CXXFLAGS=-O3 -DNDEBUG`; the observed private macro was only
`WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT=1`. The timed runtime flags were
only `WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1` and
`WEBP_BENCHMARK_SESSION=exclusive`. Crossover, batch, ablation, predictor,
legacy umbrella, and other checked experiment flags were absent. The runner's
protocol backend settings were CPU `WEBP_METAL=0`, and Metal `WEBP_METAL=1`,
`WEBP_METAL_MIN_PIXELS=0`, `WEBP_METAL_HASH=1`,
`WEBP_METAL_HASH_MIN_PIXELS=0`.

## Mechanical results

- Preflight: pass. The full preflight is in `../operators/experiment-1-stage-profile-20260817-191138/preflight.json`.
- Fixed dataset: 9 cases, photo/graphic/texture × 512×512/1600×1200/3000×2000; all manifest input hashes matched. Source manifest SHA-256: `4711e88382816a1d1546bde24f044e37c3c6f9d5a47b2b3b625f40be8d973b`.
- Matrix: methods 4 and 6; CPU and Metal; quality 75; cold 3 and warm 3.
- Raw records: 252 total = 108 cold + 36 warmup + 108 warm; 126 CPU + 126 Metal; 36 case/method/backend groups; all records successful, lossless, exact, thread level 0.
- Commands: 144 subprocess commands; each group had three separate cold PIDs, one warmup, and three warm records in one PID.
- Baseline: schema `libwebp-encoder-stage-baseline-v1`; 72 groups, 36 cold and 36 warm, n=3 per group; warmups excluded.
- Dispatch: CPU had zero Metal flags; all 126 Metal records had hash dispatch; all 42 photo Metal records had cross-color dispatch; graphic/texture Metal records were hash-only; stage evidence matched the flags.
- Correctness/determinism: `output_validation.json` passed repeated CPU bitstream equality, repeated Metal bitstream equality, and CPU/Metal decoded-pixel equality for all 18 case/method entries.
- Refusal validation: `scripts/test_experiment_guards.py` passed all five independent build/runtime guards and fail-closed lease refusals.
- No additional timed workload was run. No performance interpretation was performed.

The mechanical stage-name check used path-specific dispatch semantics. Optional
stage keys such as `lossless_predictor` are not required on palette records;
their absence was not treated as a schema failure.

## Artifacts and SHA-256

The runner-created output directory is new and non-overwriting:
`profile-data/runs/20260817-191358/`.

| Artifact | SHA-256 |
|---|---|
| `profile-data/operators/experiment-1-stage-profile-20260817-191138/preflight.json` | `6db5deaa5a85aa9796f33d04824014148c47be270fc8f84d43ca55d12b1c06da` |
| `profile-data/dataset/manifest.json` (local generated input manifest) | `4711e88382816a1d1546bde24f044e37c3c6f9d5a47b2b3b625f40be8d973b` |
| `profile-data/runs/20260817-191358/dataset_manifest.json` | `4711e88382816a1d1546bde24f044e37c3c6f9d5a47b2b3b625f40be8d973b` |
| `profile-data/runs/20260817-191358/commands.jsonl` | `5257cc565fd5b2d5643a585518ca1bc8a256e7b0b555cbceb0c8e7b4aa97b9a5` |
| `profile-data/runs/20260817-191358/records.jsonl` | `a41945ac7d9bed4ae7fa30d6444122722f02d577d96ea5f7a9108056ccf0a874` |
| `profile-data/runs/20260817-191358/baseline.json` | `b0640dacfbcdbc38fafea0999d578c3b2ce093d84a38ad215ac7889f81e36704` |
| `profile-data/runs/20260817-191358/output_validation.json` | `6ef268569ca599051192ec8a4ab6e6861c1db8d1e1e6771afc8d122fb14c5309` |
| `profile-data/runs/20260817-191358/validation_summary.json` | `a9fc6ebcad6d14da814a39c89b9f2a1a59888e11eccaa84cd030f9db2d27fb39` |
| `profile-data/runs/20260817-191358/environment_sanitized.json` | `1de50b3fe96b3fd5198f4f0befa7ec5c597bb3fcbc4d2f0251454203bd806045` |

The committed artifacts intentionally omit the generated 73,639,443-byte PPM
corpus and the runner's raw `environment.json`, which contains hardware
identifiers. The raw environment file remains local-only; the sanitized
replacement is committed.

## Handoff

Sol may later interpret the committed baseline and raw records. This operator
report makes no stage-performance conclusion, threshold recommendation,
matrix change, repetition change, or algorithm decision.
