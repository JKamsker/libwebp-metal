# Pre-Ampere packed-pair I4 flatness rejection

Parent: `51bcb5c081c32fedb91884c30a7e0997dba54f39`

The clean Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. A fresh
file-I/O batch-24 profile measured exact PNG/JPEG medians of 29.846/27.615
ms/image, with aggregate hash/byte pairs `ace64e860de89b43` / 6,441,688 and
`1cbb84d2ab926db3` / 6,400,792. Excluding the first 24-image warmup batch,
the stage profile measured:

| Format | Total | Decimate/collect/replay | Token emit | Write | Import |
|---|---:|---:|---:|---:|---:|
| PNG | 27.123 ms | 18.912 ms | 3.017 ms | 1.701 ms | 1.388 ms |
| JPEG | 26.476 ms | 18.751 ms | 3.013 ms | 1.315 ms | 1.351 ms |

Realistic photo/texture blocks still spent about 63--65% of their block
cycles in I4. Root Nsight Compute collection was necessary because the host
sets `RmProfilingAdminOnly=1`; the denied non-root attempt is retained too.
On a representative 50-CTA decimate launch, source correlation assigned the
scalar I4 `CudaIsFlat` call 306,400 executed instructions and 221 samples.
This was the largest distinct non-barrier, non-residual source interval after
the residual cooperation, scan, handoff, and fixed-cost avenues had been
exhausted.

The single candidate kept Ampere+ on the retained scalar implementation. On
pre-Ampere it read the aligned 16-entry I4 level row as eight 32-bit pairs,
omitted DC, and counted the two exact nonzero 16-bit halves per iteration with
the unchanged early `score > 3` decision. The candidate reduced native
registers from 103 to 102; stack and static shared memory remained 352 and
23,392 bytes. It did not improve the measured kernel: the same representative
launch moved from 122.11 to 122.56 us, `No Eligible` moved from 89.79% to
89.88%, eligible warps/scheduler remained 0.12, and achieved occupancy
remained 26.04%. The retained and candidate profiled outputs had the identical
SHA-256 digest `33a12dd7db111a5d8c1ec8b872a9e951bf7edb643d54cbf702f92d5acc924480`.

Five order-balanced full-corpus process pairs per format, with one warmup and
three measured batches per arm, produced 30 exact rows per format:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 29.499 ms/image | 29.768 ms/image | -0.288 ms/image |
| JPEG | 27.770 ms/image | 27.561 ms/image | +0.234 ms/image |

All timing rows retained their reference hashes and byte counts. The
candidate passed 7/7 focused tests. CPU/CUDA hashes and byte counts were exact
for methods 2--6 and qualities 25/75/98 over the six graphic/photo/texture
17x13 and 257x255 fixtures. Twenty forced-fallback cells covered both formats,
collection bands 0/1/3/5/7, and inline/pipelined token recording; every cell
matched its CPU reference.

PNG regressed and the small JPEG change is far below the 1.5 ms/image gate,
so the candidate was removed. After every statically linked focused test was
rebuilt, the restored source passed 7/7 tests and matched the parent source
blob exactly. Do not retry packed-pair I4 flatness scanning without a new
critical-path profile. Pre-Ampere thresholds, Ampere+ defaults, architecture
dispatch, and the frozen publication corpus/generator are unchanged.
