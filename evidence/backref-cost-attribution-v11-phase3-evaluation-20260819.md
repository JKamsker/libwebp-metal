# Backref Cost Attribution V11 — Phase 3 independent evaluation

Decision: **BLOCKED / UNASSESSED**. V11 produced no timed evidence, does not close or reopen the interval family, supports no CPU-stage ranking, authorizes no production change, and authorizes no future run.

## Frozen identity and authority

The audited chain is exact and linear:

`631ac52803ff7d74f8461917503d54b46a8fc5e4` → `e19eb84a61400af2d434004e8ff1e2fdf692a288` → `34c2b2782b421e90aa59bf87e06b46f9509184df` → `0baf0ac9bb6ccffedf5bdb179d9bbe33306d45df`.

Trees are `4e972436a292429cf0cf7aa185d68ad49eda6f6c`, `ae61de93df238c4cb1c47e01049b8586803dc420`, `b56b3decca3096707e8b84da724749b9423fa7fb`, and `090ee805029e8f09f3b50673ba329eeff39caec2`. The binary diff SHA-256 values for base→1A, 1A→1B, and 1B→2 are respectively `d77ad6ba424976b305fdd81d1d6bbf74217fcac8d01c5052fa2749792ec01edc`, `2e87648726b5b3fcfb96f7f6a6c100e1b43ffc6f2bb288898ae80087e8d255eb`, and `f2b055a1119d533f7267d430d2c6f1b4adb15da90d94bbe93334a12ed99aa610`.

Phase 1B adds only its authorization, hash index, and raw rehearsal evidence. It does not embed its own commit. Phase 2 adds only its refusal audit and does not alter Phase 1. This preserves non-circular 1A→1B authority. The final authority is nevertheless `REFUSED`: `timed_execution_authorized=false` and `phase_2_authority=NONE`.

The Phase 1A source receipt identifies the exact 1A commit/tree and all 28 recorded source hashes recompute correctly. All 27 frozen manifest artifact hashes also match. Public headers and `sharpyuv` have no diff from the base. The frozen manifest declares Metal disabled, `makefile.unix`, `-O3 -g -DNDEBUG -fno-omit-frame-pointer`, and fixed clang/xcrun/nm hashes. Toolchain, device, and resource receipt contents cannot be independently recovered because their declared archive was truncated.

## Implementation audit

V11 is isolated behind the fresh build, compile, and exact runtime gates:

- `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT`
- `WEBP_USE_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT`
- `WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT=1`

Ordinary and gated make dry-runs passed: the ordinary target omits V11 macro/object/runner text; the gated target contains the V11 private macro and object without a V10 compile gate. The public header tree is unchanged. The Phase 1 validation artifact records 16 correctness encodes, 16 boundary fixtures, two sanitizer configurations, four counter cells, public API/ABI equality, ordinary-build omission, deterministic/fallback behavior, and single-selected-DP/no-overwrite checks. Phase 3 hash-verified those claims but did not rebuild or run them.

The V11 parser consumes PID, PPID, and the complete remaining UTF-8 `comm` field. It treats `raw_comm` as opaque, derives `lexical_basename` only with a final-slash string split, performs no filesystem identity lookup, and never collects argv. Self must exist and exact PPID edges must form a complete acyclic chain to PID 1. Malformed rows, duplicate PIDs, self-parent edges, missing ancestor parents, ancestor cycles, invalid identity text, and non-PID1 `ppid=0` refuse. There is no positive ancestor executable set. Arbitrary names, spaces, slashes, path-like tokens, and benign lexical collisions pass. Every row, ancestor or not, refuses only on an exact denied raw or lexical identity; lookalikes pass, and `Runner.Listener` is not denied.

Process refusals use a bounded canonical JSON object with exactly `schema`, `failure_code`, `pid`, `ppid`, `raw_comm`, `lexical_basename`, `is_ancestor`, and `is_conflict`; the integrity footer carries its SHA-256. The schema excludes argv, environment, source, payload, command text, and filesystem identity. This evidence is never authority. The live rehearsal emitted no process diagnostic because structural ownership passed: 743 rows, four self-to-PID1 ancestors, zero exact conflicts, and zero discovered-PID signals.

Algorithm and timer structure match V10 after version-name normalization. V11 evaluates its selector once before mutation and enters exactly one closed baseline/candidate DP branch. Counters identify the selected body and prevent opposite-body overwrite. `dp_total` wraps that body once; `dp_setup` covers allocation through successful `CostManagerInit`; `dp_steady` covers the initial literal and pixel loop; traceback and materialization are separate. Darwin uses `mach_continuous_time`; there is no per-pixel or `PushInterval` clock. Frozen Phase 1 validation records 4,096 reads, 17 ns mean delta, and 4,625 ns maximum delta.

The transport uses one noninteractive SSH session. Only its retained directly-created child handle, PID, and object identity can be stopped at timeout. Remote state is one validated V11 child; the same session removes only that child in `finally` and must return cleanup plus absence as its last footer. No post-session cleanup path exists.

