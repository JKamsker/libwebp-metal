# Encoder stage profiling protocol

This experiment profiles the modern encoder at methods 4 and 6 without using
sampling-profiler symbol attribution as the primary measurement. Coarse
monotonic-clock probes follow encoder phase boundaries, are disabled unless
the build flag `WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT` and runtime flag
`WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1` are both present, and execute no
per-pixel probes. Default builds omit `profile_enc.c`, compile its coarse call
sites to no-ops, and do not expose `cwebp -profile_repetitions`. The supported
experiment is single-threaded; do not add `cwebp -mt`, because worker-thread
events intentionally do not inherit the calling thread's trace context.

This document defines the experiment but contains no performance results.

## Build and correctness gate

On macOS, build an optimized Metal-enabled encoder:

```sh
make -f makefile.unix -j8 clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=1 \
  CFLAGS='-O3 -DNDEBUG' CXXFLAGS='-O3 -DNDEBUG' ex
scripts/test_metal.sh examples/test_ref.ppm
```

The clean build is important when changing optimization flags. Do not use a
debug or sanitizer build for baseline records.

## Dataset

Generate the deterministic dataset before the serialized benchmark slot:

```sh
python3 scripts/encoder_stage_profile.py prepare \
  --dataset-dir profile-data/dataset
```

The manifest records absolute paths and SHA-256 hashes. It contains a full
3-by-3 matrix: `photo`, `graphic`, and `texture` content at 512x512,
1600x1200, and 3000x2000. Inputs are opaque binary PPM so decoder libraries,
metadata, alpha handling, and input conversion cannot vary between machines.
The formulas and seeds are fixed in the generator.

## Exact benchmark command

Run only after the orchestrator releases the serialized benchmark phase:

```sh
WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/encoder_stage_profile.py run \
  --encoder examples/cwebp \
  --dataset-dir profile-data/dataset \
  --output-dir profile-data/runs \
  --methods 4 6 \
  --backends cpu metal \
  --quality 75 \
  --cold-repetitions 3 \
  --warm-repetitions 3
```

For each case/method/backend, cold samples are separate one-encode processes.
Warm samples are three measured encodes after one unmeasured in-process encode.
`-profile_repetitions` is an experimental cwebp option restricted to discarded,
single-threaded lossless output; it keeps the decoded pixels and Metal process
state alive while reconstructing all per-encode libwebp state.

The CPU backend sets `WEBP_METAL=0`. The Metal backend forces both implemented
lossless paths with zero pixel thresholds. This makes selection explicit in the
record (`metal_cross_color` and `metal_hash`) and prevents crossover defaults
from changing the experiment.

Default output is `profile-data/runs/<timestamp>/`:

- `environment.json`: commit/worktree state, encoder hash/version, OS, CPU/GPU,
  power and thermal snapshots, and the runner command;
- `dataset_manifest.json`: copied content manifest and hashes;
- `commands.jsonl`: every subprocess command and trial identity;
- `records.jsonl`: one raw `libwebp-encoder-stage-v1` record per encode;
- `baseline.json`: median/MAD aggregate with warmups excluded.

Expected runtime is approximately 5-12 minutes on an Apple M4 Pro, varying with
thermal state and contention. Reserve one machine exclusively, keep it on AC
power, prevent sleep, and avoid concurrent CPU, GPU, media-engine, or disk-heavy
work. Metal requires the integrated GPU but no display access or elevated
privileges. The generated dataset uses about 75 MB; results are normally under
5 MB. A 20-minute uncontended reservation is conservative.

## Measurement schema

Each JSONL record includes run/case/backend identity, PID, in-process encode
index, `cold`, `warmup`, or `warm` role, dimensions, method, output size,
success/error status, Metal-selection flags, total nanoseconds, and a `stages`
object. Every stage entry contains accumulated monotonic nanoseconds and call
count. Repeated calls are summed.

Lossless stages are `lossless_prepare`, `lossless_container_setup`,
`lossless_analyze`, `lossless_encoder_init`, `lossless_palette`,
`lossless_input_copy`, `lossless_subtract_green`, `lossless_predictor`,
`lossless_cross_color`, `lossless_hash_chain`, `lossless_backward_refs`,
`lossless_histogram`, `lossless_huffman`, `lossless_bitstream`,
`lossless_stream_finalize`, and `lossless_riff_write`. Histogram time covers
build/combine/remap in `VP8LGetHistoImageSymbols`; Huffman time covers code
construction and tree emission. Embedded histogram-image encoding contributes
to the same hash/back-reference/histogram/Huffman/bitstream accumulators.

Metal detail stages are `metal_init`, `metal_cross_color_dispatch`,
`metal_hash_pipeline_init`, and `metal_hash_dispatch`. They are inclusive
sub-stages of their enclosing lossless phase, so stage nanoseconds must not be
summed to reconstruct total time. Cold-versus-warm interpretation should use
the role field and compare stage medians, not subtract unrelated process wall
time.

The shared trace API also exposes `lossy_import`, `lossy_encoder_init`,
`lossy_analyze`, `lossy_stat_loop`, `lossy_encode_loop`, `lossy_alpha`, and
`lossy_write` for follow-on candidate work. These fields use the same schema;
the supplied baseline matrix intentionally remains lossless-only.

## Baseline record and interpretation

`libwebp-encoder-stage-baseline-v1` groups records by case, method, backend, and
sample role. It stores count/min/median/max/MAD for total, output bytes, and
each stage, plus median stage share and Metal selection rates. `warmup` records
are retained in raw JSONL but excluded from baseline groups. A stage is a
remaining dominant CPU candidate when it has a large stable share in warm
Metal records after excluding the nested `metal_*` portion; corroborate a
candidate with a sampling profiler before optimizing it.

Re-summarize raw data without rerunning the encoder:

```sh
python3 scripts/encoder_stage_profile.py summarize \
  profile-data/runs/<run-id>/records.jsonl \
  --output profile-data/runs/<run-id>/baseline.json
```

Do not compare baseline files across commits unless encoder binary hashes,
dataset hashes, method/quality, backend environment, and machine class match.
