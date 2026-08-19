# Research experiment guard matrix

The prepared encoder experiments are independently and fail-closed
guarded. `WEBP_ENABLE_METAL` controls ordinary supported Metal acceleration;
it is not an experiment umbrella and never enables any row below. There is no
shared experimental build or runtime switch.

| Item | Build option (CMake `ON`; Unix make `1`) | Private compile macro | Exact runtime opt-in | Non-installed hook or target |
|---|---|---|---|---|
| 1 encoder stage profile | `WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT` | `WEBP_USE_ENCODER_STAGE_PROFILE_EXPERIMENT` | `WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1` | `profile_enc.c`, coarse probes, `cwebp -profile_repetitions` |
| 2 CPU/Metal crossover | `WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT` | `WEBP_USE_METAL_CROSSOVER_EXPERIMENT` | `WEBP_METAL_CROSSOVER_EXPERIMENT=1` | `webp_metal_benchmark` |
| 3 persistent batch | `WEBP_BUILD_METAL_BATCH_EXPERIMENT` | `WEBP_USE_METAL_BATCH_EXPERIMENT` | `WEBP_METAL_BATCH_EXPERIMENT=1` | batch symbol and `metal_encode_batch_experiment` |
| 4 kernel/memory ablations | `WEBP_BUILD_METAL_ABLATION_EXPERIMENT` | `WEBP_USE_METAL_ABLATION_EXPERIMENT` | `WEBP_METAL_ABLATION_EXPERIMENT=1` | variant environment reads and `metal_import_bench` |
| 5 predictor residual | `WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT` | `WEBP_USE_METAL_PREDICTOR_EXPERIMENT` | `WEBP_METAL_PREDICTOR=1` | predictor source and call-site hook |
| 6 predictor boundary decomposition | `WEBP_BUILD_PREDICTOR_BOUNDARY_EXPERIMENT` | `WEBP_USE_PREDICTOR_BOUNDARY_EXPERIMENT` | `WEBP_PREDICTOR_BOUNDARY_EXPERIMENT=1` | boundary recorder, predictor/map probes, private repetition option |
| 7 backref exact decomposition | `WEBP_BUILD_BACKREF_EXACT_EXPERIMENT` | `WEBP_USE_BACKREF_EXACT_EXPERIMENT` | `WEBP_BACKREF_EXACT_EXPERIMENT=1` | boundary recorder, backward-reference probes, private repetition option |
| 8 focused backref cache search | `WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT` | `WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT` | `WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT=1` | dedicated two-clock recorder, cache-search probes, private repetition option |
| 9 cache-size serial sweep | `WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT` | `WEBP_USE_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT` | `WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=1` | recorder-free CPU implementation A/B, dedicated external runner, no CLI option |
| 10 cache-size single-pass slab | `WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT` | `WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT` | `WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=1` | recorder-free one-allocation CPU implementation A/B, dedicated external runner, no CLI option |
| 11 backref cost/traceback workspace | `WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT` | `WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT` | `WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT=1` | recorder-free CostManager workspace A/B, private test and external runner |
| 12 independent remote backref-cost workspace A/B | `WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT` | `WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT` | `WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1` | unchanged row-11 candidate under new source/symbol/runner names and a remote-only v1 protocol |
| 13 independent v2 remote backref-cost workspace A/B | `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT` | `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT` | `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT=1` | unchanged validated workspace candidate under wholly new v2 source/symbol/runner/protocol names |
| 14 independent v3 remote backref-cost workspace A/B | `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT` | `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT` | `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT=1` | unchanged validated workspace candidate with repository-context bundle admission and wholly new v3 identities |
| 15 independent v4 remote backref-cost workspace A/B | `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT` | `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT` | `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT=1` | exact v3 candidate with indexed Python archive return and independent lease/cleanup evidence channels |
| 16 independent v5 remote backref-cost workspace A/B | `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT` | `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT` | `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT=1` | unchanged recorder-free candidate with admitted makefile toolchain and indexed evidence on every controlled refusal |
| 17 backref-cost interval-search v1 | `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT` | `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT` | `WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1` | strictly-after-tail null-hint positioning index; separate untimed recorder build and recorder-free timed runner |
| 18 backref-cost interval-search v2 | `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT` | `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT` | `WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT=1` | PushInterval-local scan-derived append hint with narrow in-call maintenance; separate untimed recorder build and recorder-free timed runner |
| 19 backref-cost interval-search v3 | `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT` | `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT` | `WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT=1` | exact v2 PushInterval-local candidate under repaired receipt/mode infrastructure; separate v3-only untimed recorder and recorder-free timed runner |
| 20 backref-cost interval specialization v1 | `WEBP_BUILD_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT` | `WEBP_USE_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT` | `WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT=1` | production-shaped outer selection between baseline and distinct always-specialized v3-local-hint paths; separate untimed recorder and recorder-free runner |
| 21 backref-cost attribution v1 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT` plus attribution-only markers | `WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT=1` | diagnostic-only same-binary Time Profiler and coarse-stage attribution of clean baseline versus exact rejected specialization; no promotion authority |
| 22 backref-cost attribution v2 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT=1` | diagnostic-only same-binary coarse monotonic stage attribution with no profiler or attach rights; no promotion authority |
| 23 backref-cost attribution v3 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT=1` | diagnostic-only single-selected-DP coarse monotonic attribution; no profiler, attach rights, or promotion authority |
| 24 backref-cost attribution v4 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT=1` | diagnostic-only v3-semantic coarse attribution with mode/state-dependent evidence return; no profiler, attach rights, or promotion authority |
| 25 backref-cost attribution v5 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT=1` | diagnostic-only merged-v4 coarse attribution with independent compact control receipts and separately verified bounded bulk return; no profiler, attach rights, or promotion authority |
| 26 backref-cost attribution v6 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT=1` | diagnostic-only merged-v5 semantics with two-commit Phase-1 freeze/authorization identity and independently verified two-plane return; no profiler, attach rights, or promotion authority |
| 27 backref-cost attribution v7 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT=1` | diagnostic-only merged-v6 semantics with one framed directly-owned SSH transaction, in-session exact-child cleanup, and final absence footer; no profiler, attach rights, or promotion authority |
| 28 backref-cost attribution v8 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT=1` | diagnostic-only merged-v7 semantics with exact executable-identity process isolation over a frozen PID/PPID/comm snapshot and verified transport ancestors; no argv scanning, profiler, attach rights, or promotion authority |
| 29 backref-cost attribution v9 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT=1` | diagnostic-only merged-v8 semantics treating kernel `comm` as an exact opaque executable-name token, with optional separately verified path provenance; no argv scanning, profiler, attach rights, or promotion authority |
| 30 backref-cost attribution v10 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT=1` | diagnostic-only merged-v9 semantics treating complete raw `comm` as opaque, including slash/space-bearing values, with separately recorded lexical basename and no filesystem identity resolution; no argv scanning, profiler, attach rights, or promotion authority |
| 31 backref-cost attribution v11 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT=1` | diagnostic-only merged-v10 semantics proving a complete acyclic self-to-PID1 chain structurally and rejecting only exact denied raw `comm` or lexical-basename identities, with bounded identity-only refusal diagnostics; no argv scanning, profiler, attach rights, or promotion authority |
| 32 backref-cost attribution v12 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT=1` | diagnostic-only v11 semantics with a retained single-session incremental full-duplex SSH pump, online bounded frame validation, raw-stream persistence, and separate silent-operator/bulk-progress deadlines; no argv scanning, profiler, attach rights, or promotion authority |
| 33 backref-cost attribution v13 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT=1` | diagnostic-only v12 semantics with explicit REQUEST_WRITE/SILENT_OPERATOR/BULK_STREAM/FOOTERS transport attribution; magic and controls remain silent until a complete validated bulk declaration; no argv scanning, profiler, attach rights, or promotion authority |
| 34 backref-cost attribution v14 | `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT` | `WEBP_USE_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT` | `WEBP_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT=1` | diagnostic-only v13 semantics with compact digest-indexed evidence, a 768 KiB archive cap, and a strict 1 MiB total framed-response cap; no argv scanning, profiler, attach rights, or promotion authority |

Every runtime value is exact: values other than `1` are disabled. Every timed
launcher additionally requires `WEBP_BENCHMARK_SESSION=exclusive`. Correctness,
plan, schema, and guard-probe modes do not bypass a build or runtime guard, but
may remain untimed and therefore do not all require the lease.

## Post-series status

The completed-series dispositions are in
[experiment-series-analysis-20260817.md](experiment-series-analysis-20260817.md).
All five guard rows remain independent and default-off. The proposed production
changes were assessed independently; only the exact 2x2 lossy kernel is
promoted as a supported default. Under row 4 only,
`WEBP_METAL_LOSSY_BLOCK_2X2=0` now selects the superseded per-pixel grid as the
`legacy_per_pixel` regression control. The historical operator matrix and raw
evidence retain their original `block_2x2` candidate name and values.

The 2026-08-18 publication audit itself adds no timing experiment. The bounded core
already has generated-input evidence, so there is no sixth build flag, runtime
flag, timing entry point, or reuse of rows 1--5. Publication corpus generation
and verification are untimed data-integrity operations:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-publication-corpus --verify
python3 scripts/test_publication_corpus.py
```

