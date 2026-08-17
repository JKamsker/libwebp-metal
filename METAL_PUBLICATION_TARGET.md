# Metal publication-target decision memo

**Decision date:** 2026-08-17
**Status:** revised after integration of research items 1--7. The original
baseline audit below remains useful historical context for `ad0a198c`; current
evidence and remaining gaps are summarized in the integration update. No
benchmark was run while revising this memo.

## Integration update

The combined research branch materially improves the evidence package without
changing the publication recommendation:

* item 1 adds a reproducible opt-in stage profiler, sanitized raw records,
  output validation, and analysis;
* item 2 adds a gated crossover harness and focused operator preset, while the
  committed threshold policy deliberately remains untuned;
* item 6 places dispatch and fallback behind the private, versioned
  backend-neutral contract in `src/enc/accelerator_enc.h`, with typed borrowed
  buffers, transactional synchronous output, capability bits, lifecycle hooks,
  deterministic expectations, and a path for a future CUDA descriptor;
* items 3--5 retain batching, ablation, and predictor-residual research as
  compile-time/runtime opt-ins outside the stable v1 stage set; and
* item 7 adds portable CPU correctness CI, physical-Metal correctness CI,
  explicitly gated performance infrastructure, and an upstream-rebase policy.

These artifacts close the largest architecture, reproducibility, and CI-design
gaps in the original audit. They do not establish production readiness: this
integration ran no performance measurements; the crossover policy has no
promoted thresholds; cross-device determinism, sanitizer/fuzzer coverage,
installed-library ABI comparison, and broader failure/memory testing remain;
and the standard Autotools path still does not build the Metal translation
units. Local CMake validation also remains environment-dependent and must be
reported separately by each integration run.

Accordingly, publish first as a research report. The backend-neutral patch
series is now a better candidate for upstream design discussion, but the
experimental-backend exit criteria below still apply. The original numeric
score is not silently recomputed: a new score should follow reviewed CI/device
evidence and released crossover measurements.

## Decision

Publish the current work first as a **research report**, accompanied by the
experimental fork and an explicit reproducibility/limitations section.  Do not
present the fork as production quality and do not submit the current patch as
an upstream backend yet.

The fallback target is an **upstreamable experimental backend** after the
experimental-backend exit criteria below are met.  A production-quality fork
is a later option, not the fallback: it requires a larger compatibility,
support, and release commitment than current evidence justifies.

## Original baseline method and evidence boundary

### Facts observed in this repository

* `ad0a198c` is one local commit on `4fe551df` (current upstream history in
  this checkout).  It adds 1,500 lines in 12 files, including two Objective-C++
  implementations, build plumbing, a script, and two project documents.
* The implementation accelerates three encoder-only stages: lossless
  cross-color search, lossless hash-chain candidate search, and an opaque,
  non-dithered RGB/BGR-to-YUV420 conversion.  The integration deliberately
  retains CPU paths for unsupported conversion modes and when Metal returns
  failure.  See `src/enc/predictor_enc.c`,
  `src/enc/backward_references_enc.c`, and `src/enc/picture_csp_enc.c`.
* The only new interface header is private
  (`src/enc/metal_enc.h`); it is not among CMake's installed public headers.
  No public `src/webp/*.h` file changes in the local commit.  This is evidence
  of no intended public C API addition, not proof of binary ABI compatibility.
* On Apple, CMake and `makefile.unix` enable Metal by default.  CMake compiles
  Objective-C++, links Foundation and Metal, and appends the two `.mm` files.
  The Autotools inputs (`configure.ac` and `src/*/Makefile.am`) have no Metal
  change, so that standard build path does not build this backend.
* Runtime activation and thresholds are controlled by process environment
  variables.  Metal source is compiled at runtime.  The code caches device,
  pipelines, queues, and growing shared buffers behind mutexes, so it has
  process-global state and serializes operations per accelerator state.
* `scripts/test_metal.sh` compares decoded lossless pixels for the
  cross-color path, compares hash-path output files byte-for-byte for methods
  0--6, and compares three lossy output files byte-for-byte.  It is a manual
  shell script, defaults to one PPM fixture, and is not registered by CTest or
  the optional fuzz-test CMake configuration.  The in-tree tests directory
  otherwise contains optional API fuzz targets.
* `BENCHMARK_RESULTS.md` records seven/ five/ three trial aggregation schemes,
  selected image names, and speedups for an M4 Pro.  It also records
  pixel-identical decode checks and a reported lossless size change of
  +0.020% to +0.468%.  The repository does not retain the input corpus, raw
  samples, harness source, commands, or machine-state capture needed to audit
  those statements here.
* The cross-color script expressly allows a different compressed stream while
  requiring lossless decoded pixels.  The hash and supported lossy paths claim
  byte identity.  The GPU cross-color scoring source uses floating-point
  `log2`, while its comments describe an independent-tile deterministic
  algorithm; no device/OS/compiler determinism matrix is present.
* `METAL_MIGRATION_TASK.md` lists migration acceptance criteria, including
  Metal-disabled builds, relevant existing tests, fallback behavior, and
  same-machine performance comparison.  It states that CMake validation was
  still pending in the recorded environment.  This checkout likewise has no
  `cmake` executable available for an independent configure/build check.

### Original assumptions and non-findings

* At the time of the baseline audit, research items 1--7 were not present in
  that checkout. The integration update above supersedes this particular
  assumption while preserving it as provenance for the original score.
* “Upstreamable” here means a patch likely to satisfy the usual expectations
  visible in this source tree: all supported build systems stay coherent,
  optional optimized paths preserve codec semantics, and testing is automated.
  It is an inference from repository structure, not a statement of an
  upstream maintainer decision.
