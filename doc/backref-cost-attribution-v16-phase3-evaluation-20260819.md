# Backref-cost attribution V16 — Phase 3 evaluation and consequence

## Decision and production status

Consequence **(2)** is selected: **retain V16 default-off as frozen forensic
evidence and reject production promotion**. No production file is changed.
V16 remains compile-time default-off and requires the exact private runtime
opt-in value `1` in its diagnostic build. No next experiment is proposed or
executed, and the broader interval family is neither closed nor reopened
because the frozen cross-cell consistency support is absent.

All frozen diagnostic and evidence gates pass. That does not support
production: photo DP medians improve while graphic DP medians regress, and
whole-encode paired directions are inconsistent in three of four cells. The
protocol also expressly forbids promotion from this diagnostic.

The complete machine-readable evaluation, including every process median,
every recorded stage share and delta, all three paired deltas, all 96 frozen
repeatability comparisons, raw identities, gate verdicts, and limitations is
`evidence/backref-cost-attribution-v16-phase3-evaluation-consequence-20260819.json`.

## Independent raw-byte provenance

The evaluator parsed and rehashed retained bytes without importing a Phase 2
summary. It decoded each frame header and payload, reconstructed the tar+gzip
archive from bulk bytes, regenerated both full-inventory digests, compared
every regular tar member byte-for-byte with the extracted evidence, and
verified both exact hash-index memberships.

| Boundary | Raw/result |
|---|---|
| linear commits | main `8ac198e565ab36eedd6e124202b78c09e5180ec1`; 1A `6f0cbbaf8a3ee527526edbd29779bd9f8c7d941c`; 1B `ef24e275a714f76bd78a04363524bc32f2e4076d`; 2 `85817c0f97ea5fe1227d0d04466736f570fba731` |
| Phase 1B outer index | 22/22 files; SHA-256 `5b3ff3ac3a9e8583745b82c16be674dd7f6817aa5029c4bf17832710cb7cd6cc` |
| rehearsal archive | 6,292 bytes; SHA-256 `d007759baf03f900d0dc3ef76277fb8d986802339eda977ac52adf51d2f241fd`; 8 members |
| rehearsal response | 15,629 bytes; SHA-256 `d2552b8004b548064ac52d78c9629c0798c24ff482ad18e7bf63836432608cb7`; eight ordered frames; empty stderr |
| Phase 2 inner index | 85/85 files plus the index; SHA-256 `9c2a1bad74ef66a482c09390ead68fbc13d68de6d4e93de860c1bd3f84a56f77` |
| Phase 2 archive | 30,700 bytes; SHA-256 `c0e5ebb5a54d53f6bff0dfec52284a8413d4e72e578868d63768f3e927531a47`; 88 members |
| Phase 2 inventory | canonical SHA-256 `fc4b74de337a9bb7d7ee2de465e6f011f48da694450de845bbb07fd3a5ab6507`; pretty-byte SHA-256 `15370a4de70dd50649577bcaa6d12f538b509668bd559c49616b8f8615590162` |
| Phase 2 response | 40,238 bytes; SHA-256 `acf0b2847caf46d1ae0a8a8c11708b1e6b5464c992f53081399c5ef7b47f35af`; eight ordered frames; empty stderr |
| Phase 2 returned index | 95/95 files; SHA-256 `e57efc36ef1730b6019d6a16995fc7ca8decaec5ea99055a2fd2d0040a3841fc`; only the index itself and post-index `transfer-cleanup.json` are outside its rows |

Both transactions are strictly below the 786,432-byte archive cap and the
exclusive 1,048,576-byte response cap. Recomputed Phase 2 cap margins are
25.6166775244x and 26.0593468860x. The one reconstructed bulk chunk is exactly
declared. Integrity is penultimate and cleanup/absence is the unique final
frame. Phase 2's lease receipt records attempted/acquired/released all true;
the rehearsal correctly records `not-attempted`. There are zero post-session
remote cleanup operations.

The frozen compact boundary intentionally keeps only digest/count receipts for
the framed request, source bundle, representative request, raw process tables,
build streams, `nm` output, corpus, and correctness products. Those omitted
bytes cannot be rehashed in Phase 3. Every cryptographic hash whose source
bytes are retained was recomputed. No missing timing row is inferred.

## Exact inventory and admission

The raw command, runner, and stage files reconstruct exactly 24 serial directly
spawned processes in frozen case/method/repetition/variant order: 24 excluded
warmups, 96 retained rows, 120 runner rows, and 120 stage rows. All 24 PIDs are
distinct; every runner stderr is empty and independently hash-matched. There is
no retry, rerun, parallel profile, profiler, Metal, CUDA, or local fallback.

The source is exact Phase 1A tree
`633eaa7df1090e9f8f6f2a82df492372a1114a4d`. All 29 admitted source hashes
match current frozen bytes. The Apple M4/Mac16,10 identity, clang 17.0.0,
Xcode 26.3, SDK 26.2, executable hashes, optimized flags, one runner binary,
required symbols, AC power, Low Power Mode off, thermal text, memory, and disk
thresholds all match. Fifty-two retained process-isolation receipts have a
complete PID-1 chain, zero exact conflicts, zero discovered-PID signals, no
argv collection, and no filesystem identity operation.

