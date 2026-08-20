#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/mnt/data/cuda_review/libwebp-metal-codex-cuda-encoder-acceleration}"
cd "$ROOT"
grep -q 'int device = 0;' src/enc/cuda_decimate_enc.cu
grep -q 'return strcmp(value, "0") != 0;' src/enc/cuda_decimate_enc.cu
grep -q 'params.recon_y_stride = (uint32_t)request->mb_w \* 16u;' src/enc/cuda_decimate_enc.cu
grep -q 'request->recon_y + (size_t)row_start \* 16 \* ys' src/enc/cuda_decimate_enc.cu
grep -q 'if (band == state->pending_band_count - 1)' src/enc/cuda_decimate_enc.cu
grep -q 'uint8_t reserved\[2\];' src/enc/cuda_decimate_enc.cu
grep -q 'const uint32_t\* const src32 = (const uint32_t\*)&w.rd;' src/enc/cuda_decimate_enc.cu
grep -q 'v.segment_params\[v.segments\[mb_index\]\]' src/enc/cuda_decimate_enc.cu
grep -q 'if (request == nullptr) return WEBP_ACCELERATOR_SUCCESS;' src/enc/cuda_enc.cu
grep -q 'pthread_detach(thread)' src/enc/cuda_enc.cu
grep -q 'set(CMAKE_CUDA_ARCHITECTURES native)' CMakeLists.txt
grep -q '^EXTRA_DIST = cuda_enc.cu cuda_enc.h$' src/enc/Makefile.am
! grep -q 'cuda_decimate_enc.cu' src/enc/Makefile.am
! grep -q 'add_test.*cuda_' CMakeLists.txt
printf 'all source assertions passed\n'
