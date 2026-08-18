# Back-reference cache-search executor handoff

This is the separate executor evidence handoff for the one frozen
`backref_cache_search` run. The designer commit remains unchanged. Raw evidence
is external and immutable at:

`/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search`

## Frozen authority

- Base: `297b9e5257ed1098503f7630f3223c1fddbef261`
- Designer/source: `90ceb5a3d81a761678c0e89d44f7c09e5ce18836`
- Manifest: `scripts/backref_cache_search_experiment_v1.json`
- Manifest SHA-256: `ed0c68b0e72fb013da5fe244d20453e3c86d1199cc7877725c2c4b4fb8041fe1`
- Operator: `scripts/run_backref_cache_search_experiment.py`
- Operator SHA-256: `1a66c966dc1d5735e5bba6ef8b281f4b8093b542c399b451c72594d8084a1848`
- Corpus generator SHA-256: `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007`
- Corpus manifest SHA-256: `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff`

## Exact execution

The only timed command executed was:

```sh
WEBP_EXPECTED_DESIGNER_COMMIT=90ceb5a3d81a761678c0e89d44f7c09e5ce18836 WEBP_BENCHMARK_SESSION=exclusive WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT=1 python3 scripts/run_backref_cache_search_experiment.py run backref_cache_search /Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search
```

The command exited `0`. The committed executor transcript is
`profile-data/runs/20260818-next-backref-cache-search-executor/executor-transcript.txt`.
The operator-owned build and raw command transcripts are respectively:

- `/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search/build.log`
- `/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search/commands.jsonl`
- `/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search/stderr/0001.log` through `0080.log`

The operator emitted one corpus-verification pass line to the executor
transcript. Per-command stderr files are all zero length and are covered by the
external artifact hash index.

## Source, device, and resource evidence

The operator recorded:

- macOS 26.5.1, build `25F80`, arm64;
- Apple clang 17.0.0 (`clang-1700.6.4.2`), target `arm64-apple-darwin25.5.0`;
- one physical Apple M4 Pro device, Metal family 4;
- 10,079,453,184 bytes available memory at preflight;
- AC power, internal battery at 100% and charged;
- no recorded thermal, performance, or CPU-power warning;
- 87.91612601280212 seconds elapsed and 356,171,776 bytes maximum observed RSS.

The SDK diagnostic recorded by the operator says that
`/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk` could not be located.
The frozen build nevertheless completed; this diagnostic was not a failed
operator gate. The build transcript also contains two linker search-path
warnings for `/opt/local/lib`; the build completed successfully.

This is a CPU-boundary diagnostic. The frozen protocol requires no Metal
dispatch evidence and makes no GPU-performance claim.

## Raw evidence inventory and hashes

The external artifact index is:

`/Users/jonaskamsker/.codex/worktrees/0351/libwebp-metal-evidence/20260818-cycle3/backref-cache-search/artifact-hashes.json`

Its SHA-256 is
`55acf72755516c68fa9b6884589553ae8b9d1ba18679de85d7a97f29491e547d` and it
covers 89 artifacts excluding the index itself. The frozen inventory is:

- 80 command rows;
- 200 raw timing records;
- 54 raw correctness records;
- 18 correctness summary rows;
- 80 per-command stderr files;
- 56 cold records, 24 discarded warmups, and 120 measured warm records;
- 88 measured record-variant and 88 measured control-variant records.

The operator’s `correctness.json` reports `ok: true`; its raw correctness
records cover repeated record determinism, control identity, decoded-pixel
identity, injected recorder failure, and recorder-open failure. The operator
validated the frozen command order and complete inventory.

## Lease and executor boundary

The operator acquired `/tmp/libwebp-metal-next-boundary.lock` and reports
`lease_released: true` in `resource-notes.json`. The lock path remains as a
zero-byte bookkeeping file, but the operator’s flock was released. No CUDA,
parallel benchmark process, source change, parameter change, rerun, or
hypothesis change occurred.

No performance interpretation was performed. This handoff contains no timing
ratio, p95 calculation, acceptance/rejection decision, or production
consequence. Evaluation is the next phase’s responsibility.
