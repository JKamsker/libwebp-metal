# Backref cost specialization alignment V3 — Phase 3 evaluation and consequence

## Decision

Phase 3 refuses any performance or causal conclusion. Phase 2 independently
resolved authority to `NONE` and completed `FAIL_CLOSED_REFUSAL_NO_HOST_CONTACT`.
It created zero SSH processes, attempted zero leases, ran zero timed processes,
and produced zero timing, correctness, work, runner, or stage rows. Therefore the
mandatory B→L null-control gate is **not evaluable/refused**, not passed or
failed. L→H and B→H interpretation is prohibited. No estimate, confidence
interval, repeatability ratio, stage-share result, production regression, or
causal claim exists; no prior sample was loaded, imputed, or pooled.

The production consequence is to retain Alignment V3 default-off and make no
production change. The research consequence is to retain the default-off code
and the successful request-channel evidence, but reject any performance claim.
The one next credible lead is a fresh independently gated handoff that proves
the three missing timing prerequisites—correctness before timing, coarse timer
record accounting, and serial direct ownership of timed children—before the
exact one-session timed command is reconsidered. Phase 3 does not run that lead.

## Exact lineage and immutable boundary

The independently resolved first-parent chain is exact:

| Phase | Commit | Tree | Exact parent |
| --- | --- | --- | --- |
| base | `c208d6ed33b0ee5e84ba02e78696879266658e7e` | `91681edbfd646c13ec1a5e9d5f47d6e56d913349` | — |
| 1A | `f6735570eb2a81faa60544b289fb0207b8cde873` | `3f40974572234b4a08da1bbb426b52c3ab6fb216` | base |
| 1B | `3b28d9066d94d9397b2b36a09540547adee9efa5` | `9c081d6b080cfe649b95d8f966192687c353b023` | Phase 1A |
| 2 | `0dcd926216af945a1688d73103b35b329b1b2c55` | `ed63a24f34db726f83be13eae9551b23737da5e2` | Phase 1B |

Phase 1B contains exactly 30 additions and no modification or deletion. Phase
2 contains exactly two additions—the read-only auditor and its JSON result—and
no other change. Phase 3 adds only this report and its machine-readable peer.
The working tree began clean. Frozen protocol, implementation, manifest,
thresholds, and Phase 1/2 evidence were not modified.

Core SHA-256 values independently rehashed from the Phase 2 tree are:

| Artifact | SHA-256 |
| --- | --- |
| V3 protocol | `a12f023f692d317cf1f969570967d77c2307b70b33e7b31f3feea4df0f853179` |
| manifest | `80676d5adabdd3cb9e7df1b559f17d61c94f7fcfe2a3bd78698316d4257acdea` |
| schema catalog | `6ae1d89c572a950bb96a9ee785df8be501a0223ae7e79b4fab735305b0ffd4e5` |
| transport | `1fc788fdc814b46128ddcdd98c22906f902e101b547478f309999d2d1604daad` |
| Phase 1B authorization | `155d3d71aae73a27b67a8c853d3840f1a5fffddc0e99ff5839df73f30bcbf142` |
| Phase 1B raw index | `e249dd079ec95aba2e0b19e59e7df1098b64316ac1ae1c3cd3422a2a912ba1a5` |
| Phase 2 audit | `c3c5bccce947c4ba621bbb642f3aafe0504cae94bdfd4052877c1294c0794195` |

The JSON peer records a 15-artifact immutable hash matrix with byte counts.

## Raw request, response, admission, archive, and cleanup

Independent raw-channel replay passes. The channel is 207,175 bytes at
SHA-256 `c99e0f1…c02e`, stderr is empty, and all 360 sequence numbers from 0
through 359 are contiguous. Frame inventory is one READY, 355 request ACKs
(one declaration acceptance plus 354 fixed chunks), one request completion,
one response declaration, one response chunk, and one response completion.
READY authenticates remote process PID 33772 before bulk transfer.

The exact request is 23,193,668 bytes at SHA-256 `3fbc67b8…1e7e`, written and
acknowledged in 354 chunks of at most 65,536 bytes. The complete request wire is
23,256,455 bytes at SHA-256 `048e5ee1…488d`. Replay reconstructs the one
18,697-byte response chunk at SHA-256 `0ddf376e…db90`, exactly equal to the
persisted response.

