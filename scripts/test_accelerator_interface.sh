#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-accelerator-test.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

cc -std=c99 -Wall -Wextra -Werror -DWEBP_ACCELERATOR_TESTING \
  -I"$repo_dir" \
  "$repo_dir/src/enc/accelerator_enc.c" \
  "$repo_dir/tests/accelerator_enc_test.c" \
  -o "$temporary_dir/accelerator_enc_test"

WEBP_ACCELERATOR=auto "$temporary_dir/accelerator_enc_test"
WEBP_ACCELERATOR=none "$temporary_dir/accelerator_enc_test"
