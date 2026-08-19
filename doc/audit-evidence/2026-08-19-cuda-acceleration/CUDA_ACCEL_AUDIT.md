# CUDA encoder acceleration audit

**Target:** `libwebp-metal-codex-cuda-encoder-acceleration`  
**Scope:** CUDA encoder backend, its accelerator ABI integration, lossy-decimate CUDA unit, CMake/Autotools packaging, and CUDA-specific tests/benchmarks.  
**Method:** complete source review of `src/enc/cuda_enc.cu`, `src/enc/cuda_decimate_enc.cu`, `src/enc/cuda_decimate_dsp.cuh`, accelerator call sites, CPU reference implementations, and build/test files; CPU build; release-archive reproduction; deterministic host-side models of the streaming and stride contracts.

## Bottom line

I found **18 confirmed defects**, **4 confirmed compression-quality divergences**, and **4 additional build/test hardening issues**. The most serious defects are concentrated in the experimental lossy-decimate stage:

1. malformed but structurally valid ABI requests can drive device out-of-bounds reads;
2. valid image heights can create advertised bands with negative row counts, unrecorded completion events, and huge copy sizes;
3. caller-supplied reconstruction strides are ignored;
4. output buffers are modified before the function knows it will return `SUCCESS`;
5. result bytes are copied from uninitialized shared memory;
6. device selection and cross-thread CUDA context handling are inconsistent with the rest of the backend.

The default CUDA-enabled release configuration also cannot be rebuilt from the generated source tarball, because both decimate implementation files are missing from `make dist`.

## Confidence and limitations

The defects marked **source-proven** follow directly from control flow, integer arithmetic, ABI text, or a reproduced build artifact. The host proofs in `cuda_audit_evidence/` model the exact arithmetic/copy sequence without requiring a GPU. This environment had **no `nvcc`, NVIDIA driver, GPU, or Compute Sanitizer**, so I could not run kernels, compare CPU/GPU output on real images, or use racecheck/memcheck. Consequently, this is exhaustive for the reviewed source and integration surfaces, but not a claim that no additional hardware-dependent defect exists.

---

# Confirmed defects

## C-01 — Decimate ignores `WEBP_CUDA_DEVICE`

**Severity:** High for multi-GPU deployments  
**Proof:** source-proven

The main backend parses `WEBP_CUDA_DEVICE` in `cuda_enc.cu:323-335` and stores it during initialization at `cuda_enc.cu:2141`. The decimate backend instead initializes `DecimateState::device` to zero at `cuda_decimate_enc.cu:1271` and never parses the environment variable. It therefore always calls `cudaSetDevice(0)` at `cuda_decimate_enc.cu:1314/1549`.

**Impact:** The advertised single “cuda” backend can split one encode across two different GPUs. `WEBP_CUDA_DEVICE=1` selects GPU 1 for color/hash/predictor/RGB/analysis but GPU 0 for decimation. On systems where device 0 is unavailable, prohibited, full, or a different architecture, the decimate stage fails despite the selected device being usable.

**Fix:** Parse the device once and share one state/device selection across every CUDA stage, or pass the selected device into the decimate state.

## C-02 — Decimate uses the current CUDA device incorrectly across host threads

**Severity:** High  
**Proof:** source-proven from CUDA host-thread semantics

`DecimateInitialize()` selects a device only on the thread that performs initialization. `COLLECT` never calls `cudaSetDevice` (`cuda_decimate_enc.cu:1426-1509`). `BEGIN/WHOLE` calls `DecimateEnsureTables()` before reselecting the device (`1548` before `1549`). The mutex serializes calls but does not transfer the calling thread's current CUDA device. NVIDIA defines the current device/context in terms of the **calling host thread**, and states that streams/events created by that thread are associated with the selected device [NVIDIA Device API; NVIDIA Runtime Contexts].

**Impact:** A prewarm thread can create streams/events/allocations on device 0, while a later encoder thread has another current device. The collect thread can then wait on events or issue copies while the wrong device is current. Depending on runtime/context state this yields invalid-resource errors, quarantine, or use of unintended-device allocations.

