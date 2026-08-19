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
| Source revision | `8ae71f74a90aad2754fcfab458d8e4ef0387dfcc` |
| Build | CMake Release, CUDA enabled |
| Result label | `win-2080super-i4-score-prep` |

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
