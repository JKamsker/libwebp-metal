# CUDA near-lossless production measurements (raw)

Measurement date: 2026-08-18.
Source branch: codex/cuda-encoder-acceleration.
GPU: NVIDIA GeForce RTX 2080 SUPER.
This file is an append-only capture. Environment/build/test output and every
benchmark JSON row are retained verbatim below; the computed tables are
derived from those rows and do not replace them.

## Scope and protocol

The benchmark calls the real `VP8ApplyNearLossless` preprocessing function
directly. RGBA import and allocation are outside the timed region. CPU uses
`WEBP_ACCELERATOR=none`; CUDA uses `WEBP_ACCELERATOR=cuda`,
`WEBP_CUDA_NEAR_LOSSLESS=1`, and a zero minimum-pixel override so every case
is forced through the stage. Warm runs use 3 untimed warmups and 7 measured
samples in each of 5 fresh processes. Cold runs use 0 warmups and 1 sample in
each of 5 fresh processes. Qualities 0, 40, and 80 map to limit_bits 5, 3, and
1. All matched CPU/CUDA hashes were identical.

Warm command template (each size/quality/variant was run five times):

```sh
/tmp/libwebp-near-lossless-measure/webp_cuda_benchmark \
  --operation near-lossless --variant cpu|cuda --width N --height N \
  --method 4 --quality Q --warmups 3 --samples 7
```

Cold command template:

```sh
/tmp/libwebp-near-lossless-measure/webp_cuda_benchmark \
  --operation near-lossless --variant cpu|cuda --width N --height N \
  --method 4 --quality Q --warmups 0 --samples 1
```

## Verbatim environment, build, and correctness output

```text
$ nvidia-smi
Tue Aug 18 11:15:41 2026       
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
$ cmake configure
-- Adding -lm flag.
-- Could NOT find PNG (missing: PNG_LIBRARY PNG_PNG_INCLUDE_DIR) 
-- Could NOT find JPEG (missing: JPEG_LIBRARY JPEG_INCLUDE_DIR) 
-- TIFF is disabled when statically linking.
-- Could NOT find GIF (missing: GIF_LIBRARY GIF_INCLUDE_DIR) 
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
-- Configuring done (0.8s)
-- Generating done (0.1s)
-- Build files have been written to: /tmp/libwebp-near-lossless-measure
$ cmake build
[  4%] Built target sharpyuv
[ 11%] Built target webputils
[ 24%] Built target webpencode
[ 48%] Built target webpdspdecode
[ 83%] Built target webpdsp
[ 88%] Built target webpdecode
[ 88%] Built target webp
[ 89%] Built target imageioutil
[ 92%] Built target webpdemux
[ 93%] Built target exampleutil
[ 98%] Built target imagedec
[100%] Built target cwebp
[  4%] Built target sharpyuv
[ 11%] Built target webputils
[ 24%] Built target webpencode
[ 48%] Built target webpdspdecode
[ 83%] Built target webpdsp
[ 88%] Built target webpdecode
[ 88%] Built target webp
[ 89%] Built target imageioutil
[ 92%] Built target webpdemux
[ 92%] Built target imageenc
[ 93%] Built target exampleutil
[ 98%] Built target imagedec
[100%] Built target dwebp
[  5%] Built target sharpyuv
[ 12%] Built target webputils
[ 27%] Built target webpencode
[ 53%] Built target webpdspdecode
[ 92%] Built target webpdsp
[ 98%] Built target webpdecode
[ 98%] Built target webp
[100%] Building C object CMakeFiles/webp_cuda_benchmark.dir/tools/cuda_benchmark.c.o
[100%] Linking CUDA executable webp_cuda_benchmark
[100%] Built target webp_cuda_benchmark
[  7%] Built target webputils
[ 12%] Built target sharpyuv
[ 27%] Built target webpencode
[ 53%] Built target webpdspdecode
[ 92%] Built target webpdsp
[ 98%] Built target webpdecode
[ 98%] Built target webp
[100%] Built target cuda_near_lossless_test
$ cuda_near_lossless_test
PASS: exact near-lossless CPU/CUDA parity across 20 cases
```

## Warm raw output (1,470 JSON rows)

The following blocks are the exact stdout from the 42 warm batches. The
`run=` lines identify the independent process; JSON rows are unmodified.

