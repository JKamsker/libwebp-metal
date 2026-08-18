# Metal experiment series: Sol analysis and disposition

> **2026-08-18 publication boundary:** this document preserves the original
> five-item interpretation. For publication support, experiment 4's
> external-image transform/hash rows and all of experiment 5 are now
> historical-only because the exact inputs have unresolved provenance and
> redistribution rights. Experiments 1--3 and experiment 4's generated-input
> lossy suite remain in the bounded core. See
> [publication-evidence-audit-20260818.md](publication-evidence-audit-20260818.md).
>
> **2026-08-18 next-boundary addendum:** the later frozen predictor/backref
> decomposition completed on publication corpus v1. Predictor
> selector-plus-apply passed its share tests but failed a required recorder
> overhead cell; standard exact LZ77 was only 3.13--4.29% of required holdout
> backref boundaries and was rejected as dominant. No production change was
> promoted. See
> [next-boundary-experiment-evaluation-20260818.md](next-boundary-experiment-evaluation-20260818.md).
>
> **2026-08-18 focused cache-search addendum:** a later independent row-8
> diagnostic found majority cache-search share in every required texture
> holdout, but method-6 cold failed its median-overhead gate. It was not
> accepted, changes no predecessor disposition, and promotes no production
> change. See
> [backref-cache-search-experiment-evaluation-20260818.md](backref-cache-search-experiment-evaluation-20260818.md).
>
> **2026-08-18 serial-sweep addendum:** the row-9 recorder-free implementation
> preserved exact output and fallback behavior in all 18 cells, but was about
> 7.6--8.9% slower by paired median and failed p95 in every performance cell.
> It is rejected, remains default off, and promotes no production change. See
> [cache-size-serial-sweep-experiment-evaluation-20260818.md](cache-size-serial-sweep-experiment-evaluation-20260818.md).
>
> **2026-08-18 single-pass slab addendum:** the independent row-10 candidate
> preserved selected cache bits, bitstreams, decoded pixels, deterministic
> output, fallback, and default-build independence. Three of four required
> holdout cells nevertheless missed the paired-median limit. It is rejected,
> remains default off, and promotes no production or threshold change. See
> [cache-size-single-pass-slab-experiment-evaluation-20260818.md](cache-size-single-pass-slab-experiment-evaluation-20260818.md).
>
> **2026-08-18 cost/traceback workspace addendum:** the row-11 executor stopped
> fail-closed before lease acquisition, build, correctness, or timing because
> Low Power Mode was enabled on AC. Independent untimed equivalence, fallback,
> build-isolation, and sanitizer checks pass, so the candidate is retained
> default off. With no mandatory holdout medians or p95 values, performance is
> unassessed and promotion is rejected for this cycle. No production or
> follow-up gate is added. See
> [backref-cost-traceback-experiment-evaluation-20260818.md](backref-cost-traceback-experiment-evaluation-20260818.md).
>
> **2026-08-18 remote workspace A/B addendum:** the row-12 remote re-freeze
> stopped before source transfer, preflight, lease, correctness, or timing when
> the frozen driver rejected its generated temporary path. No rerun or repair
> occurred. Both variants have zero samples, so performance remains unassessed
> and promotion is rejected for this cycle. The exact candidate passes untimed
> equivalence and safety checks and remains default off. See
> [backref-cost-workspace-ab-experiment-evaluation-20260818.md](backref-cost-workspace-ab-experiment-evaluation-20260818.md).

## Scope and evidence boundary

This report interprets the five serialized experiment runs committed from
`0d925e3d` through `6f539ac6`. It uses the raw samples and predefined strata,
not the operator reports' non-interpretive handoffs. No new timed workload was
run during analysis.

The mechanical validation records pass for all five experiments. Independent
recalculation confirmed the committed hashes for the timing records, summaries,
validity files, and predictor CSV. One provenance typo is retained in the
historical evidence: experiment 1's report and preflight print a 62-character
manifest digest. The actual SHA-256 of both committed manifest copies is
`4711e88382816a1d1546bde24f044e37c3c6c6f9d5a47b2b3b625f40be8d973b`.
The copies are byte-identical and their nine input hashes passed validation, so
the typo does not invalidate the samples, but the printed digest must not be
used as a verifier.

Comparisons preserve the predefined dimensions:

- cold and warm samples are never pooled;
- content, size, method, operation, and tune/holdout roles remain separate;
- paired sequence ratios are used where the harness paired CPU/baseline and
  Metal/candidate runs;
- medians, MAD, and observed ranges are descriptive, not population confidence
  intervals;
- warm samples from one process and repeated samples from one import process
  are correlated and are not counted as independent machines;
- the 15 ablation candidates create a substantial multiple-comparison burden,
  so sub-two-percent movements that change sign across strata are treated as
  noise;
