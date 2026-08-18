# Cache-size serial-sweep experiment evaluation (2026-08-18)

## Outcome

The frozen `cache_size_serial_sweep` implementation matrix completed at design
commit `69f349c8706e4181ba9ab169cc2bf42ec4c69863`; executor commit
`5f23f5f68f4515c117c38413a16434bd41a0b6d4` added the immutable raw evidence.
The candidate is **rejected** under the predeclared all-cell rule.

All 18 correctness cells pass exact baseline/candidate/repeated-candidate and
injected-failure-fallback bitstream identity, decoded-pixel identity, and source
pixel identity. All eight performance cells fail. In the four required holdout
cells, candidate/baseline paired medians are 1.07863--1.08865 against the frozen
maximum of 0.98, and p95 ratios are 1.07517--1.10229 against the maximum of
1.02. No passing stratum, fitted threshold, pooled result, or historical nested
clock can override those failures.

The implementation remains independently gated, default off, omitted from
ordinary builds, and useful as a negative research result, so it is retained.
Retention is not promotion. Production defaults, public ABI/API, installed
headers, cache semantics, quality behavior, thresholds, fallback, Metal policy,
and CUDA behavior do not change.

No additional timed work was run during this evaluation.

## Authority and ancestry

The independently verified serial history is:

1. required main parent `76c34b682818186132269a13f3e645ecd9e7800d`;
2. design/code commit `69f349c8706e4181ba9ab169cc2bf42ec4c69863`,
   whose sole parent is the required main parent;
3. execution/evidence commit `5f23f5f68f4515c117c38413a16434bd41a0b6d4`,
   whose sole parent is the design/code commit;
4. the separate evaluation/consequence descendant containing this report.

The frozen authorities are byte-identical to the handoff values:

| Authority | SHA-256 |
|---|---|
| manifest | `25e55f841908a75c8362602b3d28e257a73ef4277c87bbbcdce6c5cd5438850f` |
| operator | `e2081b69ab3d7b224967aa07c2c2a2d67f7b77d78a4c2817600dc62b7fec5a2b` |
| candidate source | `a63d2efba154f4c395d2ac8e0fe19553794cc7c3657b6a2891866604765709ca` |
| runner | `63c7523dd36d9860b3d8071d6685edfc8c1bed12cdee8cb32554938f4acef53e` |
| protocol document | `0755c0aff92c8bf897523700cc6ca33e0db92f4f508e98c8dc617ae8da956915` |
| corpus generator | `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007` |
| corpus manifest | `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff` |

The artifact index itself hashes to
`4c2e366ebaae7fbbf7a0a1e0381d935cc8cc47c3fa184eb0f670fab499bdc8f9`.
It exactly enumerates every frozen evidence file except itself. Each indexed
byte count and SHA-256 independently matches `build.log`, `commands.jsonl`,
`correctness.json`, `evaluation.json`, `operator-report.md`, `records.jsonl`,
and `resources.json`.

## Protocol and schema audit

The manifest and all seven output schema identifiers match their frozen `v1`
names. Every JSON/JSONL row parses, has the exact expected field set, and uses
the expected schema. Positive timing, size, wall-duration, and resource values
have the required primitive types and ranges.

The reconstructed execution inventory is:

| Artifact or role | Count |
|---|---:|
| command processes | 112 |
| raw sample records | 392 |
| cold measured records | 72 |
| discarded warmups | 40 |
| measured warm records | 280 |
| all measured records | 352 |
| measured baseline / candidate records | 176 / 176 |
| correctness cells | 18 |

Command order is exactly tune `texture-medium` then holdout `texture-large`,
method 4 then 6, and cold then warm. Within each cell, pair order alternates
baseline/candidate and candidate/baseline beginning with baseline/candidate.
Cold uses nine process pairs with zero warmups and one measurement per process.
Warm uses five pairs with one discarded warmup followed by seven measurements
per process. Record sequence, pair, order, variant, lifecycle, role, method,
iteration, sample role, command argument, and per-command row count all match.

Tune and holdout, methods, and lifecycles remain separate. Warm observations
are first reduced to one median per process. The paired location statistic is
the median of candidate-process/baseline-process ratios. P95 is nearest-rank in
each raw variant stratum followed by candidate/baseline division. Recomputing
those formulas directly from `records.jsonl` reproduces every committed float
exactly:

| Role/case | Method | Lifecycle | Paired median | P95 ratio | Pass |
|---|---:|---|---:|---:|---|
| tune/texture-medium | 4 | cold | 1.083918 | 1.079118 | no |
| tune/texture-medium | 4 | warm | 1.086992 | 1.108669 | no |
| tune/texture-medium | 6 | cold | 1.086159 | 1.068907 | no |
| tune/texture-medium | 6 | warm | 1.075564 | 1.057074 | no |
| holdout/texture-large | 4 | cold | 1.085352 | 1.102290 | no |
| holdout/texture-large | 4 | warm | 1.079806 | 1.075171 | no |
| holdout/texture-large | 6 | cold | 1.088650 | 1.094643 | no |
| holdout/texture-large | 6 | warm | 1.078630 | 1.081518 | no |