**Fix:** Call `cudaSetDevice(state->device)` immediately after taking the decimate mutex in every entry path, including `COLLECT`, and before every API call that touches decimate resources.

## C-03 — Decimate boolean environment variables disagree with the rest of the backend

**Severity:** Medium  
**Proof:** executable host proof

The main parser treats `0`, `false`, and `no` case-insensitively as disabled (`cuda_enc.cu:255-260`). `DecimateFlag()` disables only the exact string `0` (`cuda_decimate_enc.cu:1300-1304`). Therefore:

```text
WEBP_CUDA=false                  main disabled, decimate enabled
WEBP_CUDA_LOSSY_DECIMATE=no     decimate enabled
```

The exact parser comparison is reproduced in `cuda_audit_evidence/host_proofs.json`.

**Impact:** Operators can believe CUDA is disabled while the decimate CUDA path still initializes a context and runs kernels.

**Fix:** Reuse `EnvironmentFlag()` rather than maintaining a second parser.

## C-04 — Decimate request validation permits multiple device out-of-bounds paths

**Severity:** High  
**Proof:** source-proven; caller-triggerable through the accelerator ABI

The host validation at `cuda_decimate_enc.cu:1416-1423` checks only null pointers and positive width/height/MB dimensions. It does not validate:

- `mb_w == ceil(width / 16)` and `mb_h == ceil(height / 16)`;
- source strides against plane widths, or reject negative strides;
- reconstruction strides;
- segment IDs are in `0..3`;
- `phase`, `band_count`, and collection order;
- arithmetic overflow while constructing the arena.

Concrete device faults follow:

1. A too-large `mb_w` makes `iw = width - x*16` negative (`cuda_decimate_enc.cu:451-454`). The parallel importer then evaluates `min(c, iw - 1)` and indexes before the uploaded source (`458-467`).
2. Any segment byte greater than 3 indexes beyond the four uploaded segment records at `cuda_decimate_enc.cu:682`.
3. A negative `y_stride` or `uv_stride` is cast to `size_t` at `1554-1556`, producing a huge upload/allocation calculation.
4. Arena offsets repeatedly use unchecked `AlignUp(value + 255)` and additions (`1399`, `1567-1583`), so oversized fields can wrap and cause overlapping slices or undersized allocations.

**Internal-path qualification:** The current `frame_enc.c` call site derives geometry, tight output strides, and segment IDs from trusted encoder state, so the normal in-tree path avoids several of these inputs. The ABI callback itself nevertheless advertises a complete callable contract and returns `ERROR` for invalid requests; it must not launch unsafe work for malformed requests.

**Fix:** Centralize checked multiplication/addition, enforce exact macroblock geometry, validate all strides and enum values, scan segment IDs on the host, and reject bad band geometry.

## C-05 — Reconstruction output strides are ignored

**Severity:** High ABI correctness defect  
**Proof:** source-proven and executable host model

The ABI explicitly supplies `recon_y_stride` and `recon_uv_stride` (`accelerator_enc.h:282-290`). The backend instead hardcodes tight device strides:

```cpp
params.recon_y_stride = request->mb_w * 16;
params.recon_uv_stride = request->mb_w * 8;
```

at `cuda_decimate_enc.cu:1649-1650`. Both whole-pass and band collection copy the reconstructed planes as flat, tightly packed byte arrays (`1470-1491`, `1728-1744`).

**Impact:** Any valid caller using padded rows receives rows at the wrong offsets; padding is overwritten and later rows are shifted. The simple `4x3` plane / stride `7` reproduction in `host_proofs.json` has `equal: false` and prints the actual versus required row layout.

**Current-call-site qualification:** `frame_enc.c:674-675` happens to allocate tight planes, masking this defect in the current encoder path.

**Fix:** Either honor the request strides in the kernel and use `cudaMemcpy2DAsync` for output, or remove the stride fields and formally constrain the ABI to tight output.

## C-06 — Valid frame heights produce empty advertised bands, unrecorded events, and underflowed copies

**Severity:** High  
**Proof:** source-proven and executable host arithmetic proof