The later next-cycle rows 6 and 7 are frozen in
[next-dominant-boundary-experiments-20260818.md](next-dominant-boundary-experiments-20260818.md).
They diagnose credible implementation boundaries and do not amend item 1--5.
Both first execution attempts failed before lease acquisition or timing; the
portable continuation then completed both serial matrices. Row 6 passed its
share criteria but failed a required recorder-overhead cell; row 7 failed its
standard-LZ77 share criterion in every required cell and one p95 overhead
criterion. Neither boundary is accepted. Both rows remain default-off research
diagnostics, and the complete evidence-to-decision audit is in
[next-boundary-experiment-evaluation-20260818.md](next-boundary-experiment-evaluation-20260818.md).

Row 8 is the independently gated next-cycle diagnostic frozen in
[backref-cache-search-experiment-20260818.md](backref-cache-search-experiment-20260818.md).
It does not rerun either rejected row: it measures only the evidence-supported
cache-size search and inclusive backref boundary with a dedicated two-clock
recorder. It cannot directly promote production code or support a GPU-speedup
claim. The completed matrix found cache-search majority share in every holdout
cell, but method-6 cold exceeded the frozen median-overhead limit. Row 8 is
therefore not accepted; it remains default-off reproduction instrumentation.
See
[backref-cache-search-experiment-evaluation-20260818.md](backref-cache-search-experiment-evaluation-20260818.md).