Correctness evidence covers the exact four cells and 16 encodes: eight
baseline and eight candidate. Each cell records equal baseline/candidate and
repeat bitstreams, exact decoded RGB, unchanged input SHA-256, and the compact
bitstream size/SHA-256. Four direct counter cells add eight untimed encodes;
each has selector count equal to its selected body count, zero opposite-body
count, equal output, and zero counters after reset. Phase 1's indexed local
prerequisites record 16 boundary fixtures, two sanitizer configurations,
public API/ABI equality, default omission, and 36 isolated experiment guards.

Static re-audit confirms the selector is cached once before DP mutation; one
closed `if/else` owns exactly one body; the common predecessor chain is under
the opposite preprocessor branch; setup spans allocation through successful
`CostManagerInit`; steady spans only initial literal and the pixel loop; DP
total includes cleanup; traceback/materialization are separate; and no timer
exists inside the loop, `PushInterval`, or `InsertInterval`. All 120 rows also
pass both frozen timer-nesting inequalities and exact counter/call equality.
The 4,096-read clock record is monotonic with positive deltas and a 38 ns mean,
below the 10,000 ns cap.

## Recomputed statistics

For each process, the evaluator takes the median of its four retained raw
nanosecond rows. A variant/cell value is the median of its three process
medians. Shares divide stage median by whole-encode median. Deltas below are
`candidate / baseline - 1`; negative is faster. This is the only admitted
hierarchy—no rows are pooled and no old sample is used.

| Case/method | Whole B → C (delta) | Backrefs B → C (delta) | DP total B → C (delta) | Setup B → C (delta) | Steady B → C (delta) |
|---|---:|---:|---:|---:|---:|
| photo m4 | 924,799,146 → 919,019,354 (-0.624978%) | 138,562,917 → 138,483,104 (-0.057601%) | 31,299,604 → 30,770,688 (-1.689849%) | 1,248,209 → 1,263,021.5 (+1.186700%) | 30,029,105 → 29,518,166 (-1.701479%) |
| photo m6 | 1,187,896,104.5 → 1,188,604,104 (+0.059601%) | 136,307,792 → 139,546,729 (+2.376194%) | 31,498,042 → 31,036,957.5 (-1.463851%) | 1,274,313 → 1,275,604.5 (+0.101349%) | 30,219,354.5 → 29,765,167 (-1.502969%) |
| graphic m4 | 46,488,604 → 46,883,292 (+0.848999%) | 34,304,750.5 → 34,745,250.5 (+1.284079%) | 21,374,604.5 → 21,819,250 (+2.080251%) | 649,875.5 → 648,187.5 (-0.259742%) | 20,719,999.5 → 21,164,937 (+2.147382%) |
| graphic m6 | 46,398,333.5 → 46,783,520.5 (+0.830174%) | 34,223,791.5 → 34,656,771 (+1.265142%) | 21,314,062.5 → 21,804,167.5 (+2.299444%) | 647,062.5 → 648,417 (+0.209331%) | 20,658,166.5 → 21,150,208 (+2.381826%) |

| Case/method | Traceback delta | Materialize delta | Histogram delta | Huffman delta | Bitstream delta |
|---|---:|---:|---:|---:|---:|
| photo m4 | -2.021029% | +0.399561% | -0.280559% | -0.877712% | +0.922269% |
| photo m6 | +0.802862% | -1.195138% | -0.291970% | -0.691846% | +0.523298% |
| graphic m4 | -13.972190% | -0.583575% | -3.160500% | -3.930994% | +1.834747% |
| graphic m6 | -0.382005% | -0.807539% | -0.443783% | -3.386269% | +7.923306% |

DP-total paired deltas are direction-consistent within each cell: photo m4
`[-0.478808%, -3.995366%, -1.451827%]`, photo m6
`[-0.515614%, -1.186540%, -1.463851%]`, graphic m4
`[+3.293929%, +1.931126%, +1.513801%]`, and graphic m6
`[+3.613344%, +2.067396%, +1.899054%]`. Whole-encode paired deltas are
consistent only for photo m4; the other three cells cross zero.

All eight retained-total max/min comparisons pass; the worst is
1.0325411614 against the 2.0 cap. All 88 required-stage share-range
comparisons pass; the worst is 0.0052003148 absolute against the 0.10 cap.
The full record additionally reports every share/delta for all 21 stage names
present across the photo and graphic pipelines, including preparation,
container, input, predictor/cross-color or palette, hash-chain, finalize, and
RIFF stages.

## Limits and handoff

These are coarse nested timers, not `PushInterval` self time. They cannot
resolve call-stack, code-layout, branch-predictor, or cache causality. The
admitted scope is two 3000x2000 cases, methods 4/6, three process repetitions,
and four retained encodes per process. The frozen uncertainty rule is
descriptive repeatability only; it defines no confidence interval or
significance test. Remote absence is the cleanup-last in-session proof because
the protocol forbids follow-up contact.

There is no blocker. Raw Phase 1/2 evidence bytes are unchanged.
