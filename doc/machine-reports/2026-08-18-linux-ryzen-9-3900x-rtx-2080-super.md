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
| Source revision | `4852f92e1075124ab420d2d56524113a54255216` |
| Build | CMake Release, CUDA enabled |
| Result label | `win-2080super-token-local` |

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
  --output-dir /tmp/libwebp-cuda-results-2080super-i4-score-prep \
  --label "win-2080super-i4-score-prep"
```

## Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 103.5 ms | 56.6 ms | **1.83x** |
| PNG lossless | 141.6 ms | 92.1 ms | **1.54x** |
| PNG near-lossless | 210.9 ms | 91.0 ms | **2.32x** |
| JPEG lossy | 99.1 ms | 57.5 ms | **1.72x** |
| JPEG lossless | 713.8 ms | 145.0 ms | **4.92x** |
| JPEG near-lossless | 800.2 ms | 146.2 ms | **5.47x** |

## Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 99.7 ms | 286.0 ms | **0.35x** |
| PNG lossless | 177.7 ms | 315.4 ms | **0.56x** |
| PNG near-lossless | 220.3 ms | 330.8 ms | **0.67x** |
| JPEG lossy | 100.9 ms | 289.5 ms | **0.35x** |
| JPEG lossless | 715.4 ms | 366.6 ms | **1.95x** |
| JPEG near-lossless | 840.2 ms | 392.8 ms | **2.14x** |

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
result is `/tmp/libwebp-cuda-results-2080super-fast-flush/results.json`.
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
raw timing summary is `/tmp/libwebp-i4-balanced-ab.zRywWw.json`.

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
`/tmp/libwebp-combined-level-cost-ab.Xn4ND3.json`.

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
summary is `/tmp/libwebp-small-level-cost-ab.OHZMcV.json`.

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
`/tmp/libwebp-residual-transpose-ab.ffrAEp.json`.

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
local raw summary is `/tmp/libwebp-token-unroll-ab.frMCAJ.json`.

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
`/tmp/libwebp-phase-union-ab.yLDGe1.json`.

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
`/tmp/libwebp-i4-compact-output-ab.4oaeP2.json`.
