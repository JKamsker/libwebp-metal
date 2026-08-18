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

| Experiment | Median total ms (100 iters) | Median ms/iteration | Matched control | Speedup | Stable checksum |
| --- | ---: | ---: | --- | ---: | --- |
| `color_baseline` | 22.498958 | 0.224990 | `color_baseline` | 1.0000x | `5e40fe7c4b95d8d7` |
| `color_shared_tile` | 11.487743 | 0.114877 | `color_baseline` | 1.9585x | `5e40fe7c4b95d8d7` |
| `color_warp_histograms` | 47.530613 | 0.475306 | `color_baseline` | 0.4734x | `5e40fe7c4b95d8d7` |
| `color_parallel_entropy` | 103.496822 | 1.034968 | `color_baseline` | 0.2174x | `5e40fe7c4b95d8d7` |
| `color_specialized_kernel` | 89.581876 | 0.895819 | `color_baseline` | 0.2512x | `5e40fe7c4b95d8d7` |
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

The color variants have a valid matched control: `color_shared_tile` is
1.9585x faster, while `color_warp_histograms`, `color_parallel_entropy`,
and `color_specialized_kernel` are slower than `color_baseline` under this
runner. The hash warp-cooperative case is 0.2446x as fast as `hash_scalar`
(about 4.09x slower).

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
