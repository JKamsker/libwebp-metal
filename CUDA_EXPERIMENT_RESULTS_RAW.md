# CUDA acceleration experiment results — raw

Measurement date: 2026-08-18 UTC  
Source commit: `0fea9bac`  
Measurement branch: `codex/cuda-acceleration-measurements`  
Build directory: `build-cuda-experiments`  
Build type: Release

The raw command lines below are the commands used. Command output is captured
with stderr merged into stdout where `2>&1` is shown. Benchmark CSV rows are
copied without editing. Each benchmark run was a separate process invocation;
the five invocations were run sequentially after the previous process exited.

## Environment

### Timestamp and GPU/driver

```text
date -u 2>&1; nvidia-smi 2>&1
Tue Aug 18 10:16:31 UTC 2026
Tue Aug 18 10:16:31 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.84                 Driver Version: 595.84         CUDA Version: 13.2     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf   Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |                  MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 2080 ...    Off |   00000000:0A:00.0  On |                  N/A |
|  0%   27C    P8             14W /  250W |       9MiB /   8192MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID  ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

The initial pre-build `nvidia-smi 2>&1` capture at 10:12:41 had the same GPU,
driver, CUDA compatibility version, and no running processes. The post-run
capture above also showed no running processes.

### CUDA toolkit

```text
nvcc --version 2>&1
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Fri_Jan__6_16:45:21_PST_2023
Cuda compilation tools, release 12.0, V12.0.140
Build cuda_12.0.r12.0/compiler.32267302_0
```

### Host compiler

```text
gcc --version 2>&1; g++ --version 2>&1; cc --version 2>&1; c++ --version 2>&1
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

cc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

c++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
Copyright (C) 2023 Free Software Foundation, Inc.
There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

### Tool paths and base-image CMake check

```text
command -v cmake || true; command -v nvcc || true; command -v gcc || true; command -v g++ || true; command -v cc || true; command -v c++ || true; command -v make || true; command -v ninja || true; uname -a
/usr/bin/nvcc
/usr/bin/gcc
/usr/bin/g++
/usr/bin/cc
/usr/bin/c++
/usr/bin/make
Linux dev-build-server 6.8.0-137-generic #137-Ubuntu SMP PREEMPT_DYNAMIC Fri Jul 17 20:28:23 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

cmake --version 2>&1
/bin/bash: line 1: cmake: command not found
```

CMake 3.28.3 was used from an unprivileged temporary extraction of the
distribution package; no host packages or repository files were installed or
modified. The exact working CMake version was:

