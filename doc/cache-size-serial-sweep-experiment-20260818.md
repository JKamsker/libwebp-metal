# Frozen cache-size serial-sweep implementation experiment

## Design decision

This cycle implements exactly one alternative inside
`CalculateBestCacheSize`: a cache-resident serial sweep. It is not a recorder,
GPU path, CUDA path, policy change, or production default.

The upstream and fork implementations hold every cache-bit candidate live and
walk the reference stream once. For every literal and changed copy pixel they
visit all cache states. They allocate one histogram for each candidate from 0
through 10 and one color cache for each candidate from 1 through 10. Upstream
`main` at `178d2bc03b73aa15fc1186c1fd1c383e092a26a8` has no relevant difference
from the fork base.

The candidate instead visits cache bits in the same ascending evaluation order,
reinitializes one maximum-sized histogram and one maximum-sized color cache,
and walks the immutable reference stream once per candidate. This preserves the
exact hash state and histogram for each candidate while replacing the inner
candidate loop with a straight-line single-cache loop. It reduces 21 candidate
allocations to two and cuts the live search working set from 11 histograms plus
10 caches to one histogram plus one cache. The tradeoff is repeated sequential
reference traversal. The hypothesis is therefore specifically cache locality,
allocation traffic, and simpler data flow; it is not an asymptotic speedup
claim.

The baseline still evaluates entropy from cache bits 0 upward and changes the
winner only on a strict reduction. The candidate uses that same order and strict
comparison, so ties retain the lower cache-bit value. Quality at or below 25
still forces zero bits. A candidate allocation or injected failure does not
publish a partial result; the unchanged baseline runs with the original maximum.
Public headers, ABI/API, cache rewrite, cost evaluation, traceback, LZ77 choice,
ownership, bitstream syntax, and production defaults are unchanged.

## Closed diagnostic

The prior `backref_cache_search` observational diagnostic remains closed. Its
historical `CalculateBestCacheSize` share was about 61--64 percent of the
back-reference boundary, but method-6 cold record/control median overhead was
1.03661 and exceeded the frozen 1.03 ceiling. It is not rerun, relabeled, or
promoted here. This implementation A/B compiles no stage recorder and adds no
observational recorder.

## Independent gates and omission

| Role | Name |
|---|---|
| Build | `WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT` |
| Private compile macro | `WEBP_USE_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT` |
| Runtime opt-in | `WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=1` |
| Test-only fault injection | `WEBP_CACHE_SIZE_SERIAL_SWEEP_INJECT_FAILURE=1` |

The build flag defaults off. Default CMake and `makefile.unix` builds omit the
candidate translation unit, symbols, runtime strings, fault knob, test target,
and runner. The experiment does not reuse items 1--5, `predictor_boundary`,
`backref_exact`, or `backref_cache_search` gates. The CPU candidate requires
neither Metal nor CUDA. Runtime activation is exact-value only and fails closed
unless `WEBP_BENCHMARK_SESSION=exclusive` is present.

## Frozen recorder-free A/B

The machine-readable authority is
`scripts/cache_size_serial_sweep_experiment_v1.json`, schema
`libwebp-cache-size-serial-sweep-frozen-v1`. The operator is
`scripts/run_cache_size_serial_sweep_experiment.py`. Their SHA-256 values are
reported in the designer handoff and are verified before execution.

The operator creates two independent static builds with Metal off: an ordinary
baseline with the candidate source omitted and a candidate build with only the
new build flag enabled. It compiles the same dedicated process runner separately
against each library. The runner measures only elapsed `WebPEncode` time from
outside libwebp. There is no cache-search or backward-reference boundary clock.
Because exact boundary timing is unavailable without modifying the tested
library, end-to-end `WebPEncode` time is predeclared as the sole performance
authority; boundary timing is omitted and cannot override the decision.

The deterministic publication corpus is regenerated and checked against
`benchmarks/publication-corpus/manifest.json`. Correctness covers all nine cases
at methods 4 and 6. Baseline, candidate, repeated candidate, injected-failure
fallback, and default-build-with-candidate-environment bitstreams must be exact;
decoded PPM bytes must also equal the source.

