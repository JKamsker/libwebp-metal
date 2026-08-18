# Metal acceleration in a modern libwebp encoder: a one-device research report

**Report date:** 2026-08-17
**Evidence revision:** `8faeda52939464cdc59244b0a55cc4331cf1eef1`
**Upstream base:** `4fe551df` (`v1.6.0-221-g4fe551df`)
**Scope:** Apple Metal encoder research; one device, one calendar day
**Publication audit:** 2026-08-18 claim/corpus addendum
**Status:** reproducible bounded research core; **not production-ready or upstream-ready**

## Abstract

This report evaluates a private Metal backend for three encoder stages in a
modern libwebp tree: lossless cross-color transform search and application,
lossless hash-chain candidate search, and opaque RGB/BGR-to-YUV420 import. Five
serialized experiments profiled the encoder, tested CPU/Metal crossover,
measured persistent and batched submission, compared kernel and memory
ablations, and evaluated a standalone lossless predictor-residual kernel. All
timed evidence was collected on 2026-08-17 on one Apple M4 Pro MacBook Pro.

The results do not support a general performance claim. Warm lossless behavior
depends strongly on content, method, size, and process lifecycle. A conservative
transform threshold candidate emerged on synthetic photos but was not compiled
because it lacks different-day and device-family confirmation. Batch submission
reduced warmed import-stage time but did not materially improve serial
end-to-end encoding. The only implementation promoted from the reproducible
publication core was an exact 2x2 lossy import kernel: relative to the
historical per-pixel Metal
grid, its median candidate/baseline time was 0.590 across six independent
process-level comparisons, with wins in 6/6 comparisons. This result changes the
kernel used after lossy Metal import is selected; it does not justify lowering
the existing 80 MP end-to-end selection threshold.

Correctness gates passed within the recorded scope, including decoded-pixel
equality, required bitstream equality, repeated-output checks, and transactional
fallback tests. Publication-core correctness claims use only deterministic
generated inputs. Experiment 4's external-image transform/hash rows,
experiment 5, and the historical migration baseline remain visible as
historical appendices but are excluded from publication support because the
three inputs have unresolved provenance and licensing. The retained evidence
remains limited by one device, one day, small sample counts, correlated warm
samples, and synthetic workloads. The report therefore supports publication as
a bounded research result, not deployment or upstream submission.

## Revision, device, and evidence boundary

The implementation began at upstream commit `4fe551df`. The backend-neutral
integration, five experiments, operator artifact commits, 2x2 promotion, and
final interpretation are present at `8faeda52939464cdc59244b0a55cc4331cf1eef1`.
The timed workloads preceded that final commit:

| Experiment | Source revision at timing | Artifact commit |
|---|---|---|
| 1. Encoder stage profile | `18fd520d5d7faf0645d461bded27c0ba7ee4a48e` | `0d925e3d` |
| 2. CPU/Metal crossover | `0d925e3dd33daab83d3717e3763d36d91bcfdca7` | `64309ffc` |
| 3. Persistent/batched Metal | `64309ffce345333c1a252e54e088e696dc3018c0` | `fbec692e` |
| 4. Kernel/memory ablations | `fbec692e7ec83336d65eb7c1b9441016d4495815` | `12d2c86b` |
| 5. Predictor residual | `12d2c86b9dc6c270611f7b9209dee2edf5c0f4c9` | `6f539ac6` |
| 2x2 implementation promotion | not a new timed run | `4e7df827` |
| Combined interpretation | no timed run | `8faeda52` |

All five experiments ran on 2026-08-17 on one MacBook Pro `Mac16,7` with an
Apple M4 Pro, 14 logical CPU cores, 24 GiB physical memory, and an integrated
20-core Metal 4 GPU. The operating system was macOS 26.5.1 build 25F80. The
preflight records report AC power, a charged battery, an active no-sleep
assertion, substantial free memory, no competing experiment operator, and no
thermal, performance, or CPU-power warning. These observations do not establish
constant frequency, temperature, energy use, or absence of background noise.

This is explicitly **one-device/one-day evidence**. It supplies no estimate of
device-to-device, Apple GPU-family, OS/compiler, or day-to-day variance. No
benchmark in `BENCHMARK_RESULTS.md` or experiments 1--5 was rerun for this
report. Claims below were checked against the committed raw artifacts,
summaries, validation records, source, and SHA-256 digests.

## Backend architecture

The encoder calls a private ABI-version-1 dispatcher in
`src/enc/accelerator_enc.h`; no installed `src/webp/*.h` API is changed. A
compile-time registry currently contains a Metal descriptor on Metal-enabled
builds. The descriptor advertises three complete encoder-stage capabilities:

