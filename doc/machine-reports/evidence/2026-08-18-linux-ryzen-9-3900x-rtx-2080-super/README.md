# RTX 2080 SUPER benchmark evidence

This directory contains the raw artifacts cited by the corresponding machine
report. `SHA256SUMS` covers every evidence file other than itself.

The JSON and JSONL files are direct benchmark outputs. The TSV files contain
the variant/format prefix followed by each benchmark's JSON output. The
`gprof-i4-diagonal-replay.tar.gz` archive contains the original `gprofng`
experiment directory. `gprof-current-token-profile.tar.gz` contains the later
retained-head texture-batch profile that attributed 60.10% of samples to
`VP8PutTokenPage` and 36.26% to `VP8RecordCoeffTokens`.

`chroma-i16-overlap-ab.jsonl` contains all 60 native-sm_75 A/B timing records
for the rejected scheduling candidate. The six
`retained-lossy-stage-*.jsonl` files contain the raw guarded wall-stage records
and batch-harness output: 24 warmup plus 72 measured encodes for each of
graphic, photo, and texture.

`i4-i16-chroma-overlap-ab.jsonl` contains the 60-record full composition
screen. `i4-chroma-overlap-ab.jsonl` contains both five-process blocks for the
lean composition (120 records total), including the borderline repeat used
for its decision.

`i4-chroma-token-fallthrough-screen.jsonl` contains the 24-record screen that
showed the CPU probability layout did not compose with the lean GPU candidate.

`i4-balanced-chroma-overlap-ab-block1.jsonl` and
`i4-balanced-chroma-overlap-ab-block2.jsonl` contain the two independent
60-record timing blocks for the rejected balanced-four-warp I4/chroma
composition. `i4-balanced-chroma-overlap-parity.jsonl` contains the 105
per-case CPU/CUDA and band-3 fallback SHA-256 comparisons; every row is exact.

`i4-team-barrier-chroma-screen.jsonl` contains the 24 exact timing rows for
the rejected team-local I4 barrier plus chroma-overlap composition.

`i4-boundary-static-commit-screen.jsonl` contains the 24 exact timing rows for
the rejected boundary-gather, static-dispatch, and parallel-commit composition.

`i4-warp-argmin-static-screen.jsonl` contains the 24 exact timing rows for the
rejected warp-argmin/static-dispatch/parallel-commit composition.
`retained-phase-refresh.txt` is the raw native-sm_75 phase trace used to select
that experiment.

`partition0-token-overlap-screen.jsonl` contains the 24 exact timing rows for
the rejected host-side schedule that generated VP8 partition 0 while all eight
token partitions emitted on worker threads. The `parent` rows set
`WEBP_PARTITION0_PIPELINE=0`; candidate and parent rows came from the same
native-sm_75 binary.

`i4-singleton-chroma-overlap-screen.jsonl` contains the 24 exact timing rows
for the rejected device schedule that moved the four chroma search stages
into the idle upper team on the four singleton I4 dependency diagonals.

`lossless-stage-profile.jsonl` contains the 126 raw encoder-stage rows used to
identify the remaining lossless CPU bottleneck. The three
`libwebp-backref-profile-20260819b-*.jsonl` files contain the 63 exact
back-reference substage rows. The 24
`libwebp-workspace-screen-d-*.jsonl` files contain the four order-balanced
parent/candidate process pairs for each of graphic, photo, and texture; each
file has eleven in-process encodes, with the first excluded from the screen.
The matching configure/build logs and `libwebp-*-CMakeCache.txt` files prove
both CUDA builds requested `CMAKE_CUDA_ARCHITECTURES=native` (sm_75 on this
host). `workspace-baseline-graphic.webp` and
`workspace-candidate-graphic.webp` are the sampled exact-output pair and are
byte-identical.

The `libwebp-parcache-screen-a-*.jsonl` files are the unconditional parallel
cache-search screen; `libwebp-parcache-gated-a-*.jsonl` contains the six-case
structurally gated screen. The `libwebp-parcache-final-a-*.txt` transcripts are
the four order-balanced final serial/default CUDA batch pairs for PNG and JPEG,
and `libwebp-parcache-final-cpu-*.txt` holds the matched four-process CPU
measurements. `libwebp-parcache-parity-sha256.txt` contains all 84 output hashes
from the 42-case byte-parity matrix. The associated CTest transcript, native
CMake cache, CUDA build log, and clean non-CUDA configure/build logs are stored
under the same prefix.