For `mb_h >= 16`, the caller always advertises eight bands (`frame_enc.c:699-700`). Rows per band are ceiling-divided. Example: `mb_h=17` gives `rows_per_band=3`; bands 0–5 contain rows, while bands 6 and 7 start beyond row 17.

The launch loop computes each band's completion diagonal using a clamped `end_row` and breaks after the first matching band (`cuda_decimate_enc.cu:1676-1683`). The last three bands all map to the same final diagonal; only band 5's event is recorded. Bands 6 and 7 remain unrecorded. NVIDIA explicitly states that callers must ensure `cudaEventRecord()` has occurred because waiting on or querying a non-recorded event always reports success [NVIDIA Events].

If the ABI caller collects band 6, collection computes:

```text
row_start = 6 * 3 = 18
row_end   = min(21, 17) = 17
row_end - row_start = -1
```

That negative value is cast to `size_t` in the copy sizes at `1467/1476/1483/1490`, creating an enormous device-to-host copy request. The exact eight-band table is in `host_proofs.json`.

The in-tree caller avoids collecting empty bands because it stops after satisfying the last real macroblock row (`frame_enc.c:571-578`). However, the backend clears `pass_pending` only when the *advertised final band* is collected (`cuda_decimate_enc.cu:1503-1505`). Thus the successful in-tree pass remains pending forever and the next `BEGIN/WHOLE` performs an unnecessary stale drain (`1542-1546`).

**Fix:** Set `effective_band_count = min(requested_band_count, mb_h)`, record every matching band rather than breaking after one, reject empty collections, and clear pending state after the last non-empty band.

## C-07 — Decimate violates the ABI's transactional-output guarantee

**Severity:** High  
**Proof:** source-proven and sequence model

The descriptor advertises `WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT` (`cuda_enc.cu:3963-3970`), whose ABI definition requires caller-owned output to remain unchanged on `NOT_RUN/ERROR` (`accelerator_enc.h:46-47`). Decimate copies directly into caller buffers before all operations have succeeded:

- `WHOLE`: results, Y, U, and V are enqueued directly to caller memory and only then is the stream synchronized (`cuda_decimate_enc.cu:1728-1753`).
- `COLLECT`: results and three planes are likewise copied sequentially before final synchronization (`1463-1501`).

A failure in the third copy or final synchronization can return `ERROR` after earlier buffers were already changed. `host_proofs.json` models this sequence and shows the transactional predicate is false.

**Fix:** Copy into backend-owned host staging, synchronize, then commit to caller buffers with ordinary host copies. For streaming, stage one band at a time.

## C-08 — Decimate returns uninitialized shared-memory bytes and is not deterministic

**Severity:** Medium; possible information disclosure within the process  
**Proof:** source-proven

`MBWork w` is an uninitialized `__shared__` object (`cuda_decimate_enc.cu:664-667`). Its `DeviceResult rd` member is never zeroed (`359-405`). Fields are assigned piecemeal. In particular:

- `modes_i4[16]` is written only for blocks reached and committed by the I4 search (`1010`); it remains partially or wholly uninitialized when I4 aborts or is not selected;
- `reserved[2]` is never assigned anywhere;
- the entire struct is copied as 32-bit words to global memory (`1213-1220`) and then to the host.

The descriptor nevertheless advertises `DETERMINISTIC` (`cuda_enc.cu:3966`). Identical inputs can therefore expose stale shared-memory values in unused fields and produce bytewise-different result structs.

**Fix:** Zero `w.rd` cooperatively at kernel entry, synchronize, and/or explicitly initialize all padding/reserved/unused mode fields before export.

## C-09 — Decimate initialization leaks partially-created CUDA resources

**Severity:** Medium  
**Proof:** source-proven

`DecimateInitialize()` returns immediately on failures after creating earlier resources (`cuda_decimate_enc.cu:1315-1330`). Examples:

- if creation of `copy_stream` fails, `stream` is leaked;
- if event `n` fails, both streams and events `0..n-1` are leaked;
- if `timing_begin` succeeds and `timing_end` fails, the first event is retained (`1345-1349`).

`DecimateEnsureTables()` also retains `device_tables` when the upload fails (`1357-1379`). There is no rollback helper or destructor.

