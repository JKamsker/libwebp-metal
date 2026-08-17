#!/bin/sh
set -eu

if [ "${WEBP_METAL_PREDICTOR:-}" != 1 ]; then
  echo "set WEBP_METAL_PREDICTOR=1 for this guarded test" >&2
  exit 2
fi

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
encoder="$root_dir/examples/cwebp"
decoder="$root_dir/examples/dwebp"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-predictor-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

if [ ! -x "$encoder" ] || [ ! -x "$decoder" ]; then
  echo "build cwebp and dwebp with WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 first" >&2
  exit 2
fi

if [ "$#" -eq 0 ]; then
  set -- "$root_dir/examples/test_ref.ppm"
fi

# Disable the existing color-transform and hash accelerators so every byte
# comparison below isolates the predictor-residual experiment.
existing_accelerator_env="WEBP_METAL_MIN_PIXELS=999999999999 WEBP_METAL_HASH=0"

encode_experiment() {
  input=$1
  method=$2
  output=$3
  fail_after_dispatch=$4
  verbose=$5
  env $existing_accelerator_env \
    WEBP_METAL_VERBOSE="$verbose" \
    WEBP_METAL_PREDICTOR=1 \
    WEBP_METAL_PREDICTOR_MIN_PIXELS=0 \
    WEBP_METAL_PREDICTOR_VALIDATE=1 \
    WEBP_METAL_PREDICTOR_FAIL_AFTER_DISPATCH="$fail_after_dispatch" \
    "$encoder" -quiet -lossless -exact -m "$method" "$input" -o "$output"
}

for input do
  name=$(basename -- "$input")
  dispatch_seen=0
  for method in 0 1 2 3 4 5 6; do
    cpu="$temporary_dir/$name-m$method-cpu.webp"
    metal="$temporary_dir/$name-m$method-metal.webp"
    WEBP_METAL=0 "$encoder" -quiet -lossless -exact -m "$method" "$input" \
      -o "$cpu"

    # CPU reference validation occurs inside every successful experimental
    # dispatch. Repeat the full encode to check process-to-process determinism.
    repeat=1
    while [ "$repeat" -le 3 ]; do
      repeated="$temporary_dir/$name-m$method-metal-$repeat.webp"
      if [ "$repeat" -eq 1 ]; then
        dispatch_log="$temporary_dir/$name-m$method-dispatch.log"
        encode_experiment "$input" "$method" "$repeated" 0 1 \
          2>"$dispatch_log"
        if grep -q 'applied predictor residuals' "$dispatch_log"; then
          dispatch_seen=1
        fi
      else
        encode_experiment "$input" "$method" "$repeated" 0 0
      fi
      cmp "$cpu" "$repeated"
      if [ "$repeat" -eq 1 ]; then
        cp "$repeated" "$metal"
      else
        cmp "$metal" "$repeated"
      fi
      repeat=$((repeat + 1))
    done

    "$decoder" -quiet "$cpu" -pam -o "$temporary_dir/cpu.pam"
    "$decoder" -quiet "$metal" -pam -o "$temporary_dir/metal.pam"
    cmp "$temporary_dir/cpu.pam" "$temporary_dir/metal.pam"

    # The injected failure happens after a completed command but before the
    # result is committed to caller memory. The CPU fallback must still emit
    # the exact reference stream.
    fallback="$temporary_dir/$name-m$method-fallback.webp"
    encode_experiment "$input" "$method" "$fallback" 1 0
    cmp "$cpu" "$fallback"
  done

  if [ "$dispatch_seen" -ne 1 ]; then
    echo "predictor experiment was not selected for any method: $input" >&2
    exit 1
  fi

  printf 'PASS: predictor Metal experiment: %s\n' "$input"
done
