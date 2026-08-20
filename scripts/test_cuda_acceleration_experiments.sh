#!/bin/sh
# Compile and correctness-check every isolated CUDA acceleration experiment.
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=${WEBP_CUDA_EXPERIMENT_BUILD_DIR:-"$repo_dir/build-cuda-experiments"}
cmake_command=${CMAKE:-cmake}

"$cmake_command" -S "$repo_dir" -B "$build_dir" \
  -DWEBP_ENABLE_CUDA=ON \
  -DWEBP_BUILD_CUDA_ACCELERATION_EXPERIMENTS=ON \
  -DWEBP_BUILD_CUDA_BENCHMARK=OFF \
  -DWEBP_BUILD_CWEBP=OFF \
  -DWEBP_BUILD_DWEBP=OFF \
  -DWEBP_BUILD_GIF2WEBP=OFF \
  -DWEBP_BUILD_IMG2WEBP=OFF \
  -DWEBP_BUILD_VWEBP=OFF \
  -DWEBP_BUILD_WEBPINFO=OFF \
  -DWEBP_BUILD_WEBPMUX=OFF \
  -DWEBP_BUILD_EXTRAS=OFF
"$cmake_command" --build "$build_dir" \
  --target cuda_acceleration_experiments --parallel
"$build_dir/cuda_acceleration_experiments" --verify
