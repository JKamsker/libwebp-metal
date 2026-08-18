# CUDA experiment decision summary

This is the short decision ledger. Consult it before the raw captures in
`CUDA_EXPERIMENT_RESULTS_RAW.md`. Measurements are from 2026-08-18 on an
NVIDIA GeForce RTX 2080 SUPER with CUDA Toolkit 12.0. Results are specific to
that hardware and workload.

## Decisions

| Strategy | Measured result | Decision |
|---|---:|---|
| Cross-color shared source tile | Lab: 1.9585x faster than its matched control. Production kernel: 7.8% faster at 1024x1024 and 8.1% faster at 2048x2048. | Integrated with actual-size dynamic shared memory; enabled by default. |
| Cross-color warp-private histograms | 0.4734x control speed, or 2.11x slower. | Removed. |
| Cross-color parallel score/entropy reduction | 0.2174x control speed, or 4.60x slower. | Removed. Atomic reduction and extra synchronization overwhelmed the work saved. |
| Combined specialized color kernel | 0.2512x control speed, or 3.98x slower. | Removed. This was confounded by also enabling the losing warp/parallel paths, so specialization alone remains unproven. |
| Warp-cooperative hash matching | 0.2446x scalar speed, or 4.09x slower. | Removed. The lane-per-match mapping wasted work on the short matches in this corpus. |
| Four-context pool | 0.992494 ms/iteration versus 0.721941 ms serial: 0.7274x control speed, or 37.5% slower. | Removed. Extra streams, buffers, and smaller launches lost to the simple serial path. |
| Resident lossless pipeline | 0.419031 ms/iteration versus 2.822457 ms with equivalent stage round trips: 6.74x faster. | Retained as the highest-priority pipeline experiment; production semantics and ownership still need implementation. |
| Predictor search/residual prototype | 7.607895 ms/20 iterations versus 155.654056 ms CPU: 20.46x faster. | Retained only as a feasibility experiment; it implements three modes rather than the production selector's full 14-mode search and entropy policy. |
| SharpYUV-style iterative kernel | 0.168858 ms/iteration versus 6.690596 ms CPU: 39.62x faster. | Retained as a high-priority feasibility experiment; it is not the complete public SharpYUV algorithm. |
| Near-lossless stencil | Lab: 38.49x faster. Exact production: 4.24x–23.45x faster at the retained 256x256 warm threshold, depending on pass count. | Integrated with exact CPU semantics, a 65,536-pixel warm threshold, and a quality-aware 16,777,216-pixel cold gate. Cold one/two-pass work stays on CPU. |
| Lossless histogram construction | 14.491450 ms/20 iterations versus 41.601797 ms CPU: 2.87x faster. | Retained only as a feasibility experiment; it still does not consume the encoder's real flattened backward references. |
| Batched lossy macroblock scoring | 0.791020 ms/iteration versus 1.772970 ms CPU: 2.24x faster. | Retained as a feasibility experiment; raster-order state and CPU commit remain unresolved. |
| CUDA graphs plus double buffering | 0.766127 ms/iteration versus 0.768430 ms with direct launches: 1.0030x, a noise-level 0.3%. The simpler serial path was faster than either. | Removed. No material graph benefit at this launch count, and buffering added overhead. |

All original and follow-up benchmark rows produced stable expected checksums.
The active lab no longer builds rejected implementations; their code was
removed, while their measurements remain in the raw artifact.

The matched CPU-control follow-ups used 20 setup-inclusive iterations in each
of five fresh runs. Predictor, SharpYUV, near-lossless, histogram, and lossy
scoring GPU medians above use the same work and checksum as their paired CPU
cases. These ratios justify continued integration work, but only near-lossless
currently reproduces the complete production algorithm.

## Production shared-tile follow-up

The first production port reserved a fixed 16 KiB shared tile. It regressed the
real color kernel from about 2.31 ms to 4.58 ms at 1024x1024 and was discarded.
Allocating only the actual tile size (normally 4 KiB at method 4) recovered
occupancy and produced the retained result:

| Size | Existing kernel median | Dynamic shared-tile median | Kernel change |
|---:|---:|---:|---:|
| 1024x1024 | 2.347 ms | 2.163 ms | 7.8% faster |
| 2048x2048 | 8.217 ms | 7.551 ms | 8.1% faster |

Each cell contains 35 warm kernel samples across five deterministic inputs.
Encoded hashes were identical between builds for every matched sample. Median
1024x1024 checks at methods 2 and 6 also improved the kernel by 8.0% and 2.1%,
respectively; method 0 did not dispatch the color stage for this workload.
Median paired full-encode results were 0.9% slower at 1024x1024 and 2.6% slower
at 2048x2048, with large CPU-side variance and a color-kernel share below 1% of
the full encode. Therefore the evidence supports a kernel improvement but does
not claim a measurable end-to-end gain or justify changing crossover
thresholds.

The optimization is independently removable with
`WEBP_CUDA_ENABLE_COLOR_SHARED_TILE=OFF`.

## Production near-lossless follow-up

The exact implementation passed 20 direct CPU/CUDA parity cases spanning all
five pass counts, varied dimensions, non-contiguous source strides, repeat
determinism, and transactional decline. All 1,560 benchmark rows retained
matched output hashes.

The public encoder call site was also exercised with the deterministic
3000x2000 texture corpus at five passes. CUDA dispatch occurred and the CPU and
CUDA encoders produced byte-identical WebP output.

Warm CUDA won every measured case. The retained 256x256 minimum avoids the
noise-level 64x64 one-pass result; measured speedups there were 23.45x for five
passes, 14.93x for three passes, and 4.24x for one pass. At 4096x4096 the warm
speedups were 13.70x, 8.35x, and 2.65x, respectively.

Cold initialization invalidated the original quality-blind 4-million-pixel
proposal. At 2048x2048 only five passes barely won (1.09x). At 4096x4096, five
and three passes won by 2.99x and 1.83x, while one pass was still 1.76x slower.
The retained default requires 16,777,216 pixels and at least three passes when
the backend is cold. An explicit `WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS` value
remains a force/ablation override for every pass count.

## Evidence locations

- `CUDA_EXPERIMENT_RESULTS_RAW.md`: original 75-row capture plus matched
  lifecycle and stage-control follow-ups.
- `CUDA_NEAR_LOSSLESS_RESULTS_RAW.md`: 1,560 direct production rows plus warm
  and cold crossover medians.
- `CUDA_ACCELERATION_EXPERIMENTS.md`: active lab build and measurement protocol.
- `CUDA_BENCHMARK_RESULTS.md`: production encoder crossover and strategy context.
