# Research integration record (2026-08-17)

Post-integration operator results and the final Sol dispositions are in
[experiment-series-analysis-20260817.md](experiment-series-analysis-20260817.md).
That report promotes only the exact 2x2 lossy kernel; it leaves the recorded
experiment guards and public compatibility boundary unchanged.

## Scope and ancestry

This branch integrates the completed Metal research work onto clean main
`ad0a198c1664b7ee0c4c106dd3c1d470fff49c9c`. The architectural root is
`15ce1de9bf8aac13b5ec722929d8cf22fcfd03c1`: its private
`WebPEncoderAccelerator` descriptor remains the only owner of normal encoder
dispatch, capability discovery, CPU fallback, synchronization, and backend
selection. No CUDA implementation was revived.

The research commits were reconstructed instead of blindly cherry-picked so
overlapping call sites/build files could be reconciled before entering the
combined history and local metadata could be removed. Source-to-integration
provenance is:

| Item | Source commit(s) | Integrated commit(s) |
|---|---|---|
| 1 | `f9e63f26`, `c723ce39`, `26291748` | `94ac7ec4`, `5b4e1a94`, `17e54328` |
| 2 | `645917ca`, `5abb02bf` | `afeb8392`, `bbb6a412` |
| 3 | `a9629f81` | `c62ab477` |
| 4 | `5428873b` | `d873bd2c` |
| 5 | `c1a4a3bb` | `551b0911` |
| 7 | `08558987` | `8dea2580` |
| 8 | `200f25e2` | `501d56d0` |

## Included and reconciled work

### Item 1: profiling, operator artifacts, and analysis

Included the full three-commit logical history: opt-in encoder stage
instrumentation, `cwebp -profile_repetitions`, collection/validation/analysis
scripts, protocol documentation, sanitized raw records and aggregate analysis,
and the Unix makefile fix that preserves platform flags when callers override
`CFLAGS`. Profiling is now omitted unless
`WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT` is selected and remains inactive
without `WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1` plus the exclusive lease.

Seven recorded absolute checkout paths were replaced with `<repo>` before the
data commit was created. Machine records already omitted serial number,
hardware UUID, and provisioning UDID; that privacy boundary was retained.

### Item 2: crossover groundwork and focused preset

Included the internal runner, orchestration/analyzer, threshold schema,
deliberately untuned policy, exhaustive/focused presets, operator wrapper, and
protocol documentation. The runner is non-installed and its CMake target is
off by default. Plan and smoke modes remain untimed. Every path that reads a
clock now requires `WEBP_BENCHMARK_SESSION=exclusive`; the Python run command
also retains its explicit acknowledgement.

### Item 3: persistent/batched prototype

Included reusable-state lifecycle findings, a transactional batch
implementation, deterministic synthetic harness, result schema, documentation,
and correctness-only `--verify-only` mode. The batch request was changed from a
Metal-owned `WebPPicture` wrapper to the exact backend-neutral
`WebPAcceleratorRGBToYUVRequest` buffer shape. It is not a descriptor ABI v1
stage: the private symbol is compiled only with
`WEBP_BUILD_METAL_BATCH_EXPERIMENT`, requires
`WEBP_METAL_BATCH_EXPERIMENT=1`, and the timed mode additionally requires the
exclusive-session gate.

The source memo's proposed competing `Create`/`Destroy` interface was replaced
with an integration section pointing to `ACCELERATOR_BACKEND_DESIGN.md`.
Promotion still requires a versioned neutral batching boundary that both Metal
and CUDA could implement.

### Item 4: Metal ablations

Included all transform, hash, and lossy variants, the isolated import driver,
matrix/metadata harness, recorded aggregate baseline transcription, study
documentation, and expanded bitstream/decode correctness loops. Every variant
keeps its recorded baseline value unless an explicit environment flag changes
it. The import driver no longer joins the default Unix `all` target; CMake and
simple-make builds require `WEBP_BUILD_METAL_ABLATION_EXPERIMENT`. Variant
knobs remain inactive without `WEBP_METAL_ABLATION_EXPERIMENT=1`. Timed execution is
exclusive-session gated in both the Python harness and driver.

The item 3 batch packing and item 4 lossy variants were reconciled in one Metal
implementation: each batched dispatch honors the selected block/thread/command
variant, and contiguous readback is checked against explicit plane pointers and
strides rather than `WebPPicture` ownership.

### Item 5: predictor-residual experiment

Included the stage shortlist, isolated Metal implementation, transactional
failure/validation behavior, correctness and benchmark scripts, and the
call-site hook. It remains doubly opt-in. The generic source flag was renamed
to `WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT` /
`WEBP_USE_METAL_PREDICTOR_EXPERIMENT` so it cannot collide with item 3. No
descriptor v1 bit or request was reused or added; a future
`LOSSLESS_PREDICTOR_RESIDUAL` request is explicitly a versioned extension.
Local corpus paths in the memo were replaced with portable placeholders, and
the timed script gained the common session gate.

## Independent experiment guards (post-integration hardening)

The exact five-row build/macro/runtime matrix and independent build commands
are durable in [experiment-guard-matrix.md](experiment-guard-matrix.md). The
build options are, respectively:

1. `WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT`;
2. `WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT`;
3. `WEBP_BUILD_METAL_BATCH_EXPERIMENT`;
4. `WEBP_BUILD_METAL_ABLATION_EXPERIMENT`; and
5. `WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT`.

