# Phase 2 frozen executor/auditor refusal

Phase 2 is refused fail-closed for `BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3`. The audited chain is exact main `92c3b59b2d178c5a03ec20b897252b358f07de81` → Phase 1A `3b81544df3305601e8c0817e554833f0824ad634` → additions-only Phase 1B `b2bca487bdab0d996e03ee9def8dce1d11e7cd0e`. The trees are `6bf2a478b733d5e80ac2656448fe48c8c0964d9a`, `5e51c6925729f994dcc9987c583a9f1d02acb721`, and `bd96b57638cfd2ae3fa4ae741aa9c5f5ca3bd4a9`, respectively. Phase 1A changed 52 paths; Phase 1B added 30 paths with zero modifications, deletions, renames, or overlap.

The frozen transport consequence remains `fresh-bounded-requalification`: no deterministic V2 transport regression was found, so the 65,536-byte request chunks, 15-second request-progress deadline, buffers, retries, and connection count remain unchanged. The historical request counts are V3 `354/354` ACKed chunks, V4 `357/357`, and V2 `5/364` (`327,680/23,820,500` bytes).

The sole Phase-1B rehearsal used one SSH session and no retry. It wrote and ACKed `365/365` request chunks (`23,869,976` payload bytes; `23,934,714` wire bytes), reconstructed a complete 365-row progress chain, returned `18,659` response bytes and a `14,265`-byte archive, and recorded `214,981` stdout bytes and `0` stderr bytes. The chain’s ACK digests, ranges, cumulative bytes, order, timestamps, and latencies all reconstruct without error. Source admission, toolchain/device/resource/process isolation, archive parsing, integrity, exact-child cleanup, and absence receipts pass; rehearsal workloads, lease attempts, correctness encodes, runner children, and performance samples are all zero.

Authority is nevertheless `NONE` and the stage result is `REFUSED`: the rehearsal timed binary is `653,712` bytes with SHA-256 `1ca731d0411a15eb2626e02adb7bca789a628f4d0d9c6c57e3fa4352a958a920`, while the frozen Phase-1A reference is `643,024` bytes with SHA-256 `262f23ba84c979fbb62d868f534feca20c428063aaab4804990f01311e04ae42`. The linker-map bytes, linker-map hashes, and canonical instruction/word hashes also differ. Matching addresses, section size `50,444`, body `3,600`, padding `46,844`, spacing `16,384`, and displacement `32,768` do not cure an exact-receipt failure.

The Phase-1B success gate was reconstructed locally and produced the same result: every individual receipt/transport gate passed except `alignment build frozen`. Phase 2 made zero SSH, host/device/runner/remote, lease, benchmark, retry, rerun, profiler, CUDA, archive/extraction, sample, or alternate timing contact. No Phase 3 evaluation was run.

Machine-readable audit: `phase2-refusal-audit.json`.

Blocker: the exact Phase-1A versus rehearsal Unix-make binary/codegen identity mismatch is immutable in this frozen Phase-2 handoff; no repair or rerun is permitted.

Next lead: a future Phase-1 owner must produce a fresh independently hashed rehearsal whose Unix-make timed binary and codegen receipts exactly match a newly frozen Phase-1A identity before Phase-2 authority is reconsidered.
