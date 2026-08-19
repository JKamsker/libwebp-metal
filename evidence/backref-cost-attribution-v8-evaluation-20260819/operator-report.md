# Backref cost attribution V8 — Phase 3 independent consequence report

## Decision and blocker

This cycle is **unassessed**. It neither closes nor reopens the interval
family, selects no new bounded experiment, ranks no next CPU stage, and
authorizes no production change. There are no V8 Phase 2 raw rows, so every
requested median, share, delta, and repeatability result is unassessed. An
empty row set is not a zero-duration or zero-effect result.

The sole exact Phase-1A rehearsal refused before source admission with
`FrameRefusal: relative executable identity is ambiguous`. Phase 1B therefore
records `authorization_status=REFUSED`, `timed_execution_authorized=false`,
and `phase_2_authority=NONE`. Phase 2 independently audited that authority and
correctly ran no diagnostic, created no remote transaction, and produced no
Phase 2 commit. The missing successful rehearsal, source receipt,
representative archive calibration, and authorization are a genuine blocker
that Phase 3 cannot override.

Production disposition is **NO-GO**. V8 remains default-off and
diagnostic-only.

## Ancestry, freeze, and evidence identity

The independently resolved pre-evaluation lineage is exact and linear:

1. frozen main `fea767272f7d9d13e5e5f19cb910e6152418dcdd`, tree
   `d5ba3adc3aa0fab159ea7612c4698375c6847977`;
2. Phase 1A `9ab1014f9a72c4c82e53044a458ac0a1ee1d07c1`, direct parent main,
   tree `43b6cd35383ad6bae86c1b6a57436c0e4814117c`;
3. Phase 1B `8fd0ab2511a84be24fd39926f1dd974ede372e52`, direct parent 1A,
   tree `0775cdde9554753fbf2e29249b9cf1fa186da4a7`.

Phase 1A changed 25 files with 4,744 insertions and 26 deletions. Phase 1B
added exactly five files with 136 insertion lines under the predeclared raw
rehearsal, hash-index, and authorization-envelope paths. It modified no 1A
artifact. There is no Phase 2 commit.

The manifest enumerates 27 frozen artifacts and is separately protected by
the authorization envelope, for 28 immutable identities in total. Every
enumerated digest recomputes exactly at 1B. Core SHA-256 identities are:

- manifest `9ed7d303cbb565c2510dc051818e72d50bd0414452b042df9b17bfb58cde683a`;
- protocol `6c93e6c13ef2ffe476447c97a8bbba05cc6097d048bd7c886a2a61d9ba3bfe13`;
- schema catalog `e5b06a34d6c1e957904ddeb2d83f0794aa6ca3f59a0a87a9dd59baf1a90dc142`;
- transport `c9b15dc9fff6fd01d4a685d1c9fbcaf66ea424c3bed0becd7c17c3b202b021ed`;
- Phase-1B hash index `42837de6289dbaa5d5297cf6222186c66aed08a61a0a323411ddba15e46ded5a`;
- raw framed stdout `c5920e9cee82461135bacc35fd199da22ccca9b98ba3d79c3634972456ee4fdb`.

The Phase-1B envelope does not embed its own commit hash; its identity is the
commit containing the envelope and is supplied dynamically. This Phase 3
evaluation similarly indexes report artifacts without indexing the index
itself, so neither authority plane contains a self-hash cycle.

Before evaluation, complete V8 evidence comprised six files totaling 11,921
bytes: local validation, authorization, the three-file rehearsal hash index,
the raw rehearsal invocation, the 1,877-byte framed stdout, and empty
transport stderr. There is no V8 execution directory, JSONL, runner row,
stage row, correctness receipt from Phase 2, lease receipt, build identity, or
performance sample.

## V8 process-identity fix and ownership

The V8 fix is identity-field based. It executes exactly
`/bin/ps -axo pid=,ppid=,comm=` once per guard, freezes that snapshot, and
parses only PID, PPID, and executable `comm`. It neither requests nor scans
argv, source, command payload, or arbitrary argument text. Conflict
classification uses membership in a frozen set of 34 exact executable
basenames. Prefixes, suffixes, and lookalikes do not match.

The transaction's own self-to-PID-1 chain is independently reconstructed from
PID/PPID edges. Every member must use one of ten exact frozen transport paths;
the allowance applies only to that verified chain and gives no exemption to
unrelated processes. Missing self/parent rows, cycles, duplicates, malformed
fields, invalid UTF-8, noncanonical paths, relative path identities, and
unapproved ancestor executables all fail closed.

Untimed fixtures confirm that hostile ancestor argv/source containing runner,
CUDA, and benchmark strings is harmless when the executable identities are
allowed transport infrastructure. Exact runner, benchmark, CUDA, profiler,
and worker identities conflict even with benign arguments. Prefix/suffix
lookalikes remain allowed unless deliberately enumerated. Malformed and
ambiguous identities refuse.

