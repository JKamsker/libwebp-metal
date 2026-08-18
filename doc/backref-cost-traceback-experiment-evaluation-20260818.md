# Backref cost/traceback workspace evaluation (2026-08-18)

## Outcome

The frozen `backref_cost_traceback` cycle did not produce an A/B result.
Designer commit `355efae8dad9fc09717a4ccef874adf6bf6b2d6f` prepared the
default-off candidate and protocol. Executor commit
`40e21ac2e64e0a1b7de45f19cbd7ba04caa63f53` records a fail-closed refusal:
the required preflight observed Low Power Mode enabled on AC power, so the
timed operator was not invoked and the lease was not acquired.

Promotion is **rejected for this cycle and performance is unassessed**. This is
not a negative speed measurement: there are no tune or holdout observations,
medians, p95 values, resource records, or machine evaluation. The frozen rule
requires all 12 holdout median and p95 cells plus complete correctness,
integrity, inventory, lease, and resource evidence. Missing mandatory evidence
cannot satisfy that all-gate rule.

The implementation remains useful, independently gated, default off, and
sound under the permitted untimed checks, so it is retained as research code.
Retention is not promotion. Production API/ABI, integer-cost and tie behavior,
thresholds, fallback policy, Metal policy, CUDA behavior, and defaults do not
change. No timed follow-up, replacement gate, or new experiment is opened by
this consequence decision.

## Authority and ancestry

The independently reconstructed history is linear at the experiment boundary:

| Role | Commit | Sole experiment parent | Tree |
|---|---|---|---|
| frozen base | `3142ff3fe31cd1666c5615c5c4ee7dec2ef891f8` | merge parents `e7900b9a4bf71e799001d343721c86f4aad96316` and `ebe049680c67200239816902e8a1db9f5164dd8a` | `51b059304257caf543bdbf12badab0bd7bf6b69b` |
| designer | `355efae8dad9fc09717a4ccef874adf6bf6b2d6f` | `3142ff3fe31cd1666c5615c5c4ee7dec2ef891f8` | `437b8d7cceea68a44d377a9d792fb13993124505` |
| executor evidence | `40e21ac2e64e0a1b7de45f19cbd7ba04caa63f53` | `355efae8dad9fc09717a4ccef874adf6bf6b2d6f` | `1f636d046558eca61db32f740642178bc35d7253` |
| evaluator/consequence | separate descendant containing this report | executor evidence commit | recorded by the evaluator commit |

The executor commit adds only
`evidence/backref-cost-traceback-20260818-executor-refusal`; there is no
non-evidence difference from the designer tree. The evidence directory remains
byte-identical to the executor-commit blobs.

## Evidence index and exact hashes

The directory has ten files: `artifact-hashes.json` plus exactly nine indexed
artifacts. The independently recomputed index digest is
`ef3e9b29dd2c0e27b353ba6aec1f70a84afbfdbdeed6928b2dc4ebf9dcaeb022`.
The index set is complete and self-excluding; every recorded byte count and
digest matches:

| Indexed artifact | Bytes | SHA-256 |
|---|---:|---|
| `executor-commands.jsonl` | 684 | `3696399894516da0b697ab063014bf3af8bc1e7ba1e057f9c11e29807c60666a` |
| `lease-record.json` | 446 | `b42f3083d81914d56a9c04046ac2d512825b2726f3713fce8755d0e14582387f` |
| `operator-report.md` | 770 | `be56feac29ebdb418589399a22d9639fb9e448cca4a42fcf5930a2b755148774` |
| `preflight.json` | 3,240 | `c1d0cff88f386e6553548e15864303385529eafe8398c8f70a010b047f1c6ead` |
| `refusal.json` | 1,372 | `dcdf3ce4e4ddcc4d322e86a5aa4ae0d50f54e7e31521cddcd8c20baee533cb15` |
| `schema-validation.json` | 897 | `c7e9691a5719c65743120e2a738f751052a41237022a386562a89d43cb9b7c4c` |
| `source-hashes.json` | 2,859 | `718cbcd4ba704c3adbfefd0a3c0f46ca75bdeee6e3d83e1687924da98f04aea9` |
| `timed-child-stderr.log` | 103 | `1322596a6bde787444526999da7e46c191945166a5ed31899c7769d302dab3f9` |
| `validate.stdout.log` | 229 | `0f7218bc3d88fdb09493d925f4892a3ac3be0cf0003fa4f461db284f202528bf` |

