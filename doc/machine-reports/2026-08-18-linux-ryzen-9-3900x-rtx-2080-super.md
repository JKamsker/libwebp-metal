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

## Static I4 dispatch/commit plus token probability layout

The previously byte-exact static I4 prediction schedule, scalar-only score
scan, and 16-lane winner commit were combined with the CPU token branch layout
that makes the common dynamic probability lookup fall through. This tests
whether the known subthreshold GPU and CPU improvements become material
together without adding the previously rejected I16 reductions.

All seven CTests passed, including bit-writer growth/failure and CUDA
trellis/fallback coverage. A two-process screen appeared borderline at 1.599
ms/image PNG and 1.399 JPEG, so it was not used for a decision. The extended
five-process, order-balanced native-sm_75 gate measured:

| Format | Parent | Combined candidate | Change |
|---|---:|---:|---:|
| PNG lossy | 40.246 ms/image | 39.283 ms/image | -0.962 ms |
| JPEG lossy | 40.139 ms/image | 39.121 ms/image | -1.018 ms |

All 60 timing outputs retained the parent hash and byte count. Both gains are
below 1.5 ms/image, so the candidate was removed. This was measured only on
the RTX 2080 SUPER and makes no Ampere+ performance claim. Raw evidence is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-token-layout-combined-ab.jsonl`.

## Arithmetic token-range normalization

A fresh retained-head `gprofng` texture-batch profile attributed 60.10% of
sampled CPU time to `VP8PutTokenPage` and 36.26% to
`VP8RecordCoeffTokens`; all other named functions were below 1%. The two
normalization-table accesses were prominent instruction clusters. An exact
GCC/Clang candidate computed the shift from `clz(range + 1)` and reconstructed
the normalized range arithmetically, while retaining the tables for other
compilers. Disassembly confirmed that `bsr` and shifts replaced both loads.

The bit-writer growth/failure and CUDA trellis/fallback tests passed. Two
order-reversed native-sm_75 processes measured:

| Format | Parent | Arithmetic normalization | Change |
|---|---:|---:|---:|
| PNG lossy | 40.201 ms/image | 40.613 ms/image | +0.412 ms |
| JPEG lossy | 40.076 ms/image | 40.654 ms/image | +0.578 ms |

All 24 output hashes and byte counts matched. The candidate was removed. Raw
timing is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/token-arithmetic-normalization-screen.jsonl`;
the complete sampling experiment is
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/gprof-current-token-profile.tar.gz`.

## Retained wall-stage profile and chroma/I16 overlap

The aggregate CPU sampler above counts worker-thread CPU time, so a fresh
guarded, single-threaded wall-stage run profiled the retained native-sm_75
CUDA path directly. Each content class used a 24-image discarded warmup batch
and three measured 24-image batches at method 4 and quality 75. The 72 retained
records per class measured:

| Content | Encode total | CUDA decimate | Token emission | Token recording |
|---|---:|---:|---:|---:|
| Graphic | 25.845 ms | 20.620 ms | 0.583 ms | 0.184 ms |
| Photo | 31.656 ms | 21.727 ms | 2.750 ms | 0.177 ms |
| Texture | 76.342 ms | 51.895 ms | 10.959 ms | 0.195 ms |

This confirms that decimation, not the token loop, remains the serial wall
target on this machine. A scheduling-only candidate evaluated chroma modes in
the otherwise idle upper 128 CTA threads while the lower half performed I16
work. It did not change math, dispatch thresholds, or output order.

All seven CTests passed. Five order-balanced native-sm_75 processes measured:

| Format | Parent | Overlap candidate | Change |
|---|---:|---:|---:|
| PNG lossy | 39.973 ms/image | 38.574 ms/image | -1.399 ms |
| JPEG lossy | 40.002 ms/image | 38.910 ms/image | -1.093 ms |

All 60 timing outputs retained the parent hash and byte count. Both gains are
below the 1.5 ms/image retention threshold, so the candidate was removed. This
was measured only on the RTX 2080 SUPER and makes no Ampere+ performance claim.
The raw A/B records are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/chroma-i16-overlap-ab.jsonl`;
the six `retained-lossy-stage-*.jsonl` files in the same directory contain the
raw per-encode stage records and batch-harness outputs.

### Static-I4 composition follow-up

The exact static I4 prediction dispatch, scalar winner scan, and 16-lane
winner commit were next composed with chroma/I16 overlap. A first full
composition also included I16 warp reductions; all seven CTests passed and 60
timing outputs were byte-exact, but its five-process medians gained 1.603
ms/image PNG and only 1.332 JPEG.

Removing the I16 reductions left more lower-half work to overlap with chroma.
The lean composition passed the focused trellis/fallback test and was measured
in a second independently order-balanced five-process block because its first
JPEG result landed at 1.4985 ms/image. Combined medians across 30 samples per
cell were:

| Format | Parent | Lean composition | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.274 ms/image | 38.662 ms/image | 1.612 ms |
| JPEG lossy | 40.250 ms/image | 38.763 ms/image | 1.487 ms |

All 120 outputs retained the parent hash and byte count. JPEG remained 0.013
ms/image below the strict 1.5 ms gate, so the candidate was removed rather
than rounded into a win. This is RTX 2080 SUPER-only evidence. Raw records are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-i16-chroma-overlap-ab.jsonl`
and
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-chroma-overlap-ab.jsonl`.

An additional screen composed the lean GPU candidate with the previously
exact dynamic-token probability fall-through hint. All seven CTests passed
and all 24 outputs were byte-exact, but the gains were 1.867 ms/image PNG and
only 1.155 JPEG. Because the CPU hint reduced rather than increased the JPEG
gain, that variant was removed without a full gate. Raw records are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-chroma-token-fallthrough-screen.jsonl`.

### Balanced-I4/chroma composition follow-up

The lean GPU composition was then combined with the independently exact
four-warp I4 transform layout. Its 3/3/2/2 mode-group assignment removes the
prediction-to-transform CTA barrier while retaining the existing block size
and exact scalar comparison order. Two independent five-process,
order-balanced native-sm_75 blocks produced 30 samples per cell:

| Format | Parent | Balanced-I4/chroma | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.206 ms/image | 38.503 ms/image | 1.703 ms |
| JPEG lossy | 40.122 ms/image | 38.633 ms/image | 1.489 ms |

All 120 timed outputs matched their parent hashes and byte counts. All seven
focused CTests passed. A separate 105-case exact-byte ledger also passed,
covering methods 2--6, qualities 25/75/98, 17x13 tiny and 257x255 odd inputs
across photo/graphic/texture, plus band-3 fault fallback for every
method/content pair. JPEG remained 0.011 ms/image below the strict 1.5 ms
gate, so the candidate was removed rather than rounded into a win. This is
RTX 2080 SUPER-only evidence and makes no Ampere+ performance claim. The two
60-record timing blocks and the 105-record parity ledger are in the adjacent
evidence directory as `i4-balanced-chroma-overlap-ab-block1.jsonl`,
`i4-balanced-chroma-overlap-ab-block2.jsonl`, and
`i4-balanced-chroma-overlap-parity.jsonl`.

The next screen combined the lean candidate with the independently exact
team-local I4 barrier schedule. Four per-team numeric barriers used separate
128-thread named barriers; the two winner-publication and raster-order abort
points remained CTA-wide. All seven CTests and all 24 timed outputs were
exact. Two order-reversed native-sm_75 processes measured:

| Format | Parent | Team-barrier/chroma | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.341 ms/image | 38.356 ms/image | 1.984 ms |
| JPEG lossy | 40.213 ms/image | 38.815 ms/image | 1.398 ms |

JPEG failed the 1.5 ms screen, so the composition was removed without a full
gate. The result is specific to the RTX 2080 SUPER and makes no Ampere+
performance claim. Raw rows are in
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-team-barrier-chroma-screen.jsonl`.

The exact 13-lane I4 boundary gather was also composed with static prediction
dispatch, scalar winner selection, and the 16-lane winner copy. All seven
CTests and all 24 timed outputs were exact. Two order-reversed native-sm_75
processes measured:

| Format | Parent | Boundary/static/commit | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.374 ms/image | 39.817 ms/image | 0.557 ms |
| JPEG lossy | 40.365 ms/image | 39.129 ms/image | 1.236 ms |

Both gains are below the 1.5 ms gate, so the composition was removed without
a full run. This is RTX 2080 SUPER-only evidence. Raw rows are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-boundary-static-commit-screen.jsonl`.

A refreshed retained device trace measured I4 at 63.5% of photo and 65.4% of
texture block cycles. The next candidate used the fact that every full mode
score is its base score plus a non-negative residual cost: the exact ordered
scan therefore selects the earliest minimum full score. Warp 0 reduced that
argmin while retaining static dispatch and the validated 16-lane winner copy.

All seven CTests and all 24 timed outputs were exact. Two order-reversed
native-sm_75 processes measured:

| Format | Parent | Warp argmin/static/commit | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.112 ms/image | 38.871 ms/image | 1.241 ms |
| JPEG lossy | 40.027 ms/image | 39.203 ms/image | 0.824 ms |

Both gains are below the 1.5 ms gate, so the candidate was removed. Raw timing
rows and the refreshed device trace are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-warp-argmin-static-screen.jsonl`
and
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/retained-phase-refresh.txt`.

## Partition0/token-emission overlap

The retained eight-partition encoder emits independent token partitions on
eight CPU threads, then generates VP8 partition 0 serially. A host-scheduling
candidate first finalized the filter strength, launched all eight token
coders on workers, and generated partition 0 (headers and intra modes) on the
caller. The two operations share only finalized read-only encoder state. An
environment-off arm restored the previous schedule in the same binary.

Two order-reversed native-sm_75 processes, each with one warmup and six timed
samples per cell over the six small/medium PPM corpus images, measured:

| Parent | Partition0 overlap | Gain |
|---:|---:|---:|
| 32.301 ms/image | 31.228 ms/image | 1.073 ms/image |

All 24 aggregate timing records retained the same output hash
(`d01c3571a90d2653`) and byte count (1,610,422 bytes per six-image batch), and
all seven CTests passed. The gain is below the strict 1.5 ms/image retention
threshold, so the candidate was removed. This host result was measured only
on the Ryzen 9 3900X / RTX 2080 SUPER machine; it is not a cross-architecture
claim. Raw records are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/partition0-token-overlap-screen.jsonl`.

## Singleton-I4/chroma overlap

The I4 dependency schedule has four singleton diagonals (blocks 0, 1, 14,
and 15), where its upper 128-thread team is idle. A scheduling candidate used
those windows for the independent chroma transform, diffusion correction,
quantization/reconstruction/SSE, and residual-cost stages. If I4 aborted
before reaching a window, the original post-I4 path completed only the
remaining stages.

Two order-reversed native-sm_75 processes, each with one warmup and six timed
samples per cell over the six small/medium PPM corpus images, measured:

| Parent | Singleton-I4/chroma overlap | Gain |
|---:|---:|---:|
| 32.340 ms/image | 31.829 ms/image | 0.510 ms/image |

