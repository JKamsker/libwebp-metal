# Metal crossover experiment

This experiment determines when an eligible encoder operation should use CPU
or Metal. It does not contain benchmark results, and the runtime defaults in
the encoder remain unchanged. The checked-in policy is deliberately untuned:
an absent policy entry means CPU.

## Scope and definitions

The matrix covers the three current Metal operations independently:

* `transform`: lossless cross-color transform search;
* `hash`: lossless hash-chain candidate search plus its CPU replay; and
* `lossy`: opaque, regular RGB-to-YUV import followed by lossy encode.

Each operation is crossed with square image size, deterministic content class
(`flat`, `gradient`, `graphic`, `photo`, and `noise`), encoder method 0 through
6, and execution mode:

* **cold** is the first encode in a new process. The timed region includes
  import, runtime shader/pipeline creation reached by the encode, buffer setup,
  and the encode, but excludes process launch and deterministic input creation.
* **warm** discards three in-process encodes and measures nine subsequent
  encodes. Pipelines and capacity-sufficient buffers are therefore reusable.

The synthetic classes make the workload distributable and reproducible. They
are deliberately different in spatial frequency and compressibility. Before a
policy is promoted beyond `candidate`, repeat the confirmation matrix on a
versioned real-image corpus owned by item 1, preserving its class labels and
holdout split. Synthetic-only results are not sufficient to claim a generally
representative speedup.

## Build and untimed checks

The runner is opt-in and is never installed:

```sh
cmake -S . -B build-metal-bench \
  -DCMAKE_BUILD_TYPE=Release \
  -DWEBP_ENABLE_METAL=ON \
  -DWEBP_BUILD_METAL_BENCHMARK=ON \
  -DWEBP_BUILD_CWEBP=ON \
  -DWEBP_BUILD_DWEBP=ON
cmake --build build-metal-bench -j --target \
  webp_metal_benchmark cwebp dwebp
scripts/test_metal.sh
python3 scripts/benchmark_metal.py smoke \
  --runner build-metal-bench/webp_metal_benchmark
```

The repository's simple Make build is also supported on macOS:

```sh
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  tools/webp_metal_benchmark examples/cwebp examples/dwebp
scripts/test_metal.sh
python3 scripts/benchmark_metal.py smoke \
  --runner tools/webp_metal_benchmark
```

`smoke` never asks the runner to read the timing clock. It checks two repeated
outputs for determinism, lossless decode equality, exact CPU/Metal bitstreams
for hash and lossy operations, and an operation-specific verbose marker proving
that the requested Metal path was reached.

The matrix can be counted without running an encoder or reading a clock:

```sh
python3 scripts/benchmark_metal.py plan
```

## Later exclusive benchmark session

Do not run these commands until the benchmark orchestrator grants the exclusive
session. Record power source, thermal state, background workload, and whether
the machine was allowed to cool before cold blocks. Use a Release build and
avoid running other builds or benchmarks concurrently.

The default full synthetic sweep is:

```sh
python3 scripts/benchmark_metal.py run \
  --runner build-metal-bench/webp_metal_benchmark \
  --output results/metal-crossover-raw.jsonl \
  --acknowledge-exclusive-session
python3 scripts/benchmark_metal.py analyze \
  --input results/metal-crossover-raw.jsonl \
  --output results/metal-crossover-candidate.json
```

For a short calibration pass, retain every dimension but reduce the methods,
sizes, and samples explicitly; do not use calibration output as policy:

```sh
python3 scripts/benchmark_metal.py run \
  --runner build-metal-bench/webp_metal_benchmark \
  --output results/metal-crossover-calibration.jsonl \
  --operations transform,hash,lossy \
  --contents flat,gradient,graphic,photo,noise \
  --methods 0,3,6 --seeds 101,202,303 \
  --sides 256,1024,4096 --cold-trials 3 --warm-samples 5 \
  --acknowledge-exclusive-session
```