**Fix:** Use one cleanup path or an RAII state object; only mark initialization attempted after successful construction, or clean every partially initialized field before returning.

## C-10 — `trim`, `flush`, and end-of-encode do not manage decimate resources or in-flight work

**Severity:** Medium to High for lifecycle correctness  
**Proof:** source-proven

Decimate owns a separate global state, streams, events, arena, and table allocation (`cuda_decimate_enc.cu:1266-1297`). The backend descriptor's lifecycle callbacks point only at functions operating on `g_cuda_state` (`cuda_enc.cu:3900-3933`, `4022-4024`):

- `CUDAFlush()` synchronizes only the main stream, so it can return `SUCCESS` while a decimate `BEGIN` is still executing;
- `CUDATrim()` releases only main-backend staging; decimate's arena/tables/streams/events are never trimmed;
- `CUDAEndEncode()` invalidates only main resident caches and does not abandon/drain a pending decimate pass.

This also makes the `PERSISTENT_RESOURCES` property conditional inaccurate: when `WEBP_CUDA_ENABLE_PERSISTENT_BUFFERS=OFF`, the descriptor omits the property, but decimate still permanently retains resources.

**Fix:** Put decimate state under the descriptor context and include it in every lifecycle callback, with explicit shutdown/trim semantics.

## C-11 — Transient CUDA initialization failures are permanent for the process

**Severity:** Medium  
**Proof:** source-proven

Both initializers set `initialization_attempted = true` before querying devices or creating resources (`cuda_enc.cu:2127-2133`; `cuda_decimate_enc.cu:1306-1311`). Any transient runtime initialization error, temporary device unavailability, or initially invalid device selection permanently converts all later calls to `NOT_RUN` until process restart.

**Fix:** Distinguish permanent policy/configuration failures from retryable runtime errors; reset state after clean rollback or provide an explicit retry/reset operation.

## C-12 — Decimate timing mode defeats streaming

**Severity:** Medium performance/contract issue, debug configuration only  
**Proof:** source-proven

`BEGIN` is documented to launch without waiting (`accelerator_enc.h:240-247`). With `WEBP_CUDA_DECIMATE_TIMING` enabled, the backend records the end event and immediately calls `cudaEventSynchronize()` before setting `pass_pending` and returning (`cuda_decimate_enc.cu:1687-1725`). Thus `BEGIN` becomes fully synchronous and no CPU/GPU band overlap is possible.

**Fix:** Defer timing collection until the final band or a later flush; never synchronize inside `BEGIN`.

## C-13 — Invalid decimate threshold strings can silently disable the stage

**Severity:** Low  
**Proof:** source-proven

`WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS` is parsed with `atoll()` and cast directly to `size_t` (`cuda_decimate_enc.cu:1522-1525`). A negative string becomes a huge unsigned threshold; malformed text becomes zero. The main backend already has a checked `ParseEnvironmentSize()` implementation (`cuda_enc.cu:264-281`).

**Fix:** Reuse the checked parser and reject invalid values with a diagnostic.

## C-14 — Decimate success is never reflected in successful-stage telemetry

**Severity:** Low to Medium; test/benchmark correctness  
**Proof:** source-proven

Every main-stage wrapper sets its bit in `g_cuda_state.successful_stages` after `SUCCESS` (for example hash at `cuda_enc.cu:3302-3311`). The descriptor points directly to `WebPCUDALossyDecimate` (`4017-4019`), and that function never updates the bitset. Consequently `WebPCUDAGetSuccessfulStages()` can never report `WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE`, even after successful GPU decimation.

**Fix:** Add a wrapper under the main mutex or provide decimate-safe atomic telemetry.

## C-15 — Lossy-analysis availability probe returns false positives

**Severity:** Medium ABI integration defect  
**Proof:** source-proven

The ABI says `lossy_analysis(NULL)` returns `SUCCESS` only when a real request may be attempted under current policy (`accelerator_enc.h:311-313`). `CUDALossyAnalysisLocked()` returns `SUCCESS` immediately after environment checks (`cuda_enc.cu:3697-3701`), before checking quarantine, device availability, initialization, or profitability thresholds.

