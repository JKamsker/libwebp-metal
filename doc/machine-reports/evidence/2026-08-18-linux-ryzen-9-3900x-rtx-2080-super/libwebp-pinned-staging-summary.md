# Pre-Ampere pinned decimate-staging screen

Parent: `98518b71c31218bd2041c820dac6da9f50b59bca`.

Machine: Ryzen 9 3900X / RTX 2080 SUPER. Every CUDA build in this
experiment was Release with `-DCMAKE_CUDA_ARCHITECTURES=native`.

## Profile selection

The refreshed encoder-stage medians over eight post-warmup batch-24 samples
were:

| Format | Total | Encode loop | Decimate | Emit tokens | Write | Import |
|---|---:|---:|---:|---:|---:|---:|
| PNG | 28.431 | 24.750 | 18.927 | 3.934 | 2.185 | 1.372 |
| JPEG | 27.945 | 24.701 | 18.666 | 3.806 | 1.831 | 1.367 |

Device phase timing kept I4 at about 63--65% of photo/texture block cycles,
but its leading residual, schedule, barrier, and layout paths were already
exhausted. The retained streaming backend instead exposed a distinct transfer
boundary: each of eight bands issued separate result, Y, U, and V downloads
to pageable staging, then copied the same bytes into encoder-owned outputs.

Seven warm streaming conformance iterations per content class measured:

| Fixture | GPU execution | Result transfer | Callback wall |
|---|---:|---:|---:|
| graphic medium | 21.393 ms | 1.536 ms | 22.459 ms |
| photo medium | 21.686 ms | 1.534 ms | 22.790 ms |
| texture medium | 20.778 ms | 1.534 ms | 21.861 ms |

All 24 conformance rows were exact. The thread-lifecycle control also counted
197 `clone3` calls per batch, consistent with the predecode worker plus one
recording worker and seven emit workers per image, but only 4.360 ms total
clone syscall time per 24 images. It did not justify a worker-lifecycle
candidate.

## Candidate and result

The one candidate used `cudaHostAlloc` staging only on pre-Ampere devices and
fell back transactionally to ordinary host allocation. Ampere+ retained the
existing allocator. An environment control compared pinned and pageable
staging in the same binary. Pinned staging reduced the device-event transfer
median from 1.529--1.547 ms to 0.732--0.733 ms, but callback wall improved by
only about 0.05--0.08 ms because transfers already overlap later diagonals and
the required staging-to-encoder copies remain.

One warmup and three measured batch-24 file-I/O samples per variant and format
produced:

| Format | Pageable parent | Pinned candidate | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 35.695 ms/image | 35.976 ms/image | -0.281 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 36.239 ms/image | 35.385 ms/image | 0.854 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

All 12 timing rows were exact. Candidate and restored builds passed all seven
focused CTests. The candidate was removed because PNG regressed and JPEG was
below the 1.5 ms/image gate. Architecture thresholds, Ampere+ behavior, and
the frozen publication corpus/generator were not changed.
