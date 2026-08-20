# Pre-Ampere inverse-transform/SSE fusion rejection

Parent: `2b889a5b12608fe38ae27f5c0e412e6e792d95ac`

The retained Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. A fresh
file-I/O batch-24 profile measured exact medians of 29.574 ms/image PNG and
27.554 JPEG, with aggregate hash/byte pairs
`ace64e860de89b43` / 6,441,688 and
`1cbb84d2ab926db3` / 6,400,792. Excluding the first 24-image warmup batch,
the stage profile measured:

| Format | Total | Decimate/collect/replay | Token emit | Write |
|---|---:|---:|---:|---:|
| PNG | 26.790 ms | 18.859 ms | 3.052 ms | 1.610 ms |
| JPEG | 26.328 ms | 18.581 ms | 3.040 ms | 1.262 ms |

Device timing kept I4 at about 63--65% of photo/texture block cycles. The
retained metric-warp probe had measured 306.8 million residual, 209.0 million
SSE/flatness, and 139.5 million distortion cycles on photo. Residual scoring
is larger but its cooperation, scan, handoff, fixed-cost, and load paths are
exhausted, so the candidate targeted the distinct SSE walk.

On pre-Ampere devices, the candidate calculated four per-row SSE values in
the existing four inverse-transform lanes and reduced them within each mode's
four-lane subgroup. The later metric warp retained only flatness testing and
Ampere+ took the original scalar SSE path. This removed the later serial
16-pixel walk, but put its arithmetic and two shuffles on the inverse-transform
critical path. Native resources rose from 103 to 104 registers; the 352-byte
stack and 23,392-byte shared allocation were unchanged. Steady medium device
walls regressed for every content/format cell.

Five order-balanced full-corpus process pairs per format, with three measured
samples per arm, produced 30 exact rows per format:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 29.469 ms/image | 29.824 ms/image | -0.223 ms/image |
| JPEG | 27.704 ms/image | 28.113 ms/image | -0.274 ms/image |

The candidate passed all seven focused tests. Fifteen method/quality settings
(methods 2--6 and qualities 25/75/98) over six graphic/photo/texture 17x13
and 257x255 fixtures had exact CPU/CUDA aggregate hashes and byte counts.
Twenty PNG/JPEG fallback cells covered collection bands 0/1/3/5/7 with token
recording inline and pipelined; every CUDA hash/byte pair matched its CPU
reference.

Both formats regressed and the candidate was removed. The restored native
kernel returned to 103 registers / 23,392 shared bytes and passed 7/7 focused
tests after every statically linked executable was rebuilt. Architecture
thresholds/defaults, Ampere+ behavior, and the frozen publication corpus and
generator are unchanged.
