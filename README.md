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
scope and maintenance strategy. Historical CPU-versus-Metal measurements are
quarantined as recorded-only in
[BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md). The private backend contract and
CUDA revival plan are in
[ACCELERATOR_BACKEND_DESIGN.md](ACCELERATOR_BACKEND_DESIGN.md). The reproducible
opt-in stage profiling protocol is in
[doc/encoder_stage_profiling.md](doc/encoder_stage_profiling.md).
The five-experiment interpretation, including deliberately rejected default
changes, is in
[doc/experiment-series-analysis-20260817.md](doc/experiment-series-analysis-20260817.md).
The self-contained publication report, with the one-device/one-day boundary,
corpus-provenance audit, reproducibility notes, and unresolved blockers, is in
[doc/metal-research-report-20260817.md](doc/metal-research-report-20260817.md).
The claim-by-claim publication audit and the deterministic, redistributable
on-demand corpus are documented in
[doc/publication-evidence-audit-20260818.md](doc/publication-evidence-audit-20260818.md)
and [benchmarks/publication-corpus/README.md](benchmarks/publication-corpus/README.md).

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

## CUDA acceleration

CUDA acceleration for the lossless cross-color transform, lossless hash-chain
candidates, and opaque regular RGB-to-YUV420 conversion is available as an
opt-in CMake backend. It requires CMake 3.17 or newer and a CUDA toolkit, and is
enabled with
`-DWEBP_ENABLE_CUDA=ON`. The CUDA language is enabled only for this build mode;
CPU-only and Metal builds do not require the toolkit. For example:

```sh
cmake -S . -B build-cuda -DWEBP_ENABLE_CUDA=ON
cmake --build build-cuda -j
WEBP_TEST_BIN_DIR="$PWD/build-cuda" scripts/test_cuda.sh
```

The backend retains its device, private stream, events, and geometrically grown
staging buffers across encodes. Calls sharing those resources are serialized.
It copies results into caller buffers only after successful completion, so
initialization, allocation, launch, or device errors fall back to the CPU
without exposing partial output.

At runtime, `WEBP_ACCELERATOR=cuda` explicitly selects CUDA and
`WEBP_ACCELERATOR=none` forces the CPU path. `WEBP_CUDA=0` disables CUDA,
`WEBP_CUDA_DEVICE=N` selects a device, `WEBP_CUDA_MIN_PIXELS=N` controls the
lossless transform threshold, `WEBP_CUDA_HASH_MIN_PIXELS=N` controls hash
candidates, and `WEBP_CUDA_LOSSY_MIN_PIXELS=N` controls RGB conversion.
`WEBP_CUDA_COLOR=0`, `WEBP_CUDA_HASH=0`, and `WEBP_CUDA_LOSSY=0` disable one
stage. `WEBP_CUDA_VERBOSE=1` reports device and dispatch timings. Set a threshold
to zero for forced correctness tests. Defaults are adaptive: a stage pays the
roughly 140 ms runtime/device initialization cost only for large inputs, then
uses a lower warm-process threshold once another CUDA stage initialized the
backend: color uses 4,000,000 cold / 16,384 warm pixels, hash uses 8,000,000 /
4,000,000, and RGB uses 80,000,000 / 4,000,000. An explicit stage threshold
overrides both defaults.

Every CUDA stage and optimization has an independent `WEBP_CUDA_ENABLE_*`
CMake option. The default strategy uses persistent buffers, stream-ordered
copies, four-at-a-time hash matching, read-only hash loads, restrict-qualified
kernel pointers, packed four-byte RGB loads, 128-thread color/hash blocks, and
256-thread RGB blocks. Page-locked host staging, fused RGB 2x2 work, alternate
block widths, and stream-ordered allocation remain available for ablation but
are off by default on the measured RTX 2080 SUPER. Build the non-installed
`webp_cuda_benchmark` and concurrency runner with
`-DWEBP_BUILD_CUDA_BENCHMARK=ON`; `scripts/test_cuda_variants.sh` validates both
the default and all-strategies-disabled builds. Measurement details are in
[CUDA_BENCHMARK_RESULTS.md](CUDA_BENCHMARK_RESULTS.md).

Additional, non-installed CUDA strategy prototypes can be built with
`-DWEBP_BUILD_CUDA_ACCELERATION_EXPERIMENTS=ON`. See
[CUDA_ACCELERATION_EXPERIMENTS.md](CUDA_ACCELERATION_EXPERIMENTS.md) for the
correctness runner and raw-measurement protocol.

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
