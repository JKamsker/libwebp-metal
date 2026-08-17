# Persistent and batched Metal encoding experiment

The fixed operator matrix is complete. Warm batch submission reduced isolated
import time, but full serial encode time showed no practical batch break-even.
The prototype therefore remains opt-in and private; see
[experiment-series-analysis-20260817.md](experiment-series-analysis-20260817.md)
for the stratified result and disposition.

This document records the engineering prototype for research item 3. No
performance measurements in this document were executed as part of the
prototype turn.

## Lifecycle findings

The migrated backend already has process-persistent resources, but there is no
encoder-owned accelerator context.

- `src/dsp/lossless_enc_metal.mm` initializes a process-global `MetalState`
  with `dispatch_once`. The color-transform library, pipeline, command queue,
  and shared buffers survive every later `WebPEncode()` call in the process.
  The hash library and pipeline compile lazily under the same operation mutex
  on the first eligible hash search.
- `src/enc/picture_csp_enc_metal.mm` has a separate function-static state. Its
  RGB-to-YUV library, pipeline, gamma tables, queue, and high-water-mark buffers
  survive later imports in the process. The pixel threshold is checked before
  initialization, so small default-path images do not pay compilation cost.
  Its C++ static owner releases Metal objects during normal process teardown;
  buffer growth also releases the superseded allocation.
- Each state has one mutex and one queue. Calls from multiple threads are safe
  but serialized while they copy input, encode a command buffer, wait, and copy
  output. Callers continue to own their `WebPPicture` and input storage.
- Every accelerated operation currently creates, commits, and synchronously
  waits for a command buffer. Lossless transform and hash results are consumed
  immediately by dependent CPU work, so combining independent full lossless
  encodes requires a split-phase encoder API. Opaque RGB-to-YUV conversion is
  independent and occurs before lossy encoding, making it the smallest legal
  batching boundary.
- The public `WebPEncode()` and convenience APIs have no context or batch
  parameter. Animation encoding invokes `WebPEncode()` for individual
  candidates and frames. It benefits from the global pipeline cache inside one
  process but cannot express image-level submission batching.
- Both singleton states are intentionally process-lived and retain their
  largest shared buffers. There is no encoder-scoped shutdown hook (and the
  lossless singleton still has only process lifetime). This is acceptable for
  the existing API but is not the ownership model proposed for a production
  backend-neutral context.

## Prototype

`WebPImportRGBToYUVAMetalBatch()` is a private experiment hook. It accepts an
array of backend-neutral RGB requests whose caller-owned Y/U/V planes are
already allocated. It:

1. validates every request and calculates overflow-checked, 256-byte-aligned
   offsets;
2. packs all sources and outputs into the existing reusable shared buffers;
3. records one dispatch per image into one compute encoder and one command
   buffer;
4. commits and waits once; and
5. copies results into caller planes only after all dispatches complete.

The hook is compiled only with `WEBP_BUILD_METAL_BATCH_EXPERIMENT=ON` (CMake)
or `WEBP_BUILD_METAL_BATCH_EXPERIMENT=1` (the Unix makefile), and additionally
requires `WEBP_METAL_BATCH_EXPERIMENT=1` at runtime. The experiment harness sets
no runtime flags itself: the caller must opt in explicitly. Normal builds do
not expose the batch symbol.

The mutex covers the entire batch, so concurrent behavior matches the old
single-operation serialization. A validation, allocation, pipeline, command,
or GPU failure returns zero before modifying any picture planes. The existing
`WebPImportRGBToYUVAMetal()` now delegates a one-element request to this
implementation after applying its unchanged threshold. Its caller still runs
the existing CPU conversion when zero is returned, so public single-image
behavior and fallback are unchanged.

Batch jobs deliberately bypass the one-shot pixel threshold. Batch owners know
the aggregate work and can make their own policy; the experiment harness forces
`WEBP_METAL_LOSSY_MIN_PIXELS=0`. The hook is declared only in the internal
`src/enc/metal_enc.h`, is not installed, and is not exported as stable ABI.

This prototype reduces N command-buffer commits and waits to one for the
batched RGB-to-YUV phase. It does not overlap CPU encoding with the GPU, merge
lossless commands, or eliminate the first runtime source compilation.

## Experiment harness and result schema

The non-installed `metal_encode_batch_experiment` target uses deterministic
synthetic RGB inputs. `--verify-only` compares CPU, batched Metal, and the
unchanged single Metal path at the final WebP bitstream. Normal experiment mode
emits one JSON object per sample:

| Field | Meaning |
|---|---|
| `schema` | `libwebp-metal-persistent-batch-v1` |
| `lifecycle` | `cold` includes first pipeline compilation/allocation; `warm` excludes one same-shape priming batch |
| `submission` | `single` commits once per image; `batch` commits once for the request array |
| `stage` | `import` measures RGB-to-YUV only; `encode` includes serial WebP encoding after import |
| `width`, `height` | pixels per image |
| `batch_size` | images in the measured workload |
| `iteration` | zero-based sample within the process |
| `elapsed_ns`, `ns_per_image` | monotonic host elapsed time and normalized value |
| `encoded_bytes` | aggregate output bytes for `encode`, zero for `import` |
| `metal_command_buffers` | one for `batch`, `batch_size` for `single`; failed Metal calls abort the sample |
| `warmup_batches` | zero for cold, one for warm |

Cold mode requires one iteration. Independent cold samples must use new
processes so the singleton pipeline is genuinely uninitialized. Warm mode
performs one unmeasured workload of the same shape, priming compilation and
buffer capacity before its measured iterations. Thus cold/warm lifecycle and
batch size are independent schema dimensions, rather than mixed averages.

Build and correctness smoke commands:

```sh
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_BUILD_METAL_BATCH_EXPERIMENT=1 \
  metal-experiment
WEBP_METAL_BATCH_EXPERIMENT=1 \
extras/metal_encode_batch_experiment --verify-only \
  --width=97 --height=65 --batch-size=3 --quality=75 --method=4
```

CMake provides the same opt-in target for a static build when CMake is
available:

```sh
cmake -S . -B build-metal-item3 -DWEBP_ENABLE_METAL=ON \
  -DWEBP_BUILD_METAL_BATCH_EXPERIMENT=ON -DBUILD_SHARED_LIBS=OFF
cmake --build build-metal-item3 -j8 --target metal_encode_batch_experiment
```

## Later benchmark release

Do not run these commands until the orchestrator releases serialized
benchmarking. The planned primary matrix compares batch sizes 1, 2, 4, and 8,
both submission modes, five independent cold processes, and twenty samples in
one warmed process:

```sh
WEBP_BENCHMARK_SESSION=exclusive \
WEBP_METAL_BATCH_EXPERIMENT=1 \
WEBP_METAL_BATCH_SIZES="1 2 4 8" \
WEBP_METAL_COLD_REPETITIONS=5 WEBP_METAL_WARM_ITERATIONS=20 \
scripts/run_metal_batch_experiment.sh \
  extras/metal_encode_batch_experiment item3-import-3000x2000.jsonl \
  3000 2000
```

Repeat the matrix for end-to-end lossy encoding by setting
`WEBP_METAL_EXPERIMENT_STAGE=encode`. Use the same quality 75/method 4 defaults,
AC power, and a fixed power mode. Record `sw_vers`,
`system_profiler SPHardwareDataType`, build flags, commit, ambient/thermal
conditions, and the order of runs next to the JSONL files. Run the two stages
serially, not concurrently with other GPU benchmark items.

At 3000x2000, the import matrix is expected to take roughly 1-3 minutes and the
full-encode matrix roughly 10-30 minutes, depending on the machine and thermal
state. The packed input, Metal source/output buffers, and allocated YUV planes
use approximately 9 bytes per pixel per batch member: about 432 MB at batch 8,
before encoder working memory and bitstreams. Reserve about 1 GB for the import
matrix and 2 GB for full encoding. Reduce the maximum batch size on constrained
machines rather than allowing swapping.

## Integration with the backend-neutral interface

Research item 6 subsequently introduced `src/enc/accelerator_enc.h`. The
integrated prototype uses its exact `WebPAcceleratorRGBToYUVRequest` buffer
shape rather than adding a `WebPPicture`-based Metal request. Descriptor ABI v1
remains synchronous and single-request; the batch function is a private,
Metal-only experiment and is not advertised in the v1 stage bits.

The durable design in `ACCELERATOR_BACKEND_DESIGN.md` keeps process-lifetime
backend descriptors for the current public encoder API, explicit capability
bits, synchronous borrowed buffers, and transactional output. Its reserved
`flush` and `trim` hooks provide lifecycle groundwork. Promoting this batch
experiment still requires an encoder-level batching boundary and a versioned
descriptor extension that Metal and a future CUDA backend can both implement.

## Readiness and blockers

Production-ready aspects are the unchanged single-image delegation, one-lock
serialization, overflow/shape validation, delayed picture mutation, CPU
fallback, deterministic shader, safe buffer replacement/process cleanup,
opt-in build, and correctness harness.

Experimental aspects are the internal request type, synthetic-only harness,
process singleton ownership, aggregate-threshold policy, retained batch-sized
buffers, synchronous wait, and lossy-import-only batching. Before promotion,
the benchmark release must establish break-even batch sizes; maximum Metal
buffer sizes and memory-pressure behavior need explicit limits; allocation and
GPU failure injection need tests; cancellation/progress semantics need design;
and item 6 must define scoped context ownership and cleanup. CMake validation is
also outstanding in the current environment because CMake is not installed.