**Impact:** Dispatcher/call-site decisions can commit to a fused/accelerated path based on a device that does not exist or a backend already quarantined.

**Fix:** Make the probe run the non-mutating policy/device-availability checks, or revise the ABI to define the weaker meaning actually implemented.

## C-16 — Detached global prewarm thread is unsafe during dynamic-library unload

**Severity:** High when the shared library can be unloaded  
**Proof:** source-proven lifecycle race

A global constructor creates a detached thread (`cuda_enc.cu:2217-2233`). The thread executes functions and accesses global mutex/state in the shared object (`2188-2205`). There is no retained thread handle, join, cancellation, or library destructor.

**Impact:** A program that `dlclose()`s / unloads the library soon after loading it can unmap code and destroy globals while the detached thread is still executing, producing use-after-unload behavior. Closing the Windows thread handle likewise does not wait for completion.

**Fix:** Avoid work in a global constructor. Initialize lazily on a caller thread, or retain/join the worker and pin the module until completion.

## C-17 — Hash-chain ABI accepts links that make the kernel read outside uploaded arrays

**Severity:** High for untrusted/custom ABI callers  
**Proof:** source-proven

The host validates only non-null pointers, `size > 2`, positive `xsize`, and positive iteration count (`cuda_enc.cu:3154-3161`). The kernel trusts `chain[base_position]` as an array index (`1378`) and repeatedly reads `pixels[position + best_length]` and `chain[position]` (`1405-1420`) without verifying `0 <= position < base_position` or `< size`.

A chain entry equal to `size`, larger than `base_position`, or otherwise malformed causes immediate global-memory out-of-bounds reads. A non-decreasing/cyclic chain can also waste all iterations. Large `window_size` values can overflow the packed `best_distance << 12` result.

**Internal-path qualification:** The normal encoder supplies a CPU-generated predecessor chain and expected window bounds. The public accelerator callback still needs either explicit trusted-input documentation or validation.

**Fix:** Validate each predecessor while traversing (`position >= 0`, `< base_position`, `< size`, monotonically decreasing, within window), and validate the representable distance range.

## C-18 — Persistent resident handoffs use pointer identity as content identity

**Severity:** Low to Medium; conditional ABI correctness  
**Proof:** source-proven

Hash and lossy-analysis reuse resident device buffers when host pointer, dimensions, and counts match (for example `cuda_enc.cu:3191-3198`), without any generation token or content fingerprint. Borrowed input buffers can legally be reused and overwritten between accelerator calls. A later request with the same address but new pixels can therefore consume stale device content.

The current encoder pipeline intentionally exploits immediate handoffs and appears not to mutate those buffers between the paired stages, so this is primarily an ABI/general-reuse defect rather than a demonstrated in-tree encode failure.

**Fix:** Make residency an explicit one-shot handoff token owned by the dispatcher, invalidate at every unrelated call/end boundary, or require a generation identifier.

---

# Confirmed compression-quality divergences

These produce valid encodings, not memory corruption. The repository documentation allows CUDA output to differ byte-for-byte from the CPU encoder, but these differences remove parts of the CPU optimizer and can increase file size.

## Q-01 — Predictor stage never searches the allowed transform-grid sizes

CUDA constructs exactly one grid at `request->max_bits` (`cuda_enc.cu:2918-2933`) and unconditionally writes `*best_bits = max_bits` (`3093`). The CPU implementation evaluates every subsampling index from `min_bits` through `max_bits` and chooses the minimum total cost (`predictor_enc.c:749-765`). A request with `min_bits < max_bits` therefore cannot receive the CPU-optimal grid from CUDA.

## Q-02 — Predictor scoring omits left-neighbor mode bias and updates history only per row

CPU scoring includes both the left and above modes (`predictor_enc.c:342-376`) and immediately folds each selected tile into the accumulated histogram. CUDA reads only the mode above (`cuda_enc.cu:806-811`, bias at `870-872`) and evaluates all tiles in a row against the same pre-row accumulator, folding winners only in a later row kernel (`885-929`, launches at `3000-3055`). Tile decisions are therefore not equivalent to CPU scan order, even before floating-point approximation.

