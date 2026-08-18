# Backref-cost interval-search v2 independent evaluation

## Decision

Production promotion is rejected. The PushInterval-local scan-derived append
hint remains a credible, semantically supported, default-off experiment, but
the frozen promotion contract is conjunctive and no authorized performance
matrix exists. All eight required holdout median ratios and all eight p95
ratios are unavailable, so none can be shown to satisfy the frozen 0.995 and
1.005 ceilings.

The experiment code and evidence are retained. The audit found no safety,
semantic, API, ABI, or default-omission defect that would justify removing
them. No production path, public interface, threshold, gate, protocol, host,
runner, power, or toolchain setting is changed by this consequence.

This evaluation performed no benchmark and created no new experiment.

## Identity and ancestry

- Verified base: `22456df935cb3e9e834c0d06a3240db708ace2d7`.
- Phase 1: `d93f7b1d50ddf65d775689618f13b00a3057d1ba`, direct parent the verified
  base, tree `495f3d4427edfbe340f6ee208f281854d2389c5d`.
- Phase 2: `7757bff3eded0e640c6c1a382912323f955b49bf`, direct parent phase 1.
- Phase 2 adds only the diagnostic evidence directory. It changes no candidate,
  manifest, schema, corpus, protocol, source, threshold, or build gate.
- All 19 paths in phase 2's admitted source-hash map and all 34 frozen-artifact
  hashes in the manifest independently match the phase-1 commit.
- Manifest SHA-256:
  `2fd1a222ab0329c69eaf9258626c4a9bcd9e76ed3589a49d17130a9bed46dbac`.
- Schema-catalog SHA-256:
  `af116c02e95e43c13f1013dceda1ccd6fbcf7ce438f476c1a70ceebb144d65ed`.

## Candidate and semantic audit

V2 keeps an append hint only within one `PushInterval` invocation. The
monotonic overlap scan supplies the last visited live node. A successful tail
insertion or in-call tail pop updates that local; the local is discarded on
return. It is used for a formerly null-hint insertion only if its start is
strictly less than the new start. Equal starts and absent hints retain the
baseline positioning path.

Source inspection confirms that V2 adds no `CostManager` field, persistent
tail state, allocation, or fallible operation. It leaves cost arithmetic,
strict comparisons and tie behavior, interval ordering/lifetimes, update and
traceback order, cache/reference order, node cap, allocation/recycling,
serialized allocation fallback, and input ownership unchanged. The injected
failure selects the exact baseline algorithm before DP mutation. The helper's
runtime and failure switches accept only the exact value `1`.

The independent gates are:

- `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT`;
- `WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT=1`.

Recorder code additionally requires
`WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER`. Recorder calls are absent
from recorder-free builds. Compile-time exclusion rejects overlap with V1 and
all other backref-cost experiments. Ordinary CMake and Unix-make builds omit
the V2 source, object, runner, macro, symbols, and runtime/fault strings.

An independent phase-3 shared-library rebuild finds 86 exported symbols for
gate-off and gate-on builds, with the same symbol-set SHA-256
`e91d9c2b44b49d51a64208438cb07a85570b3516fa84cefaddf2f2ed3338cfb4`
recorded in phase 1. An independent source diff also finds zero changes under
the public WebP/SharpYUV headers.

## Independently recomputed untimed evidence

The local work file contains 36 rows: 18 baseline and 18 candidate rows over
18 case/method pairs. Twelve pairs perform interval work; the six texture
pairs activate the candidate but perform no interval insertion or positioning.
Grouping raw rows by case and method gives zero bitstream mismatches and zero
non-search-counter mismatches.

The raw totals are:

| Counter | Baseline | V2 |
| --- | ---: | ---: |
| Forward positioning steps | 5,585,685 | 0 |
| Backward positioning steps | 53,769 | 53,769 |
| Append-hint fast paths | 0 | 1,062,260 |
| Append branch checks / loads | 0 | 1,123,588 / 1,123,588 |
| Append start loads | 0 | 1,062,260 |
| Append update checks / updates | 0 | 117,020 / 1,124,012 |
| Pop-tail checks / updates | 0 | 37,438 / 15,162 |
| Runtime activations | 0 | 37 |

Thus total positioning falls from 5,639,454 to 53,769, a 99.0466% reduction;
V2 retains 0.9534% of baseline positioning work. The raw work-record SHA-256
is `faa3b720bbb1e4a6686ab231d31af787321ba9c29cf58276ddde66fed237a30a`.
No elapsed-time, duration, or timing sample is present in those rows.

