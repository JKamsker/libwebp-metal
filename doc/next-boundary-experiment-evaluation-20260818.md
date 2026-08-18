# Next-boundary experiment evaluation (2026-08-18)

## Outcome

The separately released continuation ran both frozen timed matrices on one
Apple M4 Pro, strictly serially. Both experiments passed build, correctness,
determinism, decoded-pixel, transactional-fallback, device, lease, and resource
gates. Neither candidate satisfies every predefined holdout criterion:

- `predictor_boundary` passes all selector, selector-plus-apply, and map-share
  criteria, but its method-6 cold holdout exceeds both recorder-overhead limits.
  The broader selector-plus-apply implementation boundary is therefore not
  accepted under the frozen all-cell rule.
- `backref_exact` accounts for at least 98.94% of each required holdout boundary,
  but standard exact LZ77 contributes only 3.13--4.29%, far below the required
  50%. Its method-4 warm holdout also exceeds the recorder p95-overhead limit.
  Standard exact-candidate evaluation is rejected as the proposed dominant
  boundary.

No production encoder, threshold, policy, ABI, API, or default changes are
supported. The default-off diagnostics are retained as reproducible research
instrumentation. The prior rejection of standalone residual dispatch remains
unchanged, and no independent ratios are multiplied.

## Authority and continuation protocol audit

The audited ancestry is:

1. default-branch anchor `cdf2539b29bb767b1557e5069cfee9c111f07358`;
2. designer commit `cdf64a57790d3e7d52fe2685afe0976e41cbe633`;
3. first blocked evidence `78eb0f2e8a47433e699bdd0efa3aee9b78f03408`;
4. preflight-only evaluator consequence
   `a964bb6aac67a64f71fa105db5fc8b04649ab9f0`;
5. continuation evidence `44acf69940b5d7369a013ab5dbdb46f08b0b0433`.

The frozen manifest still verifies as
`476c54607a463908ed44cf8e8d1b955af35f3def6f15d11da423a1bd90d6e969`.
The runnable operator verifies as
`a790796c2d715b3b6405b801de88401e379e710bbf09297d55038a98e993d054`.
Relative to the designer operator, its only executable difference is the
Darwin free-memory fallback from unsupported `SC_AVPHYS_PAGES` to conservative
`vm_stat` parsing. The manifest, encoder instrumentation, experiment sources,
build flags, runtime flags, matrix, hypotheses, thresholds, and all scientific
parameters are byte-identical between the designer and runnable revisions.

The continuation commands set `WEBP_EXPECTED_DESIGNER_COMMIT=a964bb6...`, not
the literal designer commit. This is a procedural deviation from the original
prose example, whose placeholder was described as the designer commit. It is
admissible for this continuation for three reasons:

- the frozen manifest defines `source_ref` as `HEAD`, and the operator's actual
  invariant requires the environment value to equal runnable `HEAD`;
- running the already-authorized preflight fix while supplying `cdf64a5...`
  would fail the exact-source check before the lease;
- the coordinator separately released the continuation from `a964bb6...`, and
  the only executable delta is the prerequisite fix described above.

Thus the substitution preserves the stronger exact-runnable-source invariant
and does not alter the measured code or criteria. It must nevertheless remain
recorded as a continuation exception; the evidence must not be represented as
having run directly at `cdf64a5...`.

The exact recorded continuation commands were:

```sh
WEBP_EXPECTED_DESIGNER_COMMIT=a964bb6aac67a64f71fa105db5fc8b04649ab9f0 \
WEBP_BENCHMARK_SESSION=exclusive \
WEBP_PREDICTOR_BOUNDARY_EXPERIMENT=1 \
python3 /Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal/scripts/run_next_boundary_experiments.py \
  run predictor_boundary \
  /Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818-cycle2/predictor-boundary

WEBP_EXPECTED_DESIGNER_COMMIT=a964bb6aac67a64f71fa105db5fc8b04649ab9f0 \
WEBP_BENCHMARK_SESSION=exclusive \
WEBP_BACKREF_EXACT_EXPERIMENT=1 \
python3 /Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal/scripts/run_next_boundary_experiments.py \
  run backref_exact \
  /Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818-cycle2/backref-exact
```

## Evidence integrity and execution audit

