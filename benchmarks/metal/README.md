# Metal optimization ablations

This directory separates the recorded migration baseline from optimization
experiments. No optimization in this patch is enabled by default, and no
performance result is claimed until the reserved benchmark session runs.

`recorded_baseline.tsv` transcribes the aggregate M4 Pro results from
`BENCHMARK_RESULTS.md`. The original raw per-trial measurements were not stored,
so the table must not be treated as raw data. The new harness writes every timed
sample to `raw_results.jsonl`, plus a complete `metadata.json`, the exact
`matrix.json`, and a mechanical `summary.json`.

## Prepared variants

| Suite | Variant | Single delta |
|---|---|---|
| transform | `dispatch_2d` | Native 2D tile dispatch avoids tile-index division/modulo. |
| transform | `threads_128`, `threads_512` | Change only transform threadgroup size from 256. |
| transform | `unretained_commands` | Use a command buffer without retained resource references. |
| hash | `match4` | Unroll match comparisons four pixels at a time. |
| hash | `write_combined_inputs` | Allocate upload-only pixel/chain buffers with write-combined CPU caching. |
| hash | `threads_128`, `threads_512` | Change only hash threadgroup size from 256. |
| hash | `unretained_commands` | Use a command buffer without retained resource references. |
| lossy | `block_2x2` | One thread reuses four RGB loads for four Y samples and one U/V sample. |
| lossy | `write_combined_inputs` | Allocate the RGB upload buffer with write-combined CPU caching. |
| lossy | `contiguous_copy` | Use one output copy when the allocated Y/U/V planes are contiguous. |
| lossy | `threads_128`, `threads_512` | Change only lossy threadgroup size from 256. |
| lossy | `unretained_commands` | Use a command buffer without retained resource references. |

Function constants specialize the alternate kernels, so disabled branches are
not paid by the GPU. Every pair explicitly resets all unrelated flags, alternates
baseline/candidate order by trial, and checks that lossless outputs remain byte
identical. The separate correctness script covers decoded transform equality and
byte-identical hash/lossy output.

## Benchmark release commands

Build before taking the exclusive benchmark lease:

```sh
make -f makefile.unix -j8 examples/cwebp examples/dwebp \
  WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1 metal-ablation-tools
```

Prepare metadata and inspect the matrix without timing anything:

```sh
python3 scripts/benchmark_metal_ablation.py \
  --output /tmp/libwebp-metal-preflight
```

After item 1 supplies the canonical corpus paths and the Terra/Luna benchmark
lease is granted, run the full matrix:

```sh
WEBP_BENCHMARK_SESSION=exclusive \
WEBP_METAL_ABLATION_EXPERIMENT=1 \
python3 scripts/benchmark_metal_ablation.py --run \
  --output /absolute/path/to/results \
  --input mitski=/absolute/path/to/mitski.png \
  --input corgi=/absolute/path/to/corgi.jpeg \
  --input siamese=/absolute/path/to/siamese.jpg
```

Suites can be reserved separately with `--suite recorded`, `--suite transform`,
`--suite hash`, or `--suite lossy`. Defaults are seven one-shot trials at methods
4 and 6, and three warmed import processes (50 samples at 6 MP, 30 at 12 MP).
On the recorded M4 Pro timings, allow roughly 20-30 minutes for the full matrix,
one CPU core for the host encoder, the integrated GPU, and about 1 GB of peak
working storage; the harness itself retains only small JSON files and temporary
outputs.

## Deferred interface-dependent work

The current encoder passes ordinary malloc-owned pointers into synchronous Metal
entry points. True zero-copy input/output requires page-aligned storage whose
lifetime is visible to Metal. Keeping transformed pixels resident for the later
hash stage additionally requires an explicit generation/ownership token because
intermediate encoder work may reuse the cached buffer. Those candidates require
a future version of the neutral interface in `src/enc/accelerator_enc.h` and
are not represented by unsafe pointer-identity heuristics here. Likewise,
command fusion or asynchronous completion cannot be correct without changing
its synchronous caller contract.
