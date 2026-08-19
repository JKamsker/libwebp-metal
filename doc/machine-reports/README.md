# Machine-specific benchmark reports

This directory is the canonical catalog for benchmark results tied to a
specific CPU, accelerator, operating system, and toolchain. Add new reports as
dated Markdown files and record the exact source revision and benchmark
configuration so results from different machines are not mistaken for a
same-machine comparison.

## Reports

| Date (UTC) | Backend | Machine | Report |
|---|---|---|---|
| 2026-08-18--19 | CUDA | AMD Ryzen 9 3900X / NVIDIA GeForce RTX 2080 SUPER | [End-to-end PNG/JPEG benchmark](2026-08-18-linux-ryzen-9-3900x-rtx-2080-super.md) |

## Older machine-specific records

These records predate this directory and remain at their original paths to
avoid rewriting historical evidence:

| Date | Backend | Machine | Record |
|---|---|---|---|
| 2026-08-18 | CUDA | NVIDIA GeForce RTX 5070 Ti Laptop GPU / Windows 11 | [Optimization-series results](../../CUDA_BENCHMARK_RESULTS.md#windows-rtx-5070-ti-laptop-results-2026-08-18) |
| 2026-08-18 | CUDA | NVIDIA GeForce RTX 2080 SUPER | [CUDA benchmark results](../../CUDA_BENCHMARK_RESULTS.md) |
| 2026-08-17 | Metal | Apple M4 Pro MacBook Pro | [Modern Metal migration results](../../BENCHMARK_RESULTS.md) |