The continuation evidence root is
`/Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818-cycle2`.
The predictor artifact index verifies as
`2cc9b59bc1cd6948137470f180719e99f4f978e614f164e2290607fe6455f701`;
the backref index verifies as
`46b6247bb4f2658634dab472f2cacd0d12fe8db589c0dd022d3716f9935583f5`.
Every one of the 88 nested artifacts in each index independently matches its
recorded SHA-256. The four outer stdout/stderr transcript hashes and byte counts
also match the committed evidence index. Prior blocked evidence was not
overwritten. Predictor outer stdout/stderr verify as
`751d1d4045ecefc731c75d2dc8935e19a3cb90b0f7d63b84e1728d85a30bdb16`
and
`930df0eeff1f46e5d5d58e8fb30c5898cd65451bb5f2bc35b51956bf092c8996`;
backref outer stdout/stderr verify as
`83eef27b73e0363529e963bbd6f4ea9da5ccc5788c24adc3d0fd3d83e97dede2`
and
`e77a98f2591279dfab512189cf00cfd553efba322c5ed8cf918fba17802e4d00`.

The operator generated publication corpus v1 from the frozen generator and
manifest. Their hashes are respectively
`6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007`
and
`34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff`.
The timed inputs are fixed by the manifest:

| Experiment role | Case | Input SHA-256 |
|---|---|---|
| predictor tune | `photo-medium` | `a1a6ab156ae4b18666a780bcdf7eaf7d2124415eb192e091dc21e7adbf383c70` |
| predictor holdout | `photo-large` | `b18f3f3e0b3324ae5c8e42f5eac831a8ba350e64c181340aa65410649b2e4612` |
| backref tune | `texture-medium` | `91d90466139f54ad441448bc7d352c637a4020ce928434dbff3a358c5a829385` |
| backref holdout | `texture-large` | `dd02badce31b757f9374f0f5de187e9de3158fe6878929207eeed24ea72d79e2` |

Each experiment has 80 synchronous command rows, 200 raw encoder records, 36
raw correctness records, and 18 correctness summary rows. Raw timing roles are
56 cold records, 24 discarded warmups, and 120 measured warm records. Excluding
warmups, each experiment has 176 measured records: 88 record and 88 matched
control. Every cold cell has seven process pairs and seven observations per
variant. Every warm cell has three process pairs, one discarded warmup per
process, and 15 measured observations per variant. Warm inferential units are
the three process medians, not the 15 correlated encodes.

The command order exactly matches the manifest's alternating pair order for:

- predictor: `photo-medium` tune then `photo-large` holdout;
- backref: `texture-medium` tune then `texture-large` holdout;
- methods 4 then 6 within each case;
- cold then warm within each method.

The predictor run ended 50.094 seconds before the backref preflight began. Each
preflight was written after acquiring `/tmp/libwebp-metal-next-boundary.lock`,
each resource record confirms release, and the lease is absent after execution.
The synchronous operator launches one process at a time. The machine records
exactly one physical Apple M4 Pro Metal 4 device, macOS 26.5.1, Python 3.9.6,
and Apple clang 17.0.0. The SDK diagnostic reports a missing Command Line Tools
SDK path, but that diagnostic is not a frozen gate and both builds completed
with the recorded Xcode toolchain.

Both correctness summaries cover all nine corpus cases at methods 4 and 6.
Every row reports deterministic bitstreams, decoded-pixel equality, and
transactional fallback. All 160 per-command stderr files are empty. The outer
stderr files contain only archive creation and missing `/opt/local/lib` search
path warnings. The build transcripts prove Metal and the experiment-specific
macro were compiled, and the frozen operator source forces the Metal backend,
but it did not enable verbose dispatch markers or store per-command
environment snapshots. Consequently, successful Metal dispatch is not
independently proven from stderr. This is an evidence limitation, not a frozen
acceptance criterion for these CPU-boundary decompositions; no dispatch-specific
performance claim is made.

No raw continuation artifact contains a CUDA command or build. Power remained
AC with a charged battery, and both ending thermal diagnostics report no warning.

Resource ceilings passed:

| Experiment | Duration | Maximum RSS | Output bytes | Longest command | Free memory |
|---|---:|---:|---:|---:|---:|
| predictor | 118.62 s | 354,729,984 | 167,113 | 3.749 s | 10,189,914,112 |
| backref | 80.33 s | 356,139,008 | 210,796 | 2.492 s | 10,181,738,496 |

These are below the frozen 3,600-second, 6 GiB RSS, 2 GiB output, and
240-second command ceilings; both free-memory observations exceed 8 GiB.

## Statistical method

Evaluation preserves experiment, case, tune/holdout, method, and lifecycle
strata. For each process, measured warm encodes are reduced to a median; cold
processes contain one measured encode. Record/control overhead is the median of
the resulting paired process ratios. Stage shares are first computed per encode,
then reduced to process medians. MAD is over process-pair values. The reported
95% descriptive interval is a 10,000-resample percentile bootstrap of those
process-pair values using frozen seed `20260818`. P95 is nearest-rank within
each raw record/control variant stratum; the table reports record p95 divided by
control p95.

