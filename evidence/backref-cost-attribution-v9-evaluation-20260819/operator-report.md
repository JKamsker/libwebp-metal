# Backref cost attribution V9 — Phase 3 independent refusal evaluation

## Decision

V9 is **unassessed and blocked by an implementation defect**. It is not a
close, reopen, or newly completed experiment. No bounded experiment was
selected, implemented, or run in Phase 3; no CPU stage is ranked; and there is
no production consequence. Production disposition is **NO-GO**.

The sole Phase-1 rehearsal refused before source admission because V9 rejects
a slash-bearing `comm` token. Phase 1B correctly records
`authorization_status=REFUSED`, `timed_execution_authorized=false`, and
`phase_2_authority=NONE`. Phase 2 then failed at that authorization gate before
invoking its frozen command. It started no remote session, created no remote
child, acquired no lease, and executed no encoder, profiler, benchmark, timer,
or CUDA workload.

There are no V9 Phase-2 runner rows, stage rows, timing rows, or performance
samples. Whole encode, backward-reference generation, selected-DP total,
setup, steady, traceback, materialization, histogram, Huffman, bitstream, and
downstream statistics are all N/A. Zero execution counts are not zero-duration
or zero-effect measurements.

## Ancestry, freeze, and evidence identity

The independently resolved pre-evaluation lineage is exact and linear:

1. main parent `2940104e909e41f973aea7f4cc525792ac088ccb`, tree
   `59f6484f1c1d731bbda7855e5faca45b03059e41`;
2. Phase 1A `d88197ad053965628b158421fca3968299a3d94a`, direct parent main,
   tree `b144753c05544c69b84d0cd35485805f6c5f51a0`;
3. Phase 1B `117da2578e5af3daa1328ba52a6847ba30a288ae`, direct parent 1A,
   tree `987c63ffd16bd32a1449f1fd8798f110633277dc`;
4. Phase 2 refusal audit `3952d4811de53872aa9e3c703490bdcf95bc21af`,
   direct parent 1B, tree `57ead6c16bae6049ccacd81ba7dd2cbb0b4e97fb`.

Phase 1A changed 25 files with 4,866 insertions and 28 deletions. Phase 1B
added exactly five predeclared authorization/rehearsal evidence files with 136
insertion lines and modified no frozen artifact. Phase 2 added exactly two
refusal-audit files with 203 insertion lines and modified neither Phase-1A nor
Phase-1B evidence.

The manifest enumerates 27 frozen artifacts and is separately protected by the
Phase-1B envelope, yielding 28 immutable identities. All 28 are byte-identical
at Phase 1A, Phase 1B, and Phase 2, and all declared SHA-256 values recompute.
Core identities are:

- manifest `a0b50086949cbd49e83d1f2a4a0877ce451ee1d1a2b5db7c767b30ffbc988ad2`;
- protocol `2848ff0a7b9dbe00fdad298275792be84a9ae200d1fcf8e22a9672d2074c1fd4`;
- schema catalog `51868efc35c53797232b25afb3890dbcc2103e6d3ca9690dccf68b0e6804dc31`;
- transport `5d9fd085400c4b50b1bb447d96565c802eb5c6c2f1606b84eb9f11382d50657b`;
- Phase-1B authorization `8290002b1ce3bd5293c6e7abac9fefa3e3c5a399ab6d8ccf1a41ba83a5c576c7`;
- raw framed stdout `79c114f954a2cd3cf478bf372590b33188f2de3590e5dc050249f8b581c7f0f3`.

Before this evaluation, V9 evidence contained eight files totaling 21,480
bytes: six Phase-1 design/rehearsal files and two Phase-2 refusal files. No
JSONL, execution archive, workload receipt, build identity, correctness receipt
from Phase 2, lease receipt, or performance sample exists.

## Exact process-identity defect

V9 executes `/bin/ps -axo pid=,ppid=,comm=` and freezes only PID, PPID, and
`comm`. It does not request argv. Its own manifest and source describe `comm`
as an exact opaque executable-name identity that is never interpreted as a
filesystem path. Nevertheless, `parse_process_snapshot()` rejects every
`comm` containing `/` with `FrameRefusal: comm is not an opaque
executable-name token` before classification.

That rejection is overrestrictive. Slash presence in this opaque process-table
field does not by itself make the identity a path or make it ambiguous. V9
already has a separate path-evidence type: an optional independently acquired,
read-only, absolute, canonical, provenanced executable path. A `comm` token and
a separately resolved path therefore must not be conflated.

The frozen deny semantics are otherwise exact: 35 denied `comm` tokens match
by exact membership, and a separately verified path may match by its exact
basename. Prefixes, suffixes, substrings, argv, embedded source, and request
payload text do not match. Hostile argv or source text cannot justify the live
refusal because argv was not collected and the classifier consumes only the
frozen identity fields plus optional resolved-path records.

The local fixture set did not catch this defect. It validates slashless V8-live
shape identities, while explicitly placing `relative/python3` in the malformed
set. Thus it encodes the overrestriction instead of testing that a
slash-bearing `comm` remains an opaque exact token.