```text
LD_LIBRARY_PATH="$measurement_cmake_dir/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$measurement_cmake_dir/root/usr/bin/cmake" --version 2>&1
cmake version 3.28.3

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

## Configure and build

### Configure command

```text
measurement_cmake_dir=/tmp/cmake-local.CgOQhW; LD_LIBRARY_PATH="$measurement_cmake_dir/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$measurement_cmake_dir/root/usr/bin/cmake" -S . -B build-cuda-experiments -DCMAKE_BUILD_TYPE=Release -DWEBP_ENABLE_CUDA=ON -DWEBP_BUILD_CUDA_ACCELERATION_EXPERIMENTS=ON 2>&1
-- The C compiler identification is GNU 13.3.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- The CUDA compiler identification is NVIDIA 12.0.140
-- Detecting CUDA compiler ABI info
-- Detecting CUDA compiler ABI info - done
-- Check for working CUDA compiler: /usr/bin/nvcc - skipped
-- Detecting CUDA compile features
-- Detecting CUDA compile features - done
-- Found CUDAToolkit: /usr/include (found version "12.0.140") 
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Performing Test HAVE_BUILTIN_BSWAP16
-- Performing Test HAVE_BUILTIN_BSWAP16 - Success
-- Performing Test HAVE_BUILTIN_BSWAP32
-- Performing Test HAVE_BUILTIN_BSWAP32 - Success
-- Performing Test HAVE_BUILTIN_BSWAP64
-- Performing Test HAVE_BUILTIN_BSWAP64 - Success
-- Found OpenGL: /usr/lib/x86_64-linux-gnu/libGL.so   
-- Performing Test HAVE_MATH_LIBRARY
-- Performing Test HAVE_MATH_LIBRARY - Failed
-- Adding -lm flag.
-- Found ZLIB: /usr/lib/x86_64-linux-gnu/libz.a (found version "1.3")  
-- Could NOT find PNG (missing: PNG_LIBRARY PNG_PNG_INCLUDE_DIR) 
-- Could NOT find JPEG (missing: JPEG_LIBRARY JPEG_INCLUDE_DIR) 
-- TIFF is disabled when statically linking.
-- Could NOT find GIF (missing: GIF_LIBRARY GIF_INCLUDE_DIR) 
-- Looking for include file GLUT/glut.h
-- Looking for include file GLUT/glut.h - not found
-- Looking for include file GL/glut.h
-- Looking for include file GL/glut.h - not found
-- Looking for include file OpenGL/glut.h
-- Looking for include file OpenGL/glut.h - not found
-- Looking for include file shlwapi.h
-- Looking for include file shlwapi.h - not found
-- Looking for include file unistd.h
-- Looking for include file unistd.h - found
-- Looking for include file wincodec.h
-- Looking for include file wincodec.h - not found
-- Looking for include file windows.h
-- Looking for include file windows.h - not found
-- Performing Test WEBP_HAVE_FLAG_AVX2
-- Performing Test WEBP_HAVE_FLAG_AVX2 - Failed
-- Performing Test WEBP_HAVE_FLAG_AVX2
-- Performing Test WEBP_HAVE_FLAG_AVX2 - Success
-- Performing Test WEBP_HAVE_FLAG_SSE41
-- Performing Test WEBP_HAVE_FLAG_SSE41 - Failed
-- Performing Test WEBP_HAVE_FLAG_SSE41
-- Performing Test WEBP_HAVE_FLAG_SSE41 - Success
-- Performing Test WEBP_HAVE_FLAG_SSE2
-- Performing Test WEBP_HAVE_FLAG_SSE2 - Success
-- Performing Test WEBP_HAVE_FLAG_MIPS32
-- Performing Test WEBP_HAVE_FLAG_MIPS32 - Failed
-- Performing Test WEBP_HAVE_FLAG_MIPS32
-- Performing Test WEBP_HAVE_FLAG_MIPS32 - Failed
-- Performing Test WEBP_HAVE_FLAG_MIPS_DSP_R2
-- Performing Test WEBP_HAVE_FLAG_MIPS_DSP_R2 - Failed
-- Performing Test WEBP_HAVE_FLAG_MIPS_DSP_R2
-- Performing Test WEBP_HAVE_FLAG_MIPS_DSP_R2 - Failed
-- Performing Test HAS_COMPILE_FLAG
-- Performing Test HAS_COMPILE_FLAG - Failed
-- Performing Test WEBP_HAVE_FLAG_NEON
-- Performing Test WEBP_HAVE_FLAG_NEON - Failed
-- Performing Test WEBP_HAVE_FLAG_NEON
-- Performing Test WEBP_HAVE_FLAG_NEON - Failed
-- Performing Test WEBP_HAVE_FLAG_MSA
-- Performing Test WEBP_HAVE_FLAG_MSA - Failed
-- Performing Test WEBP_HAVE_FLAG_MSA
-- Performing Test WEBP_HAVE_FLAG_MSA - Failed
-- Performing Test HAS_COMPILE_FLAG
-- Performing Test HAS_COMPILE_FLAG - Failed
-- Performing Test WEBP_HAVE_FLAG_VSX
-- Performing Test WEBP_HAVE_FLAG_VSX - Failed
-- Performing Test WEBP_HAVE_FLAG_VSX
-- Performing Test WEBP_HAVE_FLAG_VSX - Failed
-- Performing Test HAS_COMPILE_FLAG
-- Performing Test HAS_COMPILE_FLAG - Failed
-- Configuring done (3.9s)
-- Generating done (0.0s)
-- Build files have been written to: /home/jonas/.codex/worktrees/88d4/libwebp-metal/build-cuda-experiments
```

### Build command

```text
measurement_cmake_dir=/tmp/cmake-local.CgOQhW; LD_LIBRARY_PATH="$measurement_cmake_dir/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$measurement_cmake_dir/root/usr/bin/cmake" --build build-cuda-experiments --config Release --target cuda_acceleration_experiments --parallel 2 2>&1
Building CUDA object CMakeFiles/cuda_acceleration_experiments.dir/tools/cuda_acceleration_experiments.cu.o
Linking CUDA executable cuda_acceleration_experiments
Built target cuda_acceleration_experiments
```

## Verification

The required correctness command ran before any benchmark command.

```text
build-cuda-experiments/cuda_acceleration_experiments --verify 2>&1
device=NVIDIA GeForce RTX 2080 SUPER mode=verify iterations=1
color_baseline                  PASS checksum=5e40fe7c4b95d8d7
color_shared_tile               PASS checksum=5e40fe7c4b95d8d7
color_warp_histograms           PASS checksum=5e40fe7c4b95d8d7
color_parallel_entropy          PASS checksum=5e40fe7c4b95d8d7
color_specialized_kernel        PASS checksum=5e40fe7c4b95d8d7
context_pool                    PASS checksum=1458512bb9454275
resident_lossless_pipeline      PASS checksum=eb409c0a5af49b66
predictor_search_residual       PASS checksum=d53a6cc1b6e54b4f
hash_scalar                     PASS checksum=324c3eb3410475aa
hash_warp_cooperative           PASS checksum=324c3eb3410475aa
sharpyuv_iterative              PASS checksum=39204d15c730fffa
near_lossless_stencil           PASS checksum=5265a0bbabf36860
lossless_histogram              PASS checksum=e00d13e613731c45
lossy_macroblock_scoring        PASS checksum=8b646761439d9e9d
graphs_double_buffer            PASS checksum=1458512bb9454275
```

## Raw benchmark output

All five runs used the exact command below, with 100 kernel iterations:

```text
build-cuda-experiments/cuda_acceleration_experiments --benchmark --iterations 100 2>&1
```

### run=1

```text
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=100
experiment,iterations,total_ms,ms_per_iteration,checksum
color_baseline,100,22.344936,0.223449,5e40fe7c4b95d8d7
color_shared_tile,100,11.506412,0.115064,5e40fe7c4b95d8d7
color_warp_histograms,100,47.515483,0.475155,5e40fe7c4b95d8d7
color_parallel_entropy,100,103.496822,1.034968,5e40fe7c4b95d8d7
color_specialized_kernel,100,89.581876,0.895819,5e40fe7c4b95d8d7
context_pool,100,97.783567,0.977836,1458512bb9454275
resident_lossless_pipeline,100,39.359559,0.393596,eb409c0a5af49b66
predictor_search_residual,100,7.130624,0.071306,d53a6cc1b6e54b4f
hash_scalar,100,10.262480,0.102625,324c3eb3410475aa
hash_warp_cooperative,100,42.092082,0.420921,324c3eb3410475aa
sharpyuv_iterative,100,3.351379,0.033514,39204d15c730fffa
near_lossless_stencil,100,40.590035,0.405900,5265a0bbabf36860
lossless_histogram,100,31.278575,0.312786,e00d13e613731c45
lossy_macroblock_scoring,100,72.377518,0.723775,8b646761439d9e9d
graphs_double_buffer,100,75.264040,0.752640,1458512bb9454275
```

### run=2

```text
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=100
experiment,iterations,total_ms,ms_per_iteration,checksum
color_baseline,100,22.498958,0.224990,5e40fe7c4b95d8d7
color_shared_tile,100,11.487743,0.114877,5e40fe7c4b95d8d7
color_warp_histograms,100,47.540492,0.475405,5e40fe7c4b95d8d7
color_parallel_entropy,100,103.817436,1.038174,5e40fe7c4b95d8d7
color_specialized_kernel,100,94.985281,0.949853,5e40fe7c4b95d8d7
context_pool,100,96.867233,0.968672,1458512bb9454275
resident_lossless_pipeline,100,39.427310,0.394273,eb409c0a5af49b66
predictor_search_residual,100,7.128868,0.071289,d53a6cc1b6e54b4f
hash_scalar,100,10.293304,0.102933,324c3eb3410475aa
hash_warp_cooperative,100,42.043183,0.420432,324c3eb3410475aa
sharpyuv_iterative,100,3.375303,0.033753,39204d15c730fffa
near_lossless_stencil,100,40.683925,0.406839,5265a0bbabf36860
lossless_histogram,100,31.302938,0.313029,e00d13e613731c45
lossy_macroblock_scoring,100,72.360075,0.723601,8b646761439d9e9d
graphs_double_buffer,100,73.658650,0.736586,1458512bb9454275
```

### run=3

```text
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=100
experiment,iterations,total_ms,ms_per_iteration,checksum
color_baseline,100,22.528780,0.225288,5e40fe7c4b95d8d7
color_shared_tile,100,11.486287,0.114863,5e40fe7c4b95d8d7
color_warp_histograms,100,47.530613,0.475306,5e40fe7c4b95d8d7
color_parallel_entropy,100,103.848556,1.038486,5e40fe7c4b95d8d7
color_specialized_kernel,100,94.778015,0.947780,5e40fe7c4b95d8d7
context_pool,100,97.033088,0.970331,1458512bb9454275
resident_lossless_pipeline,100,39.372590,0.393726,eb409c0a5af49b66
predictor_search_residual,100,7.125831,0.071258,d53a6cc1b6e54b4f
hash_scalar,100,10.298762,0.102988,324c3eb3410475aa
hash_warp_cooperative,100,42.042575,0.420426,324c3eb3410475aa
sharpyuv_iterative,100,3.377547,0.033775,39204d15c730fffa
near_lossless_stencil,100,40.727360,0.407274,5265a0bbabf36860
lossless_histogram,100,31.317681,0.313177,e00d13e613731c45
lossy_macroblock_scoring,100,72.394318,0.723943,8b646761439d9e9d
graphs_double_buffer,100,73.783292,0.737833,1458512bb9454275
```

### run=4

```text
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=100
experiment,iterations,total_ms,ms_per_iteration,checksum
color_baseline,100,22.717050,0.227170,5e40fe7c4b95d8d7
color_shared_tile,100,11.579491,0.115795,5e40fe7c4b95d8d7
color_warp_histograms,100,47.587122,0.475871,5e40fe7c4b95d8d7
color_parallel_entropy,100,103.209636,1.032096,5e40fe7c4b95d8d7
color_specialized_kernel,100,85.812046,0.858120,5e40fe7c4b95d8d7
context_pool,100,96.894932,0.968949,1458512bb9454275
resident_lossless_pipeline,100,39.122223,0.391222,eb409c0a5af49b66
predictor_search_residual,100,6.944128,0.069441,d53a6cc1b6e54b4f
hash_scalar,100,10.178284,0.101783,324c3eb3410475aa
hash_warp_cooperative,100,42.008184,0.420082,324c3eb3410475aa
sharpyuv_iterative,100,3.281786,0.032818,39204d15c730fffa
near_lossless_stencil,100,40.552304,0.405523,5265a0bbabf36860
lossless_histogram,100,31.361066,0.313611,e00d13e613731c45
lossy_macroblock_scoring,100,72.563191,0.725632,8b646761439d9e9d
graphs_double_buffer,100,73.711833,0.737118,1458512bb9454275
```

### run=5

```text
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=100
experiment,iterations,total_ms,ms_per_iteration,checksum
color_baseline,100,22.220201,0.222202,5e40fe7c4b95d8d7
color_shared_tile,100,11.478358,0.114784,5e40fe7c4b95d8d7
color_warp_histograms,100,47.468971,0.474690,5e40fe7c4b95d8d7
color_parallel_entropy,100,91.704327,0.917043,5e40fe7c4b95d8d7
color_specialized_kernel,100,85.484393,0.854844,5e40fe7c4b95d8d7
context_pool,100,96.869606,0.968696,1458512bb9454275
resident_lossless_pipeline,100,39.724618,0.397246,eb409c0a5af49b66
predictor_search_residual,100,7.261624,0.072616,d53a6cc1b6e54b4f
hash_scalar,100,10.283470,0.102835,324c3eb3410475aa
hash_warp_cooperative,100,42.060343,0.420603,324c3eb3410475aa
sharpyuv_iterative,100,3.373828,0.033738,39204d15c730fffa
near_lossless_stencil,100,40.746530,0.407465,5265a0bbabf36860
lossless_histogram,100,31.351682,0.313517,e00d13e613731c45
lossy_macroblock_scoring,100,72.279965,0.722800,8b646761439d9e9d
graphs_double_buffer,100,74.333700,0.743337,1458512bb9454275
```

## Computed summary

This section was appended after the raw captures were preserved. Each median is
the median of five raw `total_ms` and `ms_per_iteration` values at 100
iterations. Matched speedup is `median(control) / median(case)`; values above
1x are faster than the matched control. The checksum column is the single
checksum observed for all five repetitions of that case.

**Correction:** the five historical color cases below are not valid matched
comparisons. `color_baseline` copied full histograms to the host and reduced
them on the CPU, while the other cases copied device-reduced scores. Their raw
times and checksums are preserved, but their displayed historical ratios must
not be used. The runner now exposes the old work separately as
`color_histogram_throughput`; the new `color_baseline` performs device
reduction and transfers the same score bytes as `color_shared_tile`. No
replacement timing has been collected yet.

| Experiment | Median total ms (100 iters) | Median ms/iteration | Matched control | Speedup | Stable checksum |
| --- | ---: | ---: | --- | ---: | --- |
| `color_baseline` | 22.498958 | 0.224990 | invalid transfer-heavy control | — | `5e40fe7c4b95d8d7` |
| `color_shared_tile` | 11.487743 | 0.114877 | none | — | `5e40fe7c4b95d8d7` |
| `color_warp_histograms` | 47.530613 | 0.475306 | none | — | `5e40fe7c4b95d8d7` |
| `color_parallel_entropy` | 103.496822 | 1.034968 | none | — | `5e40fe7c4b95d8d7` |
| `color_specialized_kernel` | 89.581876 | 0.895819 | none | — | `5e40fe7c4b95d8d7` |
| `context_pool` | 96.894932 | 0.968949 | none | — | `1458512bb9454275` |
| `resident_lossless_pipeline` | 39.372590 | 0.393726 | none | — | `eb409c0a5af49b66` |
| `predictor_search_residual` | 7.128868 | 0.071289 | none | — | `d53a6cc1b6e54b4f` |
| `hash_scalar` | 10.283470 | 0.102835 | `hash_scalar` | 1.0000x | `324c3eb3410475aa` |
| `hash_warp_cooperative` | 42.043183 | 0.420432 | `hash_scalar` | 0.2446x | `324c3eb3410475aa` |
| `sharpyuv_iterative` | 3.373828 | 0.033738 | none | — | `39204d15c730fffa` |
| `near_lossless_stencil` | 40.683925 | 0.406839 | none | — | `5265a0bbabf36860` |
| `lossless_histogram` | 31.317681 | 0.313177 | none | — | `e00d13e613731c45` |
| `lossy_macroblock_scoring` | 72.377518 | 0.723775 | none | — | `8b646761439d9e9d` |
| `graphs_double_buffer` | 73.783292 | 0.737833 | none | — | `1458512bb9454275` |

The historical color variants have no valid matched control because their
transfer and reduction work differed. The hash warp-cooperative case remains
0.2446x as fast as `hash_scalar` (about 4.09x slower).

`context_pool`, `resident_lossless_pipeline`, and `graphs_double_buffer`
are lifecycle/transfer or resident-pipeline cases and have no valid matched
control in this executable, so their absolute medians above are not directly
comparable to one another or to the existing encoder-stage values in
`CUDA_BENCHMARK_RESULTS.md`; those measurements use different workloads,
sizes, and cold/warm process semantics. The other unmatched cases likewise
have absolute medians only.

All 75 benchmark rows retained the expected checksum from verification. No
CUDA errors, oracle mismatches, benchmark failures, or checksum instability
were observed. The base image had no CMake executable on `PATH`; the build
used an unprivileged temporary CMake 3.28.3 extraction, while the repository
and implementation sources remained unchanged.

## Follow-up matched lifecycle controls

These rows were captured after adding equivalent controls. Each named case ran
in a separate process with `--benchmark --iterations 100`; the leading field is
the repetition number. All preflights passed and matched pairs retained equal
checksums.

```text
1,context_serial,100,72.415603,0.724156,1458512bb9454275
1,context_pool,100,105.199655,1.051997,1458512bb9454275
1,staged_lossless_pipeline,100,287.582406,2.875824,eb409c0a5af49b66
1,resident_lossless_pipeline,100,42.060947,0.420609,eb409c0a5af49b66
1,double_buffer_launches,100,76.307184,0.763072,1458512bb9454275
1,graphs_double_buffer,100,76.589971,0.765900,1458512bb9454275
2,context_serial,100,72.311619,0.723116,1458512bb9454275
2,context_pool,100,99.265760,0.992658,1458512bb9454275
2,staged_lossless_pipeline,100,285.926596,2.859266,eb409c0a5af49b66
2,resident_lossless_pipeline,100,41.812485,0.418125,eb409c0a5af49b66
2,double_buffer_launches,100,76.282580,0.762826,1458512bb9454275
2,graphs_double_buffer,100,77.240835,0.772408,1458512bb9454275
3,context_serial,100,71.950708,0.719507,1458512bb9454275
3,context_pool,100,99.273566,0.992736,1458512bb9454275
3,staged_lossless_pipeline,100,281.434850,2.814348,eb409c0a5af49b66
3,resident_lossless_pipeline,100,41.943610,0.419436,eb409c0a5af49b66
3,double_buffer_launches,100,86.232028,0.862320,1458512bb9454275
3,graphs_double_buffer,100,76.655094,0.766551,1458512bb9454275
4,context_serial,100,72.194083,0.721941,1458512bb9454275
4,context_pool,100,99.250465,0.992505,1458512bb9454275
4,staged_lossless_pipeline,100,281.136899,2.811369,eb409c0a5af49b66
4,resident_lossless_pipeline,100,41.903115,0.419031,eb409c0a5af49b66
4,double_buffer_launches,100,76.843025,0.768430,1458512bb9454275
4,graphs_double_buffer,100,76.429034,0.764290,1458512bb9454275
5,context_serial,100,71.917849,0.719178,1458512bb9454275
5,context_pool,100,99.249414,0.992494,1458512bb9454275
5,staged_lossless_pipeline,100,282.245718,2.822457,eb409c0a5af49b66
5,resident_lossless_pipeline,100,41.571839,0.415718,eb409c0a5af49b66
5,double_buffer_launches,100,79.440056,0.794401,1458512bb9454275
5,graphs_double_buffer,100,76.612718,0.766127,1458512bb9454275
```

## Follow-up matched stage controls

These rows add setup-inclusive CPU controls for the three retained feasibility
cases whose work can be reproduced exactly in the lab. Each pair retained an
identical checksum. The leading field is the fresh-process repetition number.

```text
1,predictor_search_residual_cpu,20,160.936394,8.046820,d53a6cc1b6e54b4f
1,predictor_search_residual,20,7.607895,0.380395,d53a6cc1b6e54b4f
1,near_lossless_stencil_cpu,20,522.716241,26.135812,5265a0bbabf36860
1,near_lossless_stencil,20,14.105610,0.705280,5265a0bbabf36860
1,lossless_histogram_cpu,20,42.290561,2.114528,e00d13e613731c45
1,lossless_histogram,20,14.218610,0.710931,e00d13e613731c45
2,predictor_search_residual_cpu,20,155.654056,7.782703,d53a6cc1b6e54b4f
2,predictor_search_residual,20,7.715936,0.385797,d53a6cc1b6e54b4f
2,near_lossless_stencil_cpu,20,538.649093,26.932455,5265a0bbabf36860
2,near_lossless_stencil,20,13.970077,0.698504,5265a0bbabf36860
2,lossless_histogram_cpu,20,41.964173,2.098209,e00d13e613731c45
2,lossless_histogram,20,14.608127,0.730406,e00d13e613731c45
3,predictor_search_residual_cpu,20,157.209398,7.860470,d53a6cc1b6e54b4f
3,predictor_search_residual,20,7.506476,0.375324,d53a6cc1b6e54b4f
3,near_lossless_stencil_cpu,20,540.101085,27.005054,5265a0bbabf36860
3,near_lossless_stencil,20,14.490868,0.724543,5265a0bbabf36860
3,lossless_histogram_cpu,20,41.490329,2.074516,e00d13e613731c45
3,lossless_histogram,20,14.798291,0.739915,e00d13e613731c45
4,predictor_search_residual_cpu,20,152.126142,7.606307,d53a6cc1b6e54b4f
4,predictor_search_residual,20,7.714203,0.385710,d53a6cc1b6e54b4f
4,near_lossless_stencil_cpu,20,542.419291,27.120965,5265a0bbabf36860
4,near_lossless_stencil,20,13.961241,0.698062,5265a0bbabf36860
4,lossless_histogram_cpu,20,41.601797,2.080090,e00d13e613731c45
4,lossless_histogram,20,14.491450,0.724573,e00d13e613731c45
5,predictor_search_residual_cpu,20,152.899515,7.644976,d53a6cc1b6e54b4f
5,predictor_search_residual,20,7.491038,0.374552,d53a6cc1b6e54b4f
5,near_lossless_stencil_cpu,20,516.328028,25.816401,5265a0bbabf36860
5,near_lossless_stencil,20,13.993661,0.699683,5265a0bbabf36860
5,lossless_histogram_cpu,20,40.963939,2.048197,e00d13e613731c45
5,lossless_histogram,20,14.171333,0.708567,e00d13e613731c45
```

Median matched results are 20.46x for predictor search/residuals
(155.654056/7.607895 ms), 38.49x for the near-lossless stencil
(538.649093/13.993661 ms), and 2.87x for histogram construction
(41.601797/14.491450 ms). All are experiment-runner results; only the
near-lossless case has since been implemented with the full production
algorithm and is subject to a separate direct crossover measurement.
 
## Follow-up matched SharpYUV and lossy-scoring controls

Measurement date: 2026-08-18. Release CUDA build on NVIDIA GeForce RTX 2080
SUPER, CUDA Toolkit 12.0, GCC/G++ 13.3.0, CMake 4.4.2. The existing
experiment implementation and all earlier raw sections were left unchanged.

The lab was rebuilt and run with `--verify` before timing. Each named case
below ran in five fresh processes with `--benchmark --iterations 20`. The
CPU and CUDA cases are matched workloads; every row retained the same checksum
within its pair.

### Verbatim environment, build, and verification output

```text
$ nvidia-smi
Tue Aug 18 11:20:47 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.84                 Driver Version: 595.84         CUDA Version: 13.2     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 2080 ...    Off |   00000000:0A:00.0  On |                  N/A |
|  0%   28C    P8             15W /  250W |       9MiB /   8192MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
$ nvcc --version
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Fri_Jan__6_16:45:21_PST_2023
Cuda compilation tools, release 12.0, V12.0.140
Build cuda_12.0.r12.0/compiler.32267302_0
$ gcc --version | head -1
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
$ g++ --version | head -1
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
$ cmake --version
cmake version 4.4.2

