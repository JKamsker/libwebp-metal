# CUDA experiment decision summary

This is the short decision ledger. Consult it before the raw captures in
`CUDA_EXPERIMENT_RESULTS_RAW.md`. Measurements are from 2026-08-18 on an
NVIDIA GeForce RTX 2080 SUPER with CUDA Toolkit 12.0. Results are specific to
that hardware and workload.

## Decisions

| Strategy | Measured result | Decision |
|---|---:|---|
| Cross-color shared source tile | Historical lab ratio invalid: its control copied full histograms and reduced on the CPU. Production kernel: 7.8% faster at 1024x1024 and 8.1% faster at 2048x2048. | Integrated from the valid production A/B with actual-size dynamic shared memory; enabled by default. |
| Cross-color warp-private histograms | Historical control ratio invalid because transfer and reduction work differed. | Removed; no valid matched performance claim is retained. |
| Cross-color parallel score/entropy reduction | Historical control ratio invalid because transfer and reduction work differed. | Removed; atomic reduction and synchronization remain unpromising, but the old ratio is not evidence. |
| Combined specialized color kernel | Historical control ratio invalid and also confounded by the warp/parallel paths. | Removed; specialization alone remains unproven. |
| Warp-cooperative hash matching | 0.2446x scalar speed, or 4.09x slower. | Removed. The lane-per-match mapping wasted work on the short matches in this corpus. |
| Four-context pool | 0.992494 ms/iteration versus 0.721941 ms serial: 0.7274x control speed, or 37.5% slower. | Removed. Extra streams, buffers, and smaller launches lost to the simple serial path. |
| Resident lossless pipeline | 0.419031 ms/iteration versus 2.822457 ms with equivalent stage round trips: 6.74x faster. | Retained as the highest-priority pipeline experiment; production semantics and ownership still need implementation. |
| Predictor search/residual prototype | 7.607895 ms/20 iterations versus 155.654056 ms CPU: 20.46x faster. | Retained only as a feasibility experiment; it implements three modes rather than the production selector's full 14-mode search and entropy policy. |
| SharpYUV-style iterative kernel | 0.168858 ms/iteration versus 6.690596 ms CPU: 39.62x faster. | Retained as a high-priority feasibility experiment; it is not the complete public SharpYUV algorithm. |
| Near-lossless stencil | Lab: 38.49x faster. Exact production: 4.24x–23.45x faster at the retained 256x256 warm threshold, depending on pass count. | Integrated with exact CPU semantics, a 65,536-pixel warm threshold, and a quality-aware 16,777,216-pixel cold gate. Cold one/two-pass work stays on CPU. |
| Lossless histogram construction prototype | 14.491450 ms/20 iterations versus 41.601797 ms CPU: 2.87x faster. | Retained as historical feasibility evidence only; it did not consume the encoder's production-linked backward references. |
| Exact production full-stream histogram counts | Correctness: direct multi-span, cache, literal, copy, prefix-boundary, repeat, invalid-command, and transactional-decline tests pass; isolated CPU/CUDA streams are byte-identical for methods 0–6. Timing (2026-08-18, RTX 5070 Ti Laptop): forced-threshold single-process A/B across the sixteen-case corpus matrix was neutral within noise (7,799 ms off vs 7,841 ms on in aggregate, mixed per-case signs). | Integrated behind `WEBP_CUDA_HISTOGRAM=1`; entropy estimation, local distance-remapped histograms, merging, and Huffman construction remain on CPU. Stays off by default: population counting is a small share of the CPU histogram stage and no profitable crossover was found. |
| Batched lossy macroblock scoring | 0.791020 ms/iteration versus 1.772970 ms CPU: 2.24x faster. | Retained as a feasibility experiment; raster-order state and CPU commit remain unresolved. |
| Exact production lossy macroblock analysis | Correctness-only implementation; byte-identical CPU/CUDA lossy streams across every method 0–6, qualities 25/75/95, and odd dimensions. The RGB stage hands packed device YUV directly to analysis when ownership/geometry match, eliminating the intervening upload. No timing has been collected. | Integrated behind `WEBP_CUDA_LOSSY_ANALYSIS=1`; portable E2E suite now requires both lossy stages during forced rows and records the handoff policy. Keep off by default until measured. |
| Fused production lossy import and analysis | Correctness-only implementation; forced CUDA output is byte-identical to CPU at method/quality pairs 0/25, 4/75, and 6/95, and odd-dimension verification passes. RGB conversion and exact analysis launch on one stream with one completion boundary, and the later callback consumes an identity-matched cached result. No timing has been collected. | Integrated behind `WEBP_CUDA_FUSED_LOSSY_ANALYSIS=1` and the two underlying lossy stage flags. Keep off by default until a new portable E2E result set proves a useful crossover. |
| Production cross-color → main-hash resident handoff | Correctness: a dedicated device copy survives the intervening transform-map encode; the main hash request reuses it only when host pointer, pixel count, and row width match, and forced batches remain byte-identical with and without reuse. Timing (2026-08-18, RTX 5070 Ti Laptop): single-process lossless encodes were up to 17% faster (photo content) and never slower across the six-case A/B. | Enabled by default; `WEBP_CUDA_RESIDENT_LOSSLESS=0` disables it. The portable forced suite records observed handoff counts as row evidence. |
| Parallel production predictor policy | Superseded: independent per-tile scoring measurably collapsed to the no-op predictor on photographic content (mode 0 on 74% of tiles, up to +22% compressed size). Replaced by guided row-sequential selection: tile rows launch in stream order and score all 14 modes against the accumulated residual histogram of previous rows with double-precision costs and fixed-order reductions, matching the CPU cost model. Decoded pixels are identical; total compressed corpus size is about 1% smaller than the CPU selector. Windows RTX 5070 Ti E2E: PNG lossless batches moved from 1.37x to about 2x and JPEG lossless batches from 1.20x to about 4.9x. | Enabled by default with 4,000,000 cold / 16,384 warm pixel thresholds; `WEBP_CUDA_PREDICTOR=0` disables it. Near-lossless quantization and non-exact transparent inputs still decline to the CPU. |
| Near-lossless predictor selection (modes-only) | Non-exact quantized selection replays the CPU's per-tile reconstruction recurrence on the device (one replay thread per tile and mode over shared-memory tiles) and returns only the mode image; the CPU applies the prediction, so the near-lossless error bound is honored exactly (measured max deviation identical to CPU at strength 40) with sizes within about 2%. Windows RTX 5070 Ti singles including cold start: photo near-lossless 1370 -> 547 ms and 1710 -> 537 ms. Deterministic across runs. | Integrated behind the predictor stage flag via the ABI v8 modes-only contract; exact requests keep the full select-and-apply path. |
| Whole-pass lossy macroblock decimation | Byte-exact CUDA port of VP8Decimate at RD_OPT_BASIC: skewed anti-diagonal wavefront reproduces the raster scan's reconstruction, non-zero, mode, and diffusion-error dependencies with integer-exact arithmetic; all twelve corpus cases emit byte-identical bitstreams and forced batches are hash-stable. Enabled by removing the mid-pass cost-table refresh (measured under 1% size effect either way, applied to CPU and CUDA alike). Windows RTX 5070 Ti 24-image batches: PNG lossy 183.5 -> 92.8 ms/image (1.98x), JPEG lossy 190.4 -> 99.1 ms/image (1.92x). | Enabled by default with 64 warm / 4,000 cold macroblock thresholds; `WEBP_CUDA_LOSSY_DECIMATE=0` disables. Trellis methods (5+) and restored upstream refresh cadence decline to the CPU. |
| Decimate tuning round | Residual-cost walks parallelized one-mode-per-warp with thread 0 replaying the CPU's exact comparison order on precomputed values (decisions unchanged, byte-identical outputs); static cost/proba tables kept device-resident across images; process-start prewarm extended to the decimate unit; cwebp fast exit skips CRT and driver teardown after outputs flush (`WEBP_NO_FAST_EXIT` opts out). Windows RTX 5070 Ti 24-image lossy batches: 92.8 -> 64.9 ms/image PNG, 99.1 -> 71.0 ms/image JPEG. | All enabled by default; the fast exit benefits CPU and CUDA fresh-process encodes alike. |
| Banded decimate result streaming | ABI v10 BEGIN/COLLECT phases: the wavefront launches asynchronously with a CUDA event per completed band of macroblock rows, and the host collects bands on a separate copy stream while lower diagonals still execute, so selection replay and token recording overlap device work. Byte-identical and hash-stable across the full suite. Windows RTX 5070 Ti 24-image lossy batches: 64.9 -> 57.2 ms/image PNG (2.91x), 71.0 -> 62.3 ms/image JPEG (2.77x). | Enabled by default (4 bands when the image has at least 8 macroblock rows, whole-pass otherwise); any band-collection failure falls back to CPU decimation from the first unreplayed row. |
| Multi-partition token emission | A stage profile attributed up to 82 ms per texture image to single-partition VP8EmitTokens. Lossy streams now default to eight standard VP8 token partitions (row y records into partition y mod 8, flat ~38 bytes/image) emitted on parallel workers, for CPU and CUDA alike. Verified: CPU/CUDA byte parity, decoded parity against the single-partition stream, methods 2-6, odd/tiny dimensions, and target-size search convergence. Windows RTX 5070 Ti 24-image lossy batches: CUDA 57.2 -> 46.9 ms/image PNG (3.28x), 62.3 -> 53.0 ms/image JPEG (2.99x); CPU baseline 166.6 -> 153.8 ms/image PNG. | Enabled by default; WEBP_TOKEN_PARTITIONS=0..3 selects 1/2/4/8 partitions (0 restores the upstream stream) and WEBP_TOKEN_EMIT_THREADS=0 forces serial emission without changing bytes. Partition count is capped so every partition owns at least one macroblock row. |
| Pipelined token recording on the accelerated decimate path | A single worker thread records each collected band's macroblocks while the main thread replays the same band; the recorder reads levels, modes, and nz-context words directly from the GPU results and processes them in exact raster order, so the saturating probability statistics and the emitted bytes are identical to inline recording (verified across content classes, qualities 25-98 incl. error diffusion, tiny/odd dimensions, and the pipeline-off cross-check). Decimate streaming moved from 4 to 8 bands for finer overlap. CPU encoder untouched, so the gain is pure ratio: CUDA lossy batches 46.9 -> 45.9 ms/image PNG (3.46x), 53.0 -> 51.0 ms/image JPEG (3.20x). GPU lossy analysis was re-tested on this build and remains neutral-to-negative; it stays off. | Enabled by default on the accelerated path; WEBP_TOKEN_RECORD_PIPELINE=0 records inline on the main thread instead. A worker-thread failure downgrades to synchronous recording at each collect point; recording errors surface as the same out-of-memory failure as inline recording. |
| RTX 2080 SUPER four-band re-check | Five alternating-process native-sm_75 A/Bs, each with one warmup and three 24-image samples: PNG 57.699 ms/image with 4 bands versus 57.126 ms with 8 (+0.572 ms); JPEG 58.583 versus 57.725 ms (+0.857 ms). Output hashes matched. Both deltas are below the 1.5 ms noise threshold and both favor 8 bands. | Rejected and removed. Retain the eight-band default; do not retry four bands on Turing without a new profiling reason. |
| RTX 2080 SUPER dispatch-threshold calibration | Isolated forced-stage grids used seven post-warmup samples per point and three fresh processes per cold point. Decimate lost at 384x384 warm (576 MBs) and won for all three inputs at 448x448 (784 MBs); cold lost for all three inputs at 1664x1664 (10,816 MBs) and won at 1792x1792 (12,544 MBs). Color and predictor won at their 4,000,000-pixel cold decision point, and three-pass near-lossless won at 16,777,216 pixels. Their warm gates also won. | Raise only decimate from 64/4,000 to 784/12,544 warm/cold macroblocks. Retain the color, predictor, and near-lossless gates. |
| Architecture-conditional decimate dispatch gates | The Turing calibration above had replaced the sm_120-tuned decimate gates (64 warm / 4,000 cold macroblocks) globally with the Turing crossover (784 / 12,544), silently declining GPU dispatch on the RTX 5070 Ti for warm images under 784 MBs and cold plain-cwebp images under 12,544 MBs (verified on-machine: no decimate pass at 576 MBs warm or 7,500 MBs cold). The gate now selects per device generation via a memoized compute-capability query: Ampere-or-newer keeps 64/4,000, older keeps 784/12,544; sizes outside the disputed band never touch the CUDA runtime. | Kept. Both generations retain their measured crossovers; WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS still overrides. |
| Turing I4 two-warp residual split | Nsight identified barrier imbalance as the kernel limit: 93.82% of scheduler cycles had no eligible warp and CTA barriers accounted for 9.6 of 16.3 cycles/instruction (58.7%). Splitting the ten serial residual walks over two warps reduced barrier share only to 56.9%, increased executed instructions 8.1%, and left the representative kernel at 189.95 vs 189.79 us. Five alternating 24-image processes: PNG 93.822 baseline vs 96.337 ms/image split; JPEG 94.042 vs 93.876 ms. Hashes matched. | Rejected and removed. The JPEG delta is noise and PNG regressed 2.515 ms/image. The I4 limit is the four-barrier-per-step recurrence and sparse diagonal wavefront, not residual-walk warp assignment alone. |
| Turing I4 prediction/transform barrier fusion | A fresh method-4 profile put I4 at 64.8--65.6% of block cycles on photo/texture. Fusing each mode's prediction, transform, quantization, and reconstruction onto four warp leaders removed one block-wide barrier per I4 step, but reduced the ten transform chains to four-way parallelism. Native-sm_75 24-image medians regressed from 57.402 to 68.425 ms/image PNG and 57.244 to 68.491 ms JPEG; output hashes and byte counts matched. | Rejected and removed. Saving one barrier does not pay for reducing mode-level transform parallelism; future barrier removal must retain at least ten-way mode concurrency. |
| Turing ten-warp I4 barrier reduction | Assigned one full warp to each of the ten I4 modes (320-thread CTA), keeping ten mode chains concurrent while fusing prediction, transform, quantization, reconstruction, and metrics behind warp-local synchronization. This removed two CTA barriers per I4 step and passed focused method-5/6 byte parity. Nevertheless, native-sm_75 24-image medians regressed from 57.402 to 59.225 ms/image PNG and 57.244 to 60.227 ms JPEG. Warm photo/texture device wall rose from 39.89/38.38 to 44.74/43.39 ms, with I4 increasing from 64.9/65.6% to 69.2/69.9% of block cycles. | Rejected and removed. Ten mostly idle warps add more scheduling/register cost than the two removed barriers save; the sparse wavefront cannot turn their theoretical occupancy into latency hiding. Future I4 work must retain compact mode-lane packing as well as mode concurrency. |
| Parallel whole-macroblock intra prediction | A setup sub-profile found luma16/chroma8 prediction generation consumed 92.8--92.9% of thread 0's import/setup cycles (borders 2.5--2.6%, source-copy tail 3.8%, nz setup 0.8%). The four luma and eight chroma mode planes now fill across all 128 CTA threads after thread 0 computes the three exact DC values. Five alternating native-sm_75 processes (15 post-warmup samples/cell) improved PNG 57.337 -> 53.668 ms/image and JPEG 58.074 -> 54.784 ms with identical hashes. The official suite measured PNG 97.1 CPU / 53.0 CUDA (1.83x) and JPEG 97.0 / 53.3 (1.82x); all 180 suite validation pairs, a 105-case methods 2--6/qualities 25--98/tiny/odd/fallback battery, and focused CUDA tests passed. | Retained. Parallelize deterministic prediction-plane pixels while preserving thread 0's exact DC sums and all unavailable-border conventions. This removes 3.7--3.8 ms/image from the preceding official CUDA batch rows. |
| Warp-cooperative intra4 prediction pixels | Replaced the four warp-leader I4 prediction generators with a uniform-mode warp routine: lanes 0--15 computed one exact 4x4 output pixel each while retaining the existing ten-way transform and metric layout and every CTA barrier. Focused method-5/6 trellis/fallback output was byte-exact. Three post-warmup 24-image samples measured PNG 52.864 ms/image versus the parent official 53.0 (noise-level -0.136 ms), while JPEG regressed to 54.499 from 53.3 (+1.199 ms, still below the 1.5 ms confidence threshold). | Rejected and removed. Per-pixel directional-mode formula and branch overhead cancels the four-leader prediction work. Do not retry this mapping without evidence that prediction, rather than transform/residual work, limits the post-2d7d65fb I4 step. |
| Warp-parallel intra4 winner commit | Kept thread 0's exact ordered score scan and tie behavior, then broadcast the selected mode and non-zero word within warp 0. Lanes 0--15 copied the winner's sixteen levels and reconstructed pixels before thread 0 committed the mode/non-zero contexts. Focused method-5/6 trellis/fallback output was byte-exact. Three alternating processes per format (nine post-warmup samples/cell) measured PNG 53.040 -> 52.387 ms/image and JPEG 53.377 -> 52.830 ms/image; hashes and byte counts matched. | Rejected and removed. The 0.654 ms PNG and 0.547 ms JPEG improvements are both below the 1.5 ms/image retention threshold. Winner copying is not a material post-2d7d65fb bottleneck; do not retry this mapping without a new profile. |
| Four-lane intra4 transform / basic quantization | Four adjacent lanes now cooperate on each of the ten I4 modes: row/column forward transform, basic quantization, and inverse transform are distributed across the group while all ten modes retain their compact two-warp mapping. Trellis quantization remains on lane 0 to preserve its dependency chain. The complete official suite moved PNG lossy CUDA from 53.0 to 50.0 ms/image and JPEG from 53.3 to 49.6 ms/image; paired CPU medians were 99.4 ms for both, producing 1.99x and 2.00x speedups. All 180 suite validations, the 105-case methods 2--6 / qualities 25--98 / tiny / odd / fallback battery, and six registered CTests passed. | Retained in `5d841ba0`. This removes 3.0--3.7 ms/image from the preceding official CUDA rows and attacks the profiled transform/quantization portion without expanding to ten mostly idle warps. |
| Register-shuffle intra4 transform transpose | The post-`5d841ba0` profile still put I4 at 70.4% of photo and 71.5% of texture block cycles. Replacing the four-lane forward/inverse transform's shared-memory transpose and internal warp synchronization with a four-shuffle cyclic register transpose passed the focused trellis, padded-stride, band-remainder, and transactional-fallback test byte-exactly. Three post-warmup 24-image samples nevertheless moved PNG from 50.568 to 51.546 ms/image and JPEG from 49.011 to 51.745 ms/image. | Rejected and removed. PNG regressed by 0.978 ms/image (inside the noise band) and JPEG regressed materially by 2.734 ms/image. The shuffle/select instruction cost exceeds the saved shared-memory synchronization on Turing; do not retry this transpose mapping blind. |
| Parallel intra4 score preparation | Temporary subphase timing attributed 36--42% of measured I4 cycles to the serial score-selection/commit interval, versus 23--27% to transform/quantization. Ten lanes now preload mode costs and calculate both sides of the CPU early-out in parallel; thread 0 preserves the exact ordered comparisons and tie behavior, and copies only the final winner. Five alternating native-sm_75 processes (15 samples/cell) moved PNG 51.625 to 49.787 ms/image and JPEG 50.667 to 49.148. The official suite measured 99.844 CPU / 48.565 CUDA ms for PNG (2.056x) and 99.723 / 48.552 for JPEG (2.054x). | Retained in `8ae71f74`. All six CTests, 180 official validations, and 105 additional methods 2--6 / qualities 25--98 / tiny / odd / band-3 fallback cases passed. Exact CI run `32214115280` passed all eleven jobs. |
| Intra4 residual-cost known-last handoff | The post-score-preparation profile put I4 metrics at 22--27% of I4 cycles. Basic quantization was extended to reduce and retain the last non-zero zigzag position, allowing each mode's residual-cost walk to skip its backward 16-coefficient scan; trellis retained its exact serial last search. The focused trellis/padded-stride/fallback test was byte-exact. Three post-warmup 24-image samples moved PNG from the 48.565 ms official baseline to 48.752 ms and JPEG from 48.552 to 48.029 ms. | Rejected and removed. The +0.187 ms PNG regression and -0.523 ms JPEG improvement are both far below the 1.5 ms/image retention threshold. The backward last scan is not a material part of the post-`8ae71f74` metrics interval. |
| Inline no-flush VP8 token bit path | The current CUDA stage profile measured texture token emission at 45--46 ms; cross-thread `gprofng` clock sampling attributed 57.3% of total CPU time to `VP8PutBit`, 19.1% to `Flush`, and 81.2% inclusively to `VP8EmitTokens`. An inline arithmetic-coder path handled state-only bits and delegated byte-boundary cases to the unchanged table-driven writer. After correcting the normalization domain to `log2(range + 1)`, historical output hashes and byte counts were exact. Three post-warmup 24-image samples measured PNG 49.721 ms and JPEG 48.493 ms versus the 48.565 / 48.552 ms official baseline. | Rejected and removed. PNG regressed 1.156 ms/image and JPEG improved only 0.059 ms/image; neither clears the 1.5 ms threshold. The inline log2/state path does not beat the existing table-driven call path. |
| Exact table-driven token-page inlining | The same token-emission profile motivated moving only the reverse page walk beside the existing boolean coder, allowing GCC to inline the unchanged `VP8PutBit`, normalization tables, carry propagation, and resize path. Focused trellis/fallback and concurrency tests passed; all 60 measured process samples retained the historical PNG/JPEG hashes and byte counts. Five alternating process medians moved PNG 48.584 to 47.454 ms/image and JPEG 49.674 to 48.305 ms/image. | Rejected and removed. The 1.130 ms PNG and 1.369 ms JPEG improvements are both below the required 1.5 ms/image confidence threshold. Cross-translation-unit call overhead is measurable but not material enough to justify coupling the encoder token representation to the bit-writer utility. |
| Local-state table-driven token-page coding | The token-emission profile and generated assembly showed `range`, `value`, and `nb_bits` still round-tripping through the writer structure for every token after plain inlining. The retained helper uses the unchanged normalization tables and `Flush` path but keeps those three values in registers between real byte flushes. Five alternating process medians moved PNG 48.646 to 44.735 ms/image and JPEG 49.576 to 44.544 ms/image with identical hashes and byte counts in all 60 samples. The official suite measured 94.366 CPU / 44.274 CUDA ms for PNG (2.131x) and 93.924 / 44.017 for JPEG (2.134x). | Retained in `4852f92e`. Six CTests, all 180 official validations, and 105 additional methods 2--6 / qualities 25--98 / tiny / odd / band-3 fallback cases passed. Exact CI run `32217152201` passed all eleven jobs, including shared-library ABI and Autotools coverage. |
| Local-state in-page byte flushing | A fresh whole-process `gprofng` profile after `4852f92e` attributed 42.92% of exclusive CPU samples to `Flush`, 29.39% to `VP8PutTokenPage`, and 22.55% to coefficient-token recording. `VP8PutTokenPage` now keeps `buf`, `pos`, and `run` local and performs the unchanged carry/run byte emission inline when the existing buffer has capacity; insufficient capacity synchronizes state and uses the original `Flush` / `BitWriterResize` slow path. Five order-balanced process medians moved PNG 44.299 to 41.843 ms/image and JPEG 44.317 to 42.017 ms/image, with identical hashes and byte counts in all 60 samples. The official suite measured 92.0 CPU / 41.6 CUDA ms for PNG (2.21x) and 92.6 / 41.7 for JPEG (2.22x). | Retained in `9a44518a`. A new always-active test covers repeated growth and allocation failure; seven CTests, all 180 official validations, and 105 additional methods 2--6 / qualities 25--98 / tiny / odd / band-3 fallback cases passed. Exact CI run `32221803146` passed all eleven jobs. |
| Packed token normalization lookup | The post-`9a44518a` end-to-end profiles agreed that `VP8PutTokenPage` consumed 54.0--54.3% of exclusive CPU samples. Instruction sampling showed its separate `kNorm` and `kNewRange` indexed loads as the largest local cluster, so an exact 16-bit table packed both values into one lookup per renormalization. The focused seven-test set passed, generated assembly confirmed one word load replaced two byte loads, and all 60 timing outputs retained their reference hashes and byte counts. Five order-balanced process medians moved PNG 42.036 to 42.029 ms/image and JPEG 41.900 to 41.939 ms/image. | Rejected and removed. PNG improved only 0.007 ms/image and JPEG regressed 0.040 ms/image, both effectively zero and far below the 1.5 ms/image threshold. The two normalization values are already cache-resident and their loads overlap enough that packing them does not reduce end-to-end latency. |
| Branchless token bit-state update | The same post-`9a44518a` instruction profile showed the token-bit decision inside the 54% `VP8PutTokenPage` loop as another local cost. An exact mask-arithmetic update replaced the bit branch: `value` and `range` reached the identical states for both bit values, generated assembly removed the conditional jump, and the seven focused tests passed. All 60 timing outputs retained reference hashes and byte counts. Five order-balanced process medians moved PNG 41.929 to 41.978 ms/image and JPEG 42.018 to 41.976 ms/image. | Rejected and removed. PNG regressed 0.049 ms/image and JPEG improved only 0.042 ms/image. The extra negate, masks, and dependent arithmetic exactly offset the unpredictable branch; retain the simpler branch until a materially different multi-token coding strategy is profiled. |
| Padded intra4 per-mode shared scratch | The guarded stage profile put medium texture decimation at 49.9 ms and direct GPU phase timing attributed 68.4% of block cycles to I4. Static layout analysis found power-of-two shared-memory strides between simultaneous modes: 32 bytes for transforms/levels, 64 for transform scratch, and 128 for reconstruction. Padding each mode rotated those bank mappings while leaving every algorithm and index within a mode unchanged. The focused seven-test set passed, all 60 timing outputs retained reference hashes and byte counts, register use stayed at 93, and shared memory rose only from 17,912 to 18,032 bytes. Five order-balanced process medians moved PNG 42.075 to 42.348 ms/image and JPEG 42.038 to 42.188 ms/image. | Rejected and removed. PNG regressed 0.273 ms/image and JPEG 0.150 ms/image. Any reduction in bank aliasing is smaller than the cost of the perturbed addressing/shared footprint; retain the compact arrays unless hardware counters identify a specific conflicting access. |
| Dynamic-probability token fall-through | Token generation makes indexed probabilities common and fixed sign/category probabilities less frequent, while the current GCC layout put the fixed case on the fall-through path in the 54% `VP8PutTokenPage` loop. A portable expected-branch hint inverted only that layout; generated assembly confirmed the indexed lookup became fall-through, the focused seven tests passed, and all 60 timing outputs retained reference hashes and byte counts. Five order-balanced process medians moved PNG 42.095 to 41.857 ms/image and JPEG 42.041 to 41.728 ms/image. | Rejected and removed. The 0.238 ms PNG and 0.313 ms JPEG gains are consistent but far below the 1.5 ms/image retention threshold. Control-flow layout alone is not material enough to keep compiler-specific hinting in this utility. |
| Unified indexed fixed-probability tokens | To remove the probability-kind branch rather than merely relayout it, fixed tokens retained their marker and low probability byte but used a reserved 2048--2303 index window. Each of the eight partition emitters built a 2.3 KiB table containing the 1,056 adaptive probabilities plus the 256 identity entries, allowing `VP8PutTokenPage` to use one unconditional indexed load for every token. Generated assembly removed the kind branch, the focused seven tests passed, and all 60 outputs retained reference hashes and byte counts. Five order-balanced process medians moved PNG 42.094 to 41.925 ms/image and JPEG 42.016 to 41.667 ms/image. | Rejected and removed. Gains of 0.170 ms PNG and 0.349 ms JPEG are far below the 1.5 ms/image threshold and do not justify changing the internal token representation, adding per-partition table setup, or expanding its test/API contract. |
| Two-lane I4 residual-cost split | The post-`4852f92e` stage profile showed token emission reduced to 23 ms on texture while CUDA decimation dominated at 53 ms. I4 was 67--68% of photo/texture block cycles; temporary subdivision put metrics at 25--28% of I4 and the residual-cost warp at 100% of the metric interval versus 56--73% for SSE/flatness and 40--48% for distortion. Two lanes per mode computed independent eight-coefficient spans while retaining all ten concurrent modes. The focused trellis/fallback test was byte-exact. Five alternating process medians moved PNG 44.813 to 45.562 ms/image and JPEG 44.779 to 45.959 ms/image. | Rejected and removed. The pair shuffle, duplicated context/table address work, and additional active lanes outweighed the shorter coefficient span, regressing PNG by 0.749 ms and JPEG by 1.180 ms. Retain one scalar lane per mode; do not retry coefficient splitting without a materially different mapping. |
| Scalar-only I4 winner scan | Temporary subdivision of the 24--25% serial select/rotate interval attributed 46--49% to the ordered ten-mode scan, 29--30% to reconstruction/rotation, and only 21--25% to level copies plus score/gate bookkeeping. Because parallel lanes already prepared exact base/full scores, the candidate scanned only those scalars and materialized the final winning `ModeScore` once, preserving mode order, early-out, and ties. The focused trellis/fallback test and all 60 timing samples were byte-exact. Five alternating process medians moved PNG 44.538 to 43.770 ms/image and JPEG 44.417 to 43.924 ms/image. | Rejected and removed. The 0.768 ms PNG and 0.492 ms JPEG gains are below the 1.5 ms/image threshold. Avoid retrying winner-scan bookkeeping alone; a useful selection change must also reduce reconstruction/rotation or another I4 interval. |
| Scalar I4 scan plus warp-parallel winner commit | Combined the exact scalar-only base/full-score scan with a warp-0 commit: lanes 0--15 copied the final winner's levels and 4x4 reconstruction while lanes 0--7 updated the I4 boundary snake, reusing the existing end-of-step CTA barrier. Mode order, early-out, ties, context updates, and reconstruction bytes remained unchanged. The focused trellis/fallback test passed, and all 60 timing samples retained the reference hashes and byte counts. Five order-balanced process medians moved PNG 44.486 to 43.403 ms/image and JPEG 44.508 to 43.835 ms/image. | Rejected and removed. The 1.083 ms PNG and 0.673 ms JPEG gains remain below the 1.5 ms/image retention threshold even after addressing both the scan and reconstruction/rotation portions of the serial interval. Do not revisit this combined mapping without a new profile or a materially lower synchronization cost. |
| Ten-warp I4 prediction mapping | The retained medium-image profile put I4 at 67--68% of block cycles and prior subphase timing attributed 18--20% of I4 to prediction. A 320-thread CTA assigned one uniform warp leader to each of the ten modes, eliminating the 2--3 serial prediction calls per leader while leaving the ten-way transform, metric, and selection algorithms unchanged. The focused trellis/fallback test passed, and all 36 timing samples retained the reference hashes and byte counts. Three order-balanced process medians moved PNG 44.268 to 44.039 ms/image and JPEG 44.518 to 44.004 ms/image. | Rejected and removed. The 0.229 ms PNG and 0.515 ms JPEG gains are far below the 1.5 ms/image threshold; extra CTA barrier participants and tighter launch-bound resource pressure absorb almost all predictor parallelism. Retain the 128-thread/four-leader mapping unless prediction can be shortened without enlarging the CTA. |
| Half-warp-paired intra16 residual costs | Intra16 selection reached 24.2% of block cycles on the medium graphic case. Because each AC block's incoming context is derivable from the already-known nonzero bitmap, two independent blocks were evaluated concurrently by the lower and upper 16-lane halves of each mode warp, reducing sixteen serial AC reductions to eight while retaining the DC reduction and exact costs. The focused trellis/fallback test passed, and all 36 timing outputs matched reference hashes and byte counts. Three order-balanced process medians moved PNG 44.530 to 44.688 ms/image and JPEG 44.463 to 44.462 ms/image. | Rejected and removed. PNG regressed 0.158 ms/image and JPEG changed by less than 0.001 ms. The mapping reduced some photo/texture intra16 phase share but raised the kernel from 93 to 100 registers, cancelling the local gain. Do not pack residual blocks into half-warps without first avoiding that register-pressure increase. |
| Decimate kernel parallelization round | Event timing showed the wavefront device wall (~36 ms at 100x75 MBs, ~145 us per anti-diagonal = per-MB block latency) is the lossy batch floor. Parallelized: source import across the block, winner level/recon copies of all three selections, intra4 predictions across the four warp leaders, and the three independent intra4 metrics on separate warps (divergence inside one warp serializes — a 3-lanes-per-mode split regressed and was replaced by the warp-aligned split). GPU wall 36.2 -> ~30.5 ms; lossy batches 45.9 -> 43.7 ms/image PNG (3.70x), 51.0 -> 50.0 ms/image JPEG (3.35x). Byte parity across content classes, qualities, tiny/odd dims. Negative results: shared-memory residual-cost tables neutral (walks are dependency-bound, tables L1-resident); thread_level=1 default (threaded analysis) neutral on batches, reverted. | WEBP_CUDA_DECIMATE_TIMING=1 prints per-pass device wall; =2 adds per-phase cycle percentages. Remaining ceiling: the intra4 sequential 16-step chain is ~60% of the wall and dependency-bound. |
| CUDA graphs plus double buffering | 0.766127 ms/iteration versus 0.768430 ms with direct launches: 1.0030x, a noise-level 0.3%. The simpler serial path was faster than either. | Removed. No material graph benefit at this launch count, and buffering added overhead. |
| Current decimate wavefront launch-gap bound | An `nvprof` GPU trace of the production method-4 1600x1200 photo path recorded 248 anti-diagonal kernels. Their execution summed to 29.926 ms and the first-launch-to-last-completion span was 30.215 ms; all 247 inter-kernel gaps summed to only 0.288 ms (1.168 us mean, 1.760 us maximum). | Do not pursue CUDA graph capture or a cooperative persistent wavefront for launch reduction on this path: even the impossible best case of deleting every measured gap is far below the 1.5 ms/image retention threshold. The older graph lab result did not establish this production-path bound. |
| Four-warp balanced I4 transform groups | The retained four-lane transform mapping packed eight mode groups into warp 0 and two into warp 1. A candidate mapped the ten groups 3/3/2/2 across the existing 128-thread CTA and let each warp consume the prediction planes its leader produced, eliminating one CTA-wide barrier per I4 step without changing the algorithm or block size. All seven focused CTests passed, and all 60 timing outputs retained reference hashes and byte counts. Five order-balanced process medians moved PNG 41.954 to 41.703 ms/image and JPEG 41.881 to 41.709 ms/image. | Rejected and removed. Gains of 0.251 ms PNG and 0.172 ms JPEG are far below the 1.5 ms/image retention threshold. The existing metric warps and next block-wide dependency absorb the local transform rebalance; do not retry group redistribution alone. |
| Combined fixed and variable residual-cost table | The I4 residual-cost warp was the measured metric critical path and `LevelCostDev` performed two dependent global loads for each coefficient. A per-image 32-bit table folded `VP8LevelFixedCosts` into all 68 hot probability-dependent entries, using the original fixed table only above level 67. All seven focused CTests passed and all 60 outputs retained reference hashes and byte counts, but the table doubled from 13 to 26 KiB and kernel registers rose from 93 to 109. Five order-balanced process medians moved PNG 41.854 to 43.433 ms/image and JPEG 41.727 to 42.939 ms/image. | Rejected and removed. PNG regressed 1.579 ms/image and JPEG 1.213 ms/image. The larger working set and address/value width cost more than the eliminated load; retain the compact two-table representation. |
| Small-level fixed-cost specialization | To avoid widening the residual-cost table, an exact hot path used the known VP8 fixed costs directly: zero for level 0 and 256 for levels 1--4. The compact 13 KiB probability table and 93-register kernel were unchanged. All seven focused CTests passed and all 60 outputs retained reference hashes and byte counts. Five order-balanced process medians moved PNG 41.851 to 42.423 ms/image and JPEG 41.712 to 42.392 ms/image. | Rejected and removed. PNG regressed 0.572 ms/image and JPEG 0.680 ms/image. The divergent range test costs more than the saved fixed-table load; retain the original branch-free indexed expression. |
| Coefficient-major I4 residual mirror | The ten simultaneous scalar residual walks read coefficient `n` from mode-major arrays separated by a 32-byte stride, creating a shared-bank alias. Basic quantization wrote through to a 320-byte coefficient-major mirror and method 6 copied its exact trellis output there, so each coefficient step became contiguous across modes without a new barrier. All seven focused CTests passed, all 60 outputs retained reference hashes and byte counts, registers stayed at 93, and shared memory rose from 17,912 to 18,232 bytes. Five order-balanced process medians moved PNG 41.765 to 41.918 ms/image and JPEG 41.582 to 41.994 ms/image. | Rejected and removed. PNG regressed 0.153 ms/image and JPEG 0.412 ms/image. The extra shared writes and footprint outweigh any reduction in read-bank aliasing; retain the single mode-major levels array. |
| Two-token boolean-coder loop unroll | The post-`9a44518a` end-to-end profiles still attributed 54.0--54.3% of sampled CPU time to `VP8PutTokenPage`. Its generated loop had one token load and back-edge per coded bit, so a GCC-only two-way unroll duplicated the exact hot body to overlap token/probability loads while preserving the serial coder state. Disassembly confirmed the two-token body, all seven focused CTests passed, and all 60 outputs matched between variants. Five order-balanced process medians moved PNG 41.968 to 41.950 ms/image and JPEG 42.004 to 41.958 ms/image. | Rejected and removed. Gains of 0.018 ms PNG and 0.046 ms JPEG are effectively zero. Loop bookkeeping and load overlap are not limiting the arithmetic coder; avoid larger unrolls unless a new profile shows the serial state chain has changed. |
| Phase-aliased decimate shared workspace | A fresh medium-texture profile measured decimation at 53.72 ms of a 78.77 ms encode and I4 at 68.4% of block cycles. I16, I4, and UV scratch have disjoint barrier-delimited lifetimes, so a POD union reduced `DecimateKernel` static shared memory from 17,912 to 11,704 bytes, raising the Turing residency ceiling from three to five CTAs/SM; registers rose from 93 to 96. All seven focused CTests passed and all 60 outputs matched. Direct medium-texture GPU wall moved 28.48 to about 28.97 ms; five order-balanced process medians moved PNG 42.108 to 42.193 ms/image and JPEG 41.889 to 42.070 ms/image. | Rejected and removed. PNG regressed 0.085 ms/image and JPEG 0.182 ms/image. The dependency-heavy sparse wavefront does not use the extra theoretical residency, while union-member addressing and register pressure cost slightly; retain direct phase arrays. |
| Compact I4 reconstruction scratch | The retained I4 output scratch used a 32-byte row stride for each 4x4 reconstruction: four cooperative row lanes wrote identical banks, and ten metric lanes read mode bases 128 bytes apart. A compact 4-byte row layout plus exact stride-aware SSE/Hadamard helpers reduced static shared memory from 17,912 to 16,792 bytes with registers unchanged at 93. All seven focused CTests passed and all 60 outputs matched. Direct medium-texture GPU wall was about 28.64 ms versus 28.48 ms for the parent; five order-balanced process medians moved PNG 41.866 to 42.004 ms/image and JPEG 41.918 to 41.971 ms/image. | Rejected and removed. PNG regressed 0.139 ms/image and JPEG 0.053 ms/image. Removing output-bank aliases is offset by stride-aware metric arithmetic; retain the BPS-strided scratch and do not conflate this result with per-mode padding. |
| Whole-I4 lower-bound pruning | Before any I4 prediction, an exact lower bound added the mandatory 211-bit-cost flag to 16 times the minimum entry computed from the canonical fixed I4 mode-cost table. If that non-negative lower bound could not beat I16 or already exceeded the header limit, the complete I4 search was skipped. All seven focused CTests passed and all 60 outputs matched. Graphic-medium device wall improved from 28.25 to 23.97 ms, while photo/texture were unchanged. Five order-balanced aggregate medians moved PNG 41.943 to 41.803 ms/image and JPEG 41.869 to 41.784 ms/image. | Rejected and removed. Aggregate gains of 0.140 ms PNG and 0.085 ms JPEG are far below the 1.5 ms/image threshold because qualifying flat/graphic macroblocks are too small a share of the six-image workload. Preserve the result for a future content-adaptive policy, but do not retain an extra table field and branch globally. |
| Local remaining-capacity token flush | The retained page coder checked `pos <= max_pos` and recomputed `max_pos - pos` at every real byte flush. An exact candidate kept remaining capacity local, decremented it by each emitted pending run plus byte, and reloaded it only after the unchanged `Flush`/resize fallback. The seven focused CTests passed, including repeated growth and byte-for-byte injected allocation-failure state; all 60 timing outputs matched. Five order-balanced medians moved PNG 42.131 to 42.083 ms/image and JPEG 42.095 to 41.945 ms/image. | Rejected and removed. Gains of 0.048 ms PNG and 0.150 ms JPEG are far below the retention threshold. The capacity check is not a material part of the 54% token-page loop; preserve the clearer direct bounds invariant. |
| Turing dual-sub-block I4 dependency diagonals | The exact `x + 2y` predecessor relation reduces sixteen serial raster steps to ten diagonals with up to two blocks each. Two 128-thread teams evaluate independent blocks while thread 0 preserves raster-order aggregation and abort behavior. Five order-balanced medians moved PNG 42.226 to 40.420 ms/image and JPEG 42.247 to 40.610; all 60 outputs matched. Seven focused CTests, 105 exact method/quality/tiny/odd/fallback cases, and all 180 official validation pairs passed. | Retained. Gains of 1.806 ms PNG and 1.637 ms JPEG clear the threshold. The official RTX 2080 SUPER persistent result is now 92.4 / 40.0 ms PNG (2.31x) and 92.3 / 40.2 ms JPEG (2.30x). |
| I4 team-local named barriers | A fresh retained-head profile put medium photo/texture I4 at 64.8--66.5% of block cycles. Temporary subphase timing captured over 96% of I4 and split it across transform/quantization (25.6--26.5%), selection/publication (22.7--23.3%), metrics (21.7--24.0%), prediction/boundary (20.9--21.4%), and raster aggregation (about 7%). A candidate replaced four of six per-diagonal CTA barriers with independent 128-thread named barriers; the two winner-publication/abort barriers stayed CTA-wide. The focused trellis/fallback test and all 60 timing outputs were byte-exact. Five order-balanced medians moved PNG 40.291 to 39.994 ms/image and JPEG 40.210 to 39.892. | Rejected and removed. Gains of 0.297 ms PNG and 0.318 ms JPEG are far below the 1.5 ms/image threshold. The two teams have sufficiently uniform work that independent progress through the numeric phases does not materially shorten the critical path. |
| Local-state coefficient-token recording | A fresh texture-medium `gprofng` profile attributed 58.2% of sampled CPU time to `VP8PutTokenPage` and 36.7% to `VP8RecordCoeffTokens`; replay itself was negligible. A candidate retained the current token-page pointer and remaining capacity locally throughout each coefficient block, synchronizing only at page growth and function return while preserving statistics and allocation-failure behavior. The bit-writer growth/failure test and focused CUDA trellis/fallback test passed; all 60 timing outputs matched. Five order-balanced medians moved PNG 40.186 to 40.485 ms/image and JPEG 40.241 to 40.392. | Rejected and removed. PNG regressed 0.299 ms/image and JPEG 0.151 ms/image. Compiler promotion plus overlap with GPU work leaves no useful end-to-end gain; keep the direct buffer state for clarity. |
| Eight-lane basic I4 quantization | Fresh I4 subphase timing attributed 25.6--26.5% to transform/quantization. A candidate widened each mode from four to eight lanes for basic quantization, halving the per-lane coefficient loop while retaining exact four-lane forward/inverse transforms and the serial method-6 trellis path. The focused trellis/fallback test passed and all 60 timing outputs matched. Five order-balanced medians moved PNG 40.163 to 40.202 ms/image and JPEG 40.366 to 40.088. | Rejected and removed. PNG regressed 0.040 ms/image and JPEG improved only 0.279 ms/image. Additional active lanes and subgroup synchronization absorb the shorter coefficient loop; retain the compact four-lane mapping. |
| Cold coefficient-statistics renormalization | A compiler branch-probability hint made the common `VP8RecordCoeffTokens` statistics increment fall through while outlining rare renormalization. The focused trellis test and all 60 outputs were exact; PNG moved 40.363 to 40.440 ms/image and JPEG 40.227 to 40.528. | Rejected and removed. Both formats regressed; the generated common path was already effective. |
| Branchless token-probability selection | The 58.2%-of-samples token-page loop loaded the indexed probability unconditionally and selected fixed-token probability with a register conditional move. Bit-writer and trellis tests plus all 60 outputs were exact; PNG moved 40.521 to 40.400 ms/image and JPEG 40.362 to 40.188. | Rejected and removed. Gains of 0.121/0.174 ms are far below threshold. |
| Split singleton I4 diagonals | Four one-block dependency diagonals split their ten modes 5/5 across both 128-thread teams with exact global comparison order. Trellis parity and all 60 outputs matched; PNG moved 40.219 to 40.537 ms/image and JPEG 40.263 to 40.525. | Rejected and removed. Cross-team publication outweighed parallel work. |
| Turing lossless backref cost-manager workspace | Native-sm_75 profiling found backrefs at 26.2 ms graphic, 83.3 ms photo, and 121.5 ms texture after forced CUDA transforms/hash. Exact decomposition attributed 72.9% of graphic backrefs to traceback, while cache search owned 48.4% photo and 65.4% texture. Four order-balanced process pairs screened the existing one-allocation `CostManager` workspace: paired median deltas were -0.005 ms graphic, +1.164 ms photo, and -1.305 ms texture. The sampled graphic streams had identical SHA-256 hashes. | Rejected; leave the research implementation default-off. Allocation topology is not a material traceback optimization on the RTX 2080 SUPER, and the only positive cell is below the 1.5 ms/image retention threshold. |
| Turing parallel lossless cache-bit search | Each color-cache bit count has an independent histogram/cache state. One CPU worker per candidate preserves the exact per-candidate recurrence, then the caller applies the original ascending strict-min tie rule. Native-sm_75 four-pair batch A/Bs moved PNG CUDA lossless from 91.820 to 77.319 ms/image and JPEG from 146.558 to 127.644; paired median gains were 14.381 and 19.406 ms/image. All paired hashes matched and a separate 42-case method/quality/content matrix was byte-exact. | Retained for pre-Ampere CUDA only, with the measured Turing gate of at least 8 cache bits and 32,768 reference commands. Ampere+ stays off pending its own evidence; `WEBP_CUDA_PARALLEL_CACHE_SEARCH=0` disables and `=1` forces the structural gate for A/Bs. |
| I16 warp reductions | Four 16-lane groups replaced 64 nonzero atomics and up to 128 64-bit metric atomics. Trellis parity and all 60 outputs matched; PNG moved 40.283 to 39.850 ms/image and JPEG 40.405 to 39.870. | Rejected alone. Exact gains of 0.433/0.535 ms are below threshold; later composition also failed the native aggregate gate. |
| Cooperative I16 forward transforms | All 256 CTA lanes evaluated the 64 transforms in exact four-lane groups without raising shared memory or occupancy. Trellis parity and all 60 outputs matched; PNG moved 40.309 to 40.374 ms/image and JPEG 40.377 to 40.307. | Rejected and removed as neutral. |
| Cooperative I16 quantization plus reductions | Four-lane basic quantization was combined with exact I16 warp reductions. Trellis parity and all 60 outputs matched; PNG moved 40.271 to 39.840 ms/image and JPEG 40.126 to 39.602. | Rejected and removed. The 0.431/0.525 ms gains show quantization added nothing material. |
| Forced-inline I4 metrics | Scalar 4x4 SSE and Hadamard helpers were forced inline. Exact two-process screens moved PNG 40.323 to 40.316 ms/image and JPEG 40.095 to 40.552. | Rejected and removed; PNG was flat and JPEG regressed. |
| Cooperative I4 metrics | Four-lane groups computed exact per-mode SSE and Hadamard values using expired transform scratch. Trellis parity passed; exact screens moved PNG 40.247 to 40.316 ms/image and JPEG 40.298 to 40.379. | Rejected and removed as neutral. |
| Seeded I4 residual-cost bound | The earliest minimum-base-score mode seeded the exact winner and residual walks unable to beat its nonnegative bound were skipped with original tie behavior. Trellis parity and all 24 outputs matched; PNG regressed 40.891 to 42.457 ms/image and JPEG 40.429 to 42.520. | Rejected and removed. Serial seeding and synchronization cost exceeded pruned walks. |
| Static I4 prediction dispatch | Four leaders called their fixed 2--3 mode routines directly instead of the runtime dispatcher. Trellis parity and all 24 outputs matched; PNG moved 40.414 to 39.608 ms/image and JPEG 40.463 to 39.690. | Rejected alone. Exact 0.806/0.773 ms gains are below threshold. |
| Parallel I4 boundary plus static dispatch | A 13-lane exact boundary gather was combined with static prediction calls. Trellis parity and all 24 outputs matched; PNG moved 40.774 to 40.233 ms/image and JPEG 40.779 to 40.065. | Rejected and removed. Gains of 0.541/0.714 ms stayed below threshold. |
| Static I4 dispatch plus warp-parallel winner publication | Static calls were combined with scalar-only score selection and a 16-lane exact winner copy. Trellis parity and all 24 outputs matched; PNG moved 40.370 to 38.850 ms/image and JPEG 40.441 to 39.103. | Rejected and removed. PNG barely reached 1.520 ms but JPEG gained only 1.338 ms, and an earlier screen put both near 1.36 ms. |
| Packed-shuffle I4 transpose | Two signed 16-bit transform intermediates were packed per register; eight width-four shuffles replaced each shared transpose and inner warp barrier, removing 1,280 bytes of scratch. Trellis parity and all 24 outputs matched; PNG regressed 40.446 to 41.096 ms/image and JPEG 40.368 to 41.104. | Rejected and removed. Turing shuffle cost exceeded the shared-memory exchange. |
| Composite I4 dispatch/publication plus I16 reductions | The three independently exact subthreshold changes were combined and tested only on the RTX 2080 SUPER. Two isolated five-process native-sm_75 gates produced a ten-process median of 40.435 to 39.068 ms/image PNG and 40.259 to 38.951 JPEG; all 120 outputs matched. Seven CTests and a 105-case method/quality/tiny/odd/fallback matrix passed. A provisional 180-pair suite also passed but its timing was excluded because that build directory was not configured with `CMAKE_CUDA_ARCHITECTURES=native`. | Rejected and removed. Aggregate native gains of 1.368 ms PNG and 1.309 ms JPEG remain below threshold. No Ampere+ performance claim is made. Raw evidence is linked from the RTX 2080 SUPER machine report. |
| Four-row cooperative I4 prediction | A fresh RTX 2080 SUPER profile put photo/texture I4 at 60.0--61.9% of block cycles. Four aligned lanes then generated one prediction row each while retaining the existing uniform 2--3-mode-per-warp assignment, dependency schedule, and scratch layout. The four focused CUDA tests, including trellis/fallback, passed. Across two order-reversed native-sm_75 processes and six samples per cell, all 24 output hashes and byte counts matched; PNG moved 40.303 to 40.987 ms/image and JPEG 40.231 to 40.894. | Rejected and removed. Cooperative row setup and duplicated boundary arithmetic regressed PNG by 0.684 ms/image and JPEG by 0.664. This is RTX 2080 SUPER-only evidence; no Ampere+ claim is made. |
| Static I4 dispatch/commit plus dynamic-token fall-through | The previously exact static I4 prediction, scalar score scan, and 16-lane winner commit were combined with the exact CPU token probability branch layout that makes the common dynamic lookup fall through. All seven CTests passed. A two-process screen was borderline, so the required native-sm_75 gate was extended to five order-balanced processes and 15 samples per cell; all 60 hashes and byte counts matched. PNG moved 40.246 to 39.283 ms/image and JPEG 40.139 to 39.121. | Rejected and removed. Full-gate gains of 0.962 ms PNG and 1.018 ms JPEG are below the 1.5 ms/image threshold; the earlier two-process 1.599/1.399 ms impression did not survive the larger gate. RTX 2080 SUPER-only, with no Ampere+ claim. |
| Arithmetic token-range normalization | A fresh retained-head texture profile attributed 60.10% of CPU samples to `VP8PutTokenPage` and 36.26% to coefficient-token recording. On GCC/Clang, an exact `clz(range + 1)` calculation replaced both normalization-table loads in the page loop; other compilers retained the tables. Disassembly confirmed `bsr` and shifts replaced both loads, and bit-writer plus trellis/fallback tests passed. Across two order-reversed native-sm_75 processes all 24 output hashes and byte counts matched; PNG moved 40.201 to 40.613 ms/image and JPEG 40.076 to 40.654. | Rejected and removed. The additional integer dependency chain regressed PNG by 0.412 ms/image and JPEG by 0.578; the cache-resident table loads are cheaper. Raw timing and the full sampling experiment are linked from the RTX 2080 SUPER report. |
| Chroma/I16 phase overlap | A new single-threaded wall-stage trace on the retained native-sm_75 build measured CUDA decimation at 20.620/21.727/51.895 ms for graphic/photo/texture, versus token emission at 0.583/2.750/10.959 ms. A scheduling-only candidate used the otherwise idle upper 128 CTA threads to evaluate and select the independent chroma modes while the lower half performed I16 work. All seven CTests passed. Five order-balanced processes and 15 samples per cell were byte-exact; PNG moved 39.973 to 38.574 ms/image and JPEG 40.002 to 38.910. | Rejected and removed. Gains of 1.399 ms PNG and 1.093 ms JPEG are below the 1.5 ms/image retention threshold. This is RTX 2080 SUPER-only evidence; no Ampere+ claim is made. Raw stage and A/B records are linked from the machine report. |
| Static I4 plus chroma-overlap composition | The exact static I4 dispatch/scalar scan/16-lane commit was composed with chroma/I16 overlap. Including the older I16 warp reductions produced 1.603 ms PNG but only 1.332 ms JPEG gains over 15 samples/cell. Removing those reductions avoided shortening the overlapped lower-half path; two independently order-balanced five-process blocks were then combined. All 120 outputs were byte-exact: PNG moved 40.274 to 38.662 ms/image and JPEG 40.250 to 38.763. | Rejected and removed. The combined gain was 1.612 ms PNG but 1.487 ms JPEG, still 0.013 ms below the strict 1.5 ms/image gate. Do not round a borderline single-hardware result into a win. RTX 2080 SUPER only; no Ampere+ claim. |
| Static I4/chroma overlap plus token fall-through | The lean GPU composition was combined with the independently exact CPU dynamic-probability fall-through hint to test whether its prior 0.31 ms JPEG gain would clear the composition's 0.013 ms deficit. All seven CTests passed and all 24 screen outputs were byte-exact. PNG moved 40.288 to 38.421 ms/image, but JPEG moved only 40.188 to 39.034. | Rejected and removed at the screen. The CPU layout reduced the composed JPEG gain to 1.155 ms/image instead of adding to it; do not assume independent microbenchmark gains compose. RTX 2080 SUPER only. |
| Balanced four-warp I4 plus chroma overlap | The lean static-I4/chroma composition was combined with the exact 3/3/2/2 four-warp transform-group layout, eliminating its prediction-to-transform CTA barrier. Ten order-balanced native-sm_75 processes produced 30 samples per cell; all 120 timing outputs matched, all seven CTests passed, and a 105-case method/quality/tiny/odd/band-3-fallback battery was byte-exact. Combined medians moved PNG 40.206 to 38.503 ms/image and JPEG 40.122 to 38.633. | Rejected and removed. PNG gained 1.703 ms/image, but JPEG gained only 1.489 ms/image, 0.011 ms below the strict gate. This is RTX 2080 SUPER-only evidence and makes no Ampere+ claim. Raw timing and parity ledgers are linked from the machine report. |
| Team-local I4 barriers plus chroma overlap | The lean static-I4/chroma composition was combined with the exact team-local named-barrier schedule. Four independent numeric barriers used one 128-thread barrier per I4 team; winner publication and raster-order abort stayed CTA-wide. All seven CTests and all 24 screen outputs were exact. Two order-reversed native-sm_75 processes moved PNG 40.341 to 38.356 ms/image and JPEG 40.213 to 38.815. | Rejected and removed at the screen. PNG gained 1.984 ms/image, but JPEG gained only 1.398 ms/image; the independently positive barrier result did not compose. RTX 2080 SUPER only, with no Ampere+ claim. |
| Parallel I4 boundary plus static dispatch/commit | The exact 13-lane boundary gather was combined with static prediction calls, scalar-only winner selection, and a 16-lane winner copy. All seven CTests and all 24 screen outputs were exact. Two order-reversed native-sm_75 processes moved PNG 40.374 to 39.817 ms/image and JPEG 40.365 to 39.129. | Rejected and removed at the screen. Gains of 0.557 ms PNG and 1.236 ms JPEG are below threshold; the standalone boundary signal was absorbed by the broader schedule. RTX 2080 SUPER only. |
| Warp-argmin I4 selection plus static dispatch/commit | A refreshed retained phase trace put I4 at 63.5% of photo and 65.4% of texture block cycles. Since every full mode score is its base score plus non-negative residual cost, the ordered early-out scan is exactly the earliest minimum full score. Warp 0 reduced that argmin and used the validated static dispatch/16-lane commit. All seven CTests and all 24 outputs were exact; PNG moved 40.112 to 38.871 ms/image and JPEG 40.027 to 39.203. | Rejected and removed at the screen. Shuffle reduction overhead left gains of 1.241 ms PNG and 0.824 ms JPEG, below threshold. RTX 2080 SUPER only. |
| Partition0/token-emission overlap | Once final probabilities and filter strength were available, VP8 partition 0 (headers and intra modes) was generated on the caller while all eight independent token partitions emitted on workers. An environment-off arm restored the prior schedule in the same native-sm_75 binary. Across two order-reversed six-image processes and six samples per cell, all 24 aggregate hashes and byte counts matched; the PPM-fed lossy corpus moved from 32.301 to 31.228 ms/image. | Rejected and removed at the screen. The 1.073 ms/image host-schedule gain is below the strict 1.5 ms/image retention threshold. All seven CTests passed. RTX 2080 SUPER only; raw rows are linked from the machine report. |
| Singleton-I4/chroma overlap | Chroma transform, error correction, quantization/reconstruction/SSE, and residual-cost stages were placed on the otherwise idle upper 128-thread team during the four singleton I4 diagonals; an early I4 abort completed only the remaining stages afterward. All seven CTests passed and all 24 aggregate hashes and byte counts matched. Two order-reversed native-sm_75 processes moved the six-image PPM-fed lossy corpus from 32.340 to 31.829 ms/image. | Rejected and removed at the screen. The exact 0.510 ms/image gain is far below the 1.5 ms/image retention threshold: the singleton windows hide only part of the chroma critical path. RTX 2080 SUPER only; raw rows are linked from the machine report. |
| Method-4 cached/no-cache traceback overlap | A worker candidate overlapped the two independent traceback variants while retaining their original descending reduction and strict comparisons. Four order-balanced native-sm_75 process pairs were byte-identical, but method 4 never requests the no-cache alternative: PNG changed by -0.281 ms/image and JPEG by +0.259 ms/image at the paired median, both noise. | Rejected and removed. The target method cannot dispatch the candidate (`do_no_cache` is limited to method 5 at quality >=75 or method 6 at quality 100); do not carry an inactive policy path. RTX 2080 SUPER only. |
| Turing forced histogram-counter diagnostic | The benchmark-only force path launches eight histogram counts per method-4 encode. Verified verbose profiling observed 504 launches; kernels averaged 0.179 ms, while the complete entropy-clustering stage remained 19--22 ms. Four order-balanced on/off process pairs per content changed total time by -0.670 ms graphic, +11.037 ms photo, and -4.646 ms texture at paired medians; the histogram-stage time itself was essentially unchanged. | No production or Ampere+ change. Counting is not the stage bottleneck, and the opposed surrounding-cache effects do not support a shared Turing force policy. Keep the production histogram default off. |
| Turing cache-search worker reuse | Ten cache-bit worker threads were kept alive across cache searches within one backward-reference call, preserving every recurrence and reduction. Four order-balanced native-sm_75 batch pairs remained byte-identical. PNG gained 0.714 ms/image, but JPEG regressed 1.456 ms/image at paired medians. | Rejected and removed. Thread creation is not a two-format bottleneck; idle workers compete with surrounding JPEG CPU work. The retained cache search continues to end workers after each search. |
| Turing parallel raw-histogram cost analysis | The independent `ComputeHistogramCost` calls for up to 30,000 raw tiles were split over 12 CPU jobs before unchanged serial compaction, clustering, and remapping. Four order-balanced forced-batch pairs retained exact hashes, but PNG changed by -0.143 ms/image and JPEG by -0.471 ms/image at paired medians. | Rejected and removed. Worker startup exceeds the initial cost phase; the 19--22 ms histogram boundary is dominated by later serial clustering/remapping. No Ampere+ change. |
| Turing traceback command-append inlining | A 0.530-second user-space sample attributed 20.75% inclusive CPU time to `VP8LBackwardReferencesTraceBackwards` and 11.32% exclusive time to `VP8LBackwardRefsCursorAdd`. Four exact implementations inlined the common within-block append and varied how a pre-Ampere gate isolated it. The unconditional prototype initially gained 2.184 ms/image PNG and 3.052 JPEG, but a four-pair CPU control regressed JPEG by 10.782 ms/image. Three architecture-safe reruns kept PNG gains of 1.630--1.859 ms/image but regressed JPEG by 2.463--2.658 ms/image. Every aggregate hash and byte count matched. | Rejected and removed. The apparent first JPEG win was not stable under path isolation, while every architecture-safe form lost on JPEG. Keep the original opaque append function and do not infer an Ampere+ result. Raw sampling reports and all 84 A/B transcripts are archived with the RTX 2080 SUPER report. |
| AVX2 combined-entropy equal-run scan | Eight combined histogram bins were added and compared in parallel; uniform blocks skipped the unchanged ordered scalar streak updates. Two order-balanced native-sm_75 process pairs were byte-exact. Applying AVX2 to every alphabet changed PNG by -0.418 ms/image and JPEG by +2.561. Restricting it to the extended literal alphabet changed PNG by +0.111 and JPEG by +1.125. | Rejected and removed. Fixed-alphabet vector setup regresses PNG, while the exact literal-only form is below the 1.5 ms/image retention threshold in both formats. This is Ryzen 9 3900X / RTX 2080 SUPER evidence only; no Ampere+ claim. |
| Turing CUDA hash compile-switch screen | A 60-sample native-sm_75 profile (six images/sample) collected 2.862 CPU seconds and put `VP8LHashChainFill` at only 0.180 seconds exclusive, confirming that the 17--27 ms hash boundary is primarily kernel/transfer work. Three existing kernel switches were rebuilt independently and screened in two order-balanced forced-batch pairs per format. Moving 128 to 256 threads regressed PNG/JPEG by 0.410/0.793 ms per image; removing four-pixel match unrolling regressed by 0.820/1.249 ms; removing read-only-cache loads changed them by -0.296/+0.206 ms. Every aggregate hash and byte count matched. | Rejected with no source change. Retain 128-thread blocks, four-pixel unrolling, and `__ldg` loads. None improves either format by the 1.5 ms/image gate, and no Ampere+ behavior or claim changes. Raw profiles, native caches, and 24 timing transcripts are archived with the RTX 2080 SUPER report. |
| Turing hash initial-pixel precheck removal | The chain-candidate path requests a match from length zero, so `HashMatchLength` checked pixel zero once in its precheck and immediately again in its four-pixel loop. An architecture-specialized kernel removed only that duplicate pair of reads on pre-Ampere while preserving the established Ampere+ specialization. Static sm_75 resources fell from 26 to 24 registers with no stack/shared/local memory. Five order-balanced forced-batch processes were exact; PNG moved 77.390 to 76.376 ms/image with a +1.013 ms paired gain, while JPEG moved 127.794 to 126.187 with +1.881 ms. | Rejected and removed. PNG's five-process paired median remains below the 1.5 ms/image gate despite JPEG's win. Do not retain a format-selective Turing result or alter Ampere+ without evidence. The exact patch, all 20 process transcripts, CTest log, SASS/resource reports, native caches, and Nsight permission failure are archived. |
| Turing hash four-pixel load-ahead | Baseline sm_75 SASS issued one pixel pair, compared it, and branched before issuing the next pair. A pre-Ampere specialization loaded all four safe in-bounds pixel pairs before retaining the same ordered comparisons; Ampere+ used a false specialization whose complete 296-instruction mnemonic stream matched the original. Seven CTests passed and five order-balanced forced-batch processes were exact. PNG moved 77.490 to 76.191 ms/image with a +1.395 ms paired gain; JPEG moved 128.278 to 126.760 with +1.851 ms. The Turing kernel rose from 26 to 32 registers. | Rejected and removed. The independent load-ahead win remains below the 1.5 ms/image gate on PNG. Preserve its exact validation for a separately gated composition, but do not retain it alone or infer an Ampere+ result. The exact patch, 20 timing transcripts, SASS/mnemonic comparisons, resource reports, CTest log, and native caches are archived. |
| Combined pre-Ampere hash matcher | Composed the two exact hash-loop candidates above: full-chain calls omit the duplicated zero-offset precheck and issue each safe four-pixel load group before the original ordered comparisons. A preliminary ten-pair run gained 1.932 ms/image PNG and 1.844 JPEG, but the required ten-pair final-build repeat gained only 1.184 PNG while gaining 2.203 JPEG. Every aggregate hash and byte count matched. The Turing specialization used 30 registers; the Ampere+ specialization retained the original 26-register, 296-instruction stream. | Rejected and removed. The final PNG result is below the 1.5 ms/image gate. This is RTX 2080 SUPER-only evidence; no Ampere+ behavior or performance claim changes. Both complete screens, the exact patch, SASS, resources, and correctness logs are archived. |
| Predictor-to-hash resident coherency | The public encoder test exposed a pre-existing decoded-pixel mismatch when CUDA predictor and hash were enabled while cross-color remained on CPU. Predictor had published pre-color residuals as resident; CPU cross-color could then rewrite the host buffer, and hash consumed the stale device copy. A new hash-ready state lets predictor output feed CUDA color but requires color to republish before hash reuse. With CUDA color disabled, hash uploads the CPU's final residuals. | Retained. The default and six-corpus public encoder suites pass, including the new no-color regression; 7/7 CTests, the default/baseline/all-disabled variant matrix, and all 180 official validation pairs pass. The cold-decline test now disables the intentional process-start prewarm, its full forced path explicitly opts into cross-color, and the variant's full-feature arm explicitly enables the otherwise default-off histogram stage it requires. This is a correctness fix; no cross-architecture speed claim is made. |
| Turing inline token-recording recheck | A retained-head profile found texture-medium at 79.09 ms, including 52.14 ms in accelerated decimation/collect/replay and 14.37 ms in token emission; its device wall was only 21.89 ms, so the recorder worker was rechecked. Five order-balanced native-sm_75 process pairs used the same PNG or JPEG corpus on both arms. Disabling the worker moved PNG 40.208 to 39.655 ms/image and JPEG 40.403 to 39.878 at process medians; paired gains were 0.553 and 0.373 ms. All rows retained the expected aggregate hashes. | Rejected with no source change. Both gains are far below 1.5 ms/image, so the measured Ampere+ pipeline default remains shared. A preliminary 8.8 ms impression compared PPM candidate input with PNG baseline input and is not valid evidence; the like-for-like PPM control was 32.362 versus 31.731 ms/image. RTX 2080 SUPER only. |
| Pre-Ampere static-I4/inline-recording composition | The independently exact static I4 prediction dispatch and 16-lane winner publication were reconstructed behind a pre-Ampere compile branch and composed with inline token recording. Two order-reversed native-sm_75 processes with six measured samples per cell retained the PNG/JPEG aggregate hashes. Pooled medians moved PNG 40.436 to 39.008 ms/image and JPEG 40.375 to 39.120. | Rejected and removed at the screen. Gains of 1.427 ms PNG and 1.255 ms JPEG remain below the strict 1.5 ms/image gate. No Ampere+ result is inferred; the exact rejected patch, 48 raw timing rows, and both native build caches are archived. |
| Turing warp-helper call elimination | Native-sm_75 SASS showed that the decimate kernel's synchronized ballots/shuffles expand to 206 out-of-line `CALL.REL.NOINC` sites. Inline PTX wrappers compiled, but ptxas retained exactly 206 calls; resources changed only from 103 to 102 registers with the same 352-byte stack and 23,392-byte shared allocation. Two order-reversed six-sample screens moved PNG 40.013 to 40.227 ms/image and JPEG 40.002 to 40.094, while both candidate hashes and byte counts differed. Rebuilding the restored source in the same cache reproduced the parent's exact bytes. CUDA 12 also rejects the legacy `__shfl*` intrinsics for native sm_75. | Rejected and removed for correctness and performance. Do not bypass synchronized warp semantics on Turing; the retained compiler-generated helpers are required by the current implementation. No Ampere+ source or claim changes. Complete SASS, resources, native caches, compiler failure, clean-rebuild control, and all 48 timing rows are archived. |
| Pre-Ampere RD-level kernel specialization | Line-info ptxas profiling proved that the monolithic kernel's 352-byte frame contains no spills and maps to trellis state unused by method 4. Compile-time RD specialization reduced the basic-search kernel from 103 registers/352-byte frame to 67 registers/no frame; method 5 and 6 became 100/272 and 94/272. All seven CTests passed and all 48 aggregate outputs were byte-exact. Two order-reversed six-sample screens moved PNG 40.147 to 39.946 ms/image and JPEG 40.201 to 39.789. | Rejected and removed. Gains of 0.200 ms PNG and 0.412 ms JPEG are below threshold. With 256 threads, both register counts permit two CTAs, while 23,392 shared bytes/CTA cap Turing residency at two (three require 70,176 bytes), so specialization does not increase occupancy. No Ampere+ claim or source change remains. Exact patch, SASS/resources, native cache, CTest log, and raw timing are archived. |
| Turing 16-band decimate streaming | The retained profile's collection/replay gap and the prior Turing 4-to-8-band result motivated doubling the streaming bands. With backend event capacity extended from 8 to 16, two order-reversed six-sample processes kept all 48 hashes/byte counts exact and moved PNG 40.185 to 39.973 ms/image and JPEG 40.317 to 39.876. A separate unsupported-request screen confirmed that asking the production eight-event backend for 16 bands safely declined to exact CPU fallback. | Rejected and removed. Valid gains of 0.211 ms PNG and 0.441 ms JPEG are below 1.5 ms/image. Keep the shared eight-band default and backend cap; no Ampere+ value or behavior changes. The exact patch, native cache, valid timing, fallback timing, and summary are archived. |
| Cold token-page growth outlining | A fresh native-sm_75 whole-process profile attributed 2.402 of 5.164 sampled CPU seconds (46.51%) to `VP8RecordCoeffTokens`. Its generated body was 4,976 bytes because the rare page-allocation path was duplicated at every inlined token site. A portable no-inline annotation reduced it to 3,644 bytes plus a 95-byte helper; 7/7 CTests and all 48 recorded outputs were exact. Two order-reversed six-sample processes moved PNG 40.221 to 40.111 ms/image and JPEG 40.170 to 40.164. | Rejected and removed. Gains of 0.110 ms PNG and 0.006 ms JPEG are far below 1.5 ms/image; the duplicated cold code is not a material instruction-cache bottleneck. RTX 2080 SUPER only. The full 104 MiB sampling experiment (compressed), exact patch, disassemblies, caches, tests, and raw timings are archived. |
| Precomputed coefficient-token band offsets | Coverage of the profiled token recorder counted 117.4 million coefficient iterations: 40.0% zero, 28.9% magnitude one, and only 0.16% above ten. Retained sm_75 assembly recomputed `band * 33` separately for token IDs and statistics pointers at every context transition. A 17-entry exact offset table replaced both chains with one 16-bit load; generated size fell 4,976 to 4,944 bytes, 7/7 CTests passed, and all 48 timing outputs were exact. PNG moved 40.240 to 40.356 ms/image; JPEG moved 40.321 to 39.851. | Rejected and removed. PNG regressed 0.116 ms/image and JPEG's 0.471 ms gain is below 1.5 ms/image. The cache-resident lookup does not provide a two-format material win and duplicates `VP8EncBands` policy. RTX 2080 SUPER only; no Ampere+ claim. Raw `.gcda`/`.gcno`, annotated coverage, exact patch, disassemblies, caches, tests, and timings are archived. |
| Fixed-bit coefficient-token prefix | The coverage profile showed zero and magnitude-one coefficients comprise 68.9% of loop iterations. A branch-first coding tree passed constant 0/1 values into the first two `AddToken` sites, removing duplicated `setcc`, shift, and dependent bit-add instructions from each selected path while preserving token/statistics order and allocation failure. All 7 CTests and 48 timing outputs were exact, but generated size rose 4,976 to 5,344 bytes. PNG moved 40.260 to 40.920 ms/image and JPEG 40.036 to 40.589. | Rejected and removed. Duplicated page/statistics paths increased code by 368 bytes and regressed PNG/JPEG by 0.660/0.554 ms/image. Keep the compact dynamic-bit form. RTX 2080 SUPER only; no Ampere+ claim. Exact patch, disassemblies, caches, tests, and raw timings are archived. |
| No-run token-byte fast flush | Coverage of 441.5 million coded tokens observed 36.43 million real byte flushes; 99.62% had no pending `0xff` run, and only 768 needed buffer growth. A direct `run == 0 && pos < max_pos` arm skipped pending-capacity arithmetic and the later run branch while preserving the existing run/resize path. It shrank `VP8PutTokenPage` from 764 to 719 bytes; 7/7 CTests and all 48 outputs were exact. PNG moved 40.144 to 40.213 ms/image and JPEG 40.027 to 40.105. | Rejected and removed. Despite the skew and smaller code, PNG/JPEG regressed 0.069/0.078 ms/image. The compiler already overlaps the pending-capacity work effectively. RTX 2080 SUPER only; no Ampere+ claim. Raw coverage, exact patch, disassemblies, caches, tests, and timings are archived. |

