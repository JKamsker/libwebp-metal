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
| Source revision | `3c21eb0d91d7e3464fdfb1ff30e1e911f782be1c` |
| Build | CMake Release, CUDA enabled |

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
  --output-dir /tmp/libwebp-cuda-benchmark-20260818 \
  --label "Ryzen 9 3900X / RTX 2080 SUPER"
```

## Persistent 24-image batch

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 99.8 ms | 60.4 ms | **1.65x** |
| PNG lossless | 141.3 ms | 88.7 ms | **1.59x** |
| PNG near-lossless | 207.6 ms | 89.2 ms | **2.33x** |
| JPEG lossy | 98.1 ms | 61.5 ms | **1.60x** |
| JPEG lossless | 686.4 ms | 144.6 ms | **4.75x** |
| JPEG near-lossless | 787.3 ms | 143.4 ms | **5.49x** |

## Fresh process per image

| Method | CPU time | CUDA time | CUDA speedup |
|---|---:|---:|---:|
| PNG lossy | 100.0 ms | 275.3 ms | **0.36x** |
| PNG lossless | 154.2 ms | 311.8 ms | **0.49x** |
| PNG near-lossless | 220.2 ms | 316.2 ms | **0.70x** |
| JPEG lossy | 101.1 ms | 277.6 ms | **0.36x** |
| JPEG lossless | 693.9 ms | 357.2 ms | **1.94x** |
| JPEG near-lossless | 801.2 ms | 375.1 ms | **2.14x** |

## Validation and interpretation

All six persistent preflight cases and all 180 single-image validation pairs
passed. Lossy CPU/CUDA encodes were required to be byte-identical; lossless
and near-lossless encodes were required to decode to identical pixels. Forced
lossless cases also verified that the requested resident CUDA handoff occurred.

CUDA improved every persistent-batch row. In a fresh process, CUDA startup
cost outweighed the accelerated work for all PNG rows and JPEG lossy, while
the longer JPEG lossless and near-lossless encodes remained faster on CUDA.
