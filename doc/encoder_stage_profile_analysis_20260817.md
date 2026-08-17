# Encoder stage profile analysis: methods 4 and 6

This report interprets the serialized Apple M4 Pro experiment in
`profile-data/runs/stage-profile-20260817`. It does not contain measurements
made during the analysis phase. All quantities below were reconstructed from
the committed `records.jsonl` by `scripts/analyze_encoder_stage_profile.py`.

## Executive result

On warm Metal photo encodes, the inclusive predictor bucket is the largest
remaining stage at both methods: 43.6--47.8% of total at method 4 and
44.7--90.3% at method 6. This bucket includes predictor search/residual
application **and** encoding the predictor transform map. Even after the
deliberately conservative subtraction of *all* direct Metal hash-dispatch time
(some of which is outside the predictor bucket), at least 32.2--38.5% of the
method-4 photo total and 30.5--88.5% of the method-6 photo total remains. The
data therefore establish predictor-path CPU work as a robust target, but do
not isolate `VP8LResidualImage` from its nested transform-map encode.

The other robust remaining CPU target is backward-reference selection. It is
23.7--27.3% of warm Metal medium/large photo time and 61.9--69.1% of warm
Metal medium/large texture time. On small texture it is still the largest
single CPU bucket (40.2--41.3%), closely followed by histogram work
(34.8--36.5%). At medium/large texture sizes, bitstream emission is a stable
second tier (9.0--10.6%), while histogram work is 6.1--11.3%.

Palette graphics are a different regime. Their warm `lossless_hash_chain`
bucket is 59.4--68.5% of total, but 55.7--66.4% is the nested forced Metal hash
dispatch. The largest remaining CPU bucket is backward-reference selection at
23.0--32.3%. This is primarily evidence that zero-threshold forced dispatch is
ineligible for these images, not evidence of a large CPU hash-chain target.

## Inputs and independent validation

The matrix contains nine deterministic opaque PPM inputs: one synthetic
`photo`, `graphic`, and `texture` formula at 512x512, 1600x1200, and 3000x2000.
Every case was encoded losslessly and exactly at quality 75, methods 4 and 6,
single-threaded, with CPU and forced-Metal backends. Each
case/method/backend group contains three separate-process cold records, one
in-process warmup, and three subsequent in-process warm records.

The independent analyzer checked the following before producing tables:

- all 252 records use `libwebp-encoder-stage-v1`, report success, and match the
  manifest dimensions and fixed encoder configuration;
- role counts are 108 cold, 36 warmup, and 108 warm; all 72 measured
  case/method/backend/role groups contain three samples;
- all 126 Metal records dispatched the hash kernel; exactly the 42 Metal photo
  records also dispatched cross-color; no CPU record reports a Metal dispatch;
- recomputed median, MAD, min/max, call-count, selection-rate, and stage-share
  fields match every field in all 72 committed baseline groups;
- the operator's separate 18-entry output check found repeatable CPU and Metal
  bitstreams and identical decoded CPU/Metal pixels. The 12 graphic/texture
  entries have identical CPU/Metal bitstreams; the six photo entries have
  different bitstreams and output sizes but identical decoded pixels.

The analysis uses medians and median absolute deviation (MAD). The ratio bounds
in `analysis_summary.json` are the most pessimistic CPU-minimum/Metal-maximum
and CPU-maximum/Metal-minimum combinations among the three observations. They
are descriptive observed bounds, not confidence intervals or paired-sample
estimates.

## Warm end-to-end outcome

The table reports internal encode time as CPU ms -> Metal ms, followed by
CPU/Metal. A ratio above 1 favors Metal. Input reading and process launch are
outside this timer.

| content-size | method 4 | method 6 |
|---|---:|---:|
| photo-small | 67.33 -> 43.27 (1.556x) | 313.50 -> 294.28 (1.065x) |
| photo-medium | 306.53 -> 166.41 (1.842x) | 456.48 -> 245.49 (1.859x) |
| photo-large | 936.67 -> 532.59 (1.759x) | 1217.58 -> 565.70 (2.152x) |
| graphic-small | 3.68 -> 10.48 (0.351x) | 3.80 -> 10.35 (0.367x) |
| graphic-medium | 14.52 -> 34.09 (0.426x) | 14.71 -> 33.72 (0.436x) |
| graphic-large | 44.29 -> 98.53 (0.449x) | 44.24 -> 99.03 (0.447x) |
| texture-small | 20.79 -> 21.56 (0.964x) | 20.68 -> 22.21 (0.931x) |
| texture-medium | 118.30 -> 102.39 (1.155x) | 117.87 -> 97.42 (1.210x) |
| texture-large | 395.10 -> 299.43 (1.320x) | 399.03 -> 289.68 (1.377x) |