All 24 aggregate records retained the same output hash
(`d01c3571a90d2653`) and byte count (1,610,422 bytes per batch), and all seven
CTests passed. The singleton intervals hide only part of the chroma path, and
the gain is far below the 1.5 ms/image retention threshold, so the candidate
was removed. This is RTX 2080 SUPER-only evidence. Raw records are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/i4-singleton-chroma-overlap-screen.jsonl`.

## Lossless back-reference profile and workspace screen

A native-sm_75 lossless stage profile used the three 1600x1200 publication
cases at quality 75 and method 4. Each cell contains 21 in-process encodes; the
first encode was discarded and the table reports the median of the remaining
20. CUDA rows forced the retained predictor and hash stages. This original
profile did not set the separate `WEBP_CUDA_COLOR=1` opt-in, so its photo
cross-color boundary remained on the CPU; a corrected full-CUDA profile is
recorded below.

| Content | CPU total | CUDA total | CPU/CUDA backrefs | CPU/CUDA hash |
|---|---:|---:|---:|---:|
| graphic | 39.709 ms | 49.836 ms | 26.665 / 26.159 ms | 4.352 / 17.005 ms |
| photo | 371.541 ms | 283.196 ms | 89.987 / 83.312 ms | 33.289 / 22.491 ms |
| texture | 231.892 ms | 184.264 ms | 143.614 / 121.525 ms | 43.956 / 18.802 ms |

An exact substage recorder then decomposed the forced-CUDA back-reference
boundary. Median shares were 72.9% traceback for graphic; 48.4% cache search
and 33.7% traceback for photo; and 65.4% cache search plus 16.9% traceback for
texture. This identifies CPU work remaining after CUDA transform/hash dispatch;
it is not a GPU kernel timing or a cross-hardware result.

The existing default-off single-allocation `CostManager` workspace candidate
was screened because it had never received performance samples. Four
order-balanced process pairs per content each discarded the first of eleven
in-process encodes. Pairwise median results were:

| Content | Parent | Workspace | Parent - workspace |
|---|---:|---:|---:|
| graphic | 50.733 ms | 50.739 ms | -0.005 ms |
| photo | 287.039 ms | 286.659 ms | +1.164 ms |
| texture | 188.471 ms | 188.752 ms | -1.305 ms |

The table's parent/workspace columns are medians across the four process
medians; the decision uses the median of paired differences shown in the last
column. The graphic baseline and candidate bitstreams also have the identical
SHA-256 `be9d2ac71ab6b8c5ac3254431fde2c94b7c22f69af68acc60263715720429628`.
The implementation already has exhaustive exact-output and fault-fallback
coverage in its frozen research protocol. It was not promoted: graphic is
neutral, photo is below the 1.5 ms/image retention threshold, and texture
regresses. All stage, substage, A/B, build, and sample bitstream artifacts are
copied into the adjacent evidence directory.

## Retained parallel cache-bit search

The cache-search decomposition above exposed independent work across cache-bit
candidates. The retained implementation gives each candidate its own CPU
worker, histogram, and color-cache state. Candidate recurrences remain
ordered; after all workers finish, the caller scans integer entropy results in
ascending cache-bit order with the original strict comparison, preserving ties
and output exactly.

An unconditional screen improved photo and texture but regressed graphic by
3.248 ms/image from worker startup. The final pre-Ampere policy therefore
requires both a requested maximum of at least 8 cache bits and at least 32,768
reference commands. Small/medium isolated screens then measured median paired
gains of -0.446/-0.341 ms for graphic (noise), +1.980/+24.800 ms for photo,
and +4.243/+38.625 ms for texture.

The final architecture-aware build was measured in four order-balanced
process pairs. Each process used one discarded warmup and three measured
six-image batches:

| Format | CPU | CUDA serial | CUDA default | CUDA speedup | Paired CUDA gain |
|---|---:|---:|---:|---:|---:|
| PNG lossless | 140.082 ms | 91.820 ms | 77.319 ms | **1.81x** | 14.381 ms |
| JPEG lossless | 698.397 ms | 146.558 ms | 127.644 ms | **5.47x** | 19.406 ms |

Every serial/default CUDA process retained the same format-specific aggregate
hash (`eec6c490be6aaf6d` PNG, `06227eb38e0ac1e3` JPEG). A separate 42-case
matrix covered methods 2--6 at quality 75 and methods 4/6 at qualities 25/98
across small/medium graphic, photo, and texture inputs; all pairs were
byte-identical. The seven focused CTests passed, and a clean non-CUDA build
produced the same CPU smoke-test hash before and after the change.

This threshold and performance result are RTX 2080 SUPER/Turing evidence only.
The default remains off on Ampere-or-newer devices pending measurements there.
`WEBP_CUDA_PARALLEL_CACHE_SEARCH=0` disables the optimization; `=1` forces the
same structural gate for matched A/B work on another architecture. Raw stage
screens, final batch transcripts, parity hashes, build logs, CMake cache, and
CTest transcript are in the adjacent evidence directory.

## Post-cache profile and traceback-overlap rejection

A fresh native-sm_75 profile at retained commit `2ec39084` first repeated the
historical 1600x1200 protocol. It confirmed the intended CPU back-reference
reduction: photo moved from 83.312 to 58.252 ms and texture from 121.525 to
83.372 ms. The initially apparent 128.554 ms photo cross-color bottleneck was
not a CUDA result: lowering `WEBP_CUDA_MIN_PIXELS` does not enable the stage;
`WEBP_CUDA_COLOR=1` is a separate required opt-in.

The corrected full-CUDA pass explicitly enabled color, predictor, and hash:

| Content | Total | Cross-color | Predictor | Hash | Backrefs | Histogram |
|---|---:|---:|---:|---:|---:|---:|
| graphic | 50.184 ms | 0.000 ms | 0.000 ms | 16.994 ms | 26.547 ms | 1.630 ms |
| photo | 154.480 ms | 5.103 ms | 14.216 ms | 26.661 ms | 66.441 ms | 23.013 ms |
| texture | 149.897 ms | 0.000 ms | 0.000 ms | 18.902 ms | 83.343 ms | 18.616 ms |

CPU backward references therefore remain the dominant lossless boundary. A
candidate attempted to overlap cached and no-cache traceback passes while
preserving their original descending reduction and strict comparisons. Four
order-balanced batch-process pairs per format, with one warmup and three
measured samples, retained the exact aggregate hashes and byte counts but
measured only noise:

| Format | Control | Candidate | Paired control - candidate |
|---|---:|---:|---:|
| PNG lossless | 76.399 ms/image | 76.876 ms/image | -0.281 ms/image |
| JPEG lossless | 127.889 ms/image | 127.689 ms/image | +0.259 ms/image |

Inspection explained the non-result: method 4 never requests the no-cache
alternative, so the overlap did not dispatch. That option is selected only
for method 5 at quality 75 or above, or method 6 at quality 100. The candidate
was removed rather than retaining inactive code. These are RTX 2080 SUPER-only
measurements and make no Ampere+ claim. All 189 raw stage rows, verbose CUDA
dispatch output, native CMake cache, and 16 A/B transcripts are in the adjacent
evidence directory.

## Forced histogram diagnostic and cache-worker reuse

The portable batch harness forces the otherwise opt-in CUDA histogram counter.
The stage profiler was rebuilt with both native sm_75 and
`WEBP_CUDA_ENABLE_HISTOGRAM=ON`; a verbose 63-row pass observed 504 histogram
dispatches, eight per encode. Their device kernels averaged 0.179 ms, with a
maximum 1.249 ms for up to 1,920,000 commands, while the complete histogram
and clustering boundary remained 19--22 ms.

Four order-balanced same-binary on/off process pairs per 1600x1200 content
case, each with one warmup and six measured encodes, found:

| Content | Histogram off | Histogram forced | Paired off - forced |
|---|---:|---:|---:|
| graphic | 49.419 ms | 50.369 ms | -0.670 ms |
| photo | 146.147 ms | 135.098 ms | +11.037 ms |
| texture | 149.446 ms | 154.662 ms | -4.646 ms |

The measured histogram boundary itself was essentially unchanged; the
content-opposed total effects arose in later CPU work after earlier small
histogram calls. Counting is therefore not the entropy-stage bottleneck, and
this does not justify changing the production default or any Ampere+ policy.

A second candidate retained the ten cache-bit worker threads across multiple
cache searches inside one backward-reference call. It preserved the exact
candidate recurrence, synchronization, and integer reduction. Four
order-balanced forced-batch process pairs per format measured:

| Format | Recreate workers | Reuse workers | Paired recreate - reuse |
|---|---:|---:|---:|
| PNG lossless | 81.703 ms/image | 80.971 ms/image | +0.714 ms/image |
| JPEG lossless | 132.562 ms/image | 134.018 ms/image | -1.456 ms/image |

All 48 rows per format retained hashes `eec6c490be6aaf6d` (PNG) and
`06227eb38e0ac1e3` (JPEG) with unchanged byte counts. The candidate was removed:
PNG is below the 1.5 ms/image gate and JPEG materially regresses. These are
RTX 2080 SUPER-only measurements. The 294 raw profiler rows, verbose dispatch
transcript, native CMake cache, and 16 batch A/B transcripts are archived in
the adjacent evidence directory.

## Parallel raw-histogram cost rejection

The initial entropy-cost calculation for each raw histogram tile is independent
before the encoder compacts non-empty tiles in exact source order. A guarded
candidate split at least 4,096 raw histograms into 12 CPU jobs, then left
compaction, entropy bins, stochastic/greedy clustering, and remapping unchanged.
The environment override enabled the structural path only for matched A/B;
the proposed default remained pre-Ampere-only.

Four order-balanced forced-batch process pairs per format, each with one
warmup and three measured samples, produced:

| Format | Serial costs | Parallel costs | Paired serial - parallel |
|---|---:|---:|---:|
| PNG lossless | 76.224 ms/image | 76.475 ms/image | -0.143 ms/image |
| JPEG lossless | 126.913 ms/image | 127.628 ms/image | -0.471 ms/image |

All 48 aggregate rows retained the format-specific output hashes and byte
counts. The candidate was removed: worker startup cost exceeds the independent
phase, confirming that the remaining histogram boundary lies in later serial
clustering/remapping. This is RTX 2080 SUPER-only evidence and makes no
Ampere+ claim. All 16 raw transcripts are in the adjacent evidence directory.

## Traceback command-append rejection

`perf` sampling was unavailable because the host has `perf_event_paranoid=4`,
so no system setting was changed. A successful `gprofng` user-space sample of
the forced six-image PNG lossless workload collected 0.530 seconds of CPU time.
It attributed 20.75% inclusive time to
`VP8LBackwardReferencesTraceBackwards`, 11.32% exclusive time to
`VP8LBackwardRefsCursorAdd`, and 7.55% to
`GetCombinedEntropyUnrefined_C`. This directed the next screen at command
append rather than another raw-histogram worker split.

The candidate exposed the private command-block layout so the common append
could store directly, while block transitions kept the original allocation and
error path. The first unconditional CUDA screen appeared to gain 2.184
ms/image PNG and 3.052 ms/image JPEG. A four-pair CPU-only control then showed
PNG neutral at +0.334 ms/image but a consistent 10.782 ms/image JPEG
regression, so the global form was rejected.

Three subsequent forms selected a pre-Ampere fast path once or predictably and
left Ampere+ on the original builder:

| Form | PNG baseline | PNG candidate | Paired gain | JPEG baseline | JPEG candidate | Paired gain |
|---|---:|---:|---:|---:|---:|---:|
| Per-command gate | 78.257 ms | 76.356 ms | +1.859 ms | 127.963 ms | 130.331 ms | -2.463 ms |
| Out-of-line fast builder | 77.645 ms | 75.828 ms | +1.859 ms | 127.482 ms | 129.759 ms | -2.528 ms |
| Inlined fast builder | 77.868 ms | 76.201 ms | +1.630 ms | 128.953 ms | 131.448 ms | -2.658 ms |

Every CUDA and CPU aggregate retained its format-specific hash and byte count.
The candidate was removed because all architecture-safe forms regressed JPEG;
the initial apparent win was not robust to isolation and repetition. This is
Ryzen 9 3900X / RTX 2080 SUPER evidence only and makes no Ampere+ claim. The
adjacent evidence directory contains both sampling reports, both native CMake
caches, and all 84 process transcripts covering the unconditional, CPU-only,
and three gated screens.

## AVX2 combined-entropy rejection

The sampled `GetCombinedEntropyUnrefined_C` function scans each combined
histogram population for equal-value streaks. An exact AVX2 candidate added
eight `X + Y` bins and compared each with its predecessor in parallel. A fully
uniform block skipped directly to the next block; every nonuniform block used
the original scalar helper, integer arithmetic, and update order.

Two order-balanced process pairs per format, with one warmup and three measured
six-image batches in each process, found:

| Form | PNG baseline/candidate | Paired gain | JPEG baseline/candidate | Paired gain |
|---|---:|---:|---:|---:|
| Every alphabet | 78.070 / 78.488 ms | -0.418 ms | 129.650 / 127.090 ms | +2.561 ms |
| Extended literal only | 77.113 / 77.002 ms | +0.111 ms | 128.448 / 127.323 ms | +1.125 ms |

All aggregate hashes and byte counts matched. The broad form regressed PNG;
keeping the fixed color and distance alphabets scalar made PNG neutral but
reduced JPEG below the 1.5 ms/image gate. The candidate was removed. These are
Ryzen 9 3900X / RTX 2080 SUPER measurements only and make no Ampere+ claim.
All 16 raw process transcripts are in the adjacent evidence directory.

## CUDA hash compile-switch rejection

A 60-sample retained-head `gprofng` profile, with six images per sample,
collected 2.862 CPU seconds.
`VP8LBackwardReferencesTraceBackwards` led at 0.420 seconds exclusive and
0.630 inclusive; `VP8LBackwardRefsCursorAdd` used 0.250 exclusive;
`GetCombinedEntropyUnrefined_C` used 0.200; and `VP8LHashChainFill` used only
0.180 exclusive / 0.410 inclusive. A native-sm_75 Release build with debug
lines further bounded CPU hash-chain preparation near 0.5 ms/image. The
remaining 17--27 ms hash-stage boundary therefore points to device search and
its required result transfer.

Three already-supported compile-time kernel choices were measured separately
in two order-balanced process pairs per format, each with one discarded warmup
and three measured six-image lossless batches:

| Candidate | PNG baseline | PNG candidate | Paired gain | JPEG baseline | JPEG candidate | Paired gain |
|---|---:|---:|---:|---:|---:|---:|
| 256 threads/block | 77.691 ms | 78.102 ms | -0.410 ms | 126.381 ms | 127.174 ms | -0.793 ms |
| Disable four-pixel match loop | 77.331 ms | 78.151 ms | -0.820 ms | 126.861 ms | 128.111 ms | -1.249 ms |
| Disable read-only-cache loads | 77.402 ms | 77.698 ms | -0.296 ms | 126.521 ms | 126.315 ms | +0.206 ms |

All outputs retained hashes `eec6c490be6aaf6d` (PNG) and
`06227eb38e0ac1e3` (JPEG), with unchanged byte counts. No candidate clears the
1.5 ms/image gate, so the source remains unchanged: Turing keeps 128-thread
blocks, four-pixel matching, and `__ldg` reads. No Ampere+ behavior or claim is
changed. The adjacent evidence directory contains the raw function, calltree,
and source-line reports, collection transcripts, three native CMake caches,
and all 24 timing transcripts.

## Hash initial-pixel precheck rejection

Nsight Compute could attach to the process but could not access hardware
counters under this user's permissions (`ERR_NVGPUCTRPERM`), so the system
configuration was left untouched. `cuobjdump` showed the retained native-sm_75
hash kernel used 26 registers and no stack, shared, or local memory. Source and
SASS inspection then found that chain candidates call the match helper from
length zero, causing its pixel-zero precheck to be repeated by the first
comparison in the four-pixel loop.

An exact template specialization removed that duplicated comparison only for
pre-Ampere devices; Ampere+ selected the original kernel. The Turing candidate
fell to 24 registers with all other static resource counts unchanged. All
seven CTests passed. Five alternating baseline/candidate processes per format,
each with one discarded warmup and three measured six-image batches, found:

| Format | Baseline | Candidate | Paired baseline - candidate |
|---|---:|---:|---:|
| PNG lossless | 77.390 ms/image | 76.376 ms/image | +1.013 ms/image |
| JPEG lossless | 127.794 ms/image | 126.187 ms/image | +1.881 ms/image |

Every aggregate output retained hash `eec6c490be6aaf6d` for PNG or
`06227eb38e0ac1e3` for JPEG and unchanged bytes. PNG did not clear the strict
1.5 ms/image gate, so the candidate was removed despite the JPEG improvement.
This is RTX 2080 SUPER-only evidence and makes no Ampere+ claim. The adjacent
evidence directory contains the exact rejected patch, 20 raw timing
transcripts, both native caches, the seven-test transcript, baseline/candidate
resource reports, candidate kernel SASS, and raw Nsight permission error.

## Hash four-pixel load-ahead rejection

The retained native-sm_75 SASS serialized its unrolled matcher: it issued one
pixel pair, compared, and branched before loading the next pair. An exact
pre-Ampere specialization issued all eight in-bounds loads for a four-pixel
group first, then retained the original ordered comparisons and first-mismatch
returns. The Ampere+ false specialization's full 296-instruction mnemonic
stream matched the original, so the experiment did not perturb that path.

The Turing specialization used 32 registers rather than 26, with no stack,
shared, or local memory in either form. Seven CTests passed. Five alternating
baseline/candidate processes per format, each with one warmup and three
measured six-image batches, found:

| Format | Baseline | Load ahead | Paired baseline - candidate |
|---|---:|---:|---:|
| PNG lossless | 77.490 ms/image | 76.191 ms/image | +1.395 ms/image |
| JPEG lossless | 128.278 ms/image | 126.760 ms/image | +1.851 ms/image |

All aggregate hashes and byte counts matched. PNG remained below the strict
1.5 ms/image gate, so load-ahead was removed as a standalone change. This is
RTX 2080 SUPER-only evidence and makes no Ampere+ performance claim. The exact
patch, 20 timing transcripts, CTest log, baseline/candidate resources, both
specialization SASS listings, normalized mnemonic streams, and native caches
are stored in the adjacent evidence directory.

## Combined hash matcher rejection

The pre-Ampere initial-precheck and load-ahead candidates were composed while
Ampere+ retained the original specialization. A preliminary ten-pair gate
measured gains of 1.932 ms/image PNG and 1.844 JPEG. The complete ten-pair gate
was repeated after the resident-handoff correction below, on the exact final
binary:

| Format | Parent | Combined matcher | Paired gain |
|---|---:|---:|---:|
| PNG lossless | 77.838 ms/image | 76.964 ms/image | +1.184 ms/image |
| JPEG lossless | 128.780 ms/image | 126.256 ms/image | +2.203 ms/image |

All output hashes and byte counts matched. Because the final PNG gain is below
1.5 ms/image, the matcher was removed. Its Turing specialization used 30
registers without stack, shared, or local memory. The Ampere+ specialization
kept the parent's 26 registers and byte-identical 296-instruction normalized
stream. This result is RTX 2080 SUPER-only and makes no Ampere+ performance
claim.

## Resident predictor-to-hash correction and final numbers

Running the public encoder suite on the candidate exposed a pre-existing
decoded-pixel mismatch also reproduced on the frozen parent. With CUDA
predictor and hash enabled but cross-color disabled, predictor published
pre-color residuals as resident; the CPU could then apply cross-color to the
host buffer while hash consumed the stale device copy.

Resident state now records whether pixels are hash-ready. Predictor output may
feed CUDA color but cannot feed hash directly. CUDA color republishes its
transformed buffer as hash-ready; when color remains on CPU, hash uploads the
final host residuals. The public test covers both paths and disables the
intentional CUDA prewarm only for its cold-decline assertion.

All seven CTests passed. The public suite passed on its default input and all
six canonical PNG cases, including the new predictor-without-CUDA-color
regression. The default/baseline/all-disabled CUDA variant matrix also passed;
its full-feature arm now explicitly enables the otherwise default-off
histogram stage required by its preflight mask. The exact final native-sm_75
build passed all 180 official validation pairs and produced these definitive
machine numbers.

### Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 92.7 ms | 40.5 ms | **2.29x** |
| PNG lossless | 145.0 ms | 78.3 ms | **1.85x** |
| PNG near-lossless | 211.6 ms | 79.5 ms | **2.66x** |
| JPEG lossy | 92.9 ms | 40.5 ms | **2.29x** |
| JPEG lossless | 725.1 ms | 133.5 ms | **5.43x** |
| JPEG near-lossless | 853.6 ms | 133.9 ms | **6.38x** |

### Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 95.5 ms | 260.3 ms | **0.37x** |
| PNG lossless | 155.5 ms | 299.4 ms | **0.52x** |
| PNG near-lossless | 221.4 ms | 308.5 ms | **0.72x** |
| JPEG lossy | 95.6 ms | 257.7 ms | **0.37x** |
| JPEG lossless | 722.5 ms | 348.8 ms | **2.07x** |
| JPEG near-lossless | 833.3 ms | 364.6 ms | **2.29x** |

The raw paired screens, failing parent reproducer, final public-test logs,
official JSONL/results, exact patches, SASS, resource reports, and copied
tiny/odd inputs are in the adjacent evidence directory under the
`libwebp-hash-combined-*` and `libwebp-resident-handoff-*` prefixes.

## Lossy recorder recheck and rejected composition

The retained native-sm_75 profile measured medium graphic/photo/texture at
25.819/31.750/79.093 ms per encode. Their accelerated decimate/collect/replay
intervals were 20.671/21.605/52.138 ms, while direct device walls were nearly
flat at 21.650/21.920/21.890 ms. Token emission was
0.589/2.849/14.374 ms; I4 represented 37.0/63.8/65.5% of device block cycles.

That texture gap justified rechecking the recorder worker. Five
order-balanced process pairs per format kept every aggregate hash and byte
count exact, but inline recording gained only 0.553 ms/image PNG (40.208 to
39.655) and 0.373 JPEG (40.403 to 39.878). A preliminary 8.8 ms impression
was discarded because it compared PPM candidate input against PNG parent
input; like-for-like PPM measured 32.362 versus 31.731 ms/image.

Inline recording was then composed with the previously exact static I4
prediction dispatch and 16-lane winner publication, isolated to the
pre-Ampere compile path. Two order-reversed processes with six samples per
cell moved PNG 40.436 to 39.008 ms/image (1.427 ms) and JPEG 40.375 to 39.120
(1.255 ms). All 48 aggregate rows retained the expected hashes. Both gains
remain below 1.5 ms/image, so the composite was removed and no Ampere+ claim
is made.

The adjacent evidence directory stores the retained profile under
`libwebp-lossy-retained-profile-*`, the 20-process recorder gate under
`libwebp-token-record-inline-*`, and the composite screen, exact rejected
patch, summaries, and native caches under `libwebp-static-i4-inline-*`.

## Warp-helper call-elimination rejection

Native-sm_75 disassembly exposed 206 out-of-line synchronized ballot/shuffle
helper calls in the CUDA module. A pre-Ampere inline-PTX wrapper candidate did
not change that count, and the decimate kernel changed only from 103 to 102
registers while retaining its 352-byte stack and 23,392-byte shared-memory
allocation.

Two order-reversed processes with six samples per cell measured PNG at 40.013
ms/image parent versus 40.227 candidate and JPEG at 40.002 versus 40.094. The
candidate changed both hashes and byte counts. Rebuilding the restored source
in the same cache reproduced the parent's exact output, isolating the failure
to the wrapper code rather than the cache configuration. CUDA 12 rejects the
legacy `__shfl*` intrinsics for a native sm_75 build, so there is no safe
fallback shortcut.

The candidate was removed for correctness and performance. Complete compressed
parent/candidate SASS, resource reports, CMake caches, 48 raw timing rows,
compiler failure, summary, and clean-rebuild control are stored under the
`libwebp-warp-helper-*` prefix in the adjacent evidence directory. This result
is specific to the RTX 2080 SUPER and does not change or characterize the
Ampere+ path.

## RD-level kernel-specialization rejection

Line-info ptxas profiling proved the retained decimate kernel's 352-byte frame
has zero spills and belongs to trellis state that method 4 never executes. A
pre-Ampere compile-time RD-level specialization reduced method 3/4 from 103
registers and 352 stack bytes to 67 registers and no frame. Method 5 and 6
specializations used 100/272 and 94/272 registers/stack bytes. All seven CTests
passed and all 48 screen outputs were byte-exact.

Two order-reversed processes with six samples per cell measured PNG at 40.147
ms/image parent versus 39.946 specialized (+0.200 ms), and JPEG at 40.201
versus 39.789 (+0.412 ms). At 256 threads, both the 103- and 67-register forms
fit two CTAs within the 65,536-register SM budget. The 23,392-byte shared-memory
allocation is the unchanged occupancy limit: two CTAs require 46,784 bytes,
while three require 70,176. The measured gains are far below the 1.5 ms/image
threshold and the specialization was removed.

The exact rejected patch, native cache, resource report, compressed SASS, 7/7
CTest log, 48 timing rows, and summary are stored under the
`libwebp-rd-specialize-*` prefix. This result is RTX 2080 SUPER-only and makes
no Ampere+ performance claim.

## Sixteen-band streaming rejection

Because eight bands previously beat four on this machine and the retained
profile still showed collection/replay work beyond the device wall, a temporary
candidate extended the backend event capacity to 16 and used 16 bands for
images at least 32 macroblock rows high.

Two order-reversed processes with six samples per cell retained every output
hash and byte count. PNG moved from 40.185 to 39.973 ms/image (+0.211 ms), and
JPEG moved from 40.317 to 39.876 (+0.441 ms). Both are far below the 1.5
ms/image threshold, so the candidate was removed. A separate screen requested
16 bands without extending the production eight-event cap; the backend safely
declined and exact CPU fallback completed the encode.

The exact patch, native cache, all valid and decline timing rows, and summary
are stored under the `libwebp-band16-*` prefix. This is RTX 2080 SUPER-only
evidence; the shared eight-band default and Ampere+ behavior remain unchanged.

## Cold token-page growth outlining rejection

A refreshed native-sm_75 whole-process sampling run attributed 2.402 of 5.164
exclusive CPU seconds (46.51%) to `VP8RecordCoeffTokens`, ahead of
`VP8PutTokenPage` at 1.291 seconds. The executable and archived copy both
contain full DWARF, although this machine's Binutils 2.42 `gprofng` crashes with
exit 139 when resolving the experiment to line or annotated-disassembly views.
The successful function report and complete compressed 104 MiB experiment are
stored alongside this report so that result remains independently inspectable.

Generated-code inspection showed the rare page-allocation branch duplicated at
each token site. Outlining only `TBufferNewPage` reduced
`VP8RecordCoeffTokens` from 4,976 to 3,644 bytes and added one 95-byte cold
helper. All seven CTests passed and every timing row retained the expected hash
and byte count. Two order-reversed processes measured:

| Format | Parent | Outlined growth | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.221 ms/image | 40.111 ms/image | 0.110 ms/image |
| JPEG lossy | 40.170 ms/image | 40.164 ms/image | 0.006 ms/image |

The candidate was removed because both gains are far below 1.5 ms/image. The
exact patch, native build caches, compressed disassemblies, 7/7 CTest log, 48
raw timing rows, sampling reports, and complete profile are stored under the
`libwebp-token-grow-*` and `libwebp-token-lines-*` prefixes. This is RTX 2080
SUPER-only evidence and makes no Ampere+ claim.

## Warp-private I4 prediction-boundary rejection

A new explicit-native profile measured PNG/JPEG lossy CUDA at 41.061/39.555
ms per image versus 85.134/85.822 on CPU. Medium-image device walls were
about 22--26 ms; I4 still represented 63--65% of photo/texture block cycles.

The pre-Ampere candidate replaced one shared 13-byte boundary per active team
with one boundary per prediction warp. Four leaders gathered and immediately
consumed their own exact samples, eliminating the first CTA-wide barrier in
each I4 dependency diagonal. Ampere+ retained the original compile branch.

Candidate and restored builds passed 7/7 CTests. All 24 timing outputs were
exact:

| Format | Parent | Private boundaries | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.888 ms/image | 39.720 ms/image | 0.167 ms/image |
| JPEG lossy | 39.405 ms/image | 39.681 ms/image | -0.276 ms/image |

PNG retained `d01c3571a90d2653` / 1,610,422 bytes and JPEG retained
`befeef70bef22946` / 1,600,198 bytes. Registers and stack remained 103 and
352 bytes; shared memory increased by 72 bytes. The source was restored
because PNG is far below the gate and JPEG regresses. The raw retained matrix,
phase traces, exact patch, screen, SASS/resources, binary hashes, native cache,
and both test transcripts are stored under `libwebp-i4-private-boundary-*` in
the adjacent evidence directory. No Ampere+ performance claim is made.

## Four-pixel mismatch-mask rejection

An explicit native-sm_75 profile measured retained hash-candidate calls at
7.557 ms for the 1,920,000-pixel resident photo and 10.891 ms for the
960,000-pixel texture. The candidate composed the independently exact
duplicate-precheck removal with four branchless mismatch bits and a
first-set-bit position per unrolled group. It was compile-time selected only
on pre-Ampere; the Ampere+ specialization's full mnemonic stream remained
identical to the parent.

Candidate and restored builds passed all seven CTests. Two order-reversed
pairs per format produced 48 byte-exact rows:

| Format | Parent | Mismatch mask | Gain |
|---|---:|---:|---:|
| PNG lossless | 75.827 ms/image | 74.587 ms/image | 1.239 ms/image |
| JPEG lossless | 127.713 ms/image | 123.393 ms/image | 4.319 ms/image |

Every PNG row retained `81fa42c7697cb521` / 6,720,632 bytes; every JPEG row
retained `a4fca74ecf18a917` / 8,956,690 bytes. The Turing kernel rose from 26
to 34 registers without changing its 296-instruction count. Since PNG still
misses the 1.5 ms/image threshold, the source was restored. The profile,
exact patch, 48 rows, resource/SASS reports, specialization comparison,
binary hashes, native cache, and candidate/restored test logs are archived
under `libwebp-hash-mask-*` in the adjacent evidence directory. No Ampere+
performance claim is made.

## Hash-chain next-link prefetch rejection

A native-sm_75 candidate moved each next-chain-link read ahead of the pixel
rejection and match scan, allowing the dependency to overlap loop work. The
change was compile-time selected only below compute capability 8. Generated
code stayed at 26 registers and 296 mnemonic instructions for both candidate
specializations; the Ampere+ false specialization's full mnemonic stream was
identical to the parent.

All seven CTests passed. Two order-reversed pairs per format, with six samples
per arm, produced 48 exact rows:

| Format | Parent | Link prefetch | Gain |
|---|---:|---:|---:|
| PNG lossless | 77.035 ms/image | 77.694 ms/image | -0.659 ms/image |
| JPEG lossless | 130.080 ms/image | 128.167 ms/image | 1.913 ms/image |

PNG retained `ae63469bc03eece1` / 6,720,632 bytes and JPEG retained
`7396c2ca11b0f48f` / 8,956,690 bytes in every row. The PNG regression rejects
the candidate despite the JPEG improvement, so the source was restored. Raw
profile output, exact patch, timing rows, resources, compressed SASS,
specialization comparison, binary hashes, explicit native cache, and both
CTest transcripts are stored under `libwebp-hash-link-prefetch-*` in the
adjacent evidence directory. This result is specific to the RTX 2080 SUPER
and makes no Ampere+ performance claim.

## Two-pixel grouped hash-matcher rejection

A current forced-lossless refresh measured dominant hash-candidate kernel
calls around 7.5 ms for 1,920,000 resident pixels and 10.9 ms for 960,000
pixels. The archived four-pixel load-ahead candidate had gained 1.395 ms/image
PNG and 1.851 JPEG but raised Turing register use from 26 to 32. A new
pre-Ampere specialization therefore grouped only two pixel pairs before their
ordered comparisons and composed the independently exact duplicate-precheck
removal.

The candidate stayed at 26 registers with no stack, shared, or local memory.
Its pre-Ampere mnemonic stream shrank from 296 to 288 instructions. The
Ampere+ false specialization retained 296 instructions and its complete
mnemonic sequence matched the parent, so no Ampere+ behavior changed.

All seven CTests passed. Two order-reversed pairs per format produced 48 exact
aggregate rows:

| Format | Parent | Two-pixel matcher | Gain |
|---|---:|---:|---:|
| PNG lossless | 77.101 ms/image | 76.102 ms/image | 0.999 ms/image |
| JPEG lossless | 128.924 ms/image | 123.830 ms/image | 5.094 ms/image |

Every PNG row retained `ae63469bc03eece1` / 6,720,632 bytes and every JPEG
row retained `7396c2ca11b0f48f` / 8,956,690 bytes. The candidate was removed
because PNG remains below the strict 1.5 ms/image gate despite the large JPEG
win. The raw current profile, exact patch, timing rows, resources, compressed
SASS, Ampere+ mnemonic comparison, binary hashes, native cache, restored
7/7 CTest log, and summary are stored under `libwebp-hash-pair-*` in the
adjacent evidence directory. These performance numbers characterize only the
RTX 2080 SUPER.

## Precomputed coefficient-token band-offset rejection

An optimized coverage build refined the dominant token-recorder profile. On
the representative PNG and JPEG corpora it observed 117,400,812 coefficient
iterations: 40.0% zero, 28.9% magnitude one, and only 0.16% above magnitude
ten. Static retained assembly showed every next-context transition forming the
same `band * 33` offset separately for the token ID and statistics pointer.

A temporary 17-entry exact offset table replaced both arithmetic chains with
one 16-bit lookup and reduced `VP8RecordCoeffTokens` from 4,976 to 4,944 bytes.
All seven CTests passed and every A/B output retained the expected hash and
byte count:

| Format | Parent | Precomputed offsets | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.240 ms/image | 40.356 ms/image | -0.116 ms/image |
| JPEG lossy | 40.321 ms/image | 39.851 ms/image | 0.471 ms/image |

The candidate was removed because PNG regressed and JPEG remained far below
the 1.5 ms/image gate. Raw `.gcda`/`.gcno`, annotated coverage sources, the
coverage workload rows, exact patch, native caches, compressed disassemblies,
7/7 CTest transcript, and 48 timing rows are stored under the
`libwebp-token-gcov-*` and `libwebp-token-band-offset-*` prefixes. This is RTX
2080 SUPER-only evidence and does not characterize or alter Ampere+.

## Fixed-bit coefficient-token prefix rejection

The branch-frequency profile showed zero and magnitude-one coefficients at
68.9% of token-recorder iterations. A temporary branch-first tree specialized
the first two packed token/statistics updates for constant zero and one. It
preserved ordering and allocation-failure behavior and passed all seven CTests,
but duplicated the inlined page/statistics paths: `VP8RecordCoeffTokens` grew
from 4,976 to 5,344 bytes.

Two order-reversed native-sm_75 processes per format retained every output
hash and byte count:

| Format | Parent | Fixed-bit prefix | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.260 ms/image | 40.920 ms/image | -0.660 ms/image |
| JPEG lossy | 40.036 ms/image | 40.589 ms/image | -0.554 ms/image |

Both formats regressed, so the candidate was removed. The exact patch, native
caches, compressed parent/candidate disassembly, symbol sizes, 7/7 CTest
transcript, and 48 raw timing rows are stored under the
`libwebp-token-fixed-bit-*` prefix. This is RTX 2080 SUPER-only evidence and
makes no Ampere+ claim.

## No-run token-byte fast-flush rejection

The native coverage run counted 36,426,600 real byte flushes in
`VP8PutTokenPage`. Pending `0xff` runs occurred on only 138,264 normal flushes
(0.38%), and buffer growth occurred 768 times. A temporary direct no-run arm
therefore bypassed pending-capacity arithmetic and the later run test for the
99.62% common case while preserving the original run and allocation paths.

The intended assembly was emitted and the function shrank from 764 to 719
bytes. Seven CTests passed and all timing outputs were exact:

| Format | Parent | No-run fast flush | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.144 ms/image | 40.213 ms/image | -0.069 ms/image |
| JPEG lossy | 40.027 ms/image | 40.105 ms/image | -0.078 ms/image |

Both formats regressed slightly, so the candidate was removed. Raw annotated
coverage and `.gcda`/`.gcno` files are stored under `libwebp-token-page-gcov-*`;
the exact patch, native caches, disassemblies, symbols, 7/7 CTest transcript,
and 48 timing rows are under `libwebp-token-norun-flush-*`. This is RTX 2080
SUPER-only evidence and makes no Ampere+ claim.

## Deferred basic-I4 reconstruction-copy rejection

A current-head native-sm_75 refresh measured I4 at 63.2% of photo and 64.8%
of texture block cycles. A temporary counter probe showed that the fixed I4
entry cost never provided a zero-work rejection, while I4 was accepted for
all representative texture macroblocks and about half of photo macroblocks.
This motivated a pre-Ampere-only method-4 candidate that kept accepted luma
pixels in the completed I4 scratch plane and selected that plane at the final
reconstruction write.

The first prototype skipped a loop that also publishes coefficient levels.
The aggregate parity screen caught the error: PNG changed from
`743146796a9addc7` / 1,610,422 bytes to `244ef6f8a2e1645b` / 1,550,038, and
JPEG changed from `8abe9f8c33699452` / 1,600,198 bytes to
`727442321fbf19a8` / 1,529,050. Those timings were discarded. The corrected
candidate always copied exact winning levels and deferred only the 256 luma
pixels. Methods 5/6 and Ampere+ retained the parent path.

All seven CTests passed. Two order-reversed pairs per format produced 48
byte-exact timing rows:

| Format | Parent | Deferred pixel copy | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.440 ms/image | 40.361 ms/image | 0.079 ms/image |
| JPEG lossy | 40.287 ms/image | 40.330 ms/image | -0.043 ms/image |

The candidate was removed because it is far below the 1.5 ms/image gate and
slightly regresses JPEG. The full phase traces, abort histogram, invalid and
corrected timing rows, exact rejected patch, native cache, baseline/candidate
resource and SASS reports, binary hashes, restored-parent CTest transcript,
and a command/result summary are stored under the `i4-deferred-copy-*` prefix
in the adjacent evidence directory. These results characterize only the RTX
2080 SUPER and do not alter or claim Ampere+ behavior.

## I16 lazy residual-cost pruning feasibility rejection

The refreshed graphic trace made I16 selection the next distinct device
target at 25.2% of block cycles. Since every residual cost is non-negative, a
temporary counter probe simulated an exact ordered lazy policy: evaluate mode
0, then skip any later mode whose base score already cannot beat the current
best full score. The probe replayed the existing source-flatness chain and
strict-less tie behavior without changing encoder decisions.

Photo and texture required every one of the four mode walks. Graphic-small
needed 3,262 of 4,096 walks (20.36% pruned); graphic-medium needed 14,757 of
30,000 (50.81% pruned). The corresponding winner histograms are preserved in
the raw trace.

Even the deliberately unrealistic assumption that the complete instrumented
graphic I16-selection intervals scale perfectly with the pruned fraction
limits the equally weighted six-image suite to 0.80 ms/image. The real ceiling
is lower because flatness, scalar selection, barriers, and winner publication
remain, while a lazy implementation adds a dependency after mode 0.

No candidate was implemented because the optimistic bound is already below
the 1.5 ms/image gate. The probe was removed, the retained native-sm_75 source
was rebuilt, and all seven CTests passed. The raw counter output, exact probe
patch, restored-parent CTest log, and calculation summary are stored under the
`i16-lazy-prune-*` prefix in the adjacent evidence directory. This is RTX 2080
SUPER-only evidence and makes no Ampere+ claim.

## Refreshed partition0/token-emission overlap

The earlier exact host overlap was recovered and re-screened on the current
retained native-sm_75 binary using the actual PNG and JPEG inputs. It generated
partition 0 on the caller while all eight token partitions ran on workers;
`WEBP_PARTITION0_PIPELINE=0` selected the same-binary parent schedule.

Seven CTests passed for both candidate and restored trees. All 24
order-reversed rows retained identical hashes and byte counts:

| Format | Parent | Partition0 overlap | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.775 ms/image | 38.559 ms/image | 1.216 ms/image |
| JPEG lossy | 39.286 ms/image | 38.885 ms/image | 0.401 ms/image |

Both gains miss the strict 1.5 ms/image gate, so the candidate was removed.
The raw rows are
`evidence/2026-08-18-linux-ryzen-9-3900x-rtx-2080-super/libwebp-partition0-current-formats-screen.jsonl`.
This is RTX 2080 SUPER-only evidence and makes no Ampere+ claim.

## Fused I4 transform/quantization handoff

A fresh 48-image `gprofng` sample first bounded the JPEG input decoder at
0.050 seconds inclusive, about 1.04 ms/image. That is below the retention gate
even before considering that PNG would be unchanged, so the next candidate
returned to the profiled 25.6--26.5% I4 transform/quantization interval.

The pre-Ampere candidate kept each four-lane group's transformed coefficient
column in registers through basic quantization and inverse-transform setup.
It wrote levels through an exact inverse-zigzag map and removed two warp
synchronizations plus the shared coefficient publish/reload. The first build
omitted the mode non-zero publication and was rejected by correctness before
timing; the corrected candidate and restored source both passed all seven
CTests.

All 24 order-reversed native-sm_75 screen rows were byte-exact:

| Format | Parent | Fused handoff | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.641 ms/image | 38.986 ms/image | 0.655 ms/image |
| JPEG lossy | 39.426 ms/image | 39.168 ms/image | 0.258 ms/image |

Resources moved from 103 to 98 registers with the same 352-byte stack and
23,392-byte shared allocation. Both gains are far below 1.5 ms/image, so the
candidate was removed. The raw sample, benchmark row, exact corrected patch,
timings, resources, binary hashes, and candidate/restored CTest logs are in
the adjacent evidence directory under `libwebp-jpeg-decode-feasibility-*` and
`libwebp-i4-fused-register-*`. This is Turing-only evidence; Ampere+ behavior
was never changed.

## Shared segment-matrix staging

The next pre-Ampere candidate staged the selected 716-byte immutable segment
bundle—three quantization matrices and all scoring lambdas—in shared memory.
Its cooperative copy ran alongside source import and used the already-required
setup barrier, so it introduced no synchronization point.

Candidate and restored source passed all seven CTests. All 24 order-reversed
native-sm_75 timing rows were byte-exact:

| Format | Parent | Shared segment | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.637 ms/image | 39.596 ms/image | 0.041 ms/image |
| JPEG lossy | 39.621 ms/image | 39.417 ms/image | 0.204 ms/image |

Resources changed from 103 registers and 23,392 shared bytes to 92 registers
and 24,104 shared bytes; the 352-byte stack and occupancy were unchanged. The
near-zero wall changes show that the original global segment reads were
already cache-resident, so the candidate was removed. The exact patch, raw
rows, parent/candidate resources, binary hashes, and both CTest transcripts
are archived under `libwebp-decimate-shared-segment-*`. This is Turing-only
evidence; Ampere+ behavior was never changed.

## Balanced-I4/chroma plus shared-segment composition

The previously exact balanced four-warp I4/chroma candidate missed the JPEG
retention gate by only 0.011 ms/image. It was therefore composed with the
independently exact shared-segment staging candidate, whose standalone JPEG
screen gained 0.204 ms/image. This remained a single local native-sm_75
composition experiment based on the retained decimation profile.

Candidate and restored source passed all seven CTests. All 24 order-reversed
screen rows were byte-exact:

| Format | Parent | Composition | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.699 ms/image | 37.664 ms/image | 2.035 ms/image |
| JPEG lossy | 39.555 ms/image | 38.198 ms/image | 1.356 ms/image |

JPEG remained 0.144 ms/image below the strict gate, so the composition was
removed. The exact composite patch, raw rows, and both CTest transcripts are
archived under `libwebp-i4-balanced-chroma-shared-*`. This is Turing-only
evidence; the experimental scheduling code was never pushed and no Ampere+
behavior or performance claim was changed.

## Uniform-AC I4 quantization

The retained I4 transform/quantization profile was combined with a native
sm_75 SASS inspection, which counted 621 static global `U16` load sites.
Because the encoder's `ExpandMatrix` duplicates luma AC `q`, `iq`, `bias`,
and `zthresh` values across indices 1--15, a pre-Ampere candidate cached one
copy of each scalar in the four-lane basic quantizer. A host check selected
the fast path only when every segment satisfied the invariant; generic
contract inputs and Ampere+ retained the original implementation.

Candidate and restored source passed all seven CTests. All 24 order-reversed
native-sm_75 timing rows were byte-exact:

| Format | Parent | Uniform-AC | Change |
|---|---:|---:|---:|
| PNG lossy | 39.548 ms/image | 39.733 ms/image | +0.185 ms/image |
| JPEG lossy | 39.633 ms/image | 39.645 ms/image | +0.012 ms/image |

Resource use fell from 103 to 101 registers with the same 352-byte stack and
23,392-byte shared allocation, but wall time did not improve. The candidate
was removed. Exact patch, rows, resource output, and candidate/restored test
logs are archived under `libwebp-i4-uniform-ac-*`. This is Turing-only
evidence and makes no Ampere+ performance claim.

## I4 source-Hadamard overlap

The 21.7--24.0% I4 metric interval includes a weighted Hadamard transform of
the same source block for all ten modes. A pre-Ampere candidate computed that
common sum in an otherwise idle upper-team lane during the preceding
transform/quantization stage. The existing barrier published it, and the
metric warp then transformed only each reconstruction. Ampere+ retained the
original source path.

Candidate and restored source passed all seven CTests. All 24 order-reversed
native-sm_75 timing rows were byte-exact:

| Format | Parent | Overlap | Change |
|---|---:|---:|---:|
| PNG lossy | 39.683 ms/image | 39.596 ms/image | -0.088 ms/image |
| JPEG lossy | 39.567 ms/image | 39.689 ms/image | +0.121 ms/image |

On texture-medium, direct GPU wall moved from 26.08 to 26.15 ms and I4 stayed
65.3% versus 65.2% of block cycles. The candidate merely transferred the
source transform to the earlier barrier's critical path, so it was removed.
Exact patch, rows, phase trace, resource output, and candidate/restored tests
are archived under `libwebp-i4-source-hadamard-*`. Turing-only evidence; no
Ampere+ behavior or performance claim changed.

The follow-up prediction-stage placement used the same exact source sum but
computed it beside the four prediction warp leaders. Candidate and restored
source passed all seven CTests and all 24 rows matched. PNG moved from 39.715
to 39.629 ms/image (-0.086), while JPEG regressed from 39.619 to 39.758
(+0.138). It was removed; raw patch, rows, resources, and tests are archived
under `libwebp-i4-source-hadamard-pred-*`. No Ampere+ path changed.

## Cooperative four-lane I4 residual scoring

The temporary native-sm_75 metric-warp probe made the next target explicit.
Two medium runs per content type measured residual-warp totals of about 84.2
million cycles for graphic, 306 million for photo, and 270 million for
texture. On photo and texture this exceeded both SSE/flatness (about 209/145
million) and distortion (about 140/139 million).

The pre-Ampere experiment replaced each scalar sixteen-coefficient residual
walk with a four-lane subgroup processing four waves. Ten groups used 40
lanes, while Ampere+ retained the original code. Both candidate and restored
source passed all seven CTests. All 24 order-reversed rows were byte-exact:

| Format | Parent | Four-lane residual | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.168 ms/image | 40.085 ms/image | 0.083 ms/image |
| JPEG lossy | 39.652 ms/image | 40.185 ms/image | -0.533 ms/image |

Registers moved from 103 to 102, with the 352-byte stack and 23,392-byte
shared allocation unchanged. The subgroup shuffles, reduction, and divergent
cost-table work outweighed the shorter chain, so the candidate was removed.
The raw probe, exact candidate patch, timing rows, build/resource transcript,
and candidate/restored tests are in the adjacent evidence directory under
`libwebp-i4-metric-warp-*` and `libwebp-i4-residual-coop4-*`. These results
apply only to the RTX 2080 SUPER; no Ampere+ path or claim changed.

## Cooperative two-lane I4 residual scoring

The follow-up reduced the measured residual warp's serial chain less
aggressively: two lanes per mode processed eight coefficient waves, and all
ten mode pairs stayed in warp 0. The first prototype called a two-lane shuffle
from lane 0 alone and therefore timed out in a bounded medium-corpus smoke
test. That invalid run was excluded. The corrected implementation executed
the shuffle in both mask members before lane 0 consumed the value.

Both corrected candidate and restored source passed all seven CTests. All 24
order-reversed native-sm_75 rows were byte-exact:

| Format | Parent | Two-lane residual | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.846 ms/image | 42.669 ms/image | -2.823 ms/image |
| JPEG lossy | 39.813 ms/image | 42.713 ms/image | -2.900 ms/image |

The candidate used 102 registers with the unchanged 352-byte stack and
23,392-byte shared allocation. The nearly 3 ms/image regressions show that
even the narrower subgroup's shuffle and duplicated control/table work is
more expensive than the scalar residual walks on this RTX 2080 SUPER. The
candidate was removed. The exact corrected patch, raw rows, prototype timeout
record, build/resources, and candidate/restored tests are archived under
`libwebp-i4-residual-coop2-*`. Ampere+ compiled the original path.

## I4 zero-residual bypass feasibility

A temporary counter read the I4 nonzero flags already produced by
quantization and counted modes that could skip the scalar residual walk's
backwards last-nonzero scan:

| Content | Zero / total modes | Rate |
|---|---:|---:|
| Graphic-medium | 424,548 / 488,950 | 86.83% |
| Photo-medium | 4,234 / 1,198,680 | 0.35% |
| Texture-medium | 0 / 1,200,000 | 0.00% |

The separate warp-cycle profile explains why the graphic number is
misleading: residual consumed about 84.2 million cycles there, while
SSE/flatness consumed about 85.6 million, so the metric barrier would not move
even if all residual work vanished. Photo and texture are residual-critical,
but their zero rates are 0.35% and 0.00%. The end-to-end ceiling is far below
1.5 ms/image; no candidate was built. The probe was removed and the restored
source passed all seven CTests. Raw probe patch, counts, build log, and
restored test transcript are archived under
`libwebp-i4-zero-residual-*`. RTX 2080 SUPER only; no Ampere+ path changed.

## I4 last-nonzero-index handoff

To test the stronger form of the zero-residual idea, a pre-Ampere candidate
published every basic quantizer's exact last-nonzero index. Two four-lane
reductions packed it into the unused upper bits of existing `i4_nz` scratch,
leaving the low bit unchanged. Residual scoring consumed the index directly
instead of rescanning sixteen levels. Trellis and Ampere+ used the original
code.

Both candidate and restored source passed all seven CTests. All 24
order-reversed native-sm_75 rows were byte-exact:

| Format | Parent | Last-index handoff | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.887 ms/image | 39.833 ms/image | 0.054 ms/image |
| JPEG lossy | 39.893 ms/image | 39.897 ms/image | -0.005 ms/image |

Resources moved from 103 to 102 registers; the 352-byte stack and 23,392-byte
shared allocation stayed fixed. The quantizer reduction cost canceled the
tiny scan saving, so the candidate was removed. Exact patch, raw rows,
candidate build/resources, and candidate/restored tests are archived under
`libwebp-i4-last-handoff-*`. RTX 2080 SUPER only; no Ampere+ path changed.

## Zero-level I4 residual-cost specialization

The native-sm_75 value probe measured the values consumed by residual
scoring:

| Content | Zero | One | 2+ |
|---|---:|---:|---:|
| Graphic-medium | 45.38% | 24.52% | 30.09% |
| Photo-medium | 74.62% | 24.54% | 0.85% |
| Texture-medium | 12.82% | 23.40% | 63.78% |

`VP8LevelFixedCosts[0]` is exactly zero, so a pre-Ampere candidate returned
the variable table's zero entry without loading the fixed table. Ampere+
compiled the original implementation. Both candidate and restored source
passed all seven CTests, and all 24 order-reversed rows were byte-exact:

| Format | Parent | Zero fast path | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.930 ms/image | 40.202 ms/image | -0.273 ms/image |
| JPEG lossy | 39.810 ms/image | 40.066 ms/image | -0.256 ms/image |

Registers, stack, and shared memory remained 103, 352 bytes, and 23,392
bytes. The value-dependent branch cost more than the avoided load, so the
candidate was removed. Raw profile, exact patch, timings, builds/resources,
and candidate/restored tests are archived under
`libwebp-i4-residual-value-*` and `libwebp-i4-zero-level-cost-*`. RTX 2080
SUPER only; no Ampere+ path changed.

## Common-level I4 residual-cost specialization

The range probe found that levels 0--4 account for 91.18% of
graphic-medium, 99.96% of photo-medium, and 82.27% of texture-medium residual
values. A pre-Ampere candidate replaced the corresponding fixed-table loads
with the exact constants: zero for level 0 and 256 for levels 1--4. Values
above 4 and all Ampere+ code retained the original compact two-table path.

Both candidate and restored source passed all seven CTests. All 24
order-reversed native-sm_75 rows were byte-exact:

| Format | Parent | Common-level path | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.810 ms/image | 40.553 ms/image | -0.743 ms/image |
| JPEG lossy | 39.729 ms/image | 40.511 ms/image | -0.783 ms/image |

Registers fell from 103 to 102; stack and shared memory stayed at 352 and
23,392 bytes. The candidate still regressed both formats, so it was removed.
Raw range profile, exact patch, timings, builds/resources, and
candidate/restored tests are archived under
`libwebp-i4-residual-range-*` and `libwebp-i4-common-level-cost-*`. RTX
2080 SUPER only; no Ampere+ path changed.

## Compact pre-Ampere I4 scratch / RD specialization composition

The retained native-sm_75 kernel resource profile exposed a distinct
occupancy boundary: method 4 used 103 registers, a 352-byte frame, and 23,392
shared bytes, so both resources limited residency to two 256-thread CTAs per
SM. The earlier exact RD-level specialization had reduced method 4 to 67
registers and no frame but left shared memory unchanged, which explained its
neutral result. The next candidate stored pre-Ampere I4 reconstruction rows at
their actual four-byte stride and composed that specialization, while Ampere+
retained the established layout and runtime RD-level behavior.

Native resources reached 69 registers, no frame, and 21,152 shared bytes for
method 4, admitting three CTAs under both 65,536-unit Turing limits. Methods 5
and 6 remained at 96/94 registers, a 272-byte frame, and 21,152 shared bytes.
Exact aggregate hashes and byte counts matched in all 15 method/quality cells:
methods 2--6 and qualities 25/75/98 over graphic/photo/texture at 17x13 and
257x255. The focused trellis suite also passed qualities 75/99, 513x517 odd
geometry, one/two passes, padded strides, every band remainder, and forced
collect/download transactional fallback.

Two order-reversed processes per format, each discarding one warmup and
retaining three 24-image samples, produced 24 exact rows:

| Format | Parent | Compact occupancy | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.438 ms/image | 38.974 ms/image | 0.465 ms/image |
| JPEG lossy | 39.427 ms/image | 39.141 ms/image | 0.286 ms/image |

The source was restored because both changes are noise. The medium corpus has
at most 75 CTAs on a diagonal; the retained two-CTA limit already makes 96
slots available across the RTX 2080 SUPER's 48 SMs. The third theoretical
residency slot is consequently mostly unused. Raw profile/resource evidence,
exact candidate patch, all timing rows, and the hash/byte matrix use the
`libwebp-i4-compact-occupancy-*` prefix. No Ampere+ code, dispatch gate, or
performance claim changed.

## Pre-Ampere decimation CUDA Graph replay

A refreshed native-sm_75 run confirmed decimation remained the dominant
lossy stage, taking 20.671 ms of 25.819 ms on graphic-medium, 21.605 ms of
31.750 ms on photo-medium, and 52.138 ms of 79.093 ms on texture-medium. The
pass submits roughly 250 dependency-ordered diagonal kernels for the medium
geometry. Nsight Systems capture was not importable on this host and Nsight
Compute counters were denied with `ERR_NVGPUCTRPERM`; the explicit launch
count and stage timings therefore motivated a pre-Ampere-only CUDA Graph
cache/replay candidate. Ampere+ remained on the retained path.

The candidate passed the focused exact trellis/fallback suite. Three retained
samples per side in a same-binary, reversed-format screen measured:

| Format | Direct launches | CUDA Graph | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.937 ms/image | 82.736 ms/image | -42.799 ms/image |
| JPEG lossy | 39.515 ms/image | 80.974 ms/image | -41.459 ms/image |

PNG hashes/bytes were `ace64e860de89b43` / 6,441,688 on both sides; JPEG was
`1cbb84d2ab926db3` / 6,400,792. The graph path more than doubled end-to-end
latency, so it was removed. The restored focused build succeeded and six of
seven CTests passed; the known silent `cuda_histogram_test` failure reproduced
unchanged. Evidence is archived under `libwebp-decimate-graph-replay-*`. This
is RTX 2080 SUPER evidence only and does not alter Ampere+ settings or claims.

## Pre-Ampere fused I4 prediction group

The next retained-head profile measured 39.44 ms/image PNG and 39.66
ms/image JPEG on the native six-image batch. Medium device traces placed I4
at 63.8% of photo and 65.5% of texture block cycles. Direct CPU stage traces
measured analysis at 10.1--11.7 ms/image, while forced-batch sampling again
landed in the exhaustively tuned token recorder/emitter. The distinct device
candidate therefore fused warp 0's DC/RD/HD predictions: RD and HD shared six
identical symmetric three-tap boundary averages, and the remaining leaders
used fixed group calls. Ampere+ retained the original loop.

Candidate and restored focused exact tests passed. All 24 order-reversed rows
matched the established aggregate output:

| Format | Parent | Fused group | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.469 ms/image | 38.798 ms/image | 0.671 ms/image |
| JPEG lossy | 39.525 ms/image | 38.644 ms/image | 0.881 ms/image |

The source was restored because neither format reached 1.5 ms/image. Evidence
under `libwebp-i4-pred-group-fusion-*` includes the exact patch, refreshed
batch/device/CPU profile, all timing rows, tests, and computed summary. This
result is RTX 2080 SUPER-only and changes no Ampere+ setting or claim.

## Pre-Ampere min/max reconstruction clipping

The retained I4 phase still consumed 63.8% of photo and 65.5% of texture
block cycles. Parsing the texture-medium output found token partitions between
137,336 and 152,730 bytes, only an 11.2% imbalance caused by the standard
75-row modulo-eight assignment; all eight coders already run concurrently.
The next candidate instead changed the frequently inlined pre-Ampere
`CudaClip8b` to signed min/max saturation while preserving Ampere+ source.

The sm_75 decimate kernel shortened by 240 instructions without changing its
103 registers, 352-byte stack, or 23,392-byte shared allocation. Candidate and
restored focused exact tests passed. All 24 timing rows matched aggregate
output:

| Format | Parent | Min/max clip | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.459 ms/image | 39.063 ms/image | 0.396 ms/image |
| JPEG lossy | 39.500 ms/image | 39.486 ms/image | 0.014 ms/image |

The code-size improvement did not move the critical path, so the candidate was
removed. Exact artifacts are under `libwebp-i4-clip-minmax-*`. This result is
RTX 2080 SUPER-only and changes no Ampere+ behavior, threshold, or claim.

## Pre-Ampere vectorized I4 transform row I/O

The refreshed medium phase trace measured I4 at 63.8% of photo and 65.2% of
texture block cycles. Native SASS inspection found the aligned source,
prediction, and reconstructed rows in the four-lane transform still used
byte-wide shared-memory operations. The candidate used `uchar4` loads and a
packed output store on pre-Ampere only; Ampere+ retained the existing source.

The DecimateKernel kept 103 registers, a 352-byte stack, and 23,392 shared
bytes. Static byte operations fell by twelve loads and four stores, but the
extraction/packing sequence grew the kernel from 23,704 to 23,712
instructions. Candidate and restored focused exact tests passed, and all 24
timing rows retained the format-specific output:

| Format | Parent | Vector row I/O | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.501 ms/image | 39.400 ms/image | 0.101 ms/image |
| JPEG lossy | 39.922 ms/image | 39.533 ms/image | 0.389 ms/image |

The source was restored because neither format reached 1.5 ms/image. Evidence
under `libwebp-i4-vector-rowio-*` includes the exact patch, complete
parent/candidate sm_75 SASS, profile/resource counts, all timing rows, tests,
and computed summary. This result is RTX 2080 SUPER-only and changes no
Ampere+ behavior, threshold, or performance claim.

## Portable lossy-decimate CUDA/FPGA conformance

Issue #19 added an opt-in WPDCRD schema-1/ABI-12 fixture generator and
standalone loopback/CUDA/FPGA runner. The native-sm_75 validation corpus held
132 CPU-golden fixtures and 48,968 macroblocks spanning methods 3--6,
qualities 0/25/75/98/100, graphic/photo/texture content, tiny/odd/aligned
geometry, synthetic flat ties, high contrast, all segment IDs, and every
I4/I16/UV prediction mode. It included 8,570 zero-nz and 40,398 nonzero-nz
macroblocks, the complete `0x01ffffff` nonzero-bit union, signed coefficient
extrema -434/619, 120 diffusion cases, 80 banded cases, and 96 partial edges.

All 132 whole-pass and all 132 streaming CUDA submissions matched every
result/reconstruction byte. Event timing separated wavefront execution from
result transfer. The focused end-to-end test matched methods 3--6 across
qualities 75/99, one/two passes, padded strides, all band remainders, and
forced collect/download fallback. A 90-cell methods 2--6, qualities 25/75/98
matrix over graphic/photo/texture at 17x13 and 257x255 matched CPU/CUDA output
SHA-256 and byte counts exactly.

The archived 94/132 initial oracle rows exposed that method 5's final CPU
score contains a second diffusion value that is intentionally discarded after
the earlier state has been published. Corrected capture records the published
neighbor state and canonical zeros for inactive bytes; corrected reruns are
132/132 exact. The default CPU build contains neither harness nor FPGA object.
Raw artifacts use `libwebp-decimate-conformance-*`. This is a conformance
result, not a speed claim; native architecture configuration and the retained
Turing/Ampere+ dispatch split are unchanged.

## NVDEC-backed lossy WebP input path

Issue #16 began with a retained-source profile at
`374ee38ab20af1f3f2f02c371aa90fc59cfab75d`, before its source changes. The
native-sm_75 CPU-decode/CUDA-encode batch median was 39.677 ms/image on the
1600x1200 graphic WebP. The direct stage profiler measured 34.923 ms total,
11.713 ms lossy analysis, 22.882 ms lossy encode loop, and 19.612 ms lossy
decimation. That isolated input CPU decode/preparation at roughly 4.75 ms and
selected a device-native input boundary rather than another exhausted I4
residual specialization.

The private opt-in `webp_cuda_transcode` tool strictly parses one complete
RIFF object and accepts only one opaque lossy `VP8 ` payload with matching
container and key-frame dimensions. NVDEC produces NV12; a GPU kernel splits
the chroma plane, and the encoder copies Y/U/V device-to-device into
backend-owned storage before unmapping the decoder surface. Host placeholder
identity binds the transaction. Both lossy analysis and decimation must report
CUDA success or the candidate output is discarded and the complete image is
CPU-decoded and encoded again. ICCP/EXIF/XMP payloads are copied byte-for-byte;
alpha, lossless, animation, multiple-image, geometry, capability, device, and
runtime failures decline with stable reasons.

The Video Codec SDK headers came from official SDK sample commit
`aa3544dcea2fe63122e4feb83bf805ea40e58dbe`; the driver supplied
`libnvcuvid`. The build used CUDA 12.0, driver 595.84, and exactly
`-DCMAKE_CUDA_ARCHITECTURES=native`. Default CPU and policy-only CPU builds,
CUDA with the transcoder tests but NVDEC disabled, and explicit NVDEC without
the SDK were all exercised. The first three built without an SDK dependency;
the last failed configuration with the intended diagnostic.

### Warm throughput

For each 1600x1200 graphic, photo, and texture WebP, four fresh process pairs
alternated CPU/NVDEC order. Each process discarded three warmups and retained
ten measurements, yielding 40 rows per backend and content type.

| Input | CPU median | NVDEC median | Gain | CPU images/s | NVDEC images/s |
|---|---:|---:|---:|---:|---:|
| Graphic | 27.627 ms | 24.689 ms | 2.938 ms | 36.20 | 40.50 |
| Photo | 42.628 ms | 29.986 ms | 12.642 ms | 23.46 | 33.35 |
| Texture | 152.499 ms | 95.013 ms | 57.486 ms | 6.56 | 10.52 |

The graphic gain clears 1.5 ms despite having little CPU decode work; photo
and texture benefit substantially more. Texture's NVDEC encode phase was
slower than the CPU-order counterpart, but its decode reduction still yielded
the 57.486 ms end-to-end gain.

### Cold process latency

Eight fresh, order-balanced processes per backend included all CUDA and
NVDEC initialization:

| Input | CPU median | NVDEC median | Gain | CPU images/s | NVDEC images/s |
|---|---:|---:|---:|---:|---:|
| Graphic | 171.063 ms | 190.908 ms | -19.845 ms | 5.85 | 5.24 |
| Photo | 182.777 ms | 190.315 ms | -7.537 ms | 5.47 | 5.25 |
| Texture | 298.034 ms | 251.066 ms | 46.968 ms | 3.36 | 3.98 |

NVDEC parser/decoder creation costs roughly 160 ms on this Turing driver, so
graphic and photo cold single-image processes regress. The measured result is
therefore retained only as a warm persistent-session throughput path. The
tool reports cold behavior rather than hiding it.

### Correctness, lifetime, and fallback

Nine direct `--verify` rows (three per content type) matched CPU-reference
dimensions and produced byte-identical decoded output and bitstreams, reported
as 99 dB. Direct rows transferred exactly 5,760,000 decoded-plane bytes D2D
(decoder-to-analysis plus analysis-to-decimation-arena) and zero decoded-plane
bytes H2D or D2H. Output hashes and counts were:

| Input | SHA-256 | Bytes |
|---|---|---:|
| Graphic | `dedeac1e41c28bf952817345714618c0b11a09fef298e730c2646a0e9abf358b` | 12,986 |
| Photo | `85b869d6a504aeea38cc15445d7c0d0318dc945290f365f4065abf7ef77375b2` | 239,436 |
| Texture | `13dcd63ba540b6aedd7c0b253d1c843da2974175fd5d9e377ce4df6b38d38ee9` | 1,167,310 |

The 189-pair CPU/NVDEC matrix covered graphic/photo/texture at 17x13,
257x255, and 1600x1200, methods 0--6, and qualities 25/75/98. All hashes and
byte counts matched: 36 medium method-3--6 cases stayed direct, 126 tiny/odd
cases retried after NVDEC sequence geometry declined, and 27 medium method-0--2
cases retried after a required CUDA encoder stage declined. A separate
device-upload test exercised qualities 0/25/75/98/100 and produced 114/114
exact direct or transactional-retry bitstreams, including eight repetitions.

Injected parser, decoder, map, allocation, and handoff failures plus an absent
device all matched the CPU reference hash. The alpha plane's decoded PGM hash
matched exactly, as did the 18,826-byte ICCP, 1,496-byte EXIF, and 3,279-byte
XMP payloads. Truncated RIFF input
returned failure without changing a pre-existing destination. Eight concurrent
processes completed 32 verified photo transcodes; every row stayed on NVDEC,
reported no host round trip, and produced the same hash and byte count.

Five focused tests passed: policy, external device YUV, existing CUDA
concurrency, trellis, and near-lossless. The established silent
`cuda_histogram_test` failure reproduced unchanged. Compute Sanitizer 2022.4.1
could not instrument this CUDA 12/driver 595 combination and terminated before
its first instrumented API call; the failure is archived and not represented
as a sanitizer pass. On this VP8/Turing route `cuvidGetDecodeStatus` likewise
returns `CUDA_ERROR_NOT_SUPPORTED` (801); the tool records that diagnostic and
rejects an unconcealed hard error only when the query itself succeeds, matching
the official SDK sample policy.

Raw inputs, outputs, JSONL rows, parity table, configuration/build/test logs,
and protocol are archived under `libwebp-nvdec-*`. No RTX 5070 Ti was
available. Issue #16's second-hardware acceptance item remains open, and this
report makes no Blackwell or cross-hardware claim. Existing warm/cold
decimation thresholds remain pre-Ampere 784/12,544 and Ampere+ 64/4,000
macroblocks; the architecture split was not changed.

## Lossy-analysis benchmark-control correction

At retained base `eb38392bb014f701f75b1666a1d9e7daf359ddef`, an isolated
native-sm_75 `cwebp` refresh validly measured CPU lossy analysis at
11.644 ms graphic, 9.721 ms photo, and 9.662 ms texture. Explicit CUDA
analysis reduced those intervals to 1.043, 1.002, and 1.008 ms. The subsequent
batch policy measurements, however, did not exercise their labeled controls.

`webp_cuda_batch_benchmark --force-cuda` calls `ConfigureDispatch()` after
startup and unconditionally writes both `WEBP_CUDA_LOSSY_ANALYSIS=1` and
`WEBP_CUDA_FUSED_LOSSY_ANALYSIS=1`. This overwrote every attempted baseline
and candidate environment setting in the 60-row automatic-policy gate and the
24-row fused screen. All archived rows are exact repeated measurements of the
same already-forced fused path, not valid A/B cells. Their prior gain tables
are withdrawn.

The temporary pre-Ampere automatic-default source was restored; the fused
screen changed no source. Both remain opt-in in production, and neither is a
candidate for the required forced-CUDA benchmark because that benchmark
already activates them. Corrected summaries accompany the unchanged raw rows
under `libwebp-lossy-analysis-default-*` and
`libwebp-fused-lossy-analysis-screen-*`. Ampere+ behavior and the existing
Turing/Ampere+ decimation threshold split are unchanged.

## Whole-program token-recording screen

The current-source whole-process profiles used the frozen six-image PNG and
JPEG sets, forced CUDA lossy encoding, method 4, quality 75, batch 24, one
warmup, and eight retained samples. PNG accumulated 2.602 seconds of CPU
samples, of which `VP8RecordCoeffTokens` held 1.481 seconds (56.92%
exclusive) and `VP8PutTokenPage` held 0.230 seconds. `ReadPNG` was 0.250
seconds inclusive. JPEG accumulated 2.632 seconds: token recording held 1.521
seconds (57.79%), page allocation 0.240 seconds, and `ReadJPEG` 0.230 seconds
inclusive. The decode totals correspond to only about 1.2--1.3 ms/image and
do not support a gate-sized decode-ahead candidate on this workload.

The selected candidate enabled whole-program interprocedural optimization to
cross the `frame_enc.c` / `token_enc.c` call boundary. The initial GCC 13
build exposed a real CUDA toolchain constraint: the CUDA link driver invokes
GCC 12, whose LTO plugin cannot read GCC 13 bytecode. The measured A/B
therefore used paired GCC 12.4 builds. Both were Release and configured with
exactly `-DCMAKE_CUDA_ARCHITECTURES=native`; only the candidate set
`-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON`.

Two order-reversed process pairs per input format yielded six control and six
IPO samples each:

| Format | Control | IPO | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 39.575 ms/image | 39.281 ms/image | 0.294 ms/image | `ace64e860de89b43` / 6,441,688 |
| JPEG lossy | 39.630 ms/image | 39.174 ms/image | 0.456 ms/image | `1cbb84d2ab926db3` / 6,400,792 |

The 24 timing rows were exact, but both gains are noise under 1.5 ms/image.
IPO was rejected without changing repository source. Full gprofng archives,
raw timing rows, build hashes, configuration, and the toolchain feasibility
failure are under `libwebp-token-ipo-*`. The Turing/Ampere+ threshold split
and all architecture defaults remain unchanged.

The same clean boundary was used to load all GitHub issues. This machine
reports RTX 2080 SUPER, compute capability 7.5; it has CUDA 12 nvJPEG headers
and library but cannot exercise Blackwell's hardware decoder. #19 was already
closed. #16's implementation remains open for its required RTX 5070 Ti
measurements, #17 remains blocked on Blackwell implementation/validation, and
#18 remains blocked on per-encode accelerator sessions/tickets and dual-GPU
benchmarking. Those measured capability and safety blockers were posted to
the three open issues rather than closing unmet acceptance criteria.

## Packed adjacent coefficient-token rejection

The current annotated gprofng view localized the dominant token recorder to
packed-token stores and adaptive-statistics read/modify/write operations.
Existing optimized coverage provided the branch population: 117.4 million
coefficient iterations were 60.0% nonzero, while only 4,596 of 362.7 million
statistics events renormalized. The next candidate therefore paired the
`v != 0` and `v > 1` token/stat updates that every nonzero coefficient emits.

On the common in-page path, generated x86-64 used one 32-bit token store and
one 64-bit load/store for the adjacent statistics. The page-boundary path
retained the original scalar allocation/failure semantics. That fallback and
the explicit zero branch nevertheless grew `VP8RecordCoeffTokens` from 4,976
to 5,346 bytes.

The native candidate passed concurrency, trellis, and near-lossless focused
tests. Two order-reversed processes per format, one warmup and three retained
batch-24 samples per process, produced exact aggregate output in all 24 rows:

| Format | Parent | Packed pair | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 41.012 ms/image | 43.978 ms/image | -2.966 ms/image | `ace64e860de89b43` / 6,441,688 |
| JPEG lossy | 40.519 ms/image | 41.443 ms/image | -0.924 ms/image | `1cbb84d2ab926db3` / 6,400,792 |

Both formats regressed, so source was restored immediately. Exact patch, raw
screen, executable hashes, tests, and decision are under
`libwebp-token-pair-*`; the selecting raw profiles are the preceding
`libwebp-token-ipo-profile-*` archives. This result is RTX 2080 SUPER-only and
does not change the Turing/Ampere+ architecture split.

## Token generation/statistics split rejection

The current native-sm_75 stage refresh continued to show a sizeable CPU token
boundary on realistic inputs, consistent with the whole-process profiles that
attribute 56.92% of PNG and 57.79% of JPEG exclusive CPU samples to
`VP8RecordCoeffTokens`. This selected a coarse overlap experiment after the
scalar token and residual specializations were exhausted.

The candidate emitted the identical token stream on the existing recorder
worker and recorded adaptive statistics on the main thread in exact
macroblock raster order. The first feasibility version used generic
`VP8RecordCoeffs`; method 3 / quality 99 correctly exposed that its event
ordering differs when a counter renormalizes. The timed version used an
exact-order statistics mirror and passed the focused trellis/fallback,
concurrency, and near-lossless tests.

Two order-reversed process pairs per input format, each with one warmup and
five retained batch-24 samples, measured:

| Format | Parent | Split candidate | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 40.451 ms/image | 39.507 ms/image | 0.944 ms/image | `99f33682e7cc9063` / 6,441,688 |
| JPEG lossy | 39.620 ms/image | 38.728 ms/image | 0.891 ms/image | `1b9eceb1d93cad23` / 6,400,792 |

All 40 timing rows matched their format's exact aggregate hash and byte count,
but neither gain reached 1.5 ms/image. Source was restored and the restored
focused tests passed. Raw profile, patch, build identity, rows, tests, and
decision use the `libwebp-token-stats-split-*` prefix. This measurement is
RTX 2080 SUPER-only and leaves the pre-Ampere 784/12,544 and Ampere+ 64/4,000
warm/cold macroblock thresholds unchanged.

## Repeated output-write bound and I4 numeric subdivision

The current retained executable was sampled directly under the required
forced-CUDA batch-24 method-4/quality-75 workload. Across the frozen PNG set,
gprofng accumulated 1.271 CPU seconds and attributed only 0.010 seconds
inclusive (0.79%) to `VP8EncWrite`; JPEG accumulated 1.251 seconds with the
same 0.010 seconds inclusive (0.80%). `WebPMemoryWrite` had no exclusive
samples. Thus the much larger cold-process `cwebp` write-stage number does not
support an output writer candidate for the repeated performance gate.

The next removable native-sm_75 clock probe split the independently profiled
I4 transform/quantization interval. Across PNG/JPEG decoded graphic, photo,
and texture inputs, forward transform represented 15.0--15.5%, basic
quantization 60.5--61.6%, and inverse transform 23.1--24.1%. Quantization is
the clear local sub-bottleneck, but the retained history already tested its
distinct implementation choices: eight-lane distribution, forward/quantize/
inverse register fusion, shared segment matrices, and uniform-AC scalar
caching. Each was exact and below 1.5 ms/image, so none was repeated.

The instrumented and restored trees both passed the trellis test, including
padded strides, every band remainder, and transactional fallback. Source is
clean. Full sampling archives, function reports, and benchmark rows use
`libwebp-output-write-profile-*`; the exact diagnostic patch, raw cycle rows,
native build identity, tests, and computed summary use
`libwebp-i4-transform-split-*`. This is RTX 2080 SUPER-only evidence and
leaves the pre-Ampere 784/12,544 and Ampere+ 64/4,000 warm/cold macroblock
thresholds unchanged.


## Direct result-to-bitwriter rejection

The selecting current-source repeated-batch profile attributed 52.8% of PNG
and 55.2% of JPEG exclusive CPU samples to `VP8RecordCoeffTokens`, with
`VP8PutTokenPage` at about 5.5%. This justified a distinct coarse experiment:
record exact adaptive statistics only, retain GPU coefficient results through
probability finalization, and encode the eight partitions directly instead of
constructing and replaying packed-token pages. Size-search and transactional
CPU fallback retained the ordinary token path.

An initial feasibility version used each accelerator result's per-block
non-zero decision mask as a packed iterator context word. The frozen PNG/JPEG
hash and byte checks rejected that assumption. A separate packed-context trace
made the corrected implementation exact; it passed basic/trellis outputs,
padded strides, every band remainder, injected fallbacks, concurrent encodes,
and 20 near-lossless cases.

Two reversed-order process pairs, one warmup and five retained forced-CUDA
batch-24 samples per process, measured:

| Format | Parent | Direct result coding | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 41.328 ms/image | 44.319 ms/image | -2.991 ms/image | `99f33682e7cc9063` / 6,441,688 |
| JPEG lossy | 39.839 ms/image | 42.924 ms/image | -3.085 ms/image | `1b9eceb1d93cad23` / 6,400,792 |

All 40 corrected timing rows were exact, but direct `PutCoeffs` traversal was
about 3 ms/image slower in both formats than the compact token emitter. Source
was restored and the restored trellis/fallback, concurrency, and near-lossless
tests passed. The invalid feasibility rows are preserved separately from the
corrected gate; all raw artifacts use `libwebp-direct-result-tokens-*`. This
is RTX 2080 SUPER-only evidence and leaves the Turing/Ampere+ thresholds and
defaults unchanged.


## Adaptive token-statistics batching rejection

A retained native phase refresh put realistic photo/texture I4 at
63.2--65.2% of block cycles, but its remaining numeric, metric, prediction,
and scheduling subdivisions are exhausted. The independent host profile still
places 52.8--55.2% of CPU samples in `VP8RecordCoeffTokens`, with adaptive
statistics read/modify/write among its largest instruction clusters.

The candidate preserved each statistics slot's event order in 16-bit batches.
It applied one packed counter addition when no saturation boundary occurred
and replayed the original bits at the rare boundary. An initial token-indexed
draft failed method-3 quality-99 because Cat5/Cat6 token slot 10 intentionally
updates statistics slot 9; the corrected implementation keyed the actual
statistics pointer and passed trellis/fallback, concurrency, and near-lossless.

Two reversed-order, three-sample batch-24 pairs were exact:

| Format | Parent | Batched stats | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 42.325 ms/image | 42.313 ms/image | 0.012 ms/image | `99f33682e7cc9063` / 6,441,688 |
| JPEG lossy | 42.376 ms/image | 42.270 ms/image | 0.106 ms/image | `1b9eceb1d93cad23` / 6,400,792 |

Both changes are noise. The cache-hot batch update merely replaced the
cache-hot packed counter update, so source was restored and all focused tests
passed again. Evidence uses `libwebp-token-stats-batch-*`. RTX 2080 SUPER
only; architecture thresholds and Ampere+ behavior are unchanged.


## Pre-Ampere UV warp-reduction rejection

Fresh native batch medians were 39.63 ms/image PNG and 39.82 JPEG. Stage
records averaged 20.92/19.79 ms in accelerated decimation and 2.94/2.97 ms
in token emission. Device phase traces placed UV numeric work at 5--7% of
realistic block cycles, the largest unexhausted non-I4 numeric interval.

A Turing-only candidate replaced the eight nonzero atomics and eight SSE
atomics for each of four UV modes with exact eight-lane ballot/shuffle
reductions. The environment-off and Ampere+ paths retained the original
atomics. Trellis including transactional fallback, concurrency, and
near-lossless tests passed. All 24 order-reversed timing rows were exact:

| Format | Parent | UV warp reduction | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 39.472 ms/image | 39.577 ms/image | -0.104 ms/image | `99f33682e7cc9063` / 6,441,688 |
| JPEG lossy | 39.575 ms/image | 39.457 ms/image | 0.118 ms/image | `1b9eceb1d93cad23` / 6,400,792 |

The shared atomics were not critical, so source was restored and the restored
focused tests passed. Raw profiles, rows, patch, resources, identities, and
tests use `libwebp-uv-warp-reduce-*`. No Ampere+ behavior or threshold
changed.


## Pre-Ampere compressed-input predecode pipeline retention

A native retained refresh measured 39.74 ms/image PNG and 39.67 JPEG. The
encoder stage profiler accounted for 27.18/26.47 ms; a temporary batch phase
probe localized the common outer gap to compressed-input decode/import at
11.71/12.30 ms/image. Output hashing was only about 0.25 ms/image. The device
profile still placed realistic I4 at 63--65%, but its measured subdivisions
and residual specializations are exhausted, so the decode wall was the
largest distinct addressable cost.

The retained internal batch-tool path keeps two decoded-picture slots. A
portable worker reads and decodes N+1 while the main thread serially encodes
N. There is no concurrent `WebPEncode`, CUDA work remains serialized, results
stay ordered, memory is bounded to one lookahead picture, and worker setup
failure uses the old serial loop. The default is restricted to pre-Ampere;
Ampere+ remains unchanged. `WEBP_CUDA_BATCH_PREDECODE=0` restores serial
decode, while `=1` is the explicit measurement override.

| Measurement | Format | Restore | Retained | Gain |
|---|---|---:|---:|---:|
| Reversed-order batch, no file I/O | PNG lossy | 39.271 | 29.351 | 9.919 ms/image |
| Reversed-order batch, no file I/O | JPEG lossy | 39.557 | 28.128 | 11.429 ms/image |
| Official suite, file I/O included | PNG lossy | 39.615 | 28.257 | 11.358 ms/image |
| Official suite, file I/O included | JPEG lossy | 39.630 | 29.429 | 10.200 ms/image |

The retained official rows are 3.24x PNG and 3.04x JPEG versus CPU. All
180/180 official validation pairs passed. Two 75-cell file-I/O-off/on
matrices were exact across methods 2--6, qualities 25/75/98, content classes,
and tiny/odd inputs; 30 injected fallback cells and 20 deterministic rows
were exact. Trellis/fallback, concurrent-encoder, and near-lossless focused
tests passed. Evidence uses `libwebp-predecode-pipeline-*`; the publication
corpus/generator and architecture-specific decimate thresholds are untouched.


## Post-predecode residual profile and scheduler rejection

The retained branch refresh measured 29.422 ms/image PNG and 27.537 JPEG at
method 4 / quality 75 with file I/O. Exact aggregates remained
`ace64e860de89b43` / 6,441,688 and `1cbb84d2ab926db3` / 6,400,792. The stage
profiler measured 19.146/18.631 ms/image in accelerated decimation,
3.011/2.992 in token emission, 1.648/1.336 in output writing, and
1.326/1.332 in import. Device phase traces kept I4 at 63.0--65.2% on realistic
photo/texture inputs.

Two removable timing probes ruled out shallow extensions of the retained
pipeline. Across retained samples, the compressed-input worker wait median was
1.534 ms/image PNG but only 0.551 JPEG. Token-worker lifecycle
setup/synchronization/teardown totaled 0.747/0.764 ms/image. Both have a
two-format upper bound below the retention gate.

A two-process profile then showed that the machine has cross-image capacity:

| Format | Sequential aggregate | Concurrent aggregate | Gain |
|---|---:|---:|---:|
| PNG lossy | 29.211 ms/image | 19.308 ms/image | 9.904 ms/image |
| JPEG lossy | 27.785 ms/image | 18.167 ms/image | 9.618 ms/image |

Every child process retained the exact expected hash and byte count. The
profile therefore selected multi-image ownership, but isolated CUDA contexts
are only a capacity bound.

The in-process candidate gave two workers separate persistent CUDA and
decimate state, first with two streams and then with the design's one-GPU-slot
final-band gate. Same-context concurrent kernels were neutral; the one-slot
form regressed PNG 28.917→30.320 ms/image and JPEG 27.295→30.170. All recorded
method-4/quality-75 rows were deterministic and exact, but the candidate failed
performance before the broad methods/qualities/tiny/fallback matrix and was
fully removed. The result confirms that raw concurrent `WebPEncode` cannot
substitute for the explicit prepare/GPU/finalize refactor and ticketed session
ownership in `doc/async-multi-image-encoder-design-20260819.md`.

Raw retained profiles and fixed-cost probes use `libwebp-predecode-next-*` and
`libwebp-token-worker-next-*`; process capacity uses
`libwebp-cross-image-capacity-*`; candidate iterations and the removed patch
use `libwebp-two-slot-*`, `libwebp-one-slot-*`, and
`libwebp-inprocess-two-worker-*`. This is Turing-only evidence. Ampere+
defaults, the 64/4,000 vs 784/12,544 macroblock split, frozen publication
corpus, and generator are unchanged.


## Line-resolved decimate counters and static raster-commit rejection

At retained parent `8c8cbd79140feffd992390c9b719d7dca9045360`, a separate
Release build used `-DCMAKE_CUDA_ARCHITECTURES=native` and `-lineinfo` to
capture full Nsight Compute source counters. The method-4/quality-75
photo-medium command encoded a 206,128-byte output with SHA-256
`33a12dd7db111a5d8c1ec8b872a9e951bf7edb643d54cbf702f92d5acc924480`.

The sampled 50-CTA by 256-thread diagonal took 117.79 us. Its 103 registers
per thread and 23.39 KiB shared memory each capped residency at two CTAs/SM;
theoretical occupancy was 50% and achieved occupancy 26.04%. Schedulers
averaged 2.08 active but only 0.12 eligible warps, leaving no eligible warp in
89.34% of cycles. CTA barriers consumed 11.12 of 19.55 warp cycles per
instruction (57.0%). DRAM throughput was only 0.79%, with 93.89% L1/TEX and
86.89% L2 hit rates.

The source view counted 334,803 excess shared wavefronts out of 846,791
(40%). Its largest sites were scalar 4x4 SSE/Hadamard loads and basic
quantization, which the existing cooperative-metric, vector-row-I/O,
eight-lane-quantization, fused-register, shared-matrix, and uniform-AC
experiments already rejected. No repeated shared-layout candidate was opened.

The largest individual not-issued barrier attribution was the raster-order I4
commit loop at 901 samples, ahead of the transform/quantization barrier at 770
and metric barrier at 644. The one pre-Ampere candidate replaced
`i4_ready[]`/`i4_next_commit` with the exact static raster ranges produced by
the ten dependency diagonals. Ampere+ retained the original scan. Registers
and stack stayed at 103/352 bytes; shared memory fell 23,392 to 23,376 bytes.

Candidate and restored native builds passed all seven focused CTests. Two
order-reversed process pairs per format produced 24 exact timing rows:

| Format | Parent | Static commit | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 34.662 ms/image | 35.642 ms/image | -0.980 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 35.022 ms/image | 34.589 ms/image | 0.434 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

The candidate was removed because PNG regressed and JPEG was noise under the
1.5 ms/image gate. The compressed raw report, source/SASS CSV, exact patch,
resources, build/test transcripts, and timing rows use the
`libwebp-decimate-source-counters-*` and `libwebp-raster-commit-*` prefixes.
This is Turing-only evidence. The 784/12,544 pre-Ampere and 64/4,000 Ampere+
decimate thresholds, frozen corpus, and generator remain unchanged.


## Retained token profile and dense-transition rejection

At parent `735de11509a65cc223342dcb5bebc2f7e04af778`, native batch-24
file-I/O rows retained the exact aggregate PNG output
`455f70a1e139f043` / 6,441,688 bytes and JPEG output
`0c4b078d5c4d3173` / 6,400,792. The current stage profile measured:

| Format | total | encode loop | decimate | emit tokens | write | import |
|---|---:|---:|---:|---:|---:|---:|
| PNG | 28.266 | 24.793 | 18.655 | 3.868 | 2.059 | 1.356 |
| JPEG | 28.493 | 24.995 | 18.877 | 4.079 | 2.062 | 1.363 |

The leading decimate/I4 sites were already covered by exact rejected
experiments, so the 3.9--4.1 ms token boundary was the largest distinct
target. Whole-process `gprofng` attributed about 30% exclusively to
coefficient recording, but a zero-loss 24K-cycle `perf` profile across all
eight emit workers put `VP8PutTokenPage` first at 35.41%, versus 12.46% for
`VP8RecordCoeffTokens`.

Line-resolved annotation placed the page cycles in the serial probability,
split, bit/range, and normalization chain. A no-source-change gcov build
counted 292,171,248 page tokens: 82.20% dynamic probabilities, 54.89% one
bits, and 53.65% normalization. Buffer growth occurred only 512 times among
24,068,432 ordinary non-0xff flushes. The distributions ruled out another
branchy common-case specialization.

One coarse candidate generated a thread-safe 65,536-entry table indexed by
normalized range, probability, and bit. Each 32-bit entry packed the exact
value increment, normalization shift, and next range. It replaced the split
multiply, bit/range decision, and two normalization loads with one lookup,
shrinking the function from 764 to 708 bytes at a 256-KiB BSS cost.

Two order-balanced native processes per format produced 24 exact timing rows:

| Format | Parent | Transition table | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 35.380 ms/image | 35.117 ms/image | 0.263 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 34.541 ms/image | 35.848 ms/image | -1.308 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

The dense random lookup was noise on PNG and materially slower on JPEG, so it
was removed before broad validation. The focused bit-writer test passed on
the candidate; the restored native tree passed all seven focused CTests.
Fresh 1/2/4/8-partition controls also confirmed that the retained eight
partitions remain fastest, especially for JPEG.

Raw retained profiles, coverage, compressed `gprofng` and `perf` captures,
exact patch, disassemblies, tests, and timing rows use
`libwebp-next-loop-*` and `libwebp-token-transition-*`. This is Ryzen 9
3900X / RTX 2080 SUPER evidence only. Ampere+ behavior, the 784/12,544
pre-Ampere and 64/4,000 Ampere+ thresholds, frozen corpus, and generator are
unchanged.


## Eight-partition AVX2 token-coder rejection

The retained native profile identified token emission as the largest distinct
boundary after the leading decimate/I4 sites were exhausted. Across all eight
emit workers, zero-loss whole-process sampling attributed 35.41% of cycles to
`VP8PutTokenPage`; fresh partition controls retained eight partitions as the
fastest layout.

At parent `079ddbd8002c871d9a169d6b70e916790ac75a77`, one coarse candidate
replaced those eight OS-thread page coders with one AVX2 lockstep routine. The
routine kept eight independent boolean-coder states, used vector range/value
transitions, and retained scalar token/probability loads and byte/run flushes.
It compiled to 2,758 bytes, versus 764 bytes for the scalar page coder.

The native Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. One warmup
and three measured batch-24 file-I/O rows per build and format produced:

| Format | Parent | AVX2 lockstep | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 36.791 ms/image | 48.201 ms/image | -11.410 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 35.072 ms/image | 51.666 ms/image | -16.594 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

All 12 timing rows were exact. Candidate and restored builds passed 7/7
focused CTests after the candidate build's initially disabled histogram option
was aligned with the parent. The source was restored because replacing eight
Ryzen workers with one SIMD thread severely regressed both formats. Raw exact
patch, cache, builds, tests, symbols, disassembly, and timings use
`libwebp-token-simd8-*`. This is Ryzen 9 3900X / RTX 2080 SUPER evidence only;
Ampere+ behavior, the 784/12,544 pre-Ampere and 64/4,000 Ampere+ thresholds,
frozen corpus, and generator are unchanged.


## Pre-Ampere pinned decimate-result staging rejection

At parent `98518b71c31218bd2041c820dac6da9f50b59bca`, a refreshed native
stage profile measured decimation at 18.927 ms/image PNG and 18.666 JPEG. The
remaining 3.934/3.806 ms token boundary had just exhausted a coarse AVX2
mapping, while device timing kept I4 at about 63--65% of photo/texture block
cycles with its leading residual, scheduling, barrier, and layout avenues
already exhausted.

The next distinct profile measured the streaming result path. Seven warm
method-4/quality-75 conformance repetitions per content class reported
1.534--1.536 ms of transfer against 20.778--21.686 ms GPU execution. Each of
eight bands used four device-to-pageable-host copies and then committed the
same result/Y/U/V bytes to encoder-owned output.

One pre-Ampere-only candidate allocated staging with `cudaHostAlloc`, falling
back safely to ordinary host memory; Ampere+ stayed byte-for-byte unchanged.
Pinned staging reduced event-timed transfer to 0.732--0.733 ms but callback
wall by only about 0.05--0.08 ms, confirming that existing stream overlap and
the host commit hide most of the apparent transfer bound.

One warmup and three measured native batch-24 file-I/O rows per variant and
format produced:

| Format | Pageable parent | Pinned candidate | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 35.695 ms/image | 35.976 ms/image | -0.281 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 36.239 ms/image | 35.385 ms/image | 0.854 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

All 12 timing and 48 conformance rows were exact. Candidate and restored
builds passed 7/7 focused CTests. Source was restored because PNG regressed
and JPEG missed the 1.5 ms/image gate. Raw evidence uses
`libwebp-pinned-staging-*`. This is Ryzen 9 3900X / RTX 2080 SUPER evidence
only; the 784/12,544 pre-Ampere and 64/4,000 Ampere+ thresholds, Ampere+
behavior, frozen corpus, and generator remain unchanged.


## Pre-Ampere packed I4 residual-load rejection

At parent `4565c4206fa427460e05258e2aaa8c418211a24d`, the refreshed native
profile still measured decimation at 18.927 ms/image PNG and 18.666 JPEG. I4
accounted for about 63--65% of realistic photo/texture block cycles, with the
scalar residual scorer its largest warp after the previously rejected scan,
subgroup, fixed-cost, table, handoff, and coefficient-layout avenues.

The single candidate used four aligned 64-bit shared loads for each contiguous
sixteen-coefficient I4 block on pre-Ampere devices, then ran the unchanged
scalar cost dependency. A uniform runtime flag left Ampere+ on the original
implementation. `cuobjdump` reported 102 registers and 23,392 shared bytes,
versus 103 and 23,392 for the exact parent.

One warmup and three measured native batch-24 file-I/O rows per build and
format produced:

| Format | Parent | Packed loads | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 35.626 ms/image | 35.063 ms/image | 0.563 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 33.736 ms/image | 34.028 ms/image | -0.292 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

All twelve rows were exact. Candidate and restored native builds passed all
eight configured CTests, including trellis, histogram, concurrency,
near-lossless, and decimate conformance self-test. The source was restored
because PNG was below the 1.5 ms/image threshold and JPEG regressed. Raw
evidence uses `libwebp-residual-packed4-*`. This is RTX 2080 SUPER evidence
only; the 784/12,544 pre-Ampere and 64/4,000 Ampere+ thresholds, Ampere+
behavior, frozen corpus, and generator remain unchanged.


## Lossy write-boundary feasibility rejection

At clean parent `3deb8d76784d650cc0f54a34858ae545f55eb6c4`, a native Release
build with `-DCMAKE_CUDA_ARCHITECTURES=native` collected two warmup and eight
measured batch-24 stage iterations. Across 192 measured image records per
format, `VP8EncWrite` averaged 2.148 ms/image PNG and 1.892 JPEG.

The host denied `perf` sampling at `perf_event_paranoid=4`, so `gprofng` clock
profiles covered one warmup and two measured batch-120 iterations per format.
Across all 360 encodes, inclusive `VP8EncWrite` user CPU totaled 50 ms, or
0.139 ms/image. Resolved samples were partition-0 mode-bit coding,
bit-writer cleanup, and memory-writer copying.

A separate one-warmup/one-measured batch-120 `strace` control then provided a
conservative feasibility bound. Every `brk`, `mmap`, `munmap`, and `madvise`
second in the entire 240-encode process—not merely calls under
`VP8EncWrite`—totaled 275.499 ms PNG and 240.139 ms JPEG. Adding those whole-
process memory costs to the write user CPU produced:

| Format | Write wall | Write user CPU | All memory syscalls | Upper bound |
|---|---:|---:|---:|---:|
| PNG lossy | 2.148 ms/image | 0.139 ms/image | 1.148 ms/image | 1.287 ms/image |
| JPEG lossy | 1.892 ms/image | 0.139 ms/image | 1.001 ms/image | 1.139 ms/image |

Because even this impossible deletion of unrelated process work misses the
1.5 ms/image gate in both formats, no output-buffer or partition-assembly
candidate was opened. Raw stage rows, compressed `gprofng` experiments,
function/call-tree reports, syscall summaries, the denied `perf` record, and
the calculation use `libwebp-write-boundary-*`. This is RTX 2080 SUPER-only
evidence; architecture thresholds/defaults, Ampere+ behavior, frozen corpus,
and generator remain unchanged.


## I4-first / I16-pruning feasibility rejection

At clean parent `c0fb63636f5469074686e60ba326bbd822afb0ac`, the native Release
build collected one warmup and three measured batch-24 method-4/quality-75
file-I/O rows. Medians were 36.389 ms/image PNG and 36.417 JPEG, with the
expected aggregate hashes and byte counts. Raw phase timing again assigned
about 63--65% of realistic photo/texture block cycles to I4.

The retained exact medium fixtures then quantified final luma modes:

| Content | I4 | I16 | I4 share |
|---|---:|---:|---:|
| Graphic | 191 | 7,309 | 2.55% |
| Photo | 4,101 | 3,399 | 54.68% |
| Texture | 7,500 | 0 | 100.00% |

The proposed distinct lever was to run I4 first and omit I16 where an exact
bound proves the I4 result wins. It was rejected before implementation. The
retained I4 raster search relies on the completed I16 RD score as its
per-block early-abort threshold; reversing the phases therefore expands work
on graphic inputs, where 97.45% of macroblocks select I16. Final outcome
coverage is not an admissible predictor, and the request has neither an exact
content discriminator nor a sufficiently strong pre-quantization I16 lower
bound. Segment-based guessing would violate byte parity.

No source candidate was opened. Raw native timing, phase traces, fixture
coverage, parent/binary/fixture hashes, and the decision summary are stored
under `libwebp-i4-first-feasibility-*` in the adjacent evidence directory.
The retained source passed all seven registered focused tests after the three
CPU test executables absent from the benchmark-only cache were built. This is
RTX 2080 SUPER-only evidence; the 784/12,544 pre-Ampere and 64/4,000 Ampere+
thresholds, architecture split, frozen corpus, and generator are unchanged.


## Coefficient-token zero-pair feasibility rejection

At clean parent `792e2592cdbda92f19a22ad3f2c6a4cfd50619bc`, the native Release
stage refresh produced exact full-corpus medians of 34.485 ms/image PNG and
35.322 JPEG. Texture-medium remained the critical host case:

| Format | Total | Decimate/collect/replay | Token emit | Write |
|---|---:|---:|---:|---:|
| PNG | 79.262 ms | 47.572 ms | 15.746 ms | 8.563 ms |
| JPEG | 82.280 ms | 47.192 ms | 18.388 ms | 9.477 ms |

Whole-thread texture sampling assigned 46.57% of PNG CPU samples and 43.62%
of JPEG samples to `VP8RecordCoeffTokens`. The restored-source full-corpus
control measured 0.520/0.460 seconds in that function over 72 encodes, equal
to 7.222/6.389 ms/image.

The adjacent ledgers already reject local token-buffer state, packed nonzero
pairs, statistics batching, generation/statistics overlap, and direct result
coding. A temporary counter therefore screened disjoint consecutive-zero
packing before opening another representation candidate. Full-corpus pair
coefficients covered 29.366% PNG and 28.794% JPEG iterations, but one pair can
remove only one store: at most 14.683% and 14.397%. The critical
texture-medium maxima were just 4.138% and 4.124%.

Even deleting the full-corpus fraction of the entire recorder, rather than a
single store while retaining statistics, bounds the benefit at 1.060 ms/image
PNG and 0.920 JPEG. Pair detection and page handling can only lower it. No
representation candidate was implemented; the counter was removed and the
restored tree passed 7/7 focused tests.

Raw exact timing/hashes, stage records, counters, probe patch, annotated
disassembly, full and texture compressed `gprofng` experiments, and restored
build/test logs use `libwebp-token-zero-pair-*` in the adjacent evidence
directory. This is RTX 2080 SUPER-only evidence; the 784/12,544 pre-Ampere and
64/4,000 Ampere+ thresholds, architecture split, frozen corpus, and generator
are unchanged.