Row 9 is the recorder-free cache-size serial-sweep implementation A/B frozen in
[cache-size-serial-sweep-experiment-20260818.md](cache-size-serial-sweep-experiment-20260818.md).
All 18 correctness cells passed exactly, but every performance cell failed the
paired-median and p95 limits. Row 9 is rejected and retained only as default-off
negative research evidence. It changes no production behavior. See
[cache-size-serial-sweep-experiment-evaluation-20260818.md](cache-size-serial-sweep-experiment-evaluation-20260818.md).

Row 10 is the wholly independent, recorder-free single-pass contiguous slab
candidate frozen in
[cache-size-single-pass-slab-experiment-20260818.md](cache-size-single-pass-slab-experiment-20260818.md).
It preserves row 9's opposite topology: all cache-bit states stay live and the
reference stream is traversed exactly once. Row 9's samples and ratios are not
inputs to row 10. Its 18 correctness cells pass, but three of four required
holdout cells fail the paired-median limit. Row 10 is rejected and retained
default off as bounded negative research evidence; it changes no production
behavior. See
[cache-size-single-pass-slab-experiment-evaluation-20260818.md](cache-size-single-pass-slab-experiment-evaluation-20260818.md).

## Default and isolation guarantees

- Default CMake and Unix make builds define none of the private macros.
  Item 1's source and CLI hook, items 2--4's drivers/targets, item 3's private
  batch symbol, item 5's source/call site, rows 6--7's shared recorder, and row
  8's dedicated recorder, probes, environment reads, symbols, and private
  repetition options, and row 9's candidate source, runtime strings, symbols,
  test target, and runner, plus row 10's candidate source, runtime strings,
  symbols, test target, and runner are omitted.
