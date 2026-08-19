# Backref-cost interval specialization v1: design and Phase-1 evidence

## Causal premise and exact mechanism

The verified base is `b2c71348c21371877328639efb5a929f2130bd09`.
No v1, v2, or v3 timing is reused, pooled, relabeled, threshold-fit, or
content-specialized. V3 remains the semantic reference only.

Recorder-free Apple-clang 17 arm64 `-O3 -DNDEBUG` codegen proves the premise.
V3 emits one 1,160-byte/290-instruction dynamic `PushInterval`, receives
`use_append_hint` in `w4`, materializes and spills the control, and retains six
direct control tests/branches plus a reload. Its hot-path counts are 64 branch
instructions (39 conditional), 52 loads, and 37 stores. The compiler therefore
does not specialize the experiment control away.

The candidate evaluates exact runtime activation once in
`VP8LBackwardReferencesTraceBackwards`, before either DP mutates `dist_array`.
Exact injected fallback is also selected there. Two private DP instantiations
share one include body: the baseline calls ordinary `PushInterval`; the
candidate calls distinct `PushIntervalSpecialized`. The candidate has no
`use_append_hint` argument, runtime-control conditional, recorder code in its
timed build, or gate-derived load. Its specialized push is 788 bytes/197
instructions with 42 branches (27 conditional), 37 loads, and 20 stores; all
targeted control arguments, tests, spills, and reloads are zero. The larger
experiment object contains both independently selectable paths, as a
production runtime selector necessarily would.

## Semantic and work identity

Fresh preprocessing transforms the exact v3 recorder-free function by making
the runtime flag constant true and removing only its dead control argument,
checks, and recorder-only arguments. The normalized result exactly equals
`PushIntervalSpecialized` at SHA-256
`e8f07cd30016566188a5a73e7c7f10c23dbc4f8e3d3ff08de332555e35eb0c35`.
The hint remains local to one push, follows only nodes traversed by that push,
moves after successful tail insertion or an in-call visited-tail pop, and is
used only for a null-hint insertion with strict `start > append_hint->start`.
Equal starts retain baseline positioning.

`CostManager` remains exactly 33,224 bytes in baseline, v3, and this candidate.
There is no field, persistent tail, node-cap, allocation, ordering, lifetime,
integer-cost, tie, update, traceback, cache, reference-order, input, ABI, or API
change. The baseline and candidate still produce identical bitstreams and
decoded pixels, deterministic repeats, and exact transactional fallback.

The separate untimed recorder reproduces all 36 v3 publication rows:
5,585,685 baseline and zero candidate forward positioning steps; 53,769
backward steps in both; 1,062,260 candidate fast paths; and 99.0466% total
positioning-step elimination. Every non-search counter is unchanged. Recorder
calls are compile-guarded and absent from recorder-free candidate binaries.

## Independent gates and frozen protocol

The fresh controls are
`WEBP_BUILD_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT`,
`WEBP_USE_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT`, and exact
runtime `WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_EXPERIMENT=1`.
`WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER` is untimed-only. The
specialization is compile-time mutually exclusive with all overlapping
backref-cost experiments. Ordinary builds omit its object, symbols, strings,
runner, and target.

The v3 receipt repair, mode/session truth table, repository-context admission,
noninteractive Unix-make toolchain, explicit artifact index, safe archive and
all-or-nothing extraction, independent lease/cleanup returns, and exact-child
deletion are retained under new identities. Rehearsal requires `mode rehearse`
with `WEBP_BENCHMARK_SESSION` absent and never attempts a benchmark lease or a
timed invocation.

The minimum causal gates were frozen before timing: exact v3 algorithm/work
identity and actual removal of every targeted runtime-control operation.
Both pass. The timing matrix remains photo-medium/graphic-medium tune and
photo-large/graphic-large holdout; methods 4/6; cold/warm; alternating order;
272 processes; 1,040 retained samples. Promotion remains conjunctive across
all eight holdout cells at paired median `<= 0.995` and raw nearest-rank p95
ratio `<= 1.005`, plus every semantic, correctness, work, operational,
resource, lease, archive, return, and cleanup gate.

Final source hashes, exact commands, rehearsal receipts, and Phase-1 timing
authorization are frozen in the manifest and
`evidence/backref-cost-interval-specialization-v1-design/phase-1-freeze.json`.