The returned remote phase-1 subset has 16 raw rows, eight per variant over the
four tune/holdout cases and methods 4/6. Recomputed totals are forward steps
`5,320,351 -> 0`, backward steps `50,215 -> 50,215`, 1,011,082 fast paths,
1,069,280 branch checks and loads, 1,011,082 start loads, 110,228 update
checks, 1,069,658 updates, 35,248 pop-tail checks, 14,398 pop-tail updates,
and 19 activations. Its eight paired cells have zero bitstream and
non-search-counter mismatches. Its work-record SHA-256 is
`cacd90390bb2bd3bad675f24d5d7779963f77e86a3984d04ec652bcd187003d1`.

The same returned rehearsal contains 26 unique correctness cells covering all
nine publication cases, methods 4/6, quality 75, and graphic-small boundary
qualities 24/25/26/100. All 26 raw rows report deterministic candidate output,
default-build independence, exact injected fallback, and decoded pixels equal
to the immutable input. The 10 exact build commands comprise three clean
clones, three detached checkouts, three admitted Unix-make builds, and one
explicit baseline-runner link. These phase-1 results support semantic safety;
they are not phase-2 timing or a substitute for the frozen execution gates.
The rehearsal checkout was the phase-1 intermediate commit
`6781a606087239b93db64b713f2ecc4076fc2b78`; a direct diff confirms that the
candidate source, helper/header, runner, publication corpus, Unix-make/CMake
build files, and remote workload script are identical to final phase 1. The
later phase-1 changes add the returned evidence and freeze `REJECT_TIMING`.

Independent opcode recounts of the committed complete arm64 translation-unit
assembly reproduce scalar `ldr` counts of 258 baseline, 266 V1, and 261 V2.
V2 restores the baseline 33,224-byte `CostManager` layout versus V1's 33,232
bytes. V2 assembly is larger (67,593 bytes versus 64,813 for V1 and 62,853 for
baseline) and has more static branch/control-flow sites, so these static facts
cannot establish an end-to-end speedup.

## Frozen matrix and unavailable holdout statistics

The manifest still specifies photo-medium and graphic-medium tune strata,
photo-large and graphic-large holdouts, methods 4/6, independent cold/warm
lifecycles, fixed alternation, 272 command processes, 1,040 retained samples,
16 evaluation cells, and eight required holdout cells. No threshold was fitted
or weakened.

| Holdout | Method | Lifecycle | Median ratio (<= 0.995) | p95 ratio (<= 1.005) | Result |
| --- | ---: | --- | --- | --- | --- |
| photo-large | 4 | cold | unavailable | unavailable | undemonstrated/fail |
| photo-large | 4 | warm | unavailable | unavailable | undemonstrated/fail |
| photo-large | 6 | cold | unavailable | unavailable | undemonstrated/fail |
| photo-large | 6 | warm | unavailable | unavailable | undemonstrated/fail |
| graphic-large | 4 | cold | unavailable | unavailable | undemonstrated/fail |
| graphic-large | 4 | warm | unavailable | unavailable | undemonstrated/fail |
| graphic-large | 6 | cold | unavailable | unavailable | undemonstrated/fail |
| graphic-large | 6 | warm | unavailable | unavailable | undemonstrated/fail |

There are zero raw timing rows, zero command processes, and zero timed samples,
so no median or nearest-rank p95 can be computed.

## Phase-2 diagnostic audit

Phase 1 froze `REJECT_TIMING` and `timed_execution_authorized: false` after its
independent return wrapper raised `KeyError: 'bundle_sha256'`; the actual
admission contract exposes top-level `source_bundle_sha256` and nested
`admission.bundle_sha256`. Phase 2 did not retry or time that handoff.

Its sole remote command used the frozen `rehearse` mode on `pandocs-agent`
with `WEBP_BENCHMARK_SESSION=exclusive`. Rehearsal requires that variable to
be unset, so it refused at `rehearsal-session-guard` with exit 1 and
`RuntimeError: rehearsal requires WEBP_BENCHMARK_SESSION unset`.

Before refusal, source admission passed: local, remote, top-level, and nested
bundle SHA-256 values all equal
`b8a3445a01d2f29e6c9a3d2c2b56915df67ee30665a45da72b63152b50421079`;
the detached source commit and tree match phase 1; repository-context bundle
verification passed; and the scoped verification repository was removed.