## Raw rehearsal reconstruction

The raw stdout is 1,941,990 bytes with SHA-256 `f6cb02af4d445ac355bdf007f8cfc19daf19d98d3e45647e0689f89264f848f4`. Eight complete frames and every complete payload hash validate in this order:

1. source admission — verified
2. operator status — complete, zero workload
3. archive build — accepted
4. lease state — not attempted
5. bulk declaration
6. bulk chunk 0
7. bulk chunk 1
8. bulk chunk 2

The next frame is chunk 3. It declares 524,288 payload bytes but contains only 359,772; the partial frame occupies 359,941 bytes. Three complete chunks contribute 1,572,864 bytes, and the partial chunk raises the locally observed compressed payload to 1,932,636 bytes—36.6275602189577% of the declared archive. The missing payload is 3,343,817 bytes. No integrity footer or cleanup/absence footer follows. The archive was not extracted.

The declared archive is 5,276,453 bytes (`21b9e17df32ed4416e9728cf0836081f1d6c2a6c8dca2dc86e6ff89bf65377a2`), 1,082,149 bytes or 25.8004% above the frozen 4 MiB expected-run bound, and 33,573 bytes or 0.6404% above the 5 MiB representative payload. The retained transport reached its fixed 7,200-second timeout during the fourth chunk. Cleanup is unknown, and the required no-second-cleanup rule was observed.

The Phase 1B hash index has correct file membership, byte sizes, and SHA-256 values, but it is not in the strict lexical order enforced by `verify_rehearsal_hash_index`. Its order is:

1. `rehearsal-invocation.json`
2. `transfer-cleanup.json`
3. `return-protocol/framed-stdout.bin`
4. `return-protocol/transport-stderr.bin`

The required order places both `return-protocol/*` entries before `transfer-cleanup.json`. This is resolved for Phase 3 by preserving immutable Phase 1 evidence and recording an independent fail-closed blocker. The index is not repaired, authority is not relaxed, and the executor is not invoked.

## Performance reconstruction

No timed process ran. Therefore every available case/method cell has zero baseline and candidate rows:

| Case | Method | Baseline rows | Candidate rows | Whole encode | Backrefs | DP total/setup/steady | Trace/materialize | Downstream | Shares/deltas/medians/repeatability |
|---|---:|---:|---:|---|---|---|---|---|---|
| photo-large | 4 | 0 | 0 | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| photo-large | 6 | 0 | 0 | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| graphic-large | 4 | 0 | 0 | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| graphic-large | 6 | 0 | 0 | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |

Raw whole-encode, backward-reference, DP total/setup/steady, traceback, materialization, histogram, Huffman, and bitstream/downstream values do not exist. Shares, baseline/candidate deltas, medians, and repeatability cannot be computed. No CPU stage can be ranked. Even complete coarse rows would not establish `PushInterval` self-time, call-stack, code-layout, cache, or branch-predictor causality.

## Blockers and final disposition

The blocker chain is explicit:

1. `CALIBRATION_BOUND_INVALID`: the archive exceeded both frozen calibration bounds.
2. `TRANSPORT_TIMEOUT_TRUNCATED_BULK`: only 3 of 11 chunks completed before timeout.
3. `INTEGRITY_AND_CLEANUP_FOOTERS_ABSENT`: integrity, exact cleanup, and absence are unproved.
4. `AUTHORITY_NONE`: Phase 1B refused timing and Phase 2 correctly did not execute.
5. `FROZEN_HASH_INDEX_UNORDERED`: the executor's independent strict-order gate would also refuse.
6. `NO_PERFORMANCE_EVIDENCE`: zero timed processes, warmups, retained rows, and total rows exist.

Process counts are: one Phase 1 rehearsal session; zero retries and reruns; zero Phase 2 executor, transport, or remote sessions; zero lease attempts; zero encoder, benchmark, timing, profiler, and CUDA workloads; zero Phase 3 process discoveries; zero signals; and zero Phase 3 or post-rehearsal cleanup operations. The frozen plan was 24 serial processes, 24 warmups, 96 retained rows, and 120 total rows; all executed counts are zero.

Phase 3 performed no encoder/workload/transport/diagnostic/rehearsal execution, no process discovery, no signal/kill/interrupt, and no remote or PID cleanup. It did not modify Phase 1 or Phase 2 evidence, contact the remote host, promote production code, schedule a run, or authorize another experiment.

Bounded local checks passed for chain/tree/diff hashes, 28 source-admission hashes, 27 manifest artifact hashes, frame decoding through truncation, JSON parsing, ownership/diagnostic/signal contracts, protocol/authority/plan semantics, archive safety/no-partial extraction, public-header diff, and ordinary/gated make dry-runs. The hash-index lexical-order check intentionally reports the frozen blocker. Encoder correctness, sanitizer, API/ABI runtime, and timer runtime checks were not rerun; their frozen Phase 1 evidence was hash-verified only.

Final decision: **V11 is unassessed and blocked. No production change. No future run.**
