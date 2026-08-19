# Frozen backref-cost interval-specialization v1 protocol

The sole Phase-2 authority, only when the manifest sets
`timed_execution_authorized` to true, is:

```sh
env WEBP_BENCHMARK_SESSION=exclusive WEBP_EXPECTED_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_interval_specialization_v1.py run /Users/jonaskamsker/.codex/worktrees/c038/libwebp-metal/evidence/backref-cost-interval-specialization-v1-execution-20260819
```

`validate` and `rehearse` require `WEBP_BENCHMARK_SESSION` to be absent and
cannot acquire the benchmark lease or invoke timing. `run` requires exact
`exclusive`, uses only its run guard, and is the only path to the operator's
exclusive nonblocking lease and recorder-free timed matrix. Every controlled
exit remains indexed and returnable; any refusal is terminal and is not a
retry authority.

Source admission requires the exact clean handoff commit/tree, frozen hashes,
matching local/remote git-bundle SHA-256, repository-context bundle verify,
detached checkout, and source hashes. The versioned receipt requires string
`source_bundle_sha256` and string `admission.bundle_sha256`, both equal the
local hash and each other. Toolchain admission requires the frozen canonical
Apple tools, explicit SDK, `/usr/bin:/bin:/usr/sbin:/sbin`, and Unix make.

Before timing, three clean builds are required: default baseline,
recorder-free v3 candidate, and separate untimed v3 recorder candidate. The
26 correctness cells cover 13 publication rows by methods 4/6, exact
bitstreams, decoded pixels, repeat determinism, candidate-off/default omission,
predecessor-gate isolation, immutable inputs, and transactional fallback. In
all active work cells, candidate positioning must be at most 10% of baseline,
activation and append-hint fast paths must be positive, forward positioning
must be removed, backward positioning and all non-search counters must match,
and hint/update/pop accounting must be internally consistent.

The timing order is tune before holdout, photo before graphic, method 4 before
6, cold before warm, then the frozen 11-pair alternating order. Inventory is
272 command processes, 176 cold retained samples, 192 discarded warmups, 864
warm retained samples, 1,040 retained total, 520 retained per variant, 16
evaluation cells, and eight required holdout cells. Timing authority is
runner-local `mach_continuous_time` around `WebPEncode` only.

Promotion requires every photo-large and graphic-large method/lifecycle cell
to pass both paired-median `<= 0.995` and nearest-rank raw-p95 `<= 1.005`, plus
all operational and correctness gates. There is no pooling with v1, v2, or any
workspace cycle, no threshold adjustment, content-specific promotion, retry,
local timing fallback, tuning, or protocol edit.
