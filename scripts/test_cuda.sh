#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
binary_dir=${WEBP_TEST_BIN_DIR:-"$root_dir/build-cuda"}
encoder="$binary_dir/cwebp"
decoder="$binary_dir/dwebp"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-cuda-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM
cuda_log="$temporary_dir/cuda.log"
cold_log="$temporary_dir/cold.log"
lossy_default_log="$temporary_dir/lossy-default.log"

if [ ! -x "$encoder" ] || [ ! -x "$decoder" ]; then
  echo "cwebp and dwebp not found in $binary_dir" >&2
  exit 2
fi

if [ "$#" -eq 0 ]; then
  set -- "$root_dir/examples/test_ref.ppm"
fi

# A known-small one-shot encode should decline before CUDA initialization.
WEBP_ACCELERATOR=none \
  "$encoder" -quiet -lossless -exact -m 4 "$root_dir/examples/test_ref.ppm" \
  -o "$temporary_dir/cold-cpu.webp"
WEBP_ACCELERATOR=cuda WEBP_CUDA_VERBOSE=1 \
  "$encoder" -quiet -lossless -exact -m 4 "$root_dir/examples/test_ref.ppm" \
  -o "$temporary_dir/cold-default.webp" 2>>"$cold_log"
cmp "$temporary_dir/cold-cpu.webp" "$temporary_dir/cold-default.webp"

# Lossy CUDA is deliberately opt-in: measured end-to-end batch performance was
# neutral, while fresh-process runtime initialization made it much slower.
WEBP_ACCELERATOR=none \
  "$encoder" -quiet -q 75 -m 4 "$root_dir/examples/test_ref.ppm" \
  -o "$temporary_dir/lossy-default-cpu.webp"
WEBP_ACCELERATOR=cuda WEBP_CUDA_LOSSY_MIN_PIXELS=0 WEBP_CUDA_VERBOSE=1 \
  "$encoder" -quiet -q 75 -m 4 "$root_dir/examples/test_ref.ppm" \
  -o "$temporary_dir/lossy-default-cuda.webp" 2>>"$lossy_default_log"
cmp "$temporary_dir/lossy-default-cpu.webp" \
    "$temporary_dir/lossy-default-cuda.webp"
if grep -q "WebP-CUDA: lossy RGB->YUV" "$lossy_default_log"; then
  echo "lossy CUDA ran without the WEBP_CUDA_LOSSY opt-in" >&2
  exit 1
fi

