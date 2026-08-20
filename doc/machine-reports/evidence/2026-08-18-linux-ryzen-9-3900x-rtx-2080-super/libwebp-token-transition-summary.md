# Boolean-coder transition-table rejection

Date: 2026-08-20 UTC

Parent: `735de11509a65cc223342dcb5bebc2f7e04af778`

Machine: Ryzen 9 3900X / RTX 2080 SUPER

All CUDA builds used `-DCMAKE_CUDA_ARCHITECTURES=native`.

## Profile selection

The retained batch-24 method-4/quality-75 file-I/O refresh produced exact
aggregate hashes and byte counts in all six measured rows:

| Format | Three retained rows (ms/image) | Hash / bytes |
|---|---|---|
| PNG | 34.226, 35.850, 35.983 | `455f70a1e139f043` / 6,441,688 |
| JPEG | 34.327, 35.256, 33.611 | `0c4b078d5c4d3173` / 6,400,792 |

The native stage build retained the last three groups after excluding its
24-image warmup:

| Format | total | encode loop | decimate | emit tokens | write | import |
|---|---:|---:|---:|---:|---:|---:|
| PNG | 28.266 | 24.793 | 18.655 | 3.868 | 2.059 | 1.356 |
| JPEG | 28.493 | 24.995 | 18.877 | 4.079 | 2.062 | 1.363 |

Decimation remained largest, but its leading I4 sites were already exhausted.
The largest distinct CPU cost was token emission. Whole-process `gprofng`
attributed 30.78% PNG / 30.95% JPEG exclusively to
`VP8RecordCoeffTokens`, with `VP8PutTokenPage` at 11.19% / 10.07%.
A separate line build reproduced 31.77% / 29.59% and 9.86% / 9.62%;
`gprofng display text -source/-disasm` crashed with RC 139 on this host, so
the failure transcripts are retained.

A sudo `perf record -e cycles:u -F999 --call-graph dwarf,16384` run collected
24K samples with zero loss. Across all eight emission workers it instead
placed `VP8PutTokenPage` at 35.41% of cycles, ahead of
`VP8RecordCoeffTokens` at 12.46%. Line-resolved annotation mapped the hot
serial chain to probability selection, split multiplication, the bit/range
decision, and normalization; buffer growth was not sampled.

A separate gcov build (no source edit) counted 292,171,248 page-coded tokens:

- dynamic probability lookup: 240,159,792 (82.20%);
- fixed probability: 52,011,456 (17.80%);
- bit one: 160,385,888 (54.89%);
- bit zero: 131,785,360 (45.11%);
- normalization: 156,736,192 (53.65%);
- no normalization: 135,435,056 (46.35%);
- buffer-growth fallback: 512 of 24,068,432 non-0xff byte flushes.

The balanced bit and normalization distributions ruled out another
common-branch specialization. The profile selected one coarse experiment
that precomputed the whole range/probability/bit transition.

As a control, fresh partition-count rows confirmed that the retained eight
token partitions remain optimal. Median batch-24 file-I/O results for
1/2/4/8 partitions were PNG 46.547/39.619/35.679/35.252 ms/image and JPEG
47.243/39.432/36.943/34.552. No partition default changed.

## Candidate and result

The candidate constructed a thread-safe 65,536-entry, 256-KiB transition
table once per process. Each 32-bit entry packed the exact value increment,
normalization shift, and next range. The page loop used one lookup instead of
the split multiply, bit/range branch, and two normalization-table lookups.
The generated function shrank from 764 to 708 bytes, while the binary gained
256 KiB of BSS. The focused bit-writer test passed.

Two order-balanced processes per format, each retaining three batch-24
file-I/O samples after one warmup, were exact in all 24 timing rows:

| Format | Parent | Candidate | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 35.380 ms/image | 35.117 ms/image | 0.263 ms/image | `455f70a1e139f043` / 6,441,688 |
| JPEG lossy | 34.541 ms/image | 35.848 ms/image | -1.308 ms/image | `0c4b078d5c4d3173` / 6,400,792 |

PNG was noise below the 1.5 ms/image gate and JPEG regressed materially.
The candidate was therefore removed before the broad correctness matrix.
The restored native tree passed all seven focused CTests. Do not retry a
dense whole-transition table on this CPU without a materially different
cache/data-layout profile.

Architecture-specific CUDA thresholds, Ampere+ behavior, and the frozen
publication corpus/generator were unchanged.

## Evidence map

- `libwebp-next-loop-retained-*`: retained end-to-end refresh.
- `libwebp-next-loop-stage-*`: retained stage profile.
- `libwebp-next-loop-parts*-*`: partition-count control.
- `libwebp-next-loop-token-profile-*` and
  `libwebp-token-transition-gprofng-profiles.tar.zst`: gprofng profiles.
- `libwebp-token-transition-perf-png.data.zst` and
  `libwebp-next-loop-token-perf-png-*`: raw perf data and reports.
- `libwebp-next-loop-token-gcov-png*`: branch-count profile.
- `libwebp-next-loop-token-transition.patch`: exact rejected patch.
- `libwebp-next-loop-transition-{png,jpeg}-*`: raw timing rows.
- `libwebp-next-loop-transition-{symbols,disassembly}-*`: generated-code
  comparison.
- `libwebp-next-loop-token-transition-restored-*`: restored build/tests.
