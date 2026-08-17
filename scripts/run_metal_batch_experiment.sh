#!/bin/sh
set -eu

if [ "${WEBP_METAL_BATCH_EXPERIMENT:-}" != 1 ]; then
  echo "refusing run without WEBP_METAL_BATCH_EXPERIMENT=1" >&2
  exit 2
fi
if [ "${WEBP_BENCHMARK_SESSION:-}" != exclusive ]; then
  echo "refusing timed run without WEBP_BENCHMARK_SESSION=exclusive" >&2
  exit 2
fi

if [ "$#" -lt 2 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 BINARY OUTPUT_JSONL [WIDTH HEIGHT]" >&2
  exit 2
fi

binary=$1
output=$2
width=${3:-3000}
height=${4:-2000}
cold_repetitions=${WEBP_METAL_COLD_REPETITIONS:-5}
warm_iterations=${WEBP_METAL_WARM_ITERATIONS:-20}
batch_sizes=${WEBP_METAL_BATCH_SIZES:-"1 2 4 8"}
stage=${WEBP_METAL_EXPERIMENT_STAGE:-import}

if [ ! -x "$binary" ]; then
  echo "experiment binary is not executable: $binary" >&2
  exit 2
fi

: > "$output"
for batch_size in $batch_sizes; do
  for submission in single batch; do
    repetition=1
    while [ "$repetition" -le "$cold_repetitions" ]; do
      "$binary" --lifecycle=cold --submission="$submission" \
        --stage="$stage" --width="$width" --height="$height" \
        --batch-size="$batch_size" --iterations=1 >> "$output"
      repetition=$((repetition + 1))
    done
    "$binary" --lifecycle=warm --submission="$submission" \
      --stage="$stage" --width="$width" --height="$height" \
      --batch-size="$batch_size" --iterations="$warm_iterations" \
      >> "$output"
  done
done

printf 'wrote Metal experiment samples to %s\n' "$output"
