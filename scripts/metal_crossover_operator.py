#!/usr/bin/env python3
"""Execute a fully predefined Metal crossover operator preset."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

import benchmark_metal as harness


SCHEMA = "libwebp-metal-crossover-preset-v1"


def load_preset(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    preset = json.loads(raw)
    if preset.get("schema") != SCHEMA:
        raise ValueError(f"unexpected preset schema: {preset.get('schema')}")
    if preset.get("status") != "predefined":
        raise ValueError("operator accepts only predefined presets")
    included_sections = []
    included_hashes = []
    for included in preset.get("include_presets", []):
        included_preset, included_hash = load_preset(path.parent / included)
        included_sections.extend(included_preset["sections"])
        included_hashes.append(included_hash)
    preset["sections"] = included_sections + preset["sections"]
    section_ids = [section["id"] for section in preset["sections"]]
    if len(section_ids) != len(set(section_ids)):
        raise ValueError("preset section IDs must be unique")
    if not any(section.get("preserve_item1_warm_guards")
               for section in preset["sections"]):
        raise ValueError("preset is missing the item-1 warm guard section")
    digest = hashlib.sha256(raw)
    for included_hash in included_hashes:
        digest.update(included_hash.encode("ascii"))
    return preset, digest.hexdigest()


def expand_cases(preset: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for section in preset["sections"]:
        methods = section["methods"]
        executions = section["executions"]
        default_seeds = section.get("seed_variants", [{"seed": 0, "role": "guard"}])
        roles = set()
        section_cases = list(section.get("cases", []))
        for grid in section.get("case_grids", []):
            for content in grid["contents"]:
                for width, height in grid["dimensions"]:
                    section_cases.append({
                        "case_id": f"{content}-{width}x{height}",
                        "content": content,
                        "width": width,
                        "height": height,
                    })
        for base_case in section_cases:
            seeds = base_case.get("seed_variants", default_seeds)
            for seed in seeds:
                roles.add(seed["role"])
                for method in methods:
                    for execution, execution_config in executions.items():
                        for trial in range(execution_config["blocks"]):
                            case = dict(base_case)
                            case.update({
                                "section_id": section["id"],
                                "section_kind": section["kind"],
                                "operation": section["operation"],
                                "method": method,
                                "seed": seed["seed"],
                                "role": seed["role"],
                                "execution": execution,
                                "trial": trial,
                                "warmups": execution_config["warmups"],
                                "samples": execution_config["samples"],
                                "expected_dispatches": (
                                    base_case["expected_dispatches"]
                                    if "expected_dispatches" in base_case
                                    else section["expected_dispatches"]
                                ),
                                "require_bitstream_equal": base_case.get(
                                    "require_bitstream_equal",
                                    section.get("require_bitstream_equal", False),
                                ),
                            })
                            blocks.append(case)
        if section["kind"] == "policy_evidence" and roles != {"tune", "holdout"}:
            raise ValueError(
                f"policy section {section['id']} must have tune and holdout roles"
            )
    return blocks


def command_output(argv: list[str], root: Path) -> str:
    try:
        return subprocess.check_output(argv, cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def metadata(
    root: Path,
    preset_path: Path,
    preset: dict[str, Any],
    preset_sha256: str,
    runner: Path,
    blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "record": "metadata",
        "schema_version": 2,
        "preset_schema": SCHEMA,
        "preset_name": preset["name"],
        "preset": str(preset_path.resolve()),
        "preset_sha256": preset_sha256,
        "git_commit": command_output(["git", "rev-parse", "HEAD"], root),
        "git_status": command_output(["git", "status", "--short"], root),
        "runner": str(runner.resolve()),
        "runner_sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hardware": command_output(["sysctl", "-n", "machdep.cpu.brand_string"], root),
        "os_version": command_output(["sw_vers", "-productVersion"], root),
        "power": command_output(["pmset", "-g", "batt"], root),
        "thermal": command_output(["pmset", "-g", "therm"], root),
        "matrix_seed": preset["matrix_seed"],
        "pair_blocks": len(blocks),
        "fixed_matrix": True,
        "calibration": False,
    }


def reference_hash(case: dict[str, Any], variant: str) -> str | None:
    reference = case.get("reference_sha256")
    if reference is None:
        return None
    return reference[str(case["method"])][variant]


def run_variant(
    runner: Path,
    case: dict[str, Any],
    variant: str,
    artifact_dir: Path,
    pair_id: str,
) -> dict[str, Any]:
    expected_hash = reference_hash(case, variant)
    artifact = artifact_dir / f"{pair_id}-{variant}.webp" if expected_hash else None
    command = harness.runner_command(
        runner,
        case,
        variant,
        case["warmups"] if case["execution"] == "warm" else 0,
        case["samples"],
        True,
        artifact,
    )
    result = harness.invoke_runner(command, case["operation"], variant)
    result["artifact_sha256"] = None
    if artifact is not None:
        result["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        artifact.unlink()
        if result["artifact_sha256"] != expected_hash:
            raise RuntimeError(
                f"reference bitstream mismatch for {case['case_id']} method "
                f"{case['method']} {variant}: {result['artifact_sha256']} != "
                f"{expected_hash}"
            )
    return result


def validate_dispatch(case: dict[str, Any], results: dict[str, dict[str, Any]]) -> None:
    if results["cpu"]["dispatches"]:
        raise RuntimeError(
            f"CPU dispatched Metal for {case['case_id']}: "
            f"{results['cpu']['dispatches']}"
        )
    expected = sorted(case["expected_dispatches"])
    if results["metal"]["dispatches"] != expected:
        raise RuntimeError(
            f"Metal dispatch mismatch for {case['case_id']} method {case['method']}: "
            f"{results['metal']['dispatches']} != {expected}"
        )


def distribution(values: list[float]) -> dict[str, float | int]:
    median = statistics.median(values)
    return {
        "n": len(values),
        "min": min(values),
        "median": median,
        "max": max(values),
        "mad": statistics.median(abs(value - median) for value in values),
    }


def summarize(raw_path: Path, summary_path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in raw_path.read_text().splitlines()]
    samples = [record for record in records if record["record"] == "sample"]
    grouped: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = (
        collections.defaultdict(lambda: collections.defaultdict(list))
    )
    for sample in samples:
        key = (
            sample["section_id"], sample["case_id"], sample["content"],
            sample["width"], sample["height"], sample["method"],
            sample["execution"], sample["role"],
        )
        grouped[key][sample["variant"]].append(sample)
    groups = []
    for key, variants in sorted(grouped.items()):
        cpu = sorted(variants["cpu"], key=lambda value: (value["pair_id"],
                                                          value["sequence"]))
        metal = sorted(variants["metal"], key=lambda value: (value["pair_id"],
                                                              value["sequence"]))
        if len(cpu) != len(metal):
            raise RuntimeError(f"unbalanced CPU/Metal samples in summary group {key}")
        ratios = [m["elapsed_ns"] / c["elapsed_ns"] for c, m in zip(cpu, metal)]
        groups.append({
            "section_id": key[0], "case_id": key[1], "content": key[2],
            "width": key[3], "height": key[4], "method": key[5],
            "execution": key[6], "role": key[7],
            "cpu_ns": distribution([value["elapsed_ns"] for value in cpu]),
            "metal_ns": distribution([value["elapsed_ns"] for value in metal]),
            "metal_over_cpu": distribution(ratios),
        })
    summary = {
        "schema": "libwebp-metal-crossover-summary-v1",
        "source": str(raw_path.resolve()),
        "aggregation": "paired sequence ratios; median/MAD/min/max; no pooling across content",
        "groups": groups,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def plan(preset_path: Path) -> int:
    preset, preset_sha256 = load_preset(preset_path)
    blocks = expand_cases(preset)
    measured = sum(2 * case["samples"] for case in blocks)
    warmups = sum(
        2 * case["warmups"] for case in blocks if case["execution"] == "warm"
    )
    maximum_pixels = max(case["width"] * case["height"] for case in blocks)
    print(json.dumps({
        "preset": preset["name"],
        "preset_sha256": preset_sha256,
        "pair_blocks": len(blocks),
        "runner_invocations": 2 * len(blocks),
        "measured_records": measured,
        "untimed_warmup_encodes": warmups,
        "total_encodes": measured + warmups,
        "maximum_pixels": maximum_pixels,
        "maximum_input_mib": round(maximum_pixels * 4 / 2**20, 1),
        "note": "plan only; no runner or timing clock was invoked",
    }, indent=2, sort_keys=True))
    return 0


def run(args: argparse.Namespace) -> int:
    if not args.acknowledge_exclusive_session:
        raise ValueError("--acknowledge-exclusive-session is required")
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise ValueError("WEBP_BENCHMARK_SESSION=exclusive is required")
    if args.output_dir.exists():
        raise ValueError(f"refusing to overwrite output directory: {args.output_dir}")
    preset, preset_sha256 = load_preset(args.preset)
    blocks = expand_cases(preset)
    rng = random.Random(preset["matrix_seed"])
    rng.shuffle(blocks)
    args.output_dir.mkdir(parents=True)
    artifact_dir = args.output_dir / ".artifacts"
    artifact_dir.mkdir()
    raw_path = args.output_dir / "raw.jsonl"
    validity_path = args.output_dir / "validity.json"
    root = Path(__file__).resolve().parents[1]
    completed_blocks = 0
    reference_checks = 0
    try:
        with raw_path.open("x", encoding="utf-8") as output:
            harness.write_jsonl(
                output,
                metadata(root, args.preset, preset, preset_sha256,
                         args.runner, blocks),
            )
            for block_index, case in enumerate(blocks):
                pair_id = f"p{block_index:05d}"
                variants = ["cpu", "metal"]
                rng.shuffle(variants)
                results = {
                    variant: run_variant(
                        args.runner, case, variant, artifact_dir, pair_id
                    )
                    for variant in variants
                }
                validate_dispatch(case, results)
                harness.verify_pair(
                    case["operation"], results["cpu"], results["metal"],
                    case["require_bitstream_equal"],
                )
                reference_checks += sum(
                    results[variant]["artifact_sha256"] is not None
                    for variant in variants
                )
                for variant in variants:
                    for sample in results[variant]["samples"]:
                        sample.update({
                            "pair_id": pair_id,
                            "section_id": case["section_id"],
                            "section_kind": case["section_kind"],
                            "case_id": case["case_id"],
                            "execution": case["execution"],
                            "trial": case["trial"],
                            "role": case["role"],
                            "dispatches": results[variant]["dispatches"],
                            "dispatch_valid": True,
                            "artifact_sha256": results[variant]["artifact_sha256"],
                        })
                        harness.write_jsonl(output, sample)
                completed_blocks += 1
                if completed_blocks % 25 == 0:
                    print(
                        f"completed {completed_blocks}/{len(blocks)} pair blocks",
                        file=sys.stderr,
                    )
        summary = summarize(raw_path, args.output_dir / "summary.json")
        validity = {
            "schema": "libwebp-metal-crossover-validity-v1",
            "valid": True,
            "preset_sha256": preset_sha256,
            "expected_pair_blocks": len(blocks),
            "completed_pair_blocks": completed_blocks,
            "measured_records": sum(2 * case["samples"] for case in blocks),
            "summary_groups": len(summary["groups"]),
            "reference_bitstream_checks": reference_checks,
            "checks": [
                "fixed preset and randomized paired CPU/Metal ordering",
                "exact sample counts",
                "operation-specific dispatch proof",
                "within-backend determinism",
                "CPU/Metal decoded equality or required bitstream equality",
                "item-1 reference bitstream hashes where specified",
                "separate tune and holdout roles for policy evidence",
            ],
        }
        validity_path.write_text(json.dumps(validity, indent=2, sort_keys=True) + "\n")
        fail_closed = {
            "schema_version": 1,
            "status": "untuned",
            "fallback": "cpu",
            "source": {
                "preset_sha256": preset_sha256,
                "raw": str(raw_path.resolve()),
                "summary": str((args.output_dir / "summary.json").resolve()),
                "note": "Sol interpretation and confirmation are required before entries may be added."
            },
            "entries": [],
        }
        (args.output_dir / "policy-untuned.json").write_text(
            json.dumps(fail_closed, indent=2, sort_keys=True) + "\n"
        )
    except Exception as error:
        validity_path.write_text(json.dumps({
            "schema": "libwebp-metal-crossover-validity-v1",
            "valid": False,
            "preset_sha256": preset_sha256,
            "expected_pair_blocks": len(blocks),
            "completed_pair_blocks": completed_blocks,
            "error": str(error),
        }, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        if artifact_dir.exists() and not any(artifact_dir.iterdir()):
            artifact_dir.rmdir()
    print(args.output_dir.resolve())
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    default_preset = root / "scripts" / "metal_crossover_focused_v1.json"
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--preset", type=Path, default=default_preset)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--preset", type=Path, default=default_preset)
    run_parser.add_argument("--runner", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--acknowledge-exclusive-session", action="store_true")
    args = parser.parse_args()
    if args.command == "plan":
        return plan(args.preset)
    if not args.runner.is_file():
        parser.error(f"runner does not exist: {args.runner}")
    return run(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
