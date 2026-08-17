#!/usr/bin/env python3
"""Pairwise Metal ablation harness.

The default mode only writes the matrix and environment manifest. Timed work
requires --run so benchmark ownership can be released explicitly.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import platform
import resource
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ENCODER = ROOT / "examples" / "cwebp"
IMPORT_BENCH = ROOT / "extras" / "metal_import_bench"

BASE_ENV = {
    "WEBP_METAL": "1",
    "WEBP_METAL_ABLATION_EXPERIMENT": "1",
    "WEBP_METAL_VERBOSE": "0",
    "WEBP_METAL_TRANSFORM_DISPATCH_2D": "0",
    "WEBP_METAL_HASH_MATCH4": "0",
    "WEBP_METAL_LOSSY_BLOCK_2X2": "0",
    "WEBP_METAL_WRITE_COMBINED_INPUTS": "0",
    "WEBP_METAL_TRANSFORM_UNRETAINED_COMMAND_BUFFERS": "0",
    "WEBP_METAL_HASH_UNRETAINED_COMMAND_BUFFERS": "0",
    "WEBP_METAL_LOSSY_UNRETAINED_COMMAND_BUFFERS": "0",
    "WEBP_METAL_LOSSY_CONTIGUOUS_COPY": "0",
    "WEBP_METAL_TRANSFORM_THREADS": "256",
    "WEBP_METAL_HASH_THREADS": "256",
    "WEBP_METAL_LOSSY_THREADS": "256",
}


@dataclasses.dataclass(frozen=True)
class Variant:
    name: str
    environment: dict[str, str]
    rationale: str


@dataclasses.dataclass(frozen=True)
class Suite:
    name: str
    runner: str
    baseline_environment: dict[str, str]
    variants: tuple[Variant, ...]


SUITES = {
    "recorded": Suite(
        "recorded",
        "cwebp",
        {
            "WEBP_METAL_MIN_PIXELS": "0",
            "WEBP_METAL_HASH": "1",
            "WEBP_METAL_HASH_MIN_PIXELS": "4000000",
            "WEBP_METAL_LOSSY": "0",
        },
        (),
    ),
    "transform": Suite(
        "transform",
        "cwebp",
        {
            "WEBP_METAL_MIN_PIXELS": "0",
            "WEBP_METAL_HASH": "0",
            "WEBP_METAL_LOSSY": "0",
        },
        (
            Variant(
                "dispatch_2d",
                {"WEBP_METAL_TRANSFORM_DISPATCH_2D": "1"},
                "Replace tile-index division/modulo with a native 2D grid.",
            ),
            Variant(
                "threads_128",
                {"WEBP_METAL_TRANSFORM_THREADS": "128"},
                "Test occupancy against the fixed 256-thread baseline.",
            ),
            Variant(
                "threads_512",
                {"WEBP_METAL_TRANSFORM_THREADS": "512"},
                "Test larger per-tile groups where the device permits them.",
            ),
            Variant(
                "unretained_commands",
                {"WEBP_METAL_TRANSFORM_UNRETAINED_COMMAND_BUFFERS": "1"},
                "Avoid command-buffer resource retain/release traffic.",
            ),
        ),
    ),
    "hash": Suite(
        "hash",
        "cwebp",
        {
            "WEBP_METAL_MIN_PIXELS": "0",
            "WEBP_METAL_HASH": "1",
            "WEBP_METAL_HASH_MIN_PIXELS": "0",
            "WEBP_METAL_LOSSY": "0",
        },
        (
            Variant(
                "match4",
                {"WEBP_METAL_HASH_MATCH4": "1"},
                "Compare four pixels per match-loop iteration.",
            ),
            Variant(
                "write_combined_inputs",
                {"WEBP_METAL_WRITE_COMBINED_INPUTS": "1"},
                "Use write-combined CPU caching for upload-only buffers.",
            ),
            Variant(
                "threads_128",
                {"WEBP_METAL_HASH_THREADS": "128"},
                "Test divergent-kernel occupancy below the fixed baseline.",
            ),
            Variant(
                "threads_512",
                {"WEBP_METAL_HASH_THREADS": "512"},
                "Test divergent-kernel occupancy above the fixed baseline.",
            ),
            Variant(
                "unretained_commands",
                {"WEBP_METAL_HASH_UNRETAINED_COMMAND_BUFFERS": "1"},
                "Avoid retain/release traffic for synchronously owned inputs.",
            ),
        ),
    ),
    "lossy": Suite(
        "lossy",
        "import",
        {
            "WEBP_METAL": "0",
            "WEBP_METAL_LOSSY": "1",
            "WEBP_METAL_LOSSY_MIN_PIXELS": "0",
        },
        (
            Variant(
                "block_2x2",
                {"WEBP_METAL_LOSSY_BLOCK_2X2": "1"},
                "Reuse four RGB loads for luma and chroma in a 2x2 block.",
            ),
            Variant(
                "write_combined_inputs",
                {"WEBP_METAL_WRITE_COMBINED_INPUTS": "1"},
                "Use write-combined CPU caching for the source upload.",
            ),
            Variant(
                "contiguous_copy",
                {"WEBP_METAL_LOSSY_CONTIGUOUS_COPY": "1"},
                "Collapse row-wise Y/U/V readback into one copy when contiguous.",
            ),
            Variant(
                "threads_128",
                {"WEBP_METAL_LOSSY_THREADS": "128"},
                "Test occupancy against the fixed 256-thread baseline.",
            ),
            Variant(
                "threads_512",
                {"WEBP_METAL_LOSSY_THREADS": "512"},
                "Test larger threadgroups where the device permits them.",
            ),
            Variant(
                "unretained_commands",
                {"WEBP_METAL_LOSSY_UNRETAINED_COMMAND_BUFFERS": "1"},
                "Avoid command-buffer resource retain/release traffic.",
            ),
        ),
    ),
}

IMPORT_DIMENSIONS = ((3000, 2000, 50), (4000, 3000, 30))


def command_output(argv: list[str]) -> dict[str, object]:
    try:
        result = subprocess.run(
            argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False, timeout=30, cwd=ROOT,
        )
        return {"argv": argv, "exit_code": result.returncode,
                "output": result.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"argv": argv, "error": str(error)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_inputs(items: Iterable[str]) -> dict[str, Path]:
    inputs: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"input must be NAME=PATH: {item}")
        name, raw_path = item.split("=", 1)
        if not name or name in inputs:
            raise ValueError(f"invalid or duplicate input name: {name}")
        inputs[name] = Path(raw_path).expanduser().resolve()
    return inputs


def selected_suites(names: list[str]) -> list[Suite]:
    if "all" in names:
        return list(SUITES.values())
    return [SUITES[name] for name in names]


def effective_environment(suite: Suite,
                          variant: Variant | None) -> dict[str, str]:
    environment = dict(BASE_ENV)
    environment.update(suite.baseline_environment)
    if variant is not None:
        environment.update(variant.environment)
    return environment


def matrix_document(suites: list[Suite]) -> dict[str, object]:
    return {
        "schema": 1,
        "baseline": "all optimization flags disabled; 256 threads per stage",
        "suites": [
            {
                "name": suite.name,
                "runner": suite.runner,
                "baseline_environment": effective_environment(suite, None),
                "variants": [
                    {
                        "name": variant.name,
                        "environment": effective_environment(suite, variant),
                        "delta": variant.environment,
                        "rationale": variant.rationale,
                    }
                    for variant in suite.variants
                ],
            }
            for suite in suites
        ],
    }


def metadata_document(args: argparse.Namespace, inputs: dict[str, Path]) -> dict[str, object]:
    commands = [
        ["sw_vers"], ["uname", "-a"],
        ["sysctl", "-n", "hw.model", "hw.memsize", "machdep.cpu.brand_string"],
        ["system_profiler", "SPHardwareDataType", "SPDisplaysDataType", "-json"],
        ["pmset", "-g", "batt"], ["pmset", "-g", "therm"],
        ["xcodebuild", "-version"], ["clang", "--version"],
        ["git", "rev-parse", "HEAD"], ["git", "status", "--short"],
    ]
    return {
        "schema": 1,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "created_local": dt.datetime.now().astimezone().isoformat(),
        "timezone": time.tzname,
        "platform": platform.platform(),
        "python": sys.version,
        "argv": sys.argv,
        "cwd": str(Path.cwd()),
        "repository": str(ROOT),
        "commands": [command_output(command) for command in commands],
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.is_file(),
                "size": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
            for name, path in inputs.items()
        },
        "parameters": {
            "trials": args.trials,
            "import_processes": args.import_processes,
            "methods": args.methods,
            "suites": args.suite,
        },
    }


def append_record(raw_file: Path, record: dict[str, object]) -> None:
    with raw_file.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, sort_keys=True) + "\n")
        output.flush()


def timed_process(
    argv: list[str], environment: dict[str, str]
) -> tuple[dict[str, object], str, str]:
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start_ns = time.perf_counter_ns()
    result = subprocess.run(
        argv,
        env={**os.environ, **environment},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    end_ns = time.perf_counter_ns()
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    timing = {
        "wall_seconds": (end_ns - start_ns) / 1_000_000_000.0,
        "user_seconds": child_after.ru_utime - child_before.ru_utime,
        "system_seconds": child_after.ru_stime - child_before.ru_stime,
        "exit_code": result.returncode,
    }
    return timing, result.stdout, result.stderr


def cwebp_record(raw_file: Path, temp_dir: Path, suite: Suite,
                  variant: Variant | None, comparison: str, order: int,
                  trial: int, input_name: str, input_path: Path,
                  method: int, baseline_digest: str | None) -> str:
    case = variant.name if variant is not None else "baseline"
    output_path = temp_dir / f"{suite.name}-{comparison}-{trial}-{case}.webp"
    environment = effective_environment(suite, variant)
    argv = [str(ENCODER), "-quiet", "-lossless", "-exact", "-m", str(method),
            str(input_path), "-o", str(output_path)]
    timing, stdout, stderr = timed_process(argv, environment)
    digest = sha256_file(output_path) if output_path.is_file() else ""
    record = {
        "schema": 1, "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "suite": suite.name, "case": case, "comparison": comparison,
        "order": order, "trial": trial, "input": input_name,
        "input_path": str(input_path), "method": method,
        "environment": environment, "argv": argv, **timing,
        "output_bytes": output_path.stat().st_size if output_path.is_file() else None,
        "output_sha256": digest or None,
        "matches_paired_baseline": (digest == baseline_digest)
            if digest and baseline_digest is not None else None,
        "stdout": stdout, "stderr": stderr,
    }
    append_record(raw_file, record)
    if output_path.exists():
        output_path.unlink()
    if timing["exit_code"] != 0:
        raise RuntimeError(f"failed: {shlex.join(argv)}\n{stderr}")
    return digest


def run_cwebp_suite(raw_file: Path, temp_dir: Path, suite: Suite,
                     inputs: dict[str, Path], methods: list[int], trials: int) -> None:
    if not suite.variants:
        for trial in range(trials):
            for input_name, input_path in inputs.items():
                for method in methods:
                    cwebp_record(raw_file, temp_dir, suite, None, "recorded", 0,
                                  trial, input_name, input_path, method, None)
        return
    for variant in suite.variants:
        for trial in range(trials):
            for input_name, input_path in inputs.items():
                for method in methods:
                    pair: list[Variant | None] = [None, variant]
                    if trial % 2:
                        pair.reverse()
                    baseline_digest: str | None = None
                    pending_variant_digest: str | None = None
                    for order, current in enumerate(pair):
                        digest = cwebp_record(
                            raw_file, temp_dir, suite, current, variant.name,
                            order, trial, input_name, input_path, method,
                            baseline_digest,
                        )
                        if current is None:
                            baseline_digest = digest
                        else:
                            pending_variant_digest = digest
                    if baseline_digest != pending_variant_digest:
                        raise RuntimeError(
                            f"bitstream mismatch: {suite.name}/{variant.name}/"
                            f"{input_name}/m{method}/trial{trial}"
                        )


def import_records(raw_file: Path, suite: Suite, variant: Variant | None,
                   comparison: str, order: int, process_index: int,
                   width: int, height: int, iterations: int) -> set[str]:
    case = variant.name if variant is not None else "baseline"
    environment = effective_environment(suite, variant)
    argv = [str(IMPORT_BENCH), str(width), str(height), str(iterations), "1"]
    timing, stdout, stderr = timed_process(argv, environment)
    process_record = {
        "schema": 1, "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "suite": suite.name, "case": case, "comparison": comparison,
        "order": order, "process": process_index, "width": width,
        "height": height, "metric": "process_wall", "environment": environment,
        "argv": argv, **timing, "stderr": stderr,
    }
    append_record(raw_file, process_record)
    if timing["exit_code"] != 0:
        raise RuntimeError(f"failed: {shlex.join(argv)}\n{stderr}")
    lines = stdout.splitlines()
    if not lines or lines[0] != "phase\tsample\tseconds\tchecksum":
        raise RuntimeError(f"unexpected import benchmark output: {stdout[:200]}")
    checksums = set()
    for line in lines[1:]:
        phase, sample, seconds, checksum = line.split("\t")
        checksums.add(checksum)
        append_record(raw_file, {
            "schema": 1, "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "suite": suite.name, "case": case, "comparison": comparison,
            "order": order, "process": process_index, "width": width,
            "height": height, "phase": phase, "sample": int(sample),
            "metric": "import", "seconds": float(seconds),
            "checksum": checksum, "environment": environment,
        })
    return checksums


def run_import_suite(raw_file: Path, suite: Suite, processes: int) -> None:
    for variant in suite.variants:
        for process_index in range(processes):
            for width, height, iterations in IMPORT_DIMENSIONS:
                pair: list[Variant | None] = [None, variant]
                if process_index % 2:
                    pair.reverse()
                pair_checksums: dict[str, set[str]] = {}
                for order, current in enumerate(pair):
                    case = current.name if current is not None else "baseline"
                    pair_checksums[case] = import_records(
                        raw_file, suite, current, variant.name, order,
                        process_index, width, height, iterations,
                    )
                if pair_checksums["baseline"] != pair_checksums[variant.name]:
                    raise RuntimeError(
                        f"import checksum mismatch: {variant.name}/"
                        f"{width}x{height}/process{process_index}"
                    )


def write_summary(raw_file: Path, summary_file: Path) -> None:
    groups: dict[tuple[object, ...], list[float]] = {}
    for line in raw_file.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("metric") == "process_wall":
            continue
        seconds = record.get("seconds", record.get("wall_seconds"))
        if seconds is None or record.get("phase") == "warmup":
            continue
        key = (record.get("suite"), record.get("comparison"), record.get("case"),
               record.get("input"), record.get("method"), record.get("width"),
               record.get("height"))
        groups.setdefault(key, []).append(float(seconds))
    rows = []
    for key, samples in sorted(groups.items(), key=lambda item: str(item[0])):
        rows.append({
            "suite": key[0], "comparison": key[1], "case": key[2],
            "input": key[3], "method": key[4], "width": key[5],
            "height": key[6], "samples": len(samples),
            "mean_seconds": statistics.fmean(samples),
            "median_seconds": statistics.median(samples),
            "min_seconds": min(samples), "max_seconds": max(samples),
        })
    indexed = {
        (row["suite"], row["comparison"], row["input"], row["method"],
         row["width"], row["height"], row["case"]): row
        for row in rows
    }
    for row in rows:
        baseline = indexed.get(
            (row["suite"], row["comparison"], row["input"], row["method"],
             row["width"], row["height"], "baseline")
        )
        if baseline is not None:
            row["baseline_over_case_median"] = (
                baseline["median_seconds"] / row["median_seconds"]
            )
            row["median_percent_change"] = 100.0 * (
                row["median_seconds"] / baseline["median_seconds"] - 1.0
            )
    summary_file.write_text(json.dumps({"schema": 1, "groups": rows}, indent=2)
                            + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="new directory for manifest and raw JSONL")
    parser.add_argument("--input", action="append", default=[], metavar="NAME=PATH",
                        help="lossless corpus input; repeat for each image")
    parser.add_argument("--suite", action="append", choices=["all", *SUITES],
                        default=[], help="suite to prepare/run (default: all)")
    parser.add_argument("--methods", type=int, nargs="+", default=[4, 6])
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--import-processes", type=int, default=3)
    parser.add_argument("--run", action="store_true",
                        help="execute timed commands; omitted means prepare only")
    args = parser.parse_args()
    if not args.suite:
        args.suite = ["all"]
    if args.trials <= 0 or args.import_processes <= 0:
        parser.error("trial counts must be positive")
    if args.run and os.environ.get("WEBP_METAL_ABLATION_EXPERIMENT") != "1":
        parser.error("--run requires WEBP_METAL_ABLATION_EXPERIMENT=1")
    if args.run and os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        parser.error("--run requires WEBP_BENCHMARK_SESSION=exclusive")
    try:
        inputs = parse_inputs(args.input)
    except ValueError as error:
        parser.error(str(error))
    suites = selected_suites(args.suite)
    args.output = args.output.expanduser().resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "matrix.json").write_text(
        json.dumps(matrix_document(suites), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output / "metadata.json").write_text(
        json.dumps(metadata_document(args, inputs), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not args.run:
        print(f"Prepared benchmark manifest only: {args.output}")
        print("No timed commands were run. Re-run with --run after benchmark release.")
        return 0
    cwebp_needed = any(suite.runner == "cwebp" for suite in suites)
    import_needed = any(suite.runner == "import" for suite in suites)
    if cwebp_needed and not ENCODER.is_file():
        parser.error(f"missing encoder: {ENCODER}")
    if import_needed and not IMPORT_BENCH.is_file():
        parser.error(f"missing import benchmark: {IMPORT_BENCH}")
    if not IMPORT_BENCH.is_file():
        parser.error(
            "missing ablation guard probe; build with "
            "WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1")
    guard = subprocess.run(
        [str(IMPORT_BENCH), "--guard-check"], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if guard.returncode != 0:
        parser.error(
            "ablation build guard check failed; build with "
            "WEBP_BUILD_METAL_ABLATION_EXPERIMENT=1: " + guard.stderr.strip()
        )
    if cwebp_needed and not inputs:
        parser.error("at least one --input NAME=PATH is required for cwebp suites")
    missing = [path for path in inputs.values() if not path.is_file()]
    if missing:
        parser.error("missing inputs: " + ", ".join(map(str, missing)))

    raw_file = args.output / "raw_results.jsonl"
    with tempfile.TemporaryDirectory(prefix="libwebp-metal-ablation-") as temp:
        temp_dir = Path(temp)
        for suite in suites:
            if suite.runner == "cwebp":
                run_cwebp_suite(raw_file, temp_dir, suite, inputs,
                                 args.methods, args.trials)
            else:
                run_import_suite(raw_file, suite, args.import_processes)
    write_summary(raw_file, args.output / "summary.json")
    print(f"Completed benchmark matrix: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
