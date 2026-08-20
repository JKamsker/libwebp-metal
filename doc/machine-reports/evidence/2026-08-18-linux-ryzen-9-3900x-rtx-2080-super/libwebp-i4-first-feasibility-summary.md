# I4-first / I16-pruning feasibility screen

Parent: `c0fb63636f5469074686e60ba326bbd822afb0ac`

The retained Release build used `CMAKE_CUDA_ARCHITECTURES=native`. One warmup
and three measured batch-24 method-4/quality-75 file-I/O samples produced these
medians:

| Format | Median | Hash | Bytes |
|---|---:|---|---:|
| PNG | 36.389 ms/image | `455f70a1e139f043` | 6,441,688 |
| JPEG | 36.417 ms/image | `0c4b078d5c4d3173` | 6,400,792 |

The phase traces again put I4 at about 63--65% of realistic photo/texture
block cycles. Exact coverage of the retained medium fixtures reported:

| Content | I4 macroblocks | I16 macroblocks | I4 share |
|---|---:|---:|---:|
| Graphic | 191 | 7,309 | 2.55% |
| Photo | 4,101 | 3,399 | 54.68% |
| Texture | 7,500 | 0 | 100.00% |

This suggested evaluating I4 first and avoiding I16 for final I4 winners.
Source inspection rejected that schedule before implementation. The exact I4
raster search uses the completed I16 RD score as its early-abort threshold at
every committed block. Running I4 first would remove that bound and force
extra work on the graphic case, where 97.45% of macroblocks select I16. More
importantly, final mode coverage is not a proof that I16 can be skipped: the
current request contains no exact content discriminator or sufficiently strong
pre-quantization I16 lower bound. A segment/content heuristic would violate the
byte-exactness requirement.

No source candidate was opened. The experiment is a profile-led feasibility
rejection, not a performance or cross-hardware claim. The 784/12,544
pre-Ampere and 64/4,000 Ampere+ thresholds, the architecture split, and the
frozen publication corpus/generator are unchanged.

The retained source passed all seven registered focused tests. The first test
invocation found three registered CPU executables absent from the benchmark
cache; its diagnostic is preserved separately. Building those targets and
rerunning produced 7/7 passes.

Files:

- `libwebp-i4-first-feasibility-{png,jpeg}-bench.jsonl`: exact timing rows.
- `libwebp-i4-first-feasibility-{png,jpeg}-phases.txt`: raw device phase logs.
- `libwebp-i4-first-feasibility-coverage.jsonl`: exact fixture outcome counts.
- `libwebp-i4-first-feasibility-build.txt`: parent, native cache entry, binary
  hashes, and compressed-fixture hashes.
- `libwebp-i4-first-feasibility-incomplete-ctest.txt`: initial incomplete-cache
  diagnostic.
- `libwebp-i4-first-feasibility-retained-ctest.txt`: complete 7/7 retained-source
  guard.
