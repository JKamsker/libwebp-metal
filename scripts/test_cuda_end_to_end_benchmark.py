#!/usr/bin/env python3
"""Unit tests for CUDA end-to-end benchmark aggregation and reporting."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).with_name("benchmark_cuda_end_to_end.py")
SPEC = importlib.util.spec_from_file_location("cuda_e2e", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
cuda_e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cuda_e2e)


def synthetic_rows():
    persistent = []
    single = []
    for format_index, image_format in enumerate(cuda_e2e.FORMATS):
        for mode_index, mode in enumerate(cuda_e2e.MODES):
            base = 100.0 + 100.0 * format_index + 20.0 * mode_index
            for variant, factor in (("cpu", 1.0), ("cuda", 0.8)):
                for _ in range(5):
                    persistent.append(
                        {
                            "format": image_format,
                            "mode": mode,
                            "variant": variant,
                            "ns_per_image": base * factor * 1e6,
                            "batch_size": 24,
                            "output_bytes": 24 * 1000 * (
                                1.1 if variant == "cuda" else 1.0
                            ),
                        }
                    )
                for repetition in range(5):
                    for input_name in cuda_e2e.CASE_NAMES:
                        single.append(
                            {
                                "format": image_format,
                                "mode": mode,
                                "variant": variant,
                                "repetition": repetition,
                                "input": input_name,
                                "elapsed_ns": base * factor * 1e6,
                                "output_bytes": 1000 * (
                                    1.1 if variant == "cuda" else 1.0
                                ),
                            }
                        )
    return persistent, single


def measured_summary():
    values = (
        ("png", "lossy", "batch", 101.9, 103.2),
        ("png", "lossy", "single", 107.6, 313.5),
        ("png", "lossless", "batch", 141.2, 102.5),
        ("png", "lossless", "single", 158.1, 350.3),
        ("png", "near-lossless", "batch", 202.901, 162.969),
        ("png", "near-lossless", "single", 355.7, 526.4),
        ("jpeg", "lossy", "batch", 101.4, 100.2),
        ("jpeg", "lossy", "single", 108.0, 310.9),
        ("jpeg", "lossless", "batch", 667.7, 602.0),
        ("jpeg", "lossless", "single", 731.3, 875.7),
        ("jpeg", "near-lossless", "batch", 778.1, 687.6),
        ("jpeg", "near-lossless", "single", 554.0, 860.6),
    )
    return [
        {
            "format": image_format,
            "mode": mode,
            "lifecycle": lifecycle,
            "cpu_ms_per_image": cpu,
            "cuda_ms_per_image": cuda,
            "speedup": cpu / cuda,
        }
        for image_format, mode, lifecycle, cpu, cuda in values
    ]


def main() -> int:
    persistent, single = synthetic_rows()
    summary = cuda_e2e.summarize(persistent, single)
    assert len(summary) == 12
    assert all(abs(row["speedup"] - 1.25) < 1e-12 for row in summary)
    assert all(abs(row["cuda_size_ratio"] - 1.1) < 1e-12 for row in summary)
    report = cuda_e2e.render_markdown(summary, 24)
    assert (
        "Times are milliseconds per image. Batch uses a persistent 24-item "
        "process" in report
    )
    assert "| PNG lossy — batch | 100.0 ms | 80.0 ms | **1.25×** |" in report
    assert (
        "| JPEG near-lossless — single | 240.0 ms | 192.0 ms | **1.25×** |"
        in report
    )
    assert (
        "Bottom line: CUDA helps persistent lossless batches, is neutral for "
        "lossy batches, and is substantially worse when starting a fresh "
        "process for each image." not in report
    )
    assert (
        "Bottom line: CUDA helps persistent lossy, lossless, near-lossless "
        "batches" in report
    )
    measured_report = cuda_e2e.render_markdown(measured_summary(), 24)
    tick = chr(96)
    expected = f"""Times are milliseconds per image. Batch uses a persistent 24-item process; single starts a new {tick}cwebp{tick} process per image. Speedup above {tick}1×{tick} favors CUDA.

| Method | CPU time | CUDA time | Speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 101.9 ms | 103.2 ms | 0.99× |
| PNG lossy — single | 107.6 ms | 313.5 ms | 0.34× |
| PNG lossless — batch | 141.2 ms | 102.5 ms | **1.38×** |
| PNG lossless — single | 158.1 ms | 350.3 ms | 0.45× |
| PNG near-lossless — batch | 202.9 ms | 163.0 ms | **1.25×** |
| PNG near-lossless — single | 355.7 ms | 526.4 ms | 0.68× |
| JPEG lossy — batch | 101.4 ms | 100.2 ms | 1.01× |
| JPEG lossy — single | 108.0 ms | 310.9 ms | 0.35× |
| JPEG lossless — batch | 667.7 ms | 602.0 ms | **1.11×** |
| JPEG lossless — single | 731.3 ms | 875.7 ms | 0.84× |
| JPEG near-lossless — batch | 778.1 ms | 687.6 ms | **1.13×** |
| JPEG near-lossless — single | 554.0 ms | 860.6 ms | 0.64× |

Bottom line: CUDA helps persistent lossless batches, is neutral for lossy batches, and is substantially worse when starting a fresh process for each image.
"""
    assert measured_report == expected

    original_command_output = cuda_e2e.command_output
    cuda_e2e.command_output = lambda command: ""
    try:
        metadata = cuda_e2e.system_metadata(
            SimpleNamespace(label=None), "test-pillow"
        )
    finally:
        cuda_e2e.command_output = original_command_output
    assert metadata["label"].endswith(" / unknown gpu")
    assert metadata["gpu"] == ""

    with tempfile.TemporaryDirectory() as directory:
        verification = Path(directory) / "verification.json"
        verification.write_text(
            json.dumps(
                {
                    "schema": cuda_e2e.SCHEMA,
                    "configuration": {"verify_only": True},
                    "corpus": [],
                }
            ),
            encoding="utf-8",
        )
        try:
            cuda_e2e.report_results(
                SimpleNamespace(results=[verification], output=None)
            )
        except RuntimeError as error:
            assert "verify-only results contain no summary" in str(error)
        else:
            raise AssertionError("verify-only report input was accepted")
    print("PASS: CUDA end-to-end benchmark aggregation and Markdown report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