```text
run=1 size=64 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":138278,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":153617,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":133439,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":131175,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":130173,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":129041,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":128691,"output_hash":"67e96c35e16aca52","output_size":16384}
run=2 size=64 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":137987,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":135203,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":132988,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":141495,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":130694,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":129752,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":128851,"output_hash":"67e96c35e16aca52","output_size":16384}
run=3 size=64 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":135944,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":134251,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":131956,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":130473,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":129602,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":128250,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":132658,"output_hash":"67e96c35e16aca52","output_size":16384}
run=4 size=64 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":138017,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":135573,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":137907,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":132327,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":132558,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":131586,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":129812,"output_hash":"67e96c35e16aca52","output_size":16384}
run=5 size=64 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":137076,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":135032,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":137707,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":131215,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":133790,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":129522,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":128760,"output_hash":"67e96c35e16aca52","output_size":16384}

run=1 size=64 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":25849,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":25558,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":25187,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":25338,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":25467,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":25358,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":25066,"output_hash":"67e96c35e16aca52","output_size":16384}
run=2 size=64 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":27231,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":27721,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":27953,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":27552,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":27211,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":28383,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":27361,"output_hash":"67e96c35e16aca52","output_size":16384}
run=3 size=64 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":25608,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":27211,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":26299,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":28723,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":26841,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":26099,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":25568,"output_hash":"67e96c35e16aca52","output_size":16384}
run=4 size=64 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":26379,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":25999,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":26269,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":25317,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":25768,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":25759,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":25578,"output_hash":"67e96c35e16aca52","output_size":16384}
run=5 size=64 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":0,"elapsed_ns":25437,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":1,"elapsed_ns":26379,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":2,"elapsed_ns":25638,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":3,"elapsed_ns":25277,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":4,"elapsed_ns":25618,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":5,"elapsed_ns":25478,"output_hash":"67e96c35e16aca52","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":0,"sequence":6,"elapsed_ns":25628,"output_hash":"67e96c35e16aca52","output_size":16384}

run=1 size=64 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":21400,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":21209,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":21069,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":21039,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":20839,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":20789,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":20950,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=2 size=64 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":20859,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":21370,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":21099,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":20869,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":21049,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":20919,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":26830,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=3 size=64 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":21159,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":21691,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":20989,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":20518,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":21390,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":20739,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":20639,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=4 size=64 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":21460,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":20989,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":20699,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":20899,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":20738,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":20738,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":20789,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=5 size=64 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":21039,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":21180,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":20859,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":20889,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":20909,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":20879,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":20678,"output_hash":"bfb17b699f8fe23b","output_size":16384}

run=1 size=64 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":16912,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":16551,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16170,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16060,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":15970,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":15900,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":15879,"output_hash":"52bd82584ee63f61","output_size":16384}
run=2 size=64 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":17172,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":16662,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16571,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16330,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16280,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":16300,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16231,"output_hash":"52bd82584ee63f61","output_size":16384}
run=3 size=64 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":33533,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":32982,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":32280,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":32080,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":31839,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":31719,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":31549,"output_hash":"52bd82584ee63f61","output_size":16384}
run=4 size=64 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":17463,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":17022,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16802,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16591,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16591,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":16520,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16500,"output_hash":"52bd82584ee63f61","output_size":16384}
run=5 size=64 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":17322,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":17192,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16822,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16761,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16641,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":16561,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16571,"output_hash":"52bd82584ee63f61","output_size":16384}

run=1 size=64 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":19076,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":19396,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":18073,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16801,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16942,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":17363,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16451,"output_hash":"52bd82584ee63f61","output_size":16384}
run=2 size=64 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":16331,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":17022,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16080,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":15930,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16501,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":16540,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16100,"output_hash":"52bd82584ee63f61","output_size":16384}
run=3 size=64 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":17884,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":18184,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":28654,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":17703,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":17202,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":17653,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16341,"output_hash":"52bd82584ee63f61","output_size":16384}
run=4 size=64 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":16161,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":17403,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16241,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16020,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16240,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":16460,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16190,"output_hash":"52bd82584ee63f61","output_size":16384}
run=5 size=64 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":0,"elapsed_ns":16280,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":1,"elapsed_ns":17393,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":2,"elapsed_ns":16741,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":3,"elapsed_ns":16090,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":4,"elapsed_ns":16111,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":5,"elapsed_ns":21119,"output_hash":"52bd82584ee63f61","output_size":16384}
{"operation":"near-lossless","variant":"cuda","width":64,"height":64,"method":4,"quality":80,"sequence":6,"elapsed_ns":16551,"output_hash":"52bd82584ee63f61","output_size":16384}

run=1 size=128 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":678817,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":671223,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":680790,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":677886,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":683135,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":681322,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":682915,"output_hash":"e95f0a29556928a0","output_size":65536}
run=2 size=128 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":698935,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":691270,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":689898,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":699426,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":694737,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":689558,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":689386,"output_hash":"e95f0a29556928a0","output_size":65536}
run=3 size=128 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":669159,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":699997,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":699375,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":684167,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":700407,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":665181,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":694977,"output_hash":"e95f0a29556928a0","output_size":65536}
run=4 size=128 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":683667,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":700147,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":691040,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":689727,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":687253,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":690158,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":689717,"output_hash":"e95f0a29556928a0","output_size":65536}
run=5 size=128 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":684528,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":677324,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":681312,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":669480,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":691310,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":691180,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":673407,"output_hash":"e95f0a29556928a0","output_size":65536}

run=1 size=128 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":40957,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":47999,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":47930,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":52427,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":41017,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":48270,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":41547,"output_hash":"e95f0a29556928a0","output_size":65536}
run=2 size=128 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":47539,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":48260,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":48451,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":47980,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":47478,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":44863,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":48290,"output_hash":"e95f0a29556928a0","output_size":65536}
run=3 size=128 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":47629,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":47820,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":48271,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":47388,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":49562,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":48120,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":47749,"output_hash":"e95f0a29556928a0","output_size":65536}
run=4 size=128 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":49873,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":49262,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":48872,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":48190,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":49963,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":47459,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":49172,"output_hash":"e95f0a29556928a0","output_size":65536}
run=5 size=128 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":0,"elapsed_ns":49322,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":1,"elapsed_ns":47869,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":2,"elapsed_ns":49132,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":3,"elapsed_ns":47759,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":4,"elapsed_ns":48630,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":5,"elapsed_ns":48852,"output_hash":"e95f0a29556928a0","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":0,"sequence":6,"elapsed_ns":48641,"output_hash":"e95f0a29556928a0","output_size":65536}

run=1 size=128 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":406579,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":409575,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":405547,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":400617,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":393905,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":391260,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":410977,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=2 size=128 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":404595,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":401008,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":400157,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":394697,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":407571,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":400197,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":409233,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=3 size=128 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":400197,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":408592,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":396320,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":398865,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":404696,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":397442,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":399776,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=4 size=128 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":409474,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":399015,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":413602,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":405267,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":407951,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":399797,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":401729,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=5 size=128 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":410566,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":402431,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":409915,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":396540,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":408844,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":401259,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":402462,"output_hash":"6d31f36f229dbc06","output_size":65536}

run=1 size=128 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":43230,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":43882,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":43381,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":42840,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":43861,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":43802,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":43181,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=2 size=128 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":43762,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":43952,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":43221,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":42910,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":43922,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":48400,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":43832,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=3 size=128 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":42971,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":48580,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":43441,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":43150,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":43361,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":43041,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":43651,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=4 size=128 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":44242,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":43291,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":42389,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":43351,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":46006,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":42880,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":43090,"output_hash":"6d31f36f229dbc06","output_size":65536}
run=5 size=128 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":0,"elapsed_ns":42940,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":1,"elapsed_ns":44293,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":2,"elapsed_ns":45445,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":3,"elapsed_ns":43441,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":4,"elapsed_ns":43631,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":5,"elapsed_ns":43371,"output_hash":"6d31f36f229dbc06","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":40,"sequence":6,"elapsed_ns":42389,"output_hash":"6d31f36f229dbc06","output_size":65536}

run=1 size=128 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":108122,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":107240,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":132938,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":111408,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":109444,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":105386,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":106228,"output_hash":"365eea827b03ee04","output_size":65536}
run=2 size=128 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":104284,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":110988,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":111818,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":105056,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":105447,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":105547,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":105998,"output_hash":"365eea827b03ee04","output_size":65536}
run=3 size=128 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":105617,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":105728,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":106108,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":106479,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":106088,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":105828,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":105346,"output_hash":"365eea827b03ee04","output_size":65536}
run=4 size=128 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":104305,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":104856,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":104045,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":109935,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":105296,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":105016,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":107341,"output_hash":"365eea827b03ee04","output_size":65536}
run=5 size=128 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":106549,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":106419,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":105838,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":107781,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":104826,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":104655,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cpu","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":103683,"output_hash":"365eea827b03ee04","output_size":65536}

run=1 size=128 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":38281,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":38913,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":44663,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":38272,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":39424,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":38772,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":39103,"output_hash":"365eea827b03ee04","output_size":65536}
run=2 size=128 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":39995,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":40345,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":38492,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":38732,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":38742,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":38211,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":38212,"output_hash":"365eea827b03ee04","output_size":65536}
run=3 size=128 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":39303,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":39494,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":39063,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":38532,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":39053,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":38903,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":39062,"output_hash":"365eea827b03ee04","output_size":65536}
run=4 size=128 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":39965,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":40265,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":38131,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":39894,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":38302,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":37851,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":39163,"output_hash":"365eea827b03ee04","output_size":65536}
run=5 size=128 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":0,"elapsed_ns":38942,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":1,"elapsed_ns":39123,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":2,"elapsed_ns":38712,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":3,"elapsed_ns":38552,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":4,"elapsed_ns":38202,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":5,"elapsed_ns":39333,"output_hash":"365eea827b03ee04","output_size":65536}
{"operation":"near-lossless","variant":"cuda","width":128,"height":128,"method":4,"quality":80,"sequence":6,"elapsed_ns":38762,"output_hash":"365eea827b03ee04","output_size":65536}

run=1 size=256 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":2868555,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":2888952,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":2820685,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":2811508,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":2863395,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":2852604,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":2848016,"output_hash":"d249f660ec81a308","output_size":262144}
run=2 size=256 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":2817769,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":2813221,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":2809164,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":2823300,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":2828931,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":2823541,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":2818641,"output_hash":"d249f660ec81a308","output_size":262144}
run=3 size=256 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":2843327,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":2788125,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":2840191,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":2795307,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":2880217,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":2880827,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":2987927,"output_hash":"d249f660ec81a308","output_size":262144}
run=4 size=256 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":2829982,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":2844559,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":2841494,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":2833720,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":2959193,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":3175287,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":2884364,"output_hash":"d249f660ec81a308","output_size":262144}
run=5 size=256 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":2865438,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":2893010,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":2877842,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":2848536,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":2864066,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":2886258,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":2867924,"output_hash":"d249f660ec81a308","output_size":262144}

run=1 size=256 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":129041,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":132667,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":128480,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":128279,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":126396,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":128009,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":125544,"output_hash":"d249f660ec81a308","output_size":262144}
run=2 size=256 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":131214,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":142246,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":138087,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":124172,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":119283,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":116488,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":115757,"output_hash":"d249f660ec81a308","output_size":262144}
run=3 size=256 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":123491,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":118100,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":115285,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":116798,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":120856,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":118771,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":118782,"output_hash":"d249f660ec81a308","output_size":262144}
run=4 size=256 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":125695,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":121307,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":118411,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":121817,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":121427,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":124212,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":120084,"output_hash":"d249f660ec81a308","output_size":262144}
run=5 size=256 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":0,"elapsed_ns":123611,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":1,"elapsed_ns":116017,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":2,"elapsed_ns":120194,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":3,"elapsed_ns":121006,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":4,"elapsed_ns":117950,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":5,"elapsed_ns":119984,"output_hash":"d249f660ec81a308","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":0,"sequence":6,"elapsed_ns":121617,"output_hash":"d249f660ec81a308","output_size":262144}

run=1 size=256 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":1694252,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":1701225,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":1696738,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":1693631,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":1689704,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":1732925,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":1686077,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=2 size=256 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":1701956,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":1699923,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":1693571,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":1687259,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":1662703,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":1692980,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":1686899,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=3 size=256 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":1701155,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":1691638,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":1698160,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":1699051,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":1698951,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":1702718,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":1693200,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=4 size=256 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":1700905,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":1693692,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":1696877,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":1683402,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":1691538,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":1704171,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":1705434,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=5 size=256 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":1705363,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":1742343,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":1682510,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":1748614,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":1725170,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":1714049,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":1696016,"output_hash":"c0ccad163a05cb9b","output_size":262144}

run=1 size=256 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":114764,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":108022,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":113732,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":114293,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":112941,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":112881,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":113833,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=2 size=256 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":116197,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":119824,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":125254,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":118532,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":133148,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":138619,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":132016,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=3 size=256 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":113673,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":107591,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":112800,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":116136,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":112259,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":117399,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":113672,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=4 size=256 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":107290,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":112039,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":113242,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":112800,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":112600,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":113021,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":112240,"output_hash":"c0ccad163a05cb9b","output_size":262144}
run=5 size=256 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":0,"elapsed_ns":109003,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":1,"elapsed_ns":110496,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":2,"elapsed_ns":113041,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":3,"elapsed_ns":117289,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":4,"elapsed_ns":117649,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":5,"elapsed_ns":112100,"output_hash":"c0ccad163a05cb9b","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":40,"sequence":6,"elapsed_ns":117439,"output_hash":"c0ccad163a05cb9b","output_size":262144}

run=1 size=256 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":479735,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":482371,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":478994,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":485717,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":481759,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":482511,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":485606,"output_hash":"0b7af86265795288","output_size":262144}
run=2 size=256 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":474555,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":482070,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":480928,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":474295,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":479766,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":488552,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":484314,"output_hash":"0b7af86265795288","output_size":262144}
run=3 size=256 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":485567,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":489594,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":478954,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":480617,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":481729,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":480877,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":486368,"output_hash":"0b7af86265795288","output_size":262144}
run=4 size=256 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":487269,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":484114,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":479956,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":476580,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":475046,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":471530,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":470007,"output_hash":"0b7af86265795288","output_size":262144}
run=5 size=256 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":474946,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":478813,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":476339,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":478553,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":482661,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":476670,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cpu","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":478023,"output_hash":"0b7af86265795288","output_size":262144}

run=1 size=256 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":114253,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":113872,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":111629,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":111959,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":112690,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":113031,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":112830,"output_hash":"0b7af86265795288","output_size":262144}
run=2 size=256 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":112831,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":113512,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":116938,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":111699,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":111979,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":112159,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":111819,"output_hash":"0b7af86265795288","output_size":262144}
run=3 size=256 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":118251,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":113732,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":111949,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":114393,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":113332,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":113342,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":114193,"output_hash":"0b7af86265795288","output_size":262144}
run=4 size=256 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":114013,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":117520,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":114023,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":114364,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":121316,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":120625,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":115255,"output_hash":"0b7af86265795288","output_size":262144}
run=5 size=256 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":0,"elapsed_ns":116427,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":1,"elapsed_ns":113211,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":2,"elapsed_ns":112650,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":3,"elapsed_ns":116918,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":4,"elapsed_ns":112370,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":5,"elapsed_ns":112260,"output_hash":"0b7af86265795288","output_size":262144}
{"operation":"near-lossless","variant":"cuda","width":256,"height":256,"method":4,"quality":80,"sequence":6,"elapsed_ns":113011,"output_hash":"0b7af86265795288","output_size":262144}

run=1 size=512 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":11427110,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":11506097,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":13211431,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":11348664,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":11304902,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":11294563,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":11287329,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=2 size=512 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":11285616,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":11503031,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":11552534,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":11747819,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":11669292,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":11577260,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":11418744,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=3 size=512 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":11027424,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":11329057,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":11148019,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":11054765,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":11060727,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":11056448,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":11049736,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=4 size=512 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":11522158,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":11554127,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":11610021,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":11641460,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":11402915,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":11404558,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":11357490,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=5 size=512 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":11713225,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":11595545,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":11551983,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":11583202,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":11582501,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":11572050,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":11629628,"output_hash":"69493c747c69b1e3","output_size":1048576}

run=1 size=512 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":440382,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":421486,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":427749,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":417750,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":431766,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":416668,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":420264,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=2 size=512 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":458105,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":410136,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":425274,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":413312,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":413001,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":413582,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":416808,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=3 size=512 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":410075,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":415426,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":403383,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":410426,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":408372,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":420314,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":423881,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=4 size=512 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":408993,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":472522,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":413181,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":409414,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":412400,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":408181,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":403945,"output_hash":"69493c747c69b1e3","output_size":1048576}
run=5 size=512 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":0,"elapsed_ns":420275,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":1,"elapsed_ns":443508,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":2,"elapsed_ns":417179,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":3,"elapsed_ns":420545,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":4,"elapsed_ns":407911,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":5,"elapsed_ns":417750,"output_hash":"69493c747c69b1e3","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":0,"sequence":6,"elapsed_ns":420795,"output_hash":"69493c747c69b1e3","output_size":1048576}

run=1 size=512 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":6992533,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":7006398,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":6949532,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":6926229,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":6958408,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":6964991,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":6973988,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=2 size=512 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":6863702,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":6896974,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":6959140,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":6891453,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":6907604,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":6994857,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":7025163,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=3 size=512 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":6861218,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":6688175,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":6727608,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":6633922,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":6639974,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":6644263,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":6935606,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=4 size=512 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":7023009,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":6968497,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":7055961,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":7060849,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":6983525,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":7007140,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":7008913,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=5 size=512 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":6983846,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":6987783,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":7140388,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":6974799,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":6964550,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":7078232,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":6900270,"output_hash":"6f029425c8f7afdc","output_size":1048576}

run=1 size=512 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":391551,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":390609,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":392994,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":390509,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":444720,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":406238,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":389798,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=2 size=512 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":400698,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":408012,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":392834,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":409555,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":420595,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":403122,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":405487,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=3 size=512 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":465239,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":473504,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":414814,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":498560,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":459357,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":490054,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":437597,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=4 size=512 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":401299,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":402472,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":402521,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":419623,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":398043,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":390379,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":392744,"output_hash":"6f029425c8f7afdc","output_size":1048576}
run=5 size=512 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":0,"elapsed_ns":409575,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":1,"elapsed_ns":415055,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":2,"elapsed_ns":436275,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":3,"elapsed_ns":411929,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":4,"elapsed_ns":403352,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":5,"elapsed_ns":398574,"output_hash":"6f029425c8f7afdc","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":40,"sequence":6,"elapsed_ns":396389,"output_hash":"6f029425c8f7afdc","output_size":1048576}

run=1 size=512 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":2091684,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":2127972,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":2125137,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":2087898,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":2095542,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":2111150,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":2125959,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=2 size=512 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":2087026,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":2121130,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":2095581,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":2093989,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":2090121,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":2084341,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":2091554,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=3 size=512 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":2090251,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":2088048,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":2090662,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":2137670,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":2116971,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":2099819,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":2098257,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=4 size=512 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":2085182,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":2090131,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":2131980,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":2096844,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":2082627,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":2094009,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":2096784,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=5 size=512 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":2085894,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":2099850,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":2109547,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":2111201,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":2106412,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":2095973,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cpu","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":2102344,"output_hash":"3093c8131f178fb9","output_size":1048576}

run=1 size=512 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":387624,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":382754,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":374619,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":375872,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":379428,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":383677,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":413142,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=2 size=512 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":379238,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":377184,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":373507,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":375962,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":374909,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":374038,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":380190,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=3 size=512 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":446202,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":382874,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":385219,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":396500,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":458135,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":437115,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":444059,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=4 size=512 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":387683,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":384929,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":385449,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":384488,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":383956,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":380240,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":414012,"output_hash":"3093c8131f178fb9","output_size":1048576}
run=5 size=512 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":0,"elapsed_ns":391201,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":1,"elapsed_ns":382544,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":2,"elapsed_ns":381512,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":3,"elapsed_ns":380119,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":4,"elapsed_ns":378707,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":5,"elapsed_ns":382784,"output_hash":"3093c8131f178fb9","output_size":1048576}
{"operation":"near-lossless","variant":"cuda","width":512,"height":512,"method":4,"quality":80,"sequence":6,"elapsed_ns":383636,"output_hash":"3093c8131f178fb9","output_size":1048576}

run=1 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":46903832,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":46964986,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":46688610,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":46847637,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":47061546,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":46707405,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":46566302,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=2 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":46053384,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":46021195,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":46062882,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":45992561,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":45846718,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":45942798,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":45917610,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=3 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":47117571,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":46863206,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":46797062,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":46771424,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":47046217,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":46445386,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":46463049,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=4 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":47934906,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":46212030,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":46256233,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":46024751,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":45961333,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":46490771,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":46132271,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=5 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":46272503,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":46477015,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":46209015,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":45989335,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":46122273,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":46044217,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":46236907,"output_hash":"5a7db78ffc65414d","output_size":4194304}

run=1 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":3131876,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":3132407,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":3123681,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":3183312,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":3119853,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":3125494,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":3126226,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=2 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":3139871,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":3124152,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":3192629,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":3225440,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":3349022,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":3196156,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":3598297,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=3 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":3286174,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":3268260,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":3272839,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":3390379,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":3268772,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":3292686,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":3274241,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=4 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":3262259,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":3229829,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":3218157,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":3231813,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":3220582,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":3280172,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":3226833,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=5 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":3274843,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":1,"elapsed_ns":3251860,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":2,"elapsed_ns":3226453,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":3,"elapsed_ns":3240619,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":4,"elapsed_ns":3238455,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":5,"elapsed_ns":3338612,"output_hash":"5a7db78ffc65414d","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":6,"elapsed_ns":3237203,"output_hash":"5a7db78ffc65414d","output_size":4194304}

run=1 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28911607,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":32644365,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":31274037,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":33102009,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":31780272,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":31814486,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":28962352,"output_hash":"326f85050b195aa5","output_size":4194304}
run=2 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28463842,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":28709109,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":28370988,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":28342585,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":28300166,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":28496883,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":28599525,"output_hash":"326f85050b195aa5","output_size":4194304}
run=3 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":27148897,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":27145691,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":27562478,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":28631655,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":28237349,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":28258298,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":27284359,"output_hash":"326f85050b195aa5","output_size":4194304}
run=4 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":27107259,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":27316570,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":27193320,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":27173523,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":27097130,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":27114082,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":27249093,"output_hash":"326f85050b195aa5","output_size":4194304}
run=5 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":27865094,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":27548142,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":27410225,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":29796780,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":27545849,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":30399204,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":28668773,"output_hash":"326f85050b195aa5","output_size":4194304}

run=1 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":3178794,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":3184063,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":3162162,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":3215732,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":3169486,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":3220151,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":3166480,"output_hash":"326f85050b195aa5","output_size":4194304}
run=2 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":3225871,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":4030042,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":3289210,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":3276947,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":3612233,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":4332056,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":3458355,"output_hash":"326f85050b195aa5","output_size":4194304}
run=3 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":3121036,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":3121487,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":3253984,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":3158466,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":3234558,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":3181409,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":3186759,"output_hash":"326f85050b195aa5","output_size":4194304}
run=4 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":3090369,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":3307984,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":3270875,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":3176319,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":3471039,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":3208659,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":3211083,"output_hash":"326f85050b195aa5","output_size":4194304}
run=5 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":3481168,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":1,"elapsed_ns":3270956,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":2,"elapsed_ns":3380130,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":3,"elapsed_ns":3209681,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":4,"elapsed_ns":3417329,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":5,"elapsed_ns":3242453,"output_hash":"326f85050b195aa5","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":6,"elapsed_ns":3216955,"output_hash":"326f85050b195aa5","output_size":4194304}

run=1 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8645728,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":8901546,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":10214006,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":10408679,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":8770421,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":8671496,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":8765772,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=2 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8789987,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":9411858,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":9098654,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":9245237,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":9105778,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":8983669,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":8944687,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=3 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":11967158,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":11727561,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":12343140,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":10979515,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":10203426,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":10869038,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":11126819,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=4 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8548387,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":8550981,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":8562843,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":8602889,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":8561942,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":8576950,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":8592319,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=5 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8915241,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":8716641,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":8907938,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":8725327,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":8921684,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":8706402,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":8801108,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}

run=1 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":3328723,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":3156712,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":3147305,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":3219580,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":3291424,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":3189354,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":3145571,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=2 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":3334925,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":3293628,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":3187280,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":3350414,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":3285903,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":3545108,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":3447735,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=3 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":3161431,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":3252872,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":3268040,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":3206165,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":3218738,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":3272819,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":3226383,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=4 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":3190576,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":3144259,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":3219600,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":3151472,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":3120004,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":3551740,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":3168705,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=5 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":3218548,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":1,"elapsed_ns":3276296,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":2,"elapsed_ns":3361735,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":3,"elapsed_ns":3241150,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":4,"elapsed_ns":3177010,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":5,"elapsed_ns":3188080,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":6,"elapsed_ns":3158556,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}

run=1 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":187571397,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":184127349,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":215292543,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":194743085,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":192198795,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":192730879,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":191441762,"output_hash":"0d884950781c04f3","output_size":16777216}
run=2 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":194756830,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":198774620,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":195125518,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":192644718,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":192849180,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":194641315,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":191514729,"output_hash":"0d884950781c04f3","output_size":16777216}
run=3 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":216469110,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":205072808,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":195823292,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":195325833,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":199026221,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":220519010,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":197915116,"output_hash":"0d884950781c04f3","output_size":16777216}
run=4 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":232631810,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":245966772,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":247510633,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":245072623,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":241584211,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":244663148,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":257764164,"output_hash":"0d884950781c04f3","output_size":16777216}
run=5 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":258645940,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":226675552,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":261900254,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":224637478,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":225105161,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":193562923,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":191002994,"output_hash":"0d884950781c04f3","output_size":16777216}

run=1 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":14734223,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":14723814,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":15100938,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":14760182,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":14451876,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":14699840,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":14613017,"output_hash":"0d884950781c04f3","output_size":16777216}
run=2 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":18393474,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":18240778,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":18285002,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":18284511,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":15499963,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":14761364,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":14695882,"output_hash":"0d884950781c04f3","output_size":16777216}
run=3 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":14505497,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":14874616,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":15111347,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":14540231,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":14538368,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":14712913,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":14653774,"output_hash":"0d884950781c04f3","output_size":16777216}
run=4 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":16307500,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":14668170,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":14861461,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":15074629,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":15138137,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":15513999,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":15317863,"output_hash":"0d884950781c04f3","output_size":16777216}
run=5 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":14962058,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":1,"elapsed_ns":14577802,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":2,"elapsed_ns":14617375,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":3,"elapsed_ns":15152735,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":4,"elapsed_ns":19651131,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":5,"elapsed_ns":15574502,"output_hash":"0d884950781c04f3","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":6,"elapsed_ns":15689486,"output_hash":"0d884950781c04f3","output_size":16777216}

run=1 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":117146472,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":116565988,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":116818178,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":116019138,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":116366745,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":118599203,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":117911309,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=2 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":114167590,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":114178631,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":115875639,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":115719959,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":114993192,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":114468502,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":114270944,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=3 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":116019868,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":116527346,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":115657071,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":115878235,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":115457369,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":114966432,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":115220917,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=4 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":114464565,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":115130428,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":120170847,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":115295497,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":115025332,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":115731610,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":115227920,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=5 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":114710104,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":115067651,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":115017878,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":115865300,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":115451929,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":115947583,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":118225776,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}

run=1 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":14911545,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":14869727,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":14526757,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":14173077,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":14211117,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":14095731,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":14203002,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=2 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":14284374,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":14281248,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":14329528,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":14743662,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":14227227,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":14484117,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":14250541,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=3 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":14373571,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":14079501,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":14199866,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":14415719,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":14353613,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":14328497,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":14257344,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=4 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":14585496,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":14346530,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":14363592,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":14303971,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":14415990,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":14239801,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":14260970,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=5 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":14257323,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":1,"elapsed_ns":14413655,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":2,"elapsed_ns":14416861,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":3,"elapsed_ns":14441758,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":4,"elapsed_ns":14196019,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":5,"elapsed_ns":14185660,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":6,"elapsed_ns":14625421,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}

run=1 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":49500941,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":48987853,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":49056632,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":49519877,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":49767799,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":48536872,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":49406726,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=2 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":50297508,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":50688989,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":50155082,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":49608001,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":50435385,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":49959988,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":50103406,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=3 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":49889697,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":49840194,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":48743517,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":49226218,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":48995227,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":50265589,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":49966840,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=4 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":52542979,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":51565285,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":52902611,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":51593077,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":51116116,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":50947291,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":51674238,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=5 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":50870087,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":51157894,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":50518741,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":50797181,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":50947732,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":50316203,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":52070208,"output_hash":"842a2b4ac20cf04e","output_size":16777216}

run=1 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":20111301,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":19020324,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":18025678,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":19088111,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":20483656,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":19441491,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":18558743,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=2 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":19873988,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":20152799,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":20061077,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":20237997,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":19930273,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":20212230,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":20214484,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=3 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":19721644,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":19402768,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":19390766,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":19985025,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":19335273,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":19066671,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":19762029,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=4 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":19913051,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":20439533,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":19696707,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":19862757,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":19653315,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":21015309,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":19573998,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=5 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":19716144,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":1,"elapsed_ns":19170214,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":2,"elapsed_ns":19362042,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":3,"elapsed_ns":19575661,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":4,"elapsed_ns":19239703,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":5,"elapsed_ns":19043107,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":6,"elapsed_ns":18697712,"output_hash":"842a2b4ac20cf04e","output_size":16777216}

run=1 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":796889719,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":791707836,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":787748475,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":787102009,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":779739857,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":776666330,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":780446937,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=2 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":765833842,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":763858435,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":764093884,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":768703800,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":764031649,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":770559956,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":762565643,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=3 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":777000540,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":773514413,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":769601289,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":771490716,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":771048211,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":769093002,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":772637157,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=4 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":768784648,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":770034722,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":756651600,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":758767280,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":764331827,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":775008999,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":853084802,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=5 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":752989387,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":749932451,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":747679516,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":750153925,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":755396782,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":747605198,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":754475523,"output_hash":"d71500fefa0dc952","output_size":67108864}

run=1 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":55018903,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":56107225,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":54897907,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":56838290,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":55177800,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":54664251,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":55579751,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=2 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":55699524,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":55584079,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":55784773,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":55474274,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":56548298,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":55575432,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":56346952,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=3 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":57156003,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":56702987,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":58716666,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":56001197,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":55652726,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":55449758,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":55959138,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=4 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":56151037,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":56146248,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":57299160,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":59401254,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":56631825,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":56232419,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":56310475,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=5 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":56180672,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":1,"elapsed_ns":55932149,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":2,"elapsed_ns":56152500,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":3,"elapsed_ns":56245654,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":4,"elapsed_ns":57146325,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":5,"elapsed_ns":56089913,"output_hash":"d71500fefa0dc952","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":6,"elapsed_ns":56387027,"output_hash":"d71500fefa0dc952","output_size":67108864}

run=1 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":447336593,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":462640380,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":465484890,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":464373065,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":463711942,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":465286941,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":469032603,"output_hash":"71f450145ee974ea","output_size":67108864}
run=2 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":456375688,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":458567569,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":458174195,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":458888559,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":457363622,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":459023120,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":458476019,"output_hash":"71f450145ee974ea","output_size":67108864}
run=3 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":439499606,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":438014885,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":445840504,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":456076090,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":450275702,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":442569398,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":443876537,"output_hash":"71f450145ee974ea","output_size":67108864}
run=4 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":460766977,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":462820380,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":460823003,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":459448276,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":456361915,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":457467329,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":466358306,"output_hash":"71f450145ee974ea","output_size":67108864}
run=5 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":460186385,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":464564709,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":461193435,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":461185010,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":460831770,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":463927910,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":461060417,"output_hash":"71f450145ee974ea","output_size":67108864}

run=1 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":54925701,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":55437275,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":54863985,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":54681886,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":54469709,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":54532205,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":55029835,"output_hash":"71f450145ee974ea","output_size":67108864}
run=2 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":54828098,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":55585512,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":55503549,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":55047057,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":55222576,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":54891306,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":54953983,"output_hash":"71f450145ee974ea","output_size":67108864}
run=3 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":55691480,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":53901398,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":53852397,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":55573490,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":54050638,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":53892261,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":53814937,"output_hash":"71f450145ee974ea","output_size":67108864}
run=4 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":56399562,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":55418261,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":55106197,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":59812172,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":54899392,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":55252080,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":55795285,"output_hash":"71f450145ee974ea","output_size":67108864}
run=5 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":54535873,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":1,"elapsed_ns":55461281,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":2,"elapsed_ns":55300089,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":3,"elapsed_ns":55023283,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":4,"elapsed_ns":55072725,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":5,"elapsed_ns":55856689,"output_hash":"71f450145ee974ea","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":6,"elapsed_ns":54661648,"output_hash":"71f450145ee974ea","output_size":67108864}

run=1 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":141661833,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":143624817,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":143783824,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":141808387,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":141687280,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":146109356,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":142803214,"output_hash":"b263af55aab9e509","output_size":67108864}
run=2 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":142428314,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":143599860,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":143236783,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":143625439,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":143073358,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":142118085,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":142846103,"output_hash":"b263af55aab9e509","output_size":67108864}
run=3 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":138176938,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":141489492,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":138812684,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":141669888,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":139012037,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":142755155,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":143370443,"output_hash":"b263af55aab9e509","output_size":67108864}
run=4 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":138690767,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":142112355,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":139542417,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":141475596,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":146861279,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":141218826,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":138139257,"output_hash":"b263af55aab9e509","output_size":67108864}
run=5 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":141686580,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":143457887,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":141876134,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":142517460,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":141549373,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":142547086,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":141869261,"output_hash":"b263af55aab9e509","output_size":67108864}

run=1 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":53622739,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":53047095,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":52636378,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":52832123,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":54128403,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":52753706,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":52918274,"output_hash":"b263af55aab9e509","output_size":67108864}
run=2 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":53643939,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":53557127,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":54834011,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":53731322,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":53599876,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":53820288,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":53514517,"output_hash":"b263af55aab9e509","output_size":67108864}
run=3 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":56518174,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":53810138,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":54159151,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":55441384,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":53832721,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":54982768,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":53757361,"output_hash":"b263af55aab9e509","output_size":67108864}
run=4 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":54760423,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":52795185,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":53564701,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":52810062,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":53123918,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":52952648,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":52581395,"output_hash":"b263af55aab9e509","output_size":67108864}
run=5 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":55024416,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":1,"elapsed_ns":54072819,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":2,"elapsed_ns":53613933,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":3,"elapsed_ns":53497876,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":4,"elapsed_ns":54884755,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":5,"elapsed_ns":53803397,"output_hash":"b263af55aab9e509","output_size":67108864}
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":6,"elapsed_ns":54088879,"output_hash":"b263af55aab9e509","output_size":67108864}

run=1 size=64 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":81702,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":79929,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":78136,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":76813,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":76012,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":80881,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":74920,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=2 size=64 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":81262,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":81081,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":77304,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":85770,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":80471,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":74930,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":74359,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=3 size=64 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":79879,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":77044,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":81662,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":74188,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":73737,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":73306,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":72966,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=4 size=64 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":88425,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":79288,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":77665,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":76152,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":75461,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":74479,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":73707,"output_hash":"bfb17b699f8fe23b","output_size":16384}
run=5 size=64 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":0,"elapsed_ns":81612,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":1,"elapsed_ns":78867,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":2,"elapsed_ns":76603,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":3,"elapsed_ns":76082,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":4,"elapsed_ns":75370,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":5,"elapsed_ns":76864,"output_hash":"bfb17b699f8fe23b","output_size":16384}
{"operation":"near-lossless","variant":"cpu","width":64,"height":64,"method":4,"quality":40,"sequence":6,"elapsed_ns":73367,"output_hash":"bfb17b699f8fe23b","output_size":16384}

```

