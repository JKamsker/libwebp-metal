# Phase 2 refusal / frozen-pipeline audit

Outcome: the independent audit passes and authority is absent. Phase 2 is
refused and the pipeline remains fail-closed. No Phase 3 action was started.

## Subject and ancestry

The audited pre-audit HEAD was
`d653a00a642fd1b2707016848a900f94ed51cfcf` (Phase 1B). Its parent is exactly
Phase 1A `e2816e632075779b299adfc2cf8ab7d87d7c0d6f`, whose parent is exactly
baseline `b96909b28b3d64f000d0f98ffa76137305010808`. Both ancestry checks and
the one-parent rule pass. The Phase 1A tree is
`2bda2d64fe60a8ca3d46911135363fcfae394503`; the Phase 1B tree before this
evidence commit is `2afa8006f5b4f670c1bf1273bb5e8e19ea1eb8f0`.

The Phase 1A→1B diff is exactly five additions: the authorization envelope,
rehearsal hash index, two empty return-protocol streams, and
`transfer-cleanup.json`. There are no modifications or deletions. All 65
manifest-frozen artifact hashes match, all 66 admission identity paths exist
and are unique, and the independently recomputed source-map digest is
`ae76c436608f9008573e2724ff4a072c89bfa4bbefe6b1ea791f9e3493e235ba`.

## Frozen identity and gate audit

The frozen manifest, protocol, schema catalog, and transport source hashes
match their Phase 1B envelope:

| Item | SHA-256 |
| --- | --- |
| manifest | `42afa14d09de7d696eacf2a60bf46d0171cf7d0288aec72e35d673b950f9d89c` |
| protocol | `0150581bae129d9c45ad41cb6db8f15c15fffddc5c1e5a5142c912dbf1e077a1` |
| schema catalog | `a18798767a7c7cccc0f782ea4fe055709b14e146393b62bbd022ef702ed457f6` |
| transport source | `fe4884df1a74b0b676fb01dfe7b9cbcf3a9232f5493e731da28d5b5da6dc98ab` |

The deterministic payload recomputation is 2,097,152 bytes with SHA-256
`2e2ea6d7479bc385057e7a55154e220e67d28e7861c8b54fae5ea8549bbca607`.
Manifest, fixture, generator, and the independent recomputation agree. The
toolchain manifest, fixture, and read-only actual identity recomputation agree
at canonical SHA-256
`7a4940524373f4b2e261a9fbb302eabe6136351a0c11b8021d037f0eae4e184b`, with
eight executables, four metadata identities, Xcode 26.3, macOS SDK 26.2, and
no xcrun dependency.

The alignment arithmetic independently matches the frozen codegen receipt:
all six addresses are distinct and zero modulo 16,384; adjacent spacing is
16,384 bytes; each DP-to-Push displacement is 49,152 bytes; body bytes are
5,624; padding is 77,588; and the `__TEXT,__br_align_v2` section is 83,212
bytes with executable pure-instruction flags. B/L canonical instruction
identity and the intended H differences pass. Linker-map hashes are
`f27167b3f8a0fbc1cbd58ea3493e5a21f597666a3b53b2d45f04be5ebd55d55d` and
`2e80a8abcf8f07be42836d3e40965b01040df1296c4534cb3ef498e7b6699305` for the
full map and extract.

The recorded Phase 1 gate set has 42 entries and no failure outcome. The
independent inventory recomputation agrees with 36 profile processes, 36
warmups, 144 retained rows, 180 runner rows, 180 stage rows, 24 correctness
encodes, 12 untimed work rows, and 100,000 bootstrap resamples with seed
`0x424c4801`. The B→L null-control, repeatability, effect-floor, and separate
production thresholds remain exactly frozen; no result was generated or
interpreted.

## Compact control and receipt contract

The exact sorted 66-entry source map recomputes to
`ae76c436608f9008573e2724ff4a072c89bfa4bbefe6b1ea791f9e3493e235ba`.
Independent canonical serialization gives:

- compact source receipt payload: 554 bytes, leaving 7,638 bytes below the
  8,192-byte exclusive control cap;
- encoded source-admission frame: 710 bytes;
- old full-map control payload: 9,285 bytes, overflowing the cap by 1,093
  bytes.

The compact receipt has only fixed identity/status fields plus source-map count
and digest. It has no full map. The complete map is the archived indexed
`source-admission-details.json` member, validated after archive integrity
against both the requested map and compact receipt. The schema, count, digest,
ordering/collision, missing-detail, archive-mismatch, and control/detail
disagreement refusal cases remain frozen.

Transport caps and ordering were audited without opening a remote transaction:
archive ≤786,432 bytes, framed response <1,048,576 bytes, control ≤8,192
bytes, and 262,144-byte chunks, with cleanup footer last. Process discovery is
observe-only (`/bin/ps` with PID/PPID/comm only); only a retained directly
spawned child may be stopped on its own timeout. Remote cleanup is restricted
to the exact canonical cycle child with an absence proof. No generic
termination invocation, prior-cycle path contact, follow-up cleanup, pooling,
or alternate data plane is authorized.

## Refusal evidence and execution record

The Phase 1B hash index contains exactly three files and 699 bytes:

- `framed-stdout.bin`: 0 bytes,
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- `transport-stderr.bin`: 0 bytes, the same empty-file hash;
- `transfer-cleanup.json`: 699 bytes,
  `cfb2305963c78f968d0265ace712b64e71c690ef1dc4d9c92a3773293edbab65`.

The transfer receipt records one directly owned transport child timing out in
`REQUEST_WRITE` under the request-progress deadline. It proves no established
remote connection, has no framed response, and leaves remote cleanup state
unknown after truncation. The authorization envelope records `REFUSED`,
`phase_2_authority=NONE`, one attempt, zero established contacts, zero lease
attempts, zero workloads, zero timing samples, zero retries/reruns, and 20
missing-receipt/exit-code refusal reasons.

For this Phase 2 audit: remote contact attempts 0, remote connections 0,
remote processes 0, leases 0, workloads 0, timing samples 0, retries 0,
reruns 0, code edits 0, and protocol edits 0. The worktree was clean before
the evidence was added; the final evidence commit contains only the two audit
files and will be left clean.

The blocker is the failed sole rehearsal and absent complete receipt set. A
future separately authorized cycle would need a successful complete sole
rehearsal and all frozen receipt gates before any timed transaction; this audit
does not retry or rerun it.
