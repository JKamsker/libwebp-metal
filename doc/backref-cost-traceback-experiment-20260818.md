# Frozen backref cost/traceback workspace experiment

## Scope and independent gates

This cycle evaluates only the contiguous/reused `CostManager` workspace
described in `doc/backref-cost-traceback-design-report-20260818.md`. The build
gate is `WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT`; it privately defines
`WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT`. Candidate execution requires the
exact value `WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT=1`. Timed execution also
requires the exact lease declaration `WEBP_BENCHMARK_SESSION=exclusive` and a
nonblocking exclusive host lock. The candidate-only fault hook is
`WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE=1`.

Ordinary builds omit candidate source, symbols, runtime strings, test target,
runner target and CLI. The experiment uses portable C with Metal disabled and
contains no CUDA and no boundary recorder. The closed `backref_cache_search`,
`cache_size_serial_sweep`, and `cache_size_single_pass_slab` commands and
samples are forbidden inputs.

## Immutable publication corpus and activation

`scripts/generate_publication_corpus.py` deterministically generates opaque P6
inputs from integer formulas and seed `0x9e3779b9`; there is no external media,
network input, model output, or runtime randomness. Its source and the complete
nine-case manifest are hash-frozen. Correctness covers photo, graphic and
texture at small, medium and large sizes with methods 4 and 6 at quality 75,
plus graphic-small at qualities 24, 25, 26 and 100. This crosses the traceback
quality edge (off below 25, eligible at 25), cache/no-cache behavior, and method
4/6 configurations.

The timed tune stratum is the three medium photo/graphic/texture cases. The
holdout stratum is the three large cases in the same category order. All use
lossless exact encoding, quality 75, methods 4 then 6, one thread, and cold then
warm lifecycle. Before freezing, an untimed breakpoint check must confirm that
`VP8LBackwardReferencesTraceBackwards` is actually entered for every timed
case/method. A failed activation check is a designer blocker; a timed no-op cell
must not be admitted.

The designer's untimed breakpoint check passed all 12 timed case/method cells;
it stopped at function entry and captured no elapsed or performance value.

The operator regenerates the corpus in a temporary directory, verifies every
input hash before use and after all work, and records each timed case hash in
the machine manifest. Inputs are never modified in place.

## Frozen A/B execution

Build `baseline` is an ordinary static Release build with Metal off and the new
option absent. Build `candidate` differs only by
`-DWEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT=ON`. The same dedicated runner
source is separately linked to each static library. It measures external
elapsed `WebPEncode` only; no library timer, counter, diagnostic or boundary
sample is compiled or emitted.

Case order is tune photo, graphic, texture; holdout photo, graphic, texture.
Within each case: method 4 then 6; within each method: cold then warm. Cold uses
exactly 11 process pairs, no warmup, and one measurement in each process. Warm
uses exactly six process pairs, two discarded warmups, and nine measurements
in each process. Pair order alternates baseline/candidate then
candidate/baseline. Cold uses all 11 entries and begins and ends
baseline/candidate; warm uses the first six entries.

The exact timed inventory is 408 runner processes, 264 cold measurements, 288
discarded warmups, 1,296 warm measurements, 1,560 measurements total, and 780
measurements per variant. There are 24 evaluation cells, of which the 12
holdout case/method/lifecycle cells are mandatory. Correctness has 26 cells.

For warm cells, each process first reduces to the median of its nine retained
measurements. The location statistic is the median of the six or eleven paired
candidate-process/baseline-process ratios. Tail is nearest-rank p95 over raw
retained candidate samples divided by nearest-rank p95 over the matching raw
baseline stratum. Category, case, method, lifecycle, role, and process are not
pooled. Tune is descriptive only. No ratios are multiplied and no historical
measurement or threshold fitting is allowed.

Every holdout cell must have paired median ratio at most 0.99 and p95 ratio at
most 1.01. Acceptance additionally requires every correctness, deterministic
repeat, candidate-fault fallback, default-build independence, immutable-input,
schema, hash, inventory, lease and resource gate. One failure rejects the
candidate; there is no partial promotion.

Resource ceilings are one benchmark process, at least 4 GiB available memory,
at most 2 GiB child RSS, at most 2 GiB output, 300 seconds per command and 3,600
seconds total. Any stale commit, dirty worktree, hash mismatch, pre-existing or
relative output, invalid/missing runtime value, invalid/missing exclusive
session, busy lease, resource failure or command failure refuses execution.

## Exact commands

Untimed validation, which never grants a lease:

```sh
WEBP_EXPECTED_BACKREF_COST_TRACEBACK_COMMIT=<DESIGN_COMMIT> \
python3 scripts/run_backref_cost_traceback_experiment.py validate
```

After separately confirming AC power, normal thermal state, sufficient disk
and sole host ownership, the executor may run exactly once into a new absolute
directory:

```sh
WEBP_EXPECTED_BACKREF_COST_TRACEBACK_COMMIT=<DESIGN_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/run_backref_cost_traceback_experiment.py run \
  /absolute/new/evidence/backref-cost-traceback
```

The output handoff is `records.jsonl`, `commands.jsonl`, `correctness.json`,
`evaluation.json`, `resources.json`, `build.log`, `operator-report.md`, and the
final `artifact-hashes.json`, using the six v1 schemas frozen by the manifest.