| Stage | GPU responsibility | CPU authority retained |
|---|---|---|
| Lossless color transform | search independent tiles, choose and apply cross-color multipliers | call-site progress/cancellation and CPU fallback |
| Lossless hash chain | produce one packed match candidate per pixel | chain construction, left extension, skip policy, progress, and final decisions |
| RGB/BGR to YUV420 | exact integer conversion for eligible opaque, non-dithered, non-Sharp-YUV input | eligibility, plane allocation, unsupported modes, and CPU fallback |

Each request contains typed borrowed buffers. ABI v1 requires synchronous
completion and transactional output: a backend may retain private device,
pipeline, queue, and staging resources, but not request pointers, and caller
outputs must remain unchanged on decline or failure. The Metal implementation
compiles embedded shader source lazily, caches pipelines and geometrically
rounded shared buffers for process lifetime, and serializes reuse with mutexes.
This persistence explains the cold/warm distinction and also creates memory,
concurrency, startup, and runtime-compiler risks.

The common dispatcher recognizes `WEBP_ACCELERATOR=auto|metal|none`; the Metal
adapter also evaluates the stage-specific `WEBP_METAL*` controls. Defaults at
the evidence revision are 65,536 pixels for cross-color transform, 4,000,000
pixels for hash candidates, and 80,000,000 pixels for lossy import. Experiments
forced paths by setting minimums to zero. The experiments did not change these
three selection thresholds.

CMake enables Metal by default on Apple platforms, compiles Objective-C++, and
links Foundation and Metal; `makefile.unix` also enables Metal by default on
macOS. The standard Autotools inputs do not build the Metal translation units.
That build-path asymmetry is a release blocker, not an undocumented support
promise.

## Methods

### Experimental discipline

The five experiment rows had independent build and runtime gates and required
`WEBP_BENCHMARK_SESSION=exclusive` for timed execution. Operator reports record
clean worktrees, exact commands, preflight state, fixed matrices, non-overwriting
outputs, and post-run mechanical validation. No timing-based stopping rule or
matrix modification was made during execution.

CPU/Metal observations were paired when the harness paired them. The analysis
uses CPU/Metal for speedup and candidate/baseline or Metal/CPU where explicitly
named. Cold and warm observations are never pooled. Medians, median absolute
deviation, and observed ranges are descriptive statistics; they are not
confidence intervals for a machine or device population. Inner samples from a
single warm process are correlated, so experiment 4's warmed import analysis
first reduces each process to its median.

### Cold, warm, content, and method strata

"Cold" means a new process for the measured operation and includes lazy Metal
initialization where that path dispatches. "Warm" means one process reused after
one or more unmeasured same-shape warmups, as specified by each harness. Warm
samples measure persistent state; they are not independent fresh-machine
replicates.

Content labels are generator-defined strata, not natural-image taxonomies:

- `photo` is a deterministic synthetic formula with smooth spatial variation;
- `graphic` is a deterministic, low-color formula that can activate palette
  behavior and change the effective hash request size;
- `texture` is a deterministic, high-frequency formula;
- experiments 4 and 5 instead use three external real-image files whose
  provenance is unresolved.

Methods 4 and 6 are kept separate throughout. Experiment 5 correctness also
covers methods 0--6, but its timed matrix covers only methods 4 and 6. Quality
is 75 where the harness exposes a quality setting. Experiment 1 uses lossless
`-exact` and thread level 0; experiment 2 also fixes thread level 0.

### Experiment protocols

1. **Stage profile.** Nine generated PPM cases cross three content classes with
   512x512, 1600x1200, and 3000x2000 sizes. For each method/backend cell, three
   cold processes and three measured warm repetitions followed one discarded
   warmup. The run contains 252 records: 108 cold, 36 warmup, and 108 warm.
2. **Crossover.** A fixed, randomized paired matrix contains 424 pair blocks,
   1,648 measured samples, and 400 discarded warmups. Seeds 101 and 303 define
   tune and holdout synthetic inputs. Transform, hash, palette guards, and lossy
   import retain separate content, size, method, lifecycle, and seed-role
   strata. A stable candidate required the predefined five-percent margin and
   consecutive tested buckets.
3. **Persistent/batched submission.** A deterministic 3000x2000 synthetic RGB
   input, quality 75, method 4, batch sizes 1/2/4/8, and single versus one-command-
   buffer batch submission were measured for import and serial full encode.
   Each cell has five cold processes and twenty sequential warm samples after a
   same-shape warmup; each stage has 200 records.