CMake suite maintained and supported by Kitware (kitware.com/cmake).
$ cmake --build /tmp/libwebp-cuda-experiment-followup --target cuda_acceleration_experiments -j
[100%] Built target cuda_acceleration_experiments
$ /tmp/libwebp-cuda-experiment-followup/cuda_acceleration_experiments --verify
device=NVIDIA GeForce RTX 2080 SUPER mode=verify iterations=1
color_baseline                  PASS checksum=5e40fe7c4b95d8d7
color_shared_tile               PASS checksum=5e40fe7c4b95d8d7
staged_lossless_pipeline        PASS checksum=eb409c0a5af49b66
resident_lossless_pipeline      PASS checksum=eb409c0a5af49b66
predictor_search_residual_cpu   PASS checksum=d53a6cc1b6e54b4f
predictor_search_residual       PASS checksum=d53a6cc1b6e54b4f
sharpyuv_iterative_cpu          PASS checksum=39204d15c730fffa
sharpyuv_iterative              PASS checksum=39204d15c730fffa
near_lossless_stencil_cpu       PASS checksum=5265a0bbabf36860
near_lossless_stencil           PASS checksum=5265a0bbabf36860
lossless_histogram_cpu          PASS checksum=e00d13e613731c45
lossless_histogram              PASS checksum=e00d13e613731c45
lossy_macroblock_scoring_cpu    PASS checksum=8b646761439d9e9d
lossy_macroblock_scoring        PASS checksum=8b646761439d9e9d
```

### SharpYUV iterative raw output

```text
run=1 experiment=sharpyuv_iterative_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative_cpu,20,136.046849,6.802342,39204d15c730fffa
run=2 experiment=sharpyuv_iterative_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative_cpu,20,132.008941,6.600447,39204d15c730fffa
run=3 experiment=sharpyuv_iterative_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative_cpu,20,133.811918,6.690596,39204d15c730fffa
run=4 experiment=sharpyuv_iterative_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative_cpu,20,135.878085,6.793904,39204d15c730fffa
run=5 experiment=sharpyuv_iterative_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative_cpu,20,131.317120,6.565856,39204d15c730fffa

