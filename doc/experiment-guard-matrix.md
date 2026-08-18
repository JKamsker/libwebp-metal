# Research experiment guard matrix

The five prepared encoder experiments are independently and fail-closed
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

The 2026-08-18 publication audit adds no timing experiment. The bounded core
already has generated-input evidence, so there is no sixth build flag, runtime
flag, timing entry point, or reuse of rows 1--5. Publication corpus generation
and verification are untimed data-integrity operations:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-publication-corpus --verify
python3 scripts/test_publication_corpus.py
```

## Default and isolation guarantees

- Default CMake and Unix make builds define none of the five private macros.
  Item 1's source and CLI hook, items 2--4's drivers/targets, item 3's private
  batch symbol, and item 5's source/call site are omitted.
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
```

CMake uses the same names with `-D<name>=ON`. Items 2--5 also require
`-DWEBP_ENABLE_METAL=ON`; item 3 requires `-DBUILD_SHARED_LIBS=OFF`, and item 4
requires `-DWEBP_BUILD_EXTRAS=ON`. Each experiment target is deliberately
non-installed.

## Untimed guard validation

The focused test does not grant the benchmark lease, read benchmark clocks, or
run an encoder. It verifies default-off make commands, forced dry-run macro
isolation for all five rows, omitted driver targets, runtime refusal, lease
refusal, the promoted item-4 default/legacy correctness mapping, and the fact
that item 4's released timed matrix was not repurposed as a follow-up:

```sh
scripts/test_experiment_guards.py
```

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
