# Cache-size single-pass slab experiment evaluation (2026-08-18)

## Outcome

The frozen `cache_size_single_pass_slab` implementation matrix completed at
designer commit `fa2400ebf4519b8f6bc3acde50e01cb1c2ab0117`; executor commit
`0a2dc8bf7ae5c4a86fc4e515330e8e76a315ca9d` added the immutable raw
evidence. The candidate is **rejected** under the predeclared all-cell rule.

All 18 correctness cells pass selected-cache-bit equivalence in untimed tests
and exact baseline/candidate/repeated-candidate/injected-failure/default-build
bitstream and decoded-pixel identity in the frozen matrix. Performance does not
pass: all four tune cells fail, and three of the four required holdout cells
miss the paired-median maximum of 0.99. Holdout method-6 warm is the only
required cell that passes both the median and p95 limits. No tune result,
passing p95, pooled statistic, historical sample, multiplied ratio, or fitted
threshold can override a required median failure.

The implementation remains independently gated, default off, omitted from
ordinary builds, and useful as bounded negative research evidence, so it is
retained. Retention is not promotion. Production defaults, public ABI/API,
installed headers, cache semantics, quality behavior, thresholds, fallback,
Metal policy, and CUDA behavior do not change.

No timed command, new experiment, closed-experiment rerun, sample reuse, or
ratio multiplication was performed during this evaluation.

## Authority, ancestry, and hashes

The independently verified linear history is:

1. original main `e7900b9a4bf71e799001d343721c86f4aad96316`, tree
   `cdeb4c90e404bbc4a5cc97893cdb9be6330acd59`;
2. designer commit `fa2400ebf4519b8f6bc3acde50e01cb1c2ab0117`, sole parent
   original main, tree `225f7f3682ac9340f475eff4269a5f22f66688fd`;
3. evidence commit `0a2dc8bf7ae5c4a86fc4e515330e8e76a315ca9d`, sole parent
   designer commit, tree `731cdfadb927fdda578042062fb08b8cbf9b9b0f`;
4. the separate evaluation/consequence descendant containing this report.

The frozen authorities independently hash as follows:

| Authority | SHA-256 |
|---|---|
| frozen manifest | `91a6b7bd95bb365b59a6e5dd273927bb173d909898fbbfa031108670ec004707` |
| operator | `c797c4ba75c2241bb9e209c0ce9eb911c3a5c1b07d95fe4dc6ff26695f8a4728` |
| candidate source | `cecf0e49d6f1ff920b4385525abfc7e43aaf9eebebe0882e27eeca2af873955a` |
| private candidate header | `4a8bb046978282e968f684b180ce79a9c24c7d75188429f021ac52eca9d63b90` |
| runner | `ba261325ed8a3196885630b588ef820097d8c623347a5742373be1c857ff6c80` |
| protocol document | `5c076d60f9af6c4e26b8592eedb3da5fc080b6b29c9f809f558692452e7a0313` |
| design report | `2a7df58e7f47586cd1fbbded12197107be8e62ce999e08603db62cef3021e9c4` |
| schema catalog | `4f33c2f9a33b06ee2ed98b074cad248b582c595213359865347ffbd77f1c565d` |
| corpus generator | `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007` |
| corpus manifest | `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff` |

The remaining designer-commit files independently hash to:

| File | SHA-256 |
|---|---|
| `CMakeLists.txt` | `3213c0620b092982833d849f12cfda9391e9e26fd658e72b7dc4b6a41ee158d8` |
| `doc/experiment-guard-matrix.md` | `9845f8c893847c12e293fd774cbecf8eb6ba9ca87c2126f26b7ffb1a2c5dcc6b` |
| `makefile.unix` | `d5ea545204836f06c297c0cc3ace1e311f13040436748064d83c6910f93be845` |
| focused untimed Python test | `cb8ba00942bd36584854921996e90706b5500449b742ab6e359530fc7949dfa0` |
| shared experiment-guard test | `394aa816e0eeb3a84cc1a34d81e77dfc1ee49816c3d9e107363f658612c4205a` |
| backward-reference dispatch source | `85745db63a6f82a0d7ee39745ff59bbeded85e1af78a61ea31a0b658142bdda0` |
| `tests/README.md` | `e9651ff06def024027e434481f7ed9abd1ead692203fab2f6e32658886f02439` |
| focused C test | `b14504198f5f54b21dc75047124f868760b30a5a653606d3c42305c2db657006` |

