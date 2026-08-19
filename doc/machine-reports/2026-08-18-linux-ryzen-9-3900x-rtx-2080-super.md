# CUDA end-to-end benchmark: Ryzen 9 3900X / RTX 2080 SUPER

Measured on 2026-08-18--19 UTC. Times are median milliseconds per image and
speedup is CPU time divided by CUDA time, so values above `1x` favor CUDA.

## Machine and build

| Item | Value |
|---|---|
| CPU | AMD Ryzen 9 3900X, 12 cores / 24 threads |
| GPU | NVIDIA GeForce RTX 2080 SUPER, 8 GiB |
| NVIDIA driver | 595.84 |
| OS | Linux 6.8.0-137-generic, x86-64, glibc 2.39 |
| CUDA toolkit | 12.0.140 |
| Compiler | GCC 13.3.0 / NVCC 12.0.140 |
| Python / Pillow | Python 3.12.3 / Pillow 10.2.0 |
| Source revision | `af921388b3abcac4efd61efb7a80a8f72e5777b7` |
| Build | CMake Release, CUDA enabled |
| Result label | `win-2080super-i4-diagonal` |

## Protocol

The repository's portable `benchmark_cuda_end_to_end.py` suite generated the
canonical six-image publication corpus in PNG and JPEG form. Encodes used
quality 75, method 4, and near-lossless strength 40. The CUDA side forced all
eligible stages for a matched CPU/CUDA hardware comparison; these numbers do
not describe the adaptive production dispatch policy.

Persistent measurements used a 24-item process, one discarded warmup, and
five measured samples. Non-batched measurements started a fresh `cwebp`
process for each image and therefore include CUDA context initialization and
process teardown. File data was page-cached unless affected by normal host
activity.

Command:

```sh
python3 scripts/benchmark_cuda_end_to_end.py run \
  --build-dir build-cuda \
  --output-dir /tmp/libwebp-cuda-results-2080super-i4-diagonal \
  --label "win-2080super-i4-diagonal"
```

## Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 92.4 ms | 40.0 ms | **2.31x** |
| PNG lossless | 143.5 ms | 92.5 ms | **1.55x** |
| PNG near-lossless | 210.7 ms | 92.2 ms | **2.28x** |
| JPEG lossy | 92.3 ms | 40.2 ms | **2.30x** |
| JPEG lossless | 684.7 ms | 146.7 ms | **4.67x** |
| JPEG near-lossless | 799.8 ms | 147.4 ms | **5.42x** |

## Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 95.6 ms | 261.2 ms | **0.37x** |
| PNG lossless | 154.4 ms | 313.0 ms | **0.49x** |
| PNG near-lossless | 221.5 ms | 322.9 ms | **0.69x** |
| JPEG lossy | 97.0 ms | 261.0 ms | **0.37x** |
| JPEG lossless | 705.2 ms | 359.6 ms | **1.96x** |
| JPEG near-lossless | 817.4 ms | 376.1 ms | **2.17x** |

## Validation and interpretation

All six persistent preflight cases and all 180 single-image validation pairs
passed. Lossy CPU/CUDA encodes were required to be byte-identical; lossless
and near-lossless encodes were required to decode to identical pixels. Forced
lossless cases also verified that the requested resident CUDA handoff occurred.

CUDA improved every persistent-batch row. In a fresh process, CUDA startup
cost outweighed the accelerated work for all PNG rows and JPEG lossy, while
the longer JPEG lossless and near-lossless encodes remained faster on CUDA.

## Adaptive dispatch calibration

An isolated warm/cold crossover re-check found that the lossy decimate
thresholds tuned on the RTX 5070 Ti dispatched too early on this Turing GPU.
Across three deterministic inputs, warm CUDA first won at 448x448 (784
macroblocks), while cold CUDA first won at 1792x1792 (12,544 macroblocks).
The defaults were raised from 64/4,000 to 784/12,544 macroblocks. Cross-color,
predictor, and three-pass near-lossless won at their existing warm and cold
decision points, so their pixel thresholds remain unchanged.

## Nsight decimate finding

A representative interior `DecimateKernel` diagonal spent 93.82% of scheduler
cycles with no eligible warp. CTA barriers accounted for 58.7% of the 16.29
cycle issue interval; achieved occupancy was 12.5%, DRAM throughput was 0.49%,
and only about ten threads per warp were active. The 16-step I4 recurrence and
its four barriers per step therefore explain the device floor. Splitting the
ten residual walks over two warps left the kernel duration flat and regressed
PNG end-to-end time, so that experiment was removed.

## CPU analysis and overlap experiment

Encoder-stage profiling on the production CUDA path measured the serial CPU
lossy-analysis stage at 10.0--12.0 ms per 1600x1200 image. Median stage times
over 24 measured encodes per content class were:

| Input family | Total | CPU analysis | CUDA decimate |
|---|---:|---:|---:|
| PNG graphic | 50.3 ms | 11.8 ms | 34.8 ms |
| PNG photo | 61.6 ms | 10.4 ms | 37.8 ms |
| PNG texture | 126.3 ms | 10.0 ms | 58.8 ms |
| JPEG graphic | 50.2 ms | 12.0 ms | 34.4 ms |
| JPEG photo | 59.3 ms | 10.8 ms | 36.9 ms |
| JPEG texture | 124.2 ms | 10.0 ms | 59.7 ms |

A two-worker batch-tool prototype attempted to overlap analysis of image N+1
with the encode of image N. Its first PNG pass improved 100.4 to 81.1
ms/image, but the reference hash changed from `b274cb32eed00ca3` to
`c942d229bf5104f7`, output bytes changed from 11,300,544 to 16,895,686, and
the next pass failed the deterministic-output check. The prototype was
removed. Concurrent calls require an explicit design that isolates or safely
schedules shared CUDA encoder state before this overlap can be used.

## Trellis decimation

The whole-pass CUDA decimator was extended from method 4's basic RD search to
method 5 selected-mode trellis and method 6 all-candidate trellis. The
canonical small+medium corpus used 12-image persistent batches with two timing
samples per backend; every PNG and JPEG CPU/CUDA output was byte-identical.

| Method | Input | CPU time | CUDA time | CUDA speedup |
|---|---|---:|---:|---:|
| Method 5 | PNG | 109.6 ms | 76.2 ms | **1.44x** |
| Method 5 | JPEG | 111.8 ms | 77.2 ms | **1.45x** |
| Method 6 | PNG | 249.0 ms | 84.4 ms | **2.95x** |
| Method 6 | JPEG | 260.6 ms | 86.2 ms | **3.03x** |

On the three canonical 1600x1200 PNG content classes, method 5 measured
192.4 ms CPU versus 114.1 ms CUDA (**1.69x**), while method 6 measured
435.3 ms CPU versus 125.3 ms CUDA (**3.47x**). A focused 513x517 RGBA test
also covers quality 75/99, one/two-pass encodes, alpha, and transactional CPU
fallback after a deliberately failed collect.

## Parallel macroblock prediction follow-up

A sub-profile attributed 92.8--92.9% of the decimator's thread-0 setup cycles
to serial luma16/chroma8 prediction-plane generation. Filling those independent
pixels across all 128 CTA threads, while retaining exact serial DC sums,
improved five-round alternating-process method-4 medians from 57.337 to
53.668 ms/image PNG and 58.074 to 54.784 ms/image JPEG. Output hashes and byte
counts matched in every sample.

The complete portable suite was repeated with label `win-2080super` and the
candidate batch binary explicitly relinked:

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 97.1 ms | 53.0 ms | **1.83x** |
| JPEG lossy — batch | 97.0 ms | 53.3 ms | **1.82x** |
| PNG lossy — fresh process | 99.3 ms | 275.9 ms | **0.36x** |
| JPEG lossy — fresh process | 100.4 ms | 274.1 ms | **0.37x** |

All 180 official validation pairs passed. A separate 105-case exact-byte
battery covered methods 2--6, qualities 25/75/98, 17x13 tiny and 257x255 odd
inputs across three content classes, and forced band-3 fallback for every
method/content pair. The focused trellis/fallback, concurrency, histogram, and
near-lossless tests also passed.

## Audited four-lane intra4 transform result

After the CUDA acceleration audit remediation, four adjacent lanes were used
per I4 mode for the forward transform, basic quantization, and inverse
transform. The complete official suite was repeated from revision `5d841ba0`.

### Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 99.4 ms | 50.0 ms | **1.99x** |
| PNG lossless | 143.1 ms | 92.3 ms | **1.55x** |
| PNG near-lossless | 209.1 ms | 93.1 ms | **2.25x** |
| JPEG lossy | 99.4 ms | 49.6 ms | **2.00x** |
| JPEG lossless | 681.4 ms | 146.4 ms | **4.65x** |
| JPEG near-lossless | 802.4 ms | 148.3 ms | **5.41x** |

### Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 101.7 ms | 269.5 ms | **0.38x** |
| PNG lossless | 155.5 ms | 317.0 ms | **0.49x** |
| PNG near-lossless | 221.3 ms | 324.1 ms | **0.68x** |
| JPEG lossy | 100.6 ms | 270.4 ms | **0.37x** |
| JPEG lossless | 703.2 ms | 362.3 ms | **1.94x** |
| JPEG near-lossless | 812.2 ms | 383.0 ms | **2.12x** |

Relative to the preceding same-machine official CUDA batch medians, PNG lossy
improved from 53.0 to 50.0 ms/image and JPEG lossy from 53.3 to 49.6 ms/image.
All 180 suite validation pairs and the additional 105-case exact lossy battery
passed. Exact CI run `32212085424` passed all eleven jobs.

## Parallel intra4 score preparation

