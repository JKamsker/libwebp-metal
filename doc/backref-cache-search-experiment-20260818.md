# Frozen focused back-reference cache-search experiment

> **Evaluation status:** the frozen matrix completed, but method-6 cold holdout
> exceeded the 1.03 median recorder/control ceiling. The candidate is not
> accepted under the all-cell rule; its default-off diagnostic is retained and
> no production consequence is promoted. See
> [backref-cache-search-experiment-evaluation-20260818.md](backref-cache-search-experiment-evaluation-20260818.md).

## Evidence audit and selection

This design starts at default-branch merge
`297b9e5257ed1098503f7630f3223c1fddbef261`. It uses the committed evaluation,
executor index, operator report, and the immutable raw records referenced by
artifact index
`46b6247bb4f2658634dab472f2cacd0d12fe8db589c0dd022d3716f9935583f5`.
The raw artifact hashes were already independently verified by the committed
evaluation; this design read the available raw `records.jsonl` without changing
it.

The predecessor formulations remain closed. `predictor_boundary` was rejected
under its all-cell recorder-overhead rule and is neither rerun nor relabeled.
`backref_exact` rejected standard LZ77 because it was only 3.13--4.29% of the
required holdout boundary and also had a method-4 warm p95 outlier. Its
default-off diagnostic is only selection input here.

The retained backref records identify one clear next sub-boundary. Reducing the
five measured warm encodes to process medians in the same manner as the prior
evaluation, `cache_search / backref_total` is 61.23--65.06% across all eight
tune/holdout, method-4/6, cold/warm cells. Required holdout cells are
61.23%, 63.93%, 61.50%, and 63.29%. The corresponding standard-LZ77 holdout
shares are 4.20%, 3.15%, 4.29%, and 3.13%. Cache rewrite and box were not
invoked on these fixed texture inputs. This supports one new staged diagnostic,
not an implementation or speedup claim.

The selected experiment is `backref_cache_search`. It uses a dedicated,
lower-distortion recorder with only an inclusive
`VP8LGetBackwardReferences` clock and an accumulated clock around
`CalculateBestCacheSize`. The old eight-stage recorder is not compiled or
enabled. The conceptual acceptance threshold is simple majority (50%), not a
threshold fitted just below the prior observations. Both methods, both
lifecycles, and every holdout rule must pass independently.

Predictor residency is deferred. The evidence says selector-plus-apply is
material but does not identify a small transactional device-resident selector
boundary. The existing Metal prototype is residual-only, has host copies and a
synchronous readback, and belongs to a rejected formulation. Re-recording the
same selector-plus-apply region with fewer clocks would not measure useful
residency. A future predictor experiment needs a new selector/residency
prototype with explicit dispatch and residency evidence before a protocol can
be frozen.

## Isolation and implementation boundary

The new independent gate is:

| Build flag | Private macro | Exact runtime flag | Private repetition option |
|---|---|---|---|
| `WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT` | `WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT` | `WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT=1` | `-backref_cache_search_repetitions` |

It does not reuse item 1--7, `predictor_boundary`, or `backref_exact` flags.
The default CMake, Unix make, and Autotools builds omit the experiment source,
symbols, environment strings, and private CLI option. The runtime value must be
exactly `1`. Repeated/timed entry points also require
`WEBP_BENCHMARK_SESSION=exclusive`; missing, invalid, or non-exclusive states
refuse before corpus generation, build, lease acquisition, or timing.

The recorder is observational. Record mode adds two clocks; matched control
uses the same binary and runtime opt-in but omits both boundary clocks. Both
record total encode time. Recorder open failure and explicit record-failure
injection abandon only evidence output. Untimed tests require repeated record,
control, injected-failure, and open-failure bitstreams to be identical, and the
decoded pixels to equal the input. The experiment does not change public ABI,
API, production defaults, thresholds, cache semantics, or the accelerator
descriptor.

Acceptance can establish only a future implementation-research boundary around
`CalculateBestCacheSize`. CPU LZ77 generation, cache rewrite, cost comparison,
traceback, winner selection, linked-reference ownership, and bitstream
semantics remain outside the candidate. No direct production promotion and no
GPU or end-to-end speedup claim is permitted from this diagnostic.

## Frozen protocol

The machine-readable authority is
`scripts/backref_cache_search_experiment_v1.json`, SHA-256
`ed0c68b0e72fb013da5fe244d20453e3c86d1199cc7877725c2c4b4fb8041fe1`.
It freezes all parameters;
`scripts/run_backref_cache_search_experiment.py` accepts only the fixed
experiment ID and exact frozen output path. There is no criterion, parameter,
case, method, sample-count, order, output, or threshold override.

