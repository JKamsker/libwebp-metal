# Experiment 4 operator report

Status at artifact assembly: completed-valid. This report records execution only; it contains no timing interpretation, variant ranking, or recommendation.

## Scope and source

- Experiment: Metal kernel/memory ablations (item 4 only).
- Required source base: `18fd520d5d7faf0645d461bded27c0ba7ee4a48e`.
- HEAD before execution: `fbec692e7ec83336d65eb7c1b9441016d4495815`.
- Verified experiment-1/2/3 commits were preserved.
- No other agent or experiment was used; codec algorithms were not modified.

## Commands and flags

The exact commands were:

```text
make -f makefile.unix clean
make -f makefile.unix -j8 examples/cwebp examples/dwebp WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1 metal-ablation-tools
python3 scripts/benchmark_metal_ablation.py --output /tmp/libwebp-metal-experiment-4-preflight-20260817T191001Z
WEBP_METAL_ABLATION_EXPERIMENT=1 WEBP_TEST_REQUIRE_METAL=1 scripts/test_metal.sh <fixed-canonical-mitski.png> <fixed-canonical-corgi.jpeg> <fixed-canonical-siamese.jpg>
scripts/test_experiment_guards.py
WEBP_BENCHMARK_SESSION=exclusive WEBP_METAL_ABLATION_EXPERIMENT=1 python3 scripts/benchmark_metal_ablation.py --run --output /tmp/libwebp-metal-experiment-4-run-20260817T191001Z --input mitski=<fixed-canonical-mitski.png> --input corgi=<fixed-canonical-corgi.jpeg> --input siamese=<fixed-canonical-siamese.jpg>
```

`WEBP_ENABLE_METAL=1` was effective from the Darwin makefile default; it was not supplied as an extra experiment flag. The only external experiment build flag was `WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1`. The only timed runtime flags were `WEBP_BENCHMARK_SESSION=exclusive` and `WEBP_METAL_ABLATION_EXPERIMENT=1`. Encoder-stage-profile, crossover, batch, predictor, legacy umbrella, and other experiment flags were absent. Ablation knobs came only from the committed harness `BASE_ENV` and one-variant deltas.

## Timing phases

- Operator/preflight start: `2026-08-17T19:10:01Z`.
- Clean/build boundary: `2026-08-17T19:12:57Z` to `2026-08-17T19:13:22Z` (25 seconds).
- Untimed manifest/correctness/guard phase: `2026-08-17T19:13:32Z` to `2026-08-17T19:18:05Z` (273 seconds).
- Full-matrix timed command: `2026-08-17T19:19:40Z` to `2026-08-17T19:37:08Z` (1,048 seconds; 17m28s).
- No second matrix, calibration workload, or timing-based early stop was used.

## Fixed matrix and mechanical validation

- Suites: `recorded`, `transform`, `hash`, `lossy`.
- Methods: 4 and 6; cwebp trials: 7; warmed import processes: 3.
- Inputs: fixed classes `mitski`, `corgi`, `siamese`; their committed hashes are recorded in `preflight.json` and `metadata.json`.
- Candidates: transform 4, hash 5, lossy 6; 15 candidate variants and 19 case entries including suite baselines.
- Pair blocks: transform 168, hash 210, lossy 36, total 414.
- Timed invocation records: 870; raw records: 3,822; summary groups: 138.
- Validation: 85/85 checks passed, including schema/matrix completeness, fixed input hashes, zero exits, lossless bitstream equality, import checksum equality, deterministic outputs, deterministic alternating order, exact environment isolation/reset, no forbidden external flags, ablation guard probe, and forced-Metal dispatch evidence.

The untimed correctness gate observed all required forced Metal operations and passed decoded CPU/Metal equality plus all committed variant byte-equality checks. The raw harness output was not modified; repository copies redact only absolute corpus paths, temporary paths, and sensitive hardware identifiers.

## Outputs and hashes

Original output directory: `/private/tmp/libwebp-metal-experiment-4-run-20260817T191001Z`.

| File | Original SHA-256 | Committed sanitized SHA-256 |
|---|---|---|
| `metadata.json` | `c2f746e69552c745c561688f0dfc677a9d2ba8dfe99998e47fa3f71558a9c2fb` | `59e634300af0cadc0e3b2a3166d806f2454844fba87bb8ffae19127c6ebcfc78` |
| `matrix.json` | `73196aa185db07aa1a70eb40d3349fec137cb37e1d19dcdfd2e63fad22138b80` | `73196aa185db07aa1a70eb40d3349fec137cb37e1d19dcdfd2e63fad22138b80` |
| `raw_results.jsonl` | `8f873f89b541a109a08f6ecbc2c1d4dd7dfef1c1e6dafe2d085b17458396d1da` | `284571cc0186d62405e73f1dd16e651ae7a1588cadf4be908ef376fa3f4c1c1c` |
| `summary.json` | `e8cb44c5708214cb767664305c39ade6a8388a84f445227c76fff8cbc257589d` | `e8cb44c5708214cb767664305c39ade6a8388a84f445227c76fff8cbc257589d` |

Committed files are under this directory: `preflight.json`, `metadata.json`, `matrix.json`, `raw_results.jsonl`, `summary.json`, `validation.json`, and this report.

## Handoff

Sol may later interpret the timing samples and ratios in the sanitized `summary.json`/`raw_results.jsonl`, compare candidates under the released protocol, and make any research recommendation. This operator report makes no performance conclusion.