The `libwebp-post-parcache-v1-*.jsonl` files are the first exploratory
post-change stage pass on the 3000x2000 large cases. The
`libwebp-post-parcache-v2-*.jsonl` files correct the dimensions to the
historical 1600x1200 protocol; their run transcript is intentionally empty
because `cwebp` was quiet. The `libwebp-post-parcache-v3-*.jsonl` files repeat
the medium cases with `WEBP_CUDA_COLOR=1`, predictor, and hash explicitly
enabled. Its verbose transcript proves CUDA dispatch, including the resident
cross-color input handoff. Each pass has 21 rows per content case (one warmup
and 20 measured encodes), for 189 raw rows total. The matching stage CMake
cache records `CMAKE_CUDA_ARCHITECTURES=native` and the stage-profile build
option.

The 16 `libwebp-partrace-screen-*.txt` files are four order-balanced process
pairs for PNG and JPEG lossless batches. `off` set
`WEBP_CUDA_PARALLEL_TRACEBACK=0`; `candidate` set it to 1. Each transcript has
one discarded warmup plus three measured rows and preserves the invoked
command. Output hashes and byte counts match within each format. The tested
method-4 path does not request a no-cache candidate, so the proposed overlap
never dispatched and was removed.

The `libwebp-post-parcache-v4-*.jsonl` pass set the histogram runtime flag in a
build where `WEBP_CUDA_ENABLE_HISTOGRAM=OFF`; it is retained as explicit no-op
evidence. The `libwebp-post-parcache-v5-*.jsonl` pass used the rebuilt native
sm_75 profiler with the histogram accelerator compiled in, and its verbose run
transcript contains 504 `histogram counted` dispatch records. The matching
`libwebp-histogram-stage-CMakeCache.txt` records both the native architecture
and enabled histogram option.

The 24 `libwebp-histogram-turing-v6-*.jsonl` files are four order-balanced
runtime on/off pairs for each medium graphic, photo, and texture case. Each
contains one warmup and six measured encodes (168 rows total); the three quiet
run transcripts are empty by design. Together v4, v5, and v6 contain 294 raw
stage-profile rows.

The 16 `libwebp-cache-worker-reuse-*.txt` files are four order-balanced forced
batch pairs per PNG/JPEG format. `off` recreates cache-search workers per
search; `reuse` keeps them alive within a backward-reference call. Each
transcript contains one discarded warmup and three measured JSON rows plus the
invoked command. The removed candidate retained identical format-specific
hashes and byte counts.

The 16 `libwebp-parhist-screen-*.txt` files are four order-balanced forced
batch pairs for each PNG/JPEG format. `off` keeps raw-histogram cost analysis
serial; `parallel` splits at least 4,096 raw tiles into 12 CPU jobs before the
unchanged ordered compaction and clustering path. Each transcript contains one
discarded warmup and three measured rows. All hashes and byte counts match;
the candidate was removed after both format medians regressed.

`libwebp-post-parcache-gprofng-functions.txt` and
`libwebp-post-parcache-gprofng-calltree.txt` are the raw text reports from the
successful user-space sampling run that identified traceback and command append
as the next screen. The two `libwebp-cursor-inline-*-CMakeCache.txt` files
record the clean-parent and candidate native-sm_75 builds.

The 84 `libwebp-cursor-inline-*.txt` timing transcripts preserve five complete
screens: the unconditional CUDA prototype (16), its CPU-only control (16), and
three pre-Ampere isolation forms (16 each). Every CUDA transcript contains one
discarded warmup and three measured six-image rows; CPU controls contain one
warmup and two rows. Commands, hashes, byte counts, process order, and raw
nanosecond timings are included. All forms were removed after the CPU control
or architecture-safe JPEG cells regressed.

The 16 `libwebp-combined-entropy-avx2-*.txt` transcripts preserve two
order-balanced process pairs per format for both AVX2 screens. The unversioned
files vectorize every population alphabet; `v2` keeps fixed color/distance
alphabets scalar and vectorizes only the extended literal alphabet. Each file
contains its command, one discarded warmup, and three raw measured rows. Both
forms were byte-exact and were removed after failing the two-format gate.

