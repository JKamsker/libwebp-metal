# Frozen remote v4 protocol

The sole timing pipeline is `execute_backref_cost_workspace_remote_v4.py run`
to `pandocs-agent`, after an exact clean source handoff commit is supplied in
`WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V4_COMMIT` and
`WEBP_BENCHMARK_SESSION=exclusive`. The driver retains the v3 canonical path,
source bundle hash, empty bare verification repository, repository-context
`git bundle verify`, detached commit/tree, clean-status, and source-hash gates.

Before builds, the operator fails closed unless the host is the frozen Darwin
arm64 M4 identity, the compiler and effective SDK match, AC power is active,
Low Power Mode is off, thermal/performance records are clear, memory/disk
minimums pass, and no `Runner.Worker`, benchmark, or CUDA process is active.
`Runner.Listener` may remain active; no service, runner directory, host, power,
or device state is changed.

The one nonblocking v4 lease surrounds two serial static Release builds,
correctness, and all timing. There is one timed child at a time and no recorder,
CUDA, local timed fallback, or asynchronous work. The corpus/order/counts are:

- correctness: 13 case/quality rows x methods 4 and 6 = 26 cells;
- timing: medium photo/graphic/texture tune, then large photo/graphic/texture
  holdout; method 4 then 6; cold then warm;
- cold: 11 alternating process pairs, one measured encode, zero warmups;
- warm: six alternating process pairs, two discarded then nine measured;
- 408 command processes, 264 cold measured, 288 warmups, 1,296 warm measured,
  1,560 total measured, 780 measured per variant, 24 evaluation cells, and 12
  required holdout cells.

Timing is runner-local `mach_continuous_time` around `WebPEncode` only. Each
cell uses the median of paired candidate/baseline process medians and the
nearest-rank raw p95 ratio. Tune cells are descriptive. Every holdout cell must
have paired median ratio <= 0.99 and p95 ratio <= 1.01. Promotion additionally
requires every identity, ordinary-build omission, isolation, 26-cell bitstream,
decoded-pixel, repeat, fallback, immutable-input, host-state, lease, resource,
inventory, archive/member/hash, returned-index, and exact-cleanup gate.

Evidence return has three independent channels in this order: hash-verified
lease record; indexed archive, digest, and full inventory; post-deletion cleanup
receipt. Extraction is all-or-nothing. Failure retains protocol logs and, for
an extractor rejection, the quarantined archive and exact rejection inventory.
`transfer-cleanup.json` is intentionally created after and excluded from the
already verified local returned index; that exclusion is explicit in the index.

Any mismatch refuses the cycle. There is no rerun, edit, parameter change,
fallback timing, pooling, threshold adjustment, or production consequence in
the executor. The evaluator alone audits and applies the frozen decision.
