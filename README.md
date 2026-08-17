# WebP Codec

```
      __   __  ____  ____  ____
     /  \\/  \/  _ \/  _ )/  _ \
     \       /   __/  _  \   __/
      \__\__/\____/\_____/__/ ____  ___
            / _/ /    \    \ /  _ \/ _/
           /  \_/   / /   \ \   __/  \__
           \____/____/\_____/_____/____/v1.6.0
```

WebP codec is a library to encode and decode images in WebP format. This package
contains the library that can be used in other programs to add WebP support, as
well as the command line tools 'cwebp' and 'dwebp' to compress and decompress
images respectively.

## Metal acceleration

This fork adds optional Metal acceleration for lossless cross-color search,
lossless backward-reference candidate search, and opaque RGB/BGR to YUV420
conversion. It is based on current libwebp rather than the legacy libwebp 1.0.3
tree. See [METAL_MIGRATION_TASK.md](METAL_MIGRATION_TASK.md) for the migration
scope and maintenance strategy. Current CPU-versus-Metal measurements are in
[BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md). The private backend contract and
CUDA revival plan are in
[ACCELERATOR_BACKEND_DESIGN.md](ACCELERATOR_BACKEND_DESIGN.md). The reproducible
opt-in stage profiling protocol is in
[doc/encoder_stage_profiling.md](doc/encoder_stage_profiling.md).
The five-experiment interpretation, including deliberately rejected default
changes, is in
[doc/experiment-series-analysis-20260817.md](doc/experiment-series-analysis-20260817.md).

Project home: https://github.com/JKamsker/libwebp-metal

Metal is enabled by default in CMake builds on Apple platforms and can be
controlled explicitly with `-DWEBP_ENABLE_METAL=ON` or `OFF`. The simple Unix
makefile also enables it by default on macOS:

```sh
make -f makefile.unix -j8 ex
scripts/test_metal.sh /path/to/image.png [/path/to/another.jpg]
```

At runtime, `WEBP_METAL=0` disables lossless Metal acceleration,
`WEBP_METAL_HASH=0` disables hash candidate search, and
`WEBP_METAL_LOSSY=0` disables lossy import acceleration. The corresponding
`*_MIN_PIXELS` variables set crossover thresholds; setting them to `0` forces
the relevant path for correctness testing. `WEBP_METAL_VERBOSE=1` reports which
Metal operations were selected. `WEBP_ACCELERATOR=none` is a backend-neutral
CPU-only override; `auto` (the default) or `metal` selects the Metal descriptor.
Selected lossy imports use the exact 2x2 Metal kernel by default.

Additional encoder-stage research is documented in
[GPU_STAGE_EVALUATION.md](GPU_STAGE_EVALUATION.md). Its predictor-residual
prototype is excluded from normal builds and remains disabled at runtime unless
both experimental build and runtime flags are explicitly enabled.

See https://developers.google.com/speed/webp for details on the image format.

CI runner requirements, raw performance artifacts, and alert thresholds are
documented in [doc/ci-performance.md](doc/ci-performance.md). The monthly
upstream maintenance checklist is in
[doc/upstream-rebase.md](doc/upstream-rebase.md).

The latest source tree is available at
https://chromium.googlesource.com/webm/libwebp

It is released under the same license as the WebM project. See
https://www.webmproject.org/license/software/ or the "COPYING" file for details.
An additional intellectual property rights grant can be found in the file
PATENTS.

## Building

See the [building documentation](doc/building.md).

## Encoding and Decoding Tools

The examples/ directory contains tools to encode and decode images and
animations, view information about WebP images, and more. See the
[tools documentation](doc/tools.md).

## APIs

See the [APIs documentation](doc/api.md), and API usage examples in the
`examples/` directory.

## Bugs

Please report Metal integration and accelerator bugs in the
[libwebp-metal issue tracker](https://github.com/JKamsker/libwebp-metal/issues).
For bugs in upstream libwebp, use the WebP component of the
[issue tracker](https://issues.webmproject.org/issues/new?component=1618983&template=2023995).
For security reports, select 'Security report' from the Template dropdown.

Patches welcome! See [how to contribute](CONTRIBUTING.md).

## Discuss

Email: webp-discuss@webmproject.org

Web: https://groups.google.com/a/webmproject.org/group/webp-discuss
