# Pre-Ampere I4 source-transform reuse rejection

Parent: `86c64e2fb9c6862f8a69f496b20fecab3329dbe1`

The clean Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. Fresh
file-I/O batch-24 medians were 29.536 ms/image PNG and 27.559 JPEG, with exact
aggregate hash/byte pairs `ace64e860de89b43` / 6,441,688 and
`1cbb84d2ab926db3` / 6,400,792.

The retained root Nsight Compute profile captured one representative 50-CTA
photo decimate launch at 121.89 us. It executed 3,879,409 instructions, spent
89.79% of scheduler cycles with no eligible warp, and achieved 26.04%
occupancy. Source correlation assigned 140,800 instructions to the four-lane
I4 forward-transform body. All ten modes transform the same source block, so
repeated source loads and horizontal arithmetic were a distinct remaining
transform cost after the residual and metric specializations were exhausted.

One pre-Ampere candidate computed the four exact source-side horizontal
numerator rows once per block in otherwise-idle prediction lanes. Each of the
ten mode groups computed only its reference-side terms, subtracted them from
the source numerators, and then applied the retained rounding constants and
vertical pass. The algebra preserved the original `src - ref` transform
exactly. Ampere+ compiled the retained transform path.

The candidate kept 103 registers and the 352-byte stack, but added 128 bytes
of static shared scratch (23,392 to 23,520 bytes). Nsight showed that the
extra publication/address arithmetic outweighed the removed repeated source
work: executed instructions rose by 16,800 to 3,896,209 and duration regressed
to 123.39 us. `No Eligible` moved to 89.86% and achieved occupancy stayed
26.04%. The retained and candidate profiled output SHA-256 digests both equal
`33a12dd7db111a5d8c1ec8b872a9e951bf7edb643d54cbf702f92d5acc924480`.

Five order-balanced full-corpus process pairs per format, with one warmup and
three measured batches per arm, produced 30 exact rows per format:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 29.209 ms/image | 29.490 ms/image | -0.244 ms/image |
| JPEG | 27.619 ms/image | 27.902 ms/image | -0.381 ms/image |

The candidate passed 7/7 focused tests. CPU/CUDA hashes and byte counts were
exact for methods 2--6 and qualities 25/75/98 over six graphic/photo/texture
17x13 and 257x255 fixtures. Twenty forced-fallback cells covered PNG/JPEG,
collection bands 0/1/3/5/7, and inline/pipelined token recording; every cell
matched its CPU reference.

Both formats regressed, so the candidate was removed. Every statically linked
focused executable was rebuilt; the restored source blob and native resources
match the parent exactly and 7/7 tests pass. Do not retry source-side I4
forward-transform reuse on Turing without a materially different register-only
handoff that avoids shared publication. Architecture thresholds, Ampere+
behavior, the pre-Ampere split, and the frozen publication corpus/generator
are unchanged.