All original and follow-up benchmark rows produced stable expected checksums.
The historical color rows remain raw evidence, but their ratios are not matched
comparisons because the baseline transferred and reduced different data. The
active lab now separates that histogram-throughput case and gives the matched
baseline a device reduction plus the same score transfer as the shared-tile
case. Rejected implementations remain removed.

The matched CPU-control follow-ups used 20 setup-inclusive iterations in each
of five fresh runs. Predictor, SharpYUV, near-lossless, histogram, and lossy
scoring GPU medians above use the same work and checksum as their paired CPU
cases. These ratios justify continued integration work, but only near-lossless
currently reproduces the complete production algorithm.

## Production shared-tile follow-up

The first production port reserved a fixed 16 KiB shared tile. It regressed the
real color kernel from about 2.31 ms to 4.58 ms at 1024x1024 and was discarded.
Allocating only the actual tile size (normally 4 KiB at method 4) recovered
occupancy and produced the retained result:

| Size | Existing kernel median | Dynamic shared-tile median | Kernel change |
|---:|---:|---:|---:|
| 1024x1024 | 2.347 ms | 2.163 ms | 7.8% faster |
| 2048x2048 | 8.217 ms | 7.551 ms | 8.1% faster |

Each cell contains 35 warm kernel samples across five deterministic inputs.
Encoded hashes were identical between builds for every matched sample. Median
1024x1024 checks at methods 2 and 6 also improved the kernel by 8.0% and 2.1%,
respectively; method 0 did not dispatch the color stage for this workload.
Median paired full-encode results were 0.9% slower at 1024x1024 and 2.6% slower
at 2048x2048, with large CPU-side variance and a color-kernel share below 1% of
the full encode. Therefore the evidence supports a kernel improvement but does
not claim a measurable end-to-end gain or justify changing crossover
thresholds.

