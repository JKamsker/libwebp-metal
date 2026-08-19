# CUDA acceleration audit remediation — 2026-08-19

This records the disposition of every item in `cuda_accel_audit_bundle(1)`
against the current `codex/cuda-encoder-acceleration` branch. The audit was a
few commits behind the reviewed tree: a public-encoder decimate trellis test
already existed by the time remediation began, but its narrower coverage and
lack of CTest registration meant the substance of B-03 still applied. All
other confirmed defects remained applicable.

## Confirmed defects

| ID | Disposition | Remediation |
|---|---|---|
| C-01 | Fixed | Decimate parses and validates `WEBP_CUDA_DEVICE` and retains the selected device in its resource state. |
| C-02 | Fixed | Every decimate entry path selects the retained device while holding the decimate mutex, before touching its streams, events, allocations, or tables. Concurrent public encodes are covered by `cuda_concurrency_test`. |
| C-03 | Fixed | Decimate booleans now recognize `0`, `false`, and `no` case-insensitively, matching the main CUDA backend. |
| C-04 | Fixed | Central validation enforces exact macroblock geometry, source/reconstruction strides, phases, band controls, segment IDs, and checked arena arithmetic. Direct malformed-geometry and segment tests require transactional `ERROR`. |
| C-05 | Fixed | Device reconstruction remains tightly packed internally; successful host commit copies each logical row into the independent caller strides. The trellis test forces padded Y and UV output strides. |
| C-06 | Fixed | The backend derives the number of non-empty bands, records every applicable event, requires sequential collection, and clears pending state at the final effective band. Tests cover all eight `mb_h mod 8` values. |
| C-07 | Fixed | Device downloads land in backend-owned host staging, synchronize, and only then commit caller results and planes. Injected failures after each kind of staged copy leave the current band untouched; public fallback remains byte-exact. |
| C-08 | Fixed | Every byte of the shared `DeviceResult` is cooperatively zeroed before its first phase barrier, covering reserved and unused I4 fields. |
| C-09 | Fixed | A single release helper rolls back partial streams, events, tables, arena, timing storage, and host staging. Failed table upload frees its allocation, and arena growth allocates before replacing the old buffer. |
| C-10 | Fixed | Flush, end-of-encode, and trim now synchronize/abandon or release decimate state. The descriptor reports persistent resources whenever decimate is compiled. |
| C-11 | Fixed | Main and decimate initialization mark success only after resource creation. Device/runtime/stream failures roll back and remain retryable instead of poisoning the process permanently. |
| C-12 | Fixed | Streaming `BEGIN` records timing end without synchronizing. Timing is reported after final collection, or after synchronous `WHOLE`. |
| C-13 | Fixed | The decimate threshold uses checked full-string unsigned parsing and returns `ERROR` with a verbose diagnostic for malformed, negative, or overflowing input. |
| C-14 | Fixed | A serialized wrapper records `WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE` after successful begin/collect/whole calls. |
| C-15 | Fixed | The null lossy-analysis probe checks quarantine, current availability, device count, and configured device. The concurrency test rejects an unavailable configured device before accepting device 0. |
| C-16 | Fixed | The process prewarm object retains its thread handle and joins it during destruction on POSIX and Windows, preventing code/global teardown while it is running. |
| C-17 | Fixed | Hash requests reject unrepresentable packed fields and scan every usable predecessor for `-1 <= predecessor < position`. Invalid-chain and oversized-window tests require unchanged output. |
| C-18 | Fixed | ABI v12 adds dispatcher-owned, non-zero encode-generation tokens to resident producer/consumer requests. Reuse requires token and identity agreement, terminal consumers invalidate offers one-shot, mismatches invalidate them, and end-of-encode clears all generations. Dispatcher tests prove matching lossy and lossless generations; concurrent forced predictor/hash encodes exercise the real path. |

## Compression-policy findings

Q-01 through Q-04 describe real optimizer differences, not corrupt output.
They are retained as explicit policies rather than being presented as CPU-
equivalent searches:

- `WEBP_CUDA_PREDICTOR=1` is now required. The documented policy searches only
  `max_bits`, uses above-mode but not left-mode bias, folds history per row,
  and uses floating-point entropy/ties.
- `WEBP_CUDA_COLOR=1` is now required. The documented policy scores local
  tiles independently without the CPU neighbor-multiplier and accumulated-
  histogram guidance.
- Both stages are off by default. Forced tests require deterministic output,
  decoded-pixel parity, and no more than a 25% encoded-size increase over the
  CPU encoder on every supplied regression input and method.

This makes the quality trade-off an explicit caller decision and turns a
future worsening of the accepted bound into a test failure.

## Build, packaging, and test findings

| ID | Disposition | Remediation |
|---|---|---|
| B-01 | Fixed | Automake distribution manifests include both decimate sources plus the CUDA contract tests and shared test support. |
| B-02 | Fixed | The distributable default is Turing (`sm_75`) SASS plus `compute_75` PTX; local performance builds explicitly request `native`. A fresh build emitted both code forms. |
| B-03 | Fixed | CTest registers CPU dispatcher tests and all CUDA tests, with return code 77 as the no-device skip. Decimate coverage now includes padded strides, all band remainders, invalid geometry/segments, concurrent calls, telemetry, and transactional failure injection. A trusted, non-PR physical-CUDA workflow runs CTest, the forced encoder suite, Compute Sanitizer, and release-manifest checks. |
| B-04 | Fixed | Installed `libwebp.pc` uses `-lcudart` without a build-host toolkit path. |
| B-05 | Fixed | CUDA compilation uses hidden visibility. A fresh shared build exported none of the private descriptor, decimate, or telemetry helpers. |
| B-06 | Fixed | Experimental histogram compilation defaults off. Decimate remains compiled by default after the contract rewrite, focused GPU coverage, and removal of its experimental designation; runtime dispatch still has conservative policy/threshold controls. |

## Local verification

On the RTX 2080 SUPER host:

- focused static CUDA build: passed;
- CTest: 6/6 passed (`accelerator_enc_auto`, `accelerator_enc_cpu`,
  concurrency, histogram/hash contract, trellis/decimate contract, and
  near-lossless);
- forced public CUDA encoder suite: passed, including the 25% quality budgets;
- fresh CPU-only configure/build: 2/2 dispatcher CTests passed;
- fresh shared CUDA build: passed; private CUDA symbols were absent from the
  dynamic symbol table;
- fresh default CUDA code generation: `sm_75` plus `compute_75` PTX;
- generated pkg-config metadata: `Libs.private: ... -lcudart`, with no CUDA
  toolkit path.

The installed Compute Sanitizer 2022.4.1 package on this host could not inject
its own `libsanitizer-collection.so` (even when its packaged directory was
provided explicitly), so it terminated before the first CUDA API call. The
trusted CUDA workflow keeps memcheck and racecheck mandatory on a functioning
runner; this local tool-installation failure is not reported as a sanitizer
pass.

The local host also lacks the Autoconf/Automake executables needed to execute
`make dist`; the source manifest was corrected and the trusted CUDA workflow
performs the actual archive-content check.