for input do
  name=$(basename -- "$input")

  WEBP_ACCELERATOR=none \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-cpu.webp"

  WEBP_ACCELERATOR=cuda WEBP_CUDA_MIN_PIXELS=0 WEBP_CUDA_VERBOSE=1 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-cuda-1.webp" 2>>"$cuda_log"
  WEBP_ACCELERATOR=cuda WEBP_CUDA_MIN_PIXELS=0 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-cuda-2.webp"
  cmp "$temporary_dir/$name-cuda-1.webp" \
      "$temporary_dir/$name-cuda-2.webp"

  "$decoder" -quiet "$temporary_dir/$name-cpu.webp" -pam \
    -o "$temporary_dir/$name-cpu.pam"
  "$decoder" -quiet "$temporary_dir/$name-cuda-1.webp" -pam \
    -o "$temporary_dir/$name-cuda.pam"
  cmp "$temporary_dir/$name-cpu.pam" "$temporary_dir/$name-cuda.pam"

  WEBP_ACCELERATOR=cuda WEBP_CUDA=0 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-disabled.webp"
  cmp "$temporary_dir/$name-cpu.webp" "$temporary_dir/$name-disabled.webp"

  WEBP_ACCELERATOR=cuda WEBP_CUDA_DEVICE=2147483647 \
    WEBP_CUDA_MIN_PIXELS=0 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-no-device.webp"
  cmp "$temporary_dir/$name-cpu.webp" "$temporary_dir/$name-no-device.webp"

  # CUDA hash candidates plus CPU replay promise the exact CPU bitstream.
  for method in 0 1 2 3 4 5 6; do
    WEBP_ACCELERATOR=none \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-cpu.webp"
    WEBP_ACCELERATOR=cuda WEBP_CUDA_COLOR=0 WEBP_CUDA_HASH=1 \
      WEBP_CUDA_HASH_MIN_PIXELS=0 WEBP_CUDA_VERBOSE=1 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-cuda.webp" 2>>"$cuda_log"
    cmp "$temporary_dir/$name-hash-cpu.webp" \
        "$temporary_dir/$name-hash-cuda.webp"
  done

  # Cross-color output may choose a different valid transform than the CPU,
  # but it must remain deterministic and decode losslessly at every method.
  for method in 0 1 2 3 4 5 6; do
    WEBP_ACCELERATOR=none \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-color-cpu.webp"
    WEBP_ACCELERATOR=cuda WEBP_CUDA_COLOR=1 WEBP_CUDA_HASH=0 \
      WEBP_CUDA_MIN_PIXELS=0 WEBP_CUDA_VERBOSE=1 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-color-cuda-1.webp" 2>>"$cuda_log"
    WEBP_ACCELERATOR=cuda WEBP_CUDA_COLOR=1 WEBP_CUDA_HASH=0 \
      WEBP_CUDA_MIN_PIXELS=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-color-cuda-2.webp"
    cmp "$temporary_dir/$name-color-cuda-1.webp" \
        "$temporary_dir/$name-color-cuda-2.webp"
    "$decoder" -quiet "$temporary_dir/$name-color-cpu.webp" -pam \
      -o "$temporary_dir/$name-color-cpu.pam"
    "$decoder" -quiet "$temporary_dir/$name-color-cuda-1.webp" -pam \
      -o "$temporary_dir/$name-color-cuda.pam"
    cmp "$temporary_dir/$name-color-cpu.pam" \
        "$temporary_dir/$name-color-cuda.pam"
  done

  # The opaque regular RGB/BGR conversion also promises the exact CPU stream.
  for settings in "25 0" "75 4" "95 6"; do
    set -- $settings
    quality=$1
    method=$2
    WEBP_ACCELERATOR=none \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-cpu.webp"
    WEBP_ACCELERATOR=cuda WEBP_CUDA_LOSSY=1 \
      WEBP_CUDA_LOSSY_MIN_PIXELS=0 WEBP_CUDA_VERBOSE=1 \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-cuda.webp" 2>>"$cuda_log"
    cmp "$temporary_dir/$name-lossy-cpu.webp" \
        "$temporary_dir/$name-lossy-cuda.webp"
  done

  # Near-lossless preprocessing promises the exact CPU-preprocessed stream.
  for quality in 20 60 90; do
    WEBP_ACCELERATOR=none \
      "$encoder" -quiet -lossless -near_lossless "$quality" -m 4 "$input" \
      -o "$temporary_dir/$name-near-cpu.webp"
    WEBP_ACCELERATOR=cuda WEBP_CUDA_COLOR=0 WEBP_CUDA_HASH=0 \
      WEBP_CUDA_NEAR_LOSSLESS=1 WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS=0 \
      WEBP_CUDA_VERBOSE=1 \
      "$encoder" -quiet -lossless -near_lossless "$quality" -m 4 "$input" \
      -o "$temporary_dir/$name-near-cuda.webp" 2>>"$cuda_log"
    cmp "$temporary_dir/$name-near-cpu.webp" \
        "$temporary_dir/$name-near-cuda.webp"
  done

  printf 'PASS: CUDA color/hash/RGB correctness checks: %s\n' "$input"
done

grep -q "WebP-CUDA: using" "$cuda_log"
grep -q "WebP-CUDA: transformed" "$cuda_log"
grep -q "WebP-CUDA: hash candidates" "$cuda_log"
grep -q "WebP-CUDA: lossy RGB->YUV" "$cuda_log"
if grep -q "WebP-CUDA: using" "$cold_log"; then
  echo "small default encode initialized CUDA before its cold threshold" >&2
  exit 1
fi
printf 'PASS: observed forced color/hash/RGB CUDA stages\n'
printf 'PASS: lossy CUDA remains opt-in by default\n'