4. **Ablations.** Four transform, five hash, and six lossy candidates were each
   compared with a 256-thread, otherwise-reset baseline. Transform/hash use
   seven alternating one-shot trials for each of three images and methods 4/6.
   Lossy import uses three warmed processes, 50 inner samples at 6 MP and 30 at
   12 MP. The full artifact has 414 pair blocks and 3,822 raw records.
5. **Predictor residual.** Three images, methods 4/6, seven alternating fresh-
   process runs, and CPU versus predictor-Metal produce 84 timing rows. The
   correctness gate covers methods 0--6, three fresh-process repetitions,
   decoded equality, exact streams, internal CPU-reference comparison, and an
   injected post-dispatch failure.

The protocol descriptions above preserve what ran. For publication, only
experiment 4's generated-input lossy suite is retained; its external-image
transform/hash suites and all of experiment 5 are historical appendices. The
claim-by-claim decision is recorded in
`doc/publication-evidence-audit-20260818.md`.

## Corpus provenance and licensing audit

| Corpus | Use | Provenance and availability | Publication status |
|---|---|---|---|
| Experiment 1 generated PPMs | stage profile and experiment-2 warm guards | Deterministic formulas in committed `scripts/encoder_stage_profile.py`; manifest and per-image hashes committed. The 73,639,443-byte generated PPM set is intentionally omitted and can be regenerated. | Reproducible from repository source. The generator is distributed with the repository under `COPYING`; no third-party asset is identified. |
| Experiment 2 synthetic inputs | transform/hash/lossy crossover | Deterministically generated by the committed benchmark runner from fixed dimensions, content labels, and tune/holdout seeds 101/303. | Reproducible from repository source; no external media identified. |
| Experiment 3 synthetic RGB | batch/import study | Deterministically generated by committed `extras/metal_encode_batch_experiment.c`. | Reproducible from repository source; no external media identified. |
| Experiment 4 lossy import | warmed 2x2 and memory/kernel comparisons | Deterministic bytes generated by committed `extras/metal_import_bench.c` at 6 MP and 12 MP. | Reproducible from repository source; no external media identified. |
| Publication corpus v1 | future correctness and predefined performance protocols; exact experiment-1 inputs | Versioned generator and portable manifest in `scripts/generate_publication_corpus.py` and `benchmarks/publication-corpus/manifest.json`; explicit seed, categories, dimensions, byte counts, and hashes. | Generated on demand. Generator, manifest, and generated PPMs use the BSD-3-Clause terms in `COPYING`; no third-party media is embedded. |
| `mitski.png` | experiment-4 transform/hash/recorded suites and correctness; experiment 5; historical baseline | SHA-256 `4dc95f6926a01f4c6ab32ac0559d8a4c3db1722bd26bde96efeff685ca7fdab0`; file absent from repository. | **Blocked:** no source URL, author, license, or redistribution terms found. |
| `corgi.jpeg` | experiment-4 transform/hash/recorded suites and correctness; experiment 5; historical baseline | SHA-256 `7991a0293e31ae253247be6e1fe3b9df1bf106c0ea4ec536bba40b5c7d0fd8d0`; file absent from repository. | **Blocked:** no source URL, author, license, or redistribution terms found. |
| `siamese.jpg` | experiment-4 transform/hash/recorded suites and correctness; experiment 5; historical baseline | SHA-256 `5c449f30fb52754c83c5aca1c10716bb7fbae9bfdac1c057da491d6174713c8e`; file absent from repository. | **Blocked:** no source URL, author, license, or redistribution terms found. |

The three names and hashes identify the measured bytes but do not establish a
right to redistribute them. Therefore the complete experiment-4 matrix and
experiment 5 are computationally auditable from their committed timing
artifacts but not independently rerunnable from this repository. The promoted
2x2 timing comparison itself uses generated bytes; the missing files affect the
full matrix's transform/hash/recorded suites and its external-image correctness
gate. A publication package must either document the original sources, authors,
and licenses and make the exact bytes lawfully available, or rerun the frozen
protocols on a clearly licensed, versioned corpus and report the new evidence
separately. Substituting look-alike files under the same names would invalidate
the comparison.

The unresolved files no longer block the bounded publication core: that core
retains experiments 1--3 and experiment 4's generated-input lossy suite. They
still block exact reproduction and publication use of experiment 4's
transform/hash rows, experiment 5, and the historical migration baseline.
Publication corpus v1 does not retroactively replace those bytes.

The experiment-1 operator report and preflight contain a 62-character manifest
digest missing one `c6`. The actual SHA-256 of both byte-identical committed
manifest copies is:

```text
4711e88382816a1d1546bde24f044e37c3c6c6f9d5a47b2b3b625f40be8d973b
```

All nine generated input hashes passed validation. The transcription error does
not invalidate the samples, but the shorter digest must not be used for
verification.

## Results

