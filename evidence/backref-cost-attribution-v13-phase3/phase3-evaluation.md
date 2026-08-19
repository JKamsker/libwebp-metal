# Backref cost attribution V13 — Phase 3 independent evaluation

Date: 2026-08-19 (Europe/Vienna)

Evaluator: Phase 3 only (Sol/high)

Status: **REFUSAL CONFIRMED; INTERVAL FAMILY UNASSESSED; NO EXECUTION AUTHORITY**

## Decision

The interval family is **unassessed**. Phase 2 correctly refused in
`BULK_STREAM` at the `bulk-progress` deadline. No complete archive, integrity
footer, cleanup/absence footer, safe extraction, production diagnostic, or
timing rows exist in the persisted V13 evidence. Consequently:

- production and future execution are not authorized;
- the family cannot be closed and no new experiment is authorized;
- whole-encode, backward-reference, DP total/setup/steady, traceback,
  materialization, downstream, share, delta, median, repeatability, and limit
  values are all unassessed;
- no CPU stage can be ranked.

This evaluation does not reuse predecessor timing. It does not infer missing
values from declarations, protocol bounds, or prior-cycle observations.

## Identity and authority

The history is exactly linear:

1. main/base `7700d05060803afcac030aa5452849f93515b0d8`;
2. Phase 1A `258b217e3b277bc694ccf11f890e41c7c32efb78`, sole direct child of base;
3. Phase 1B `10efe0c337ea0a82e6ba99c73a246671bb9c5554`, sole direct child of 1A;
4. Phase 3 is the commit containing this report, a direct child of 1B.

The Phase 1A tree is `932483a6c9a1e419af0f67ed173ea5c73f87ef03`.
Phase 1B adds exactly five files in the predeclared V13 evidence/envelope
locations and modifies no Phase 1A file. All 28 manifest `frozen_artifacts`
were independently hashed from the Phase 1A commit and matched. The four
authority hashes also matched Phase 1A and the Phase 1B envelope:

| Artifact | Recomputed SHA-256 |
| --- | --- |
| manifest | `d34f1bdef448c97fa2fbde768c863039bd310ef74e48512af33120b3c1d04eab` |
| protocol | `37e12ad27925dd63c4e2e6ba6b4c02dec75fa9c6090f208b92f79d14186bfd11` |
| schema catalog | `3f7124eb61bf036645e550354d34e6698f681e8a3a2622453a147057efb6e733` |
| transport source | `cc0c56dbf828491e5c07cb1c12a007ae1dda39354b02384802dabd84407ad4df` |

The authority is non-circular: 1A freezes source/protocol; 1B is a direct
child that adds evidence and an envelope; the execution command would receive
1B dynamically as `EXPECTED_FREEZE_COMMIT`. A pure evaluation of the actual
envelope rejects immediately with `Phase-1B did not authorize timed
execution`. Missing receipts after truncation would independently fail later
gates even if the boolean were altered.

## Persisted raw stream reconstruction

The local raw files and lexical hash index were independently rehashed:

| Path relative to rehearsal root | Bytes | Recomputed SHA-256 | Index/envelope |
| --- | ---: | --- | --- |
| `return-protocol/framed-stdout.bin` | 1,942,116 | `edaafe783c94d5cb9dcef376012bb64960730d1f6a92f493f3f60464be41109d` | match |
| `return-protocol/transport-stderr.bin` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | match |
| `transfer-cleanup.json` | 688 | `5c2e994cd2b8c43d686dcd38286ef6b611d165911f1e1daf1f7ee6966f255708` | match |

The hash index itself is 592 bytes with SHA-256
`52646b7196ce71f08170a9476388c13f920a74b728d2d11aaa61da22706d37a3`;
its paths are unique, strictly lexical, safe, and exactly equal to the three
persisted rehearsal files.

The 46-byte magic is exact. Eight complete frames have consecutive sequences
0 through 7 and valid recomputed payload hashes:

1. `source-admission`;
2. `operator-status`;
3. `archive-build`;
4. `lease-state`;
5. `bulk-declaration`;
6. bulk chunk 0, 524,288 bytes;
7. bulk chunk 1, 524,288 bytes;
8. bulk chunk 2, 524,288 bytes.

The next frame header is complete (`sequence=8`, `chunk_index=3`, declared
payload 524,288 bytes, declared digest
`80fce27c72f7c86119e38c271b8c63a0ba0b5ff07e415018a96cc14283180195`),
but only 359,772 payload bytes are persisted. Their diagnostic partial digest
is `203d9b2650a6ab623663c7c1981f65c98674a0c8486a00d9f9211db46f02c989`.
The partial digest is not a frame-integrity proof. Observed archive payload is
therefore 1,932,636 bytes (three complete chunks plus the partial fourth), and
framing/control overhead is 9,480 bytes.

No integrity or cleanup frame is present. The stream cannot finalize, the
declared archive cannot be materialized or hashed, and extraction is correctly
forbidden.