- stage timers are inclusive. A parent minus a nested Metal timer is an
  accounting remainder, not a pure CPU measurement.

## Disposition summary

| Experiment | Disposition | Durable consequence |
|---|---|---|
| 1. Encoder stage profile | Retain as an opt-in research path | Predictor-path and backward-reference CPU work remain the next architectural targets; no stage share is translated into a threshold. |
| 2. CPU/Metal crossover | Retain the transform result as an unvalidated candidate; reject other default changes | A machine-readable transform candidate is recorded, but compiled eligibility and pixel thresholds remain unchanged. |
| 3. Persistent/batched Metal | Retain as an opt-in research path; do not promote | Warm import submission amortizes, but no end-to-end batch break-even was observed and the private batch ABI stays experimental. |
| 4. Kernel/memory ablations | Promote the exact 2x2 lossy import kernel; reject the other default changes | The 2x2 kernel becomes the production default. The old per-pixel grid remains only as an ablation regression control. |
| 5. Predictor residual | Reject the standalone stage for promotion; retain gated code as a correctness/reference path | Its cold end-to-end case is negative in every median stratum. No descriptor stage, default, or threshold is added. |

## 1. Encoder stage profile

The accepted run contains 252 records: three cold samples and three measured
warm samples for every case/method/backend cell, plus one discarded warmup per
warm cell. All 18 output-validation cells are deterministic within backend and
decode identically across CPU and Metal.

Warm end-to-end CPU/Metal ratios (greater than one favors forced Metal) are:

| Content/size | Method 4 | Method 6 |
|---|---:|---:|
| photo 512x512 | 1.534x | 1.082x |
| photo 1600x1200 | 1.843x | 1.867x |
| photo 3000x2000 | 1.787x | 2.169x |
| graphic 512x512 | 0.314x | 0.336x |
| graphic 1600x1200 | 0.426x | 0.434x |
| graphic 3000x2000 | 0.447x | 0.452x |
| texture 512x512 | 0.999x | 1.003x |
| texture 1600x1200 | 1.149x | 1.168x |
| texture 3000x2000 | 1.335x | 1.312x |

The dominant remaining warm Metal buckets are content-dependent:

- On photos, inclusive `lossless_predictor` is 43.8--47.6% of method-4
  time and 44.7--89.9% of method-6 time. It includes predictor selection,
  residual application, and nested encoding of the predictor map, so it does
  not establish that residual application alone is hot.
- `lossless_backward_refs`, which does not enclose a Metal dispatch, is
  2.5--27.0% on photos (the low endpoint is the predictor-dominated 512x512,
  method-6 cell) and 43.6--68.9% on textures. Histogram construction is another
  38% on 512x512 textures but falls to about 6% at 6 MP; bitstream work is about
  9% at the larger texture sizes.
- On palette graphics, direct Metal hash dispatch consumes 55.1--56.0 ms at
  6 MP and 55--69% of total time across the size ladder. This is dispatch
  ineligibility, not evidence that CPU hash construction should be optimized.
- Cold Metal initialization is about 24.6--31.2 ms and is effectively absent
  from measured warm records. Small cold and warm policies therefore cannot be
  conflated.

The profile supports target selection only. The experiment stays default-off;
no new profiler split or follow-up timing pipeline is introduced here.

## 2. CPU/Metal crossover

The focused run contains 424 randomized pair blocks and 1,648 measured samples.
Tune and holdout seeds agree on the only conservative candidate: isolated
cross-color transform on synthetic photos.

| Execution | Method | First tested stable bucket | Evidence through maximum |
|---|---:|---:|---|
| cold | 4 | 768x768 (589,824 pixels) | all 12 tune/holdout observations at 768 and 1024 are at most 0.95 Metal/CPU |
| cold | 6 | 768x768 (589,824 pixels) | all 12 tune/holdout observations at 768 and 1024 are at most 0.95 Metal/CPU |
| warm | 4 | 192x192 (36,864 pixels) | all observations at all six tested buckets are at most 0.95 |
| warm | 6 | 192x192 (36,864 pixels) | all observations at all six tested buckets are at most 0.95 |

These entries are recorded in
`scripts/metal_threshold_policy.m4pro-20260817.candidate.json`. They are not
compiled: the current call boundary does not expose method or initialization
state, and the data cover one M4 Pro on one day. The existing 65,536-pixel
transform default is therefore deliberately unchanged pending the predefined
different-day and supported-GPU confirmation.

Hash has no policy entry. Warm synthetic photos are 2.0--13.7% slower at every
tested size and method; warm textures become consistently favorable only from
1.92 MP at method 4 and 1.05 MP at method 6. Cold photos are slower through
6 MP, while cold textures show a five-percent-margin win only at the single
largest 6 MP bucket, which fails the two-consecutive-bucket rule. The strata
cannot be pooled, and older real-photo results point in the opposite direction,
so neither disabling hash globally nor changing its 4 MP threshold is justified
from this run.