### Experiment 1: encoder stage profile

All 18 case/method output-validation cells were deterministic within backend
and decoded identically across CPU and Metal. Warm end-to-end CPU/Metal ratios
(greater than one favors forced Metal) were:

| Content and size | Method 4 | Method 6 |
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

The profile shows why aggregate speedup is misleading. On photos,
`lossless_predictor` accounts for 43.8--47.6% of warm method-4 time and
44.7--89.9% of method-6 time, but that inclusive bucket combines selector,
residual, and predictor-map encoding. On textures, non-nested
`lossless_backward_refs` accounts for 43.6--68.9%. On palette graphics, forced
Metal hash dispatch consumes 55.1--56.0 ms at 6 MP and 55--69% of total time.
Cold Metal initialization is approximately 24.6--31.2 ms and nearly vanishes
from measured warm records. These data select research targets; they do not
define a new threshold.

### Experiment 2: CPU/Metal crossover

Only isolated cross-color transform on synthetic photos produced a conservative
candidate in both tune and holdout data:

| Lifecycle | Method | First tested stable bucket | Supporting observations |
|---|---:|---:|---|
| cold | 4 | 768x768 (589,824 pixels) | all 12 tune/holdout observations at 768 and 1024 were at most 0.95 Metal/CPU |
| cold | 6 | 768x768 (589,824 pixels) | all 12 tune/holdout observations at 768 and 1024 were at most 0.95 Metal/CPU |
| warm | 4 | 192x192 (36,864 pixels) | every observation at all six tested buckets was at most 0.95 |
| warm | 6 | 192x192 (36,864 pixels) | every observation at all six tested buckets was at most 0.95 |

The candidate is recorded in
`scripts/metal_threshold_policy.m4pro-20260817.candidate.json` but is not
compiled. The current request lacks method and initialization state, and the
data lack a different-day and supported-GPU confirmation. The 65,536-pixel
transform default remains unchanged.

Hash crossover is content-dependent and inconclusive for policy. Warm synthetic
photos were 2.0--13.7% slower with Metal in every tested size/method cell; warm
textures became consistently favorable only from 1.92 MP at method 4 and 1.05
MP at method 6. Cold photos were slower through 6 MP; cold textures achieved the
five-percent margin only at the single largest bucket. Forced warm palette hash
was 2.16--3.23x slower, but palette packing halved request width, leaving all
measured requests below the existing 4 MP default. This argues against lowering
the threshold but does not establish an exclusion above 4 MP.

Lossy end-to-end import supplied no policy entry. Cold Metal/CPU medians ranged
from about 1.00 to 1.38; warm ratios were mostly 0.97--1.01 and frequently
crossed one. Even at 10,240x10,240 the practical end-to-end gain remained below
the predefined margin. The 80 MP default is unchanged.

### Experiment 3: persistent and batched Metal

Using one command buffer reduced warm import median time per image relative to
single submission by 34.6% at batch 2, 16.4% at batch 4, and 20.5% at batch 8.
The non-monotonic sequence and first-sample/allocation variability support only
the qualitative conclusion that submission can be amortized.

Cold import did not break even: batch submission was 16.7%, 10.0%, and 3.7%
slower at batch sizes 2, 4, and 8. Across cold and warm serial full-encode cells,
batch/single median time per image ranged from 0.988 to 1.015; the largest
observed improvement was 1.24% at cold batch 8. The private batch symbol and
harness remain research infrastructure. No common ABI, batch-size policy, or
default behavior was promoted.

### Experiment 4: kernel and memory ablations

#### Historical external-image transform/hash appendix (excluded from publication core)

Transform candidate pooled paired medians ranged from -0.45% to +1.57%; hash
candidates ranged from -0.09% to +0.51%. Every candidate had pairs on both
sides of one. Stratum-median signs also changed except for transform 512
threads, which consistently regressed by 0.87--2.75%. With nine such
comparisons and no correction model, these small movements are treated as
order/run variation rather than wins in the historical interpretation. These
rows depend on the three unresolved external images and support no claim in the
publishable core.

#### Generated-input lossy import (publication core)

Lossy import is summarized at the independent-process level:

| Candidate | Median candidate/baseline | Process wins | Disposition |
|---|---:|---:|---|
| exact 2x2 block grid | 0.590 (-41.0%) | 6/6 | promoted |
| 512 threads | 0.803 (-19.7%) | 6/6 | retained for research; not combined with 2x2 |
| contiguous copy | 0.941 (-5.9%) | 5/6 | rejected; only 1.3% at 12 MP and one regression |
| 128 threads | 1.008 (+0.8%) | 2/6 | rejected |
| unretained commands | 1.002 (+0.2%) | 2/6 | rejected |
| write-combined input | 0.999 (-0.1%) | 3/6 | rejected |