Static ownership inspection finds no route from a PID discovered in the
snapshot to any signal API. The sole signal-capable site in V9 infrastructure
is timeout handling on the retained directly owned `Popen` object, guarded by
its creation identity. Phase 3 invoked no timeout fixture and sent no signal.

## Authorization, refusal transport, and cleanup

The one allowed rehearsal used one noninteractive remote session, with zero
retry and zero rerun. Read-only parsing of its raw 1,879-byte stdout found six
ordered frames: source admission, operator status, archive build, lease state,
integrity footer, and cleanup footer. Sequence and payload hashes recompute.
Transport stderr is empty.

Source admission and operator status are `unavailable`; archive build is
`not-attempted`; integrity is `refused` with the exact `comm` error. Lease
attempt state is unknown (`null`) because the operator was never invoked; no
lease was verified or acquired. There is no bulk declaration, chunk, archive,
or extraction.

The representative 5 MiB request was framed, but refusal occurred before
archive construction. Returned archive bytes and chunks are zero, finite
margin is zero, and usable archive calibration is incomplete. No throughput or
capacity conclusion follows.

The cleanup footer is the final frame. It records `status=complete`, removal
of the exact validated V9 child, and an absence proof after 9,976,613,167 ns.
That cleanup completed in the same session. There was no second SSH/SCP cleanup
and no later remote-path inspection or cleanup.

Phase 2 independently respected the refusal. Its first failed gate was
`phase1b-authorization.timed_execution_authorized`; the exact frozen Phase-2
command was not invoked. Phase 2 therefore performed no process discovery,
remote cleanup, or absence claim of its own.

## Frozen implementation and validation scope

Source review confirms V9 remains behind default-off build and compile gates
and an exact-value runtime gate. The CMake option is `OFF`, the make variable
defaults to `0`, overlapping predecessor experiments are rejected, and the
runtime selector is true only when
`WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT` equals `1`. Other values fall
back to the baseline path. V9 adds private internal surfaces only; the frozen
Phase-1 evidence reports ordinary target/string omission and public API/ABI
equality.

The frozen validation scope reports 16 local correctness encodes, 16 boundary
fixtures, four counter cells, two sanitizer configurations, and a 4,096-read
clock check. It reports bitstream/pixel/input correctness, deterministic
fallback, and counter reset. These are Phase-1 local validation facts, not
Phase-2 workload statistics, and Phase 3 did not rerun them.

Source structure preserves one cached selector evaluation before DP mutation,
one closed baseline/candidate `if/else`, exactly one selected DP body, and no
opposite-body overwrite. The baseline and specialized bodies use the frozen
DP include; setup, steady, total, traceback, and materialization boundaries and
counter equality requirements remain the frozen validation contract. No clock
is placed in `PushInterval` or another per-pixel helper. None of these facts
creates performance evidence without a Phase-2 workload.

The frozen order was photo-large then graphic-large, method 4 then method 6,
with variant pairs baseline/candidate, candidate/baseline,
baseline/candidate. The planned counts were 16 correctness encodes, 24 serial
profile processes, 24 excluded warmups, 96 retained rows, and 120 total runner
and stage rows under one exclusive lease. Actual Phase-2 counts are zero for
every item, and no order was realized.

## Source, toolchain, device, and resources

Local Git and hash checks verify exact Phase-1A source commit/tree and all
frozen source identities. The rehearsal failed before remote source admission,
so there is no live V9 source receipt, toolchain receipt, runner binary
identity, device/resource receipt, corpus, correctness receipt, timer receipt,
command-plan artifact, or lease receipt.

The manifest declares Darwin arm64, Mac16,10, Apple M4, 24 GiB physical
memory, Apple clang 17.0.0, target arm64 Darwin 25.2.0, SDK 26.2, and the frozen
Xcode developer directory, plus memory/disk/resource thresholds. These are
frozen requirements, not live observations from the refused V9 rehearsal or
Phase 2.

Artifact ownership remains separated: Phase 1 owns the design freeze,
rehearsal, and refusal envelope; Phase 2 owns its additions-only refusal audit;
Phase 3 adds only this independent evaluation. Phase 3 contacted no remote or
source task, delegated no work, and changed no production file.

## Statistics, consequence, and V10 recommendation

For photo-large/method 4, photo-large/method 6, graphic-large/method 4, and
graphic-large/method 6, baseline and candidate row counts are both zero.
Medians, shares, deltas, and repeatability are N/A. No older rows were pooled,
relabelled, or recomputed. With no workload, no CPU stage can be ranked.

The final consequence is **unassessed/blocked due to the process-identity
implementation defect; no production consequence**.

The only recommendation is a high-level V10 gate correction: treat `comm` as
an opaque exact token even when it contains `/`; use a canonical absolute
resolved executable path only when that separate identity is independently
acquired and required; and retain scoped fail-closed handling for malformed
snapshots, incomplete/cyclic ancestry, exact denied identities, and missing or
malformed required path evidence. This V9 cycle neither implements that change
nor proposes a future execution or run.

Machine-readable findings are in `phase3-audit.json`; the exact local report
checks are in `phase3-local-validation.json`.