The three-sample observed bounds preserve every directional conclusion above
except the small textures: method 4 spans 0.892--1.045 and method 6 spans
0.916--1.021. Photo-small method 6 is positive but modest (1.048--1.095). The
remaining photo, graphic, and medium/large texture directions do not cross 1
within the observed samples. These are corpus-local findings, not population
speedups.

## Warm stage attribution

### Photos: cross-color plus hash

| size | method | total ms | predictor ms (% total) | backward refs ms (%) | hash dispatch ms (%) | cross dispatch ms (%) |
|---|---:|---:|---:|---:|---:|---:|
| small | 4 | 43.27 | 18.85 (43.6%) | 7.24 (16.7%) | 4.18 (9.7%) | 5.04 (11.7%) |
| medium | 4 | 166.41 | 79.63 (47.8%) | 45.44 (27.3%) | 15.57 (9.4%) | 5.82 (3.5%) |
| large | 4 | 532.59 | 251.23 (47.2%) | 137.34 (25.8%) | 79.97 (15.0%) | 19.11 (3.6%) |
| small | 6 | 294.28 | 265.77 (90.3%) | 7.63 (2.6%) | 5.33 (1.8%) | 7.13 (2.4%) |
| medium | 6 | 245.49 | 147.81 (60.2%) | 44.54 (18.1%) | 16.14 (6.6%) | 16.92 (6.9%) |
| large | 6 | 565.70 | 252.79 (44.7%) | 133.83 (23.7%) | 80.18 (14.2%) | 50.71 (9.0%) |

Method 6 is not uniformly more expensive in the predictor bucket: its small
and medium cases are much larger than method 4, while the large cases are
nearly equal. The encoder source searches a wider predictor transform-bit
range above method 4, and method 6 also caps transform bits at 4 rather than 5,
but this coarse profile cannot assign the observed discontinuity to a specific
loop. A finer predictor split is required before selecting a subroutine.

Cross-color is not a remaining CPU bottleneck in these warm photo records. Its
inclusive parent is 3.7--12.9% at method 4 and 2.6--9.2% at method 6, and the
direct Metal dispatch accounts for nearly all of the parent median. Method 6
cross dispatch grows from 7.13 ms at small to 50.71 ms at large, versus
5.04--19.11 ms at method 4. This is consistent with method 6's finer transform
tile grid, but the dispatch timer also includes allocation where needed, host
copies, command construction, synchronous wait, and readback; it is not GPU
kernel time alone.

### Hash-only graphics and textures

| content-size | method | total ms | backward refs ms (%) | histogram ms (%) | bitstream ms (%) | hash parent / direct dispatch ms |
|---|---:|---:|---:|---:|---:|---:|
| graphic-small | 4 | 10.48 | 2.43 (23.1%) | 0.68 (6.5%) | <0.01 | 7.18 / 6.96 |
| graphic-large | 4 | 98.53 | 31.47 (31.9%) | 1.04 (1.1%) | 0.01 | 58.78 / 55.37 |
| graphic-small | 6 | 10.35 | 2.38 (23.0%) | 0.74 (7.1%) | <0.01 | 7.04 / 6.84 |
| graphic-large | 6 | 99.03 | 32.01 (32.3%) | 1.04 (1.1%) | 0.01 | 58.83 / 55.20 |
| texture-small | 4 | 21.56 | 8.67 (40.2%) | 7.88 (36.5%) | 1.36 (6.3%) | 2.99 / 2.29 |
| texture-medium | 4 | 102.39 | 63.38 (61.9%) | 11.15 (10.9%) | 9.25 (9.0%) | 12.18 / 7.35 |
| texture-large | 4 | 299.43 | 203.18 (67.9%) | 18.89 (6.3%) | 30.67 (10.2%) | 30.64 / 15.46 |
| texture-small | 6 | 22.21 | 9.18 (41.3%) | 7.73 (34.8%) | 1.37 (6.2%) | 2.86 / 2.14 |
| texture-medium | 6 | 97.42 | 64.01 (65.7%) | 10.98 (11.3%) | 10.35 (10.6%) | 6.79 / 2.00 |
| texture-large | 6 | 289.68 | 200.09 (69.1%) | 17.66 (6.1%) | 29.08 (10.0%) | 27.21 / 12.26 |