## Cold raw output (90 JSON rows)

The following blocks are the exact stdout from the 18 cold batches.

```text
run=1 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":45394231,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=2 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":47611390,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=3 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":45474291,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=4 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":45166376,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=5 size=1024 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":46349054,"output_hash":"5a7db78ffc65414d","output_size":4194304}

run=1 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":229272834,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=2 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":146890914,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=3 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":148251283,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=4 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":155805887,"output_hash":"5a7db78ffc65414d","output_size":4194304}
run=5 size=1024 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":0,"sequence":0,"elapsed_ns":143319898,"output_hash":"5a7db78ffc65414d","output_size":4194304}

run=1 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":27601446,"output_hash":"326f85050b195aa5","output_size":4194304}
run=2 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28092132,"output_hash":"326f85050b195aa5","output_size":4194304}
run=3 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28057407,"output_hash":"326f85050b195aa5","output_size":4194304}
run=4 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28390189,"output_hash":"326f85050b195aa5","output_size":4194304}
run=5 size=1024 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":28481348,"output_hash":"326f85050b195aa5","output_size":4194304}

run=1 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":136705761,"output_hash":"326f85050b195aa5","output_size":4194304}
run=2 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":138952605,"output_hash":"326f85050b195aa5","output_size":4194304}
run=3 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":141683242,"output_hash":"326f85050b195aa5","output_size":4194304}
run=4 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":138655380,"output_hash":"326f85050b195aa5","output_size":4194304}
run=5 size=1024 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":40,"sequence":0,"elapsed_ns":138900047,"output_hash":"326f85050b195aa5","output_size":4194304}

run=1 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8873685,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=2 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8852696,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=3 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":9024366,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=4 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8837989,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=5 size=1024 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":8761837,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}

run=1 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":138122375,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=2 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":144743606,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=3 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":137421597,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=4 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":139052903,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}
run=5 size=1024 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":1024,"height":1024,"method":4,"quality":80,"sequence":0,"elapsed_ns":136934067,"output_hash":"aa6d0b6c4c51a529","output_size":4194304}

run=1 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":192481883,"output_hash":"0d884950781c04f3","output_size":16777216}
run=2 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":190132678,"output_hash":"0d884950781c04f3","output_size":16777216}
run=3 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":188379625,"output_hash":"0d884950781c04f3","output_size":16777216}
run=4 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":189187784,"output_hash":"0d884950781c04f3","output_size":16777216}
run=5 size=2048 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":182766546,"output_hash":"0d884950781c04f3","output_size":16777216}

run=1 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":156716427,"output_hash":"0d884950781c04f3","output_size":16777216}
run=2 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":177599711,"output_hash":"0d884950781c04f3","output_size":16777216}
run=3 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":171863002,"output_hash":"0d884950781c04f3","output_size":16777216}
run=4 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":173054877,"output_hash":"0d884950781c04f3","output_size":16777216}
run=5 size=2048 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":0,"sequence":0,"elapsed_ns":173026734,"output_hash":"0d884950781c04f3","output_size":16777216}

run=1 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":114001176,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=2 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":111996383,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=3 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":115736385,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=4 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":112960243,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=5 size=2048 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":115937511,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}

run=1 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":171023685,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=2 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":167978551,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=3 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":169373214,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=4 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":170513413,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}
run=5 size=2048 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":40,"sequence":0,"elapsed_ns":174398956,"output_hash":"3b7d3b44a2d821e5","output_size":16777216}

run=1 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":35698651,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=2 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":34894120,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=3 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":35865534,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=4 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":35331967,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=5 size=2048 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":36008069,"output_hash":"842a2b4ac20cf04e","output_size":16777216}

run=1 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":163640873,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=2 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":177316943,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=3 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":171118171,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=4 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":171526343,"output_hash":"842a2b4ac20cf04e","output_size":16777216}
run=5 size=2048 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":2048,"height":2048,"method":4,"quality":80,"sequence":0,"elapsed_ns":183886829,"output_hash":"842a2b4ac20cf04e","output_size":16777216}

run=1 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":750660074,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=2 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":765671367,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=3 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":744170230,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=4 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":759865039,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=5 size=4096 quality=0 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":746788728,"output_hash":"d71500fefa0dc952","output_size":67108864}

run=1 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":331084834,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=2 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":250884248,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=3 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":246257893,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=4 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":259205202,"output_hash":"d71500fefa0dc952","output_size":67108864}
run=5 size=4096 quality=0 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":0,"sequence":0,"elapsed_ns":249237785,"output_hash":"d71500fefa0dc952","output_size":67108864}

run=1 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":456478903,"output_hash":"71f450145ee974ea","output_size":67108864}
run=2 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":456323524,"output_hash":"71f450145ee974ea","output_size":67108864}
run=3 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":465887798,"output_hash":"71f450145ee974ea","output_size":67108864}
run=4 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":461113004,"output_hash":"71f450145ee974ea","output_size":67108864}
run=5 size=4096 quality=40 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":460523414,"output_hash":"71f450145ee974ea","output_size":67108864}

run=1 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":322444915,"output_hash":"71f450145ee974ea","output_size":67108864}
run=2 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":251125459,"output_hash":"71f450145ee974ea","output_size":67108864}
run=3 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":248712415,"output_hash":"71f450145ee974ea","output_size":67108864}
run=4 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":253069638,"output_hash":"71f450145ee974ea","output_size":67108864}
run=5 size=4096 quality=40 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":40,"sequence":0,"elapsed_ns":247319875,"output_hash":"71f450145ee974ea","output_size":67108864}

run=1 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":141890856,"output_hash":"b263af55aab9e509","output_size":67108864}
run=2 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":142350844,"output_hash":"b263af55aab9e509","output_size":67108864}
run=3 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":141985773,"output_hash":"b263af55aab9e509","output_size":67108864}
run=4 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":142440042,"output_hash":"b263af55aab9e509","output_size":67108864}
run=5 size=4096 quality=80 variant=cpu
{"operation":"near-lossless","variant":"cpu","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":144815305,"output_hash":"b263af55aab9e509","output_size":67108864}

run=1 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":303103491,"output_hash":"b263af55aab9e509","output_size":67108864}
run=2 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":245517371,"output_hash":"b263af55aab9e509","output_size":67108864}
run=3 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":253353249,"output_hash":"b263af55aab9e509","output_size":67108864}
run=4 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":244149037,"output_hash":"b263af55aab9e509","output_size":67108864}
run=5 size=4096 quality=80 variant=cuda
{"operation":"near-lossless","variant":"cuda","width":4096,"height":4096,"method":4,"quality":80,"sequence":0,"elapsed_ns":250586705,"output_hash":"b263af55aab9e509","output_size":67108864}

```