The optimization is independently removable with
`WEBP_CUDA_ENABLE_COLOR_SHARED_TILE=OFF`.

## Production near-lossless follow-up

The exact implementation passed 20 direct CPU/CUDA parity cases spanning all
five pass counts, varied dimensions, non-contiguous source strides, repeat
determinism, and transactional decline. All 1,560 benchmark rows retained
matched output hashes.

The public encoder call site was also exercised with the deterministic
3000x2000 texture corpus at five passes. CUDA dispatch occurred and the CPU and
CUDA encoders produced byte-identical WebP output.

Warm CUDA won every measured case. The retained 256x256 minimum avoids the
noise-level 64x64 one-pass result; measured speedups there were 23.45x for five
passes, 14.93x for three passes, and 4.24x for one pass. At 4096x4096 the warm
speedups were 13.70x, 8.35x, and 2.65x, respectively.

Cold initialization invalidated the original quality-blind 4-million-pixel
proposal. At 2048x2048 only five passes barely won (1.09x). At 4096x4096, five
and three passes won by 2.99x and 1.83x, while one pass was still 1.76x slower.
The retained default requires 16,777,216 pixels and at least three passes when
the backend is cold. An explicit `WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS` value
remains a force/ablation override for every pass count.

## Persistent CUDA batch follow-up

