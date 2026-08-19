# Backref cost attribution V3 — Phase 3 independent evaluation

## Decision

The interval family is **unassessed** in this cycle. It is neither closed nor
reopened, no next CPU boundary is ranked, and no follow-up experiment is
proposed or run. Phase 2 correctly failed closed before remote admission
because Phase 1 remained `PENDING_REMOTE_REHEARSAL` with
`timed_execution_authorized=false`.

There are no V3 timing rows. Consequently there are no whole-encode,
backward-reference, selected-DP total/setup/steady, traceback,
materialization, histogram, Huffman, serialization, share, delta, median, or
repeatability statistics to report. A zero row count is not a zero duration.

## Independent identity reconstruction

The history is exact and linear:

1. frozen main `086059436a46f1d5cd48d401fc06e2f96bbf095b`, tree
   `68e364d94feafb9a85e8d138f5e5ea5a37f2a594`;
2. Phase 1 `a8a9dfdb3cd882d63980f4234c40e5c8cb91f5e1`, parent frozen main,
   tree `af7eabc288db9de596d16b1b6a51c38ab25174bf`, 24 changed files,
   4,051 insertions and 180 deletions;
3. Phase 2 `e9b807695a7db1b688c1a920ef5038132fbab4cb`, parent Phase 1,
   tree `3750887d3c87849a2b6cd29bee02f0641d8d2170`, two evidence files and
   134 insertions.

Frozen identities independently match:

- manifest: `123fed6025da0fe1e054c7d6384f8a02bd63bdc11a7c2e93b9948da70f908e64`;
- protocol: `9deb1aeaa39434d4c0e4cbfca98da4e5cdcfc90414071a2e1f851cfab8a5c76c`;
- schema catalog: `99bdd77af00dec49ae080a4c92cd18e002c2d4da877a2a7f7592d14980d7f90a`;
- all 25 frozen artifact hashes match, with zero mismatches;
- Phase 2 refusal JSON: `edfdc29b4e24a1c6bec4f0b394e6b942db132f455461f7795267c6266f0be106`;
- Phase 2 command transcript: `2c85ed5f4414d4a675e859960f928c0d2834632de7523b2eb02668ae64ac92de`.

The machine-readable audit records every frozen file hash, all nine schema
identities, commit trees, and Phase 2 Git blob identities.

## Authorization, command, and evidence counts

Phase 2 invoked the one frozen wrapper once from the clean Phase 1 identity;
the expanded expected commit was
`a8a9dfdb3cd882d63980f4234c40e5c8cb91f5e1`. It exited 1 with the exact
authorization refusal before `prepare_remote()` could run. The committed
Phase 2 evidence directory contains exactly two refusal files and no profile,
stage, record, or JSONL file.

| Item | Frozen plan | Actual Phase 2 |
|---|---:|---:|
| wrapper invocations | 1 | 1 |
| serial profile processes | 24 | 0 |
| pre-timing correctness encodes | 16 | 0 |
| pre-timing counter-check encodes | 8 | 0 |
| timed profile encodes | 120 | 0 |
| total encoder encodes | 144 | 0 |
| warmups | 24 | 0 |
| retained rows | 96 | 0 |
| total runner rows | 120 | 0 |
| total stage rows | 120 | 0 |
| profiler invocations | 0 | 0 |
| CUDA invocations | 0 | 0 |
| production promotions | 0 | 0 |

The intended 24-profile order reconstructs exactly as photo-large before
graphic-large, method 4 before method 6, with repetition variant order
baseline/candidate, candidate/baseline, baseline/candidate. None of those
profile commands executed.

For every case/method cell—photo-large method 4, photo-large method 6,
graphic-large method 4, and graphic-large method 6—baseline rows are 0,
candidate rows are 0, and all requested timing summaries are unavailable.

## Repaired diagnostic audit

The V3 build uses independent default-off build, compile, and exact-value
runtime gates and excludes predecessor gates. Its selector is read once before
DP mutation. A closed `if/else` selects exactly one baseline or specialized DP
body, while the predecessor common baseline chain is in the opposite
preprocessor branch. Body-entry counters are instantiated separately for the
baseline and candidate implementations.

`dp_total` begins immediately before that sole selected call and ends after
the body has performed cleanup and returned. Setup covers allocation through
successful `CostManagerInit`; steady covers only the initial literal and pixel
DP loop. Traceback and materialization have separate boundaries. No clock is
inside `PushInterval` or another per-pixel helper.

The required successful-encode relationship is preserved in source and runner
validation:

`selected_dp_calls == selector_evaluations == dp_total.calls ==
dp_setup.calls == dp_steady.calls`, with `setup + steady <= dp_total` and
`dp_total + traceback + materialize <= lossless_backward_refs`.

## Untimed final validation

All final validation was local and untimed; it made no remote mutation,
acquired no lease, invoked no profiler or CUDA path, and sent no process
signal.

- Protocol, admission, indexed archive, and absolute ownership tests passed.
- The 23-gate isolation/default-off matrix passed.
- Sixteen correctness encodes passed across both immutable large corpus cases,
  methods 4/6, baseline/candidate, and two repeats. Bitstreams were identical
  and deterministic, decoded RGB matched, and input hashes remained unchanged.
- Four direct case/method counter cells passed for both variants: selector
  count equaled the selected body count, the opposite body count was zero,
  candidate and baseline products matched, and explicit reset returned all
  counters to zero. This rules out the V2 duplicate call and candidate-result
  overwrite in the tested V3 structure.
- Two sanitizer configurations passed 16 boundary fixtures.
- Public API/ABI equality, ordinary-build omission, and the exact runtime truth
  table passed; only the exact value `1` enables the candidate.
- Synthetic accounting passed for both variants with selector, selected DP,
  `dp_total`, `dp_setup`, and `dp_steady` calls all equal to 1 and valid
  setup/steady nesting.
- The local 4,096-read monotonic clock check passed: 1,043 positive deltas,
  10 ns mean read delta, 41 ns minimum positive delta, and 42 ns maximum delta.
- The local driver `validate` mode passed at Phase 2 commit with no benchmark
  lease attempt and no timed binary invocation.

These checks establish that the repaired V3 diagnostic is structurally and
functionally credible. They do not replace the missing frozen remote timing
run and are not performance evidence.

## Device, resource, ownership, and return evidence

The manifest freezes a target of Darwin arm64, Mac16,10 / Apple M4, 24 GiB,
Apple clang 17.0.0, and SDK 26.2. Phase 2 observed none of that target state:
authorization failed before remote admission. No actual remote source,
toolchain, device, thermal, memory, disk, or competing-process receipt exists.

Phase 2 contacted no remote host, performed no process discovery, spawned no
workload child, attempted no lease, archive, transfer, extraction, or cleanup,
and created no run directory. Therefore lease/archive/cleanup receipts are
absent and not applicable to a Phase 2 run. Reported session `37199` remained
untouched throughout Phase 2 and Phase 3.

## Consequence and limitation

V3 repaired and revalidated the attribution-v2 duplicate-DP/fallthrough
defect, but the attribution objective itself was not executed. Without timed
rows, this evaluation cannot say why the approximately 99% interval-positioning
work reduction and graphic wins did not translate to photo end-to-end wins.
It cannot close or reopen the interval family and cannot rank a next CPU
boundary.

The final blocker remains the missing accepted controlled no-workload remote
rehearsal. Any future diagnostic would require wholly new independent gates;
none is authorized, proposed, or run here. There is no production change.

The complete machine reconstruction is in `phase3-audit.json`.
