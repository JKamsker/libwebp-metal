#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
binary_dir=${WEBP_TEST_BIN_DIR:-"$root_dir/examples"}
encoder="$binary_dir/cwebp"
decoder="$binary_dir/dwebp"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-metal-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM
metal_log="$temporary_dir/metal.log"
require_metal=${WEBP_TEST_REQUIRE_METAL:-0}
run_ablation=${WEBP_METAL_ABLATION_EXPERIMENT:-0}
metal_verbose=0
if [ "$require_metal" = 1 ]; then
  metal_verbose=1
fi

if [ ! -x "$encoder" ] || [ ! -x "$decoder" ]; then
  echo "cwebp and dwebp not found in $binary_dir" >&2
  exit 2
fi
if [ "$run_ablation" = 1 ]; then
  ablation_probe="$root_dir/extras/metal_import_bench"
  if [ ! -x "$ablation_probe" ] ||
     ! "$ablation_probe" --guard-check >/dev/null; then
    echo "build the test binaries with WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1" >&2
    exit 2
  fi
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
  WEBP_METAL_VERBOSE="$metal_verbose" WEBP_METAL_MIN_PIXELS=0 \
    WEBP_METAL_HASH=0 \
    "$encoder" -quiet -lossless -exact -m 4 "$input" \
    -o "$temporary_dir/$name-transform-metal-baseline.webp" 2>>"$metal_log"
  "$decoder" -quiet "$temporary_dir/$name-transform-cpu.webp" -pam \
    -o "$temporary_dir/$name-transform-cpu.pam"
  "$decoder" -quiet "$temporary_dir/$name-transform-metal-baseline.webp" -pam \
    -o "$temporary_dir/$name-transform-metal.pam"
  cmp "$temporary_dir/$name-transform-cpu.pam" \
      "$temporary_dir/$name-transform-metal.pam"

  if [ "$run_ablation" = 1 ]; then
    for variant in dispatch_2d threads_128 threads_512 unretained_commands; do
      case "$variant" in
        dispatch_2d) set -- WEBP_METAL_TRANSFORM_DISPATCH_2D=1 ;;
        threads_128) set -- WEBP_METAL_TRANSFORM_THREADS=128 ;;
        threads_512) set -- WEBP_METAL_TRANSFORM_THREADS=512 ;;
        unretained_commands)
          set -- WEBP_METAL_TRANSFORM_UNRETAINED_COMMAND_BUFFERS=1 ;;
      esac
      env "$@" WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=0 \
        "$encoder" -quiet -lossless -exact -m 4 "$input" \
        -o "$temporary_dir/$name-transform-$variant.webp"
      cmp "$temporary_dir/$name-transform-metal-baseline.webp" \
          "$temporary_dir/$name-transform-$variant.webp"
    done
  fi

  # Candidate search plus CPU replay promises the exact CPU bitstream.
  for method in 0 1 2 3 4 5 6; do
    WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-cpu.webp"
    WEBP_METAL_VERBOSE="$metal_verbose" WEBP_METAL_MIN_PIXELS=0 \
      WEBP_METAL_HASH=1 \
      WEBP_METAL_HASH_MIN_PIXELS=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$temporary_dir/$name-hash-metal-baseline.webp" 2>>"$metal_log"
    cmp "$temporary_dir/$name-hash-cpu.webp" \
        "$temporary_dir/$name-hash-metal-baseline.webp"
    if [ "$run_ablation" = 1 ]; then
      for variant in match4 write_combined threads_128 threads_512 \
                     unretained_commands; do
        case "$variant" in
          match4) set -- WEBP_METAL_HASH_MATCH4=1 ;;
          write_combined) set -- WEBP_METAL_WRITE_COMBINED_INPUTS=1 ;;
          threads_128) set -- WEBP_METAL_HASH_THREADS=128 ;;
          threads_512) set -- WEBP_METAL_HASH_THREADS=512 ;;
          unretained_commands)
            set -- WEBP_METAL_HASH_UNRETAINED_COMMAND_BUFFERS=1 ;;
        esac
        env "$@" WEBP_METAL_MIN_PIXELS=0 WEBP_METAL_HASH=1 \
          WEBP_METAL_HASH_MIN_PIXELS=0 \
          "$encoder" -quiet -lossless -exact -m "$method" "$input" \
          -o "$temporary_dir/$name-hash-$variant.webp"
        cmp "$temporary_dir/$name-hash-cpu.webp" \
            "$temporary_dir/$name-hash-$variant.webp"
      done
    fi
  done

  # The supported opaque RGB/BGR conversion also promises the exact stream.
  for settings in "25 0" "75 4" "95 6"; do
    set -- $settings
    quality=$1
    method=$2
    WEBP_METAL_LOSSY=0 \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-cpu.webp"
    WEBP_METAL_VERBOSE="$metal_verbose" WEBP_METAL_LOSSY=1 \
      WEBP_METAL_LOSSY_MIN_PIXELS=0 \
      "$encoder" -quiet -q "$quality" -m "$method" "$input" \
      -o "$temporary_dir/$name-lossy-metal-baseline.webp" 2>>"$metal_log"
    cmp "$temporary_dir/$name-lossy-cpu.webp" \
        "$temporary_dir/$name-lossy-metal-baseline.webp"
    if [ "$run_ablation" = 1 ]; then
      for variant in block_2x2 write_combined contiguous_copy threads_128 \
                     threads_512 unretained_commands; do
        case "$variant" in
          block_2x2) set -- WEBP_METAL_LOSSY_BLOCK_2X2=1 ;;
          write_combined) set -- WEBP_METAL_WRITE_COMBINED_INPUTS=1 ;;
          contiguous_copy) set -- WEBP_METAL_LOSSY_CONTIGUOUS_COPY=1 ;;
          threads_128) set -- WEBP_METAL_LOSSY_THREADS=128 ;;
          threads_512) set -- WEBP_METAL_LOSSY_THREADS=512 ;;
          unretained_commands)
            set -- WEBP_METAL_LOSSY_UNRETAINED_COMMAND_BUFFERS=1 ;;
        esac
        env "$@" WEBP_METAL_LOSSY=1 WEBP_METAL_LOSSY_MIN_PIXELS=0 \
          "$encoder" -quiet -q "$quality" -m "$method" "$input" \
          -o "$temporary_dir/$name-lossy-$variant.webp"
        cmp "$temporary_dir/$name-lossy-cpu.webp" \
            "$temporary_dir/$name-lossy-$variant.webp"
      done
    fi
  done

  printf 'PASS: Metal correctness checks: %s\n' "$input"
done

if [ "$require_metal" = 1 ]; then
  grep -q "WebP-Metal: transformed" "$metal_log"
  grep -q "WebP-Metal: hash candidates" "$metal_log"
  grep -q "WebP-Metal: lossy RGB->YUV" "$metal_log"
  printf 'PASS: observed all forced Metal operations\n'
fi
