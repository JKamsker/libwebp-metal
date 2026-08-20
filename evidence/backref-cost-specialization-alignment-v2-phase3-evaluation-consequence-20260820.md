# Backref cost specialization alignment V2 — Phase 3 evaluation and consequence

## Decision

Phase 3 refuses an experimental or production conclusion. Phase 2 authority is
`NONE`, the sole rehearsal timed out in `REQUEST_WRITE`, no remote connection
was established, no timed workload ran, and no Alignment V2 timing row exists.
The mandatory B→L null-control gate is therefore **not evaluable/refused**. It
is not a pass or a fail. There is no effect estimate, no bootstrap interval, no
L→H or B→H interpretation, no causal claim, and no imputation or pooling.

The consequence is to retain the feature default-off and make no production
change. The only next lead is a separately authorized fresh future cycle that
investigates SSH/request-channel reachability under fresh gates. It must not
change the frozen protocol, transport caps, statistical thresholds, or reuse
samples. This evaluation does not run that experiment.

## Immutable lineage and boundaries

The independently resolved first-parent chain is exact:

| Phase | Commit | Tree | Exact parent |
| --- | --- | --- | --- |
| baseline | `b96909b28b3d64f000d0f98ffa76137305010808` | `cab7f4e8d03d59fcae3c0ae89ef5033931955d56` | — |
| 1A | `e2816e632075779b299adfc2cf8ab7d87d7c0d6f` | `2bda2d64fe60a8ca3d46911135363fcfae394503` | baseline |
| 1B | `d653a00a642fd1b2707016848a900f94ed51cfcf` | `2afa8006f5b4f670c1bf1273bb5e8e19ea1eb8f0` | Phase 1A |
| 2 | `9c1d562db0e7fc79829a920762e81e16a5c80de8` | `11228053812f02f98411c91c59fa22d7c9c3ef17` | Phase 1B |

Phase 1A→1B contains exactly five additions and no modification or deletion:
the authorization envelope, raw hash index, two empty transport streams, and
the 699-byte transfer-cleanup receipt. Phase 2 contains exactly two additions
and no other change. Phase 3 adds only this report and its JSON peer.

All 65 manifest-frozen artifacts exist and match their SHA-256; all 66
admission identity paths are unique and obey the exact self-manifest-plus-frozen
artifact rule. Their sorted source-map commitment has 66 rows and SHA-256
`ae76c436608f9008573e2724ff4a072c89bfa4bbefe6b1ea791f9e3493e235ba`.

The core immutable hashes are:

| Evidence | SHA-256 |
| --- | --- |
| protocol | `0150581bae129d9c45ad41cb6db8f15c15fffddc5c1e5a5142c912dbf1e077a1` |
| manifest | `42afa14d09de7d696eacf2a60bf46d0171cf7d0288aec72e35d673b950f9d89c` |
| schema catalog | `a18798767a7c7cccc0f782ea4fe055709b14e146393b62bbd022ef702ed457f6` |
| transport source | `fe4884df1a74b0b676fb01dfe7b9cbcf3a9232f5493e731da28d5b5da6dc98ab` |
| Phase 1 validation | `dbb5bd2e96eb4493c837938ec3587927a1741311e3e6fb0abed72d2e4d8fb6fb` |
| Phase 1 codegen | `8fea9afc0bf61f83c168db0991a6e0662b400a6fe640fd94232bd4107a171993` |
| Phase 1B authorization | `b613a867c4c6e75be4676577e2041efdcdf16bc994bdcf1c15dd2727b61281a3` |
| Phase 1B raw index | `30cd9be45e89f062e98b21f05966aa84f37db6c9ca40bb3dc91cfaeae924a0cf` |
| Phase 2 audit JSON | `ab2d6f5ded26e99be59d694f5b0e9c55c3c2e145a3486d501bd202ed98d5d512` |
| Phase 2 audit Markdown | `f39ce263f58d5e407a2fc36c1ca9b6cade33a267db79fb275ce4524635188f28` |

The machine-readable peer contains the complete 15-path hash matrix.

## Frozen identities, compact control, and transport

The payload independently recomputes to 2,097,152 bytes and SHA-256
`2e2ea6d7479bc385057e7a55154e220e67d28e7861c8b54fae5ea8549bbca607`;
manifest, generator, fixture, and agreement match, while stale Alignment V1,
V2, V3, and V4 identities are rejected. The local read-only toolchain identity
matches eight executable and four metadata rows at canonical SHA-256
`7a4940524373f4b2e261a9fbb302eabe6136351a0c11b8021d037f0eae4e184b`
(Xcode 26.3, macOS SDK 26.2, no xcrun). This is local identity evidence, not a
remote device receipt.

The compact source receipt and archived full-detail contract commit to the
same exact sorted 66-row map and digest. Local canonical reconstruction proves
the compact count/digest and full-detail count/digest/map equal the requested
map. No remote compact receipt or full detail exists. Exact size proof using
the frozen serializer is:

