#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <install-prefix>" >&2
  exit 2
fi

install_prefix=$(CDPATH= cd -- "$1" && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/libwebp-cmake-consumer.XXXXXX")
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

cat >"$temporary_dir/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.16)
project(libwebp_installed_consumer C)
find_package(WebP CONFIG REQUIRED)
add_executable(installed_consumer main.c)
target_link_libraries(installed_consumer PRIVATE WebP::webp)
EOF

cat >"$temporary_dir/main.c" <<'EOF'
#include <stdint.h>
#include <stdlib.h>

#include <webp/decode.h>
#include <webp/encode.h>

int main(void) {
  const uint8_t rgba[8] = {255, 0, 0, 255, 0, 255, 0, 255};
  uint8_t* encoded = NULL;
  int width = 0;
  int height = 0;
  const size_t encoded_size = WebPEncodeLosslessRGBA(rgba, 2, 1, 8, &encoded);
  const int ok = encoded_size != 0 && encoded != NULL &&
                 WebPGetInfo(encoded, encoded_size, &width, &height) &&
                 width == 2 && height == 1;
  WebPFree(encoded);
  return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
EOF

cmake -S "$temporary_dir" -B "$temporary_dir/build" -G Ninja \
  -DCMAKE_PREFIX_PATH="$install_prefix" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$temporary_dir/build" --parallel 2
"$temporary_dir/build/installed_consumer"
printf 'PASS: installed CMake package links and runs: %s\n' "$install_prefix"
