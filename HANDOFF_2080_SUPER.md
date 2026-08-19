# Handoff: continuing CUDA work on the RTX 2080 SUPER machine

Written 2026-08-19 at the end of the RTX 5070 Ti session. Branch:
`codex/cuda-encoder-acceleration`, tip `4f9235ee`, CI green for every
commit on the branch.

## Where the work stands

This fork accelerates libwebp encoding (Metal ~2x on Mac; this branch is
the CUDA/Windows counterpart). On the 5070 Ti Laptop GPU, forced 24-image
batches measured with the official suite:

| Method | speedup | ms/image (CUDA / CPU) |
|---|---:|---:|
| PNG lossy — batch | 3.77x | 43.6 / 164.4 |
| JPEG lossy — batch | 3.52x | 49.2 / 173.2 |
| PNG lossless — batch | 1.98x | 83.8 / 165.7 |
| JPEG lossless — batch | 4.69x | 153.5 / 719.4 |
| PNG / JPEG near-lossless — batch | 2.59x / 5.71x | |
| PNG / JPEG lossy — single (fresh process) | 1.03x / 1.05x | first time above parity |

Every lossy output is byte-identical to this fork's CPU encoder; lossless
modes promise decoded-pixel parity where the GPU search differs. The
stage-by-stage progression (0.95x → 3.77x) and full prose history are in
`CUDA_BENCHMARK_RESULTS.md` ("Windows RTX 5070 Ti Laptop results");
accepted/rejected experiments with numbers are in
`CUDA_EXPERIMENT_SUMMARY.md`.

How the lossy pipeline works now, in one paragraph: a byte-exact CUDA
port of VP8Decimate runs whole passes in skewed anti-diagonal wavefront
order (t = x + 2y), streamed in 8 bands (ABI v10 BEGIN/COLLECT) so the
CPU replays and a worker thread records tokens for band k while the GPU
still computes band k+1; token streams default to eight standard VP8
partitions whose final arithmetic coding runs on parallel worker
threads (CPU and CUDA encodes alike); a background prewarm at process
start hides most driver context creation. Fork-level semantic changes,
each with an env restore: no mid-pass probability refresh
(`WEBP_TOKEN_REFRESH_SHIFT` restores upstream and declines acceleration),
8 token partitions (`WEBP_TOKEN_PARTITIONS=0`), cwebp fast exit
(`WEBP_NO_FAST_EXIT=1`), pipelined recording
(`WEBP_TOKEN_RECORD_PIPELINE=0`), threaded emission
(`WEBP_TOKEN_EMIT_THREADS=0`).

The current bottleneck picture on the 5070 Ti: the GPU wavefront wall is
~27.7 ms for a 100x75-MB image and the CPU-side serial chain (analysis
~11 ms, collect+replay, import ~4 ms) is about the same — a balanced
crossover. Further batch gains must shrink both sides. The i4 phase is
~60% of the GPU wall and dependency-bound (per-step cost measured ~9k
cycles where ~4k is accounted for — suspect barrier skew and shared-mem
latency). Measured-neutral ideas (do not redo blind): shared-memory cost
tables, GPU lossy analysis (tested three times), `thread_level=1`
default, warp-cooperative i4 residual walk. Key CUDA lesson from this
round: divergent branches inside one warp serialize — extra parallelism
must be warp-aligned.

## Cautions

- **Never modify the frozen files** `scripts/generate_publication_corpus.py`
  and `benchmarks/publication-corpus/manifest.json` — CI pins their raw
  bytes (LF, enforced via `.gitattributes`).
- Thresholds and defaults were tuned on the 5070 Ti (sm_120). The 2080
  SUPER is Turing (sm_75) with different SM count, clocks, and an older
  measured init cost (~140 ms, CUDA 12.0 at the time). The historical
  2080 SUPER rows at the top of `CUDA_BENCHMARK_RESULTS.md` predate
  every stage on this branch — they are not comparable evidence.
- `CMAKE_CUDA_ARCHITECTURES=native` is the default; a fresh build dir on
  the 2080 machine picks sm_75 automatically.
