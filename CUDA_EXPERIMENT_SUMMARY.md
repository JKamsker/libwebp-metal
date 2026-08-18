# CUDA experiment decision summary

This is the short decision ledger. Consult it before the raw captures in
`CUDA_EXPERIMENT_RESULTS_RAW.md`. Measurements are from 2026-08-18 on an
NVIDIA GeForce RTX 2080 SUPER with CUDA Toolkit 12.0. Results are specific to
that hardware and workload.

## Decisions

| Strategy | Measured result | Decision |
|---|---:|---|
| Cross-color shared source tile | Historical lab ratio invalid: its control copied full histograms and reduced on the CPU. Production kernel: 7.8% faster at 1024x1024 and 8.1% faster at 2048x2048. | Integrated from the valid production A/B with actual-size dynamic shared memory; enabled by default. |
| Cross-color warp-private histograms | Historical control ratio invalid because transfer and reduction work differed. | Removed; no valid matched performance claim is retained. |
| Cross-color parallel score/entropy reduction | Historical control ratio invalid because transfer and reduction work differed. | Removed; atomic reduction and synchronization remain unpromising, but the old ratio is not evidence. |
| Combined specialized color kernel | Historical control ratio invalid and also confounded by the warp/parallel paths. | Removed; specialization alone remains unproven. |
| Warp-cooperative hash matching | 0.2446x scalar speed, or 4.09x slower. | Removed. The lane-per-match mapping wasted work on the short matches in this corpus. |
| Four-context pool | 0.992494 ms/iteration versus 0.721941 ms serial: 0.7274x control speed, or 37.5% slower. | Removed. Extra streams, buffers, and smaller launches lost to the simple serial path. |
| Resident lossless pipeline | 0.419031 ms/iteration versus 2.822457 ms with equivalent stage round trips: 6.74x faster. | Retained as the highest-priority pipeline experiment; production semantics and ownership still need implementation. |
| Predictor search/residual prototype | 7.607895 ms/20 iterations versus 155.654056 ms CPU: 20.46x faster. | Retained only as a feasibility experiment; it implements three modes rather than the production selector's full 14-mode search and entropy policy. |
| SharpYUV-style iterative kernel | 0.168858 ms/iteration versus 6.690596 ms CPU: 39.62x faster. | Retained as a high-priority feasibility experiment; it is not the complete public SharpYUV algorithm. |
| Near-lossless stencil | Lab: 38.49x faster. Exact production: 4.24x–23.45x faster at the retained 256x256 warm threshold, depending on pass count. | Integrated with exact CPU semantics, a 65,536-pixel warm threshold, and a quality-aware 16,777,216-pixel cold gate. Cold one/two-pass work stays on CPU. |
| Lossless histogram construction prototype | 14.491450 ms/20 iterations versus 41.601797 ms CPU: 2.87x faster. | Retained as historical feasibility evidence only; it did not consume the encoder's production-linked backward references. |
| Exact production full-stream histogram counts | Correctness: direct multi-span, cache, literal, copy, prefix-boundary, repeat, invalid-command, and transactional-decline tests pass; isolated CPU/CUDA streams are byte-identical for methods 0–6. Timing (2026-08-18, RTX 5070 Ti Laptop): forced-threshold single-process A/B across the sixteen-case corpus matrix was neutral within noise (7,799 ms off vs 7,841 ms on in aggregate, mixed per-case signs). | Integrated behind `WEBP_CUDA_HISTOGRAM=1`; entropy estimation, local distance-remapped histograms, merging, and Huffman construction remain on CPU. Stays off by default: population counting is a small share of the CPU histogram stage and no profitable crossover was found. |
| Batched lossy macroblock scoring | 0.791020 ms/iteration versus 1.772970 ms CPU: 2.24x faster. | Retained as a feasibility experiment; raster-order state and CPU commit remain unresolved. |
| Exact production lossy macroblock analysis | Correctness-only implementation; byte-identical CPU/CUDA lossy streams across every method 0–6, qualities 25/75/95, and odd dimensions. The RGB stage hands packed device YUV directly to analysis when ownership/geometry match, eliminating the intervening upload. No timing has been collected. | Integrated behind `WEBP_CUDA_LOSSY_ANALYSIS=1`; portable E2E suite now requires both lossy stages during forced rows and records the handoff policy. Keep off by default until measured. |
| Fused production lossy import and analysis | Correctness-only implementation; forced CUDA output is byte-identical to CPU at method/quality pairs 0/25, 4/75, and 6/95, and odd-dimension verification passes. RGB conversion and exact analysis launch on one stream with one completion boundary, and the later callback consumes an identity-matched cached result. No timing has been collected. | Integrated behind `WEBP_CUDA_FUSED_LOSSY_ANALYSIS=1` and the two underlying lossy stage flags. Keep off by default until a new portable E2E result set proves a useful crossover. |
| Production cross-color → main-hash resident handoff | Correctness: a dedicated device copy survives the intervening transform-map encode; the main hash request reuses it only when host pointer, pixel count, and row width match, and forced batches remain byte-identical with and without reuse. Timing (2026-08-18, RTX 5070 Ti Laptop): single-process lossless encodes were up to 17% faster (photo content) and never slower across the six-case A/B. | Enabled by default; `WEBP_CUDA_RESIDENT_LOSSLESS=0` disables it. The portable forced suite records observed handoff counts as row evidence. |
| Parallel production predictor policy | Superseded: independent per-tile scoring measurably collapsed to the no-op predictor on photographic content (mode 0 on 74% of tiles, up to +22% compressed size). Replaced by guided row-sequential selection: tile rows launch in stream order and score all 14 modes against the accumulated residual histogram of previous rows with double-precision costs and fixed-order reductions, matching the CPU cost model. Decoded pixels are identical; total compressed corpus size is about 1% smaller than the CPU selector. Windows RTX 5070 Ti E2E: PNG lossless batches moved from 1.37x to about 2x and JPEG lossless batches from 1.20x to about 4.9x. | Enabled by default with 4,000,000 cold / 16,384 warm pixel thresholds; `WEBP_CUDA_PREDICTOR=0` disables it. Near-lossless quantization and non-exact transparent inputs still decline to the CPU. |
| Near-lossless predictor selection (modes-only) | Non-exact quantized selection replays the CPU's per-tile reconstruction recurrence on the device (one replay thread per tile and mode over shared-memory tiles) and returns only the mode image; the CPU applies the prediction, so the near-lossless error bound is honored exactly (measured max deviation identical to CPU at strength 40) with sizes within about 2%. Windows RTX 5070 Ti singles including cold start: photo near-lossless 1370 -> 547 ms and 1710 -> 537 ms. Deterministic across runs. | Integrated behind the predictor stage flag via the ABI v8 modes-only contract; exact requests keep the full select-and-apply path. |
| CUDA graphs plus double buffering | 0.766127 ms/iteration versus 0.768430 ms with direct launches: 1.0030x, a noise-level 0.3%. The simpler serial path was faster than either. | Removed. No material graph benefit at this launch count, and buffering added overhead. |