## Control-plane facts and limits

The complete, digest-checked controls establish only the following:

- source admission reported exact Phase 1A commit/tree and all admitted source
  hashes; those source hashes match the local Phase 1A files;
- the pre-operator classifier reported a complete self-to-PID1 chain, 744
  parsed rows, exact PID/PPID/opaque `comm` semantics, no positive executable
  allowlist, no filesystem identity operation, no argument collection, no
  denied identity conflict, and zero discovered-PID signals;
- the operator reported `rehearse`, `complete`, exit 0, empty stdout/stderr,
  and `benchmark_lease_acquisition_attempted=false`;
- the lease frame is exactly `not-attempted`, with no receipt required or
  available;
- the archive builder reported accepted, exit 0;
- the declaration reports a 16,814,059-byte tar+gzip archive, SHA-256
  `8c2cc3f909447473516153ed86fecb8592bef3ece3087477d713b7281cf19cfe`,
  512 KiB chunks, 33 chunks, and 12 members.

The declared archive is below the 33,554,432-byte cap (cap/declaration ratio
1.9956175959653764). The deterministic 16,777,216-byte representative payload
hash was independently reproduced as
`d90bd85e521c276ce14b448ac05e57b6775fcf9dfcb37d9f90719a3d5b5d1904`;
it is exactly 2.0 times the 8,388,608-byte expected-run bound. The untimed
deterministic archive fixture independently reproduced two byte-identical
16,782,794-byte archives with SHA-256
`9d7ee691c01af8e968ff00d0cb98c51cedd76c8bce205e09ff3cc1cd00927ad8`
and cap ratio 1.9993352715882706. That fixture validates deterministic local
construction, not the truncated remote archive.

The remote declaration and inventory are declarations, not complete-archive
proof. Device, compiler executable, SDK, power, thermal, free-memory,
free-disk, detailed resource receipts, raw process snapshot, runner binary,
timer validation, and archive member contents were inside the unreturned
archive and are independently **unassessed**. The source-admission and
pre-operator classification control objects are available, but their raw
process snapshot is not.

## Refusal and cleanup audit

The explicit deadline states are structurally correct:

- `REQUEST_WRITE` remains governed by request-progress plus the absolute
  bound while response bytes are concurrently persisted;
- half-close starts `SILENT_OPERATOR` for magic, partial/complete controls, and
  a partial declaration;
- only a complete declaration passing frame digest, JSON, basic declaration
  shape, size, compression, chunk shape, and inventory schema/status enters
  `BULK_STREAM`;
- bulk reads renew the bulk-progress deadline;
- complete chunks move to `FOOTERS`, which has its own finite progress bound;
- cleanup must be unique and last for success.

The persisted transfer receipt says `BULK_STREAM` / `bulk-progress`, direct
transport child timed out, cleanup footer false, cleanup state
`unknown-after-truncation`, and zero post-session cleanup operations. That is
consistent with the independently parsed bytes. The retained direct SSH
`Popen` handle and creation identity are the only timeout signal authority.
Static audit found one signal site, `self.process.kill()`, guarded by retained
object identity and used only on timeout; discovered PIDs never enter it.

The correct consequence of truncation is exactly what Phase 2 recorded: do
not reconnect, do not perform a second cleanup, do not claim absence, do not
extract, and do not run the diagnostic. Remote child cleanup/absence remains
unknown. This Phase 3 did not inspect any live process or remote experiment
path and did not signal any process.

## Implementation and safety audit

Untimed local checks independently verified:

- build gate `WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT` is default
  off and isolated;
- compile macro `WEBP_USE_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT` appears
  only in the selected build;
- runtime opt-in `WEBP_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT=1` is exact;
  absent, empty, `0`, `01`, and `true` are false;
- ordinary objects, targets, strings, and public header trees omit V13;
- ordinary and V13 static libraries expose equal public `WebP*` symbol sets;
- baseline/candidate use one binary; the selector is evaluated once before
  mutation; preprocessed V13 contains one baseline DP call, one candidate DP
  call, and one `dp_total` boundary in a closed `if/else` outside the fallback
  chain;
- the selected body records one counter family and the opposite body remains
  zero; reset returns counters to zero; invalid runtime values use baseline;
- the specialized `PushIntervalSpecialized` body is semantically identical to
  its frozen source; no per-pixel timer was added;
- successful setup ends after `CostManagerInit`, steady encloses the initial
  literal and pixel loop, total encloses the selected body including cleanup,
  and traceback/materialization have separate boundaries;
- 16 untimed correctness encodes matched baseline/candidate bitstreams,
  repeated outputs, decoded RGB, and immutable corpus hashes for both cases
  and methods 4/6;
- four case/method counter cells matched bytes/digests and selected-body
  invariants;
- undefined/integer and bounds/pointer-overflow sanitizer builds passed 16
  boundary fixtures with equal baseline/candidate results;
