# Modern libwebp Metal migration

## Objective

Rebase WebP-Metal's useful GPU acceleration work onto current upstream
libwebp while preserving upstream history and keeping the accelerator changes
as a small, maintainable patch stack.

The legacy repositories remain references:

- `../WebP-Metal`: working Metal implementation based on libwebp 1.0.3.
- `../15418-Final-Project`: original CUDA research implementation.

WebP-Metal is not imported as a separate library. Its accelerated stages use
private libwebp encoder data and must be integrated into the same build.

## Repository strategy

- Keep `upstream` pointed at `webmproject/libwebp`.
- Keep `main` as current upstream plus a short sequence of Metal commits.
- Port behavior semantically instead of replaying the legacy repository or
  blindly cherry-picking old CPU backports.
- Retain upstream CPU implementations as the fallback on unsupported systems,
  small inputs, disabled configurations, or recoverable Metal failures.

## Work breakdown

1. Add an opt-in/Apple-conditional Metal build option and Objective-C++ build
   plumbing.
2. Add cached Metal device, pipeline, queue, and shared-buffer management.
3. Port the lossless cross-color transform search to the current
   `VP8LColorSpaceTransform()` contract, including progress/cancellation and
   `best_bits` handling.
4. Port GPU hash-chain candidate search while retaining the CPU replay of
   left-extension and skip decisions.
5. Port opaque, non-dithered RGB/BGR to YUV420 conversion at the current
   `ImportYUVAFromRGBA()` integration point.
6. Add correctness and fallback tests.

Potential accelerator calls distinguish three outcomes:

- unavailable: run the existing CPU implementation;
- completed: use the accelerator result;
- error/cancelled: propagate the encoding failure where appropriate.

## Deliberately excluded from the migration

- Old vendored libwebp source and its deleted/trimmed build files.
- CPU optimizations already present or superseded upstream, including the
  trellis, NEON WHT, and histogram-copy changes.
- The legacy change that alters `cwebp` multithreading defaults.
- CUDA modernization. The CUDA tree is an algorithm reference for a later,
  separately scoped backend.

## Current phase acceptance criteria

- The modern tree configures and builds with Metal enabled on macOS.
- It also builds with Metal explicitly disabled.
- Existing relevant libwebp tests pass.
- Metal and CPU lossless encodes decode to identical pixels.
- Hash-chain and lossy conversion paths retain byte-identical output where the
  legacy implementation promises it.
- Disabled, unavailable, below-threshold, and recoverable Metal failures use
  the CPU path safely.
- CPU and Metal performance remain in the same ballpark as the legacy records,
  with same-machine comparisons used where the published hardware differs.

## Current implementation status

Completed in the initial modernization pass:

- current upstream libwebp history retained;
- CMake and `makefile.unix` Metal build plumbing added;
- lossless cross-color search adapted to current progress and `best_bits`
  handling;
- hash-chain candidates adapted to current storage and progress handling;
- opaque RGB/BGR conversion integrated at `ImportYUVAFromRGBA()`;
- CPU-only and Metal-enabled builds completed with `makefile.unix`;
- forced Metal-vs-CPU correctness tests passed for PNG and JPEG inputs,
  including hash methods 0 through 6 and three lossy configurations.

The current environment does not have CMake installed, so the CMake path is
implemented but still needs a configure/build validation when CMake is
available.

A subsequent requested benchmark pass measured cumulative lossless encoding,
isolated hash acceleration, and warmed lossy import. The results and comparison
with the legacy M4 Max records are in `BENCHMARK_RESULTS.md`. Complete lossless
and hash performance matched or improved on the legacy profile; same-machine
lossy measurements showed no migration regression.

## Later work

- Cold- and warm-start benchmarking and crossover threshold retuning.
- Optional backend-neutral organization for a modern CUDA implementation.
- Release branches/tags based on stable upstream libwebp releases.
