#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <metal-off-prefix> <metal-on-prefix>" >&2
  exit 2
fi

off_prefix=$(CDPATH= cd -- "$1" && pwd)
on_prefix=$(CDPATH= cd -- "$2" && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-abi.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

diff -ru "$off_prefix/include" "$on_prefix/include"

find_library() {
  find "$1" \( -name 'libwebp.dylib' -o -name 'libwebp.so' \) \
    -print | head -n 1
}

off_library=$(find_library "$off_prefix")
on_library=$(find_library "$on_prefix")
if [ -z "$off_library" ] || [ -z "$on_library" ]; then
  echo "installed shared libwebp not found in both prefixes" >&2
  exit 2
fi

exported_symbols() {
  case $(uname -s) in
    Darwin) nm -gUj "$1" ;;
    *) nm -D --defined-only "$1" | awk '{print $3}' ;;
  esac | LC_ALL=C sort -u
}

exported_symbols "$off_library" >"$temporary_dir/metal-off.symbols"
exported_symbols "$on_library" >"$temporary_dir/metal-on.symbols"
diff -u "$temporary_dir/metal-off.symbols" "$temporary_dir/metal-on.symbols"
printf 'PASS: installed headers and exported ABI match with Metal off/on\n'
