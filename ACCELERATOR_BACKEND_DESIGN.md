# Encoder accelerator backend design

## Scope and evidence

This is the private interface between the current libwebp encoder and optional
compute backends. It is deliberately not a public WebP API and not a generic
GPU runtime. The first ABI describes only the three complete stages already in
this tree:

- `VP8LColorSpaceTransform()`: lossless cross-color transform search and
  application;
- the candidate-search half of `VP8LHashChainFill()`, with CPU replay of the
  left-extension and skip policy;
- the opaque, non-dithered, non-Sharp-YUV RGB/BGR to YUV420 import path in
  `ImportYUVAFromRGBA()`.

The local `15418-Final-Project` repository was reviewed at commit `b55ba547`.
Its final CUDA path installs a `VP8LColorSpaceTransform` function pointer,
allocates/frees device buffers on each call, synchronizes with device-to-host
copies, and aborts on CUDA errors. Commit `b8716e42` added a dummy launch to
hide roughly 70 ms of first-use cost. Commits `880100d5` and `33db2bfd`
disabled cross-tile histogram/neighbor dependencies and repaired barriers to
make independently scheduled tiles deterministic. Those algorithm decisions
remain relevant; the per-call allocation, global DSP override, bundled old CUB,
error-abort behavior, and whole-project CUDA language enablement do not.

The current Metal implementation already improves resource lifetime: its
device, command queues, pipelines, and capacity-rounded shared buffers persist
for the process, and mutexes serialize reuse. Before this change, however, the
three encoder call sites named Metal directly and the lossy and lossless files
had independent global state and environment parsing. The interface below
removes the encoder-to-Metal dependency without changing those kernel caches.

## ABI and capability discovery

`src/enc/accelerator_enc.h` defines ABI version 1. A backend returns one static,
immutable `WebPEncoderAccelerator` descriptor with:

- a name used by `WEBP_ACCELERATOR=auto|none|metal|cuda` selection;
- a stage bit mask;
- behavioral properties;
- an opaque backend-owned context;
- one typed callback per supported stage;
- optional `flush` and `trim` lifecycle hooks.

The required properties are synchronous completion and transactional outputs.
The current Metal descriptor additionally declares deterministic operation,
persistent resources, and serialized access. A descriptor that advertises a
stage without its typed callback is rejected as an accelerator error and the
CPU implementation remains the authority.

The built-in registry is compile-time, not a dynamic plugin ABI. Metal is added
under `WEBP_USE_METAL`. A CUDA port should add `WebPGetCUDAEncoderAccelerator()`
under `WEBP_USE_CUDA` to the same short registry. In automatic mode, a backend
that returns `NOT_RUN` permits the next backend to try the stage; an attempted
backend error goes directly to CPU fallback. An explicit, unknown backend name
selects none, which is safer than silently selecting a different accelerator.

The existing Metal controls remain compatible and are evaluated inside Metal:
`WEBP_METAL`, `WEBP_METAL_HASH`, `WEBP_METAL_LOSSY`, their minimum-pixel
thresholds, and `WEBP_METAL_VERBOSE`. `WEBP_ACCELERATOR=none` is the new common
kill switch; `WEBP_ACCELERATOR=metal` forces backend selection but does not
override a Metal stage-specific disable or threshold.

## Lifecycle and resource ownership

Backend descriptors have process lifetime. Backend initialization must be lazy
and thread-safe because libwebp has no global accelerator init/shutdown API and
the lossy import call occurs before either encoder object exists. A backend may
retain its device, compiled pipelines/modules, streams/queues, events, and
private staging buffers across encodes. It must not retain any pointer from a
request.

All request buffers are borrowed until the synchronous callback returns:

| Stage | Borrowed input | Mutable output committed only on success |
| --- | --- | --- |
| Lossless color transform | dimensions, transform bits, quality, original `argb` | transformed `argb`, tile `transform_image` |
| Lossless hash chain | `pixels`, CPU-built `chain`, search parameters | one packed candidate per pixel |
| RGB to YUV420 | packed-channel pointers, source step/stride, dimensions | caller-allocated Y/U/V planes and their strides |

