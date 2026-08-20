# Opt-in NVDEC WebP transcoding

`webp_cuda_transcode` is a private benchmark/tool for opaque, lossy
WebP-to-WebP transcoding. It extracts a validated `VP8 ` payload, decodes it
to an NVDEC NV12 surface, and transfers the Y/U/V planes device-to-device into
the CUDA lossy analysis and decimation stages. It does not change libwebp's
public decoder API or its default build.

## Build

The tool and its NVIDIA dependency are both opt-in. CPU-only, Metal, and
ordinary CUDA builds do not locate or link the Video Codec SDK.

```sh
VIDEO_CODEC_SDK_ROOT=/path/to/Video_Codec_SDK cmake -S . -B build-nvdec \
  -DWEBP_ENABLE_CUDA=ON \
  -DWEBP_BUILD_CUDA_TRANSCODER=ON \
  -DWEBP_ENABLE_NVDEC=ON \
  -DWEBP_BUILD_LIBWEBPMUX=ON \
  -DCMAKE_CUDA_ARCHITECTURES=native
cmake --build build-nvdec --target webp_cuda_transcode
```

`nvcuvid.h` is found below `VIDEO_CODEC_SDK_ROOT` or
`NVIDIA_VIDEO_CODEC_SDK_ROOT`; the installed NVIDIA driver must provide
`libnvcuvid`. Configuration fails explicitly when NVDEC is requested but
either dependency is missing. NVDEC also requires the default
`WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS=ON`, because analysis-owned device planes
must remain valid until decimation consumes them.
`WEBP_BUILD_CUDA_TRANSCODER=ON` with `WEBP_ENABLE_NVDEC=OFF` still builds the
portable container-policy test and
has no NVIDIA Video Codec SDK dependency.

## Use and policy

```sh
build-nvdec/webp_cuda_transcode \
  --backend auto --device 0 --method 4 --quality 75 \
  --warmups 3 --samples 20 --verify input.webp output.webp
```

`--backend auto` and `--backend nvdec` try NVDEC for one complete, opaque,
lossy image. `--backend cpu` selects the reference CPU decoder. Every path
uses the normal CUDA-capable WebP encoder and its existing independent stage
fallbacks.

The NVDEC path accepts exactly one `VP8 ` image with matching RIFF, VP8X, and
VP8 key-frame dimensions. It declines `VP8L`, alpha, animation, multiple image
chunks, unsupported NVDEC geometry/capability, and any parser, decoder,
mapping, allocation, or handoff failure. A decline discards the entire
attempt and reruns the input through the CPU decoder; no partial NVDEC output
is committed. `WEBP_NVDEC_INJECT=parser|decoder|map|allocation|handoff`
provides stable failure injection for validation.

ICCP, EXIF, and XMP chunk payloads are copied byte-for-byte to the new lossy
container. Alpha inputs take the CPU RGBA path so alpha is re-encoded rather
than dropped. Malformed or truncated RIFF input fails without replacing an
existing destination. Output is written to a temporary sibling and renamed
only after the full transcode succeeds.

The mapped NV12 surface is split on the GPU. Before it is unmapped, the CUDA
encoder copies all three planes into backend-owned device memory and records
the exact host-placeholder identity. Both CUDA lossy analysis and CUDA lossy
decimation must consume that transaction; otherwise the tool discards the
attempt and performs a complete CPU retry. Decoder-owned pointers therefore
never outlive the mapped surface.

Each measured image emits one JSON object with the selected backend, decoded
format, stable decline reason, phase latency, images/s, output byte count,
NVDEC diagnostic status, and decoded-plane transfer accounting. Direct NVDEC
rows must report zero decoded H2D and D2H bytes. The D2D counter includes both
the decoder-to-analysis copy and the analysis-to-decimation-arena copy. On
Turing VP8 the optional
`cuvidGetDecodeStatus` query returns `CUDA_ERROR_NOT_SUPPORTED` (801); this is
recorded, while a successfully queried unconcealed decode error is rejected.
This matches the Video Codec SDK sample's diagnostic treatment of the query.

`--verify` builds a CPU-decoded reference with identical method and quality,
checks output dimensions, and requires at least 40 dB decoded-output PSNR.
The retained RTX 2080 SUPER corpus is stronger: NVDEC and CPU-reference WebP
outputs have identical SHA-256 and byte counts for graphic, photo, and texture
inputs.

## Performance interpretation

NVDEC decoder/parser creation dominates a cold one-image process on the RTX
2080 SUPER. Reusing the session removes that fixed cost and is the intended
throughput mode. Warm and cold numbers must therefore be reported separately;
the tool does not turn a warm batch result into a single-image latency claim.
The evidence and machine report record the exact native-sm_75 build and both
sets of measurements. No RTX 5070 Ti or cross-hardware claim is made without
measurements on that device.