Static call-graph inspection finds one signal-capable site in all V8
infrastructure: timeout handling on the retained `Popen` object created by the
repository driver, after retained PID and Python object identity validation.
Frozen snapshot PIDs never enter it. Phase 3 did not invoke the synthetic
timeout fixture because this phase forbids signaling any PID. No discovered,
pre-existing, remote, Phase 2, or Phase 3 PID was signaled or stopped.

The live rehearsal reached the identity parser and failed closed on an
ambiguous relative executable identity before classification could be
accepted. That is a safety refusal, not a recurrence of V7's argv substring
false positive. The refusal leaves timing unauthorized.

## Semantics, gates, order, counts, and timers

Source inspection and untimed local tests confirm independent default-off V8
build, compile, and exact-value runtime gates. The candidate activates only
for `WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT=1`; predecessor gates remain
mutually isolated. Ordinary objects, targets, symbols, and strings omit V8,
and public API/ABI surfaces match.

The specialized `PushInterval` body remains semantically identical to frozen
`673bc3fa`. V8 evaluates the selector once before DP mutation, then one closed
baseline/candidate `if/else` invokes exactly one DP body. The predecessor
fallthrough is excluded. Local checks observed only the selected body, equal
bitstreams and decoded pixels, deterministic output, immutable inputs, exact
runtime fallback, and counter reset.

Timer boundaries match the frozen contract: `dp_total` surrounds one selected
DP call through cleanup; setup runs from before allocation through successful
`CostManagerInit`; steady includes only the initial literal and pixel loop;
traceback and chosen-path materialization are separate. No clock exists in
`PushInterval`, insertion, or another per-pixel helper. Darwin uses
`mach_continuous_time` with `mach_timebase_info`.

The frozen diagnostic order is photo-large then graphic-large, method 4 then
method 6, with paired variants baseline/candidate, candidate/baseline,
baseline/candidate. It permits 16 correctness encodes, exactly 24 serial
profile processes, 24 excluded warmups, 96 retained rows, and 120 total runner
and stage rows. Actual Phase 2 counts are zero for every item; no order was
realized and no exclusive lease was attempted.

The Phase 3 local suite passed 16 untimed correctness encodes, four
baseline/candidate counter cells, two sanitizer configurations, 16 boundary
fixtures, default omission, API/ABI equality, and the exact runtime truth
table. The local 4,096-read clock check was monotonic with 14 ns mean and 83 ns
maximum consecutive-read delta. These are invariants, not performance data.

## Source, toolchain, device, resources, lease, and transport

Local Git and manifest checks verify exact Phase-1A source commit/tree and all
frozen source hashes. The live V8 rehearsal, however, failed before remote
source admission. Consequently there is no observed V8 remote source receipt,
toolchain receipt, runner binary identity, device/resource receipt, corpus,
correctness receipt, timer receipt, plan artifact, or lease receipt. The
Apple/Xcode/toolchain/device/resource values in the manifest are frozen
requirements only; Phase 3 does not misrepresent them as live observations.

Read-only decoding of the raw rehearsal stream found exactly six ordered
frames: source admission, operator status, archive build, lease state,
integrity footer, and cleanup footer. Frame framing and payload hashes verify.
The first three controls are unavailable/unavailable/not-attempted; integrity
is `refused` with the exact ambiguous-identity error. There is no bulk
declaration, chunk, archive, or extraction. The representative request carried
the declared 5 MiB deterministic payload, but no representative archive was
constructed, so usable calibration and finite margin are absent.

The cleanup footer is the final frame. It records `status=complete`, removal
of the exact validated V8 child
`/Users/pandocs-agent-001/.libwebp-metal-backref-cost-attribution-v8/run.ev2dl3x3`,
and absence proof after 9,808,014,250 ns. The proof returned in the same one
session, with zero second SSH/SCP cleanup operations. Local archive fixtures
independently pass safe inventory, corruption rejection, all-or-nothing
extraction, and no-partial-extraction behavior; no live archive existed to
extract.

## Raw statistics and consequence

For photo-large/method 4, photo-large/method 6, graphic-large/method 4, and
graphic-large/method 6, both baseline and candidate row counts are zero.
Whole encode, backward references, selected-DP total/setup/steady, traceback,
materialization, histogram, Huffman, bitstream, and downstream values are all
unassessed. Shares, baseline-to-candidate deltas, medians, and repeatability
are also unassessed. No values were fabricated, pooled from earlier cycles, or
treated as zeros.

The final consequence is: **interval family unassessed; no next CPU-stage
ranking; no new bounded experiment; no production promotion**. The genuine
authorization blocker is retained exactly as evidence.

Machine-readable details are in `phase3-audit.json`; untimed command outcomes
are in `phase3-local-validation.json`.
