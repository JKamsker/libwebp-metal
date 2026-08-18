# CUDA end-to-end benchmark: Ryzen 9 3900X / RTX 2080 SUPER

Measured on 2026-08-18 UTC. Times are median milliseconds per image and
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
| Source revision | `9393a44d96f626635ba8b6b988fd02759390ac65` |
| Build | CMake Release, CUDA enabled |
| Result label | `win-2080super` |

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
  --build-dir build-cuda-sm75-gate \
  --output-dir /tmp/libwebp-cuda-results-2080super \
  --label "win-2080super"
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