A temporary subphase profile found that serial I4 score selection and commit
consumed 36--42% of measured I4 cycles, more than the 23--27% transform and
quantization interval. Revision `8ae71f74` prepares each mode's header, base,
and full scores on ten parallel lanes, while thread 0 retains the exact ordered
comparison and tie behavior and copies only the final winning levels.

Five alternating baseline/candidate processes, each retaining three samples
after one warmup, improved PNG from 51.625 to 49.787 ms/image and JPEG from
50.667 to 49.148 ms/image. The complete official suite measured:

### Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 99.8 ms | 48.6 ms | **2.06x** |
| PNG lossless | 151.1 ms | 92.1 ms | **1.64x** |
| PNG near-lossless | 206.5 ms | 93.7 ms | **2.20x** |
| JPEG lossy | 99.7 ms | 48.6 ms | **2.05x** |
| JPEG lossless | 673.6 ms | 146.7 ms | **4.59x** |
| JPEG near-lossless | 790.8 ms | 147.2 ms | **5.37x** |

### Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 101.1 ms | 262.8 ms | **0.38x** |
| PNG lossless | 154.0 ms | 312.4 ms | **0.49x** |
| PNG near-lossless | 220.2 ms | 327.4 ms | **0.67x** |
| JPEG lossy | 100.7 ms | 269.8 ms | **0.37x** |
| JPEG lossless | 700.8 ms | 365.4 ms | **1.92x** |
| JPEG near-lossless | 812.4 ms | 384.3 ms | **2.11x** |

All 180 official validation pairs, six registered CTests, and an additional
105 exact-byte cases across methods 2--6, qualities 25/75/98, tiny and odd
dimensions, three content classes, and band-3 fallback passed. Exact code CI
run `32214115280` passed all eleven jobs.

## Local-state token-page arithmetic coding

After the GPU work reduced decimation, the current encoder-stage profile put
texture token emission at 45--46 ms/image. `gprofng` clock sampling attributed
81.2% of sampled CPU time inclusively to `VP8EmitTokens`. Plain table-driven
inlining was measurable but below the retention threshold. Revision
`4852f92e` instead keeps the arithmetic coder's `range`, `value`, and
`nb_bits` in locals across each token page, committing them to the writer only
when the unchanged byte-flush path is required.

Five alternating baseline/candidate processes, each retaining three samples
after one warmup, measured PNG 48.646 to 44.735 ms/image and JPEG 49.576 to
44.544 ms/image. Every one of the 60 samples retained the same output hash and
byte count.

### Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 94.4 ms | 44.3 ms | **2.13x** |
| PNG lossless | 143.9 ms | 90.2 ms | **1.59x** |
| PNG near-lossless | 209.8 ms | 92.6 ms | **2.27x** |
| JPEG lossy | 93.9 ms | 44.0 ms | **2.13x** |
| JPEG lossless | 679.3 ms | 145.6 ms | **4.66x** |
| JPEG near-lossless | 792.0 ms | 148.3 ms | **5.34x** |

### Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 97.6 ms | 263.1 ms | **0.37x** |
| PNG lossless | 155.2 ms | 321.4 ms | **0.48x** |
| PNG near-lossless | 222.5 ms | 328.6 ms | **0.68x** |
| JPEG lossy | 97.3 ms | 264.2 ms | **0.37x** |
| JPEG lossless | 702.2 ms | 366.6 ms | **1.92x** |
| JPEG near-lossless | 819.8 ms | 379.4 ms | **2.16x** |

The suite passed all 180 validation pairs. Six registered CTests and an
additional 105 exact-byte cases covering methods 2--6, qualities 25/75/98,
three content classes, 17x13 and 257x255 dimensions, and forced band-3
fallback also passed. Exact CI run `32217152201` passed all eleven jobs.

## Local-state in-page byte flushing

A new whole-process profile after `4852f92e` attributed 42.92% of exclusive
CPU samples to `Flush`, 29.39% to `VP8PutTokenPage`, and 22.55% to coefficient
token recording. Revision `9a44518a` keeps the output-buffer state local while
coding a token page and emits the unchanged carry and pending-run bytes inline
when capacity is already available. Buffer growth and allocation failure still
use the original `Flush` / `BitWriterResize` path.

Five order-balanced baseline/candidate processes, each with one warmup and
three retained 24-image samples, measured:

| Format | `4852f92e` baseline | In-page byte flushing | Change |
|---|---:|---:|---:|
| PNG lossy | 44.299 ms/image | 41.843 ms/image | **-2.456 ms** |
| JPEG lossy | 44.317 ms/image | 42.017 ms/image | **-2.300 ms** |

Every one of the 60 outputs retained its reference hash and byte count. The
complete official suite measured:

### Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 92.0 ms | 41.6 ms | **2.21x** |
| PNG lossless | 142.5 ms | 92.4 ms | **1.54x** |
| PNG near-lossless | 210.5 ms | 92.6 ms | **2.27x** |
| JPEG lossy | 92.6 ms | 41.7 ms | **2.22x** |
| JPEG lossless | 694.7 ms | 146.2 ms | **4.75x** |
| JPEG near-lossless | 808.1 ms | 146.8 ms | **5.51x** |

### Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 97.7 ms | 266.1 ms | **0.37x** |
| PNG lossless | 154.4 ms | 316.6 ms | **0.49x** |
| PNG near-lossless | 221.3 ms | 328.0 ms | **0.67x** |
| JPEG lossy | 96.5 ms | 270.0 ms | **0.36x** |
| JPEG lossless | 690.0 ms | 362.7 ms | **1.90x** |
| JPEG near-lossless | 799.8 ms | 382.3 ms | **2.09x** |

The `win-2080super-fast-flush` suite passed all 180 validation pairs; its raw
result is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/official-fast-flush-results.json`.
Seven registered CTests and an additional 105 exact-byte cases across methods
2--6, qualities 25/75/98, tiny and odd inputs, three content classes, and
forced band-3 fallback passed. Exact CI run `32221803146` passed all eleven
jobs.

## Wavefront launch bound and I4 warp balancing

An `nvprof` trace of the production method-4 1600x1200 photo path recorded 248
anti-diagonal kernels. Their execution time summed to 29.926 ms; the span from
the first launch to the final completion was 30.215 ms. All inter-kernel gaps
therefore totaled only 0.288 ms, with a 1.168 us mean and 1.760 us maximum.
Deleting every gap could not meet the 1.5 ms/image retention threshold, so
CUDA graph capture and cooperative persistent launch were not implemented.

The retained four-lane I4 transform packed eight mode groups into warp 0 and
two into warp 1. A byte-exact candidate instead distributed them 3/3/2/2 over
the existing four warps and removed the prediction-to-transform CTA barrier.
All seven focused CTests passed. Five order-balanced baseline/candidate
processes, each with one warmup and three retained 24-image samples, measured:

| Format | Baseline | Balanced groups | Change |
|---|---:|---:|---:|
| PNG lossy | 41.954 ms/image | 41.703 ms/image | -0.251 ms |
| JPEG lossy | 41.881 ms/image | 41.709 ms/image | -0.172 ms |

All 60 outputs retained their reference hash and byte count. Both gains were
far below the retention threshold, so the code change was removed. The local
raw timing summary is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-balanced-ab.json`.

## Combined residual-cost table

An exact candidate folded the fixed coefficient-level costs into the 68 hot
entries of each probability-dependent table. This reduced the common residual
cost from two dependent loads to one, while levels above 67 retained the
original fixed-cost fallback. The probability-dependent table grew from 13 to
26 KiB and `DecimateKernel` register use rose from 93 to 109.

All seven focused CTests passed. Five order-balanced processes per variant,
with one warmup and three retained 24-image samples, measured:

| Format | Baseline | Combined level costs | Change |
|---|---:|---:|---:|
| PNG lossy | 41.854 ms/image | 43.433 ms/image | +1.579 ms |
| JPEG lossy | 41.727 ms/image | 42.939 ms/image | +1.213 ms |

All 60 outputs retained their reference hash and byte count. The larger table
and wider addressing outweighed the saved load, so the candidate was removed.
The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/combined-level-cost-ab.json`.

## Small-level residual-cost specialization

A compact follow-up used the exact VP8 fixed costs directly for levels 0–4,
avoiding their fixed-table load without changing table size or the kernel's
93-register footprint. All seven focused CTests passed. Five order-balanced
processes per variant measured:

| Format | Baseline | Small-level specialization | Change |
|---|---:|---:|---:|
| PNG lossy | 41.851 ms/image | 42.423 ms/image | +0.572 ms |
| JPEG lossy | 41.712 ms/image | 42.392 ms/image | +0.680 ms |

All 60 outputs retained their reference hash and byte count. The added range
test outweighed the saved load, so the candidate was removed. The local raw
summary is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/small-level-cost-ab.json`.

## Coefficient-major I4 residual mirror

The ten scalar I4 residual walks originally read coefficient `n` from
mode-major level arrays at a 32-byte stride. A candidate added a 320-byte
coefficient-major shared-memory mirror, populated without a new barrier, to
make those simultaneous reads contiguous. All seven focused CTests passed;
all 60 outputs retained their reference hashes and byte counts. Kernel
registers stayed at 93 and static shared memory increased from 17,912 to
18,232 bytes. Five order-balanced process medians measured:

| Format | Baseline | Coefficient-major mirror | Change |
|---|---:|---:|---:|
| PNG lossy | 41.765 ms/image | 41.918 ms/image | +0.153 ms |
| JPEG lossy | 41.582 ms/image | 41.994 ms/image | +0.412 ms |

