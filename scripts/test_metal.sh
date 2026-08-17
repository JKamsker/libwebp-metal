#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
encoder="$root_dir/examples/cwebp"
decoder="$root_dir/examples/dwebp"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-metal-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

if [ ! -x "$encoder" ] || [ ! -x "$decoder" ]; then
  echo "build cwebp and dwebp before running this test" >&2
  exit 2
fi

if [ "$#" -eq 0 ]; then
  set -- "$root_dir/examples/test_ref.ppm"
fi

for input do
  name=$(basename -- "$input")

  # The independent-tile cross-color search may change the compressed stream,
  # but a lossless decode must remain pixel-exact.
  WEBP_METAL=0 "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-transform-cpu.webp"
  WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=0 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-transform-metal.webp"
  "$decoder" -quiet "$temporary_dir/$name-transform-cpu.webp" -pam \
    -o "$temporary_dir/$name-transform-cpu.pam"
  "$decoder" -quiet "$temporary_dir/$name-transform-metal.webp" -pam \
    -o "$temporary_dir/$name-transform-metal.pam"
  cmp "$temporary_dir/$name-transform-cpu.pam" \
      "$temporary_dir/$name-transform-metal.pam"

  # Candidate search plus CPU replay promises the exact CPU bitstream.
  for method in 0 1 2 3 4 5 6; do
    WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-cpu.webp"
    WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=1 \
      WEBP_METAL_HASH_MIN_PIXELS=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-metal.webp"
    cmp "$temporary_dir/$name-hash-cpu.webp" \
        "$temporary_dir/$name-hash-metal.webp"
  done

  # The supported opaque RGB/BGR conversion also promises the exact stream.
  for settings in "25 0" "75 4" "95 6"; do
    set -- $settings
    quality=$1
    method=$2
    WEBP_METAL_LOSSY=0 \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-cpu.webp"
    WEBP_METAL_LOSSY=1 WEBP_METAL_LOSSY_MIN_PIXELS=0 \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-metal.webp"
    cmp "$temporary_dir/$name-lossy-cpu.webp" \
        "$temporary_dir/$name-lossy-metal.webp"
  done

  printf 'PASS: Metal correctness checks: %s\n' "$input"
done