The batch benchmark measured six PNG or JPEG inputs (three content types at
small and medium sizes), quality 75, method 4, and near-lossless 40. These
are persistent-process, forced-stage runs with page-cached `/tmp` file I/O;
they do not justify lowering production cold thresholds.

| Format | Mode | Batch 6 CPU/CUDA total ms | Batch 6 speedup | Batch 24 CPU/CUDA total ms | Batch 24 speedup |
|---|---|---:|---:|---:|---:|
| PNG | lossy | 602.791 / 614.401 | 0.9811x | 2445.182 / 2477.368 | 0.9870x |
| PNG | lossless | 847.751 / 619.866 | 1.3676x | 3389.177 / 2460.732 | 1.3773x |
| PNG | near-lossless | 1246.506 / 965.494 | 1.2911x | 4869.623 / 3911.262 | 1.2450x |
| JPEG | lossy | 619.277 / 613.559 | 1.0093x | 2433.595 / 2405.487 | 1.0117x |
| JPEG | lossless | 3988.384 / 3535.765 | 1.1280x | 16023.908 / 14449.061 | 1.1090x |
| JPEG | near-lossless | 4820.437 / 4241.282 | 1.1366x | 18673.450 / 16503.490 | 1.1315x |

CUDA is worthwhile for persistent lossless and near-lossless batches; lossy
is effectively neutral. Batch sizes 6 and 24 have no material per-image
throughput difference after warmup. Fresh per-image CUDA processes lost to CPU
because each launch paid CUDA initialization:

| Format | Mode | Fresh CPU/CUDA six-process median ms | Speedup |
|---|---|---:|---:|
| PNG | lossy | 645.322 / 1880.912 | 0.3431x |
| PNG | lossless | 948.875 / 2101.623 | 0.4515x |
| PNG | near-lossless | 2134.368 / 3158.435 | 0.6758x |
| JPEG | lossy | 648.090 / 1865.276 | 0.3475x |
| JPEG | lossless | 4388.008 / 5253.948 | 0.8352x |
| JPEG | near-lossless | 3323.956 / 5163.455 | 0.6437x |

All 120 persistent rows and 360 fresh rows were stable; all 180 fresh
validation pairs passed decoded parity, including 60/60 exact lossy outputs.
The complete raw rows and validation records are in
`CUDA_BATCH_RESULTS_RAW.md`.

Production action: lossy RGB-to-YUV CUDA is now opt-in through
`WEBP_CUDA_LOSSY=1`. One-shot encodes retain cold thresholds. Persistent
lossless callers may advertise `WEBP_CUDA_BATCH_SIZE` and
`WEBP_CUDA_BATCH_PIXELS`; conservative defaults require 6 images and
6,000,000 pixels for lossless or 5 images and 5,000,000 pixels for
near-lossless before the first item may use warm dispatch thresholds. The
portable `scripts/benchmark_cuda_end_to_end.py` suite reproduces this
PNG/JPEG matrix on other systems and emits `raw.jsonl`, `results.json`, and
the four-column human-readable `report.md`.