Palette graphics are different: forced warm hash is 2.16--3.23x slower in all
six size/method cells. Those six-color inputs are packed to half-width before
hash search, however, so even the 6 MP source becomes a 3 MP request. Every
measured palette request is therefore below the existing 4 MP hash threshold
and would stay on CPU without the experiment's forced dispatch. The result is
a useful regression guard and argues against lowering that threshold, but it
does not justify a categorical palette exclusion for unmeasured requests above
4 MP. No request field, eligibility rule, or private ABI change is made.

Lossy end-to-end import has no entry. Cold Metal/CPU medians range from about
1.00 to 1.38 and never establish a five-percent win. Warm ratios are mostly
0.97--1.01, with observed ranges frequently crossing one; even at 10,240x10,240
the practical end-to-end gain is below the predefined margin. The conservative
80 MP default is unchanged.

## 3. Persistent/batched Metal

The matrix has five independent cold processes and twenty sequential warm
samples for each submission/batch-size cell at 3000x2000. Stage-only warm
import median time per image improves with one command buffer: 34.6% at batch
2, 16.4% at batch 4, and 20.5% at batch 8. The sequence is not monotonic and
contains first-sample and allocation/copy variability, so it supports
amortization qualitatively rather than a smooth scaling model.

Cold import does not establish a batch break-even: batch submission is 16.7%
slower at batch 2, 10.0% slower at batch 4, and 3.7% slower at batch 8 by
median. More importantly, serial full encoding dominates. Across cold and warm
end-to-end cells, batch/single median time per image ranges from 0.988 to 1.015;
most cells are neutral or slower and the largest observed improvement is only
1.24% at cold batch 8. No end-to-end batch size clears a practical acceptance
margin.

The private batching symbol, synthetic harness, and one-command-buffer proof
remain useful research infrastructure. Promotion would still require a neutral
versioned batch boundary, memory limits, cancellation semantics, and a workload
that batches more than import. No production ABI or aggregate policy is added.

## 4. Kernel and memory ablations

Transform and hash candidates are non-actionable after preserving all six
input/method strata. Their pooled paired medians range from -0.45% to +1.57%
for transform and -0.09% to +0.51% for hash. Every candidate has individual
pairs on both sides of one. Stratum-median signs also cross one except for the
transform 512-thread candidate, which instead regresses in all six strata by
0.87--2.75%. With four transform and five hash comparisons, the apparent small
wins are below run/order variation and the one consistent transform result is
a loss, so none is promoted.

The warmed lossy import comparisons use the median measured sample within each
of three independent processes at 6 MP and 12 MP, rather than treating all
2,880 inner samples as independent:

| Candidate | Median candidate/baseline | Independent process wins | Decision |
|---|---:|---:|---|
| 2x2 block grid | 0.590 (-41.0%) | 6/6 | Promote |
| 512 threads | 0.804 (-19.7%) | 6/6 | Retain for research; interaction with the promoted grid was not measured |
| contiguous copy | 0.941 (-5.9%) | 5/6 | Reject; only 1.3% at 12 MP and one process regressed |
| 128 threads | 1.008 (+0.8%) | 2/6 | Reject |
| unretained commands | 1.002 (+0.2%) | 2/6 | Reject |
| write-combined input | 0.999 (-0.1%) | 3/6 | Reject |

The 2x2 grid computes the same integer YUV values while reusing four RGB loads.
The committed checksum and bitstream gates passed, including the ablation
variant. It is now the ordinary Metal kernel specialization. The experiment
gate can still select the legacy per-pixel grid as a correctness/regression
control. The 512-thread result is not combined with 2x2 without interaction and
cross-device evidence; no thread default changes.

This is a stage implementation change, not evidence for lowering the 80 MP
end-to-end threshold. Experiment 2 shows why those decisions remain separate.

## 5. Predictor residual

The correctness suite preserves exact streams and decoded pixels, and the
injected post-dispatch failure preserves transactional CPU fallback. The timed
CSV contains 84 fresh-process observations. Performance is consistently
negative:

| Input | Method 4 median paired Metal/CPU | Method 6 median paired Metal/CPU |
|---|---:|---:|
| `mitski.png` | 1.039 | 1.034 |
| `corgi.jpeg` | 1.017 | 1.014 |
| `siamese.jpg` | 1.011 | 1.008 |

Metal is slower in 37 of 42 close pairs. The median absolute penalty is
30--40 ms in every input/method stratum, consistent with another cold pipeline,
upload, dispatch, wait, and readback boundary. The two largest-image percentage
effects approach the CSV's centisecond resolution, but none supplies a positive
end-to-end case.

