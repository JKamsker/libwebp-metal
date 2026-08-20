# Line-resolved decimate profile and static raster-commit screen

Date: 2026-08-20 UTC

Retained parent: `8c8cbd79140feffd992390c9b719d7dca9045360`

Hardware: AMD Ryzen 9 3900X / NVIDIA GeForce RTX 2080 SUPER (sm_75)

The profile-only build was configured as Release with
`-DCMAKE_CUDA_ARCHITECTURES=native -DCMAKE_CUDA_FLAGS=-lineinfo`.

## Profile command

```text
sudo -n ncu --target-processes all --kernel-name regex:DecimateKernel \
  --launch-skip 120 --launch-count 1 \
  --section SpeedOfLight --section Occupancy --section SchedulerStats \
  --section WarpStateStats --section MemoryWorkloadAnalysis \
  --section SourceCounters \
  --export /tmp/libwebp-next-current-decimate-lineinfo-ncu \
  --force-overwrite ./build-cuda-ncu/cwebp -m 4 -q 75 \
  -o /tmp/libwebp-next-current-decimate-lineinfo.webp \
  /tmp/libwebp-cuda-batch-corpus-20260818/png/photo-medium.png
```

The encoded output is 206,128 bytes with SHA-256
`33a12dd7db111a5d8c1ec8b872a9e951bf7edb643d54cbf702f92d5acc924480`.

## Source-counter result

The sampled 50-CTA by 256-thread `DecimateKernel` launch took 117.79 us.
It used 103 registers/thread and 23.39 KiB shared memory/CTA. Register and
shared-memory limits both allowed two CTAs/SM; theoretical occupancy was 50%
and achieved occupancy was 26.04%.

Schedulers had an average 2.08 active but only 0.12 eligible warps. No warp
was eligible in 89.34% of scheduler cycles, and CTA barriers accounted for
11.12 of 19.55 warp cycles per executed instruction (57.0%). DRAM throughput
was only 0.79%; L1/TEX and L2 hit rates were 93.89% and 86.89%.

Source counters attributed 334,803 of 846,791 shared wavefronts (40%) to
excess bank wavefronts. The largest sites mapped to the scalar 4x4 SSE and
Hadamard loads and basic quantization. Those exact areas were already covered
by rejected cooperative-metric, vector-row-I/O, eight-lane-quantization,
fused-register-handoff, shared-matrix, and uniform-AC experiments, so the
conflict total did not justify another layout variant.

The largest individual not-issued barrier attribution instead landed at the
raster-order I4 commit loop (901 samples), ahead of the transform/quantization
barrier at source line 1473 (770) and metric barrier at line 1497 (644).

## Candidate and screen

The one pre-Ampere candidate replaced `i4_ready[]` and `i4_next_commit` with
the exact static raster block ranges made ready by each of the ten dependency
diagonals. The Ampere+ branch retained the original readiness scan. The
candidate kept 103 registers and the 352-byte stack, while static shared
memory fell from 23,392 to 23,376 bytes.

The native-sm_75 candidate passed all seven focused CTests. Two order-reversed
process pairs per input format used batch 24, method 4, quality 75, one warmup,
three retained samples, forced CUDA, and file I/O. Pooled medians were:

| Format | Parent | Candidate | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 34.662 ms/image | 35.642 ms/image | -0.980 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 35.022 ms/image | 34.589 ms/image | 0.434 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

All 24 rows matched their format's hash and byte count. PNG regressed and the
JPEG gain was far below the 1.5 ms/image gate, so the candidate was removed.
The restored native build passed all seven focused CTests. No Ampere+ source
behavior, architecture threshold, frozen corpus file, or generator changed.