The artifact index itself hashes to
`9b831c1b5af71363846a64bbf6973e79404580bde27e2fef3211e9e268fbc913`.
It exactly enumerates every frozen evidence file except itself. Each byte count
and SHA-256 was recomputed independently:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `build.log` | 39,286 | `c0f5e6424605ba917a091238157a89f46b003371644af835c87cc0e75d69bcea` |
| `commands.jsonl` | 74,429 | `ba357be4bbe7dc0864986ed33cd84129a33b831f6cc505f335e296eac57bca16` |
| `correctness.json` | 9,591 | `2c35673e0d0012a55e9d4ded24d9671bd28713019bf61545a7c4d067d2ad36e9` |
| `evaluation.json` | 2,397 | `31b7fec269b12ddc5f2ce5a6180db6188a144d0198a7ba9d14cdef2bfbe4e988` |
| `operator-report.md` | 310 | `97241d10cee2e049da82cb7d5ad293654de94e33700602789b639626fd6aa7c4` |
| `records.jsonl` | 206,190 | `cd0de4846cba36da4d8b964064979bef5ff2a0da828c51646ceef951eb30cdd2` |
| `resources.json` | 359 | `534b6703817becdcbce0ce0aade2b79ffda714ad709ca4bdccea8928169485a8` |

The evidence files remain byte-identical to their evidence-commit blobs. This
evaluation does not modify or add to the frozen evidence directory.

## Schemas, corpus, protocol, and inventory

The exact six schema identifiers are:

- `libwebp-cache-size-single-pass-slab-sample-v1`;
- `libwebp-cache-size-single-pass-slab-command-v1`;
- `libwebp-cache-size-single-pass-slab-correctness-v1`;
- `libwebp-cache-size-single-pass-slab-evaluation-v1`;
- `libwebp-cache-size-single-pass-slab-resources-v1`;
- `libwebp-cache-size-single-pass-slab-artifact-hashes-v1`.

Every JSON and JSONL object parses, has the exact required field set, carries
the expected schema identifier, and satisfies the catalog's primitive and
range requirements. The evaluation declares end-to-end `WebPEncode` as its
only timing authority and correctly records no boundary timing.

The deterministic publication corpus was regenerated twice during the audit
and matched its tracked manifest. The nine PPM hashes are:

| Case | Dimensions | Bytes | SHA-256 |
|---|---:|---:|---|
| photo-small | 512x512 | 786,447 | `18a612146faf5cdc2d9f786ddcd946615235db992c83011d37c89b1728b90922` |
| graphic-small | 512x512 | 786,447 | `ddd376ba50104a0d7aea5498def73c9299d5304cd4ffe4c02f18d1107b6f79cf` |
| texture-small | 512x512 | 786,447 | `51c73a488d129f60eca7a110cc3dbf7117045a8e13104ee1bf87922707c651e6` |
| photo-medium | 1600x1200 | 5,760,017 | `a1a6ab156ae4b18666a780bcdf7eaf7d2124415eb192e091dc21e7adbf383c70` |
| graphic-medium | 1600x1200 | 5,760,017 | `c42deaa474e253db740384e7e93a208c82ff11cd66dc2930c34678a9e8279234` |
| texture-medium | 1600x1200 | 5,760,017 | `91d90466139f54ad441448bc7d352c637a4020ce928434dbff3a358c5a829385` |
| photo-large | 3000x2000 | 18,000,017 | `b18f3f3e0b3324ae5c8e42f5eac831a8ba350e64c181340aa65410649b2e4612` |
| graphic-large | 3000x2000 | 18,000,017 | `26d81b74583a1b379282c6cf45bb8eeb2b352958b221a5ebf7ea8421c575e5cc` |
| texture-large | 3000x2000 | 18,000,017 | `dd02badce31b757f9374f0f5de187e9de3158fe6878929207eeed24ea72d79e2` |

All nine cases are correctness inputs. Timed roles are tune
`graphic-medium` and holdout `texture-large`. Execution is tune before
holdout, method 4 before 6, and cold before warm. Cold uses 11 process pairs,
zero warmups, and one measurement per process. Warm uses six process pairs,
two discarded warmups, and nine measurements per process. Pair process order
alternates baseline/candidate and candidate/baseline, beginning with
baseline/candidate; cold consumes 11 order entries and warm consumes six.

Record sequence, process pair, process order, variant, lifecycle, role, method,
iteration, sample role, command arguments, and per-command row counts all match
that frozen construction. The reconstructed inventory is:

| Artifact or role | Count |
|---|---:|
| command processes | 136 |
| all raw sample records | 616 |
| cold measured records | 88 |
| discarded warmups | 96 |
| warm measured records | 432 |
| all measured records | 520 |
| measured baseline / candidate records | 260 / 260 |
| correctness cells | 18 |

Warm observations reduce first to one median per process. The location metric
is the median of six or eleven candidate-process/baseline-process ratios. P95
is nearest-rank within each raw measured variant stratum followed by
candidate/baseline division. Case, method, lifecycle, and tune/holdout roles
are never pooled.

## Correctness, semantics, fallback, and build gates

Source reconstruction confirms one immutable-reference traversal with all
cache-bit states simultaneously live. Literal or changed-copy cache updates run
from the maximum cache bits down through one. Entropy selection runs from zero
up through the maximum and replaces the winner only on strict improvement, so
ties retain the lower cache-bit value. Quality at or below 25 still selects
zero. The result is published only after complete evaluation; allocation or
injected failure leaves the caller's maximum unchanged and dispatches the
unchanged baseline.

The candidate uses one zero-filled allocation containing metadata,
histograms, variable literal arrays, and cache colors. It does not call the
baseline histogram or color-cache allocators and initializes one reference
cursor. It does not replay the stream and is not the closed serial-sweep
topology.

The correctness matrix exactly crosses nine cases and methods 4 and 6. Every
input and decoded hash matches the publication manifest, and every recorded
decoded-source, deterministic-repeat, fallback, and default-build flag is true.
The frozen stream hashes are:

| Case | Method-4 bitstream SHA-256 | Method-6 bitstream SHA-256 | Decoded/source SHA-256 |
|---|---|---|---|
| photo-small | `b5b9df591b5460706593d464d08fbc70389cec19231bc602708eced19e269403` | `b5b9df591b5460706593d464d08fbc70389cec19231bc602708eced19e269403` | `18a612146faf5cdc2d9f786ddcd946615235db992c83011d37c89b1728b90922` |
| graphic-small | `1dc7528be6a7fe377aa08fba7b0e0a9d3490bb4ec72cae1200c3e3246b0818cd` | `1dc7528be6a7fe377aa08fba7b0e0a9d3490bb4ec72cae1200c3e3246b0818cd` | `ddd376ba50104a0d7aea5498def73c9299d5304cd4ffe4c02f18d1107b6f79cf` |
| texture-small | `d45edae7ef6176f0784f38fbdc4cb8c8c433c1478cfd33198ae4f1a531893dd4` | `d45edae7ef6176f0784f38fbdc4cb8c8c433c1478cfd33198ae4f1a531893dd4` | `51c73a488d129f60eca7a110cc3dbf7117045a8e13104ee1bf87922707c651e6` |
| photo-medium | `c3a7275a566db42b96ca287acb623a16b042912e01b99585c2b7f14a4f43587a` | `37a5c7db4627702812695a3d76ea44cbf52e412c960a76395d2f40425b881152` | `a1a6ab156ae4b18666a780bcdf7eaf7d2124415eb192e091dc21e7adbf383c70` |
| graphic-medium | `be9d2ac71ab6b8c5ac3254431fde2c94b7c22f69af68acc60263715720429628` | `be9d2ac71ab6b8c5ac3254431fde2c94b7c22f69af68acc60263715720429628` | `c42deaa474e253db740384e7e93a208c82ff11cd66dc2930c34678a9e8279234` |
| texture-medium | `aa578b4802eca8c086546d4a67b1f65524ece9fbd073255e21e6c62f760feb75` | `aa578b4802eca8c086546d4a67b1f65524ece9fbd073255e21e6c62f760feb75` | `91d90466139f54ad441448bc7d352c637a4020ce928434dbff3a358c5a829385` |
| photo-large | `d21aa8d0755b8c6bc377afcf1142499c66a42d2de1d00561fdd65a126a7ce83c` | `7c72ce50697d343dafe98a21b39e9255a669b7b84c1ca820b2fcd7206579a521` | `b18f3f3e0b3324ae5c8e42f5eac831a8ba350e64c181340aa65410649b2e4612` |
| graphic-large | `f4bd94160601ce53fad92579816fce9866267fdc00eebee62dd2d2ef9f71074a` | `f4bd94160601ce53fad92579816fce9866267fdc00eebee62dd2d2ef9f71074a` | `26d81b74583a1b379282c6cf45bb8eeb2b352958b221a5ebf7ea8421c575e5cc` |
| texture-large | `fe3ab825aeb1dd6154a358c5e17e5081cae805497da8b4de30cd962a484cf52c` | `fe3ab825aeb1dd6154a358c5e17e5081cae805497da8b4de30cd962a484cf52c` | `dd02badce31b757f9374f0f5de187e9de3158fe6878929207eeed24ea72d79e2` |

