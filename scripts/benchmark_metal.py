#!/usr/bin/env python3
"""Reproducible CPU/Metal crossover experiment orchestration.

`smoke` never reads a clock. `run` is the only performance-collecting command
and requires an explicit acknowledgement because benchmark sessions are
serialized by the project orchestrator.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import platform
import random
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
CONTENTS = ("flat", "gradient", "graphic", "photo", "texture", "noise")
METHODS = tuple(range(7))
OPERATIONS = ("transform", "hash", "lossy")
DEFAULT_SIDES = {
    "transform": (128, 192, 256, 384, 512, 768, 1024, 1536),
    "hash": (512, 768, 1024, 1536, 2048, 3072, 4096),
    "lossy": (1024, 2048, 3072, 4096, 6144, 8192, 10240),
}
DISPATCH_MARKERS = {
    "transform": "WebP-Metal: transformed ",
    "hash": "WebP-Metal: hash candidates for ",
    "lossy": "WebP-Metal: lossy RGB->YUV ",
}


def csv_values(value: str, convert=str) -> tuple[Any, ...]:
    return tuple(convert(item) for item in value.split(",") if item)


def command_output(argv: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(argv, cwd=cwd, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def runner_command(
    runner: Path,
    case: dict[str, Any],
    variant: str,
    warmups: int,
    samples: int,
    measure: bool,
    artifact: Path | None = None,
) -> list[str]:
    width = case.get("width", case.get("side"))
    height = case.get("height", case.get("side"))
    command = [
        str(runner),
        "--operation", case["operation"],
        "--variant", variant,
        "--content", case["content"],
        "--width", str(width),
        "--height", str(height),
        "--method", str(case["method"]),
        "--seed", str(case["seed"]),
        "--warmups", str(warmups),
        "--samples", str(samples),
    ]
    if measure:
        command.append("--measure")
    if artifact is not None:
        command.extend(("--artifact", str(artifact)))
    return command


def invoke_runner(command: list[str], operation: str, variant: str) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"runner failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    try:
        samples = [json.loads(line) for line in completed.stdout.splitlines()]
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid runner JSON: {error}\n{completed.stdout}") from error
    if not samples:
        raise RuntimeError("runner returned no samples")
    dispatches = sorted(
        name for name, marker in DISPATCH_MARKERS.items()
        if marker in completed.stderr
    )
    return {"samples": samples, "dispatches": dispatches}


def verify_pair(
    operation: str,
    cpu: dict[str, Any],
    metal: dict[str, Any],
    require_bitstream_equal: bool | None = None,
) -> None:
    cpu_first = cpu["samples"][0]
    metal_first = metal["samples"][0]
    if cpu_first["input_hash"] != metal_first["input_hash"]:
        raise RuntimeError("CPU and Metal inputs differ")
    if require_bitstream_equal is None:
        require_bitstream_equal = operation in ("hash", "lossy")
    if not require_bitstream_equal:
        if cpu_first["decoded_hash"] != metal_first["decoded_hash"]:
            raise RuntimeError(f"{operation} CPU and Metal decoded pixels differ")
    elif cpu_first["encoded_hash"] != metal_first["encoded_hash"]:
        raise RuntimeError(f"{operation} CPU and Metal bitstreams differ")


def write_jsonl(stream, record: dict[str, Any]) -> None:
    stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()


def roles_for_seeds(seeds: tuple[int, ...]) -> dict[int, str]:
    if len(seeds) < 3:
        raise ValueError("at least three seeds are required (including holdout)")
    holdout_count = max(1, len(seeds) // 3)
    return {
        seed: "holdout" if index >= len(seeds) - holdout_count else "tune"
        for index, seed in enumerate(seeds)
    }


def make_cases(args: argparse.Namespace) -> list[dict[str, Any]]:
    roles = roles_for_seeds(args.seeds)
    cases: list[dict[str, Any]] = []
    for operation in args.operations:
        sides = args.sides or DEFAULT_SIDES[operation]
        for content in args.contents:
            for method in args.methods:
                for side in sides:
                    for seed in args.seeds:
                        for execution in args.executions:
                            trials = args.cold_trials if execution == "cold" else 1
                            for trial in range(trials):
                                cases.append({
                                    "operation": operation,
                                    "content": content,
                                    "method": method,
                                    "side": side,
                                    "seed": seed,
                                    "role": roles[seed],
                                    "execution": execution,
                                    "trial": trial,
                                })
    return cases


def metadata(root: Path, args: argparse.Namespace, case_count: int) -> dict[str, Any]:
    runner_bytes = args.runner.read_bytes()
    return {
        "record": "metadata",
        "schema_version": SCHEMA_VERSION,
        "git_commit": command_output(["git", "rev-parse", "HEAD"], root),
        "git_dirty": bool(command_output(["git", "status", "--porcelain"], root)),
        "runner": str(args.runner.resolve()),
        "runner_sha256": hashlib.sha256(runner_bytes).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "case_blocks": case_count,
        "matrix_seed": args.matrix_seed,
        "operations": args.operations,
        "contents": args.contents,
        "methods": args.methods,
        "seeds": args.seeds,
        "executions": args.executions,
        "cold_trials": args.cold_trials,
        "warmups": args.warmups,
        "warm_samples": args.warm_samples,
        "environment": {
            "os_version": command_output(["sw_vers", "-productVersion"], root),
            "hardware": command_output(["sysctl", "-n", "machdep.cpu.brand_string"], root),
        },
    }


def run_experiment(args: argparse.Namespace) -> int:
    if not args.acknowledge_exclusive_session:
        raise SystemExit(
            "refusing to collect timings without --acknowledge-exclusive-session"
        )
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    root = Path(__file__).resolve().parents[1]
    cases = make_cases(args)
    randomizer = random.Random(args.matrix_seed)
    randomizer.shuffle(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        write_jsonl(output, metadata(root, args, len(cases)))
        for block_index, case in enumerate(cases):
            variants = ["cpu", "metal"]
            randomizer.shuffle(variants)
            results: dict[str, dict[str, Any]] = {}
            pair_id = f"b{block_index:07d}"
            for variant in variants:
                cold = case["execution"] == "cold"
                command = runner_command(
                    args.runner,
                    case,
                    variant,
                    0 if cold else args.warmups,
                    1 if cold else args.warm_samples,
                    True,
                )
                results[variant] = invoke_runner(
                    command, case["operation"], variant
                )
            verify_pair(case["operation"], results["cpu"], results["metal"])
            eligible = case["operation"] in results["metal"]["dispatches"]
            for variant in variants:
                for sample in results[variant]["samples"]:
                    sample.update({
                        "pair_id": pair_id,
                        "execution": case["execution"],
                        "trial": case["trial"],
                        "role": case["role"],
                        "dispatches": results[variant]["dispatches"],
                        "eligible": eligible,
                    })
                    write_jsonl(output, sample)
            if block_index % 25 == 0:
                print(f"completed {block_index + 1}/{len(cases)} blocks", file=sys.stderr)
    return 0


def smoke(args: argparse.Namespace) -> int:
    cases = [
        {"operation": operation, "content": "photo", "side": 256,
         "method": method, "seed": 101}
        for operation in OPERATIONS for method in (0, 4, 6)
    ]
    observed_operations = set()
    for case in cases:
        results = {
            variant: invoke_runner(
                runner_command(args.runner, case, variant, 1, 2, False),
                case["operation"], variant,
            )
            for variant in ("cpu", "metal")
        }
        verify_pair(case["operation"], results["cpu"], results["metal"])
        if case["operation"] in results["metal"]["dispatches"]:
            observed_operations.add(case["operation"])
    missing = set(OPERATIONS) - observed_operations
    if missing:
        raise RuntimeError(f"Metal dispatch not observed for operations: {sorted(missing)}")
    print(f"PASS: {len(cases)} untimed correctness/determinism smoke pairs")
    return 0


def plan(args: argparse.Namespace) -> int:
    cases = make_cases(args)
    cold = sum(case["execution"] == "cold" for case in cases)
    warm = len(cases) - cold
    maximum_pixels = max(case["side"] ** 2 for case in cases)
    print(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "case_blocks": len(cases),
        "runner_invocations": len(cases) * 2,
        "cold_blocks": cold,
        "warm_blocks": warm,
        "timed_encodes": cold * 2 + warm * 2 * args.warm_samples,
        "maximum_pixels": maximum_pixels,
        "maximum_input_mib": round(maximum_pixels * 4 / 2**20, 1),
        "note": "plan only; no encoder or timing clock was invoked",
    }, indent=2, sort_keys=True))
    return 0


def bootstrap_median_ci(values: list[float], seed: str) -> tuple[float, float, float]:
    if len(values) < 5:
        return statistics.median(values), -math.inf, math.inf
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    medians = []
    for _ in range(2000):
        medians.append(statistics.median(rng.choice(values) for _ in values))
    medians.sort()
    return (
        statistics.median(values),
        medians[int(0.025 * len(medians))],
        medians[int(0.975 * len(medians))],
    )


def analyze(args: argparse.Namespace) -> int:
    records = [json.loads(line) for line in args.input.read_text().splitlines()]
    metadata_record = next(record for record in records if record["record"] == "metadata")
    samples = [record for record in records if record["record"] == "sample"]
    by_pair: dict[str, dict[str, list[dict[str, Any]]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for sample in samples:
        if sample["eligible"]:
            by_pair[sample["pair_id"]][sample["variant"]].append(sample)

    observations: dict[tuple[Any, ...], list[float]] = collections.defaultdict(list)
    for variants in by_pair.values():
        if set(variants) != {"cpu", "metal"}:
            continue
        cpu_samples = sorted(variants["cpu"], key=lambda sample: sample["sequence"])
        metal_samples = sorted(variants["metal"], key=lambda sample: sample["sequence"])
        if len(cpu_samples) != len(metal_samples):
            continue
        exemplar = variants["cpu"][0]
        key = (
            exemplar["operation"], exemplar["content"], exemplar["method"],
            exemplar["execution"], exemplar["width"], exemplar["role"],
        )
        observations[key].extend(
            math.log(metal["elapsed_ns"] / cpu["elapsed_ns"])
            for cpu, metal in zip(cpu_samples, metal_samples)
        )

    evidence: dict[tuple[Any, ...], dict[str, Any]] = {}
    for key, values in observations.items():
        median, low, high = bootstrap_median_ci(values, repr(key))
        evidence[key] = {
            "pairs": len(values),
            "ratio": math.exp(median),
            "ci_low": math.exp(low) if math.isfinite(low) else 0.0,
            "ci_high": math.exp(high) if math.isfinite(high) else math.inf,
            "wins": len(values) >= args.minimum_pairs and math.exp(high) <= 1 - args.margin,
        }

    entries = []
    for operation in OPERATIONS:
        for method in METHODS:
            for execution in ("cold", "warm"):
                content_thresholds = []
                complete = True
                for content in CONTENTS:
                    sizes = sorted({
                        key[4] for key in evidence
                        if key[:4] == (operation, content, method, execution)
                    })
                    threshold = None
                    for index, side in enumerate(sizes):
                        if len(sizes) - index < 2:
                            continue
                        stable = True
                        for candidate_side in sizes[index:]:
                            for role in ("tune", "holdout"):
                                item = evidence.get((operation, content, method,
                                                     execution, candidate_side, role))
                                if item is None or not item["wins"]:
                                    stable = False
                        if stable:
                            threshold = side * side
                            break
                    if threshold is None:
                        complete = False
                        break
                    content_thresholds.append(threshold)
                if complete:
                    entries.append({
                        "operation": operation,
                        "method": method,
                        "execution": execution,
                        "minimum_pixels": max(content_thresholds),
                        "content_rule": "worst_case_across_classes",
                        "margin": args.margin,
                    })

    policy = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "fallback": "cpu",
        "source": {
            "results": str(args.input),
            "git_commit": metadata_record["git_commit"],
            "runner_sha256": metadata_record["runner_sha256"],
        },
        "entries": entries,
        "decision": {
            "minimum_pairs_per_role": args.minimum_pairs,
            "required_metal_margin": args.margin,
            "requires_tune_and_holdout_ci": True,
            "requires_two_or_more_winning_sizes_through_maximum": True,
            "missing_entry_means": "cpu",
        },
    }
    args.output.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(entries)} conservative candidate entries to {args.output}")
    return 0


def add_matrix_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--operations", type=lambda x: csv_values(x),
                        default=OPERATIONS)
    parser.add_argument("--contents", type=lambda x: csv_values(x),
                        default=CONTENTS)
    parser.add_argument("--methods", type=lambda x: csv_values(x, int),
                        default=METHODS)
    parser.add_argument("--seeds", type=lambda x: csv_values(x, int),
                        default=(101, 202, 303))
    parser.add_argument("--executions", type=lambda x: csv_values(x),
                        default=("cold", "warm"))
    parser.add_argument("--sides", type=lambda x: csv_values(x, int))
    parser.add_argument("--cold-trials", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--warm-samples", type=int, default=9)
    parser.add_argument("--matrix-seed", type=int, default=0x4D455441)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--runner", required=True, type=Path)
    smoke_parser.set_defaults(function=smoke)

    plan_parser = subparsers.add_parser("plan")
    add_matrix_arguments(plan_parser)
    plan_parser.set_defaults(function=plan)

    run_parser = subparsers.add_parser("run")
    add_matrix_arguments(run_parser)
    run_parser.add_argument("--runner", required=True, type=Path)
    run_parser.add_argument("--output", required=True, type=Path)
    run_parser.add_argument("--acknowledge-exclusive-session", action="store_true")
    run_parser.set_defaults(function=run_experiment)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--input", required=True, type=Path)
    analyze_parser.add_argument("--output", required=True, type=Path)
    analyze_parser.add_argument("--minimum-pairs", type=int, default=5)
    analyze_parser.add_argument("--margin", type=float, default=0.05)
    analyze_parser.set_defaults(function=analyze)

    args = parser.parse_args()
    if hasattr(args, "runner") and not args.runner.is_file():
        parser.error(f"runner does not exist: {args.runner}")
    return args.function(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
