# CUDA acceleration experiments

This lab implements the computational core of the follow-up CUDA ideas without
changing the shipping encoder. It is non-installed, opt-in, and intentionally
kept outside the private accelerator ABI until measurements justify promoting a
path. Every GPU result is checked against a deterministic CPU oracle before it
can be benchmarked.

## Implemented cases

| Idea | Experiment names | What is exercised |
|---|---|---|
| Cross-color redesign | `color_baseline`, `color_shared_tile`, `color_warp_histograms`, `color_parallel_entropy`, `color_specialized_kernel` | Per-tile transform histograms, shared pixel reuse, warp-private counters, parallel scoring, and compile-time specialization |
| Multiple CUDA contexts | `context_pool` | Four private non-blocking streams and staging buffers processing independent images concurrently |
| Device-resident lossless pipeline | `resident_lossless_pipeline` | One upload across predictor residuals, subtract-green, cross-color, and hash-signature generation |
| Predictor search/residuals | `predictor_search_residual` | Batched tile mode scoring followed by residual generation |
| Warp-cooperative hash matching | `hash_scalar`, `hash_warp_cooperative` | Scalar-thread and warp-cooperative exact match-length discovery |
| SharpYUV | `sharpyuv_iterative` | Fixed-point 2x2 RGB-to-YUV conversion with four chroma correction iterations |
| Near-lossless preprocessing | `near_lossless_stencil` | Three exact ping-pong passes of the four-neighbor quantization stencil |
| Lossless histograms | `lossless_histogram` | Parallel construction of literal, channel, and distance token histograms |
| Lossy macroblock scoring | `lossy_macroblock_scoring` | Batched SSD evaluation of four intra16 candidates per macroblock |
| Graphs and double buffering | `graphs_double_buffer` | Two pinned staging slots, private streams, instantiated graph reuse, and overlapped transfers |

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

Interpret only like-for-like pairs directly: the five color cases share one
checksum, as do scalar/warp hash. `context_pool`, `resident_lossless_pipeline`,
and `graphs_double_buffer` answer lifecycle/transfer questions and should also be
compared against the existing encoder-stage benchmark in
`CUDA_BENCHMARK_RESULTS.md`. Keep raw output unedited; put conclusions in a
separate section after the captured data.
