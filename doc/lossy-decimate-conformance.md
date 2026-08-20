# Portable lossy-decimate conformance

The private encoder accelerator ABI defines lossy decimation as one complete
macroblock rate-distortion operation. ABI version 12 and fixture schema version
1 are the current contract. The fixture format is independent of CUDA, FPGA,
Metal, pointer size, compiler layout, and host byte order.

## Boundary

An input request contains the visible Y/U/V 4:2:0 planes, image and macroblock
geometry, one segment ID per macroblock, all four quantizer/RD segment records,
the complete coefficient level-cost and probability tables, the RD search
level, I4 header limit, diffusion flag, and requested band count. The complete
pass starts with the encoder's fixed top/left border state. Later top/left
reconstruction, nonzero context, prediction context, and diffusion state are
produced by preceding macroblocks in the same anti-diagonal wavefront; they are
not host-precomputed inputs.

Successful output consists of one result record per macroblock and the padded
Y/U/V reconstruction planes. Each result names every coefficient, the packed
nonzero contexts, distortion and header terms, selected I16/I4/UV modes,
published chroma diffusion state, and the conditional `StoreMaxDelta` value.
Inactive I4 modes, reserved bytes, and compiler padding are canonical zero.

Only `WEBP_ACCELERATOR_SUCCESS` permits the caller to consume output.
`NOT_RUN` and `ERROR` leave all caller-owned output bytes unchanged so the CPU
path can run transactionally. CPU token recording, entropy coding, VP8 syntax,
and RIFF/WebP container assembly remain outside this boundary. Approximate
transforms and Tensor Core variants are not conforming implementations.

## WPDCRD schema version 1

Every integer is little-endian. Arrays use the ABI's documented logical order,
never a C struct dump. The payload is:

1. Eight-byte magic `WPDCRD1\n`, `u32` schema version, and `u32` accelerator
   ABI version.
2. `u32` flags (bit 0 is error diffusion), `u32` width, height, macroblock
   width and height, signed `u32` RD level and I4 header limit, `u32` band
   count, and one reserved zero `u32`.
3. Tightly packed visible Y, U, and V planes, followed by the macroblock
   segment IDs.
4. Four segment records. Each contains Y1, Y2, and UV quantizer matrices
   (`q`, `iq`, `bias`, `zthresh`, and `sharpen`) followed by all nine signed
   lambda/distortion values.
5. `4 * 8 * 3 * 68` `u16` level costs and `4 * 8 * 3 * 11` coefficient
   probabilities.
6. One 840-byte semantic result record per macroblock. Reserved and compiler
   padding bytes are omitted and restored as zero by the loader.
7. Tight padded reconstruction planes sized `mb_w*16` by `mb_h*16` for Y and
   `mb_w*8` by `mb_h*8` for each chroma plane.
8. An eight-byte FNV-1a payload checksum. Fixture manifests additionally carry
   SHA-256 hashes for fixtures, source images, and CPU-produced WebP files.

Readers reject unknown schema/ABI versions, checksum failures, invalid or
overflowing geometry, truncation, and trailing payload bytes. Writers use a
temporary file and rename so an incomplete capture is never published.

## Build and run

The harness is opt-in and contributes no fixture implementation to ordinary
CPU, Metal, CUDA, or Autotools libraries:

```sh
cmake -S . -B build-conformance -G Ninja \
  -DWEBP_BUILD_DECIMATE_CONFORMANCE=ON
cmake --build build-conformance --target cwebp lossy_decimate_conformance
ctest --test-dir build-conformance -R lossy_decimate_conformance
```

For CUDA, also use `-DWEBP_ENABLE_CUDA=ON` and an appropriate
`CMAKE_CUDA_ARCHITECTURES` value. Generate CPU-golden fixtures without changing
the frozen publication corpus or its generator:

```sh
python3 scripts/generate_lossy_decimate_fixtures.py \
  --cwebp build-conformance/cwebp --output-dir fixtures \
  --include-synthetic input.ppm
```

The default methods are 3 through 6 and qualities are 25, 75, and 98. Methods
0 through 2 do not all invoke this complete RD stage. `--include-synthetic`
adds a flat predictor tie case and a high-contrast coefficient/edge case.
Input paths may include tiny, odd-sized, graphic, photo, and texture cases.

Run whole-pass, banded, transport/fallback, and coverage checks with:

```sh
build-conformance/lossy_decimate_conformance --backend loopback fixtures/*.wpd
build-conformance/lossy_decimate_conformance --backend cuda fixtures/*.wpd
build-conformance/lossy_decimate_conformance \
  --backend cuda --streaming fixtures/*.wpd
build-conformance/lossy_decimate_conformance --coverage fixtures/*.wpd
build-conformance/lossy_decimate_conformance \
  --backend loopback --inject timeout fixtures/example.wpd
```

Coverage JSON reports segment and prediction-mode masks, I4/I16 and
zero/nonzero macroblocks, the union of packed nonzero contexts, signed
coefficient extrema, error-diffusion cases, banded passes, and partial edges.
Mismatch diagnostics identify the plane or result byte and the affected
macroblock's principal semantic fields.

## FPGA adapter and timing

`WEBP_ENABLE_FPGA_EXPERIMENTAL=ON` registers a dependency-free `fpga`
descriptor advertising the same logical stage. The skeleton returns
`NOT_RUN` without touching output. A future transport implementation stays
behind that descriptor; no vendor headers or runtime dependencies enter
normal builds.

Each runner row separates fixture transport/deserialization, the synchronous
accelerator callback, accelerator execution, result transfer, result compare,
CPU replay/tokenization, and total time. CUDA execution and result-transfer
values come from events bracketing the wavefront and downloads. A portable
backend that cannot expose those internal boundaries reports zero for the two
backend-private fields. CPU replay/tokenization is zero in this standalone
stage runner because it deliberately stops at the ABI boundary; end-to-end
encoder benchmarks must report that phase separately.