#### Promoted exact 2x2 lossy import kernel

The promoted kernel assigns one GPU thread to each 2x2 chroma block. It loads
up to four RGB pixels once, emits the corresponding one-to-four Y samples, and
computes one U/V pair with the same integer arithmetic and gamma table behavior
as the previous per-pixel grid. Odd widths and heights are bounds-checked. A
Metal function constant specializes the branch, so the selected path does not
pay for the inactive grid.

The checksum, bitstream, forced-dispatch, and variant correctness gates passed.
At the final evidence revision, 2x2 is the ordinary Metal specialization;
`WEBP_METAL_LOSSY_BLOCK_2X2=0` can select the legacy per-pixel grid only when
the ablation experiment is compiled and enabled. The experiment did not measure
the 2x2 grid combined with 512 threads, so their ratios cannot be multiplied or
assumed independent. It measured 6 MP and 12 MP warmed imports, not the 80 MP
end-to-end default threshold. Promotion is therefore an implementation choice
inside an already-selected Metal path, not a crossover-policy claim.

### Historical experiment 5: predictor residual (excluded from publication core)

The 84-row fresh-process CSV was negative in every median stratum:

| Input | Method 4 Metal/CPU | Method 6 Metal/CPU |
|---|---:|---:|
| `mitski.png` | 1.039 | 1.034 |
| `corgi.jpeg` | 1.017 | 1.014 |
| `siamese.jpg` | 1.011 | 1.008 |

Metal was slower in 37 of 42 paired comparisons. The median absolute penalty
was 30--40 ms in every input/method stratum, consistent with adding a cold
pipeline, upload, dispatch, wait, and readback boundary. The two largest-image
percentage effects approach the CSV's centisecond resolution, but no stratum
shows a positive median.

The recorded interpretation rejected the standalone stage for promotion. Its
doubly gated source remains unchanged. Because every input is one of the three
unresolved external files, the six-stratum result and its correctness run are
historical evidence, not reproducible publication claims. The appendix neither
supports a general predictor conclusion nor rules out a fused or resident
predictor selector and residual pipeline.

### Historical migration baseline: recorded only

`BENCHMARK_RESULTS.md` records, but does not retain raw trials for, 2.092--2.593x
complete-lossless speedups, 1.376--1.758x hash-search speedups, and 2.806--2.818x
warmed-import speedups on the M4 Pro. It also records decoded-pixel equality,
hash/lossy byte identity where required, and lossless file-size increases of
0.020--0.468% for the cross-color path.

Those values are **recorded-only historical claims**. The repository lacks the
original per-trial records, commands as executed, complete environment capture,
and available/licensed input corpus. They were not independently reproduced for
this report and are not used to justify the 2x2 promotion or threshold policy.

## Rejected and inconclusive paths

| Path | Decision and reason |
|---|---|
| Transform threshold change | candidate recorded, not compiled; one device/day and request lacks method/lifecycle state |
| Hash threshold or content rule | rejected/inconclusive; photo, texture, palette, cold, and warm strata disagree |
| Lossy threshold reduction | rejected; end-to-end crossover margin not met |
| Common batch ABI/default | not promoted; import amortizes but serial end-to-end encoding is neutral |
| Transform ablations | historical disposition only; external-image evidence excluded from publication core |
| Hash ablations | historical disposition only; external-image evidence excluded from publication core |
| 512-thread lossy kernel | inconclusive; promising alone, unmeasured with promoted 2x2 and on other devices |
| Other lossy memory/command changes | rejected; small, inconsistent, or size-specific effects |
| Standalone predictor residual | remains default-off; historical external-image result excluded from publication core |

## Correctness, determinism, and fallback contracts

ABI v1 has three results. `SUCCESS` permits the caller to consume complete host-
visible output. `NOT_RUN` means unavailable, disabled, below threshold, or
declined; outputs must be unchanged and another backend or CPU may run. `ERROR`
means an attempted accelerator operation failed; outputs must still be
unchanged, the accelerator chain stops, and CPU fallback runs. The current
Metal boolean adapter maps both declines and failures to `NOT_RUN`, so error
classification and telemetry remain incomplete even though CPU fallback is
preserved.

The evidence supports these bounded contracts:

- lossless outputs must always decode to the same pixels as CPU/input;
- hash candidates and eligible RGB-to-YUV conversion are expected to be CPU-
  equivalent and are covered by focused bitstream or plane/checksum gates;
- cross-color transform selection may differ from CPU because the independent-
  tile heuristic and floating-point scoring may choose a different legal
  transform; decoded lossless pixels, rather than stream identity, are the
  primary contract;
