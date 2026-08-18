# Frozen cache-size single-pass slab experiment

## Decision and audited semantics

This cycle implements one private CPU candidate inside
`CalculateBestCacheSize`: a single-pass contiguous state slab. Upstream `main`
at `178d2bc03b73aa15fc1186c1fd1c383e092a26a8` and the fork baseline use one
immutable-reference traversal while keeping cache-bit candidates 0 through the
maximum live together. Each candidate histogram and each nonzero cache is,
however, separately allocated and initialized.

The candidate preserves that one traversal and the exact update algorithm. One
`WebPSafeCalloc` contains the slab metadata, 11 possible histogram objects,
their variable literal arrays, and 10 possible color arrays. Internal pointers
are wired once; no candidate state is copied or replayed. The zero-filled slab
replaces 21 allocation calls and their independent initialization passes at the
10-bit edge. This is not the rejected serial sweep: all candidates remain live,
and the reference cursor advances once rather than once per cache-bit value.

Literal keys are still derived from the largest cache and shifted while cache
bits descend. Copy colors still update only when the color changes. Entropy is
still evaluated for bits 0 upward and the winner changes only for a strict
reduction, preserving lower-bit ties. Quality at or below 25 still selects zero.
The result is published only after the full search; an allocation or injected
failure leaves the requested maximum untouched and invokes the unchanged
baseline. Cache rewrite, cost evaluation, traceback, LZ77 selection, ownership,
public ABI/API, installed headers, and production behavior remain unchanged.

The prior `backref_cache_search` diagnostic and `cache_size_serial_sweep`
implementation evidence are closed historical context only. Neither is rerun,
reproduced, relabeled, promoted, used as a sample, or combined by multiplying
ratios. This protocol compiles and invokes no stage recorder.

## Independent gates and default omission

The build gate is
`WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`; it privately defines
`WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`. Runtime activation requires
the exact value `WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=1` and exact
`WEBP_BENCHMARK_SESSION=exclusive`. The candidate-only fault hook is
`WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_INJECT_FAILURE=1`.

All gates are independent of the closed experiments. The build option defaults
off. Ordinary CMake and `makefile.unix` builds omit candidate source, object,
symbols, strings/live knobs, test target, and runner. The implementation is C,
requires neither Metal nor CUDA, and changes no public header.

## Frozen recorder-free A/B protocol

The machine authority is
`scripts/cache_size_single_pass_slab_experiment_v1.json`; the sole timed
pipeline is `scripts/run_cache_size_single_pass_slab_experiment.py run`. Before
any work it verifies frozen hashes, exact handoff commit, clean worktree,
`WEBP_BENCHMARK_SESSION=exclusive`, available memory, and a nonblocking
exclusive host lease. A missing/invalid session, stale commit, dirty tree, busy
lease, existing output path, hash mismatch, or resource failure refuses the
pipeline.

The operator creates ordinary and candidate static Release builds with Metal
off and links the same dedicated runner against each. The runner measures only
external elapsed `WebPEncode`; no library clock or recorder exists. CUDA is
forbidden. The deterministic publication corpus is regenerated and verified
against `benchmarks/publication-corpus/manifest.json`.

Correctness crosses all nine publication cases with methods 4 and 6. Baseline,
candidate, repeated candidate, injected-failure fallback, and an ordinary build
given the candidate environment must produce byte-identical streams. All are
decoded, must match one another, and must match the source PPM bytes.

The timed order is tune `graphic-medium`, holdout `texture-large`, method 4 then
6, and cold then warm. Cold has exactly 11 process pairs, no warmup, and one
measurement per process. Warm has exactly six process pairs, two discarded
warmups, and nine measurements per process. Within every cell process order
alternates baseline/candidate and candidate/baseline; cold begins and ends with
baseline/candidate, while warm uses the first six entries of that sequence.

Warm observations first reduce to one median per process. The location metric
is the median of candidate-process/baseline-process ratios. The tail metric is
nearest-rank p95 over raw measured samples in each variant stratum, candidate
divided by baseline. Cases, methods, lifecycles, and tune/holdout roles cannot
be pooled. Tune is descriptive. Every holdout method/lifecycle cell must have a
paired median ratio at most 0.99 and p95 ratio at most 1.01. Every correctness,
hash, inventory, resource, and required performance gate must pass.

The exact inventory is 136 runner processes, 88 cold measurements, 96 discarded
warmups, 432 warm measurements, 520 measurements total (260 per variant), and
18 correctness cells. Resource ceilings are one benchmark process, at least 4
GiB available memory, at most 2 GiB child RSS, at most 2 GiB output, at most 300
seconds per command, and at most 5400 seconds total. Schemas are the six
`libwebp-cache-size-single-pass-slab-*-v1` identifiers frozen in the manifest.

## Exact executor pipeline

Validation is untimed and does not grant the lease:

```sh
python3 scripts/run_cache_size_single_pass_slab_experiment.py validate
```

After independently confirming AC power, normal thermal state, sufficient disk
space, and sole ownership of the host, the executor may run this predefined
pipeline exactly once with a new absolute output path:

```sh
WEBP_EXPECTED_CACHE_SIZE_SINGLE_PASS_SLAB_COMMIT=<DESIGN_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/run_cache_size_single_pass_slab_experiment.py run \
  /absolute/new/evidence/cache-size-single-pass-slab
```

No closed experiment command may be run, and no historical value may be added
to this protocol's samples or ratios. The complete output directory, including
`artifact-hashes.json`, is the immutable executor handoff.

## Untimed verification scope

Dedicated tests cover cache bits 0--10; qualities 0, 25, 26, 75, and 100;
explicit all-candidate ties; exhaustive binary literal streams; mixed literal
and copy references; empty, tiny, odd, block-boundary, and 65,537-pixel inputs;
one-slab layout; allocation/fault transactionality; deterministic repeats;
immutable pixels and references; all publication cases; methods 4 and 6;
bitstreams and decoded pixels; default-off/build independence; invalid runtime
and missing-lease refusal; Python schemas; and array-bounds, pointer-overflow,
undefined-behavior, and integer sanitizer smoke execution.