## Evidence locations

- `CUDA_EXPERIMENT_RESULTS_RAW.md`: original 75-row capture plus matched
  lifecycle and stage-control follow-ups.
- `CUDA_NEAR_LOSSLESS_RESULTS_RAW.md`: 1,560 direct production rows plus warm
  and cold crossover medians.
- `CUDA_ACCELERATION_EXPERIMENTS.md`: active lab build and measurement protocol.
- `CUDA_BENCHMARK_RESULTS.md`: production encoder crossover and strategy context.
- `CUDA_BATCH_RESULTS_RAW.md`: persistent and fresh-process batch rows,
  validation records, and computed medians.
- `scripts/benchmark_cuda_end_to_end.py`: portable cross-system runner and
  report generator for the same PNG/JPEG lifecycle matrix.

## Pre-Ampere deferred basic-I4 reconstruction-copy rejection

A refreshed native-sm_75 device trace kept I4 at 63.2% of photo and 64.8% of
texture block cycles. A temporary counter probe found the fixed 211-bit I4
entry cost never rejected a macroblock before the first 4x4 block, but I4 was
ultimately accepted for every representative texture macroblock and about
half of photo macroblocks. The candidate therefore left accepted method-4
luma pixels in the completed I4 scratch plane and selected that plane at the
final reconstruction write, avoiding a redundant 256-byte shared-memory copy.
It was compile-time restricted to pre-Ampere; trellis modes and Ampere+
retained the parent path.

The first prototype incorrectly skipped coefficient-level publication along
with the pixels; the aggregate parity gate caught different hashes and byte
counts, and those timings were discarded. The corrected candidate always
published the exact winning levels. Seven CTests passed and all 48 corrected
A/B rows were byte-exact:

| Format | Parent | Deferred pixel copy | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.440 ms/image | 40.361 ms/image | 0.079 ms/image |
| JPEG lossy | 40.287 ms/image | 40.330 ms/image | -0.043 ms/image |

The candidate was removed because it is neutral-to-negative and far below the
1.5 ms/image threshold. Raw phase traces, abort counters, the invalid and
corrected screens, exact patch, native cache, resource/SASS reports, binary
hashes, and restored-parent CTest log are stored under the
`i4-deferred-copy-*` prefix in the RTX 2080 SUPER evidence directory. This is
Turing-only performance evidence and makes no Ampere+ claim.

## I16 lazy residual-cost pruning feasibility rejection

The refreshed graphic profile put I16 selection at 25.2% of retained block
cycles. A temporary exact counter probe simulated evaluating mode 0 first and
skipping later residual-cost walks whenever their non-negative-cost base score
could not beat the best full score under the original ordered tie rule.

Photo and texture skipped none of four mode walks. Graphic-small needed 3,262
of 4,096 walks (20.36% pruned); graphic-medium needed 14,757 of 30,000
(50.81% pruned). Even assigning the entire instrumented graphic I16-selection
interval to residual walks and scaling it perfectly by those prune fractions
yields only a 0.80 ms/image six-image-suite ceiling. Actual savings must be
smaller because fixed selection work remains and a lazy implementation adds a
mode-0 dependency.