The standalone stage is therefore rejected for production promotion. The code
stays behind its independent build/runtime gates because it is a useful exact
oracle for all 14 predictors and because no warm stage-only experiment was run.
Any future value must come from selector acceleration and a resident/fused
pipeline, not from interpreting the inclusive predictor parent as residual-only
time. No descriptor bit, request, threshold, or default is added.

## Combined architectural consequences

1. Remaining CPU opportunity is in predictor selection/map encoding and
   backward-reference selection, not another standalone low-arithmetic kernel.
   Texture backward references are the clearest independent bucket. Predictor
   work needs a finer semantic split before choosing an implementation boundary.
2. Crossover policy eventually needs content eligibility and lifecycle state.
   A single pixel threshold cannot reconcile cold/warm transform behavior,
   photo/texture hash disagreement, and palette regressions. This series does
   not add such an interface: the relevant eligible region was not measured
   broadly enough to define one.
3. Persistent resources already remove roughly 25--31 ms after first use.
   Batch submission saves a material fraction of warmed import but not serial
   encoding. End-to-end batching needs more resident/batched stages before its
   memory and ABI costs are justified.
4. Kernel-level wins and end-to-end policy are separate. The 2x2 import kernel
   is worth using whenever import is selected, while the data still reject a
   lower lossy crossover threshold.
5. A standalone predictor-residual dispatch has no credible measured
   end-to-end case. The stage profile supports research on the broader predictor
   path only.

## Implemented changes

- The exact 2x2 RGB-to-YUV kernel is the default specialization. Under the
  existing ablation gate, `WEBP_METAL_LOSSY_BLOCK_2X2=0` selects the legacy
  per-pixel regression control.
- The untimed Metal correctness suite names the old specialization
  `legacy_per_pixel`. The released timed ablation matrix remains unchanged for
  historical reproduction; it is not repurposed as a follow-up under item 4's
  gate.
- The M4 Pro transform candidate policy is recorded separately from the empty
  production fallback. No compiled threshold changes.
- Existing Metal correctness tests cover exact shader output for the promoted
  specialization, including its legacy per-pixel regression control.

## Validation of this interpretation and change

- Recomputed every recorded cross-artifact SHA-256 in the five validation
  handoffs. The sole mismatch is the documented experiment-1 manifest typo;
  all timing and summary artifacts match their recorded digests.
- Regenerated experiment 1's baseline from `records.jsonl`; it is semantically
  identical, with only the expected embedded absolute worktree path differing.
- Recomputed the experiment-2 decision rule from tune and holdout pair ratios,
  experiment-3 per-image medians, experiment-4 per-process paired medians, and
  experiment-5 close-pair ratios directly from raw records.
- Validated both threshold policy JSON files against every field constraint in
  `metal_threshold_policy.schema.json` (the optional `jsonschema` Python module
  is not installed in the test environment).
- Passed `scripts/test_experiment_guards.py`, including default-off macro
  isolation, omitted-target and runtime refusals, missing-lease refusals, the
  production/legacy correctness mapping, and preservation of the historical
  timed ablation matrix.
- Passed CPU build/roundtrip, accelerator-interface, default Metal, and
  ablation-gated Metal correctness suites. The Metal suites observed every
  forced operation and compared CPU/Metal streams. A 97x65 batch verify also
  matched CPU, single Metal, and batched Metal streams, exercising odd edges in
  the 2x2 default.
- Passed Python compilation, shell syntax, `git diff --check`, and confirmed no
  installed header differs from the experiment base. CMake was unavailable on
  this host; both ordinary and experiment-gated Unix Make builds succeeded.

All validation above is untimed. No new benchmark lease was requested or used.

The 2026-08-18 release/build hardening follow-up added installed static/shared
CMake consumers, explicit Autotools Metal off/on coverage, installed
header/export comparison, adversarial public-API tests, and a forced-Metal
UBSan mutation harness. This is correctness and distribution evidence
only: it did not run timed workloads, change thresholds, or promote any
research-only path.

## Remaining uncertainties

- Performance evidence comes from one M4 Pro on one day. Transform candidates
  remain synthetic-photo-only, and the promoted 2x2 kernel was measured at 6
  and 12 MP rather than the current 80 MP end-to-end selection threshold.
- The ablation matrix did not measure 2x2 combined with 512 threads, so their
  gains cannot be multiplied or assumed independent.
- Batch evidence covers one 6 MP synthetic input, quality 75, method 4, and a
  serial encoder after import; it is not a service-level concurrency result.
- Predictor evidence covers three images, cold processes, methods 4 and 6, and
  centisecond timing resolution. It decisively rejects this standalone cold
  boundary but does not measure a fused or resident predictor path.

No new follow-up experiment pipeline was prepared. Consequently there are no
new build flags, runtime flags, or operator entry points; the original five
independent guard rows remain unchanged.