Backends should upload into private buffers, run, validate device completion,
then copy to caller outputs. In-place or zero-copy execution is allowed only if
the backend can restore the original bytes after any failure; otherwise it
violates the transactional property. Backend allocations never become caller
owned and must use overflow-checked sizes.

There is no automatic destruction at process exit. The optional `trim` hook is
the future way to release capacity caches while keeping the descriptor usable.
The optional `flush` hook is a synchronization boundary for a future encoder
batch API. ABI v1 stage calls remain synchronous, so current Metal needs neither
hook. An asynchronous callback must not be added to ABI v1.

## Result, fallback, and synchronization contract

Every callback returns exactly one of:

| Result | Meaning | Output rule | Dispatcher action |
| --- | --- | --- | --- |
| `WEBP_ACCELERATOR_SUCCESS` | Stage finished and host can read its output | output is complete | caller consumes it |
| `WEBP_ACCELERATOR_NOT_RUN` | backend/stage unavailable, disabled, below threshold, or declined | output is byte-unchanged | try next backend, then CPU |
| `WEBP_ACCELERATOR_ERROR` | allocation, compilation, launch, device, or completion failure after attempting the stage | output is byte-unchanged | stop accelerator chain, run CPU |

Accelerator failure is recoverable because the public encoder has a complete
CPU implementation. CPU allocation or encoding failures continue to set the
normal `WebPPicture` error. Invalid input from a libwebp call site is a program
bug; backends still return `ERROR`/`NOT_RUN` rather than aborting. Device-lost
state should be quarantined by the backend so later calls decline cheaply.

Callbacks must be thread-safe. They return only after command completion and
host visibility. The current Metal backends use shared-storage buffers,
`waitUntilCompleted`, a completion-status check, then `memcpy`, all under a
mutex. A CUDA backend should use a private stream plus events or stream
synchronization, copy into host outputs only after success, and serialize any
shared staging allocation. Synchronizing the entire CUDA device is unnecessary.

Progress and cancellation remain in the CPU call sites. The GPU work is one
synchronous stage; after success the lossless call sites continue current
progress reporting and can propagate cancellation. A future chunked/asynchronous
ABI must make cancellation explicit rather than reading `WebPPicture` from a
backend thread.

## Determinism and stage semantics

`DETERMINISTIC` means repeated calls through one backend on the same device and
software stack produce identical stage outputs. It does not require the
lossless cross-color heuristic to choose the same transform as upstream CPU.
All successful WebP files must decode to identical pixels; stages documented as
CPU-equivalent (currently hash candidates and RGB-to-YUV) should also remain
byte-identical in focused tests.

The color transform keeps the deterministic independent-tile semantics ported
from CUDA: zero neighbor multipliers and no accumulated cross-tile histogram.
A revived CUDA kernel must match those current Metal semantics, including
quality-dependent search, signed-byte arithmetic, score tie behavior, tile
packing, and applying the chosen transform. It must not copy the older wrapper
that ran both CPU and CUDA or the older assertions that assumed a fixed tile
size.

Hash acceleration produces candidates only. The CPU retains construction of
the modern hash chain, progress/cancellation, left extension, and skip decisions.
This boundary avoids coupling kernels to mutable encoder policy. RGB-to-YUV is
eligible only after the caller has excluded alpha, Sharp-YUV, dithering, and
negative stride; output strides are explicit because WebP plane padding is not
part of the device result. The exact 2x2 Metal grid is the production
specialization selected after the item-4 ablation matrix.

New work such as predictor residual/final-transform or subtract-green/fused
transforms must receive a new stage bit and typed request only after its modern
CPU call-site semantics, ordering, and fallback transaction are defined. Do not
route unrelated kernels through the color-transform request.

## Persistence, batching, and instrumentation

Persistence is advertised explicitly so threshold policy can account for warm
pipelines and reused buffers. Backends should grow staging capacity
geometrically or in bounded pages, never shrink on the hot path, and serialize
reuse or maintain a small pool. The current Metal path rounds buffers and keeps
them for the process. A CUDA port should create its context/module/stream once
and reuse allocations rather than repeating the historical `cudaMalloc` and
`cudaFree` sequence.