- Every perf change must keep CPU-vs-CUDA byte parity (lossy) and pass
  the verify-only gates; fault-inject the fallback path when touching
  the streaming/recording machinery.

## Task list for this machine

**Complete this list first, in order, before entering the endless
optimization loop below.** Tick each box as it lands; 1–5 are the
cross-hardware validation this machine exists for, and the loop's
measurements are meaningless until they pass.

- [x] 1. **Build and gate.** Fresh build dir, `-DWEBP_ENABLE_CUDA=ON
  -DWEBP_BUILD_CUDA_BENCHMARK=ON -DWEBP_BUILD_CWEBP=ON
  -DWEBP_BUILD_DWEBP=ON`; build `cwebp dwebp webp_cuda_batch_benchmark
  cuda_concurrency_test cuda_near_lossless_test cuda_histogram_test`.
  Run the three tests. Then byte-parity spot checks (CPU vs
  `WEBP_ACCELERATOR=cuda` cwebp, `-q 25/75/90/98 -m 2..6`, photo /
  graphic / texture, tiny and odd dimensions) and the six verify-only
  batch matrices (`--verify-only`, lossy/lossless/near-lossless x
  png/jpeg).
- [x] 2. **Exercise the fallback path on this GPU:**
  `WEBP_CUDA_DECIMATE_FAIL_COLLECT=<band>` for bands 0/1/3/5/7, pipeline
  on and off — outputs must stay byte-identical to CPU.
- [x] 3. **Run the official suite** and file a new result set:
  `python scripts/benchmark_cuda_end_to_end.py run --build-dir
  <build>/Release --output-dir <temp>/libwebp-cuda-results-2080super
  --label "win-2080super"`. Compare against the 5070 Ti sets with the
  `report` subcommand (the 5070 Ti machine has
  `libwebp-cuda-results-win{...,-trim}` under its temp dir; results.json
  files are portable — copy them over or re-derive from the table in
  `CUDA_BENCHMARK_RESULTS.md`). Add a cross-hardware section to that
  file with whatever this GPU shows.
- [x] 4. **Measure the GPU wall here:** `WEBP_CUDA_DECIMATE_TIMING=1`
  (per-pass device wall) and `=2` (per-phase cycle percentages) on
  photo/graphic/texture-medium. On the 5070 Ti: ~27.7 ms wall, i4 ~60%,
  import ~12%, i16-sel ~6%. If Turing shifts the phase mix, the tuning
  priorities shift with it. Also A/B 4 vs 8 bands
  (`pass->band_count` in `frame_enc.c` / backend `kMaxDecimateBands`) —
  the 8-band choice was tuned on the 5070 Ti.
- [x] 5. **Re-check dispatch thresholds on Turing.** Warm/cold gates
  (`WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS` 64 warm / 4000 cold,
  `WEBP_CUDA_MIN_PIXELS`, predictor and NL thresholds) were never
  validated on this hardware. If forced CUDA loses to CPU on some mode
  here, the fix is threshold calibration, not code.
