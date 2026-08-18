#!/usr/bin/env python3
"""Run and compare reproducible CPU/CUDA file-to-WebP batch benchmarks."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import random
import shutil
import socket
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


SCHEMA = "libwebp-cuda-end-to-end-benchmark-v1"
FORMATS = ("png", "jpeg")
MODES = ("lossy", "lossless", "near-lossless")
VARIANTS = ("cpu", "cuda")
CASE_NAMES = (
    "photo-small",
    "graphic-small",
    "texture-small",
    "photo-medium",
    "graphic-medium",
    "texture-medium",
)
ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_publication_corpus.py"
CUDA_ENVIRONMENT_NAMES = (
    "WEBP_ACCELERATOR",
    "WEBP_CUDA",
    "WEBP_CUDA_DEVICE",
    "WEBP_CUDA_VERBOSE",
    "WEBP_CUDA_TIMING",
    "WEBP_CUDA_HANDOFF_MARKERS",
    "WEBP_CUDA_COLOR",
    "WEBP_CUDA_HASH",
    "WEBP_CUDA_LOSSY",
    "WEBP_CUDA_NEAR_LOSSLESS",
    "WEBP_CUDA_LOSSY_ANALYSIS",
    "WEBP_CUDA_FUSED_LOSSY_ANALYSIS",
    "WEBP_CUDA_RESIDENT_LOSSLESS",
    "WEBP_CUDA_PREDICTOR",
    "WEBP_CUDA_HISTOGRAM",
    "WEBP_CUDA_MIN_PIXELS",
    "WEBP_CUDA_HASH_MIN_PIXELS",
    "WEBP_CUDA_LOSSY_MIN_PIXELS",
    "WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS",
    "WEBP_CUDA_LOSSY_ANALYSIS_MIN_MACROBLOCKS",
    "WEBP_CUDA_PREDICTOR_MIN_PIXELS",
    "WEBP_CUDA_HISTOGRAM_MIN_COMMANDS",
    "WEBP_CUDA_BATCH_SIZE",
    "WEBP_CUDA_BATCH_PIXELS",
    "WEBP_CUDA_BATCH_MIN_IMAGES",
    "WEBP_CUDA_BATCH_MIN_PIXELS",
    "WEBP_CUDA_NEAR_LOSSLESS_BATCH_MIN_IMAGES",
    "WEBP_CUDA_NEAR_LOSSLESS_BATCH_MIN_PIXELS",
    "WEBP_CUDA_HASH_BATCH_MIN_PIXELS",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except OSError as error:
        return f"unavailable: {error}"
    return completed.stdout.strip()


def run_checked(
    command: list[str], *, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def observed_resident_lossless_handoff(stderr: str) -> bool:
    return any(
        line.startswith("WebP-CUDA: hash candidates")
        and "(resident pixels)" in line
        for line in stderr.splitlines()
    )


def clean_environment(
    variant: str, force_cuda: bool, cuda_device: Optional[int]
) -> dict[str, str]:
    environment = os.environ.copy()
    for name in CUDA_ENVIRONMENT_NAMES:
        environment.pop(name, None)
    environment["WEBP_ACCELERATOR"] = "none" if variant == "cpu" else "cuda"
    environment["WEBP_CUDA"] = "0" if variant == "cpu" else "1"
    if cuda_device is not None:
        environment["WEBP_CUDA_DEVICE"] = str(cuda_device)
    if variant == "cuda" and force_cuda:
        environment.update(
            {
                "WEBP_CUDA_COLOR": "1",
                "WEBP_CUDA_HASH": "1",
                "WEBP_CUDA_LOSSY": "1",
                "WEBP_CUDA_NEAR_LOSSLESS": "1",
                "WEBP_CUDA_LOSSY_ANALYSIS": "1",
                "WEBP_CUDA_FUSED_LOSSY_ANALYSIS": "1",
                "WEBP_CUDA_RESIDENT_LOSSLESS": "1",
                "WEBP_CUDA_PREDICTOR": "1",
                "WEBP_CUDA_HISTOGRAM": "1",
                "WEBP_CUDA_MIN_PIXELS": "0",
                "WEBP_CUDA_HASH_MIN_PIXELS": "0",
                "WEBP_CUDA_LOSSY_MIN_PIXELS": "0",
                "WEBP_CUDA_NEAR_LOSSLESS_MIN_PIXELS": "0",
                "WEBP_CUDA_LOSSY_ANALYSIS_MIN_MACROBLOCKS": "0",
                "WEBP_CUDA_PREDICTOR_MIN_PIXELS": "0",
                "WEBP_CUDA_HISTOGRAM_MIN_COMMANDS": "0",
            }
        )
    return environment


def load_generator() -> Any:
    specification = importlib.util.spec_from_file_location(
        "publication_corpus", GENERATOR
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def prepare_corpus(
    output: Path,
) -> tuple[dict[str, list[Path]], list[dict[str, Any]], str]:
    try:
        from PIL import Image, __version__ as pillow_version
    except ImportError as error:
        raise RuntimeError(
            "Pillow is required to create deterministic PNG/JPEG inputs; "
            "install it in a disposable virtual environment"
        ) from error

    ppm_dir = output / "ppm"
    png_dir = output / "png"
    jpeg_dir = output / "jpeg"
    png_dir.mkdir(parents=True, exist_ok=True)
    jpeg_dir.mkdir(parents=True, exist_ok=True)
    generator = load_generator()
    manifest = generator.generate(ppm_dir)
    generator.verify(manifest, generator.CANONICAL_MANIFEST)

    paths: dict[str, list[Path]] = {"png": [], "jpeg": []}
    records: list[dict[str, Any]] = []
    cases = {case["case_id"]: case for case in manifest["cases"]}
    for name in CASE_NAMES:
        case = cases[name]
        ppm = ppm_dir / case["file"]
        png = png_dir / f"{name}.png"
        jpeg = jpeg_dir / f"{name}.jpg"
        with Image.open(ppm) as image:
            image.save(png, format="PNG", optimize=False, compress_level=6)
            image.save(
                jpeg,
                format="JPEG",
                quality=95,
                subsampling=0,
                optimize=False,
                progressive=False,
            )
        for image_format, path, settings in (
            ("png", png, "optimize=false,compress_level=6"),
            (
                "jpeg",
                jpeg,
                "quality=95,subsampling=0,optimize=false,progressive=false",
            ),
        ):
            paths[image_format].append(path)
            records.append(
                {
                    "case": name,
                    "format": image_format,
                    "width": case["width"],
                    "height": case["height"],
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "settings": settings,
                }
            )
    return paths, records, pillow_version


def encoding_arguments(mode: str) -> list[str]:
    if mode == "lossy":
        return ["-q", "75", "-m", "4"]
    if mode == "lossless":
        return ["-lossless", "-exact", "-q", "75", "-m", "4"]
    return [
        "-lossless",
        "-exact",
        "-q",
        "75",
        "-near_lossless",
        "40",
        "-m",
        "4",
    ]


def verify_persistent(
    benchmark: Path,
    corpus: dict[str, list[Path]],
    batch_size: int,
    cuda_device: Optional[int],
) -> list[dict[str, Any]]:
    records = []
    for image_format in FORMATS:
        for mode in MODES:
            command = [
                str(benchmark),
                "--variant",
                "cuda",
                "--mode",
                mode,
                "--batch-size",
                str(batch_size),
                "--force-cuda",
                "--verify-only",
                *(str(path) for path in corpus[image_format]),
            ]
            completed = run_checked(
                command,
                environment=clean_environment("cuda", False, cuda_device),
            )
            records.append(
                {
                    "operation": "persistent_verification",
                    "format": image_format,
                    "mode": mode,
                    "command": command,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "pass": True,
                }
            )
    return records


def run_persistent(
    benchmark: Path,
    corpus: dict[str, list[Path]],
    *,
    batch_size: int,
    warmups: int,
    samples: int,
    seed: int,
    cuda_device: Optional[int],
) -> tuple[list[dict[str, Any]], list[str]]:
    cases = [
        (image_format, mode, variant)
        for image_format in FORMATS
        for mode in MODES
        for variant in VARIANTS
    ]
    random.Random(seed).shuffle(cases)
    rows: list[dict[str, Any]] = []
    order: list[str] = []
    for image_format, mode, variant in cases:
        case_id = f"{image_format}-{mode}-batch-{variant}"
        order.append(case_id)
        command = [
            str(benchmark),
            "--variant",
            variant,
            "--mode",
            mode,
            "--batch-size",
            str(batch_size),
            "--warmups",
            str(warmups),
            "--samples",
            str(samples),
            "--include-file-io",
            "--force-cuda",
            *(str(path) for path in corpus[image_format]),
        ]
        completed = run_checked(
            command,
            environment=clean_environment(variant, True, cuda_device),
        )
        case_rows = [json.loads(line) for line in completed.stdout.splitlines()]
        if len(case_rows) != samples:
            raise RuntimeError(
                f"{case_id}: expected {samples} rows, got {len(case_rows)}"
            )
        hashes = {row["output_hash"] for row in case_rows}
        if len(hashes) != 1:
            raise RuntimeError(f"{case_id}: unstable output hashes")
        for row in case_rows:
            requires_resident_handoff = variant == "cuda" and mode != "lossy"
            resident_handoff_observed = row.get(
                "resident_lossless_handoff_observed", False
            )
            if requires_resident_handoff and not resident_handoff_observed:
                raise RuntimeError(
                    f"{case_id}: resident lossless handoff was not observed"
                )
            row.update(
                {
                    "lifecycle": "batch",
                    "format": image_format,
                    "case_id": case_id,
                    "command": command,
                }
            )
            rows.append(row)
    return rows, order


def run_single(
    cwebp: Path,
    corpus: dict[str, list[Path]],
    output: Path,
    *,
    samples: int,
    seed: int,
    cuda_device: Optional[int],
) -> tuple[list[dict[str, Any]], list[str]]:
    cases = [
        (image_format, mode, variant, repetition, index)
        for repetition in range(samples)
        for image_format in FORMATS
        for mode in MODES
        for variant in VARIANTS
        for index in range(len(CASE_NAMES))
    ]
    random.Random(seed ^ 0x5EED5EED).shuffle(cases)
    rows: list[dict[str, Any]] = []
    order: list[str] = []
    output.mkdir(parents=True, exist_ok=True)
    for image_format, mode, variant, repetition, index in cases:
        name = CASE_NAMES[index]
        destination = (
            output
            / f"{image_format}-{mode}-{variant}-{name}-r{repetition + 1}.webp"
        )
        command = [
            str(cwebp),
            "-quiet",
            *encoding_arguments(mode),
            str(corpus[image_format][index]),
            "-o",
            str(destination),
        ]
        case_id = (
            f"{image_format}-{mode}-single-{variant}-{name}-r{repetition + 1}"
        )
        order.append(case_id)
        environment = clean_environment(variant, True, cuda_device)
        if variant == "cuda" and mode != "lossy":
            environment["WEBP_CUDA_HANDOFF_MARKERS"] = "1"
        begin = time.perf_counter_ns()
        completed = subprocess.run(
            command,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        elapsed_ns = time.perf_counter_ns() - begin
        if completed.returncode != 0:
            raise RuntimeError(
                f"{case_id} failed ({completed.returncode}): {completed.stderr}"
            )
        resident_handoff_observed = observed_resident_lossless_handoff(
            completed.stderr
        )
        if (
            variant == "cuda"
            and mode != "lossy"
            and not resident_handoff_observed
        ):
            raise RuntimeError(
                f"{case_id}: resident lossless handoff was not observed"
            )
        rows.append(
            {
                "operation": "fresh_file_encode",
                "lifecycle": "single",
                "format": image_format,
                "mode": mode,
                "variant": variant,
                "input": name,
                "repetition": repetition,
                "elapsed_ns": elapsed_ns,
                "output_bytes": destination.stat().st_size,
                "output_sha256": sha256(destination),
                "output_path": str(destination),
                "case_id": case_id,
                "command": command,
                "stderr": completed.stderr,
                "resident_lossless_handoff_observed": (
                    resident_handoff_observed
                ),
            }
        )
    return rows, order


def validate_single(
    dwebp: Path, rows: list[dict[str, Any]], output: Path
) -> list[dict[str, Any]]:
    indexed = {
        (
            row["format"],
            row["mode"],
            row["input"],
            row["repetition"],
            row["variant"],
        ): row
        for row in rows
    }
    decoded = output / "decoded"
    decoded.mkdir(parents=True, exist_ok=True)
    validation: list[dict[str, Any]] = []
    for image_format in FORMATS:
        for mode in MODES:
            repetitions = sorted(
                {
                    row["repetition"]
                    for row in rows
                    if row["format"] == image_format and row["mode"] == mode
                }
            )
            for repetition in repetitions:
                for name in CASE_NAMES:
                    cpu = indexed[(image_format, mode, name, repetition, "cpu")]
                    cuda = indexed[(image_format, mode, name, repetition, "cuda")]
                    cpu_path = Path(cpu["output_path"])
                    cuda_path = Path(cuda["output_path"])
                    output_equal = cpu_path.read_bytes() == cuda_path.read_bytes()
                    decoded_paths = []
                    for variant, source in (("cpu", cpu_path), ("cuda", cuda_path)):
                        destination = (
                            decoded
                            / f"{image_format}-{mode}-{name}-r{repetition + 1}-{variant}.pam"
                        )
                        run_checked(
                            [
                                str(dwebp),
                                "-quiet",
                                str(source),
                                "-pam",
                                "-o",
                                str(destination),
                            ]
                        )
                        decoded_paths.append(destination)
                    decoded_equal = (
                        decoded_paths[0].read_bytes() == decoded_paths[1].read_bytes()
                    )
                    # The RGB-to-YUV stage promises the exact CPU bitstream.
                    # Lossless color search may choose a different valid
                    # transform, so those modes promise decoded-pixel parity.
                    required_equality = (
                        "encoded_bytes" if mode == "lossy" else "decoded_pixels"
                    )
                    passed = (
                        output_equal
                        if required_equality == "encoded_bytes"
                        else decoded_equal
                    )
                    record = {
                        "operation": "single_validation",
                        "format": image_format,
                        "mode": mode,
                        "input": name,
                        "repetition": repetition,
                        "output_equal": output_equal,
                        "decoded_equal": decoded_equal,
                        "required_equality": required_equality,
                        "cpu_output_sha256": cpu["output_sha256"],
                        "cuda_output_sha256": cuda["output_sha256"],
                        "cpu_decoded_sha256": sha256(decoded_paths[0]),
                        "cuda_decoded_sha256": sha256(decoded_paths[1]),
                        "pass": passed,
                    }
                    validation.append(record)
                    if not passed:
                        raise RuntimeError(f"validation failed: {record}")
    return validation


def summarize(
    persistent: list[dict[str, Any]], single: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    batch_groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    batch_byte_groups: dict[tuple[str, str, str], list[float]] = defaultdict(
        list
    )
    for row in persistent:
        key = (row["format"], row["mode"], row["variant"])
        batch_groups[key].append(row["ns_per_image"] / 1e6)
        batch_byte_groups[key].append(row["output_bytes"] / row["batch_size"])

    repetitions: dict[tuple[str, str, str, int], list[float]] = defaultdict(list)
    byte_repetitions: dict[
        tuple[str, str, str, int], list[float]
    ] = defaultdict(list)
    for row in single:
        key = (row["format"], row["mode"], row["variant"], row["repetition"])
        repetitions[key].append(row["elapsed_ns"] / 1e6)
        byte_repetitions[key].append(row["output_bytes"])
    single_groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    single_byte_groups: dict[
        tuple[str, str, str], list[float]
    ] = defaultdict(list)
    for key, values in repetitions.items():
        image_format, mode, variant, _ = key
        group = (image_format, mode, variant)
        single_groups[group].append(sum(values) / len(values))
        byte_values = byte_repetitions[key]
        single_byte_groups[group].append(sum(byte_values) / len(byte_values))

    summary = []
    for image_format in FORMATS:
        for mode in MODES:
            for lifecycle, groups, byte_groups in (
                ("batch", batch_groups, batch_byte_groups),
                ("single", single_groups, single_byte_groups),
            ):
                cpu_key = (image_format, mode, "cpu")
                cuda_key = (image_format, mode, "cuda")
                cpu_ms = statistics.median(groups[cpu_key])
                cuda_ms = statistics.median(groups[cuda_key])
                cpu_bytes = statistics.median(byte_groups[cpu_key])
                cuda_bytes = statistics.median(byte_groups[cuda_key])
                summary.append(
                    {
                        "format": image_format,
                        "mode": mode,
                        "lifecycle": lifecycle,
                        "cpu_ms_per_image": cpu_ms,
                        "cuda_ms_per_image": cuda_ms,
                        "speedup": cpu_ms / cuda_ms,
                        "cpu_bytes_per_image": cpu_bytes,
                        "cuda_bytes_per_image": cuda_bytes,
                        "cuda_size_ratio": cuda_bytes / cpu_bytes,
                    }
                )
    return summary


def method_label(row: dict[str, Any]) -> str:
    return f"{row['format'].upper()} {row['mode']} \u2014 {row['lifecycle']}"


def bottom_line(summary: list[dict[str, Any]]) -> str:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in summary:
        grouped[(row["lifecycle"], row["mode"])].append(row["speedup"])
    batch_wins = [
        mode
        for mode in MODES
        if statistics.median(grouped[("batch", mode)]) >= 1.05
    ]
    lossy_batch = statistics.median(grouped[("batch", "lossy")])
    singles_lose = all(
        row["speedup"] < 1.0
        for row in summary
        if row["lifecycle"] == "single"
    )
    if batch_wins == ["lossless", "near-lossless"] and 0.95 <= lossy_batch <= 1.05:
        batch_clause = (
            "CUDA helps persistent lossless batches, is neutral for lossy "
            "batches"
        )
    elif batch_wins:
        batch_clause = (
            "CUDA helps persistent " + ", ".join(batch_wins) + " batches"
        )
    else:
        batch_clause = "CUDA does not materially help the measured batches"
    single_clause = (
        "is substantially worse when starting a fresh process for each image"
        if singles_lose
        else "has mixed results when starting a fresh process for each image"
    )
    return f"Bottom line: {batch_clause}, and {single_clause}."


def render_markdown(summary: list[dict[str, Any]], batch_size: int) -> str:
    lookup = {
        (row["format"], row["mode"], row["lifecycle"]): row for row in summary
    }
    tick = chr(96)
    lines = [
        "Times are milliseconds per image. "
        f"Batch uses a persistent {batch_size}-item process; single starts a new "
        f"{tick}cwebp{tick} process per image. Speedup above "
        f"{tick}1\u00d7{tick} favors CUDA.",
        "",
        "| Method | CPU time | CUDA time | Speedup |",
        "|---|---:|---:|---:|",
    ]
    for image_format in FORMATS:
        for mode in MODES:
            for lifecycle in ("batch", "single"):
                row = lookup[(image_format, mode, lifecycle)]
                speedup = f"{row['speedup']:.2f}\u00d7"
                if row["speedup"] >= 1.05:
                    speedup = f"**{speedup}**"
                lines.append(
                    f"| {method_label(row)} | "
                    f"{row['cpu_ms_per_image']:.1f} ms | "
                    f"{row['cuda_ms_per_image']:.1f} ms | {speedup} |"
                )
    lines.extend(
        [
            "",
            bottom_line(summary),
            "",
        ]
    )
    return "\n".join(lines)


def render_comparison(results: list[dict[str, Any]]) -> str:
    lines = []
    for result in results:
        lines.extend(
            [
                f"## {result['system']['label']}",
                "",
                render_markdown(
                    result["summary"], result["configuration"]["batch_size"]
                ),
            ]
        )
    if len(results) > 1:
        labels = [result["system"]["label"] for result in results]
        lines.extend(
            [
                "## Speedup comparison",
                "",
                "| Method | " + " | ".join(labels) + " |",
                "|---|" + "|".join("---:" for _ in labels) + "|",
            ]
        )
        summaries = [
            {
                (row["format"], row["mode"], row["lifecycle"]): row
                for row in result["summary"]
            }
            for result in results
        ]
        for image_format in FORMATS:
            for mode in MODES:
                for lifecycle in ("batch", "single"):
                    key = (image_format, mode, lifecycle)
                    label = method_label(summaries[0][key])
                    values = [
                        f"{summary[key]['speedup']:.2f}\u00d7"
                        for summary in summaries
                    ]
                    lines.append(f"| {label} | " + " | ".join(values) + " |")
        lines.append("")
    return "\n".join(lines)


def system_metadata(args: argparse.Namespace, pillow_version: str) -> dict[str, Any]:
    gpu = command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version",
            "--format=csv,noheader",
        ]
    )
    gpu_lines = gpu.splitlines()
    gpu_name = gpu_lines[0] if gpu_lines else "unknown gpu"
    label = args.label or f"{socket.gethostname()} / {gpu_name}"
    return {
        "label": label,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "lscpu": command_output(["lscpu"]),
        "python": sys.version,
        "pillow": pillow_version,
        "gpu": gpu,
        "nvidia_smi": command_output(["nvidia-smi"]),
        "nvcc": command_output(["nvcc", "--version"]),
        "git_commit": command_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]
        ),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_jsonl(path: Path, groups: list[list[dict[str, Any]]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for group in groups:
            for row in group:
                stream.write(json.dumps(row, sort_keys=True) + "\n")


def run_suite(args: argparse.Namespace) -> int:
    build_dir = args.build_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    binaries = {
        "benchmark": build_dir / "webp_cuda_batch_benchmark",
        "cwebp": build_dir / "cwebp",
        "dwebp": build_dir / "dwebp",
    }
    missing = [
        str(path) for path in binaries.values() if not os.access(path, os.X_OK)
    ]
    if missing:
        raise RuntimeError("missing executable(s): " + ", ".join(missing))

    corpus, corpus_records, pillow_version = prepare_corpus(output / "corpus")
    verification = verify_persistent(
        binaries["benchmark"], corpus, args.batch_size, args.cuda_device
    )
    if args.verify_only:
        result = {
            "schema": SCHEMA,
            "system": system_metadata(args, pillow_version),
            "configuration": {
                "build_dir": str(build_dir),
                "output_dir": str(output),
                "batch_size": args.batch_size,
                "warmups": args.warmups,
                "samples": args.samples,
                "seed": args.seed,
                "cuda_device": args.cuda_device,
                "verify_only": True,
                "binaries": {
                    name: {"path": str(path), "sha256": sha256(path)}
                    for name, path in binaries.items()
                },
            },
            "corpus": corpus_records,
            "verification": verification,
        }
        (output / "verification.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"PASS: {len(verification)} persistent CPU/CUDA verification cases")
        return 0

    persistent, persistent_order = run_persistent(
        binaries["benchmark"],
        corpus,
        batch_size=args.batch_size,
        warmups=args.warmups,
        samples=args.samples,
        seed=args.seed,
        cuda_device=args.cuda_device,
    )
    single, single_order = run_single(
        binaries["cwebp"],
        corpus,
        output / "outputs",
        samples=args.samples,
        seed=args.seed,
        cuda_device=args.cuda_device,
    )
    single_validation = validate_single(
        binaries["dwebp"], single, output / "outputs"
    )
    summary = summarize(persistent, single)
    result = {
        "schema": SCHEMA,
        "system": system_metadata(args, pillow_version),
        "configuration": {
            "batch_size": args.batch_size,
            "warmups": args.warmups,
            "samples": args.samples,
            "seed": args.seed,
            "cuda_device": args.cuda_device,
            "quality": 75,
            "method": 4,
            "near_lossless": 40,
            "file_io": "page-cached unless the operator documents otherwise",
            "cuda_policy": "forced stages for matched CPU/CUDA comparison",
            "cuda_lossy_analysis": (
                "forced exact macroblock analysis with resident YUV handoff"
            ),
            "cuda_fused_lossy_analysis": (
                "forced RGB conversion plus exact analysis before one sync"
            ),
            "cuda_lossless_handoff": (
                "forced transformed-pixel reuse from color to main hash"
            ),
            "cuda_predictor": (
                "forced parallel 14-mode tile selector and exact residuals"
            ),
            "cuda_histogram": (
                "forced exact global backward-reference population counts"
            ),
            "validation_policy": {
                "lossy": "encoded_bytes",
                "lossless": "decoded_pixels",
                "near-lossless": "decoded_pixels",
            },
            "outputs_retained": args.keep_outputs,
            "binaries": {
                name: {"path": str(path), "sha256": sha256(path)}
                for name, path in binaries.items()
            },
        },
        "corpus": corpus_records,
        "execution_order": {
            "persistent": persistent_order,
            "single": single_order,
        },
        "verification": verification,
        "validation_counts": {
            "total": len(single_validation),
            "passed": sum(row["pass"] for row in single_validation),
            "encoded_exact": sum(
                row["output_equal"] for row in single_validation
            ),
            "decoded_exact": sum(
                row["decoded_equal"] for row in single_validation
            ),
            "lossy_exact": sum(
                row["mode"] == "lossy" and row["output_equal"]
                for row in single_validation
            ),
        },
        "summary": summary,
    }
    write_jsonl(
        output / "raw.jsonl",
        [verification, persistent, single, single_validation],
    )
    result_path = output / "results.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = render_markdown(summary, args.batch_size)
    (output / "report.md").write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"\nMachine-readable results: {result_path}")
    if not args.keep_outputs:
        shutil.rmtree(output / "outputs")
    return 0


def report_results(args: argparse.Namespace) -> int:
    results = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.results
    ]
    for path, result in zip(args.results, results):
        if result.get("schema") != SCHEMA:
            raise RuntimeError(
                f"{path}: unsupported schema {result.get('schema')!r}"
            )
        if result.get("configuration", {}).get("verify_only") or not result.get(
            "summary"
        ):
            raise RuntimeError(
                f"{path}: verify-only results contain no summary to report"
            )
    reference = results[0]
    reference_corpus = {
        (row["case"], row["format"]): row["sha256"]
        for row in reference["corpus"]
    }
    comparison_keys = ("batch_size", "quality", "method", "near_lossless")
    for path, result in zip(args.results[1:], results[1:]):
        corpus = {
            (row["case"], row["format"]): row["sha256"]
            for row in result["corpus"]
        }
        if corpus != reference_corpus:
            raise RuntimeError(f"{path}: corpus hashes do not match the first run")
        mismatches = [
            key
            for key in comparison_keys
            if result["configuration"].get(key)
            != reference["configuration"].get(key)
        ]
        if mismatches:
            raise RuntimeError(
                f"{path}: incomparable configuration: {', '.join(mismatches)}"
            )
    report = render_comparison(results)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    subparsers = top.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run the complete benchmark suite")
    run.add_argument("--build-dir", required=True, type=Path)
    run.add_argument("--output-dir", required=True, type=Path)
    run.add_argument("--label", help="human-readable system label")
    run.add_argument("--batch-size", type=int, default=24)
    run.add_argument("--warmups", type=int, default=1)
    run.add_argument("--samples", type=int, default=5)
    run.add_argument("--seed", type=int, default=0xC0DA)
    run.add_argument("--cuda-device", type=int)
    run.add_argument("--verify-only", action="store_true")
    run.add_argument("--keep-outputs", action="store_true")
    run.set_defaults(function=run_suite)

    report = subparsers.add_parser(
        "report", help="render one or more machine-readable result files"
    )
    report.add_argument("results", nargs="+", type=Path)
    report.add_argument("--output", type=Path)
    report.set_defaults(function=report_results)
    return top


def main() -> int:
    args = parser().parse_args()
    if getattr(args, "batch_size", 1) < 1:
        raise SystemExit("--batch-size must be positive")
    if getattr(args, "samples", 1) < 1:
        raise SystemExit("--samples must be positive")
    if getattr(args, "warmups", 0) < 0:
        raise SystemExit("--warmups must be non-negative")
    cuda_device = getattr(args, "cuda_device", None)
    if cuda_device is not None and cuda_device < 0:
        raise SystemExit("--cuda-device must be non-negative")
    try:
        return args.function(args)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