The extra shared writes and footprint outweighed the read-layout improvement,
so the candidate was removed. The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/residual-transpose-ab.json`.

## Two-token boolean-coder loop unroll

Current whole-process profiles attributed 54.0--54.3% of sampled CPU time to
`VP8PutTokenPage`. A GCC-only candidate unrolled its exact coder loop twice;
disassembly confirmed two token bodies per back-edge. All seven focused CTests
passed and all 60 timed outputs matched between variants. Five order-balanced
process medians measured:

| Format | Baseline | Two-token unroll | Change |
|---|---:|---:|---:|
| PNG lossy | 41.968 ms/image | 41.950 ms/image | -0.018 ms |
| JPEG lossy | 42.004 ms/image | 41.958 ms/image | -0.046 ms |

The gains are effectively zero, so the larger generated loop was removed. The
local raw summary is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/token-unroll-ab.json`.

## Phase-aliased decimate workspace

The I16, I4, and UV scratch arrays have disjoint barrier-delimited lifetimes.
A POD union reduced `DecimateKernel` static shared memory from 17,912 to
11,704 bytes, raising the Turing residency ceiling from three to five CTAs/SM;
registers rose from 93 to 96. All seven focused CTests passed and all 60 timed
outputs matched. Direct medium-texture GPU wall moved from 28.48 to about
28.97 ms. Five order-balanced process medians measured:

| Format | Baseline | Aliased workspace | Change |
|---|---:|---:|---:|
| PNG lossy | 42.108 ms/image | 42.193 ms/image | +0.085 ms |
| JPEG lossy | 41.889 ms/image | 42.070 ms/image | +0.182 ms |

The sparse wavefront did not benefit from the additional theoretical
occupancy, so the candidate was removed. The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/phase-union-ab.json`.

## Compact I4 reconstruction scratch

A compact 4-byte row layout replaced the 32-byte-strided 4x4 I4 output
scratch, removing row-write and cross-mode metric bank aliases. Exact
stride-aware SSE/Hadamard helpers reduced static shared memory from 17,912 to
16,792 bytes with registers unchanged at 93. All seven focused CTests passed
and all 60 timed outputs matched. Five order-balanced process medians measured:

| Format | Baseline | Compact I4 output | Change |
|---|---:|---:|---:|
| PNG lossy | 41.866 ms/image | 42.004 ms/image | +0.139 ms |
| JPEG lossy | 41.918 ms/image | 41.971 ms/image | +0.053 ms |

The added stride-aware metric work offset the bank-layout improvement, so the
candidate was removed. The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-compact-output-ab.json`.

## Whole-I4 lower-bound pruning

An exact lower bound skipped the complete I4 search when its mandatory flag
and minimum possible 16-block mode cost could not beat I16 or satisfy the
header limit. All seven focused CTests passed and all 60 timed outputs matched.
Graphic-medium device wall improved from 28.25 to 23.97 ms, but photo and
texture were unchanged. Five order-balanced aggregate medians measured:

| Format | Baseline | I4 lower-bound pruning | Change |
|---|---:|---:|---:|
| PNG lossy | 41.943 ms/image | 41.803 ms/image | -0.140 ms |
| JPEG lossy | 41.869 ms/image | 41.784 ms/image | -0.085 ms |

The aggregate gains are far below the retention threshold, so the candidate
was removed. The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-lower-bound-ab.json`.

## Local token-flush capacity tracking

An exact token-page candidate kept remaining output capacity local instead of
recomputing `max_pos - pos` at every byte flush. The unchanged resize fallback
preserved exact partial state under injected allocation failure. All seven
focused CTests passed and all 60 timed outputs matched. Five order-balanced
medians measured:

| Format | Baseline | Local capacity | Change |
|---|---:|---:|---:|
| PNG lossy | 42.131 ms/image | 42.083 ms/image | -0.048 ms |
| JPEG lossy | 42.095 ms/image | 41.945 ms/image | -0.150 ms |

The gains are far below the retention threshold, so the candidate was
removed. The local raw summary is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/token-available-ab.json`.

## Dual-sub-block I4 dependency diagonals

The retained scheduler replaces the sixteen serial Intra4 sub-block steps
with the ten exact `x + 2y` dependency diagonals. Two independent 128-thread
teams can evaluate the two blocks on a diagonal concurrently, while thread 0
still aggregates completed block scores in the CPU's raster order. Direct
boundary construction preserves the external top-right samples at the
macroblock edge.

`DecimateKernel` moved from 128 to 256 threads, 93 to 100 registers, and
17,912 to 23,392 bytes of static shared memory. On this Turing GPU that raises
the residency ceiling from 12 to 16 warps per SM. Direct method-4
medium-image device medians moved as follows:

| Content | Parent | Diagonal scheduler | Change |
|---|---:|---:|---:|
| Graphic | 28.665 ms | 21.788 ms | **-6.877 ms** |
| Photo | 24.897 ms | 22.038 ms | **-2.859 ms** |
| Texture | 23.525 ms | 20.935 ms | **-2.590 ms** |

Five order-balanced parent/candidate processes, each with one warmup and
three retained 24-image samples, produced these aggregate medians:

| Format | Parent | Diagonal scheduler | Change |
|---|---:|---:|---:|
| PNG lossy | 42.226 ms/image | 40.420 ms/image | **-1.806 ms** |
| JPEG lossy | 42.247 ms/image | 40.610 ms/image | **-1.637 ms** |

All 60 timed outputs matched their reference hashes and byte counts. Seven
focused CTests passed, as did a separate 105-case exact-byte matrix covering
methods 2--6, qualities 25/75/98, 17x13 and 257x255 inputs, three content
classes, and forced band-3 transactional fallback. The official suite then
passed all 180 validation pairs (including 60 exact lossy pairs) and produced
the tables at the top of this report. Raw official results are in
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/official-i4-diagonal-results.json`; the local A/B
summary is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-diagonal-ab.json`.

## I4 team-local named barriers

Temporary subphase timing on the retained diagonal scheduler captured over
96% of I4 cycles. Transform/quantization used 25.6--26.5%,
selection/publication 22.7--23.3%, metrics 21.7--24.0%, prediction/boundary
20.9--21.4%, and raster aggregation about 7%. A byte-exact candidate replaced
four per-diagonal CTA barriers with independent 128-thread named barriers,
leaving the two publication/abort barriers block-wide.

| Format | Parent | Team-local barriers | Change |
|---|---:|---:|---:|
| PNG lossy | 40.291 ms/image | 39.994 ms/image | -0.297 ms |
| JPEG lossy | 40.210 ms/image | 39.892 ms/image | -0.318 ms |

All 60 order-balanced timing outputs matched. The gains are far below the
1.5 ms/image retention threshold, so the candidate was removed. Raw evidence
is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-team-barrier-ab.tsv`.

## Local-state coefficient-token recording

A texture-medium CPU profile attributed 58.2% of samples to
`VP8PutTokenPage` and 36.7% to `VP8RecordCoeffTokens`. Keeping the active
token-page pointer and capacity local across each coefficient block preserved
exact output and allocation-failure behavior but did not improve end-to-end
time:

| Format | Parent | Local record state | Change |
|---|---:|---:|---:|
| PNG lossy | 40.186 ms/image | 40.485 ms/image | +0.299 ms |
| JPEG lossy | 40.241 ms/image | 40.392 ms/image | +0.151 ms |

All 60 order-balanced timing outputs matched. The candidate was removed. Raw
evidence is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/token-record-local-ab.tsv` and the CPU
profile is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/gprof-i4-diagonal-replay.tar.gz`.

## Eight-lane basic I4 quantization

Widening basic I4 quantization from four to eight lanes per mode halved each
lane's coefficient loop while retaining the exact four-lane transforms and
method-6 trellis chain. It was byte-exact but neutral:

| Format | Parent | Eight-lane quantizer | Change |
|---|---:|---:|---:|
| PNG lossy | 40.163 ms/image | 40.202 ms/image | +0.040 ms |
| JPEG lossy | 40.366 ms/image | 40.088 ms/image | -0.279 ms |

All 60 order-balanced outputs matched. The candidate was removed; raw
evidence is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-quant8-ab.tsv`.

## Cold coefficient-statistics renormalization

The retained CPU profile attributed 36.7% of samples to
`VP8RecordCoeffTokens`. Generated code for its inlined statistics update took
a forward branch around probability-count renormalization on every recorded
event even though renormalization is rare. A compiler branch-probability hint
moved that exceptional path out of line and made the common increment
fall-through, but the end-to-end result regressed:

| Format | Parent | Cold renormalization | Change |
|---|---:|---:|---:|
| PNG lossy | 40.363 ms/image | 40.440 ms/image | +0.077 ms |
| JPEG lossy | 40.227 ms/image | 40.528 ms/image | +0.301 ms |

The focused trellis test passed and all 60 order-balanced outputs matched.
The candidate was removed; raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/recordstats-hint-ab.jsonl`.

## Branchless token-probability selection

The current whole-process profile attributed 58.2% of CPU samples to
`VP8PutTokenPage`. A candidate unconditionally loaded the indexed probability
and used a register conditional move for fixed-probability tokens, removing
the token-type branch from the generated boolean-coder loop. Fixed tokens use
only low indices 0--255, so the speculative indexed load remained in bounds.

| Format | Parent | Branchless selection | Change |
|---|---:|---:|---:|
| PNG lossy | 40.521 ms/image | 40.400 ms/image | -0.121 ms |
| JPEG lossy | 40.362 ms/image | 40.188 ms/image | -0.174 ms |

The bit-writer and trellis tests passed and all 60 order-balanced outputs
matched. Both gains are far below the 1.5 ms/image threshold, so the candidate
was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/tokenprob-branchless-ab.jsonl`.

## Split singleton I4 diagonals

Four of the ten retained I4 dependency diagonals contain one sub-block and
normally leave the second 128-thread team idle. A candidate split those
blocks' ten prediction modes 5/5 across both teams, retained global mode
comparison order, and used the existing per-team scratch. The necessary
cross-team publication outweighed the parallel work:

| Format | Parent | Split singleton | Change |
|---|---:|---:|---:|
| PNG lossy | 40.219 ms/image | 40.537 ms/image | +0.318 ms |
| JPEG lossy | 40.263 ms/image | 40.525 ms/image | +0.262 ms |

The full CUDA trellis parity test passed and all 60 order-balanced outputs
matched. The candidate was removed; raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-singleton-split-ab.jsonl`.

## I16 warp reductions

The non-trellis I16 phase used 64 contending atomics for nonzero flags and up
to 128 contending 64-bit atomics for SSE and texture distortion per
macroblock. An exact candidate replaced them with four independent 16-lane
warp reductions and one shared-memory writer per mode.

| Format | Parent | Warp reductions | Change |
|---|---:|---:|---:|
| PNG lossy | 40.283 ms/image | 39.850 ms/image | -0.433 ms |
| JPEG lossy | 40.405 ms/image | 39.870 ms/image | -0.535 ms |

The full CUDA trellis parity test passed and all 60 order-balanced outputs
matched. The gains are below the 1.5 ms/image threshold, so the candidate was
removed. Raw evidence is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i16-warp-reduce-ab.jsonl`.

## Cooperative I16 forward transforms

An exact candidate mapped the 64 I16 forward transforms across all 256 CTA
lanes using the retained four-lane separable transform. It reused the
not-yet-populated I16 level arrays for bounded row intermediates, so shared
memory and occupancy were unchanged.

| Format | Parent | Cooperative transform | Change |
|---|---:|---:|---:|
| PNG lossy | 40.309 ms/image | 40.374 ms/image | +0.065 ms |
| JPEG lossy | 40.377 ms/image | 40.307 ms/image | -0.071 ms |

The full CUDA trellis parity test passed and all 60 order-balanced outputs
matched. The candidate was removed; raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i16-coop-forward-ab.jsonl`.

## Cooperative I16 quantization with warp reductions

A final I16 candidate combined the measured metric warp reductions with
four-lane basic quantization for all 64 mode/block pairs. It remained exact,
but cooperative quantization added no measurable gain beyond the separately
measured reductions:

| Format | Parent | Quantize + reduce | Change |
|---|---:|---:|---:|
| PNG lossy | 40.271 ms/image | 39.840 ms/image | -0.431 ms |
| JPEG lossy | 40.126 ms/image | 39.602 ms/image | -0.525 ms |

The full CUDA trellis parity test passed and all 60 order-balanced outputs
matched. The combination remains below the 1.5 ms/image threshold and was
removed. Raw evidence is `evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i16-quant-reduce-ab.jsonl`.

## Forced-inline I4 metrics

Forcing the scalar 4x4 SSE and Hadamard metric helpers inline preserved exact
output but did not improve a two-process order-balanced screen: PNG was flat
(40.323 vs. 40.316 ms/image) and JPEG regressed (40.095 vs.
40.552 ms/image). The candidate was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-metric-inline-ab.jsonl`.

## Cooperative I4 metrics

Four-lane groups computed the per-mode SSE and Hadamard metrics in parallel,
reusing expired transform scratch for the exact Hadamard transpose. The full
trellis parity test passed, but a two-process order-balanced screen was
neutral: PNG moved from 40.247 to 40.316 ms/image and JPEG from 40.298 to
40.379 ms/image. The candidate was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-coop-metrics-screen.jsonl`.

## Seeded I4 residual-cost bound

An exact candidate evaluated the earliest minimum-base-score mode first, then
skipped parallel residual walks whose nonnegative cost could not beat that
seed (including exact earlier-mode tie handling). The serial seed and extra
synchronization dominated: PNG regressed from 40.891 to 42.457 ms/image and
JPEG from 40.429 to 42.520 ms/image in a two-process screen. The trellis
parity test and all 24 timed outputs matched. The candidate was removed. Raw
evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-rcost-bound-screen.jsonl`.

## Static I4 prediction dispatch

The four retained prediction leaders used a static schedule of direct mode
calls instead of invoking the runtime mode dispatcher 2--3 times per leader.
The trellis parity test and all 24 screen outputs matched. PNG improved from
40.414 to 39.608 ms/image and JPEG from 40.463 to 39.690 ms/image, but both
~0.8 ms gains remain below the 1.5 ms/image threshold. The candidate was
removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-static-pred-screen.jsonl`.

## Parallel I4 boundary plus static prediction

The static prediction schedule was combined with a 13-lane gather of the
exact left, top-left, top, and top-right boundary samples, reusing the existing
CTA barrier. Trellis parity and all 24 screen outputs matched. PNG moved from
40.774 to 40.233 ms/image and JPEG from 40.779 to 40.065 ms/image; both gains
remain below 1.5 ms/image, so the candidate was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-boundary-pred-screen.jsonl`.

## Static I4 prediction plus warp-parallel winner publication