## Q-03 — Predictor cost/tie behavior uses floating point instead of the CPU fixed-point model

CUDA uses `double`/`log2`-based entropy and floating-point bias calculations in predictor selection; CPU uses integer entropy/cost functions and exact tie ordering. Near equal candidates can choose different modes and propagate different history to following tiles.

## Q-04 — Color transform removes spatial and accumulated-histogram guidance

The CPU cross-color optimizer passes both left and above multipliers and accumulated red/blue histograms into each tile search (`predictor_enc.c:910-1081`, `1105-1157`). CUDA's color kernel scores each tile independently with local histograms and floating-point entropy (`cuda_enc.cu:376-586`), without those neighboring multipliers or global accumulators. This is a deliberate simplification but can produce materially worse transform choices on spatially coherent images.

---

# Build, packaging, and test issues

## B-01 — `make dist` omits required default-CUDA source files

**Severity:** High release blocker  
**Proof:** reproduced

CMake enables `WEBP_CUDA_ENABLE_LOSSY_DECIMATE` by default when CUDA is enabled and appends `cuda_decimate_enc.cu` (`CMakeLists.txt:151-154`, `499-503`). Autotools `EXTRA_DIST` lists only `cuda_enc.cu cuda_enc.h` (`src/enc/Makefile.am:38-40`).

I ran `autoreconf -fi`, `configure`, and `make dist`. The resulting `libwebp-1.6.0.tar.gz` contains:

```text
src/enc/cuda_enc.h
src/enc/cuda_enc.cu
```

and omits both `cuda_decimate_enc.cu` and `cuda_decimate_dsp.cuh`. See `cuda_audit_evidence/release_cuda_manifest.txt` and the three `cuda-dist-*.log` files.

**Impact:** A release tarball cannot build the default CUDA configuration.

**Fix:** Add both files to `EXTRA_DIST` and add a CI job that configures CUDA from `make dist` output.

## B-02 — Default `CMAKE_CUDA_ARCHITECTURES=native` makes release artifacts build-host-specific

**Severity:** Medium deployment/build issue

When no architecture is supplied and CMake is at least 3.24, the project forces `native` (`CMakeLists.txt:118-124`). CMake defines `native` as compiling for the architecture(s) of the host's GPU(s), and documents that the special value was added in 3.24 [CMake CUDA_ARCHITECTURES; CMake 3.24 notes]. This is unsuitable as an unconditional default for GPU-less builders, cross-compilation, and redistributable packages intended for a range of NVIDIA architectures.

**Fix:** Require packagers to specify an architecture list, or choose a documented baseline SASS+PTX policy; reserve `native` for local benchmark builds.

## B-03 — CUDA tests are executables, not CTest tests, and decimate has no correctness test

**Severity:** Medium quality gap  
**Proof:** source/build reproduced

`cuda_concurrency_test`, `cuda_histogram_test`, and `cuda_near_lossless_test` are created only under `WEBP_BUILD_CUDA_BENCHMARK` (`CMakeLists.txt:993-1027`), but no `add_test()` registers them. There is no decimate correctness/stride/band/device test at all, and no CUDA workflow under `.github`.

A CPU build succeeded, but `ctest` reported `No tests were found!!!`; see `cuda_audit_evidence/cpu-*.log`. The CUDA-specific shell script executes some binaries manually, but it does not exercise lossy decimate.

**Fix:** Add `enable_testing()`/`add_test()`, device-conditional skips, and focused tests for padded strides, every `mb_h mod band_count`, invalid segments/geometry, multi-thread/multi-device calls, and transactional failure injection.

## B-04 — Installed pkg-config metadata hardcodes a toolkit library directory

**Severity:** Low to Medium packaging issue

CMake sets `CUDA_LIBS` to `-L${CUDAToolkit_LIBRARY_DIR} -lcudart` (`CMakeLists.txt:131`), and `src/libwebp.pc.in` places it in `Libs.private`. This embeds the build machine's absolute CUDA toolkit path in installed static-link metadata, even though the CMake target correctly links `CUDA::cudart` (`CMakeLists.txt:750-752`).