The default matrix has 18,480 paired blocks (73,920 timed encodes) and includes 100 MP lossy
inputs (about 400 MiB for the source RGBA buffer, with additional encoder and
Metal allocations). Provisionally budget 2--7 wall-clock days and up to roughly
2 GiB peak resident memory on an Apple-silicon workstation; method 6 and
incompressible content dominate and may push the run beyond that range. Use the calibration
pass to replace this estimate with a machine-specific one before reserving the
full session. The controller writes and flushes each JSONL record immediately,
but intentionally refuses to overwrite an existing result file.

## Output contract and correctness gates

The raw output is JSON Lines. The first record contains schema version, exact
Git commit and dirty state, runner SHA-256, matrix parameters, platform, and
hardware strings. Every later record is one sample with:

* operation, CPU/Metal variant, content, dimensions, method, and seed;
* tune/holdout role, cold/warm mode, randomized pair ID, and trial;
* elapsed nanoseconds and whether the requested Metal dispatch was observed;
* input, encoded-stream, and decoded-pixel hashes plus encoded size.

CPU and Metal order is randomized reproducibly inside each close pair, and the
pair blocks are also randomized. A missing Metal marker makes a pair ineligible
rather than silently treating CPU fallback as Metal performance. Any lossless
decode mismatch, hash/lossy bitstream mismatch, or repeated-output mismatch
aborts the run. Raw data is immutable; analysis writes a separate candidate.

The policy representation is specified by
`scripts/metal_threshold_policy.schema.json`. Its status progresses from
`untuned` to `candidate` and only to `validated` after independent corpus and
machine confirmation. Missing combinations always select CPU.

## Conservative decision rule

For each operation/content/method/execution/size and for tune and holdout seeds
separately, analysis uses the median paired log time ratio and a deterministic
2,000-resample 95% bootstrap interval. A size wins only when there are at least
five eligible pairs and the upper confidence bound says Metal is at least 5%
faster. The per-content crossover is the smallest tested size for which that
condition holds on both tune and holdout data at that size and every larger
tested size, with at least two consecutive winning size buckets.

The installable candidate for an operation/method/execution combination is the
largest crossover across all content classes. If any class has no stable
crossover, no entry is emitted and CPU remains the fallback. Thresholds are
never interpolated below a tested bucket. This worst-class aggregation avoids
requiring a runtime content classifier and prevents a favorable class from
hiding a regression. A content-specific table should only be considered after
item 1 supplies a stable, cheap classifier and a new holdout experiment shows
that classification cost and mistakes preserve the margin.

Before promotion, repeat the neighborhoods immediately below, at, and above
each candidate on a different day and on each supported Apple GPU family. A
candidate that reverses, loses its margin, or relies on an unobserved dispatch
remains CPU.

## Dependencies and current interface limitations

This work is intentionally modular around the runner's JSON protocol:

* **Item 1 baseline/corpus:** final content generalization depends on its
  versioned image set, labels, CPU baseline flags, and holdout ownership. The
  synthetic generator is a reproducible engineering fixture, not a replacement
  for that baseline. Importing the corpus should happen in the controller, not
  in dispatch code.
* **Item 6 accelerator interface:** current lossless Metal state eagerly
  compiles the transform pipeline before the hash pipeline can run. Thus a cold
  hash measurement reflects the current shared setup coupling. Also, the lossy
  import occurs before `WebPEncode()` receives `WebPConfig.method`, and the
  accelerator calls expose neither a dispatch-status signal nor an explicit
  cold/warm context. A final method-aware runtime policy should be adapted at
  the item 6 boundary after it exposes operation identity, method, initialization
  state, and observed dispatch. The experiment dimensions and output schema do
  not depend on that implementation.

Until those dependencies land and confirmation data exists, do not translate a
candidate JSON file into compiled thresholds and do not claim a speedup.
