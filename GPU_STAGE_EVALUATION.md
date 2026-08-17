# Additional encoder stages: GPU suitability

## Scope and decision rule

This is a structural assessment of the current encoder at
`v1.6.0-221-g4fe551df` plus the initial Metal migration. It intentionally
contains no new timing results. Item 1's stage profiler must establish the
remaining hot stages before any candidate advances on performance grounds.

A candidate is acceptable only if it either preserves the CPU bitstream or has
an explicitly approved quality/size contract. Device work must be synchronous
at the current encoder call sites, caller-owned outputs must remain unchanged
unless the operation succeeds, and a decline or recoverable failure must run
the existing CPU implementation.

Scores below range from 1 (poor) to 5 (strong). `Movement` scores the amount of
useful computation relative to host/device traffic; `amortization` assumes a
warm pipeline but calls out where resident or fused buffers are required.

## Modern pipeline map

The public `WebPEncode()` entry selects one of two substantially different
pipelines.

Lossless (`VP8LEncodeImage` / `VP8LEncodeStream`):

1. Analyze colors, palette eligibility, entropy transform, and transform tile
   sizes. Method 6 / quality 100 may create many crunch configurations.
2. Optionally sort and encode a palette, then map pixels to palette indices.
3. Apply subtract-green, choose predictor modes and tile sampling, apply the
   predictor residuals, then search/apply cross-color transforms.
4. For each chosen configuration, fill the hash chain; create LZ77/RLE/box
   backward references and choose color-cache behavior.
5. Build local histograms, combine/remap them, build canonical Huffman codes,
   and serialize transform data, trees, and image symbols.
6. With `thread_level > 0`, whole crunch configurations can run in two CPU
   workers. The smallest completed stream wins.

Lossy (`WebPEncode` / `VP8EncLoop` or `VP8EncTokenLoop`):

1. Convert ARGB to YUVA (regular or SharpYUV) and clean transparent samples.
2. Initialize macroblocks, analyze segment complexity and assign segments.
3. Run one or more statistics/rate-control passes. Each macroblock performs
   intra-mode search, transforms, quantization, reconstruction, and rate-
   distortion scoring while probability state is periodically finalized.
4. Run the final macroblock/token pass, update prediction boundaries and loop-
   filter statistics in raster order, encode alpha (optionally in parallel),
   and serialize the frame headers and partitions.

The initial migration already accelerates lossless cross-color search,
lossless hash candidates (with CPU replay), and regular opaque RGB-to-YUV.
Those are baselines rather than new candidates here.

## Candidate ranking

| Rank | Candidate boundary | Movement | Parallelism | Sync | Determinism | Quality | Amortization | Decision |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Lossless predictor search plus residual application | 3 | 5 | 4 | 5 | 5 | 4 | Prototype exact residual application now; investigate fixed-point tile histograms/search next. |
| 2 | Lossless near-lossless preprocessing | 4 | 5 | 4 | 5 | 5 | 4 | Strong local stencil/multi-pass candidate, but require byte-for-byte CPU preprocessing output before enabling. |
| 3 | Lossy macroblock mode/RD batches | 4 | 4 | 2 | 4 | 5 | 5 | Highest compute potential, but only after separating immutable per-MB trials from raster-order context/probability commits. |
| 4 | Lossless histogram construction and cost precomputation | 3 | 4 | 3 | 5 | 5 | 3 | Flatten refs and accelerate exact counts/costs only; retain stochastic/greedy merge and tie order on CPU initially. |
| 5 | Palette mapping | 2 | 5 | 5 | 5 | 5 | 2 | Exact and easy, but low arithmetic intensity and only applies to <=256-color images. Prefer fusion/resident input. |
| 6 | Subtract-green as a standalone dispatch | 1 | 5 | 5 | 5 | 5 | 1 | Do not dispatch alone. Fuse into a resident predictor/cross-color chain. |
| 7 | Huffman construction and bitstream serialization | 1 | 1 | 1 | 5 | 5 | 1 | Keep on CPU; small/global/order-sensitive work is a poor device boundary. |

`Sync` is high when the stage needs few/global barriers and low when host or
cross-workgroup coordination is intrinsic.

### 1. Predictor transform

The expensive selector evaluates 14 exact integer predictors for each tile,
accumulates 4x256-bin residual histograms across several tile sizes, and makes
deterministic mode decisions using accumulated histograms and fixed-point
entropy. Pixel residual generation for a fixed predictor map is much simpler:
every output reads immutable left/top/top-left/top-right source pixels and one
small mode-map entry, then performs exact byte-lane arithmetic.

The included experiment implements only that final application boundary. It
de-risks all 14 predictor formulas, row/tile boundaries, bitstream identity,
and commit/fallback semantics without pretending that it accelerates the full
selector. Standalone movement is one 4-byte source upload, a small mode-map
upload, and one 4-byte result download per pixel. Its likely long-term value is
as the terminal kernel of a device-resident predictor search, followed by
fused subtract-green/cross-color work.

Near-lossless residual quantization and the non-`exact` cleanup of fully
transparent pixels mutate prediction context in scan order. The experiment
declines those cases rather than weakening output equivalence.

### 2. Near-lossless preprocessing