Every measured baseline and candidate row has the same bitstream byte count and
FNV-1a signature within its case/method stratum. The committed correctness
matrix exactly crosses all nine publication cases with methods 4 and 6. Its
input and decoded hashes match the publication manifest, and every
determinism/fallback flag is true. Source inspection confirms those summaries
were emitted only after comparing baseline, candidate, repeated candidate, and
injected-failure fallback streams and decoded PPMs. The independent untimed
validation repeated the complete matrix and passed.

## Build, host, resource, and lease audit

The transcript contains two clean static Release builds with Metal explicitly
off. The baseline configure command omits the candidate option; the candidate
command adds only `WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=ON`. The same
runner source is separately linked to each static library. The baseline build
does not compile the candidate translation unit, while the candidate does.
No installed header changed, and the only new header is private under
`src/enc`.

The execution context records a physical MacBook Pro `Mac16,7`, Apple M4 Pro,
14 CPU cores, 20 GPU cores, arm64, Metal 4, macOS 26.5.1 build 25F80, Darwin
25.5.0, Xcode 26.3 build 17C529, and Apple clang 17.0.0
(`clang-1700.6.4.2`). Untimed post-run host queries corroborated those fields,
AC power, a charged battery, and no thermal, performance, or CPU-power warning.
`nvcc` was absent, CUDA was not run, and the frozen build disabled Metal.

The context names Xcode's macOS 26.2 SDK path. The build transcript proves the
compiler identity but is not verbose enough to prove the effective sysroot.
Post-run compiler inspection selected the Command Line Tools macOS 26.5 SDK as
its implicit sysroot, while an explicit `xcrun --sdk macosx` query selected the
reported Xcode 26.2 SDK. The effective timed-build SDK is therefore not
conclusively recorded. This provenance limitation does not turn a failed
performance gate into a pass, but it precludes a stronger SDK-specific claim.

Post-run power inspection also showed Low Power Mode enabled on AC; the frozen
preflight did not record that setting. Pairing and alternating order reduce its
effect on the within-run A/B comparison, and the candidate loses by a wide
margin in every cell, but the omission further limits system-state
reproducibility.

Resource and lease gates otherwise pass:

| Gate | Observed | Requirement |
|---|---:|---:|
| available memory | 10,283,384,832 bytes | at least 4 GiB |
| total elapsed | 162.557661 s | at most 3,600 s |
| maximum child RSS | 283,000,832 bytes | at most 2 GiB |
| output before index | 241,541 bytes | at most 2 GiB |
| longest command | 3.637276 s | at most 240 s |

The frozen operator uses one synchronous child at a time and a nonblocking
exclusive flock at `/tmp/libwebp-metal-cache-size-serial-sweep.lock`. The
supplemental lease record shows no holder before execution, the operator PID as
holder during execution, and no holder after exit. `resources.json` records
`lease_released: true`; an independent final `lsof` query also found no holder.

## Untimed final validation

The evaluator ran no timing subcommand and acquired no benchmark lease. These
untimed checks passed:

- frozen manifest/operator/hash validation;
- exact evidence/schema/inventory/order/statistic reconstruction;
- exhaustive chosen-cache-bit equivalence over binary and mixed reference
  streams, cache bits 0--10, quality edges, and targeted sizes;
- complete nine-case, two-method end-to-end bitstream and decoded-pixel
  equivalence, deterministic repeat, default-off behavior, and transactional
  injected failure;
- ordinary/candidate build independence, omitted baseline symbols/strings,
  exact runtime refusal, and independent experiment guards;
- undefined-behavior and integer-sanitizer smoke coverage;
- Python bytecode compilation and diff hygiene.

## Consequence, limitations, and next lead

The serial sweep is slower, not merely inconclusive, on this frozen matrix. It
must not be promoted, and no cache-size threshold or dispatch rule should be
fitted from these data. The default-off research implementation is safe within
the tested scope and preserves exact output/fallback behavior, so removing it
would discard a reproducible negative result without improving production
behavior.

The evidence remains limited to one machine, one OS/compiler state, one
execution, deterministic synthetic textures at two sizes, methods 4 and 6,
lossless quality 75, single-threaded encoding, and end-to-end `WebPEncode`
timing. Warm samples within a process are correlated. It does not estimate a
device population, natural-image workload mix, energy, concurrency, long-run
thermal behavior, or isolated cache-search time. The SDK and Low Power Mode
record limitations above must accompany any reproduction claim.

If a later cycle is authorized, the next lead is a **single-pass contiguous
cache-state layout**: preserve the baseline's one reference traversal and exact
ascending/tie semantics while replacing per-candidate allocation topology with
one transactional slab for histograms and color-cache state. It must use wholly
new independent gates, proposed as
`WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`,
`WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`, and
`WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=1`; it must not reuse this cycle's
serial-sweep gate or evidence. That lead was recorded only. It was not built,
timed, or run in this cycle.