* No ABI symbol comparison, sanitizer run, device-matrix test, source review
  by a Metal specialist, or benchmark was performed for this memo.

## Scored comparison (fitness **now**, 1--5)

Weights emphasize the obligations that differ among the targets.  A score of
3 means adequate only with disclosed limits; 5 means demonstrated and
release-ready for that criterion.

| Criterion | Weight | Production-quality fork | Research report | Upstreamable experimental backend |
|---|---:|---:|---:|---:|
| Correctness, quality, and determinism evidence | 25 | 2 | 3 | 2 |
| Build/distribution, platform, and ABI posture | 15 | 2 | 4 | 1 |
| Test coverage and reproducibility | 15 | 2 | 3 | 2 |
| Performance evidence and crossover rationale | 15 | 3 | 4 | 3 |
| Maintenance, security, and operational burden | 15 | 2 | 4 | 2 |
| Fit with observable upstream integration conventions | 15 | 2 | 4 | 1 |
| **Weighted total / 5** | **100** | **2.15** | **3.60** | **1.85** |

Interpretation:

* A research report can accurately present the architectural port, stated
  measurements, CPU fallback design, and the known Apple-only boundary
  without promising a stable supported product.  Its score does not validate
  the reported benchmarks; it reflects that limitations can be disclosed.
* A production fork has promising stated performance and a private API
  surface, but defaults Metal on for Apple builds, changes some encoded output,
  lacks build-path/test-matrix evidence, and takes on runtime shader/compiler
  and OS/device support obligations.
* The implementation is a reasonable *candidate* for an upstream experiment,
  but is least ready for that target: an upstream patch needs automated,
  maintained build/test coverage and a clearer portability and determinism
  contract than this standalone modernization commit currently supplies.

## Risks and missing evidence

| Area | Risk now | Evidence needed before raising the target |
|---|---|---|
| Codec semantics | Cross-color output can differ; GPU floating-point behavior has not been compared across Apple GPU families. | Corpus-wide decode, bitstream/size/quality policy, repeated-run and cross-device determinism results. |
| Correctness | Manual script covers narrow modes and fixtures; fuzzers do not exercise forced Metal paths. | Automated regression suite, adversarial dimensions/strides/formats/cancellation tests, fuzz/sanitizer evidence. |
| Build and ABI | Autotools omits the backend; CMake was not independently configured here; static consumers may need framework-link verification. | CI builds with Metal on/off across every supported build/distribution mode, installed-library link and ABI comparison. |
| Performance | Tables lack retained corpus, commands, raw samples, variance, thermal/power data, and crossover study. | Versioned harness/corpus manifest, raw results, warm/cold latency, memory/energy and threshold analysis on a device matrix. |
| Operations | Runtime shader compilation adds startup failure modes and a roughly 25 ms cost is noted in source; global buffers and mutexes affect concurrency and memory retention. | Failure-injection, memory/concurrency tests, lifecycle/telemetry policy, and either stable runtime-compilation justification or packaged shader strategy. |
| Maintenance/upstream | 1,500-line mixed C/Objective-C++ patch touches encoder internals and two build systems only. | Small reviewable patch series, backend abstraction rationale, ownership/support plan, and upstream maintainer feedback. |

## Milestones and exit criteria

### Research report — recommended immediate exit

Publish only when the report:

1. labels all benchmark numbers as results recorded in
   `BENCHMARK_RESULTS.md`, supplies exact commands/corpus provenance where
   available, and says which results have not been independently reproduced;
2. describes the three accelerated stages, default/override behavior,
   CPU fallbacks, output-equivalence promises, and the Apple-only scope;
3. includes this risk list and avoids a production-quality or upstream-ready
   claim; and
4. makes the commit/base revision and the manual test script discoverable.

### Upstreamable experimental backend — fallback exit

Reclassify only after all of the following are evidenced and reviewed:

1. all maintained build paths have an explicit Metal-on/off policy, with CI
   configure/build/install/link coverage; a disabled backend remains portable;
2. deterministic and codec-quality contracts are written down, and automated
   tests cover the full supported conversion surface, lossless decode fidelity,
   cancellation, fallbacks, and byte identity where promised;
3. Metal-forced tests are integrated into the normal test workflow and are run
   on a documented Apple GPU/OS matrix, with fuzz/sanitizer or equivalent
   adversarial coverage;
4. a reproducible benchmark package captures corpus licenses/hashes, commands,
   raw samples, variance, cold/warm behavior, memory, energy where practical,
   and justified thresholds; and
5. the patch is refactored into reviewable units with an explicit runtime
   shader, framework-linking, and long-term owner policy, then receives
   upstream design feedback.

### Production-quality fork — later exit

Require the experimental-backend criteria plus release branch/version policy,
security and dependency review, documented support/compatibility matrix,
crash/failure telemetry policy, reproducible release artifacts, and sustained
regression/performance evidence across supported Apple hardware.  Decide
whether output changes are acceptable as a documented encoder-quality tradeoff
before enabling acceleration by default in any release channel.

## What could change this decision

The recommendation should move to the fallback target when the integrated
groundwork produces reviewed evidence that closes the remaining build,
automated correctness, cross-device determinism/quality, threshold, and
maintenance gaps above.
It could move directly toward a production fork only if that evidence also
establishes a funded/supportable Apple release commitment and a defensible
default-on output policy.  Conversely, a demonstrated mismatch, flaky output,
unsupported build breakage, or irreproducible performance benefit strengthens
the research-report recommendation or limits publication to a negative result.