`VP8ApplyNearLossless()` performs up to five 4-neighbor stencil passes. Each
pass can use separate input/output buffers, making pixels independent within a
pass and preserving the exact CPU banker's rounding and threshold tests.
Quality is intentionally changed by this stage, so acceptance still requires
the GPU's preprocessed ARGB to equal the CPU buffer byte-for-byte; merely
meeting a PSNR threshold is not sufficient.

### 3. Lossy macroblock work

Transforms, quantization, reconstruction, and mode scoring are compute-heavy,
fixed-point operations over many small blocks. A useful boundary must batch
many macroblocks; dispatching individual 4x4/16x16 DSP calls cannot amortize
submission. Exact mode scores and tie order can preserve the stream, but the
current iterator also carries left/top prediction state, non-zero contexts,
probability refreshes, filter statistics, and rate-control passes. A safe first
step is GPU evaluation of candidate trials with CPU selection/commit in raster
order, analogous to hash candidates plus CPU replay.

### 4. Histograms

Raw local histogram construction and independent histogram costs can use exact
integer atomics/reductions. The linked `VP8LBackwardRefs` representation first
needs a deterministic flattened command stream, adding movement. Stochastic
and greedy combination mutate a global queue/set with order-sensitive equal-
cost decisions; they should remain on CPU until an exact replay protocol is
designed.

## Predictor-residual experiment

The released cold end-to-end matrix is now complete. All six input/method
median strata regressed by 0.8--3.9%, with a 30--40 ms median absolute penalty
and 37/42 slower close pairs. Correctness and transactional fallback passed,
but the standalone stage is rejected for promotion and retained only as a
default-off correctness/reference path. The inclusive predictor profile still
motivates selector/fused research; it does not overturn the residual result.
See
[doc/experiment-series-analysis-20260817.md](doc/experiment-series-analysis-20260817.md).

The experiment is isolated from the normal Metal build and disabled twice:

- build with `WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1` (CMake) or
  `WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1` (the Unix makefile);
- run with `WEBP_METAL_PREDICTOR=1`.

`WEBP_METAL_PREDICTOR_MIN_PIXELS` defaults to 1,048,576 and may be set to `0`
for correctness tests. `WEBP_METAL_PREDICTOR_VALIDATE=1` computes the existing
C predictor functions into a private reference buffer and compares every
residual before committing the Metal output. Validation mismatch, device
failure, unsupported semantics, or
`WEBP_METAL_PREDICTOR_FAIL_AFTER_DISPATCH=1` leaves `argb` untouched and runs
`CopyImageWithPrediction()`.

The experiment's call is private and synchronous. It deliberately does not
reuse the color-transform request. When promoted, a versioned extension of the
backend-neutral interface should gain a new `LOSSLESS_PREDICTOR_RESIDUAL` stage
bit and a typed
request containing width, height, predictor bits, borrowed mode map, exact/
near-lossless semantics, and borrowed mutable ARGB. Backend descriptors should
advertise this stage independently. A later fused/resident design should be a
separate capability, not an implicit change to this request's ownership.

## Correctness and acceptance gates

Build and smoke validation:

```sh
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 examples/cwebp examples/dwebp
WEBP_METAL_PREDICTOR=1 \
scripts/test_predictor_metal_experiment.sh examples/test_ref.ppm
```

Before promotion, run the same script on opaque photographic, graphic, odd-
dimension, single-row/column, and alpha-bearing corpora. Acceptance requires:

1. internal CPU reference equality for every dispatched residual;
2. byte-identical CPU/accelerated WebP streams for methods 0 through 6;
3. identical streams over at least three fresh-process repetitions;
4. decoded pixels identical to the CPU reference (lossless quality is exact);
5. injected post-dispatch failure and all declined cases byte-identical to the
   CPU fallback;
6. sanitizer/fuzzer coverage of dimensions, modes, and boundary pixels;
7. later performance results showing positive end-to-end median speedup with
   no material p95 regression above the selected crossover threshold.

## Historical benchmark protocol

The operator later ran this cold protocol under the serialized benchmark lease.
It is retained for provenance, not as an instruction to rerun without a new
release:

```sh
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 examples/cwebp examples/dwebp
WEBP_METAL_PREDICTOR=1 scripts/test_predictor_metal_experiment.sh \
  /absolute/path/to/corpus/mitski.png \
  /absolute/path/to/corpus/corgi.jpeg \
  /absolute/path/to/corpus/siamese.jpg
mkdir -p benchmark-results/item5
WEBP_METAL_PREDICTOR=1 WEBP_BENCHMARK_SESSION=exclusive RUNS=7 \
scripts/benchmark_predictor_metal_experiment.sh \
  benchmark-results/item5/predictor-cold.csv \
  /absolute/path/to/corpus/mitski.png \
  /absolute/path/to/corpus/corgi.jpeg \
  /absolute/path/to/corpus/siamese.jpg
```

This produces 84 alternating fresh-process observations (3 images x 2 methods
x 2 variants x 7 runs), including lazy compilation in the experimental arm.
Allow roughly 10 minutes on an Apple M4-class laptop, plus build time; it uses
one CPU encode and the system Metal GPU at a time and needs less than 2 GiB of
free memory for this corpus. Warm in-process stage and end-to-end measurements
should use item 1's profiling driver after that commit is integrated; do not
infer warm crossover behavior from this fresh-process CSV.