## Computed warm medians

Each median is over 35 measured samples (5 processes × 7 samples). Speedup is
CPU median divided by CUDA median; values above 1x favor CUDA.

| Size | Quality (limit bits) | CPU median ms | CUDA median ms | CPU/CUDA | Stable hash |
|---:|---:|---:|---:|---:|:--|
| 64² | 0 (5) | 0.132558 | 0.025768 | 5.1443x | 67e96c35e16aca52 |
| 64² | 40 (3) | 0.076864 | 0.020919 | 3.6744x | bfb17b699f8fe23b |
| 64² | 80 (1) | 0.016641 | 0.016551 | 1.0054x | 52bd82584ee63f61 |
| 128² | 0 (5) | 0.689386 | 0.048190 | 14.3056x | e95f0a29556928a0 |
| 128² | 40 (3) | 0.402431 | 0.043381 | 9.2767x | 6d31f36f229dbc06 |
| 128² | 80 (1) | 0.105838 | 0.038913 | 2.7199x | 365eea827b03ee04 |
| 256² | 0 (5) | 2.848016 | 0.121427 | 23.4546x | d249f660ec81a308 |
| 256² | 40 (3) | 1.696877 | 0.113672 | 14.9278x | c0ccad163a05cb9b |
| 256² | 80 (1) | 0.480617 | 0.113342 | 4.2404x | 0b7af86265795288 |
| 512² | 0 (5) | 11.503031 | 0.416808 | 27.5979x | 69493c747c69b1e3 |
| 512² | 40 (3) | 6.964991 | 0.405487 | 17.1769x | 6f029425c8f7afdc |
| 512² | 80 (1) | 2.095973 | 0.382874 | 5.4743x | 3093c8131f178fb9 |
| 1024² | 0 (5) | 46.272503 | 3.231813 | 14.3178x | 5a7db78ffc65414d |
| 1024² | 40 (3) | 28.300166 | 3.220151 | 8.7885x | 326f85050b195aa5 |
| 1024² | 80 (1) | 8.907938 | 3.219580 | 2.7668x | aa6d0b6c4c51a529 |
| 2048² | 0 (5) | 198.774620 | 14.874616 | 13.3633x | 0d884950781c04f3 |
| 2048² | 40 (3) | 115.657071 | 14.328497 | 8.0718x | 3b7d3b44a2d821e5 |
| 2048² | 80 (1) | 50.265589 | 19.696707 | 2.5520x | 842a2b4ac20cf04e |
| 4096² | 0 (5) | 769.093002 | 56.146248 | 13.6980x | d71500fefa0dc952 |
| 4096² | 40 (3) | 459.448276 | 55.029835 | 8.3491x | 71f450145ee974ea |
| 4096² | 80 (1) | 142.112355 | 53.643939 | 2.6492x | b263af55aab9e509 |

