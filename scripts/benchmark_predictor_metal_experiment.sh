#!/bin/sh
# Prepared measurement harness. Do not run as part of ordinary tests.
set -eu

if [ "${WEBP_METAL_PREDICTOR:-}" != 1 ]; then
  echo "refusing run without WEBP_METAL_PREDICTOR=1" >&2
  exit 2
fi
if [ "${WEBP_BENCHMARK_SESSION:-}" != exclusive ]; then
  echo "refusing timed run without WEBP_BENCHMARK_SESSION=exclusive" >&2
  exit 2
fi

usage() {
  echo "usage: $0 OUTPUT.csv INPUT [INPUT ...]" >&2
  exit 2
}

[ "$#" -ge 2 ] || usage
output=$1
shift
root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
encoder="$root_dir/examples/cwebp"
runs=${RUNS:-7}
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-predictor-bench.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

[ -x "$encoder" ] || {
  echo "build cwebp with WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 first" >&2
  exit 2
}

probe_input=$1
probe_output="$temporary_dir/probe.webp"
probe_log="$temporary_dir/probe.log"
if ! env WEBP_METAL=1 WEBP_METAL_MIN_PIXELS=999999999999 \
    WEBP_METAL_HASH=0 WEBP_METAL_VERBOSE=1 \
    WEBP_METAL_PREDICTOR=1 WEBP_METAL_PREDICTOR_MIN_PIXELS=0 \
    WEBP_METAL_PREDICTOR_VALIDATE=1 \
    "$encoder" -quiet -lossless -exact -m 4 "$probe_input" \
    -o "$probe_output" 2>"$probe_log" ||
   ! grep -q 'applied predictor residuals' "$probe_log"; then
  echo "predictor dispatch unavailable; rebuild with WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1" >&2
  exit 2
fi

printf 'input,method,run,variant,real_seconds\n' >"$output"

measure() {
  input=$1
  method=$2
  run=$3
  variant=$4
  timing="$temporary_dir/time.txt"
  if [ "$variant" = cpu ]; then
    /usr/bin/time -p -o "$timing" env WEBP_METAL=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" -o /dev/null
  else
    /usr/bin/time -p -o "$timing" env \
      WEBP_METAL_MIN_PIXELS=999999999999 WEBP_METAL_HASH=0 \
      WEBP_METAL_PREDICTOR=1 WEBP_METAL_PREDICTOR_MIN_PIXELS=0 \
      WEBP_METAL_PREDICTOR_VALIDATE=0 \
      "$encoder" -quiet -lossless -exact -m "$method" "$input" -o /dev/null
  fi
  seconds=$(awk '$1 == "real" { print $2 }' "$timing")
  escaped_input=$(printf '%s' "$input" | sed 's/"/""/g')
  printf '"%s",%s,%s,%s,%s\n' \
    "$escaped_input" "$method" "$run" "$variant" "$seconds" >>"$output"
}

for input do
  for method in 4 6; do
    run=1
    while [ "$run" -le "$runs" ]; do
      if [ $((run % 2)) -eq 1 ]; then
        measure "$input" "$method" "$run" cpu
        measure "$input" "$method" "$run" predictor_metal
      else
        measure "$input" "$method" "$run" predictor_metal
        measure "$input" "$method" "$run" cpu
      fi
      run=$((run + 1))
    done
  done
done

printf 'wrote %s\n' "$output"