- compact control payload: 554 bytes;
- compact encoded frame: 710 bytes;
- exclusive control cap: 8,192 bytes;
- compact margin: 7,638 bytes;
- Alignment V1 full-map control: 9,285 bytes, 1,093 bytes over the cap.

Frozen transport remains request ≤67,108,864 bytes, archive ≤786,432 bytes,
framed response <1,048,576 bytes, control ≤8,192 bytes, and chunks of 262,144
bytes. Fresh local fixtures pass at 7,903 archive bytes (SHA-256
`818eb8d8d7dbd45ac64acc25058dfa6488aef5a9e2c78f0b0c46aac4fb24161f`)
and at 528,384 archive / 531,414 framed-response bytes. Frame order, integrity,
extraction, cleanup-last, refusal handling, request/response direction, and
retained-child-only timeout behavior pass locally. There is no remote cap,
archive, extraction, integrity, or cleanup receipt.

## Raw inventory and absent data

The Phase 1B raw index is exact, sorted, and has no mismatch: three files,
699 bytes total. `framed-stdout.bin` and `transport-stderr.bin` are both empty
and have SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
`transfer-cleanup.json` is 699 bytes with SHA-256
`cfb2305963c78f968d0265ace712b64e71c690ef1dc4d9c92a3773293edbab65`.
Observed response frames: 0.

The one rehearsal attempt timed out under the request-progress deadline in
`REQUEST_WRITE`. It established 0 remote contacts, attempted 0 leases, ran 0
encoder/timed/profiler workloads, generated 0 samples, and made 0 retries or
reruns. Remote cleanup is unknown after truncation. Nineteen required receipts
are absent; together with exit status 1 these produce 20 refusal reasons.

Alignment V2 has 0 execution directories, remote/device/resource/process/lease
receipts, archives, archive-build receipts, integrity or cleanup footers,
extracted artifacts, correctness rows, work rows, runner rows, stage rows,
retained timing rows, or exact B/L/H triples. The V4 indexes independently
rehash cleanly at 123 and 133 sorted unique rows, but 0 V4 rows are eligible,
loaded, reused, or pooled for Alignment V2 statistics.

## Correctness, work, ABI, and code generation

Fresh Phase 3 local non-timing validation passes Python compilation, payload,
toolchain, process ownership, archive, streaming, admission, protocol, all 42
experiment guards, and the untimed correctness/sanitizer/ABI/codegen test. The
latter runs 3 local variant correctness encodes and 36 sanitizer boundary
encodes across two sanitizer configurations. B/L/H bitstreams match, the
runtime fallback truth table passes, public API symbols are equal, the ordinary
build omits the experiment, the timed build is recorder-free, and B/L common
work matches with H-only hint activity.

All six private symbols are distinct, ordered as Push B/L/H then DP B/L/H,
zero modulo 16,384, and spaced 16,384 bytes apart. Each DP is 49,152 bytes from
its corresponding Push body. The `__TEXT,__br_align_v2` section is 83,212
bytes: 5,624 body bytes and 77,588 padding bytes, with executable
pure-instruction flags. B/L Push and DP canonical instructions are equal; H is
distinct. Full linker map SHA-256 is
`f27167b3f8a0fbc1cbd58ea3493e5a21f597666a3b53b2d45f04be5ebd55d55d`;
extract SHA-256 is
`2e80a8abcf8f07be42836d3e40965b01040df1296c4534cb3ef498e7b6699305`.

The fresh temporary runner is 681,672 bytes at SHA-256
`cf929de3828949fe99c23b70e5948945ce2313f2dc80aef663b2cb59371f8253`,
not the Phase 1 reference binary's 676,520 bytes / `b8d9deb7…`. This is
non-gating build-root-dependent debug-path variance explicitly anticipated by
the manifest. The frozen symbol codegen, addresses, section, and linker-map
facts match exactly. Remote codegen remains absent.

`git diff --check` reports only four preserved trailing spaces in raw linker-map
literal rows (two in each committed map). These are recorded raw formatting,
not source edits.

## Statistical adjudication

The frozen planned inventory remains 36 profile processes, 36 warmups, 144
retained rows, 180 runner rows, 180 stage rows, 24 correctness encodes, 12
untimed work rows, and 12 paired rows per cell/metric. The bootstrap remains
100,000 resamples from seed `0x424c4801`.

B→L must be applied first in all four cells for DP total, DP steady, and whole
encode: absolute mean ≤0.75%, interval contains zero, endpoints within ±1.50%,
and every paired row within ±3.00%. With zero rows, that gate is not evaluable
and is refused—not passed. Consequently L→H and B→H are forbidden from
interpretation. The 0.10% effect floor, repeatability ratio ≤2.0, stage-share
range <0.10, and historical production paired-regression bound +0.50% remain
unchanged and unevaluated. There is no effect estimate or causal result.

## Delivery boundary

Only the human- and machine-readable Phase 3 consequence artifacts are added.
No prior artifact, source, protocol, cap, threshold, or production path is
changed. PR and CI delivery status are reported from the hosting service in the
final handoff because they occur after this commit is created.