Timed execution is fixed to tune `texture-medium`, holdout `texture-large`,
methods 4 then 6, and cold then warm. Cold has nine process pairs and one
measured encode per process. Warm has five process pairs, one discarded warmup,
and seven measured encodes per process. Pair order alternates baseline/candidate
and candidate/baseline, beginning and ending baseline/candidate. The inventory
is 112 processes, 72 cold measurements, 40 discarded warmups, 280 warm
measurements, and 352 total measurements (176 per variant).

Warm samples reduce to a median per process. Each pair produces a candidate /
baseline process ratio. The paired median must be at most 0.98 and nearest-rank
p95 candidate / baseline must be at most 1.02 independently in every holdout
method/lifecycle cell. Tune is descriptive. No content, method, lifecycle, or
tune/holdout pooling is allowed. Every correctness, hash, inventory, resource,
median, and p95 gate must pass.

Resource gates require one benchmark process at a time, at least 4 GiB available
memory, at most 2 GiB child RSS, at most 2 GiB evidence, at most 240 seconds per
command, and at most 3600 seconds total. The operator acquires the nonblocking
host lock `/tmp/libwebp-metal-cache-size-serial-sweep.lock` and refuses a busy
lease.

Evidence schemas are:

- `libwebp-cache-size-serial-sweep-sample-v1`
- `libwebp-cache-size-serial-sweep-command-v1`
- `libwebp-cache-size-serial-sweep-correctness-v1`
- `libwebp-cache-size-serial-sweep-evaluation-v1`
- `libwebp-cache-size-serial-sweep-resources-v1`
- `libwebp-cache-size-serial-sweep-artifact-hashes-v1`

## Operator checklist and exact commands

1. Confirm the handoff commit and a clean worktree.
2. Confirm no other timed task owns the host and reserve the exclusive session.
3. Confirm AC power, normal thermal state, at least 4 GiB available memory, and
   sufficient evidence space.
4. Set the expected designer commit exactly; do not substitute a descendant.
5. Run validation without an exclusive session.
6. Run the timed command once with an absolute, nonexistent evidence path.
7. Do not run any historical recorder or combine its ratios with this A/B.
8. Preserve the complete output directory and verify `artifact-hashes.json`.

```sh
python3 scripts/run_cache_size_serial_sweep_experiment.py validate
```

```sh
WEBP_EXPECTED_CACHE_SIZE_SWEEP_COMMIT=<DESIGNER_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/run_cache_size_serial_sweep_experiment.py run \
  /absolute/new/evidence/cache-size-serial-sweep
```

The operator freezes these baseline build commands:

```sh
cmake -S . -B <baseline-build> \
  -DWEBP_ENABLE_METAL=OFF -DBUILD_SHARED_LIBS=OFF \
  -DWEBP_BUILD_EXTRAS=OFF -DWEBP_BUILD_CWEBP=ON \
  -DWEBP_BUILD_DWEBP=ON -DCMAKE_BUILD_TYPE=Release
cmake --build <baseline-build> --target cwebp dwebp -j4
```

The candidate uses the same commands with exactly one additional configure
argument:

```sh
-DWEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=ON
```

The operator compiles `tools/cache_size_serial_sweep_runner.c` once against
each corresponding static build. Timed execution without
`WEBP_BENCHMARK_SESSION=exclusive` is refused both by the runner and by the
candidate runtime selector.

## Untimed verification

These commands do not constitute a timed experiment:

```sh
python3 scripts/test_cache_size_serial_sweep_experiment.py
python3 scripts/test_experiment_guards.py
python3 -m py_compile \
  scripts/run_cache_size_serial_sweep_experiment.py \
  scripts/test_cache_size_serial_sweep_experiment.py
```

The dedicated tests cover exhaustive binary literal streams, mixed literal/copy
streams, exact selected cache bits 0--10, quality edges, zero/odd/small/block-
boundary/large sizes, immutable inputs, all publication cases and methods,
bitstream and decoded-pixel identity, determinism, transactional injected
failure, default-off behavior, default/candidate build independence, invalid
runtime values, missing-lease refusal, and fail-fast undefined-behavior plus
integer-sanitizer execution.
