# Cache-size serial-sweep execution environment

This supplemental report records execution context outside the operator's
frozen output directory. The frozen raw output files are preserved unchanged
under `evidence/cache-size-serial-sweep/`.

## Frozen source and inputs

- Required parent/main: `76c34b682818186132269a13f3e645ecd9e7800d`
- Executed source commit: `69f349c8706e4181ba9ab169cc2bf42ec4c69863`
- Parent relationship: `69f349c8706e4181ba9ab169cc2bf42ec4c69863 76c34b682818186132269a13f3e645ecd9e7800d`
- Pre-execution worktree status: clean
- Validation command: `python3 scripts/run_cache_size_serial_sweep_experiment.py validate`
- Validation result: exit 0; schema `libwebp-cache-size-serial-sweep-frozen-v1`
- Manifest SHA-256: `25e55f841908a75c8362602b3d28e257a73ef4277c87bbbcdce6c5cd5438850f`
- Operator SHA-256: `e2081b69ab3d7b224967aa07c2c2a2d67f7b77d78a4c2817600dc62b7fec5a2b`
- Candidate source SHA-256: `a63d2efba154f4c395d2ac8e0fe19553794cc7c3657b6a2891866604765709ca`
- Runner SHA-256: `63c7523dd36d9860b3d8071d6685edfc8c1bed12cdee8cb32554938f4acef53e`
- Protocol SHA-256: `0755c0aff92c8bf897523700cc6ca33e0db92f4f508e98c8dc617ae8da956915`
- Corpus generator SHA-256: `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007`
- Publication manifest SHA-256: `34582ce2d2da7f14e3711280e1c2ab44ffc5fe460de4abac7c5696fc5b1875ff`

## Exact execution invocation

```text
WEBP_EXPECTED_CACHE_SIZE_SWEEP_COMMIT=69f349c8706e4181ba9ab169cc2bf42ec4c69863 WEBP_BENCHMARK_SESSION=exclusive python3 scripts/run_cache_size_serial_sweep_experiment.py run /Users/jonaskamsker/.codex/worktrees/f5cd/libwebp-metal/evidence/cache-size-serial-sweep
```

The command ran once and exited 0. The outer operator process emitted no
stdout or stderr bytes. The operator's preserved `build.log` contains the
build subprocess output; timed runner output is preserved in
`records.jsonl` and `commands.jsonl`.

## Machine, OS, SDK, compiler, and GPU

- Host: physical MacBook Pro `Mac16,7`, Apple M4 Pro, arm64
- CPU: 14 cores (10 performance, 4 efficiency)
- GPU: Apple M4 Pro, 20 cores, built-in; Metal support: Metal 4
- OS: macOS 26.5.1, build 25F80; Darwin 25.5.0
- Xcode: 26.3, build 17C529
- macOS SDK: `/Applications/Xcode-26.3.0.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk`
- Compiler: Apple clang 17.0.6.4.2 (`clang-1700.6.4.2`), target `arm64-apple-darwin25.5.0`
- CUDA: `nvcc` absent; the frozen build also set `WEBP_ENABLE_METAL=OFF`

## Preflight resource state

- Power: AC Power; internal battery 100% and charged
- Thermal: `pmset -g therm` reported no thermal warning, performance warning,
  or CPU power status
- Available memory reported by the operator preflight:
  `10283384832` bytes (minimum required `4294967296`)
- Evidence filesystem: `357937796` KiB available before execution (22% used),
  exceeding the 2 GiB evidence ceiling
- Inherited `WEBP_*`, compiler, SDK, CMake, and deployment-target overrides:
  none observed

## Frozen flags observed in the run

- Baseline: ordinary build with the candidate option absent/OFF
- Candidate build: `WEBP_BUILD_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=ON`
- Candidate compile macro: `WEBP_USE_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=1`
- Candidate runtime: `WEBP_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT=1`
- Failure injection was used only by the frozen correctness gate:
  `WEBP_CACHE_SIZE_SERIAL_SWEEP_INJECT_FAILURE=1`
- Timed session: `WEBP_BENCHMARK_SESSION=exclusive`
