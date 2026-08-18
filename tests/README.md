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

## Building

### Fuzzers

Follow the [build instructions](../doc/building.md) for libwebp, optionally
adding build flags for various sanitizers (e.g., -fsanitize=address).

`-DWEBP_BUILD_FUZZTEST=ON` can then be used to compile the fuzzer targets:

```shell
$ cmake -B ./build -S . -DWEBP_BUILD_FUZZTEST=ON
$ make -C build
```