## Computed cold medians

Each median is over five one-shot process samples. Speedup is CPU median divided
by CUDA median; values above 1x favor CUDA.

| Size | Quality (limit bits) | CPU median ms | CUDA median ms | CPU/CUDA | Stable hash |
|---:|---:|---:|---:|---:|:--|
| 1024² | 0 (5) | 45.474291 | 148.251283 | 0.3067x | 5a7db78ffc65414d |
| 1024² | 40 (3) | 28.092132 | 138.900047 | 0.2022x | 326f85050b195aa5 |
| 1024² | 80 (1) | 8.852696 | 138.122375 | 0.0641x | aa6d0b6c4c51a529 |
| 2048² | 0 (5) | 189.187784 | 173.026734 | 1.0934x | 0d884950781c04f3 |
| 2048² | 40 (3) | 114.001176 | 170.513413 | 0.6686x | 3b7d3b44a2d821e5 |
| 2048² | 80 (1) | 35.698651 | 171.526343 | 0.2081x | 842a2b4ac20cf04e |
| 4096² | 0 (5) | 750.660074 | 250.884248 | 2.9921x | d71500fefa0dc952 |
| 4096² | 40 (3) | 460.523414 | 251.125459 | 1.8338x | 71f450145ee974ea |
| 4096² | 80 (1) | 142.350844 | 250.586705 | 0.5681x | b263af55aab9e509 |

## Evaluation for the originating task

Correctness: 1,560/1,560 raw rows retained stable expected hashes, and the
direct parity test passed all 20 sizes/strides/limit-bit cases.

Warm crossover: the GPU is faster in every tested case, with the weakest
measured case at 64² quality 80 (1.0054x, effectively parity). A warm
minimum of 65,536 pixels (256²) is conservative for this GPU and avoids
claiming a small-image win.

Cold crossover: initialization dominates. At 1,024² CUDA is 3.26x–15.6x
slower; at 2,048² it is faster only at quality 0 (1.0934x); at 4,096² it is
faster at qualities 0 and 40 but remains 1.76x slower at quality 80. The
evidence does not support the current single quality-blind 4-million-pixel
cold threshold. A conservative integration should keep cold dispatch on CPU
unless the implementation adds a quality-aware gate; if a single gate is
required, use at least 16,777,216 pixels and still keep quality 80 on CPU
until larger-image evidence exists. These recommendations are intentionally
more conservative than the warm threshold.