Batch submission is intentionally a hook, not active behavior: no common
encoder session currently spans lossy import and both lossless stages without a
public-ABI change. `flush` supplies a future batch boundary and `trim` supplies
cache control. A later ABI can add begin/end batch tokens once a private encoder
owner exists; it must not key global state by `WebPPicture*`.

Metal's existing `WEBP_METAL_VERBOSE=1` reports selected device, thresholds,
stage dimensions, and elapsed command time. Future backends should provide the
same facts with the backend/stage name and distinguish declined, completed, and
error outcomes. Timing must use backend events where available and stay off by
default. A structured counter/timing snapshot can be added in a later ABI; it
should count attempts, declines, successes, errors, uploaded/downloaded bytes,
and device time per stage. The dispatcher must not add clocks or logging to the
default CPU path.

## Metal and CUDA integration

Metal now plugs in through `src/enc/metal_enc.c`. It adapts the descriptor's
typed requests to the two existing Objective-C++ implementations. Encoder C
files include only `accelerator_enc.h`; Objective-C/Metal types do not cross the
interface. The Metal implementation still owns two caches (lossless/hash and
lossy import). Consolidating them behind one shared device/queue allocator is a
safe follow-up, not required for backend neutrality.

A CUDA implementation should be introduced without reviving the old tree:

1. Add an opt-in `WEBP_ENABLE_CUDA` build choice and define `WEBP_USE_CUDA`
   only for supported toolchains; do not make CUDA a project-wide required
   language.
2. Implement one CUDA descriptor and private context with lazy device/module,
   stream/event, and staging-buffer creation. Use the CUDA toolkit's maintained
   CUB if needed rather than importing `src/cub` from the 2019 repository.
3. Port and validate one complete stage at a time, starting with lossless color
   transform because it has a direct historical algorithm and a current Metal
   oracle. Return `NOT_RUN` for unsupported devices/sizes and `ERROR` for failed
   attempted work; never `abort()`.
4. Add the descriptor to the compile-time registry and cover `auto`, `cuda`,
   `none`, no-device, forced-small-input, device-error, and concurrent encode
   cases.
5. Compare decoded pixels and stage output as required above before enabling a
   stage by default. Performance threshold work is separate from this design.

## Migration plan and compatibility risks

The first migration is implemented in this change: all three call sites use the
neutral dispatcher, Metal is an adapter, and CPU-only builds contain a cheap
empty registry. Remaining work and risks are:

- **Metal error classification:** the legacy Metal entry points return boolean,
  so their adapter currently maps every decline/failure to `NOT_RUN`. Change
  them to return the three-state result before relying on error telemetry or a
  second accelerator after Metal.
- **Environment is process-global:** like existing Metal controls,
  `WEBP_ACCELERATOR` is read during calls. Applications must not mutate
  environment variables concurrently. A future private per-encode preference
  needs an owner that does not alter `WebPConfig` or `WebPPicture` ABI.
- **Backend priority:** automatic mode follows compile-time registry order.
  Once Metal and CUDA coexist on one platform, choose and document a stable
  order or add measured capability ranking; never let it vary per call.
- **Global persistence:** cached resources intentionally survive until process
  exit. Embedders that need memory reclamation require a safe internal trim
  boundary before it can be exposed publicly.
- **Determinism is backend-scoped:** float/log implementation or kernel compiler
  changes can affect lossless transform choices. Keep tie-breaking tests and
  record backend/device/toolchain when diagnosing output drift.
- **Cancellation latency:** a single large synchronous dispatch cannot respond
  to progress-hook cancellation until it completes. Chunking is a new ABI and
  must preserve transactional fallback.
- **Integer limits:** request fields mirror current encoder `int` dimensions and
  stage arithmetic. Each backend must check multiplication and API-specific
  index limits before allocation/launch.
- **Public ABI:** all headers remain under `src/enc`; no symbols or fields are
  added to installed WebP headers. Do not expose backend handles until lifecycle
  and threading semantics can be supported as a public compatibility promise.

Focused fake-backend tests exercise empty-registry fallback, capability gating,
success, decline, error, missing callbacks, and output preservation by compliant
backends. Existing Metal correctness tests remain the integration coverage for
actual shader results and CPU fallback.