All default to off in both CMake and `makefile.unix`. Their exact runtime
opt-ins are `WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1`,
`WEBP_METAL_CROSSOVER_EXPERIMENT=1`, `WEBP_METAL_BATCH_EXPERIMENT=1`,
`WEBP_METAL_ABLATION_EXPERIMENT=1`, and `WEBP_METAL_PREDICTOR=1`. Timed
launchers additionally require `WEBP_BENCHMARK_SESSION=exclusive`. The
non-timed static gate command is `scripts/test_experiment_guards.py`; ordinary
CPU and Metal correctness commands are recorded in the linked matrix.

### Item 7: CI, performance signal, and rebase groundwork

Included portable CPU correctness, physical-Metal correctness, and isolated
performance workflows; deterministic corpus generation; raw sample analysis;
round-trip testing; and CI/rebase policy documents. `scripts/test_metal.sh`
combines item 7's configurable binary directory and required-dispatch markers
with every item 4 variant check. Performance collection now selects the
neutral `WEBP_ACCELERATOR=none|metal` policy at the top level and requires the
exclusive-session environment. Hardware diagnostics remove serial number,
hardware UUID, and provisioning UDID before upload.

### Item 8: publication decision

Included the publication-target memo and retained its original `ad0a198c`
audit as historical evidence. An integration update records the item 1--7
artifacts and remaining gaps. The research-report recommendation is unchanged;
no score or publication claim was upgraded without released measurements and
device evidence.

## Deliberately omitted or superseded pieces

* Unsanitized absolute worktree/corpus paths were not committed. No build
  product, Python bytecode cache, temporary output, benchmark output, or local
  environment dump belongs in the integration commit.
* Item 3's `WebPMetalImportRequest` / `WebPPicture` ownership shape and proposed
  competing public lifecycle API were superseded by the neutral typed request
  and existing descriptor lifecycle hooks.
* Item 4's automatic inclusion of `metal_import_bench` in the default Unix
  build was omitted; research drivers must be explicitly requested.
* Generic, overlapping experimental build-flag names were replaced with
  stage-specific names. All prototypes remain absent/inactive by default.
* Ungated direct timing entry points were not retained. Correctness-only smoke,
  plan, validation, and schema modes do not require a benchmark lease.
* Item 8 statements that items 1--7 were absent are preserved only as clearly
  labeled baseline-audit provenance, not current repository facts.

## Compatibility and architecture invariants

* `src/webp/*.h` is unchanged from `ad0a198c`; no installed public API or ABI
  surface was added. All accelerator and experiment headers are private.
* `SUCCESS` remains the only accelerator status that permits consuming output.
  `NOT_RUN` and recoverable `ERROR` leave caller output unchanged and lead to
  the existing CPU computation.
* Descriptor ABI v1 remains synchronous, transactional, typed per encoder
  stage, process-persistent, and serialized by each backend's private state.
* `WEBP_ACCELERATOR=none` is the backend-neutral CPU override. Metal-specific
  flags tune or isolate the Metal descriptor but do not own call-site dispatch.
* Default encoder behavior, threshold values, public entry points, and the
  three v1 stage bits are unchanged. CUDA can later provide another descriptor
  without changing encoder call sites.

## Validation record

No performance benchmark was run. Validation performed during integration:

* full simple-make CPU-only build of `cwebp` and `dwebp`;
* full simple-make default Metal build of `cwebp` and `dwebp`;
* neutral-interface fake backend, invalid descriptor, status, output, and CPU
  override tests;
* CPU fallback round-trip and the combined correctness/variant suite;
* forced Metal transform/hash/lossy correctness with dispatch-marker checks;
* stage-profiler schema, warm-role, summary, and Metal-marker smoke;
* item 2's nine-pair untimed correctness/determinism smoke and plan generation;
* item 3's small transactional batch bitstream comparison;
* item 5's methods 0--6, three-run determinism, decoded equality, internal
  validation, and injected post-dispatch fallback smoke;
* Python compilation, POSIX shell syntax, JSON parsing/schema checks, workflow
  YAML parsing, make dry runs, public-header diff, and refusal tests for every
  timed entry point.

CMake was not installed in the integration environment, so its configuration
and targets were inspected and statically checked but not configured or built
locally. The committed GitHub workflows provide the intended CMake coverage.

## Follow-up dependencies and remaining risks

* Item 1 consumers should use the sanitized `<repo>` path records and must not
  infer new crossover thresholds from stage share alone.
* Item 2 owns threshold promotion; `metal_threshold_policy.untuned.json` must
  remain the fallback until a released, same-runner study is accepted.
* Item 3 batching needs a neutral descriptor ABI extension, aggregate policy,
  memory limits, and cancellation semantics before encoder use.
* Item 4 variants need released measurements before any default changes; flags
  and case identifiers should remain stable for comparison.
* Item 5 promotion needs its dedicated typed request plus broader alpha,
  dimension, sanitizer/fuzzer, and device coverage.
* Item 7 workflows depend on a trusted physical Apple-silicon runner and CMake;
  performance results are signals, never portable correctness gates.
* The standard Autotools path still does not compile the Metal translation
  units. Cross-device determinism, installed-library ABI/symbol comparison,
  memory-pressure/failure injection, and CUDA implementation work remain open.