Predictor shares use the sum of the three non-overlapping measured components
as the complete measured predictor boundary. Backref standard-LZ77 and
accounted shares use inclusive `backref_total` as denominator. Intervals are
descriptive for this run and do not imply hardware-population confidence.

In the tables, `n` is measured raw observations per variant. Warm rows have
`n=15` but only three process-pair inferential units. Share entries are
`median ± MAD [bootstrap 95% interval]`.

### Predictor cells

| role/case | method | lifecycle | n | selector+apply share | selector share | record/control median ± MAD [95%] | p95 ratio |
|---|---:|---|---:|---:|---:|---:|---:|
| tune/photo-medium | 4 | cold | 7 | 72.55% ± 1.62 [70.93, 74.34] | 69.60% ± 1.57 [68.03, 71.34] | 1.0146 ± 0.0324 [0.9822, 1.0476] | 0.9744 |
| tune/photo-medium | 4 | warm | 15 | 99.15% ± 0.02 [99.10, 99.17] | 95.48% ± 0.03 [95.44, 95.56] | 1.0495 ± 0.0044 [0.9863, 1.0539] | 0.9844 |
| tune/photo-medium | 6 | cold | 7 | 83.57% ± 1.30 [82.02, 84.84] | 81.66% ± 1.36 [80.18, 82.90] | 0.9949 ± 0.0259 [0.9738, 1.0290] | 1.0082 |
| tune/photo-medium | 6 | warm | 15 | 99.67% ± 0.09 [99.47, 99.76] | 97.47% ± 0.09 [97.30, 97.55] | 1.0056 ± 0.0063 [0.9865, 1.0118] | 0.9966 |
| holdout/photo-large | 4 | cold | 7 | 88.82% ± 0.94 [87.88, 89.88] | 85.17% ± 0.87 [84.30, 86.54] | 1.0024 ± 0.0400 [0.9569, 1.0424] | 0.9984 |
| holdout/photo-large | 4 | warm | 15 | 99.73% ± 0.04 [99.69, 99.87] | 96.08% ± 0.10 [95.62, 96.18] | 1.0001 ± 0.0541 [0.9347, 1.0542] | 0.9818 |
| holdout/photo-large | 6 | cold | 7 | 88.59% ± 0.61 [88.29, 90.89] | 85.21% ± 0.47 [84.75, 87.56] | **1.0359** ± 0.0312 [0.9970, 1.0456] | **1.0564** |
| holdout/photo-large | 6 | warm | 15 | 99.82% ± 0.01 [99.74, 99.83] | 95.71% ± 0.02 [95.69, 96.13] | 0.9932 ± 0.0024 [0.9527, 0.9955] | 1.0068 |

### Backref cells

| role/case | method | lifecycle | n | standard-LZ77 share | accounted share | record/control median ± MAD [95%] | p95 ratio |
|---|---:|---|---:|---:|---:|---:|---:|
| tune/texture-medium | 4 | cold | 7 | 3.26% ± 0.05 [3.15, 3.31] | 99.26% ± 0.03 [98.96, 99.29] | 1.0259 ± 0.0103 [1.0146, 1.0283] | 1.0146 |
| tune/texture-medium | 4 | warm | 15 | 2.28% ± 0.01 [2.26, 2.31] | 99.21% ± 0.03 [98.90, 99.23] | 0.9973 ± 0.0011 [0.9962, 1.0029] | 0.9652 |
| tune/texture-medium | 6 | cold | 7 | 3.18% ± 0.04 [3.01, 3.23] | 99.21% ± 0.07 [98.94, 99.28] | 0.9804 ± 0.0279 [0.9525, 1.0116] | 1.0191 |
| tune/texture-medium | 6 | warm | 15 | 2.18% ± 0.04 [2.13, 2.23] | 99.24% ± 0.01 [98.88, 99.25] | 1.0136 ± 0.0008 [1.0128, 1.0229] | 1.0311 |
| holdout/texture-large | 4 | cold | 7 | **4.20%** ± 0.02 [4.15, 4.21] | 98.99% ± 0.09 [98.97, 99.31] | 1.0063 ± 0.0174 [0.9889, 1.0430] | 1.0102 |
| holdout/texture-large | 4 | warm | 15 | **3.15%** ± 0.00 [2.10, 3.15] | 99.22% ± 0.28 [98.88, 99.50] | 1.0073 ± 0.0074 [0.9999, 1.3511] | **1.3458** |
| holdout/texture-large | 6 | cold | 7 | **4.29%** ± 0.03 [4.27, 4.49] | 99.01% ± 0.09 [98.96, 99.28] | 0.9941 ± 0.0171 [0.9770, 1.0214] | 0.9908 |
| holdout/texture-large | 6 | warm | 15 | **3.13%** ± 0.00 [3.13, 3.15] | 98.94% ± 0.05 [98.89, 99.27] | 1.0015 ± 0.0045 [0.9970, 1.0243] | 1.0005 |