- [ ] 6. **Nsight Compute deep-dive on the i4 phase** if Nsight is
  available on this machine (it wasn't used on the laptop). Target:
  explain the ~9k cycles/step in the 16-step i4 chain in `DecimateKernel`
  (`src/enc/cuda_decimate_enc.cu`), then attack the largest component.
  This is the main unexplored GPU-side lever.
- [ ] 7. **CPU-side analyze (~11 ms/image)** — largest remaining serial
  CPU chunk. GPU analysis measured neutral three times as-built; a leaner
  fused variant, or overlapping analysis of image N+1 with the encode of
  image N inside the batch tool, are the unexplored angles.
- [ ] 8. **Multi-image GPU overlap** (design task): batch callers could
  hide the entire GPU wall by decimating image N+1 while tokenizing image
  N, but that changes the synchronous encode-call contract — needs an
  explicit async batch API sketch before any code.
- [ ] 9. **Trellis (m5/m6) decimate support** — currently declines to
  CPU; methods 5+ add trellis quantization to the search.
- [ ] 10. **Merge decision:** the branch is many CI-green commits ahead
  of main and self-contained. Consider a PR to main once cross-hardware
  numbers from this machine are in.

## Goal: the endless lossy optimization loop

Once every box above is ticked, switch to this standing goal and run it
indefinitely:

> Improve PNG→WebP lossy and JPG→WebP lossy end-to-end performance in a
> loop: profile the e2e conversion → pick the largest addressable cost →
> optimize (tune an existing CUDA kernel, introduce a new one, or shrink
> the CPU-side serial chain — whichever the profile points at) →
> re-measure → better? keep, document, commit, push, watch CI — worse or
> neutral? revert, and record the negative result so it is never retried
> blind.

Rules that make the loop trustworthy (all learned the hard way on the
5070 Ti — do not relax them):

1. **Profile before touching anything.** Use, in this order of
   granularity: the batch benchmark medians → `WEBP_CUDA_DECIMATE_TIMING=1/2`
   (device wall + kernel phase mix) → the opt-in CPU stage profiler →
   Nsight. Only optimize what the current profile says is largest;
   remember the batch is near a balanced GPU/CPU crossover, so a win on
   one side may not move the total.
2. **Every kept change is byte-exact.** CPU-vs-CUDA `cmp` across content
   classes, qualities 25–98 (98 exercises error diffusion), methods 2–6,
   tiny/odd dimensions — plus the fault-injected fallback when touching
   streaming/recording. Deliberate bitstream changes (like the token
   partitions were) must apply to CPU and CUDA identically, decode
   identically, and carry an env restore.
3. **Measure with the tools, not by eye.** Batch tool with
   `--warmups 1 --samples 3` for iteration; the full suite for any number
   that gets written down. Deltas under ~1.5 ms/image are noise — rerun
   before believing them.
4. **Keep or kill, never keep-and-wonder.** A neutral result is a kill:
   revert the code, keep one ledger row in `CUDA_EXPERIMENT_SUMMARY.md`
   saying what was tried, the numbers, and why it stays out. Wins get a
   ledger row, a `CUDA_BENCHMARK_RESULTS.md` update, a conventional
   commit, a push, and a CI check (never assume green).
5. **Already-known-neutral on the 5070 Ti** (retest on Turing only with a
   reason): shared-memory cost tables, GPU lossy analysis (3x),
   `thread_level=1` default, warp-cooperative i4 residual walk. Known
   CUDA lesson: divergent branches inside one warp serialize — new
   parallelism must be warp-aligned or data-parallel across lanes.
6. **Suite cadence:** full suite + docs + commit once per kept change or
   per few hours of iterating, whichever comes first — never let more
   than one unvalidated change stack.

## Crib sheet

```powershell
# configure + build (from repo root; new build dir on this machine)
cmake -S . -B build-cuda -G "Visual Studio 17 2022" -A x64 `
  -DWEBP_ENABLE_CUDA=ON -DWEBP_BUILD_CUDA_BENCHMARK=ON `
  -DWEBP_BUILD_CWEBP=ON -DWEBP_BUILD_DWEBP=ON
cmake --build build-cuda --config Release --target `
  cwebp dwebp webp_cuda_batch_benchmark cuda_concurrency_test `
  cuda_near_lossless_test cuda_histogram_test

# force CUDA / force CPU
$env:WEBP_ACCELERATOR = "cuda"   # or "none"; WEBP_CUDA=0 also disables

# suite (needs Python 3.9+, Pillow)
python scripts\benchmark_cuda_end_to_end.py run `
  --build-dir build-cuda\Release `
  --output-dir $env:TEMP\libwebp-cuda-results-2080super `
  --label "win-2080super"

# diagnostics
$env:WEBP_CUDA_DECIMATE_TIMING = "2"          # GPU wall + phase breakdown
$env:WEBP_CUDA_DECIMATE_FAIL_COLLECT = "3"    # fault-inject band 3
$env:WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT = "1"  # CPU stage profile
#   (needs -DWEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=ON build +
#    WEBP_BENCHMARK_SESSION=exclusive + WEBP_STAGE_PROFILE_OUTPUT=<file>)
```

The benchmark corpus generates deterministically on first suite run; the
suite validates 180 CPU/CUDA pairs (byte-exact for lossy, decoded parity
for lossless modes) before timing anything.
