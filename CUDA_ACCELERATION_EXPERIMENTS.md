# CUDA acceleration experiments

This lab implements the computational core of the follow-up CUDA ideas without
changing the shipping encoder. It is non-installed, opt-in, and intentionally
kept outside the private accelerator ABI until measurements justify promoting a
path. Every GPU result is checked against a deterministic CPU oracle before it
can be benchmarked.

The current decisions and concise measurements are in
`CUDA_EXPERIMENT_SUMMARY.md`. Rejected implementations have been removed from
the active runner; their original raw rows remain preserved in
`CUDA_EXPERIMENT_RESULTS_RAW.md`.

## Implemented cases

| Idea | Experiment names | What is exercised |
|---|---|---|
| Cross-color redesign | `color_baseline`, `color_shared_tile` | Matched per-tile transform histogram control and the retained shared-pixel strategy |
| Device-resident lossless pipeline | `staged_lossless_pipeline`, `resident_lossless_pipeline` | Matched per-stage round-trip control and one-upload pipeline across predictor residuals, subtract-green, cross-color, and hash-signature generation |
| Predictor search/residuals | `predictor_search_residual_cpu`, `predictor_search_residual` | Matched CPU/GPU batched tile mode scoring followed by residual generation |
| SharpYUV | `sharpyuv_iterative_cpu`, `sharpyuv_iterative` | Matched CPU/GPU fixed-point 2x2 RGB-to-YUV conversion with four chroma correction iterations |
| Near-lossless preprocessing | `near_lossless_stencil_cpu`, `near_lossless_stencil` | Matched CPU/GPU three-pass four-neighbor quantization stencil |
| Lossless histograms | `lossless_histogram_cpu`, `lossless_histogram` | Matched CPU/GPU construction of literal, channel, and distance token histograms |
| Lossy macroblock scoring | `lossy_macroblock_scoring_cpu`, `lossy_macroblock_scoring` | Matched CPU/GPU SSD evaluation of four intra16 candidates per macroblock |

The SharpYUV case is a fixed-point iterative workload shaped like the production
algorithm, not a drop-in implementation of every public `SharpYuvConvert` mode.
The resident pipeline uses a deterministic candidate signature rather than the
encoder's complete backward-reference policy. These boundaries are deliberate:
the experiments answer whether the GPU execution strategy is promising before
the much larger integration and policy-compatibility work is undertaken.

## Build and correctness check

```sh
cmake -S . -B build-cuda-experiments \
  -DWEBP_ENABLE_CUDA=ON \
  -DWEBP_BUILD_CUDA_ACCELERATION_EXPERIMENTS=ON
cmake --build build-cuda-experiments \
  --target cuda_acceleration_experiments --parallel
build-cuda-experiments/cuda_acceleration_experiments --verify
```

Or run `scripts/test_cuda_acceleration_experiments.sh`. Verification performs no
timing loop. The executable exits nonzero on a CUDA error or oracle mismatch.

## Measurement protocol

Do not mix correctness failures with timing results. The `--benchmark` mode
automatically runs an untimed CPU-oracle preflight for each selected case, then
prints raw CSV. Its time is end-to-end wall time: one allocation/setup and final
download per case, amortized across the requested kernel iterations.

Use a release build, record `nvidia-smi` and compiler information, allow the GPU
to become idle, and collect at least five independent runs. A suggested raw-data
capture is:

```sh
nvidia-smi > CUDA_EXPERIMENT_RESULTS_RAW.md
nvcc --version >> CUDA_EXPERIMENT_RESULTS_RAW.md
for run in 1 2 3 4 5; do
  printf '\nrun=%s\n' "$run" >> CUDA_EXPERIMENT_RESULTS_RAW.md
  build-cuda-experiments/cuda_acceleration_experiments \
    --benchmark --iterations 100 >> CUDA_EXPERIMENT_RESULTS_RAW.md
done
```

Interpret the retained color cases, staged/resident pipeline cases, and each
`_cpu`/GPU pair as matched controls. Keep raw output unedited; put conclusions
in a separate section after the captured data. These controls compare the
experiment workloads, not complete production stages; the summary ledger
records the remaining semantic gaps.