`source-hashes.json` enumerates 18 authorities. Each byte count and SHA-256
matches the corresponding designer-commit blob and the unchanged executor
tree:

| Frozen source artifact | SHA-256 |
|---|---|
| `scripts/backref_cost_traceback_experiment_v1.json` | `bd07a2ebf37e9907fd5182959ac3e01d49249f6803ef584b3de68ae6afe814ee` |
| `scripts/backref_cost_traceback_schemas_v1.json` | `56448224ba69cf1fff4550adbe107d957b176216922bcaa4027b46b71e13ba73` |
| `CMakeLists.txt` | `f143cb5d034fb7ef369e6def35b11b3002cc93cacdbe021505dd19009914c8ca` |
| `makefile.unix` | `805edbb6cc55bc39d88e978aea536fd179fcc92730a38b57ee251af21acdf4df` |
| `doc/backref-cost-traceback-design-report-20260818.md` | `7d8aa30ea5aa98e6febb97cb9ee316edb26755c13f3710640f000a4663fade7b` |
| `doc/backref-cost-traceback-experiment-20260818.md` | `8468b00cbdf3a16400ed9f9f3b4c20bfbec911d7169fc7f3023821d967677379` |
| `doc/experiment-guard-matrix.md` | `603b5d8c65b4c963a03928780534115c628f73e2968a6dd8e049b2a7bfbbd824` |
| `scripts/run_backref_cost_traceback_experiment.py` | `00e259fbba76fd3721f7e3d432e1e5fd5d13ee5d20dbedd63ee9bdfbb56b7d72` |
| `scripts/test_backref_cost_traceback_experiment.py` | `c335a1866d25680717d849d3ce871456efe24d89b7a9570ab85332ee80e48c6a` |
| `scripts/test_experiment_guards.py` | `29131b22571282e62e53693fb9c12eed7a9e40a66a5d87757878d10a698419f2` |
| `scripts/generate_publication_corpus.py` | `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007` |
| `benchmarks/publication-corpus/manifest.json` | `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff` |
| `src/enc/backward_references_cost_enc.c` | `7a4a5d124aec642603374e9f4ff790a8d913598bf6aaae2057c51a2e50e006d0` |
| `src/enc/backref_cost_traceback_experiment_enc.c` | `1efec4acd747dc4fb1eee45c22d6b7b2b2fbafa4aab0885fec4f24b294be9d40` |
| `src/enc/backref_cost_traceback_experiment_enc.h` | `084a7bbf4d3d8d8e29bf5f9acb1dd56a00b83c70118fd5d6760584b0d5134846` |
| `tests/backref_cost_traceback_experiment_test.c` | `d633b90130db922b3026600825345665ca046d418529454818397975b4898371` |
| `tests/README.md` | `c15d09c01e09712f6b1b7faaa6a124586a571d9bb97c2b28cbd2f2f9874b86fe` |
| `tools/backref_cost_traceback_experiment_runner.c` | `f2e15321fd0b079c02b8750e5f4dcedc22e603b2fad6fd4beb2e235aeb4643f4` |

The manifest's 17 self-independent `frozen_artifacts` entries also match. The
manifest itself is separately bound by the source hash above.

## Refusal, preflight, lease, and process audit

The refusal files consistently identify designer commit `355efae8...`, frozen
parent `3142ff3f...`, a clean designer worktree, and preflight time
`2026-08-18T14:42:10Z`. The recorded host is an arm64 MacBook Pro `Mac16,7`
with Apple M4 Pro, 24 GiB memory, macOS 26.5.1, Xcode 26.3/Apple clang 17,
Metal 4, AC power, a charged battery, no thermal/performance/CPU-power warning,
no matching benchmark or CUDA process, more than 4 GiB available memory, and
ample disk. `nvcc` was not found.