The raw diagnostic records show:

- build commands/outputs: 0/0, not attempted;
- correctness cells: 0, not attempted;
- work rows: 0, not attempted;
- timed runner invoked: false;
- timing command processes/sample rows/timed samples: 0/0/0;
- benchmark lease attempted/acquired/released: false/false/false;
- Runner.Worker and competing benchmark/CUDA matches: zero in all recorded
  pre-admission, post-admission, and post-refusal process snapshots;
- device, power/thermal, resource, and toolchain admission: not attempted;
- remote archive, archive transfer, extraction, and independent lease
  transfer: not attempted;
- exact validated child `run.SMd9dq`: removed, with absence proved.

The local diagnostic artifact index has 16 entries and the returned index has
17 entries including the artifact index. Independent SHA-256 and byte-count
verification passes for every entry, with no post-index exclusions. This
validates the returned diagnostic files but cannot replace the remote archive,
transfer, extraction, lease, or execution evidence that was never produced.

Key phase-2 hashes are:

- artifact index:
  `28f1d04ee62f3a88f8b3157760c55484e73296e44856cef4d45d997a08681f4a`;
- returned index:
  `935ccf083f16c22908e8a8af36135fcc3f40a500c40f41c41e37924a221f588d`;
- diagnostic result:
  `4668529390733595c86acd5ca469816608436746d68721db562fa4dbec69244b`;
- refusal-return report:
  `cfde53104f43e8d7c88a8264a448cab3a6cf7982f04fd6da7e82adac43b5c2a9`;
- source admission:
  `e865666cb30035937dda7e077989b34a2b248a085c95a0c5f2f1cf32d794eff0`;
- cleanup receipt:
  `4a5e9c6a7d83ab4f44b9188d4fb4e69730de0ed6c59e0db802e010d7218f1e0c`.

## Gate-by-gate result

| Frozen gate | Evaluation |
| --- | --- |
| Ancestry, commit/tree identity, frozen hashes | pass |
| Candidate identity and independent build/runtime/recorder gates | pass |
| Default omission and overlap exclusion | pass |
| Public API/header and recorded ABI equality | pass |
| Exact interval semantics and transactional fallback | pass |
| Frozen corpus, methods, strata, order, counts, and thresholds | pass |
| Static assembly/layout and phase-1 causal claim | pass as untimed evidence only |
| Phase-1 correctness, repeat, fallback, immutable input, sanitizer/boundary evidence | pass as design evidence |
| Phase-2 source/bundle admission | pass |
| Phase-2 process isolation and exact-child cleanup | pass |
| Phase-2 toolchain/device/power/resource admission | not reached; promotion gate undemonstrated |
| Phase-2 lease acquisition/release | not attempted; promotion gate undemonstrated |
| Phase-2 build/correctness/work/activation gates | not attempted; promotion gate undemonstrated |
| Phase-2 remote archive/index/transfer/extraction/independent lease return | not attempted; promotion gate undemonstrated |
| Phase-2 local diagnostic indexes | pass, but limited to refusal artifacts |
| Eight holdout median gates | unavailable; promotion fails |
| Eight holdout p95 gates | unavailable; promotion fails |
| Conjunctive production promotion | fail |

## Untimed phase-3 validation

The focused V2 implementation, admission, archive, protocol, and complete
18-row experiment-guard tests pass. The implementation test rebuilt default
and candidate CMake configurations, verified default symbol/string/object and
runner omission, executed all 26 correctness cells and exact fallback/repeat
comparisons, decoded immutable inputs, and exercised undefined/integer and
array-bounds/pointer-overflow sanitizer builds over interval-boundary fixtures.
No timing was collected.

## Consequence and blocker

There is no production consequence beyond rejection: V2 stays wholly
default-off, is not enabled for any content or method, and contributes no
ordinary object, symbol, string, or behavior. The evidence is retained because
it establishes a materially distinct mechanism, exact semantic behavior in
the tested matrix, and direct search-work elimination without V1's persistent
manager state.

The terminal blocker is operational and evidentiary: the frozen handoff never
completed a schema-valid independent return rehearsal, and phase 2's
refusal-only diagnostic itself stopped at the incompatible session guard.
Consequently the execution, lease, host-state, archive-return, and all timing
gates remain undemonstrated. Any future work requires a separately authorized
cycle with fresh identities; nothing further is authorized or run here.