No candidate was implemented because its optimistic ceiling is already below
the 1.5 ms/image gate. The probe was removed and the retained build passed all
seven CTests. Exact counters, probe patch, and restored-parent test log are
stored under `i16-lazy-prune-*` in the RTX 2080 SUPER evidence directory. This
is Turing-only evidence and makes no Ampere+ claim.

## Pre-Ampere two-pixel grouped hash-matcher rejection

A retained forced-lossless refresh still measured material hash-candidate
kernels at about 7.5 and 10.9 ms. The prior four-pixel load-ahead result gained
1.395/1.851 ms per PNG/JPEG image but used 32 Turing registers, so a midpoint
candidate grouped two pixel pairs at a time and composed the independently
exact duplicate-precheck removal. It was selected only on pre-Ampere.

The new Turing specialization stayed at the parent's 26 registers and reduced
the hash kernel's mnemonic count from 296 to 288. The Ampere+ false
specialization retained 296 instructions with a mnemonic stream identical to
the parent. Seven CTests passed and all 48 screen records were byte-exact:

| Format | Parent | Two-pixel matcher | Gain |
|---|---:|---:|---:|
| PNG lossless | 77.101 ms/image | 76.102 ms/image | 0.999 ms/image |
| JPEG lossless | 128.924 ms/image | 123.830 ms/image | 5.094 ms/image |

The candidate was removed because the PNG gain is below the 1.5 ms/image gate
despite the large JPEG win. Raw profile output, exact patch, all timing rows,
resources, SASS and false-specialization comparison, binary hashes, native
cache, and restored-parent CTest log are stored under `libwebp-hash-pair-*` in
the RTX 2080 SUPER evidence directory. No Ampere+ performance claim is made.

## Pre-Ampere hash-chain next-link prefetch rejection

The next isolated hash-candidate dependency was the chain-link load. A
pre-Ampere-only candidate issued that load at the top of the loop so it could
overlap the pixel rejection and match scan; Ampere+ retained a separately
compiled parent specialization. Both candidate specializations stayed at 26
registers and 296 mnemonic instructions, and the Ampere+ mnemonic stream was
identical to the parent.

Seven CTests passed and all 48 native-sm_75 timing rows retained exact hashes
and byte counts:

| Format | Parent | Link prefetch | Gain |
|---|---:|---:|---:|
| PNG lossless | 77.035 ms/image | 77.694 ms/image | -0.659 ms/image |
| JPEG lossless | 130.080 ms/image | 128.167 ms/image | 1.913 ms/image |

The candidate was removed because PNG regressed. The exact patch, raw timing
rows, profile, resources, compressed SASS, specialization comparison, binary
hashes, native cache, and candidate/restored CTest logs are stored under
`libwebp-hash-link-prefetch-*` in the RTX 2080 SUPER evidence directory. This
is Turing-only performance evidence and makes no Ampere+ claim.

## Pre-Ampere four-pixel mismatch-mask rejection

A fresh explicit-native profile measured the material hash calls at 7.557 ms
for 1.92 MP resident pixels and 10.891 ms for 0.96 MP non-resident pixels. A
Turing specialization composed the proven duplicate-precheck removal with a
four-bit mismatch mask, replacing four divergent early returns per unrolled
group with one first-set-bit result. Ampere+ retained a specialization whose
296-instruction mnemonic stream exactly matched the parent.

Both candidate and restored trees passed seven CTests. All 48 timing rows were
byte-exact:

| Format | Parent | Mismatch mask | Gain |
|---|---:|---:|---:|
| PNG lossless | 75.827 ms/image | 74.587 ms/image | 1.239 ms/image |
| JPEG lossless | 127.713 ms/image | 123.393 ms/image | 4.319 ms/image |

The pre-Ampere kernel rose from 26 to 34 registers. The candidate was removed
because PNG remained below 1.5 ms/image. Profile output, exact patch, timing
rows, resources, compressed SASS, specialization comparison, binary hashes,
native cache, and both CTest logs are under `libwebp-hash-mask-*` in the RTX
2080 SUPER evidence directory. No Ampere+ performance claim is made.

## Pre-Ampere warp-private I4 boundary rejection

Fresh native-sm_75 end-to-end medians were 41.061 ms/image PNG and 39.555
JPEG, while medium device walls remained about 22--26 ms and I4 accounted for
63--65% of photo/texture block cycles. To remove the first CTA barrier from
each I4 dependency diagonal, a Turing-only candidate gave all four prediction
warp leaders their own exact 13-byte boundary. Each leader gathered and
immediately consumed its copy; Ampere+ retained the parent code.

Both candidate and restored trees passed seven CTests. All 24 screen rows were
byte-exact:

| Format | Parent | Private boundaries | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.888 ms/image | 39.720 ms/image | 0.167 ms/image |
| JPEG lossy | 39.405 ms/image | 39.681 ms/image | -0.276 ms/image |

Registers and stack stayed at 103 and 352 bytes; shared memory rose from
23,392 to 23,464 bytes. The candidate was removed because PNG is far below
1.5 ms/image and JPEG regresses. The retained profile, phase traces, exact
patch, rows, SASS/resources, binary hashes, native cache, and both CTest logs
are under `libwebp-i4-private-boundary-*` in the RTX 2080 SUPER evidence
directory. No Ampere+ performance claim is made.

## Refreshed partition0/token-emission overlap rejection

The retained texture stage profile still showed 7.34 ms/image in lossy write,
so the exact earlier host schedule was recovered and screened on the current
native-sm_75 binary with the actual PNG and JPEG inputs. It finalized filter
strength, launched all eight token partitions on workers, and generated
partition 0 on the caller. `WEBP_PARTITION0_PIPELINE=0` supplied a same-binary
parent.

Candidate and restored trees passed 7/7 CTests. All 24 order-reversed rows
matched hashes and byte counts:

| Format | Parent | Partition0 overlap | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.775 ms/image | 38.559 ms/image | 1.216 ms/image |
| JPEG lossy | 39.286 ms/image | 38.885 ms/image | 0.401 ms/image |

Both gains miss the strict 1.5 ms/image gate, and JPEG rules out using this
host schedule to rescue the borderline Turing GPU composition. The candidate
was removed. Raw rows are archived as
`libwebp-partition0-current-formats-screen.jsonl` with the RTX 2080 SUPER
machine report. No Ampere+ performance claim is made.

## Pre-Ampere fused I4 coefficient handoff rejection

A fresh 48-image JPEG sampling profile attributed only 0.050 seconds
inclusive to `ReadJPEG` (about 1.04 ms/image), bounding input decode below the
retention gate. The still-actionable retained subphase profile assigns
25.6--26.5% of I4 cycles to transform/quantization. A Turing-only candidate
therefore kept each four-lane mode group's transformed coefficient column in
registers through basic quantization and inverse-transform setup. It removed
two warp synchronizations and the shared coefficient publish/reload while
preserving the exact zigzag levels and arithmetic. An omitted non-zero publish
was caught before timing; the corrected candidate and restored tree both
passed 7/7 CTests.

All 24 corrected screen rows matched hashes and byte counts:

| Format | Parent | Fused handoff | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.641 ms/image | 38.986 ms/image | 0.655 ms/image |
| JPEG lossy | 39.426 ms/image | 39.168 ms/image | 0.258 ms/image |

The candidate reduced the kernel from 103 to 98 registers but both gains are
far below 1.5 ms/image, so it was removed. Raw profile, exact corrected patch,
timings, resources, binary hashes, and both CTest logs are archived under the
`libwebp-i4-fused-register-*` and `libwebp-jpeg-decode-feasibility-*`
prefixes. RTX 2080 SUPER only; no Ampere+ behavior or performance claim.

## Pre-Ampere shared segment-matrix staging rejection

The retained transform/quantization profile motivated staging the selected
716-byte immutable segment bundle (three quantization matrices and lambdas)
in shared memory. Threads copied it alongside source import, so the existing
setup barrier absorbed publication and no synchronization was added. The
pre-Ampere-only candidate and restored tree both passed 7/7 CTests, and all
24 order-reversed timing rows matched hashes and byte counts:

| Format | Parent | Shared segment | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.637 ms/image | 39.596 ms/image | 0.041 ms/image |
| JPEG lossy | 39.621 ms/image | 39.417 ms/image | 0.204 ms/image |

Registers fell from 103 to 92 while shared memory rose from 23,392 to 24,104
bytes, but both timing changes are noise. The candidate was removed: segment
data was already cache-resident, and quantization remains arithmetic-bound.
Raw patch, rows, resources, binary hashes, and both CTest logs are archived
under `libwebp-decimate-shared-segment-*`. RTX 2080 SUPER only; no Ampere+
behavior or performance claim.

## Balanced-I4/chroma plus shared-segment composition rejection

The retained wall-stage profile still identified decimation as the dominant
serial cost. The exact balanced four-warp I4/chroma schedule had previously
missed the JPEG gate by 0.011 ms/image, so it was composed with the separately
exact shared-segment candidate, whose prior JPEG screen gained 0.204
ms/image. This tested whether the two validated schedules composed without
introducing another unvalidated idea.

The local native-sm_75 candidate and restored tree both passed 7/7 CTests,
and all 24 order-reversed timing rows matched hashes and byte counts:

| Format | Parent | Composition | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.699 ms/image | 37.664 ms/image | 2.035 ms/image |
| JPEG lossy | 39.555 ms/image | 38.198 ms/image | 1.356 ms/image |

JPEG remained below the strict 1.5 ms/image gate, demonstrating again that
independent micro-gains do not add reliably. The composition was removed.
Its exact patch, rows, and candidate/restored CTest logs are archived under
`libwebp-i4-balanced-chroma-shared-*`. This was a Turing-only local screen;
no Ampere+ code or performance claim was retained.

## Pre-Ampere uniform-AC I4 quantization rejection

Native-sm_75 disassembly exposed 621 static global `U16` load sites in the
decimate kernel, while `ExpandMatrix` guarantees that luma AC entries 1--15
of `q`, `iq`, `bias`, and `zthresh` are identical. A host-validated fast path
cached those four AC scalars in the four-lane basic I4 quantizer and retained
the generic path for arbitrary contract matrices. Ampere+ compiled only the
unchanged generic implementation.

Candidate and restored trees passed 7/7 CTests, and all 24 order-reversed
native-sm_75 rows matched hashes and byte counts:

| Format | Parent | Uniform-AC | Change |
|---|---:|---:|---:|
| PNG lossy | 39.548 ms/image | 39.733 ms/image | +0.185 ms/image |
| JPEG lossy | 39.633 ms/image | 39.645 ms/image | +0.012 ms/image |

The candidate lowered register use from 103 to 101 but did not reduce wall
time, confirming that the repeated AC loads were already coalesced or
cache-resident. It was removed. Exact patch, rows, resources, and both test
logs are archived under `libwebp-i4-uniform-ac-*`. RTX 2080 SUPER only; no
Ampere+ behavior or claim changed.

## Pre-Ampere I4 source-Hadamard overlap rejection

The retained I4 profile assigned 21.7--24.0% of I4 cycles to metrics. Each
distortion mode serially transforms the common source and its reconstruction,
while two team warps are idle during the preceding transform/quantization
stage. A pre-Ampere candidate computed the common source Hadamard sum in one
idle lane before the existing barrier, then reused it for all ten modes.

Candidate and restored trees passed 7/7 CTests and all 24 order-reversed rows
were exact:

| Format | Parent | Overlap | Change |
|---|---:|---:|---:|
| PNG lossy | 39.683 ms/image | 39.596 ms/image | -0.088 ms/image |
| JPEG lossy | 39.567 ms/image | 39.689 ms/image | +0.121 ms/image |

A texture trace was likewise flat at 26.08 versus 26.15 ms GPU wall, with I4
65.3% versus 65.2% of block cycles. The work moved across the barrier but did
not shorten its critical path, so the candidate was removed. Exact patch,
rows, phase trace, resources, and tests are archived under
`libwebp-i4-source-hadamard-*`. RTX 2080 SUPER only; Ampere+ stayed unchanged.

A follow-up moved the same exact precompute into the earlier prediction
interval, where four warp leaders generate modes and the remaining lanes are
idle. It also passed 7/7 CTests and all 24 rows matched, but PNG moved only
39.715 to 39.629 ms/image (-0.086) while JPEG regressed from 39.619 to 39.758
(+0.138). That placement was removed too; neither existing I4 barrier hides
this work. Raw follow-up artifacts use the
`libwebp-i4-source-hadamard-pred-*` prefix.

## Pre-Ampere four-lane I4 residual cooperation rejection

A temporary native-sm_75 warp probe split the I4 metric interval into the
residual, SSE/flatness, and distortion warps. Across two reported medium runs,
the residual warp accumulated 84.2 million cycles on graphic content, about
306 million on photo, and about 270 million on texture. It was the largest
metric warp for the realistic photo and texture inputs, so the next candidate
targeted that measured dependency chain.

Four adjacent lanes cooperatively evaluated each I4 residual in four
coefficient waves instead of one lane walking sixteen coefficients. Ten mode
groups occupied 40 lanes; Ampere+ compiled the unchanged scalar path.
Candidate and restored trees passed 7/7 CTests, and all 24 order-reversed
native-sm_75 rows matched hashes and byte counts:

| Format | Parent | Four-lane residual | Gain |
|---|---:|---:|---:|
| PNG lossy | 40.168 ms/image | 40.085 ms/image | 0.083 ms/image |
| JPEG lossy | 39.652 ms/image | 40.185 ms/image | -0.533 ms/image |

Registers fell from 103 to 102 with the same 352-byte stack and 23,392-byte
shared allocation, but shuffle, reduction, and table-lookup overhead erased
the shorter serial chain. The candidate was removed. Raw probe patch/output,
candidate patch, timing rows, build resources, and both test logs are archived
under `libwebp-i4-metric-warp-*` and `libwebp-i4-residual-coop4-*`. RTX 2080
SUPER only; Ampere+ behavior and performance claims are unchanged.

## Pre-Ampere two-lane I4 residual cooperation rejection