The decisive field is `low_power_mode_ac: true`, corroborated in the artifact
as `Low Power Mode: Yes on AC Power`. The executor did not change power
settings. `lease-record.json` and `preflight.json` agree that the exact lock
path `/tmp/libwebp-metal-backref-cost-traceback.lock` was absent, no holder was
found, acquisition was not attempted, and release was not applicable because
the run never started.

Before evaluator work, a nonblocking exclusive probe of that exact lock
succeeded and was explicitly unlocked; the probe-created empty marker was then
removed. Process-table and `lsof` checks found no operator, runner, temporary
backref build, matching `cwebp`/`dwebp`, or open lock holder. A final check at
`2026-08-18T14:54:38Z` again found the lease path absent and no matching
process. These checks establish evaluator ownership only; they are not reused
as performance observations.

## Schemas and absent execution data

The frozen catalog defines six normal-output schemas:

- `libwebp-backref-cost-traceback-sample-v1`;
- `libwebp-backref-cost-traceback-command-v1`;
- `libwebp-backref-cost-traceback-correctness-v1`;
- `libwebp-backref-cost-traceback-evaluation-v1`;
- `libwebp-backref-cost-traceback-resources-v1`;
- `libwebp-backref-cost-traceback-artifact-hashes-v1`.

The artifact index parses and satisfies its catalog entry. No normal command,
sample, correctness, evaluation, or resource object exists to validate. The
intended `run` directory does not exist, and there is no `records.jsonl`,
`commands.jsonl`, `correctness.json`, `evaluation.json`, `resources.json`, or
`build.log` beneath it.

The exact reconstructed execution inventory is:

| Record class | Frozen requirement | Committed refusal evidence |
|---|---:|---:|
| command processes | 408 | 0 |
| cold measured samples | 264 | 0 |
| discarded warmups | 288 | 0 |
| warm measured samples | 1,296 | 0 |
| all measured samples | 1,560 | 0 |
| measured samples per variant | 780 | 0 |
| correctness cells | 26 | 0 |
| evaluation cells | 24 | 0 |
| mandatory holdout cells | 12 | 0 |
| resource records | 1 required for a completed run | 0 |

Five refusal metadata objects use clear versioned identifiers, but those
identifiers are not definitions in the frozen six-schema catalog:
`libwebp-backref-cost-traceback-preflight-v1`,
`libwebp-backref-cost-traceback-lease-record-v1`,
`libwebp-backref-cost-traceback-executor-refusal-v1`,
`libwebp-backref-cost-traceback-refusal-schema-validation-v1`, and
`libwebp-backref-cost-traceback-source-hashes-v1`. The two rows in
`executor-commands.jsonl` have no `schema` field. All parse, have the expected
internal shapes, and agree on the refusal, but they cannot be described as
catalog-validated refusal schemas. `schema-validation.json` accurately marks
normal timed-output validation not applicable; its name must not be read as a
formal validation of these ad hoc refusal envelopes.

The recorded `validate` subcommand proves the 17 frozen file hashes and returns
the manifest/operator hashes. By source inspection, that subcommand does not
call the operator's commit/worktree validator; the separate preflight source
record and this evaluation's Git/blob reconstruction provide those checks.

## Source, build, runtime, activation, and fallback audit

The candidate is omitted unless
`WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT` is enabled. That build option
privately defines `WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT` and adds only the
candidate helper, private test, and runner. Ordinary CMake and Unix make builds
omit the helper translation unit, private symbols, runtime/fault strings, test,
and runner. No installed/public header changes between base and designer.

