# Tests

This is a collection of tests for the libwebp libraries, currently covering
fuzzing through the APIs. Additional test vector coverage can be found at:
https://chromium.googlesource.com/webm/libwebp-test-data

The repository-level `scripts/test_experiment_guards.py` test verifies that the
prepared encoder experiments are default-off, independently selectable,
and fail closed at their runtime and timed-launch boundaries. It never grants a
benchmark lease or runs timed work. See
`doc/experiment-guard-matrix.md` for the exact flag matrix.

`scripts/test_cache_size_serial_sweep_experiment.py` additionally verifies the
recorder-free cache-size implementation candidate, exact baseline equivalence,
transactional fallback, build omission, lease refusal, and sanitizer coverage.

`scripts/test_cache_size_single_pass_slab_experiment.py` verifies the private,
default-off single-pass contiguous cache-state slab: exact selected bits and
ties, immutable inputs, one-allocation layout, transactional fault fallback,
publication-corpus bitstream and decoded-pixel identity at methods 4 and 6,
runtime and lease refusal, build independence, determinism, and array-bounds,
pointer-overflow, undefined-behavior, and integer-sanitizer coverage. It runs no
timed protocol.

`scripts/test_backref_cost_traceback_experiment.py` verifies the private,
default-off CostManager workspace candidate: exact reconstructed references and
cache indexes, ties and edge sizes, deterministic repeats, injected workspace
fallback, publication stream/decode identity, immutable inputs, build/runtime
omission and sanitizer execution. It runs no timed protocol.

`scripts/test_backref_cost_workspace_ab_experiment.py` independently re-freezes
that unchanged workspace candidate behind new remote-A/B gates. It proves a
canonical preprocessed-source match to main `e7c1be7d...`, old-gate isolation,
default omission, exact publication-corpus streams and decoded pixels, injected
fallback, missing-session refusal, and sanitizer coverage without timing.

`scripts/test_backref_cost_workspace_remote_v2_experiment.py` establishes the
next independent v2 gate identity from main `d12036f...`. It checks the exact
validated candidate projection, all 26 method-4/6 correctness cells,
transactional fallback, sanitizers, prior-gate isolation, and complete default
artifact omission without invoking the recorder-free timing runner.

`scripts/test_backref_cost_workspace_remote_v3_experiment.py` re-establishes
the unchanged candidate behind wholly new v3 gates from baseline `805e5ac...`.
It verifies semantic projection, all 26 method-4/6 correctness cells,
transactional fallback, old-gate isolation, sanitizers, and default source,
symbol, target, runtime, and fault-string omission. The companion admission
test exercises canonical paths, an empty repository-context bundle verify,
exact commit/tree/source hashes, malformed rejection, cleanup, and the shared
admission-only/executor implementation without timing.

`scripts/test_backref_cost_workspace_remote_v4_experiment.py` proves that v4
retains the exact frozen v3 candidate semantics under independent gates and all
26 correctness/fallback/sanitizer/ordinary-build omission checks. Its archive
test covers indexed explicit-member construction, canonical containment,
complete pre-extraction inventory, safe extraction and local returned hashes,

`scripts/test_backref_cost_workspace_remote_v5_experiment.py` proves the
independent v5 candidate identity, exact 26-cell correctness/fallback behavior,
predecessor isolation, default omission, and sanitizer coverage. The companion
v5 protocol/admission/archive tests prove explicit make-toolchain admission,
indexed controlled refusals, AppleDouble/xattr rejection, repository-context
source admission, independent lease/cleanup return, and frozen matrix counts.
plus traversal, absolute, symlink, hardlink, FIFO, and nonregular rejection.
The frozen live design record exercises the same builder/extractor over ssh on
`pandocs-agent` without a benchmark session, lease, runner, or timed command.

`scripts/test_backref_cost_interval_search_v1_experiment.py` verifies the new
strictly-after-tail CostManager positioning index across 26 publication cells,
candidate-off and predecessor-gate isolation, deterministic repeat, injected
pre-DP exact fallback, decoded pixels, ordinary-build omission, and sanitizer
coverage. Its separate recorder is untimed and omitted from timed binaries;
the protocol/admission/archive tests retain the proven indexed return,
independent lease/cleanup, and noninteractive Unix-make admission structure
under new v1 identities.

`scripts/test_backref_cost_interval_search_v2_experiment.py` verifies the
PushInterval-local scan-derived append hint across the same 26 publication
cells, candidate-off and predecessor-gate isolation, deterministic repeat,
injected pre-DP fallback, decoded pixels, default omission, and sanitizer
boundaries. Its recorder is untimed and absent from both timed binaries; the
v2 protocol/admission/archive tests retain indexed safe return, independent
lease/cleanup, exact-child absence, and admitted noninteractive Unix make.

`scripts/test_backref_cost_interval_search_v3_experiment.py` verifies the
same normalized PushInterval-local candidate under fresh v3 gates, including
unchanged `CostManager` layout, equal-start behavior, transactional fallback,
sanitizers, fuzzed boundaries, default omission, gate isolation, and the
v3-only recorder/recorder-free timing split. Its protocol tests additionally
enforce the repaired admission-receipt fields and disjoint mode/session table.

`scripts/test_backref_cost_interval_specialization_v1_experiment.py` verifies
the production-shaped continuation: one pre-DP runtime selection chooses the
ordinary DP or a distinct always-on v3 local-hint DP, while the optimized hot
candidate has no experiment-control parameter or dataflow. It retains the v3
semantic, work, fallback, sanitizer, ABI, omission, and protocol gates.

## Building

### Fuzzers

Follow the [build instructions](../doc/building.md) for libwebp, optionally
adding build flags for various sanitizers (e.g., -fsanitize=address).

`-DWEBP_BUILD_FUZZTEST=ON` can then be used to compile the fuzzer targets:

```shell
$ cmake -B ./build -S . -DWEBP_BUILD_FUZZTEST=ON
$ make -C build
```
