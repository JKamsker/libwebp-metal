# Backref-cost interval-search v3 design and Phase-1 evidence

## Scope and candidate identity

The verified base is `c472599ce8d3aee1e4f5bcf70b56b9c354351660`.
V1 remains rejected and v2 remains untimed; neither cycle contributes samples
or is relabeled. V3 is an infrastructure-only port of v2's
`PushInterval`-local scan-derived append hint. Normalized preprocessing and
helper-source tests require the v2 and v3 candidates to be identical after
private version names are removed. Both layouts require a 33,224-byte
`CostManager`; v3 adds no field, persistent tail, or `ConnectIntervals`
bookkeeping.

The local hint starts null in each `PushInterval`, follows only nodes already
visited by that call's monotonic overlap scan, moves after a successful tail
insertion or an in-call pop of the visited tail, and dies on return. Only the
final null-hint insertion may use it, and only for `start > append_hint->start`.
Equal starts execute the baseline path. Integer costs, ties, replacement and
update order, interval lifetime, allocation/recycling, traceback, cache and
reference order, input immutability, and pre-DP transactional fallback are
unchanged.

Fresh controls are
`WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT`,
`WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT`, and exact runtime
`WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT=1`. The optional recorder has
the separate `WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_RECORDER` compile guard and
is forbidden from timed binaries. All overlapping backref experiments are
compile-time mutually exclusive. Ordinary targets omit v3 objects, symbols,
runtime/fault strings, and the runner.

## Receipt and mode repair

The versioned source-admission receipt has authoritative top-level
`source_bundle_sha256` and nested `admission.bundle_sha256`. Both must exist,
be strings, equal the locally computed bundle SHA-256, and equal one another.
No v3 code reads a top-level `bundle_sha256`. Contract fixtures reject missing,
renamed, wrong-type, unequal, wrong-local-hash, and unexpected-version forms.

Execution has three disjoint modes. `validate` is local and untimed;
`rehearse` is remote and untimed and requires the benchmark-session variable
to be absent; `run` is the only timing mode and requires its exact value to be
`exclusive`. Run uses a run-only guard and does not call the rehearsal guard.
The exhaustive environment table includes absent, empty, exact, case-changed,
numeric, and unrelated values. Rehearsal creates a non-acquired lease record,
never opens the benchmark lease, and returns it independently before safe
archive extraction.

## Preserved pipeline and frozen question

The pipeline retains the v5/v1 canonical safe root, repository-context git
bundle verification, explicit noninteractive Apple Unix-make toolchain and
SDK, Python indexed archive builder and all-or-nothing extractor, independent
lease-record transfer, exact-child deletion, and post-delete absence proof.
CMake is used only by local correctness testing, never by remote execution.
There are no installs, downloads, global `PATH`, host, runner/service,
directory, power, Low Power Mode, CUDA, or parallel benchmark changes.

Tune is photo-medium and graphic-medium; holdout is photo-large and
graphic-large. Methods 4/6 and cold/warm are independent. Cold uses 11
alternating process pairs with one retained encode and no warmup. Warm uses six
alternating pairs with two discarded warmups and nine retained encodes. The
matrix has 272 command processes and 1,040 retained samples. Tune is
descriptive. All eight holdout cells must conjunctively satisfy paired median
ratio `<= 0.995` and nearest-rank raw p95 ratio `<= 1.005`, along with every
identity, correctness, work, host, resource, lease, archive, transfer, and
cleanup gate.

## Phase-1 evidence and decision

All gates passed and Phase 1 authorizes exactly one frozen Phase-2 run. Local
full-publication recorder evidence has 36 rows: baseline positioning is
5,585,685 forward plus 53,769 backward steps; v3 is zero forward plus the same
53,769 backward steps, a 99.047% total reduction, with 1,062,260 append-hint
fast paths. The exact remote rehearsal's 16 tune/holdout rows reproduce zero
forward steps, unchanged 50,215 backward steps, 1,011,082 fast paths, and a
99.065% total reduction. Neither record contains an elapsed field.

The success rehearsal admitted provisional clean commit
`0ed73d55dbf193902550f7787d3c3937275958ca`, executed ten exact Unix-make
commands, 26 correctness cells, and 16 work rows, then safely returned a
ten-member indexed archive plus an independent non-acquired lease record. The
separate controlled missing-make refusal returned its four-member indexed
archive. Both transfer wrappers prove matching top-level/nested/local bundle
hashes, zero benchmark-lease attempts, zero timed invocations/samples,
exact-child deletion, and absence. Final evidence lives under
`evidence/backref-cost-interval-search-v3-design/remote-rehearsal-success` and
`remote-rehearsal-refusal`.

The final evidence inventory, frozen source hashes, exact command, and
authorization are in `scripts/backref_cost_interval_search_v3_manifest.json`
and `phase-1-freeze.json`. V1 and v2 remain unpooled and retain their original
decisions.
