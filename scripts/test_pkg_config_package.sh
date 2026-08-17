#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <install-prefix>" >&2
  exit 2
fi

install_prefix=$(CDPATH= cd -- "$1" && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-pkg-consumer.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

cat >"$temporary_dir/main.c" <<'EOF'
#include <stdint.h>
#include <stdlib.h>

#include <webp/decode.h>
#include <webp/encode.h>

int main(void) {
  const uint8_t rgb[6] = {255, 0, 0, 0, 255, 0};
  uint8_t* encoded = NULL;
  int width = 0;
  int height = 0;
  const size_t size = WebPEncodeLosslessRGB(rgb, 2, 1, 6, &encoded);
  const int ok = size != 0 && WebPGetInfo(encoded, size, &width, &height) &&
                 width == 2 && height == 1;
  WebPFree(encoded);
  return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
EOF

PKG_CONFIG_PATH="$install_prefix/lib/pkgconfig" \
  cc -std=c99 -Wall -Wextra -Werror "$temporary_dir/main.c" \
    $(PKG_CONFIG_PATH="$install_prefix/lib/pkgconfig" \
      pkg-config --cflags --libs --static libwebp) \
    -o "$temporary_dir/installed_consumer"
"$temporary_dir/installed_consumer"
printf 'PASS: installed pkg-config package links and runs: %s\n' \
  "$install_prefix"