**Fix:** Avoid absolute build-host paths in `.pc`; use an appropriate stable linker token/dependency mechanism or do not expose private CUDA linkage for configurations that cannot support it portably.

## B-05 — CUDA private helper symbols are likely exported from shared builds

**Severity:** Low; hardening/ABI-surface issue  
**Proof status:** source-indicated, not binary-verified because no CUDA compiler was available

The project sets hidden visibility for Objective-C++/Metal but does not set `CMAKE_CUDA_VISIBILITY_PRESET`. Several CUDA helper/test entry points use plain `extern "C"` without a private visibility annotation, including `WebPGetCUDAEncoderAccelerator` and telemetry helpers. On toolchains using default visibility these become unintended shared-library exports.

**Fix:** Set CUDA visibility to hidden and explicitly export only supported public ABI symbols.

## B-06 — Experimental CUDA stages are enabled by default once CUDA is enabled

**Severity:** Low policy risk

Both histogram and lossy decimate are described as experimental but default to `ON` (`CMakeLists.txt:151-154`). Given the untested ABI and memory-safety defects above, an opt-in backend enables the least mature stages automatically.

**Fix:** Default experimental stages off until covered by GPU CI and contract tests.

---

# Checked areas where I did not find a concrete defect

- The lossy-analysis CPU and CUDA code both intentionally evaluate the same limited intra-mode set; the apparent two-mode restriction is not a CUDA-only mismatch.
- Near-lossless validates dimensions/stride/quantization bounds and stages output before committing. I found no source-proven memory-safety defect there.
- Histogram validates command modes/ranges in the kernel, counts invalid commands, stages output, and checks the invalid count before commit. I found no concrete defect beyond missing test registration/hardware execution.
- RGB-to-YUV output copying honors caller strides and commits after synchronization. The remaining concern is only the conditional resident-buffer generation issue described in C-18.
- Anti-diagonal scheduling in decimate respects the apparent left/top reconstruction dependencies; I did not find a definite race from the schedule itself by source inspection.

---

# Recommended repair order

1. Disable `WEBP_CUDA_ENABLE_LOSSY_DECIMATE` by default immediately.
2. Fix C-04 through C-08: complete validation, band geometry/events, output strides, transactional staging, and result initialization.
3. Unify state/device/lifecycle handling (C-01, C-02, C-09 through C-11).
4. Add decimate GPU tests and Compute Sanitizer coverage before re-enabling it.
5. Fix hash-chain validation and prewarm unload safety.
6. Fix the release archive and architecture policy.
7. Decide whether predictor/color simplifications are acceptable; if yes, document expected compression deltas and enforce regression budgets.

# Reproduction artifacts

- `cuda_audit_evidence/reproduce_host_proofs.py` — deterministic parser/band/stride/transaction models.
- `cuda_audit_evidence/host_proofs.json` — generated proof output.
- `cuda_audit_evidence/assert_source_evidence.sh` — source assertions for the key defects.
- `cuda_audit_evidence/release_cuda_manifest.txt` — generated tarball's CUDA files.
- `cuda_audit_evidence/cuda-dist-*.log` — release archive reproduction logs.
- `cuda_audit_evidence/cpu-*.log` — successful CPU configuration/build and empty CTest result.
- `cuda_audit_evidence/toolchain.txt` — audit environment/tool availability.


# External references

- **[NVIDIA Device API]** NVIDIA CUDA Runtime API, Device Management: <https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html> (`cudaGetDevice` and `cudaSetDevice`).
- **[NVIDIA Runtime Contexts]** NVIDIA CUDA Runtime API, Driver/Runtime Context Interactions: <https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DRIVER.html>.
- **[NVIDIA Events]** NVIDIA CUDA Programming Guide, Advanced Host Programming / CUDA Events: <https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/advanced-host-programming.html>.
- **[CMake CUDA_ARCHITECTURES]** CMake documentation: <https://cmake.org/cmake/help/latest/prop_tgt/CUDA_ARCHITECTURES.html>.
- **[CMake 3.24 notes]** CMake 3.24 release notes: <https://cmake.org/cmake/help/latest/release/3.24.html>.