The static prediction schedule was combined with scalar-only score selection
and a 16-lane winner copy. This attacks separate prediction and publication
portions of the I4 dependency loop without increasing the CTA size. The full
CUDA trellis parity test passed, and all 24 order-balanced screen outputs
matched their baseline hash and byte count.

| Format | Parent | Combined candidate | Change |
|---|---:|---:|---:|
| PNG lossy | 40.370 ms/image | 38.850 ms/image | -1.520 ms |
| JPEG lossy | 40.441 ms/image | 39.103 ms/image | -1.338 ms |

The PNG result barely crossed 1.5 ms/image, but JPEG did not, and an earlier
screen put both gains near 1.36 ms/image. The improvement therefore did not
robustly clear the retention threshold across the two target formats, so the
candidate was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-static-pred-warp-commit-screen.jsonl`.

## Shuffle-transposed I4 transforms

An exact candidate packed each four-lane transform row into two 32-bit
registers and replaced both shared-memory transposes and their inner warp
barriers with eight width-four shuffle operations. This removed 1,280 bytes
of shared scratch. The corrected implementation passed the full CUDA trellis
parity test, and all 24 order-balanced screen outputs matched their baseline
hash and byte count, but shuffle cost on Turing outweighed the saved shared
traffic:

| Format | Parent | Shuffle transpose | Change |
|---|---:|---:|---:|
| PNG lossy | 40.446 ms/image | 41.096 ms/image | +0.650 ms |
| JPEG lossy | 40.368 ms/image | 41.104 ms/image | +0.736 ms |

The candidate was removed. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-shuffle-transpose-screen.jsonl`.

## Composite I4 dispatch/publication and I16 reductions

Three independently exact but subthreshold changes were combined: static
direct I4 prediction calls, scalar-only I4 score selection with a 16-lane
winner copy, and 16-lane I16 nonzero/SSE/distortion reductions. This was
measured only on the RTX 2080 SUPER; no cross-architecture performance claim
is made.

Preliminary sm_75-cubin screens looked promising, but the build directory had
not been configured with the handoff's required
`CMAKE_CUDA_ARCHITECTURES=native`. After rebasing onto `fa078ac0`, both an
isolated parent and candidate were rebuilt as confirmed native `sm_75` cubins.
Two independent five-process, order-balanced runs produced these medians:

| Run | Format | Parent | Composite | Change |
|---|---|---:|---:|---:|
| Native 1 | PNG lossy | 40.493 ms/image | 38.934 ms/image | -1.559 ms |
| Native 1 | JPEG lossy | 40.338 ms/image | 39.233 ms/image | -1.105 ms |
| Native 2 | PNG lossy | 40.383 ms/image | 39.104 ms/image | -1.279 ms |
| Native 2 | JPEG lossy | 40.227 ms/image | 38.850 ms/image | -1.377 ms |
| Combined 10-process median | PNG lossy | 40.435 ms/image | 39.068 ms/image | **-1.368 ms** |
| Combined 10-process median | JPEG lossy | 40.259 ms/image | 38.951 ms/image | **-1.309 ms** |

All 120 native timing outputs matched their parent hashes and byte counts.
The candidate also passed all seven focused CTests and a 105-case exact-byte
methods 2--6 / qualities 25--98 / tiny / odd / band-3 fallback matrix. A
provisional pre-rebase suite completed all 180 validation pairs, but its
timings are excluded because that build directory was not configured with
`native`. Both aggregate native gains remain below 1.5 ms/image, so the
candidate was removed.

Raw evidence is in
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-i16-combined-native-ab.jsonl`,
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-i16-combined-native-ab-rerun.jsonl`,
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-i16-combined-exact-matrix.jsonl`,
and
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-i16-combined-provisional-official-results.json`.
The preliminary screen and two pre-`native` A/Bs are retained alongside them
for auditability, but are not used for the decision.

## Four-row cooperative I4 prediction

A fresh retained-head profile measured PNG lossy at 90.11 ms/image CPU and
39.23 ms/image CUDA, and JPEG lossy at 88.10 and 38.83 ms/image. Device phase
timing put photo/texture I4 at 60.0--61.9% of block cycles. A candidate kept
the existing uniform 2--3-mode-per-warp assignment but used four aligned lanes
to generate one prediction row each, instead of filling every 4x4 prediction
from the warp leader.

The concurrency, histogram, trellis/fallback, and near-lossless tests passed.
Two order-reversed native-sm_75 processes produced six samples per cell:

| Format | Parent | Cooperative rows | Change |
|---|---:|---:|---:|
| PNG lossy | 40.303 ms/image | 40.987 ms/image | +0.684 ms |
| JPEG lossy | 40.231 ms/image | 40.894 ms/image | +0.664 ms |

All 24 timing outputs retained their parent hash and byte count. The candidate
was removed because both formats regressed. This was measured only on the RTX
2080 SUPER and makes no Ampere+ performance claim. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-cooperative-prediction-screen.jsonl`.