run=1 experiment=sharpyuv_iterative
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative,20,3.377155,0.168858,39204d15c730fffa
run=2 experiment=sharpyuv_iterative
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative,20,3.404185,0.170209,39204d15c730fffa
run=3 experiment=sharpyuv_iterative
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative,20,3.349222,0.167461,39204d15c730fffa
run=4 experiment=sharpyuv_iterative
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative,20,3.382354,0.169118,39204d15c730fffa
run=5 experiment=sharpyuv_iterative
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
sharpyuv_iterative,20,3.359632,0.167982,39204d15c730fffa
```

### Lossy macroblock scoring raw output

```text
run=1 experiment=lossy_macroblock_scoring_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring_cpu,20,35.682644,1.784132,8b646761439d9e9d
run=2 experiment=lossy_macroblock_scoring_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring_cpu,20,34.866901,1.743345,8b646761439d9e9d
run=3 experiment=lossy_macroblock_scoring_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring_cpu,20,35.459397,1.772970,8b646761439d9e9d
run=4 experiment=lossy_macroblock_scoring_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring_cpu,20,34.887911,1.744396,8b646761439d9e9d
run=5 experiment=lossy_macroblock_scoring_cpu
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring_cpu,20,37.242135,1.862107,8b646761439d9e9d

