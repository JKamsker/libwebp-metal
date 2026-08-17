#!/bin/sh
set -eu

if [ "${WEBP_METAL_CROSSOVER_EXPERIMENT:-}" != "1" ]; then
  echo "refusing run: set WEBP_METAL_CROSSOVER_EXPERIMENT=1" >&2
  exit 2
fi
if [ "${WEBP_BENCHMARK_SESSION:-}" != "exclusive" ]; then
  echo "refusing timed run: set WEBP_BENCHMARK_SESSION=exclusive after release" >&2
  exit 2
fi

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
run_id=$(date -u +%Y%m%dT%H%M%SZ)
output_dir=${WEBP_METAL_OPERATOR_OUTPUT_DIR:-${TMPDIR:-/tmp}/libwebp-metal-crossover-$run_id}

cd "$root_dir"
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT=1 \
  CFLAGS='-O3 -DNDEBUG' CXXFLAGS='-O3 -DNDEBUG' \
  tools/webp_metal_benchmark examples/cwebp examples/dwebp

scripts/test_metal.sh
WEBP_METAL_CROSSOVER_EXPERIMENT=1 python3 scripts/benchmark_metal.py smoke \
  --runner tools/webp_metal_benchmark

exec python3 scripts/metal_crossover_operator.py run \
  --preset scripts/metal_crossover_focused_v1.json \
  --runner tools/webp_metal_benchmark \
  --output-dir "$output_dir" \
  --acknowledge-exclusive-session
