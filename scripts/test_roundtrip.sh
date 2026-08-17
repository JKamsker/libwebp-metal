#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
binary_dir=${WEBP_TEST_BIN_DIR:-"$root_dir/examples"}
encoder="$binary_dir/cwebp"
decoder="$binary_dir/dwebp"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-roundtrip.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

if [ ! -x "$encoder" ] || [ ! -x "$decoder" ]; then
  echo "cwebp and dwebp not found in $binary_dir" >&2
  exit 2
fi

input=${1:-"$root_dir/examples/test_ref.ppm"}
"$encoder" -quiet -lossless -exact "$input" -o "$temporary_dir/out.webp"
"$decoder" -quiet "$temporary_dir/out.webp" -pam -o "$temporary_dir/out.pam"

# Re-encode the decoded pixels to exercise both public command-line paths. A
# successful parse/decode plus a second lossless encode is a portable smoke
# gate; exact CPU-vs-Metal comparisons live in test_metal.sh.
"$encoder" -quiet -lossless -exact "$temporary_dir/out.pam" \
  -o "$temporary_dir/roundtrip.webp"
test -s "$temporary_dir/roundtrip.webp"
printf 'PASS: lossless round-trip smoke test: %s\n' "$input"