The `libwebp-post-rejections-profile-*` and `libwebp-profile-lines-*` files
preserve the 60-sample `gprofng` collection commands, function and calltree
reports, annotated traceback/hash sources, and the Release-with-debug-lines
native-sm_75 CMake cache that directed the CUDA hash screen. The 24
`libwebp-hash-toggle-*.txt` timing transcripts contain two order-balanced
process pairs per PNG/JPEG format for 256-thread blocks, scalar matching, and
ordinary rather than `__ldg` loads. The three corresponding CMake caches prove
that only the named switch changed and every build requested
`CMAKE_CUDA_ARCHITECTURES=native`. Commands, raw nanosecond timings, hashes,
and byte counts are retained in each transcript.

The 20 `libwebp-hash-precheck-{png,jpeg}-*.txt` files preserve the five-process
gate for the rejected pre-Ampere initial-pixel-precheck removal. Each process
contains one discarded warmup and three measured rows. The matching baseline
and candidate CMake caches, exact candidate patch, seven-test transcript,
baseline/candidate `cuobjdump` resource reports, and candidate-kernel SASS are
stored with the same prefix. `libwebp-hash-ncu-permission.txt` is the raw
Nsight Compute attempt showing `ERR_NVGPUCTRPERM`; no system setting was
changed to bypass it.

The 20 `libwebp-hash-loadahead-{png,jpeg}-*.txt` files preserve the
five-process gate for the rejected pre-Ampere four-pixel load-ahead. The same
prefix includes the exact patch, native baseline/candidate caches, seven-test
transcript, resource reports, candidate and Ampere-baseline specialization
SASS, and normalized original/Ampere mnemonic streams. The normalized streams
are byte-identical, demonstrating that the architecture-specialized candidate
left the established Ampere+ instruction path unchanged.

The `libwebp-hash-combined-*` files preserve both ten-pair screens for the
rejected composition of precheck removal and four-pixel load-ahead. The
`final` transcripts are the decisive final-build repeat; PNG's paired median
gain fell below the retention threshold. The exact candidate patch, 90-case
method/quality/tiny/odd transcript, official candidate run, native cache,
resource report, SASS, normalized Ampere+ equivalence proof, and six copied
PPM inputs are included.

The `libwebp-resident-handoff-*` files preserve the independently retained
correctness fix. They include the original failing predictor/hash stage
combination probe, the exact patch, final 7-test and six-corpus public-encoder
transcripts, the default/baseline/all-disabled CUDA variant run, native cache,
system capture, and final official `raw.jsonl`, `results.json`, report, and run
transcript. The earlier parent and candidate failures under
`libwebp-hash-combined-test-cuda-*` demonstrate that the stale resident-pixel
bug predated the rejected matcher.

The `libwebp-lossy-retained-profile-*` files contain the current native-sm_75
stage records, summary, and direct per-phase device timing for medium graphic,
photo, and texture inputs. `libwebp-token-record-inline-*` preserves every raw
row from the five-pair PNG/JPEG recorder-pipeline recheck plus its computed
summary. `libwebp-static-i4-inline-*` preserves both order-reversed composite
screens, their summary, the exact rejected pre-Ampere patch, and parent and
candidate native CMake caches. Raw input-format controls were not promoted to
a performance claim; the report documents the invalid cross-format contrast.

The `libwebp-warp-helper-*` files preserve the rejected attempt to replace
sm_75 sync intrinsics after SASS inspection found 206 out-of-line warp-helper
calls. The complete compressed parent/candidate SASS, resource reports, native
CMake caches, 48 timing rows, computed summary, and legacy-intrinsic compiler
failure are included. The inline-PTX build retained all 206 calls, was slightly
slower, and changed both PNG and JPEG output. The clean-rebuild transcript
shows that the candidate cache produces the parent's exact bytes once the
source wrappers are removed, isolating the mismatch from the one differing
histogram build option.

Inspect the sampling archives with:

```sh
mkdir -p /tmp/libwebp-profile-check
tar -xzf gprof-i4-diagonal-replay.tar.gz -C /tmp/libwebp-profile-check
gprofng display text -functions \
  /tmp/libwebp-profile-check/libwebp-gprof-i4-diagonal-replay.er
tar -xzf gprof-current-token-profile.tar.gz -C /tmp/libwebp-profile-check
gprofng display text -functions \
  /tmp/libwebp-profile-check/current.er
```

Verify the copied artifacts from this directory with:

```sh
sha256sum -c SHA256SUMS
```
