#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-cuda-variants.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM
cmake_command=${CMAKE:-cmake}

build_and_test() {
  name=$1
  shift
  build_dir="$temporary_dir/$name"
  "$cmake_command" -S "$root_dir" -B "$build_dir" \
    -DWEBP_ENABLE_CUDA=ON \
    -DWEBP_BUILD_CWEBP=ON \
    -DWEBP_BUILD_DWEBP=ON \
    -DWEBP_BUILD_CUDA_BENCHMARK=ON \
    -DWEBP_BUILD_EXTRAS=OFF \
    -DWEBP_BUILD_ANIM_UTILS=OFF \
    -DWEBP_BUILD_GIF2WEBP=OFF \
    -DWEBP_BUILD_IMG2WEBP=OFF \
    -DWEBP_BUILD_VWEBP=OFF \
    -DWEBP_BUILD_WEBPINFO=OFF \
    -DWEBP_BUILD_WEBPMUX=OFF \
    "$@"
  "$cmake_command" --build "$build_dir" \
    --target cwebp dwebp webp_cuda_batch_benchmark cuda_concurrency_test \
      cuda_near_lossless_test -j
  WEBP_TEST_BIN_DIR="$build_dir" "$root_dir/scripts/test_cuda.sh"
  batch_log="$temporary_dir/$name-batch.log"
  WEBP_CUDA_VERBOSE=1 WEBP_CUDA_BATCH_MIN_PIXELS=1 \
    "$build_dir/webp_cuda_batch_benchmark" --variant cuda --mode lossless \
      --batch-size 24 --batch-aware --verify-only \
      "$root_dir/examples/test_ref.ppm" 2>"$batch_log"
  grep -q "WebP-CUDA: transformed" "$batch_log"
  "$build_dir/cuda_concurrency_test"
  if [ "$name" = defaults ]; then
    "$build_dir/cuda_near_lossless_test"
  else
    "$build_dir/cuda_near_lossless_test" --allow-fallback
  fi
}

build_and_test defaults
build_and_test baseline \
  -DWEBP_CUDA_ENABLE_COLOR_SHARED_TILE=OFF \
  -DWEBP_CUDA_ENABLE_NEAR_LOSSLESS=OFF \
  -DWEBP_CUDA_ENABLE_PERSISTENT_BUFFERS=OFF \
  -DWEBP_CUDA_ENABLE_PINNED_HOST_MEMORY=OFF \
  -DWEBP_CUDA_ENABLE_ASYNC_COPIES=OFF \
  -DWEBP_CUDA_ENABLE_HASH_MATCH4=OFF \
  -DWEBP_CUDA_ENABLE_RGB_BLOCK_2X2=OFF \
  -DWEBP_CUDA_ENABLE_COLOR_256_THREAD_BLOCKS=OFF \
  -DWEBP_CUDA_ENABLE_HASH_256_THREAD_BLOCKS=OFF \
  -DWEBP_CUDA_ENABLE_RGB_256_THREAD_BLOCKS=OFF \
  -DWEBP_CUDA_ENABLE_READ_ONLY_CACHE=OFF \
  -DWEBP_CUDA_ENABLE_RESTRICT_POINTERS=OFF \
  -DWEBP_CUDA_ENABLE_RGB_PACKED4_LOADS=OFF \
  -DWEBP_CUDA_ENABLE_STREAM_ORDERED_ALLOCATIONS=OFF

printf 'PASS: default and baseline CUDA compile-time variants\n'