- `DETERMINISTIC` means repeated calls on one backend, device, and software
  stack produce the same stage output. No cross-device or cross-OS determinism
  claim is made;
- experiment 5's injected post-dispatch failure left the destination unchanged
  and reproduced the CPU stream; the batch verify-only gate likewise exercised
  transactional rejection;
- unsupported alpha, Sharp-YUV, dithering, negative-stride, unavailable-device,
  disabled, and below-threshold cases remain CPU-authoritative.

For the publication core, experiment 1 passed repeated CPU and Metal stream
equality within backend and CPU/Metal decoded-pixel equality for all 18
case/method cells. Experiment 2
reported zero decoded-pixel, required bitstream, input-hash, dispatch-marker, or
repeated-hash contract failures. Experiment 3's untimed 97x65 verification
matched CPU, single Metal, and batched Metal streams. Experiment 4's generated
lossy-import rows passed checksum and exact variant checks. The remaining
experiment 4 checks and experiment 5's internal-reference, exact-stream,
repeated-run, decoded-pixel, and injected-fallback checks are retained only as
historical external-image evidence. These are focused tests, not a substitute
for fuzzing, sanitizers, adversarial dimensions, cancellation, or a device
matrix.

## Statistical limitations

- All timing evidence comes from one M4 Pro on one day; the unit of hardware
  replication is one.
- Most strata have three, five, or seven independent process observations.
  Warm iterations within one process are correlated.
- Medians, MAD, ranges, and paired ratios are descriptive. No population model,
  confidence interval, power analysis, or false-discovery correction is claimed.
- Fifteen experiment-4 candidates create a multiple-comparison burden. Small
  sign-changing effects are deliberately rejected.
- Synthetic photo/graphic/texture formulas test controlled structures but do
  not estimate real-world content frequency or workload mix.
- Stage timers are inclusive. A parent timer minus a nested Metal timer is an
  accounting remainder, not a clean CPU-stage measurement.
- Experiment 3 covers one 6 MP synthetic input, quality 75, method 4, and a
  serial encoder. It is not a concurrency, throughput, memory, or service-level
  experiment.
- Experiment 4's 2x2 timing result covers deterministic generated bytes at
  warmed 6 MP and 12 MP. The full experiment's external-image correctness gate
  is not independently rerunnable. Neither supplies a cold, 80 MP, energy, or
  cross-device estimate.
- Historical experiment 5 uses unresolved external inputs, centisecond shell
  timing, and cold processes. It is excluded from the publication core.
- No experiment records GPU energy, peak retained allocation, queue contention,
  multi-threaded application behavior, or long-run thermal equilibrium.

## Reproducibility

Generate and verify the portable publication corpus at the current revision;
this is untimed and requires no benchmark lease:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-publication-corpus --verify
python3 scripts/test_publication_corpus.py
```

### Verify the committed evidence without timing

From a clean checkout of the evidence revision:

```sh
git checkout 8faeda52939464cdc59244b0a55cc4331cf1eef1

shasum -a 256 \
  profile-data/dataset/manifest.json \
  profile-data/runs/20260817-191358/dataset_manifest.json \
  profile-data/runs/20260817-191358/records.jsonl \
  profile-data/runs/20260817-173551-experiment-2-crossover-focused/raw.jsonl \
  profile-data/runs/20260817-184558-experiment-3-metal-batch/item3-import-3000x2000.jsonl \
  profile-data/operators/experiment-4-metal-ablation-20260817T191001Z/raw_results.jsonl \
  profile-data/operators/experiment-5-metal-predictor-20260817T2003Z/predictor-cold.csv

python3 scripts/encoder_stage_profile.py summarize \
  profile-data/runs/20260817-191358/records.jsonl \
  --output /tmp/libwebp-metal-stage-baseline.json
python3 scripts/test_experiment_guards.py
python3 -m json.tool \
  profile-data/runs/20260817-173551-experiment-2-crossover-focused/validity.json \
  >/dev/null
python3 -m json.tool \
  profile-data/operators/experiment-4-metal-ablation-20260817T191001Z/validation.json \
  >/dev/null
```

After a Metal-enabled build, the manual correctness entry point is:

```sh
scripts/test_metal.sh examples/test_ref.ppm
```

Regenerate the omitted experiment-1 corpus and verify all canonical metadata
and hashes:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-metal-stage-dataset --verify
```

The publication manifest is path-independent and byte-identical at every output
location. Historical experiment-1 run manifests embed local paths, but their
nine image hashes are exactly the publication-corpus v1 hashes.

### Historical timed commands

