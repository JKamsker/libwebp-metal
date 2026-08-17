#!/bin/sh
set -eu

if [ "${WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT:-}" != 1 ]; then
  echo "set WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 for this guarded test" >&2
  exit 2
fi
if [ "${WEBP_BENCHMARK_SESSION:-}" != exclusive ]; then
  echo "stage profiling requires WEBP_BENCHMARK_SESSION=exclusive" >&2
  exit 2
fi

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
encoder="$root_dir/examples/cwebp"
input="$root_dir/examples/test_ref.ppm"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-stage-profile-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

if [ ! -x "$encoder" ]; then
  echo "build cwebp before running this test" >&2
  exit 2
fi

WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 \
  WEBP_STAGE_PROFILE_OUTPUT="$temporary_dir/cpu.jsonl" \
  WEBP_STAGE_PROFILE_RUN_ID=smoke \
  WEBP_STAGE_PROFILE_CASE_ID=test-ref \
  WEBP_STAGE_PROFILE_BACKEND=cpu \
  WEBP_STAGE_PROFILE_SAMPLE_SET=warm \
  WEBP_METAL=0 \
  "$encoder" -quiet -lossless -exact -m 4 -profile_repetitions 2 "$input"

python3 - "$temporary_dir/cpu.jsonl" <<'PY'
import json
import sys

rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
assert len(rows) == 2
assert [row["sample_role"] for row in rows] == ["warmup", "warm"]
assert all(row["ok"] and row["schema"] == "libwebp-encoder-stage-v1"
           for row in rows)
required = {
    "lossless_analyze", "lossless_predictor", "lossless_hash_chain",
    "lossless_backward_refs", "lossless_histogram", "lossless_huffman",
    "lossless_bitstream",
}
assert all(required <= set(row["stages"]) for row in rows)
PY

python3 "$root_dir/scripts/encoder_stage_profile.py" summarize \
  "$temporary_dir/cpu.jsonl" --output "$temporary_dir/baseline.json"
python3 - "$temporary_dir/baseline.json" <<'PY'
import json
import sys

baseline = json.load(open(sys.argv[1], encoding="utf-8"))
assert baseline["schema"] == "libwebp-encoder-stage-baseline-v1"
assert len(baseline["groups"]) == 1
assert baseline["groups"][0]["sample_role"] == "warm"
PY

WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 \
  WEBP_STAGE_PROFILE_OUTPUT="$temporary_dir/metal.jsonl" \
  WEBP_STAGE_PROFILE_RUN_ID=smoke \
  WEBP_STAGE_PROFILE_CASE_ID=test-ref \
  WEBP_STAGE_PROFILE_BACKEND=metal \
  WEBP_STAGE_PROFILE_SAMPLE_SET=cold \
  WEBP_METAL=1 WEBP_METAL_MIN_PIXELS=0 \
  WEBP_METAL_HASH=1 WEBP_METAL_HASH_MIN_PIXELS=0 \
  "$encoder" -quiet -lossless -exact -m 6 -profile_repetitions 1 "$input"

python3 - "$temporary_dir/metal.jsonl" <<'PY'
import json
import sys

record = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert record["ok"] and record["metal_cross_color"] and record["metal_hash"]
required = {
    "metal_init", "metal_cross_color_dispatch", "metal_hash_pipeline_init",
    "metal_hash_dispatch",
}
assert required <= set(record["stages"])
PY

echo "PASS: encoder stage profile schema, warm roles, summary, and Metal flags"
