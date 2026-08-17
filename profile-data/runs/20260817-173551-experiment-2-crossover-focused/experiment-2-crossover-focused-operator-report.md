# Experiment 2 CPU/Metal crossover focused operator report

Operator status: **completed-valid**.

The exact committed focused pipeline completed with exit status 0. No codec algorithm, preset, threshold, or policy file was modified. Performance ratios were not interpreted.

## Run identity and timing

- Required source base: `18fd520d5d7faf0645d461bded27c0ba7ee4a48e`.
- HEAD at launch: `0d925e3dd33daab83d3717e3763d36d91bcfdca7`.
- Worktree at launch: clean; operator raw metadata also records an empty Git status.
- Start: `2026-08-17T17:35:50Z` (`2026-08-17T19:35:50+0200`).
- End observed after process exit: `2026-08-17T18:24:26Z` (`2026-08-17T20:24:26+0200`).
- Observed wall runtime: `00:48:36` (2,916 seconds).
- Build, correctness, and smoke completed before operator metadata creation at `2026-08-17T17:35:56.286669Z`; the wrapper did not emit separate timestamps for those subphases. The timed matrix then ran until the observed end.

## Exact command and guards

```sh
WEBP_METAL_CROSSOVER_EXPERIMENT=1 WEBP_BENCHMARK_SESSION=exclusive scripts/run_metal_crossover_operator.sh
```

The wrapper executed:

```sh
make -f makefile.unix clean
make -f makefile.unix -j8 WEBP_ENABLE_METAL=1 \
  WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT=1 \
  CFLAGS='-O3 -DNDEBUG' CXXFLAGS='-O3 -DNDEBUG' \
  tools/webp_metal_benchmark examples/cwebp examples/dwebp
scripts/test_metal.sh
WEBP_METAL_CROSSOVER_EXPERIMENT=1 python3 scripts/benchmark_metal.py smoke \
  --runner tools/webp_metal_benchmark
python3 scripts/metal_crossover_operator.py run \
  --preset scripts/metal_crossover_focused_v1.json \
  --runner tools/webp_metal_benchmark \
  --output-dir "${TMPDIR}/libwebp-metal-crossover-20260817T173551Z" \
  --acknowledge-exclusive-session
```

Effective build flags were `WEBP_ENABLE_METAL=1`, `WEBP_BUILD_METAL_CROSSOVER_EXPERIMENT=1`, `CFLAGS=-O3 -DNDEBUG`, and `CXXFLAGS=-O3 -DNDEBUG`. Effective runtime flags were `WEBP_METAL_CROSSOVER_EXPERIMENT=1` and `WEBP_BENCHMARK_SESSION=exclusive`. All other experiment and legacy umbrella names were absent. The exclusive-session lease assertion, focused output non-overwrite check, and no-other-experiment process scan passed.

The untimed independent guard test passed:

```text
PASS: five independent build/runtime guards and fail-closed leases
```

The focused plan was unchanged: 424 pair blocks, 848 runner invocations, 1,648 measured records, 400 discarded warmup encodes, 2,048 total encodes, and 400 MiB maximum source input. The matrix retained 18 item-1 warm guard blocks and 36 item-1 backend/method reference hashes; transform photo methods 4/6 used six sizes with tune/holdout roles; photo and texture hash strata remained separate; palette graphics remained forced-dispatch guards; and lossy photo/graphic/texture ladders remained bounded at methods 4/6.

Preflight is recorded at `profile-data/operators/experiment-2-crossover-focused-20260817T173310Z/preflight.json` with SHA-256 `5d997a0083879cc09dc7ad15bbcd4ebc522f54794d3afb75ee48846f0f58fb30`.

Machine preconditions recorded in the sanitized preflight were AC power with a charged battery, no thermal/performance/CPU-power warning, 78% system-wide free memory, 360,397,052 KiB temporary/worktree disk available, active idle-sleep prevention, and no competing experiment operator. Architecture, logical CPU count, memory size, OS version, load average, sleep settings, and contention checks were recorded without committing hardware identifiers.

## Mechanical validation

- `validity.json`: `valid=true`.
- Pair blocks: `424/424`.
- Measured sample records: `1,648`.
- Expected/enforced warmup encodes: `400`.
- Summary groups: `248`.
- Runner invocations: `848`.
- Item-1 reference hash checks: `36/36`.
- CPU records with Metal markers: `0`.
- Metal marker mismatches: `0`.
- Within-backend repeated-hash determinism failures: `0`.
- Input-hash pair mismatches: `0`.
- Decoded-pixel equality contract failures: `0`.
- Required bitstream-equality contract failures: `0`.
- Lossless decode-to-input failures: `0`.
- Randomized pair-order or sequence-count contract failures: `0`.
- Policy: `status=untuned`, `fallback=cpu`, `entries=[]`.

The full machine-readable validation record is `validation_summary.json` in this directory.

## Original output and committed sanitized artifacts

Original output was preserved, unmodified, at:

`/private/var/folders/g_/y0l39t0x5q39xs0msnnn7hb80000gn/T/libwebp-metal-crossover-20260817T173551Z`

Original file SHA-256 values:

- `raw.jsonl`: `a4415fea51c105068e67c0d0de4c40527485d713f317d37abae65149fd9326e4`
- `summary.json`: `85132eaf03efbb11f73ab1a39a88197a08cd967afe021775cd6661d1612db6d9`
- `validity.json`: `1b3428e3f6f409a9025629b2892d5e668055f35a57b45322df32f68defa09641`
- `policy-untuned.json`: `eb4febb7688cd57b1e27a76ae19cd745450b77cd01613c7d5795d12e3c540d06`

Committed copies are sanitized only for metadata/path disclosure; sample records and mechanical validity content are preserved:

- `raw.jsonl`: `ab39ee2857a79f9699c3b54fd69fac7705c91cdf35cb06ab174916aef12a2184`
- `summary.json`: `6e0beb8e014439b5692f5e02334e9257ee9070158af5bfd1cd5d85740bb58f6c`
- `validity.json`: `1b3428e3f6f409a9025629b2892d5e668055f35a57b45322df32f68defa09641`
- `policy-untuned.json`: `22c186267c07399d471387695bb068a12dfb097b4b892a8d3b668e06a9336cfa`

The committed `raw.jsonl` omits metadata hardware, machine, and power fields and replaces local absolute preset/runner paths. The original output hashes above were rechecked after sanitization, and every original sample record is identical to its committed sanitized counterpart.

Sol owns all later ratio interpretation, tune/holdout assessment, candidate/threshold decisions, and any policy change. This operator made none of those decisions.
