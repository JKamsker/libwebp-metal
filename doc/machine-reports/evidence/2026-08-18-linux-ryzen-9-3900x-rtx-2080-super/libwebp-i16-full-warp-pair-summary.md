# Pre-Ampere full-warp-paired I16 residual rejection

Parent: `36500ab759b3bb4239dbe0ada672614d99a64374`

The retained Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. A fresh
file-I/O batch-24 profile measured exact medians of 29.055 ms/image PNG and
27.629 JPEG, with aggregate hash/byte pairs
`ace64e860de89b43` / 6,441,688 and
`1cbb84d2ab926db3` / 6,400,792. Excluding the first warmup batch, the stage
profile measured:

| Format | Total | Decimate/collect/replay | Token emit | Write |
|---|---:|---:|---:|---:|
| PNG | 26.859 ms | 18.756 ms | 3.015 ms | 1.657 ms |
| JPEG | 26.400 ms | 18.665 ms | 2.974 ms | 1.305 ms |

Native device timing put I16 selection at 25.2% of graphic-medium block
cycles, versus 9.7% photo and 8.6% texture. The candidate used all eight
existing CTA warps as two full residual-cost warps per I16 mode. Each warp
handled eight AC blocks using incoming contexts derived exactly from the
already-complete non-zero bitmap. This avoided the masks and partial-warp
shuffle path of the earlier rejected half-warp experiment. The change was
uniformly gated to pre-Ampere devices; the Ampere+ arm retained the existing
four-warp mapping.

The candidate reduced the native kernel from 103 to 100 registers while
shared memory rose from 23,392 to 23,456 bytes; the 352-byte stack was
unchanged. A single exact medium PNG phase screen moved graphic/photo/texture
device wall from 25.88/26.27/20.55 ms to 20.83/20.99/19.91 ms, with identical
aggregate hash `26f02e79e7287adf` and 1,412,568 bytes.

Five order-balanced full-corpus process pairs per format, three measured
samples per arm, produced 30 exact rows per format:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 29.019 ms/image | 29.176 ms/image | 0.322 ms/image |
| JPEG | 27.523 ms/image | 27.262 ms/image | 0.340 ms/image |

The candidate also passed all seven registered focused tests. Fifteen
method/quality settings (methods 2--6 and qualities 25/75/98) over six
graphic/photo/texture 17x13 and 257x255 fixtures had exact CPU/CUDA aggregate
hashes and byte counts. Twenty PNG/JPEG fallback cells covered collection
bands 0/1/3/5/7 with token recording both inline and pipelined; every CUDA
hash/byte pair matched its CPU reference.

Both paired gains are far below the required 1.5 ms/image two-format gate,
and the PNG pooled median regressed. The candidate was removed. The final
retained native kernel returned to 103 registers / 23,392 shared bytes and
passed 7/7 focused tests. Architecture thresholds/defaults, Ampere+ behavior,
and the frozen publication corpus/generator are unchanged.