run=1 experiment=lossy_macroblock_scoring
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring,20,16.121666,0.806083,8b646761439d9e9d
run=2 experiment=lossy_macroblock_scoring
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring,20,15.773266,0.788663,8b646761439d9e9d
run=3 experiment=lossy_macroblock_scoring
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring,20,15.820395,0.791020,8b646761439d9e9d
run=4 experiment=lossy_macroblock_scoring
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring,20,15.927374,0.796369,8b646761439d9e9d
run=5 experiment=lossy_macroblock_scoring
device=NVIDIA GeForce RTX 2080 SUPER mode=benchmark iterations=20
experiment,iterations,total_ms,ms_per_iteration,checksum
lossy_macroblock_scoring,20,15.470972,0.773549,8b646761439d9e9d
```

### Computed medians

Medians are across the five fresh-process rows. Speedup is CPU
milliseconds-per-iteration divided by CUDA milliseconds-per-iteration.

| Matched pair | CPU median total ms | CUDA median total ms | CPU median ms/iteration | CUDA median ms/iteration | Speedup | Stable checksum |
|---|---:|---:|---:|---:|---:|:--|
| `SharpYUV iterative` | 133.811918 | 3.377155 | 6.690596 | 0.168858 | 39.6226x | 39204d15c730fffa |
| `Lossy macroblock scoring` | 35.459397 | 15.820395 | 1.772970 | 0.791020 | 2.2414x | 8b646761439d9e9d |

Both matched pairs are internally correct under the lab oracle. The GPU
result is 39.6226x faster for the SharpYUV-shaped iterative workload and
2.2414x faster for lossy macroblock scoring in this corpus. These remain
experiment-runner results rather than production integrations; the workloads
do not yet prove end-to-end encoder benefit or full public-algorithm coverage.
