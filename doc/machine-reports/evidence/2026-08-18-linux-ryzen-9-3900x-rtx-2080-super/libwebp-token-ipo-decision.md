# Token-recording IPO screen

Base: `b9bb9c80e290d9e2cfb7cdeb695444722bedede8`

The refreshed whole-process gprofng profiles sampled the current forced-CUDA
lossy batch path before selecting a source/build candidate. PNG accumulated
2.602 seconds of CPU samples: `VP8RecordCoeffTokens` was 1.481 seconds
(56.92% exclusive, 59.62% inclusive), `VP8PutTokenPage` was 0.230 seconds,
and `ReadPNG` was 0.250 seconds inclusive. JPEG accumulated 2.632 seconds:
`VP8RecordCoeffTokens` was 1.521 seconds (57.79% exclusive, 60.08%
inclusive), `VP8PutTokenPage` was 0.240 seconds, and `ReadJPEG` was 0.230
seconds inclusive. Across 192 retained images per profile, input decode was
only about 1.2--1.3 ms/image and could not independently clear the gate.

The selected distinct candidate was CMake IPO/LTO, intended to optimize the
cross-translation-unit `frame_enc.c` to `token_enc.c` boundary without another
token or residual micro-specialization. The first native build used the
machine-default GCC 13 for C while CMake's CUDA link driver selected GCC 12;
linking correctly rejected GCC 13 LTO bytecode with:

```text
lto1: fatal error: bytecode stream ... generated with LTO version 13.1
instead of the expected 12.0
```

The actual A/B therefore used paired GCC 12.4 control and IPO builds. Both
were Release and used exactly `-DCMAKE_CUDA_ARCHITECTURES=native`. Relevant
configuration and executable identities were:

```text
control: CMAKE_C_COMPILER=/usr/bin/gcc-12
control: CMAKE_CUDA_COMPILER=/usr/bin/nvcc
control: CMAKE_CUDA_ARCHITECTURES=native
IPO:     CMAKE_C_COMPILER=/usr/bin/gcc-12
IPO:     CMAKE_CUDA_COMPILER=/usr/bin/nvcc
IPO:     CMAKE_CUDA_ARCHITECTURES=native
IPO:     CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
control webp_cuda_batch_benchmark SHA-256:
  254f2debeb78e2e22130a1452752eb6d9f96faf2a1cae760d6427df68a4fc1b0
IPO webp_cuda_batch_benchmark SHA-256:
  6d0db0585c8e73daf44a2dda95d8a24eaddafe0d280553f5e2863618e9122d7a
```

Two order-reversed process pairs per format produced 24 retained rows. The
median across the six control and six IPO samples per format was:

| Format | Control | IPO | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 39.575 ms/image | 39.281 ms/image | 0.294 ms/image | `ace64e860de89b43` / 6,441,688 |
| JPEG lossy | 39.630 ms/image | 39.174 ms/image | 0.456 ms/image | `1cbb84d2ab926db3` / 6,400,792 |

All control/candidate aggregate hashes and byte counts were exact. Both gains
are noise under the 1.5 ms/image retention gate, so IPO was rejected without
changing repository source. The raw 24 rows are in
`libwebp-token-ipo-screen.txt`; the full profile experiments are archived as
`libwebp-token-ipo-profile-png.tar.gz` and
`libwebp-token-ipo-profile-jpeg.tar.gz`.

This is an RTX 2080 SUPER/native-sm_75 result. It changes no Turing or Ampere+
default and makes no cross-hardware claim.