- An ordinary Metal build continues to include the supported transform, hash,
  and RGB-to-YUV acceleration. Item 4's alternate environment knobs are read
  only when both its build macro and exact runtime opt-in are present.
- Selecting one row defines only that row's private macro. Build flags cannot
  activate another row, and runtime flags cannot compensate for a missing
  build flag.
- `WEBP_BUILD_METAL_BENCHMARK` and `WEBP_BUILD_METAL_ABLATION` are rejected
  legacy names. Use the exact row-2 and row-4 names in the table.
- No experiment changes an installed header, public symbol, descriptor ABI v1,
  caller ownership, CPU fallback, or transactional output rule.

## Independent build commands

Unix make examples (run one experiment flag at a time):

Run `make -f makefile.unix clean` before changing rows because the simple
makefile does not track preprocessor flags as object dependencies.

```sh
# Item 1
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=1 examples/cwebp

# Item 2
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT=1 tools/webp_metal_benchmark

# Item 3
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_METAL_BATCH_EXPERIMENT=1 metal-experiment

# Item 4
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1 metal-ablation-tools

# Item 5
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_ENABLE_METAL_PREDICTOR_EXPERIMENT=1 examples/cwebp

# Item 6
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_PREDICTOR_BOUNDARY_EXPERIMENT=1 examples/cwebp

# Item 7
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_BACKREF_EXACT_EXPERIMENT=1 examples/cwebp

# Item 8
make -f makefile.unix WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT=1 examples/cwebp

# Item 9 (CPU-only implementation A/B)
make -f makefile.unix WEBP_ENABLE_METAL=0 \
  WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=1 examples/cwebp

# Item 10 (CPU-only implementation A/B)
make -f makefile.unix WEBP_ENABLE_METAL=0 \
WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=1 examples/cwebp
```

```sh
WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT=1 examples/cwebp

WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1 examples/cwebp
WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT=1 examples/cwebp
WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT=1 examples/cwebp
WEBP_BUILD_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT=1 examples/cwebp
```

CMake uses the same names with `-D<name>=ON`. Items 2--8 require
`-DWEBP_ENABLE_METAL=ON`; items 9--17 explicitly use Metal off. Item 3 requires
`-DBUILD_SHARED_LIBS=OFF`, and item 4 requires `-DWEBP_BUILD_EXTRAS=ON`. Each
experiment target is deliberately non-installed.

## Untimed guard validation

The focused guard test does not grant the benchmark lease, read benchmark
results, or run an encoder. It verifies default-off make commands, forced
dry-run macro isolation for all twenty rows, omitted driver targets, runtime
refusal, lease refusal, the promoted item-4 default/legacy correctness mapping, and the fact
that item 4's released timed matrix was not repurposed as a follow-up:

```sh
scripts/test_experiment_guards.py
```

That guard also runs the pure untimed Darwin free-memory portability unit test.
It never calls the next-boundary `run` command or grants an exclusive session.

Normal correctness remains separate:

```sh
make -f makefile.unix clean
make -f makefile.unix WEBP_ENABLE_METAL=0 examples/cwebp examples/dwebp
scripts/test_roundtrip.sh

make -f makefile.unix clean
make -f makefile.unix WEBP_ENABLE_METAL=1 examples/cwebp examples/dwebp
scripts/test_metal.sh
```

Item-specific correctness commands must supply their row's runtime opt-in.
Item 4 additionally builds `metal-ablation-tools` so `scripts/test_metal.sh`
can use its `--guard-check` probe before testing variants. The exact experiment
protocols remain in their respective documents.

## Sequential measurement boundary

After a separate benchmark release, an operator may run items 1 through 5 in
sequence. Each delegated worker should receive only one row's predefined
command, build option, runtime opt-in, corpus/preset, output directory, and the
exclusive lease. Workers must return raw artifacts without interpreting or
tuning results; Sol owns cross-item interpretation and any policy decision.
