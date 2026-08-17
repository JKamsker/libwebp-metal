# Metal crossover experiment

This experiment determines when an eligible encoder operation should use CPU
or Metal. It does not contain benchmark results, and the runtime defaults in
the encoder remain unchanged. The checked-in policy is deliberately untuned:
an absent policy entry means CPU.

## Released operator pipeline

The normal operator workflow is the fixed
`scripts/metal_crossover_focused_v1.json` preset. It incorporates the item-1
operator commit `c723ce39` and Sol interpretation commit `26291748`; the
operator does not choose cases, dimensions, methods, repetition counts,
stopping rules, or a calibration outcome. There is no calibration phase.

After the exclusive benchmark session is released, the exact command is:

```sh
WEBP_BENCHMARK_SESSION=exclusive scripts/run_metal_crossover_operator.sh
```

The entry point performs a clean optimized Metal build, runs the existing
correctness suite and the untimed harness smoke gate, then executes the fixed
matrix and writes the resulting directory under `${TMPDIR:-/tmp}`. It refuses
to enter the timed phase unless `WEBP_BENCHMARK_SESSION` is exactly
`exclusive`, refuses to overwrite an output directory, and aborts on the first
correctness, determinism, reference-hash, or dispatch-proof failure.

The fixed matrix contains 424 randomized CPU/Metal pair blocks, 848 runner
processes, 1,648 measured records, and 400 discarded warmup encodes:

* all 18 item-1 case/method warm Metal groups are retained as end-to-end
  guards, with item-1 CPU and Metal bitstream SHA-256 references;
* transform evidence is restricted to photo content at methods 4 and 6, six
  sizes, and separate tune/holdout formulas;
* hash evidence keeps photos and textures as separate strata at methods 4 and
  6, emphasizing the medium/large back-reference sensitivity region;
* palette graphics are a separate warm forced-dispatch guard and are never
  pooled into hash threshold evidence; and
* lossy import uses methods 4 and 6 and bounded photo/graphic/texture size
  ladders. It remains a separate exploratory stratum because item 1 contains no
  lossy baseline.

Cold evidence uses a new process for every encode. Warm evidence uses one
process, discards fixed warmups, and measures fixed subsequent repetitions.
The largest input is 10,240 square: 400 MiB of source RGBA plus encoder and
Metal allocations. Provisionally reserve 45--150 minutes, 2 GiB of memory,
and 1 GiB of temporary disk headroom. The item-1 lossless portion should be
only minutes; high-resolution lossy method-6 cases dominate uncertainty. The
operator may not shorten or extend the run based on observed timings.

Successful output contains:

* `raw.jsonl`: immutable metadata and all paired sample records;
* `summary.json`: per-section/content/case/method/execution/role median, MAD,
  min/max, and paired Metal/CPU ratios without cross-content pooling;
* `validity.json`: the mechanical gate result and exact counts; and
* `policy-untuned.json`: an empty, CPU-fallback policy proving that the
  operator does not install or infer thresholds.

Sol must later inspect all four files. In particular, Sol decides whether any
size ladder supports a candidate, checks tune versus holdout direction and
noise, confirms the full 18-group warm guard outcome, and documents why every
missing combination remains CPU. Operator output is invalid unless
`validity.json` has `"valid": true`, all 424 pair blocks completed, all 1,648
records are present, CPU records have no Metal markers, each Metal record has
exactly its declared operation markers, repeated hashes are deterministic,
CPU/Metal decoded or bitstream equality matches the case contract, and all 36
item-1 backend/method reference hashes match.

## Scope and definitions

The threshold matrix covers the three current Metal operations independently,
plus a combined lossless mode used only for item-1 end-to-end guards:

* `transform`: lossless cross-color transform search;
* `hash`: lossless hash-chain candidate search plus its CPU replay; and
* `lossy`: opaque, regular RGB-to-YUV import followed by lossy encode.

The focused operation ladders use explicit rectangular or square dimensions,
deterministic content classes, methods 4 and 6, and execution mode:

* **cold** is the first encode in a new process. The timed region includes
  import, runtime shader/pipeline creation reached by the encode, buffer setup,
  and the encode, but excludes process launch and deterministic input creation.
* **warm** discards the preset's fixed in-process warmups and measures its fixed
  subsequent repetitions. Pipelines and capacity-sufficient buffers are
  therefore reusable.

The `photo`, `graphic`, and `texture` formulas reproduce the item-1 generator
when seed zero is used; nonzero fixed seeds provide tune/holdout variation.
They are deliberately different in spatial frequency and compressibility.
Before a policy is promoted beyond `candidate`, repeat the confirmation matrix
on a versioned real-image corpus owned by item 1, preserving its class labels
and holdout split. Synthetic-only results are not sufficient to claim a
generally representative speedup.

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
python3 scripts/metal_crossover_operator.py plan
```

## Separately reserved exhaustive preset

The focused operator is the only released item-2 command. A separate inherited
`scripts/metal_crossover_exhaustive_v1.json` preset preserves the broader
methods 0--6, content, size, repetition, and holdout study for a later multi-day
reservation. It is fully predefined but must not be substituted for the
focused command without a new serialized benchmark release.

Its scale can be inspected without encoding:

```sh
python3 scripts/metal_crossover_operator.py plan \
  --preset scripts/metal_crossover_exhaustive_v1.json
```

The exhaustive preset currently expands to 15,984 pair blocks, 31,968 runner
processes, and 63,888 measured records, plus 12,070 warmups. It has the same
400 MiB maximum source allocation and approximately 2--3 GiB peak memory, but
should be budgeted in days. There is intentionally no operator calibration or
runtime-dependent branch table: focused and exhaustive are two immutable,
separately released matrices.

## Output contract and correctness gates

The raw output is JSON Lines. The first record contains schema version, exact
Git commit and dirty state, runner SHA-256, matrix parameters, platform, and
hardware strings. Every later record is one sample with:

* operation, CPU/Metal variant, content, dimensions, method, and seed;
* tune/holdout role, cold/warm mode, randomized pair ID, and trial;
* elapsed nanoseconds and the exact set of observed Metal operation markers;
* input, encoded-stream, and decoded-pixel hashes plus encoded size.

CPU and Metal order is randomized reproducibly inside each close pair, and the
pair blocks are also randomized. A missing or extra Metal marker invalidates
the operator run rather than silently treating CPU fallback as Metal
performance. Any reference hash, decode, required bitstream, or repeated-output
mismatch aborts the run. Raw data is immutable; operator aggregation never
creates a candidate threshold.

The policy representation is specified by
`scripts/metal_threshold_policy.schema.json`. Its status progresses from
`untuned` to `candidate` and only to `validated` after independent corpus and
machine confirmation. Missing combinations always select CPU.

## Conservative decision rule

For each operation/content/method/execution/size, Sol reviews tune and holdout
records separately. A focused size may become a candidate only when every
observed paired Metal/CPU ratio is at most 0.95 at that bucket and every larger
tested bucket in both roles, with at least two consecutive buckets. This
all-observations rule is deliberately conservative for the focused cold sample
count; medians, MAD, and ranges are still reported, but no small-sample interval
is labeled a confidence interval. Thresholds are never interpolated below a
tested bucket.

Transform interpretation uses only the photo eligibility stratum. Hash photos
and textures remain separate, and palette graphics remain a forced-dispatch
regression guard. Without a runtime eligibility classifier, disagreement
between hash strata or a palette regression means no hash entry. Lossy import
uses the worst crossover across its tested content classes. If any required
stratum has no stable crossover, no entry is emitted and CPU remains the
fallback.

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