The four-lane screen showed that subgroup overhead outweighed its four-wave
chain, so the same residual-warp profile motivated a narrower two-lane
experiment. Ten pairs remained entirely in warp 0 and processed eight
coefficient waves. An initial prototype violated the shuffle mask contract
and hung the bounded medium smoke test; no timing from it was used. Moving the
prior-wave shuffle into both named lanes corrected the synchronization.

The corrected candidate and restored tree passed 7/7 CTests. All 24
order-reversed native-sm_75 rows were byte-exact:

| Format | Parent | Two-lane residual | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.846 ms/image | 42.669 ms/image | -2.823 ms/image |
| JPEG lossy | 39.813 ms/image | 42.713 ms/image | -2.900 ms/image |

The candidate retained the four-lane experiment's 102-register allocation,
but nearly three milliseconds of regression in both formats decisively
rejects coefficient-wave subgrouping. It was removed. Exact corrected patch,
timeout record, 24 rows, resources/build output, and both test logs are under
`libwebp-i4-residual-coop2-*`. RTX 2080 SUPER only; Ampere+ compiled the
unchanged scalar path.

## I4 zero-residual bypass feasibility rejection

A temporary native-sm_75 counter used the already-published I4 nonzero flags
to measure how often scalar residual scoring could bypass its backwards
last-nonzero scan. Two diagnostic passes per medium input reported:

| Content | Zero residual modes | Rate |
|---|---:|---:|
| Graphic | 424,548 / 488,950 | 86.83% |
| Photo | 4,234 / 1,198,680 | 0.35% |
| Texture | 0 / 1,200,000 | 0.00% |

The high graphic rate is not actionable: the preceding warp profile measured
its residual warp at 84.2 million cycles versus 85.6 million for SSE/flatness,
so even deleting residual work entirely would leave the metric barrier set by
another warp. Photo and texture are the cases where residual is critical, but
their zero rates are negligible or zero. The ceiling is therefore far below
1.5 ms/image and no candidate was built. The probe was removed and the
restored tree passed 7/7 CTests. Raw patch, counts, build, and restored test
output are under `libwebp-i4-zero-residual-*`. RTX 2080 SUPER only.

## Pre-Ampere I4 last-index handoff rejection

The zero-mode probe showed that a zero-only bypass could not move the critical
warp, so a stronger candidate reused quantization's exact last-nonzero index
for every basic I4 mode. On pre-Ampere, two subgroup reductions packed that
index into the unused upper bits of the existing `i4_nz` scratch word; the
residual warp skipped its backwards sixteen-level scan. Trellis and Ampere+
retained the original path and scratch interpretation.

Candidate and restored trees passed 7/7 CTests. All 24 order-reversed
native-sm_75 rows were byte-exact:

| Format | Parent | Last-index handoff | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.887 ms/image | 39.833 ms/image | 0.054 ms/image |
| JPEG lossy | 39.893 ms/image | 39.897 ms/image | -0.005 ms/image |

Registers fell from 103 to 102, with stack and shared memory unchanged, but
the quantizer reduction offset the eliminated scan. The candidate was
removed. Exact patch, rows, build/resources, and both test logs are archived
under `libwebp-i4-last-handoff-*`. RTX 2080 SUPER only; no Ampere+ claim.

## Pre-Ampere zero-level residual-cost rejection

A temporary native-sm_75 probe counted the coefficient values actually
charged by I4 residual scoring:

| Content | Zero | One | 2+ |
|---|---:|---:|---:|
| Graphic-medium | 45.38% | 24.52% | 30.09% |
| Photo-medium | 74.62% | 24.54% | 0.85% |
| Texture-medium | 12.82% | 23.40% | 63.78% |

Because `VP8LevelFixedCosts[0]` is exactly zero, a pre-Ampere candidate
returned the variable table's zero entry directly and skipped the redundant
fixed-table load. Ampere+ compiled the original compact two-table path.
Candidate and restored trees passed 7/7 CTests, and all 24 rows were exact:

| Format | Parent | Zero fast path | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.930 ms/image | 40.202 ms/image | -0.273 ms/image |
| JPEG lossy | 39.810 ms/image | 40.066 ms/image | -0.256 ms/image |

Resources stayed at 103 registers, a 352-byte stack, and 23,392 shared bytes.
The added divergent branch cost more than the avoided load, so the candidate
was removed. Raw probe, exact patch, rows, builds/resources, and tests are
archived under `libwebp-i4-residual-value-*` and
`libwebp-i4-zero-level-cost-*`. RTX 2080 SUPER only.

## Pre-Ampere common-level residual-cost rejection

The zero-only branch regressed, but a follow-up counter found levels 0--4
covered 91.18% of graphic, 99.96% of photo, and 82.27% of texture residual
values. Because the fixed costs are exactly zero for level 0 and 256 for
levels 1--4, a pre-Ampere candidate used those immediates and retained the
original compact lookup above level 4. Ampere+ compiled the original path.

Candidate and restored trees passed 7/7 CTests. All 24 order-reversed
native-sm_75 rows were byte-exact:

| Format | Parent | Common-level path | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.810 ms/image | 40.553 ms/image | -0.743 ms/image |
| JPEG lossy | 39.729 ms/image | 40.511 ms/image | -0.783 ms/image |

Registers fell from 103 to 102, but the remaining >4 divergence and larger
control path outweighed the fixed-table loads. The candidate was removed.
Raw range probe, exact patch, rows, builds/resources, and tests are archived
under `libwebp-i4-residual-range-*` and
`libwebp-i4-common-level-cost-*`. RTX 2080 SUPER only.

## Pre-Ampere compact-I4 occupancy rejection

The retained native-sm_75 method-4 kernel used 103 registers, a 352-byte
frame, and 23,392 bytes of shared memory, limiting it to two resident CTAs per
Turing SM. The previously exact RD-level specialization removed the register
limit (67 registers, no frame), but had remained at two CTAs because shared
memory was unchanged. A new candidate stored each reconstructed I4 block at
its actual four-byte row stride on pre-Ampere and composed that specialization;
Ampere+ retained the established layout and runtime RD-level path.

The candidate reached its profiled resource goal: method 4 used 69 registers,
no frame, and 21,152 shared bytes, permitting three CTAs per Turing SM. Exact
CPU/CUDA hashes and byte counts matched for all 15 method/quality cells across
methods 2--6, qualities 25/75/98, and graphic/photo/texture inputs at 17x13
and 257x255. The focused trellis test also covered qualities 75/99, 513x517,
one/two passes, padded strides, band remainders, and transactional fallbacks.
All 24 order-reversed timing rows matched:

| Format | Parent | Compact occupancy | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.438 ms/image | 38.974 ms/image | 0.465 ms/image |
| JPEG lossy | 39.427 ms/image | 39.141 ms/image | 0.286 ms/image |

Both gains are noise, so the candidate was removed. The corpus has at most 75
CTAs on a diagonal; two resident CTAs across 48 SMs already expose 96 slots,
leaving the third theoretical slot mostly unused. Exact patch, resource
profile, 24 raw rows, and the 15-cell hash/byte matrix are archived under
`libwebp-i4-compact-occupancy-*`. RTX 2080 SUPER only; Ampere+ code, dispatch
gates, and performance claims remain unchanged.

## Pre-Ampere decimation CUDA Graph replay rejection

The refreshed native-sm_75 profile kept decimation as the dominant retained
lossy stage: 20.671/25.819 ms on graphic, 21.605/31.750 ms on photo, and
52.138/79.093 ms on texture. The medium wavefront also requires roughly 250
dependent diagonal launches. Nsight Compute counters were unavailable with
`ERR_NVGPUCTRPERM`, so the next distinct candidate cached and replayed that
explicit launch sequence as CUDA Graphs on pre-Ampere only. Ampere+ retained
the existing launch path.

The candidate trellis/fallback suite was byte-exact. A same-binary screen used
`WEBP_CUDA_DECIMATE_GRAPH=0` as the control and reversed format order:

| Format | Parent | Graph replay | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.937 ms/image | 82.736 ms/image | -42.799 ms/image |
| JPEG lossy | 39.515 ms/image | 80.974 ms/image | -41.459 ms/image |

All retained rows matched aggregate hashes and byte counts (`ace64e860de89b43`
/ 6,441,688 bytes for PNG; `1cbb84d2ab926db3` / 6,400,792 bytes for JPEG).
Graph-node scheduling more than doubled the decimation-heavy cost on Turing,
so the candidate was removed without expanding to the full matrix. Restored
source passed six of seven local CTests; the sole silent
`cuda_histogram_test` exit is pre-existing in the untouched parent. Exact
patch, raw rows, profile, tests, and summary are archived under
`libwebp-decimate-graph-replay-*`. RTX 2080 SUPER only; no Ampere+ claim.

## Pre-Ampere fused I4 prediction-group rejection

Fresh native-sm_75 tracing kept I4 at 63.8% of photo and 65.5% of texture
block cycles. Whole forced-batch sampling placed the CPU work in the already
exhausted token recorder/emitter, so the next distinct device candidate fused
warp 0's fixed DC/RD/HD prediction group. RD and HD reused six symmetric
three-tap boundary averages; the other warp leaders used direct calls for
their fixed mode groups. Ampere+ retained the original dispatcher loop.

The focused trellis, padded-stride, band-remainder, and transactional-fallback
test passed for both candidate and restored source. All 24 order-reversed
native timing rows matched hashes and byte counts:

| Format | Parent | Fused prediction group | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.469 ms/image | 38.798 ms/image | 0.671 ms/image |
| JPEG lossy | 39.525 ms/image | 38.644 ms/image | 0.881 ms/image |

Both gains are below 1.5 ms/image, so the candidate was removed. Reusing the
shared prediction arithmetic improves the earlier static-dispatch shape but
still cannot move enough of the sequential I4 chain. Exact patch, profile,
24 rows, tests, and summary are archived under
`libwebp-i4-pred-group-fusion-*`. RTX 2080 SUPER only; no Ampere+ claim.

## Pre-Ampere min/max reconstruction-clip rejection

The retained profile kept I4 at 63.8--65.5% of realistic photo/texture block
cycles. Texture token partitions differed by only 11.2%, an unavoidable
consequence of assigning 75 macroblock rows modulo eight already-concurrent
standard partitions. The next distinct candidate therefore replaced
pre-Ampere `CudaClip8b` range tests with signed integer min/max saturation;
Ampere+ retained the original expression.

The native sm_75 decimate kernel became 240 SASS instructions shorter while
remaining at 103 registers, a 352-byte stack, and 23,392 shared bytes.
Candidate and restored focused exact suites passed, and all 24 order-reversed
rows matched hashes and byte counts:

| Format | Parent | Min/max clip | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.459 ms/image | 39.063 ms/image | 0.396 ms/image |
| JPEG lossy | 39.500 ms/image | 39.486 ms/image | 0.014 ms/image |

The shorter code is largely outside the critical path, and both gains are
below 1.5 ms/image. The candidate was removed. Exact patch, partition/profile
evidence, resources, 24 rows, tests, and summary are archived under
`libwebp-i4-clip-minmax-*`. RTX 2080 SUPER only; no Ampere+ claim.

## Pre-Ampere vectorized I4 transform-row I/O rejection

The refreshed native-sm_75 profile again put I4 at 63.8% of photo and 65.2%
of texture block cycles. After excluding the previously tested coefficient
handoff, quantizer-width, matrix, transpose, and clipping variants, generated
code showed aligned four-byte I4 row accesses still emitted as byte-wide
shared-memory operations. A pre-Ampere candidate used `uchar4` loads for the
source/prediction rows and one `uchar4` store for the inverse-transform row;
Ampere+ retained the established scalar source.

The candidate reduced static byte-wide sites from 893 to 881 loads and from
203 to 199 stores, but extraction/packing increased the sm_75 kernel from
23,704 to 23,712 instructions. Registers, stack, and shared memory stayed at
103, 352 bytes, and 23,392 bytes. Candidate and restored focused exact tests
passed, and all 24 order-reversed rows matched hashes and byte counts:

| Format | Parent | Vector row I/O | Gain |
|---|---:|---:|---:|
| PNG lossy | 39.501 ms/image | 39.400 ms/image | 0.101 ms/image |
| JPEG lossy | 39.922 ms/image | 39.533 ms/image | 0.389 ms/image |

Both gains are noise under the strict 1.5 ms/image gate, so the source was
restored. Exact patch, full parent/candidate SASS, profile, raw rows, tests,
and summary are archived under `libwebp-i4-vector-rowio-*`. RTX 2080 SUPER
only; no Ampere+ behavior, threshold, or performance claim changed.

## Portable lossy-decimate conformance target

GitHub issue #19 is implemented as an opt-in, backend-neutral conformance
surface rather than a performance candidate. WPDCRD schema 1 serializes the
complete ABI-12 lossy-decimate request and CPU-golden result/reconstruction
bytes without C layout or endian dependencies. The standalone runner covers
loopback transport and transactional decline/error/timeout, whole and banded
CUDA execution, a dependency-free FPGA decline skeleton, coverage reporting,
and split execution/result-transfer diagnostics.

On the native-sm_75 RTX 2080 SUPER build, 132 fixtures (48,968 macroblocks)
covered methods 3--6, qualities 0/25/75/98/100, tiny/odd/aligned inputs, all
segments, all I4/I16/UV prediction modes, zero/nonzero contexts, diffusion,
band boundaries, flat ties, and signed coefficient extremes. All 132 whole
and all 132 streaming CUDA submissions matched every semantic result and
reconstruction byte. A separate 90-cell methods 2--6, qualities 25/75/98
tiny/odd matrix matched CPU/CUDA SHA-256 and byte counts, while the expanded
end-to-end test retained exact methods 3--6 bitstreams and forced fallbacks.

The first expanded oracle run retained a useful audit failure: 38 method-5 or
no-diffusion cases recorded an inactive/discarded CPU diffusion tail. Capture
now records the state actually published to neighboring macroblocks; both the
94/132 initial rows and 132/132 corrected rows are archived. This work makes
no speed or cross-hardware claim and changes no Turing/Ampere+ threshold.
Artifacts use the `libwebp-decimate-conformance-*` prefix.