The eight response frames are ordered source admission, operator status,
archive build, lease state, bulk declaration, bulk chunk, integrity footer,
cleanup footer. The 14,363-byte archive at SHA-256 `2543b175…bb1` inspects and
extracts successfully with 11 members and 10 indexed artifacts. The compact
receipt, archived detail, and independently reconstructed requested map all
agree on source commit Phase 1A, tree `3f409745…6b216`, 66 sorted paths, map
SHA-256 `3f67633b…0d88`, and bundle SHA-256 `65fb1980…a5d8`.

Integrity is complete. Cleanup validates and removes only the exact transaction
child, and the footer proves absence. No prior-cycle path was contacted; no
discovered PID was signaled; no setting changed. The rehearsal used one remote
contact and zero retries, workloads, samples, profiler invocations, or leases.
Phase 2 and Phase 3 made zero host contacts.

Frozen caps remain unchanged: control payload 8,192 bytes, request 33,554,432
bytes, archive 786,432 bytes, response less than 1,048,576 bytes, request chunks
65,536 bytes, and response chunks 262,144 bytes. The frozen exact worst-case
request is 31,553,162 bytes with 2,001,270 bytes margin. The compact source
receipt is 554 payload bytes / 710 encoded bytes with 7,638 bytes payload
margin; the V1 full-map payload is 9,309 bytes, 1,117 bytes over the cap.

## Identities, resources, safety, and local validation

Payload generation, fixture, and manifest agree at 2,097,152 bytes and SHA-256
`25309a36…6845`; stale predecessor identities are rejected. Toolchain manifest,
fixture, and actual identity agree for eight executables and four metadata
files: Xcode 26.3, macOS SDK 26.2, no xcrun dependency. The admitted device is
Apple M4 / Mac16,10 with 25,769,803,776 physical bytes, 10,820,812,800 available
memory bytes, and 18,964,152,320 available disk bytes, on AC power with low
power mode off. Process admission observed 748 rows, found no exact identity
conflict, and signaled none. Lease state is `not-attempted`.

Fresh Phase 3 local non-timing validation passes Python compilation, payload,
toolchain, process ownership, archive, streaming/backpressure, admission,
protocol, all 43 experiment guards, and the experiment correctness/codegen
test. It performs 3 local semantic encodes plus 36 sanitizer boundary encodes
across two configurations. Bitstreams, decoded output, fallback, determinism,
immutability, public ABI, default omission, selector isolation, and B/L work
identity pass; H alone records append-hint work. These are local non-timing
checks and do not replace the missing Phase 2 prerequisites or samples.

All six private B/L/H PushInterval and DP addresses are distinct, zero modulo
16,384, and spaced 16,384 bytes apart. Each DP is 49,152 bytes from its
corresponding Push body. `__TEXT,__br_align_v3` is executable pure instructions,
83,212 bytes total: 5,624 body bytes and 77,588 padding bytes. B/L canonical
instructions match; H is distinct only at the frozen append-hint boundary. The
remote rehearsal timed runner is recorder-free, 687,448 bytes at SHA-256
`992ec45a…9f97`.

## Statistical adjudication and blockers

The frozen plan remains 36 profile processes, 36 excluded warmups, 144 retained
rows, 180 runner rows, 180 stage rows, 24 correctness encodes, 12 work rows, and
100,000 deterministic bootstrap resamples with seed `0x424c4801`. Actual Phase
2 counts are zero for every item.

B→L must pass first in every cell and metric: absolute mean ≤0.75%, 95% CI
contains zero, endpoints within ±1.50%, and every pair within ±3.00%. With zero
rows, none can be computed. L→H and B→H are therefore forbidden. The 0.10%
effect floor, repeatability ratio ≤2.0, stage-share range <0.10, and historical
production regression bound +0.50% remain frozen and unevaluated.

The exact authority blockers are:

1. The mandatory 24 correctness encodes before timing were not run in the
   zero-workload rehearsal.
2. Coarse timer record accounting was not run in the rehearsal.
3. Serial and direct ownership of timed children was not proven because the
   rehearsal had no timed children.

## Delivery state and evidence

The local branch has no configured upstream. Phase 3 did not create or query a
PR, CI, or remote branch and did not merge anything; those delivery states are
therefore not yet known from Phase 3 evidence.

Primary frozen evidence is under
`evidence/backref-cost-specialization-alignment-v3-design/`: `phase1b-authorization.json`,
`phase1b-rehearsal-hashes.json`, `phase2-audit.json`, and `rehearsal/`. The JSON
peer to this report contains exact paths, counts, identities, hashes, authority,
blockers, statistical nulls, consequence, and the sole next lead.