Timed reproduction requires an Apple Metal device, a clean checkout of each
row's source revision, an exclusive benchmark lease, and the exact commands in
the corresponding operator report. The authoritative reports are:

- `profile-data/runs/20260817-191358/experiment-1-stage-profile-operator-report.md`;
- `profile-data/runs/20260817-173551-experiment-2-crossover-focused/experiment-2-crossover-focused-operator-report.md`;
- `profile-data/runs/20260817-184558-experiment-3-metal-batch/experiment-3-metal-batch-operator-report.md`;
- `profile-data/operators/experiment-4-metal-ablation-20260817T191001Z/operator-report.md`;
- `profile-data/operators/experiment-5-metal-predictor-20260817T2003Z/operator-report.md`.

The released timed command forms were the following; sanitized local absolute
paths are represented by explicit placeholders:

```sh
# Experiment 1, at 18fd520d5d7faf0645d461bded27c0ba7ee4a48e
WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1 \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/encoder_stage_profile.py run \
  --encoder examples/cwebp --dataset-dir profile-data/dataset \
  --output-dir profile-data/runs --methods 4 6 --backends cpu metal \
  --quality 75 --cold-repetitions 3 --warm-repetitions 3

# Experiment 2, at 0d925e3dd33daab83d3717e3763d36d91bcfdca7
WEBP_METAL_CROSSOVER_EXPERIMENT=1 \
WEBP_BENCHMARK_SESSION=exclusive \
scripts/run_metal_crossover_operator.sh

# Experiment 3, at 64309ffce345333c1a252e54e088e696dc3018c0
WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_BATCH_EXPERIMENT=1 \
WEBP_METAL_BATCH_SIZES='1 2 4 8' WEBP_METAL_COLD_REPETITIONS=5 \
WEBP_METAL_WARM_ITERATIONS=20 \
scripts/run_metal_batch_experiment.sh extras/metal_encode_batch_experiment \
  /absolute/new/output/item3-import-3000x2000.jsonl 3000 2000

WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_BATCH_EXPERIMENT=1 \
WEBP_METAL_BATCH_SIZES='1 2 4 8' WEBP_METAL_COLD_REPETITIONS=5 \
WEBP_METAL_WARM_ITERATIONS=20 WEBP_METAL_EXPERIMENT_STAGE=encode \
scripts/run_metal_batch_experiment.sh extras/metal_encode_batch_experiment \
  /absolute/new/output/item3-encode-3000x2000.jsonl 3000 2000

# Experiment 4, at fbec692e7ec83336d65eb7c1b9441016d4495815
WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_ABLATION_EXPERIMENT=1 \
python3 scripts/benchmark_metal_ablation.py --run \
  --output /absolute/new/output \
  --input mitski=/licensed/corpus/mitski.png \
  --input corgi=/licensed/corpus/corgi.jpeg \
  --input siamese=/licensed/corpus/siamese.jpg

# Experiment 5, at 12d2c86b9dc6c270611f7b9209dee2edf5c0f4c9
WEBP_METAL_PREDICTOR=1 WEBP_BENCHMARK_SESSION=exclusive RUNS=7 \
scripts/benchmark_predictor_metal_experiment.sh \
  /absolute/new/output/predictor-cold.csv \
  /licensed/corpus/mitski.png /licensed/corpus/corgi.jpeg \
  /licensed/corpus/siamese.jpg
```

Each command assumes the exact build and untimed correctness prerequisites in
its operator report. Paths must be new/non-overwriting. The `/licensed/corpus`
placeholder means hash-matching inputs whose provenance and use rights have
first been resolved; it does not imply that such a directory is committed.

Experiments 1--3 can recreate their synthetic inputs from committed source.
Experiments 4--5 cannot be rerun exactly until the three hash-matching files are
available with documented rights. Do not substitute files or rerun a frozen
historical matrix from the final revision and label it the original experiment.

### Key artifact digests

| Evidence | SHA-256 |
|---|---|
| experiment 1 records | `a41945ac7d9bed4ae7fa30d6444122722f02d577d96ea5f7a9108056ccf0a874` |
| experiment 1 output validation | `6ef268569ca599051192ec8a4ab6e6861c1db8d1e1e6771afc8d122fb14c5309` |
| experiment 2 raw | `ab39ee2857a79f9699c3b54fd69fac7705c91cdf35cb06ab174916aef12a2184` |
| experiment 2 validity | `1b3428e3f6f409a9025629b2892d5e668055f35a57b45322df32f68defa09641` |
| experiment 3 import / encode | `1c7719b075b2fa371c4b109692f56bf43e83be425b5508eee44e8f0edcf325dd` / `693a881a4c0035b4bed48f9421ec3b8c1959912396172ae291c8f2f12ab2d405` |
| experiment 4 raw / validation | `284571cc0186d62405e73f1dd16e651ae7a1588cadf4be908ef376fa3f4c1c1c` / `2d288ba9d25b8e81967f3c240db8292d2ca1024e630b7dae3f71a1ac397ddd31` |
| experiment 5 CSV / validation | `b8f0d259ad841079f926693b79dd0ca2571c0d0473eee053bc161870e142f149` / `7384f24ea3b21c75b0e29db27832178ca9828331b338070165526c67870777bf` |