Candidate dispatch additionally requires the exact value
`WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT=1`; other values remain off. The timed
runner independently requires exact `WEBP_BENCHMARK_SESSION=exclusive` and
rejects a baseline/candidate runtime mismatch. The frozen build protocol sets
Metal off and forbids CUDA. No Metal source, policy, public request structure,
threshold, CUDA source, or CUDA option changed.

Source reconstruction confirms one workspace allocation owns the pixel costs,
the exact cached-cost interval array, and 490 extra interval nodes while the ten
inline nodes remain first. Existing integer costs, DP traversal, strict
`manager->costs[i] > cost` updates, existing `cost >= interval->cost`
replacement relation, interval ordering, `dist_array`, traceback, cache
decisions, reference order, and final acceptance are unchanged. If workspace
allocation or the private injected workspace fault fails, the candidate attempt
is cleared before any DP update and the unchanged baseline path is rerun. Other
allocation/reference failures preserve the original error behavior.

The call site reaches `VP8LBackwardReferencesTraceBackwards` only on the
non-low-effort selected standard/box path at quality at least 25. The designer
report says a debugger stopped at entry for all 12 medium/large case-method
combinations. No debugger transcript, activation counter, or call-count record
was committed, and the executor produced no corroborating correctness or timed
record. The claim is therefore designer-reported, source-plausible activation,
not independently countable executor evidence. The retained candidate itself
contains no recorder or counter.

## Untimed evaluator validation

No candidate source was modified. The evaluator ran only the frozen hash/guard
checks and existing untimed equivalence, fallback, build-independence, corpus,
and sanitizer suite:

```sh
WEBP_EXPECTED_BACKREF_COST_TRACEBACK_COMMIT=355efae8dad9fc09717a4ccef874adf6bf6b2d6f \
  python3 scripts/run_backref_cost_traceback_experiment.py validate
python3 scripts/test_experiment_guards.py
python3 scripts/test_backref_cost_traceback_experiment.py
```

Results:

- frozen validator: pass; manifest
  `bd07a2ebf37e9907fd5182959ac3e01d49249f6803ef584b3de68ae6afe814ee`,
  operator
  `00e259fbba76fd3721f7e3d432e1e5fd5d13ee5d20dbedd63ee9bdfbb56b7d72`;
- shared guards: pass, including eleven independent build/runtime guards,
  fail-closed leases, and the next-boundary free-memory portability check;
- focused suite: pass for exact `PixOrCopy` equivalence, all 26 bitstream and
  decoded-pixel cells, deterministic repeat, invalid values, injected workspace
  fallback, default-build independence, corpus immutability, runner/session
  refusal, UBSan+integer, and array-bounds+pointer-overflow sanitizer smoke.

The focused suite builds and executes correctness cases without measuring or
recording elapsed values. Its runner checks are refusal-only and exit before
encoding. It neither acquires the benchmark lease nor invokes the timed matrix.

## Frozen criteria and consequence

| Criterion | Outcome |
|---|---|
| ancestry, frozen source hashes, and refusal artifact hashes | pass |
| fail-closed Low Power Mode handling | pass |
| build/runtime/session isolation and default omission | pass in source and untimed tests |
| source-level integer/tie semantics and transactional workspace fallback | unchanged; untimed tests pass |
| frozen executor correctness matrix | absent; unassessed |
| command/sample/evaluation/resource inventories | absent; mandatory gate unsatisfied |
| all 12 holdout paired medians at most 0.99 | absent; unassessed |
| all 12 holdout p95 ratios at most 1.01 | absent; unassessed |
| frozen all-gate promotion decision | **reject promotion for this cycle** |

The parent/PR lead must carry one explicit limitation: this cycle establishes
only a correct fail-closed refusal plus independent untimed candidate safety.
It establishes no performance direction, speedup, regression, resource bound,
or production readiness. The blocker is the absent mandatory executor matrix
caused by Low Power Mode on AC. Per the cycle instruction, that blocker closes
this attempt; it does not authorize a rerun or a follow-up gate. The next lead
is consequence integration: retain the code default off, label promotion
unassessed/rejected for this cycle, and make no production change.