Publication corpus v1 is generated by
`scripts/generate_publication_corpus.py` (SHA-256
`6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007`)
from `benchmarks/publication-corpus/manifest.json` (SHA-256
`34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff`).
It is deterministic BSD-3-Clause integer-formula P6 data with no third-party
media. Tune is `texture-medium`, SHA-256
`91d90466139f54ad441448bc7d352c637a4020ce928434dbff3a358c5a829385`.
Holdout is `texture-large`, SHA-256
`dd02badce31b757f9374f0f5de187e9de3158fe6878929207eeed24ea72d79e2`.
All nine corpus hashes are frozen in the manifest and verified after generation
for correctness tests at methods 4 and 6.

The encoder is lossless, exact, quality 75, and single-threaded. Order is tune
then holdout; method 4 then 6; cold then warm. Cold is one measured encode in a
fresh process, with seven alternating record/control process pairs. Warm is one
process with one discarded warmup then five measured encodes, with three
alternating process pairs. Pair order is record-control, control-record,
record-control, control-record, record-control, control-record, record-control;
warm uses its first three entries.

The matrix has 80 synchronous command rows and 200 raw records: 56 cold, 24
discarded warmups, and 120 measured warm records. Excluding warmups gives 88
record and 88 control observations. Correctness has 18 summary rows and 54 raw
records (repeated record and control; failure paths deliberately emit none).
Warm inference first reduces each process's five measured encodes to a median.
Tune/holdout, method, and lifecycle are never pooled.

Report paired record/control medians, MAD, and a 10,000-resample percentile
bootstrap 95% interval over process-pair values with seed `20260818`. Report
nearest-rank p95 in every raw variant stratum. Report cache-search share per
encode, reduced to process medians. Intervals are descriptive and do not alter
decisions. No ratio may be multiplied by a historical stage, hash, or
end-to-end ratio.

Every required `texture-large x method 4/6 x cold/warm` cell must satisfy:

- median `cache_search / backref_total` at least 0.50;
- record/control total-time median ratio at most 1.03;
- record/control total-time nearest-rank p95 ratio at most 1.05;
- exactly one inclusive backref call and two cache-search calls per record
  encode.

Every correctness, determinism, decoded-pixel, transactional recorder-failure,
schema, order, inventory, hash, source, lease, device, and resource gate must
also pass. Any failed or missing criterion rejects the candidate. Tune is
descriptive only. There is one candidate and no best-of choice.

Raw records use `libwebp-backref-cache-search-v1`; command rows use
`libwebp-backref-cache-search-command-v1`; correctness uses
`libwebp-backref-cache-search-correctness-v1`. Nanoseconds and call counts are
preserved. Evidence includes exact source, OS, SDK, compiler, GPU/device count,
power, thermal, load, raw observations, stderr hashes, build transcript,
resource notes, and a complete artifact hash index. This is a CPU-boundary
diagnostic, so it makes no GPU-performance or dispatch-specific claim.

The operator allows exactly one physical Metal device and one synchronous
benchmark process. It uses the established host-wide non-blocking lease
`/tmp/libwebp-metal-next-boundary.lock`. Ceilings are 8 GiB minimum free
memory, 6 GiB observed RSS, 2 GiB evidence, 240 seconds per command, and 60
minutes total. It stops rather than adapts on any failure and writes failure,
resource, operator, and hash evidence after lease acquisition. The lease is
released in all exit paths.

## Untimed designer validation

These commands contain no performance comparison, acceptance calculation, or
timed matrix and do not acquire the benchmark lease:

```sh
python3 scripts/run_backref_cache_search_experiment.py validate
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cache_search_experiment.py
python3 scripts/test_publication_corpus.py
scripts/test_roundtrip.sh
scripts/test_accelerator_interface.sh
python3 -m py_compile scripts/run_backref_cache_search_experiment.py \
  scripts/test_backref_cache_search_experiment.py \
  scripts/test_experiment_guards.py
git diff --check
```

The focused test temporarily supplies the exact session string only to activate
the recorder during untimed correctness work. It never calls the operator's
`run` subcommand, reads benchmark acceptance metrics, or acquires the lease.

## Executor command

After the immutable designer commit is supplied as `<commit>`, the only timed
command is:

```sh
WEBP_EXPECTED_DESIGNER_COMMIT=<commit> \
WEBP_BENCHMARK_SESSION=exclusive \
WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT=1 \
python3 scripts/run_backref_cache_search_experiment.py run \
  backref_cache_search \
  /Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search
```

The operator creates the fixed output parent; the final directory must not
exist. The executor must run this command unchanged, on one physical Metal
device, with no other experiment, parameter change, interpretation, or CUDA
work.
