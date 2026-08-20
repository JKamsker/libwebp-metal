# Backref Cost Specialization Alignment V4 Phase 3 Consequence

Phase 3 independently accepts the Phase 2 run as complete raw timing evidence, but the mandatory B-to-L null control fails. The causal diagnostic is invalid, L-to-H and B-to-H are not interpreted, the 0.10% effect floor and historical production gate are not applied to H, and no production change is authorized. The V4 candidate is rejected for production and retained only as diagnostic evidence.

## Independent evidence audit

The exact linear ancestry is `91ab79b70bb1f99888dce63e8b1ac512741bafb3` → `f1e1b1afd4c12921b326276ae7f07f4d27137548` → `22eaed7f89e12fc3a4510f75f570ca5edffe5ea2` → `7f3bb9a4d05c786aac8cf4176268582123365959`. Phase 1B has 29 added files and no modified/deleted files; Phase 2 has 155 added files and no modified/deleted files. Phase 1A's tree is exactly `4ec54223425a9ae3c08f720181bc34162e3db1bb`.

The Phase 1B 27-file rehearsal index, Phase 2 136-file operator index, and Phase 2 152-file returned-evidence index independently reproduce every declared size and SHA-256. The frozen manifest, protocol, schema catalog, and transport hashes are respectively `5297e3da7b771ca1d5abf4695dc46e381a4660aae758bc7964cd67ac64fb6b13`, `35e656d9281b25fc5111521a6777197f155f12c1f7cd610e49962df8f6588cc5`, `beef76ba2f8cad02ab825e213a549f4610e7cf50808a69238c2edb618b6d130f`, and `e2bdd726ac1c546ef57658d1ef9bcc07a7e17bd0a2628f07900c162fafeb5db8`.

The authority was `ALIGNMENT_V4_CONDITIONAL_DIAGNOSTIC_AUTHORITY`: one pipeline was permitted, but no performance row was admissible before the three in-pipeline gates passed. Gate A passed 24 correctness encodes. Gate B passed one 4,096-read monotonic-clock child and three separated timer-accounting rows, with one selected DP body, exact reset/call/nesting invariants, and zero per-pixel clock calls. Gate C passed all 76 receipts: ordinals 0–75 are contiguous; PID, creation identity, and start token are unique; every observed parent is the one operator; every child is shell/wrapper/grandchild-free, non-overlapping, exited and reaped before its successor; maximum live ownership is one; and all child stderr is empty.

The run contains 12 work rows, 36 profile processes, 36 excluded warmups, 144 retained rows, 180 runner rows, and 180 stage rows. All 180 stage rows pass the frozen call and nesting accounting. The single SSH transaction acknowledged 21,300,655 request bytes in 326/326 chunks, returned a 61,518-byte archive and 66,074-byte framed response, and had zero transport stderr. The exclusive lease was acquired and released; indexed extraction, exact-child cleanup, and exact-child absence passed; no retry, rerun, external profiler, CUDA, discovered-PID signal, prior-cycle contact, or post-run remote cleanup occurred.

Remote identity is Mac16,10 / Apple M4 under Xcode 26.3, Apple clang 17.0.0, and macOS SDK 26.2, with no `xcrun`. AC power, low-power mode off, no thermal warning, memory/disk margins, unchanged settings, observe-only process discovery, source admission, and the 66-path map all pass. Independent local V4 validation passes ABI equality, default omission, 44-way guard isolation, CMake/Unix make integration, correctness/fallback/determinism/immutability, sanitizer boundaries, timer/ownership refusal fixtures, and transport/archive/security fixtures.

The candidate identity also passes: six distinct entries are all 16-KiB aligned in executable pure-instruction `__TEXT,__br_align_v4`; section/body/padding sizes are 83,212/5,624/77,588 bytes, each corresponding entry is spaced by 16,384 bytes, and DP-to-Push displacement is 49,152 bytes. B/L canonical instructions and work are equal, H differs only at the frozen hint boundary, and the timed binary is recorder-free.

## Frozen statistics and null consequence

All 36 frozen statistics were recomputed from the 144 retained rows: four cells × three metrics × B→L/L→H/B→H, 12 pairs each, with 100,000 paired bootstrap resamples and the frozen `0x424c4801` seed derivation. This is 432 paired percentages and 3,600,000 bootstrap draws. No prior samples were loaded or pooled. All 12 repetition ratios pass (maximum `1.013790336740853` ≤ `2.0`) and all 132 required stage-share ranges pass (maximum `0.0081188998953923` < `0.10`).

Eleven of the twelve mandatory B→L domains pass all four bounds. Graphic method 4 whole encode fails only the requirement that the 95% interval contain zero:

- mean: `-0.6199563389094708%` (passes `|mean| ≤ 0.75%`)
- 95% paired-bootstrap interval: `[-1.0795343104954225%, -0.21412171812593112%]` (endpoints pass ±1.50%, but zero is excluded)
- paired range: `[-2.5938194656142124%, +0.6932719761235405%]` (passes ±3.00%)

Because one required domain fails, the entire B→L gate fails. The pre-frozen consequence is fail-closed: L→H and B→H remain uninterpreted, the effect floor cannot rescue a claim, the historical +0.50% production-review gate is not evaluated, and production promotion is false.

Machine-readable full statistics are in `evidence/backref-cost-specialization-alignment-v4-design/phase3-evaluation.json`; the independent audit summary is in `evidence/backref-cost-specialization-alignment-v4-design/phase3-audit.json`.

## Consequence and next lead

Reject the V4 production change and retain this cycle only as evidence that the runtime admission model works while the scientific null remains invalid.

Exactly one next lead is proposed and not run: a fresh independently gated whole-encode stage-attribution null cycle should localize the graphic-m4 B/L drift before H is reconsidered, without reusing any V4 sample.
