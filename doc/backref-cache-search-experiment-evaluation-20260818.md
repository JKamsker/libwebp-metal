# Back-reference cache-search experiment evaluation (2026-08-18)

## Outcome

The one frozen `backref_cache_search` matrix completed at designer source
`90ceb5a3d81a761678c0e89d44f7c09e5ce18836`, and its raw evidence was indexed
separately by executor commit
`5ab9cfc0cf435e821ce7cd8d7c8c2112ef170ec8`. The diagnostic is **not accepted**
under its predeclared all-cell rule.

All four texture-large holdout cells pass the 50% cache-search-share criterion,
at 60.90--64.15%. All four pass the nearest-rank p95 record/control ceiling.
Three pass the median-overhead ceiling. Method-6 cold has a record/control
median ratio of 1.03661, above the frozen 1.03 maximum. No threshold is fitted
after observation, no strata are pooled, and the otherwise passing cells do not
override this required failure.

The dedicated diagnostic remains useful, independent, default off, and omitted
from ordinary builds, so it is retained for reproduction. Acceptance would
have established at most a future implementation-research boundary; rejection
therefore supports no production implementation, threshold, policy, default,
public ABI/API, or cache-semantic change. It also supports no GPU, dispatch, or
end-to-end speedup claim.

The closed predecessor decisions are unchanged. `predictor_boundary` remains
rejected under its recorder-overhead rule. `backref_exact` remains rejected
because standard exact LZ77 was only 3.13--4.29% of the required boundary and
had a warm p95 outlier. This evaluation does not rerun, relabel, or combine
either predecessor ratio.

## Authority and exact ancestry

The audited commit sequence is:

1. default-branch merge
   `297b9e5257ed1098503f7630f3223c1fddbef261`;
2. design, protocol, and diagnostic code
   `90ceb5a3d81a761678c0e89d44f7c09e5ce18836`;
3. separate immutable raw-evidence handoff
   `5ab9cfc0cf435e821ce7cd8d7c8c2112ef170ec8`;
4. the separate descendant evaluation commit containing this report.

The executor commit changes only its evidence index, transcript, and operator
report relative to the designer commit. The frozen manifest and operator are
byte-identical at the designer and executor revisions:

| Authority | SHA-256 |
|---|---|
| `scripts/backref_cache_search_experiment_v1.json` | `ed0c68b0e72fb013da5fe244d20453e3c86d1199cc7877725c2c4b4fb8041fe1` |
| `scripts/run_backref_cache_search_experiment.py` | `1a66c966dc1d5735e5bba6ef8b281f4b8093b542c399b451c72594d8084a1848` |
| publication-corpus generator | `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007` |
| publication-corpus manifest | `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff` |

The external evidence root is
`/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search`.
Its `artifact-hashes.json` digest is
`55acf72755516c68fa9b6884589553ae8b9d1ba18679de85d7a97f29491e547d`.
All 89 indexed nested artifacts independently match their recorded hashes, and
the index exactly covers every external file except itself. The complete
evidence occupies 268,234 bytes including the index.

## Protocol, source, and execution audit

The diagnostic source has one inclusive clock around
`VP8LGetBackwardReferences` and one accumulated clock around
`CalculateBestCacheSize`. Record timing rows contain exactly one inclusive
backref call and two cache-search calls. Controls use the same binary and exact
runtime opt-in while recording zero boundary clocks. The experiment source,
runtime strings, private CLI option, and symbols are conditional on the new
row-8 build macro; installed headers do not differ from the baseline.

The executor ran the exact frozen command once. Preflight records the designer
source, manifest hash, `WEBP_BENCHMARK_SESSION=exclusive`, and the host-wide
lease path after the operator acquired its non-blocking flock. The final
resource record reports successful completion and `lease_released: true`. The
evaluator did not probe or acquire that flock.

The independently reconstructed inventory is:

| Artifact or role | Count |
|---|---:|
| synchronous commands / unique command processes | 80 / 80 |
| raw timing records | 200 |
| cold / discarded warmup / measured warm records | 56 / 24 / 120 |
| measured record / control observations | 88 / 88 |
| raw correctness / correctness summary rows | 54 / 18 |
| empty per-command stderr files | 80 |

Command order exactly follows tune then holdout, method 4 then 6, cold then
warm, and the seven frozen alternating pair orders. Each cold process contains
one measured encode. Each warm process contains one discarded warmup followed
by five measured encodes. Every schema, sequence, case, method, lifecycle,
variant, encoder option, environment field, PID grouping, encode index, sample
role, dimensions, and success field is consistent with the manifest.

All nine generated corpus cases at methods 4 and 6 pass repeated-record
determinism, record/control bitstream identity, decoded-pixel identity, injected
record-failure transactionality, and recorder-open-failure transactionality.
The 54 raw correctness records are exactly the two successful recorder rows and
one control row for each of the 18 case/method cells; the two deliberate failure
paths emit no recorder row. Source audit confirms the operator compared all
five encoded variants before recording each successful summary.

The build transcript proves that Metal and only the new cache-search macro were
compiled. The diagnostic is CPU-boundary accounting: the protocol neither
requires nor records Metal dispatch markers. The machine record contains one
physical Apple M4 Pro Metal 4 device, macOS 26.5.1 build 25F80, arm64, Python
3.9.6, and Apple clang 17.0.0. No CUDA marker appears in the build, command, or
operator evidence.

The SDK query reports a missing Command Line Tools SDK path, and the linker
reports the already-documented `/opt/local/lib` search-path warnings. Neither
was a frozen failure gate; the build and matrix completed. Resource gates pass:

| Gate | Observed | Ceiling or requirement |
|---|---:|---:|
| preflight free memory | 10,079,453,184 bytes | at least 8 GiB |
| elapsed duration | 87.916126 s | at most 3,600 s |
| maximum child RSS | 356,171,776 bytes | at most 6 GiB |
| evidence bytes | 268,234 | at most 2 GiB |
| longest command | 1.924519 s | at most 240 s |
| physical Metal devices | 1 | exactly 1 |

Power remained AC with a charged battery. No thermal, performance, or CPU-power
warning was recorded.

## Frozen statistical reproduction

Evaluation preserves case, tune/holdout role, method, lifecycle, and variant.
Warm observations are first reduced to one median per process. For each process
pair, overhead is the record-process median divided by the matched
control-process median. Cache-search share is computed per encode as
`cache_search / backref_total` and then reduced to a process median. The table
reports medians, MAD, and a 10,000-resample percentile bootstrap 95% interval
over those process-pair values using the single frozen seed `20260818` stream.
P95 is nearest-rank within each raw variant stratum; the displayed ratio is
record p95 divided by control p95. Intervals are descriptive and do not change
the decision.

In the table, `n` is measured raw observations per variant and `pairs` is the
inferential process-pair count. Share and overhead entries are
`median ± MAD [bootstrap 95% interval]`.

| role/case | method | lifecycle | n / pairs | cache-search share | record/control median | p95 ratio |
|---|---:|---|---:|---:|---:|---:|
| tune/texture-medium | 4 | cold | 7 / 7 | 62.24% ± 0.31 [61.93, 62.65] | 1.0077 ± 0.0099 [0.9664, 1.0176] | 1.0204 |
| tune/texture-medium | 4 | warm | 15 / 3 | 65.13% ± 0.02 [64.86, 65.15] | 1.0138 ± 0.0208 [0.9871, 1.0346] | 1.0478 |
| tune/texture-medium | 6 | cold | 7 / 7 | 61.63% ± 0.43 [61.42, 62.54] | 0.9988 ± 0.0267 [0.9707, 1.0229] | 0.9941 |
| tune/texture-medium | 6 | warm | 15 / 3 | 65.08% ± 0.32 [63.65, 65.41] | 1.0109 ± 0.0032 [1.0077, 1.0413] | 1.0190 |
| holdout/texture-large | 4 | cold | 7 / 7 | 61.58% ± 0.55 [60.87, 62.10] | 0.9903 ± 0.0089 [0.9814, 1.0169] | 1.0004 |
| holdout/texture-large | 4 | warm | 15 / 3 | 64.14% ± 0.30 [63.84, 64.79] | 0.9975 ± 0.0019 [0.9956, 1.0226] | 1.0096 |
| holdout/texture-large | 6 | cold | 7 / 7 | 60.90% ± 0.22 [60.67, 61.76] | **1.0366** ± 0.0163 [1.0129, 1.0474] | 1.0383 |
| holdout/texture-large | 6 | warm | 15 / 3 | 64.15% ± 0.31 [63.80, 64.46] | 0.9978 ± 0.0067 [0.9905, 1.0045] | 0.9660 |

The seven method-6 cold holdout pair ratios are 1.01293, 1.04358, 1.02029,
1.01087, 1.06559, 1.04736, and 1.03661. Their median is 1.03661. The p95 ratio
is separately compliant at 1.03832; it cannot cure the median failure.

## Decision and consequences

Every share, exact-call-count, p95, correctness, determinism, decoded-pixel,
transactional-fallback, inventory, schema, hash, source, lease, device, and
resource gate passes. The method-6 cold holdout median-overhead gate fails.
Because every required holdout cell had to pass every criterion, the sole
candidate is **rejected/not accepted as a future implementation-research
boundary in this cycle**.

The diagnostic is retained because it is independently gated, observational,
transactional, reproducible, and materially narrows the measured region. Its
retention is not acceptance. No production source is changed by this
evaluation. No threshold, policy, default, live knob, public ABI/API, installed
header, accelerator descriptor, fallback rule, call order, ownership rule, or
cache behavior changes.

No additional experiment is necessary to interpret this frozen result, so this
evaluation defines no new build flag, runtime flag, timing entry point, or
protocol and runs no follow-up. The next credible opportunity, if a later cycle
is authorized, is a recorder-free transactional implementation A/B confined to
`CalculateBestCacheSize`, using completely new independent build/runtime gates
and exact cache/bitstream equivalence. That would test an implementation rather
than infer a speedup from nested clocks. Cost evaluation plus traceback is the
fallback architectural lead if no semantics-preserving cache-search prototype
can be frozen. Predictor residency remains deferred until an explicit resident
selector prototype exists.

## Limitations and reproducibility

This is one machine, one OS/compiler state, one execution day, and deterministic
synthetic texture input at two sizes and two methods. Warm observations within
a process are correlated. Bootstrap intervals describe this fixed sample; they
do not estimate hardware-population uncertainty. The diagnostic does not
measure natural-image prevalence, energy, concurrency, device-family behavior,
end-to-end implementation speedup, or GPU dispatch. Inclusive clocks do not
prove that every internal cache-search operation is independently accelerable.

The machine-readable evaluation is
`profile-data/runs/20260818-next-backref-cache-search-evaluation/evaluation.json`.
Reproduce the read-only audit without a benchmark session or lease:

```sh
python3 scripts/evaluate_backref_cache_search_experiment.py
```

The evaluator verifies all external hashes, source authority, command and raw
record structure, correctness summaries, resources, frozen statistics, and the
exact failure set before printing the committed JSON content. It has no timing
or run subcommand and writes no evidence.