The omitted medium graphic values follow the same pattern: direct hash
dispatch is 57.9--58.0% and backward references 28.7--28.9%. Graphics enter
the palette path and make two hash/back-reference calls; texture makes one.
Photos make three or four hash-dispatch calls depending on the small-case
transform metadata. Consequently, equal stage names do not imply equal work
composition across content classes.

`lossless_hash_chain` is the enclosing stage. Metal computes candidate matches,
then the CPU replays candidates and performs left extension. The direct hash
timer includes host copies, command encoding, synchronous wait, and readback,
but buffer growth occurs before that timer and remains only in the parent.
Parent minus dispatch is therefore an accounting remainder, not pure CPU
hash-chain time.

## Cold versus warm Metal

The process-global `metal_init` median is 23.81--31.70 ms in cold Metal
records and at most 0.00030 ms in warm records. It creates the device, compiles
the cross-color source/pipeline, and creates the queue. Because initialization
is shared, hash-only graphics and textures pay for the cross-color pipeline on
their first Metal call too. The separately timed first hash-pipeline setup is
only 0.071--0.105 ms in these records, plausibly benefiting from the already
initialized compiler/runtime; that number should not be generalized beyond
this machine and OS cache state.

| content | method | Metal cold-minus-warm total across sizes | cold `metal_init` across sizes |
|---|---:|---:|---:|
| photo | 4 | 26.81--39.74 ms | 26.13--30.74 ms |
| photo | 6 | 28.24--40.58 ms | 25.09--29.40 ms |
| graphic | 4 | 32.27--39.66 ms | 25.85--31.70 ms |
| graphic | 6 | 28.59--35.66 ms | 23.81--29.52 ms |
| texture | 4 | 22.49--45.15 ms | 24.06--29.64 ms |
| texture | 6 | 30.47--48.82 ms | 28.17--28.99 ms |

Initialization explains most of the small-image cold penalty. It does not
numerically explain every total delta: CPU first-use, allocation, cache, GPU
buffer growth, and run-order effects also change, and stage medians are not
paired observations. Cold-minus-warm CPU totals range from -0.81 to +7.41 ms,
showing that first-use effects are not Metal-only. Direct dispatch remains
material in warm execution: hash dispatch reaches about 80 ms on large photos,
55 ms on large graphics, and 12--15 ms on large textures; cross dispatch
reaches 19 ms at method 4 and 51 ms at method 6 on the large photo.

## Accounting cautions and limitations

The stage timers are coarse, monotonic, and inclusive:

- `lossless_predictor` wraps both `VP8LResidualImage` and
  `EncodeImageNoHuffman` for the predictor map. The latter adds nested hash,
  backward-reference, histogram, Huffman, and bitstream samples.
- `lossless_cross_color` likewise includes transform-map encoding after the
  color transform. Palette work also has nested image encoding.
- global hash/back-reference/histogram/Huffman/bitstream buckets aggregate the
  main image and transform metadata images. Their call counts differ by path.
- stage medians and total medians may come from different samples. Percentages
  are median-stage/median-total, not medians of per-record percentages.

Stage shares must therefore not be summed, and a parent-minus-child residual
must not be labeled pure CPU time. The dominant predictor and backward-reference
findings survive this constraint: backward references do not enclose Metal
dispatch, and the photo predictor remains large under a conservative subtraction
of every hash dispatch in the encode.

Statistical and corpus limits are substantial. There are only three measured
records per group; warm samples are sequential and correlated within one
process after one warmup; cold samples are separate processes. Backend order
was not randomized or interleaved. The run was on battery at 91% with load
averages 2.76/2.69/2.37, although macOS reported no thermal or performance
warning. The corpus has one synthetic generator per class, no alpha, no real
photographs, and one quality/thread configuration. Forced zero Metal thresholds
measure path behavior, not production dispatch eligibility. Photo CPU/Metal
bitstreams and sizes differ, so their end-to-end comparison is decoded-output
equivalent rather than bit-identical.

Confidence is high for the within-corpus identification of predictor-path and
backward-reference work, the forced-dispatch penalty on palette graphics, and
the one-time initialization cost. Confidence is moderate for exact shares and
relative scaling. It is low for generalization to real-world image populations,
default crossover thresholds, other Apple GPUs, or multi-threaded encoding.

## Reproducible analysis

This command only reads committed records and performs no encode:

```sh
python3 scripts/analyze_encoder_stage_profile.py \
  --records profile-data/runs/stage-profile-20260817/records.jsonl \
  --manifest profile-data/runs/stage-profile-20260817/dataset_manifest.json \
  --baseline profile-data/runs/stage-profile-20260817/baseline.json \
  --output-json profile-data/runs/stage-profile-20260817/analysis_summary.json \
  --output-csv profile-data/runs/stage-profile-20260817/analysis_table.csv
```

`analysis_summary.json` retains the independently reconstructed 72 groups,
CPU/Metal pairs, cold/warm differences, raw input hashes, validation outcome,
and uncertainty/accounting notes. `analysis_table.csv` is a flat 36-row table
for review.

## Handoff to item 2

Item 2 should treat the following as the exact baseline contract:

- source revision measured: `f9e63f26aa3fd66e306561a1bc6e0eab7a582a2a`;
  optimized Metal-enabled `cwebp` SHA-256
  `ce590e18fe005f0358cece1cc39df9dc26b6449ed9673ef0833bb5b57f28e10a`;
- corpus manifest:
  `profile-data/runs/stage-profile-20260817/dataset_manifest.json`, SHA-256
  `d89d22b0f25aa046a89343a840f48e567cc43624e5e279b3b57a3cca61bff89c`;
- raw baseline records:
  `profile-data/runs/stage-profile-20260817/records.jsonl`, SHA-256
  `84434068f6b544157b43426fce12c9cc1a6af32714f36d30f05c0b097a68af0b`;
- committed aggregate:
  `profile-data/runs/stage-profile-20260817/baseline.json`, SHA-256
  `3833005998d076a6cf95abb9e95345fffbd31355f2e5f8fd99c333aa9647b33a`;
- comparison configuration: lossless, exact, quality 75, methods 4 and 6,
  thread level 0; steady-state claims use warm groups only, while cold/init
  claims remain separate;
- dispatch contract: CPU uses `WEBP_METAL=0`; Metal uses `WEBP_METAL=1`,
  `WEBP_METAL_MIN_PIXELS=0`, `WEBP_METAL_HASH=1`, and
  `WEBP_METAL_HASH_MIN_PIXELS=0`.

Eligibility is path-specific. Predictor and cross-color candidates use the six
photo/method groups, all of which have cross-color=1 and hash=1. Palette
graphics have hash=1, cross-color=0, and are guardrails for forced-dispatch
regression rather than evidence for default eligibility. Textures have hash=1,
cross-color=0, and no palette; medium/large textures at both methods are the
cleanest backward-reference candidate subset. Medium/large photos at both
methods provide a second backward-reference subset, while all 18 warm Metal
groups remain end-to-end guardrails. Do not pool content classes or use the
forced results to choose a production threshold.

A candidate sample is eligible only if its case hash and encoder configuration
match, the record reports success, its required dispatch flags match the path
above, repeated output is deterministic, and decoded pixels match the CPU
reference. For an implementation intended to preserve the current algorithm,
also require the candidate backend bitstream hash to match the current backend
hash in `output_validation.json`. Report medians/MAD and the three-sample
observed range; do not present the bounds as confidence intervals.

The present data are sufficient to select the predictor path as a coarse item-2
target, but insufficient to choose between predictor search/residual application
and transform-map encoding. The next predefined measurement, if subroutine
selection is required, is to add non-overlapping probes around
`VP8LResidualImage` and the following `EncodeImageNoHuffman`, then rerun the
same nine-case matrix. For exact cold-cost decomposition, add separate probes
for device/queue creation, shader/library compilation, buffer growth, and first
command submission and rerun the existing cold-only matrix. Neither follow-up
was executed during this analysis.

## Implications for items 3--5

- Any item changing dispatch or eligibility should analyze photo cross+hash,
  palette-graphic hash-only, and texture hash-only as separate strata. The
  graphic slowdown is a required guardrail, not a threshold recommendation.
- Any item changing backward-reference, histogram, or bitstream code should use
  medium/large textures at both methods as its sensitivity subset and retain
  the full 18-group warm matrix for correctness/performance regression checks.
- Candidate benchmarking should reuse `libwebp-encoder-stage-v1` and this
  analyzer rather than introduce parallel stage names. The shared API already
  exposes lossless analyze, predictor parent, subtract-green, cross-color,
  hash/backrefs, histogram, Huffman, and the lossy import/analyze/stat-loop/
  encode-loop buckets.
- No lossy records exist in this run. Item 5 may reuse the trace API/schema,
  but cannot draw a lossy timing conclusion from this baseline. A lossy study
  requires its own predefined corpus/matrix and serialized benchmark release.