## Frozen criteria and decisions

### `predictor_boundary`

All four required photo-large cells exceed the 65% selector-plus-apply and 50%
selector minimums. Predictor-map share is 11.18%, 0.27%, 11.41%, and 0.18%
for method-4 cold/warm and method-6 cold/warm respectively, so the 35% map
deferral trigger is not reached.

The method-6 cold holdout has recorder/control median ratio 1.0359, above the
1.03 maximum, and p95 ratio 1.0564, above the 1.05 maximum. The method-4 warm
tune cell also fails the median-overhead limit at 1.0495, although tune cells
do not decide acceptance. Under the predefined rule that every method and
lifecycle holdout cell must pass, the future selector-plus-apply boundary is
**rejected/not accepted in this cycle**. The strong measured share is retained
as a research observation, but the distorted required cell prevents promotion.
It is not evidence for residual-only dispatch.

### `backref_exact`

All required texture-large cells exceed the 90% accounted-share minimum, but
standard LZ77 contributes only 3.13--4.29%, failing the 50% minimum in every
required cell. The method-4 warm p95 overhead ratio is 1.3458, also above the
1.05 maximum; its three pair-median overhead ratios are 1.3511, 1.0073, and
0.9999, and no recorded thermal warning explains the outlier.

Standard exact-LZ77 candidate evaluation is therefore **rejected** as the
proposed dominant texture backref boundary. The raw decomposition suggests
cache search, cost evaluation, and traceback own most of the measured work,
but those are not the frozen candidate and receive no promotion or inferred
speedup. CPU serial selection, traceback, cache mutation, and fallback semantics
remain authoritative.

## Implemented consequences and publication boundary

No performance implementation is promoted. No threshold, policy, default,
descriptor stage, public/private ABI, installed header, CPU fallback, or cache
semantic changes. Rows 6 and 7 remain independently build- and runtime-gated,
default off, and omitted from ordinary builds. Their code is retained because
it is useful for exact reproduction and boundary decomposition; retaining it
does not make either candidate accepted.

No new experiment is required to interpret these frozen outcomes, so this
evaluation adds no build/runtime flag or timing entry point. A future attempt
to pursue predictor residency must use a new independently gated protocol that
does not reuse the rejected measurement. A future backref attempt should first
form a credible boundary around the observed cache-search/cost/traceback work
without moving order-sensitive CPU selection or cache semantics; it too would
be a new experiment and is not run here.

The publication claim is limited to deterministic BSD-3-Clause synthetic
photo/texture cases on one M4 Pro, one OS/compiler state, and one execution day.
It is a boundary-selection result, not an end-to-end speedup, natural-image,
multi-device, energy, concurrency, or production-readiness claim. Successful
Metal dispatch was not independently logged, warm observations within a
process are correlated, and the hardware replication count is one.

The initial preflight failures and their immutable evidence remain part of the
audit trail. The continuation supersedes only the earlier statement that no
criteria were observed; it does not rewrite the failed attempts.

## Untimed evaluator validation

The evaluator performs no timed pipeline and never acquires the benchmark
lease. The final validation set is:

```sh
python3 scripts/test_next_boundary_operator_portability.py
python3 scripts/run_next_boundary_experiments.py validate
python3 scripts/test_experiment_guards.py
python3 scripts/test_next_boundary_experiments.py
python3 scripts/test_publication_corpus.py
scripts/test_roundtrip.sh
scripts/test_accelerator_interface.sh
make -f makefile.unix clean
make -f makefile.unix -j4 WEBP_ENABLE_METAL=0 \
  examples/cwebp examples/dwebp
python3 -m py_compile scripts/run_next_boundary_experiments.py \
  scripts/test_next_boundary_experiments.py \
  scripts/test_next_boundary_operator_portability.py \
  scripts/test_experiment_guards.py
git diff --check
```

Corpus generation is separately regenerated under a temporary directory with
`scripts/generate_publication_corpus.py --verify`, and all nine generated file
hashes are compared with the frozen manifest. JSON documents are parsed. The
ordinary CPU binary is also checked with `nm` and `strings` to confirm that
boundary symbols, private CLI options, and runtime flag strings are absent.
These checks are correctness and evidence validation only.