All measured rows have one invariant bitstream byte count and FNV-1a signature
within each case/method stratum: `graphic-medium` is 548 bytes /
`4fb34c8576a07821`, and `texture-large` is 18,000,080 bytes /
`1e6ae4c767091f74`, for both methods and variants.

The private C test independently compares selected cache bits for cache bits
0--10, exact ties, qualities 0/25/26/75/100, exhaustive binary literals, mixed
literal/copy streams, and targeted sizes through 65,537 pixels. It also checks
immutable inputs and transactional failure. The focused end-to-end untimed
test repeats baseline, candidate-off, candidate-on, candidate-repeat,
injected-fallback, and ordinary-build-with-candidate-environment stream and
decode equivalence across the complete matrix.

Activation is fail-closed and requires the default-off build option
`WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`, private macro
`WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT`, exact runtime value
`WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=1`, and exact session value
`WEBP_BENCHMARK_SESSION=exclusive`. Invalid runtime or missing session refuses
encoding. Ordinary CMake and Unix make builds omit the source, macro, symbols,
runtime/fault strings, and focused target. No installed or public header is
changed.

## Raw statistics and criteria

The table reports descriptive raw medians and nearest-rank raw p95s in
milliseconds for each A/B stratum, then the frozen acceptance statistics
recomputed directly from `records.jsonl`. Cold has 11 raw rows per variant;
warm has 54 measured raw rows per variant. Acceptance requires paired median
at most 0.99 and p95 ratio at most 1.01 in every holdout cell.

| Role/case | Method | Life | Raw n B / C | Raw median B / C ms | Raw p95 B / C ms | Paired median ratio | P95 ratio | Median | P95 | Cell |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| tune/graphic-medium | 4 | cold | 11 / 11 | 15.738125 / 15.948458 | 28.856500 / 28.043208 | 1.007155782 | 0.971815986 | fail | pass | fail |
| tune/graphic-medium | 4 | warm | 54 / 54 | 14.591375 / 14.752667 | 14.892333 / 15.315292 | 1.009201061 | 1.028401124 | fail | fail | fail |
| tune/graphic-medium | 6 | cold | 11 / 11 | 15.651541 / 15.807625 | 15.826458 / 16.061083 | 1.013095132 | 1.014824858 | fail | fail | fail |
| tune/graphic-medium | 6 | warm | 54 / 54 | 14.592438 / 14.787730 | 15.127000 / 15.126792 | 1.010746980 | 0.999986250 | fail | pass | fail |
| holdout/texture-large | 4 | cold | 11 / 11 | 401.365791 / 400.010750 | 409.263584 / 406.229333 | 0.994950938 | 0.992586071 | fail | pass | fail |
| holdout/texture-large | 4 | warm | 54 / 54 | 396.472292 / 391.867396 | 403.917125 / 396.648833 | 0.990321491 | 0.982005487 | fail | pass | fail |
| holdout/texture-large | 6 | cold | 11 / 11 | 404.031125 / 403.294708 | 412.663041 / 408.629292 | 0.997983489 | 0.990225078 | fail | pass | fail |
| holdout/texture-large | 6 | warm | 54 / 54 | 397.733021 / 393.446250 | 402.334250 / 398.333917 | 0.988181990 | 0.990057190 | pass | pass | pass |

Every committed float is exactly reproduced by the frozen formulas. Therefore:

| Criterion | Result |
|---|---|
| all 18 correctness cells | pass |
| exact selected bits/order/ties and immutable inputs | pass in independent untimed tests |
| exact bitstreams, decoded pixels, determinism, fallback, default-build independence | pass |
| source/protocol/corpus/schema/evidence hashes and evidence immutability | pass |
| schema, raw-row, process, order, lifecycle, role, and sample inventory | pass |
| runtime/build/lease fail-closed gates and default omission | pass |
| resource ceilings and recorded lease release | pass |
| execution-time device/power/thermal/disk/sole-host provenance | not independently provable from frozen artifacts; limitation |
| tune performance (descriptive) | 0/4 cells pass |
| required holdout paired medians | 1/4 pass; criterion fails |
| required holdout p95 ratios | 4/4 pass |
| every required holdout performance cell | 1/4 pass; criterion fails |
| frozen all-gate promotion rule | **fail: reject** |