## Risks and unresolved publication blockers

1. **Historical corpus provenance and licensing:** the source, author, license,
   and redistribution terms for `mitski.png`, `corgi.jpeg`, and `siamese.jpg` are
   unresolved. This blocks publication and exact reproduction of experiment
   4's transform/hash rows, experiment 5, and the historical baseline, but not
   the generated-input publication core.
2. **Missing historical raw evidence:** `BENCHMARK_RESULTS.md` has aggregate
   numbers but no raw trials, executed command log, or complete environment
   capture. Those claims must remain labeled recorded-only or be rerun under a
   new, versioned protocol.
3. **One-device/one-day scope:** there is no supported-device, different-day,
   OS, compiler, or cross-device determinism matrix. This blocks threshold and
   readiness claims.
4. **Build/distribution gap:** Autotools omits Metal; installed-library ABI and
   static-consumer framework linking have not been demonstrated across build
   modes.
5. **Correctness depth:** no sanitizer/fuzzer campaign, broad natural-image corpus,
   adversarial dimensions/strides/formats, device-loss, cancellation, or
   concurrent-encode campaign is part of this evidence package.
6. **Operational behavior:** runtime shader compilation, process-global
   environment selection, persistent buffers, serialized access, lack of trim,
   and coarse error classification remain unresolved support risks.
7. **Output policy:** the cross-color heuristic can produce a different legal
   lossless bitstream and has only same-device determinism evidence. A release
   must define acceptable size/output drift before default enablement.
8. **Publication metadata:** before external release, assign durable artifact
   URLs/version identifiers and document authorship, review, and archival
   location; repository-relative paths alone are not a long-term archive.

These blockers do not prevent publishing the candid, reproducible bounded core
with the limits above. They do prevent describing the entire historical archive
as reproducible or the implementation as production-quality, supported, or
ready for upstream submission.

## Future work

- Rerun frozen protocols on at least two days and a supported Apple GPU-family
  matrix, retaining compiler/SDK versions and cold/warm, energy, memory, and
  thermal state.
- If the historical external-image results are to be published, provenance-
  clear the exact bytes. Otherwise define any natural-image follow-up as a new
  protocol with its own version, corpus rights/hashes, default-off build/runtime
  gates, and exclusive-session refusal; never relabel it as an item 1--5 run.
- Confirm the 2x2 kernel on odd/small/large dimensions, at and above the 80 MP
  threshold, and on multiple GPU families; measure its interaction with 512
  threads rather than multiplying independent ratios.
- Split the inclusive predictor bucket into selector, residual, and predictor-
  map encoding; investigate a resident/fused boundary only if correctness can
  remain transactional.
- Target texture backward-reference selection and exact candidate evaluation,
  where the profile shows independent CPU work, without moving order-sensitive
  policy into a kernel.
- Design content and lifecycle eligibility only after the measurement matrix
  supports it. A single pixel threshold cannot represent the current cold/warm
  and photo/texture/palette differences.
- Complete Metal-on/off build, install, link, ABI, sanitizer, fuzz, failure-
  injection, cancellation, and concurrent-use CI before considering an
  upstream experimental backend.
- Preserve the private synchronous ABI until ownership, memory limits,
  cancellation, and batch lifecycle have explicit contracts; do not expose
  accelerator handles in the public WebP API prematurely.

## Conclusion

The study establishes that a backend-neutral, CPU-fallback Metal experiment can
be evaluated reproducibly for synthetic workloads and audited from committed
raw artifacts. It also establishes that performance policy is content- and
lifecycle-dependent: several attractive aggregate or stage-level results do not
survive stratification. The exact 2x2 import grid is the sole promoted kernel
change, backed by a large within-device warmed stage effect and focused
correctness gates. Threshold changes and generalized batching are not promoted.
External-image ablations and the standalone predictor-residual result retain
their historical implementation dispositions but are not publication-core
conclusions.

The appropriate claim is narrow: on one Apple M4 Pro on 2026-08-17, under the
committed protocols and limitations, the 2x2 grid improved an already-selected
warmed Metal import stage while preserving the tested output contracts. The
evidence does not establish production quality, general Apple performance, or
upstream readiness.