All original and follow-up benchmark rows produced stable expected checksums.
The historical color rows remain raw evidence, but their ratios are not matched
comparisons because the baseline transferred and reduced different data. The
active lab now separates that histogram-throughput case and gives the matched
baseline a device reduction plus the same score transfer as the shared-tile
case. Rejected implementations remain removed.

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

## Persistent CUDA batch follow-up

The batch benchmark measured six PNG or JPEG inputs (three content types at
small and medium sizes), quality 75, method 4, and near-lossless 40. These
are persistent-process, forced-stage runs with page-cached `/tmp` file I/O;
they do not justify lowering production cold thresholds.

| Format | Mode | Batch 6 CPU/CUDA total ms | Batch 6 speedup | Batch 24 CPU/CUDA total ms | Batch 24 speedup |
|---|---|---:|---:|---:|---:|
| PNG | lossy | 602.791 / 614.401 | 0.9811x | 2445.182 / 2477.368 | 0.9870x |
| PNG | lossless | 847.751 / 619.866 | 1.3676x | 3389.177 / 2460.732 | 1.3773x |
| PNG | near-lossless | 1246.506 / 965.494 | 1.2911x | 4869.623 / 3911.262 | 1.2450x |
| JPEG | lossy | 619.277 / 613.559 | 1.0093x | 2433.595 / 2405.487 | 1.0117x |
| JPEG | lossless | 3988.384 / 3535.765 | 1.1280x | 16023.908 / 14449.061 | 1.1090x |
| JPEG | near-lossless | 4820.437 / 4241.282 | 1.1366x | 18673.450 / 16503.490 | 1.1315x |

CUDA is worthwhile for persistent lossless and near-lossless batches; lossy
is effectively neutral. Batch sizes 6 and 24 have no material per-image
throughput difference after warmup. Fresh per-image CUDA processes lost to CPU
because each launch paid CUDA initialization:

| Format | Mode | Fresh CPU/CUDA six-process median ms | Speedup |
|---|---|---:|---:|
| PNG | lossy | 645.322 / 1880.912 | 0.3431x |
| PNG | lossless | 948.875 / 2101.623 | 0.4515x |
| PNG | near-lossless | 2134.368 / 3158.435 | 0.6758x |
| JPEG | lossy | 648.090 / 1865.276 | 0.3475x |
| JPEG | lossless | 4388.008 / 5253.948 | 0.8352x |
| JPEG | near-lossless | 3323.956 / 5163.455 | 0.6437x |

All 120 persistent rows and 360 fresh rows were stable; all 180 fresh
validation pairs passed decoded parity, including 60/60 exact lossy outputs.
The complete raw rows and validation records are in
`CUDA_BATCH_RESULTS_RAW.md`.

Production action: lossy RGB-to-YUV CUDA is now opt-in through
`WEBP_CUDA_LOSSY=1`. One-shot encodes retain cold thresholds. Persistent
lossless callers may advertise `WEBP_CUDA_BATCH_SIZE` and
`WEBP_CUDA_BATCH_PIXELS`; conservative defaults require 6 images and
6,000,000 pixels for lossless or 5 images and 5,000,000 pixels for
near-lossless before the first item may use warm dispatch thresholds. The
portable `scripts/benchmark_cuda_end_to_end.py` suite reproduces this
PNG/JPEG matrix on other systems and emits `raw.jsonl`, `results.json`, and
the four-column human-readable `report.md`.

## Evidence locations

- `CUDA_EXPERIMENT_RESULTS_RAW.md`: original 75-row capture plus matched
  lifecycle and stage-control follow-ups.
- `CUDA_NEAR_LOSSLESS_RESULTS_RAW.md`: 1,560 direct production rows plus warm
  and cold crossover medians.
- `CUDA_ACCELERATION_EXPERIMENTS.md`: active lab build and measurement protocol.
- `CUDA_BENCHMARK_RESULTS.md`: production encoder crossover and strategy context.
- `CUDA_BATCH_RESULTS_RAW.md`: persistent and fresh-process batch rows,
  validation records, and computed medians.
- `scripts/benchmark_cuda_end_to_end.py`: portable cross-system runner and
  report generator for the same PNG/JPEG lifecycle matrix.