## Build, resources, lease, stderr, and limitations

The build transcript records two static Release builds with Metal explicitly
off. The baseline omits the candidate option; the candidate adds only
`WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT=ON`. The same runner source
is linked separately to each static library. AppleClang identifies as
17.0.0.17000604, and discovered dependencies come from the Command Line Tools
macOS SDK. CUDA is forbidden by the manifest and no CUDA source, option, or
tool appears in the build or evidence.

Resource and lease gates pass:

| Gate | Observed | Requirement |
|---|---:|---:|
| available memory preflight | 10,361,896,960 bytes | at least 4 GiB |
| total elapsed | 187.869625083 s | at most 5,400 s |
| maximum child RSS | 282,968,064 bytes | at most 2 GiB |
| output before index | 331,893 bytes | at most 2 GiB |
| longest command | 4.603503333 s | at most 300 s |
| parallel benchmark processes | 1 | exactly 1 |

The operator uses one synchronous child and a nonblocking exclusive flock at
`/tmp/libwebp-metal-cache-size-single-pass-slab.lock`. `resources.json` records
release. Before this audit, an independent nonblocking exclusive acquisition
succeeded, no experiment runner/operator process was active, and the evaluator
explicitly unlocked while leaving the persistent marker intact.

The transcript has two linker warnings for duplicate static libraries; both
builds still succeed. CMake's failed architecture-capability probes are normal
feature detection on arm64, not compiler diagnostics from candidate source.
No candidate C warning or build error appears. Timed child stdout had to parse
entirely as sample JSON for execution to complete, but the operator did not
preserve a separate timed-child stderr artifact, so a stronger stderr-empty
claim is unavailable.

The frozen artifacts also do not record execution-time hardware identity, AC
power, battery, thermal/performance/CPU-power warnings, disk availability, sole
host ownership, or `nvcc` discovery. Untimed evaluator queries on the current
host show a MacBook Pro `Mac16,7`, Apple M4 Pro, 14 cores, 24 GiB RAM, macOS
26.5.1 build 25F80, Apple clang 17.0.0 (`clang-1700.6.4.2`), Command Line Tools
SDK, AC power, charged battery, no recorded thermal/performance/CPU-power
warning, ample disk, and no `nvcc`. These corroborate the likely environment
but cannot retroactively prove its state during timing. This provenance gap
limits reproduction claims; it cannot rescue failed required performance
cells.

The result covers one execution, deterministic synthetic graphic/texture
inputs at two sizes, methods 4 and 6, lossless exact quality 75, thread level
zero, and end-to-end encoding. Warm samples within a process are correlated.
It does not estimate a device population, natural-image workload mix, energy,
concurrency, long-run thermal behavior, or isolated cache-search time. The
design report also makes no AddressSanitizer pass claim on this Apple host;
executable array-bounds, pointer-overflow, undefined-behavior, and integer
sanitizer checks are the frozen sanitizer scope.

## Untimed final validation

The evaluator ran no timing subcommand and did not enter a benchmark session.
These commands passed:

```sh
python3 scripts/run_cache_size_single_pass_slab_experiment.py validate
python3 scripts/test_cache_size_single_pass_slab_experiment.py
python3 scripts/test_experiment_guards.py
python3 scripts/test_publication_corpus.py
```

They respectively verified the frozen manifest/operator hashes; exhaustive
selected-bit/equivalence/fallback/determinism/build-independence and sanitizer
coverage; ten independent build/runtime/lease guards; and publication-corpus
schema, license, provenance, and two-generation byte determinism.

## Consequence and next lead

The single-pass slab is output-equivalent but does not satisfy the required
end-to-end median improvement consistently. It must not be promoted, and no
cache-size threshold or dispatch rule should be fitted from these data. The
default-off implementation is safe and useful as a reproducible negative
topology result, so direct removal is not warranted.

No new experiment is required for this decision, no follow-up experiment is
proposed here, and none was run. If future profiling identifies a different
boundary worth testing, it must first freeze a wholly new build option, compile
macro, exact runtime opt-in, corpus roles, lifecycle, statistics, acceptance
limits, resource/lease prerequisites, and output schemas; it may not reuse the
closed row-8, row-9, or row-10 samples or multiply their ratios.