- canonical path/source admission, request framing, three-state lease/mode
  truth tables, malicious archive rejection, all-or-nothing extraction,
  structural deny-only ownership, and identity-only refusal diagnostics passed;
- the frozen plan is exactly photo-large then graphic-large, methods 4 then 6,
  three repetitions with B/C, C/B, B/C order, 24 serial processes, 24 warmups,
  96 retained rows, and 120 runner/stage rows.

No local timer check, performance encode, profile command, CUDA command,
profiler, production command, or remote command was run by Phase 3.

The persisted Phase 1A local summary claims a 4,096-read clock gate, synthetic
timer accounting, and additional streaming fixtures. Their detailed raw
records are not persisted outside the truncated archive, so measured clock
values are not promoted to independently recomputed evidence. Timer boundary
and state-machine semantics were audited statically/purely.

## Discrepancies and evidence limits

1. The protocol says a declaration receives full “inventory validation” before
   `BULK_STREAM`. The online validator checks inventory object schema/status at
   that transition but does not validate its member list/count/types,
   `member_count`, or `inventory_sha256`. Full inventory equality is deferred
   until complete archive inspection. This is an overstatement in the frozen
   prose. It did not authorize extraction or weaken this refusal: the archive
   never completed and final verification could not run.
2. The remote transport source assigns `mode = metadata["mode"]` twice. This
   is redundant and semantically inert.
3. A historical negative such as “no unpersisted command was ever executed”
   cannot be proved from files alone. Persisted evidence contains one rehearsal
   stream, explicitly records rehearsal invocation count 1 and diagnostic count
   0, contains no V13 execution directory or timing rows, and the authorization
   gate rejects production. Phase 3 observed no contradictory evidence.
4. The declared inventory names rehearsal/build/resource artifacts, but no full
   archive hash, content hash cross-check, or safe extraction is available.
   Declaration values are not substituted for returned evidence.
5. Cleanup/absence is unknown by design after transport truncation. No Phase 3
   action attempted to change that state.

## Commands and checks

Sensitive frozen commands and Phase 3 disposition:

```sh
# NOT RUN: frozen rehearsal (Phase 2 already used its sole authority)
env -u WEBP_BENCHMARK_SESSION EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_attribution_v13.py rehearse "$PWD/evidence/backref-cost-attribution-v13-design/rehearsal"

# NOT RUN: production diagnostic
env WEBP_BENCHMARK_SESSION=exclusive EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_attribution_v13.py run "$PWD/evidence/backref-cost-attribution-v13-execution-20260819"
```

Executed validation entry points (all local and untimed):

```sh
python3 scripts/test_backref_cost_attribution_v13_archive.py
python3 scripts/test_backref_cost_attribution_v13_admission.py
python3 scripts/test_backref_cost_attribution_v13_process_ownership.py
python3 -m py_compile scripts/backref_cost_attribution_v13_admission.py scripts/backref_cost_attribution_v13_archive.py scripts/backref_cost_attribution_v13_paths.py scripts/backref_cost_attribution_v13_transport.py scripts/execute_backref_cost_attribution_v13.py scripts/run_backref_cost_attribution_v13_experiment.py scripts/test_backref_cost_attribution_v13_admission.py scripts/test_backref_cost_attribution_v13_archive.py scripts/test_backref_cost_attribution_v13_experiment.py scripts/test_backref_cost_attribution_v13_process_ownership.py scripts/test_backref_cost_attribution_v13_protocol.py scripts/test_backref_cost_attribution_v13_streaming.py
make -B -n -f makefile.unix WEBP_ENABLE_METAL=0 WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT=1 src/enc/backref_cost_attribution_v13_experiment_enc.o
make -B -n -f makefile.unix WEBP_ENABLE_METAL=0 examples/cwebp
```

Additional inline Python audit programs (run as `python3 - <<'PY'`) performed:
raw frame reconstruction; Phase 1A artifact/authority hash recomputation;
pure authority rejection and deterministic deadline-state checks; untimed
CMake baseline/V13 builds, public-symbol/string/guard checks, 16 correctness
encodes, counter checks, and sanitizer boundaries; semantic source/preprocessor
checks; and frozen plan reconstruction. Their exact inputs, outputs, and
results are represented in the machine-readable companion report. Read-only
inspection used `git diff/show/rev-parse/rev-list/merge-base/status/log`, `rg`,
`sed`, `nl`, `jq`, `wc`, `find`, and `shasum` within this worktree only.

There was one invocation of each listed validation command, no validation
retry, no rehearsal retry/rerun, no diagnostic, no lease, no second cleanup,
no tuning, no pooling, no alternate timing, and no production/future run.

## Handoff

The branch is `codex/backref-cost-attribution-v13`. The Phase 3 commit is the
single commit containing this report and
`phase3-evaluation.json`, directly on Phase 1B. Push, PR URL, and hosted check
status are external post-commit facts and are reported in the final handoff;
the report intentionally uses a non-circular self-reference rather than
embedding its own commit hash.
