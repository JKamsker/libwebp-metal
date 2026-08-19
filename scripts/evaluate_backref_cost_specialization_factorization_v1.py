#!/usr/bin/env python3
"""Frozen independent evaluator for specialization factorization v1 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_specialization_factorization_v1_manifest.json"
PAIRS = (("B", "L"), ("L", "H"), ("B", "H"))
METRICS = {
    "dp_total": lambda row: row["stages"]["backref_cost_dp_total"]["ns"],
    "dp_steady": lambda row: row["stages"]["backref_cost_dp_steady"]["ns"],
    "whole_encode": lambda row: row["total_ns"],
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def verify_index(evidence: Path) -> dict:
    index = load_json(evidence / "artifact-hashes.json")
    rows = index["artifacts"]
    names = [row["path"] for row in rows]
    if names != sorted(names) or len(names) != len(set(names)):
        raise RuntimeError("artifact hash index order/membership is invalid")
    actual = sorted(path.relative_to(evidence).as_posix()
                    for path in evidence.rglob("*") if path.is_file() and
                    path.name != "artifact-hashes.json")
    if names != actual:
        raise RuntimeError("artifact hash index does not cover exact evidence tree")
    for row in rows:
        path = evidence / row["path"]
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise RuntimeError(f"artifact hash mismatch: {row['path']}")
    return {"indexed_artifacts": len(rows),
            "index_sha256": sha256(evidence / "artifact-hashes.json")}


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    location = probability * (len(ordered) - 1)
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize(values: list[float], seed: int) -> dict:
    if len(values) != 12:
        raise RuntimeError("every frozen pairwise statistic requires 12 rows")
    generator = random.Random(seed)
    boot = []
    for _ in range(100000):
        boot.append(sum(values[generator.randrange(len(values))]
                        for _ in values) / len(values))
    return {
        "paired_percentages": values,
        "count": len(values),
        "mean_percent": statistics.fmean(values),
        "median_percent": statistics.median(values),
        "sample_stddev_percent": statistics.stdev(values),
        "minimum_percent": min(values),
        "maximum_percent": max(values),
        "negative_count": sum(value < 0 for value in values),
        "zero_count": sum(value == 0 for value in values),
        "positive_count": sum(value > 0 for value in values),
        "bootstrap_mean_ci95_percent": [percentile(boot, 0.025),
                                         percentile(boot, 0.975)],
        "bootstrap_resamples": 100000,
        "bootstrap_seed": seed,
    }


def classify(layout: float, hint: float, total: float) -> str:
    if abs(total) < 0.10:
        return "indeterminate-small"
    if layout * hint < 0:
        return "interaction-mixed-opposite-sign"
    if abs(layout) >= 0.60 * abs(total) and abs(hint) < 0.60 * abs(total):
        return "layout-dominant"
    if abs(hint) >= 0.60 * abs(total) and abs(layout) < 0.60 * abs(total):
        return "hint-dominant"
    return "interaction-mixed"


def evaluate(evidence: Path) -> dict:
    manifest = load_json(MANIFEST)
    integrity = verify_index(evidence)
    plan = load_json(evidence / "profile-plan.json")
    if len(plan) != 36 or [row["ordinal"] for row in plan] != list(range(36)):
        raise RuntimeError("profile plan count/order mismatch")
    expected = []
    ordinal = 0
    for case in manifest["corpus"]:
        for method in manifest["protocol"]["methods"]:
            for repetition, variants in enumerate(
                    manifest["protocol"]["variant_order"]):
                for variant in variants:
                    expected.append((ordinal, case["case_id"], method,
                                     repetition, variant))
                    ordinal += 1
    observed = [(row["ordinal"], row["case_id"], row["method"],
                 row["repetition"], row["variant"]) for row in plan]
    if observed != expected:
        raise RuntimeError("profile plan differs from frozen order")

    retained: dict[tuple[str, int, int, str, int], dict] = {}
    output_digests: dict[tuple[str, int, int, int], set[tuple[int, str]]] = {}
    stage_records = runner_records = retained_records = 0
    repetition_medians: dict[tuple[str, int, str], list[float]] = {}
    repetition_shares: dict[tuple[str, int, str], list[dict[str, float]]] = {}
    for profile in plan:
        stage_path = evidence / "stages" / (profile["profile_id"] + ".jsonl")
        runner_path = evidence / "runner" / (profile["profile_id"] + ".jsonl")
        stderr_path = evidence / "runner" / (profile["profile_id"] + ".stderr")
        stages = load_jsonl(stage_path)
        outputs = load_jsonl(runner_path)
        if stderr_path.read_bytes() or len(stages) != 5 or len(outputs) != 5:
            raise RuntimeError("profile stream inventory/stderr mismatch")
        stage_records += len(stages)
        runner_records += len(outputs)
        if [row.get("iteration") for row in outputs] != list(range(5)) or \
                [row.get("sample_role") for row in outputs] != \
                ["warmup", "retained", "retained", "retained", "retained"] or \
                [row.get("encode_index") for row in stages] != list(range(5)) or \
                [row.get("sample_role") for row in stages] != \
                ["warmup", "warm", "warm", "warm", "warm"]:
            raise RuntimeError("warmup/retained lifecycle mismatch")
        warm = stages[1:]
        kept_outputs = outputs[1:]
        if len(warm) != 4 or len(kept_outputs) != 4:
            raise RuntimeError("retained row inventory mismatch")
        retained_records += len(warm)
        repeat_key = (profile["case_id"], profile["method"], profile["variant"])
        total_median = statistics.median(row["total_ns"] for row in warm)
        repetition_medians.setdefault(repeat_key, []).append(total_median)
        repetition_shares.setdefault(repeat_key, []).append({
            timer: statistics.median(row["stages"][timer]["ns"]
                                     for row in warm) / total_median
            for timer in manifest["acceptance"]["required_timer_stages"]})
        for retained_ordinal, (stage, output) in enumerate(zip(warm, kept_outputs)):
            if output.get("schema") != \
                    "libwebp-backref-cost-specialization-factorization-v1-output-v1" or \
                    stage.get("schema") != "libwebp-encoder-stage-v1" or \
                    stage["backend"] != profile["variant"] or \
                    output["variant"] != profile["variant"] or \
                    output["case_id"] != profile["case_id"] or \
                    stage["case_id"] != profile["case_id"] or \
                    stage["method"] != profile["method"] or \
                    output["method"] != profile["method"] or \
                    stage.get("ok") is not True or stage.get("error_code") != 0:
                raise RuntimeError("variant/method row identity mismatch")
            for timer in manifest["acceptance"]["required_timer_stages"]:
                if timer not in stage["stages"]:
                    raise RuntimeError(f"missing timer stage: {timer}")
            key = (profile["case_id"], profile["method"],
                   profile["repetition"], profile["variant"], retained_ordinal)
            retained[key] = stage
            digest_key = (profile["case_id"], profile["method"],
                          profile["repetition"], retained_ordinal)
            output_digests.setdefault(digest_key, set()).add(
                (output["bitstream_bytes"], output["bitstream_fnv1a64"]))
    if stage_records != 180 or runner_records != 180 or retained_records != 144:
        raise RuntimeError("global raw row count mismatch")
    if any(len(values) != 1 for values in output_digests.values()):
        raise RuntimeError("B/L/H timed bitstreams differ")
    ratios = {}
    share_ranges = {}
    for key, medians in repetition_medians.items():
        if len(medians) != 3 or min(medians) <= 0:
            raise RuntimeError("repeatability median inventory invalid")
        ratio = max(medians) / min(medians)
        ratios["/".join(map(str, key))] = ratio
        if ratio > manifest["acceptance"]["repeatability_max_ratio"]:
            raise RuntimeError("repeatability threshold failed")
        shares = repetition_shares[key]
        ranges = {
            timer: max(row[timer] for row in shares) -
                   min(row[timer] for row in shares)
            for timer in manifest["acceptance"]["required_timer_stages"]}
        share_ranges["/".join(map(str, key))] = ranges
        if any(value > 0.10 for value in ranges.values()):
            raise RuntimeError("repeatability stage-share threshold failed")

    work = load_jsonl(evidence / "work-metrics.jsonl")
    summary = load_json(evidence / "work-metric-summary.json")
    codegen = load_json(evidence / "codegen.json")
    correctness = load_json(evidence / "correctness.json")
    if len(work) != 12 or summary.get("rows") != 12 or \
            not summary.get("baseline_layout_work_equal") or \
            not summary.get("hint_boundary_active_only_in_H") or \
            codegen.get("recorder_symbols_in_timed_binary") is not False or \
            not codegen.get("baseline_layout_mnemonics_equal") or \
            not codegen.get("all_six_private_addresses_distinct") or \
            len(correctness) != 4 or \
            not all(row.get("all_variants_equal") for row in correctness):
        raise RuntimeError("correctness/work/codegen gate failed")

    statistics_rows = {}
    classifications = {}
    cell_index = 0
    for case in manifest["corpus"]:
        for method in manifest["protocol"]["methods"]:
            cell = f"{case['category']}-m{method}"
            statistics_rows[cell] = {}
            classifications[cell] = {}
            for metric_index, (metric, getter) in enumerate(METRICS.items()):
                statistics_rows[cell][metric] = {}
                means = {}
                for pair_index, (left, right) in enumerate(PAIRS):
                    values = []
                    for repetition in range(3):
                        for retained_ordinal in range(4):
                            lhs = getter(retained[(case["case_id"], method,
                                                   repetition, left,
                                                   retained_ordinal)])
                            rhs = getter(retained[(case["case_id"], method,
                                                   repetition, right,
                                                   retained_ordinal)])
                            if lhs <= 0:
                                raise RuntimeError("nonpositive timing denominator")
                            values.append(100.0 * (rhs - lhs) / lhs)
                    label = f"{left}_to_{right}"
                    seed = 0x424C4801 + cell_index * 100 + metric_index * 10 + pair_index
                    row = summarize(values, seed)
                    statistics_rows[cell][metric][label] = row
                    means[label] = row["mean_percent"]
                classifications[cell][metric] = classify(
                    means["B_to_L"], means["L_to_H"], means["B_to_H"])
            cell_index += 1

    material = manifest["acceptance"]["maximum_material_regression_percent"]
    promotion_checks = []
    for cell, metrics in statistics_rows.items():
        for metric in ("dp_steady", "whole_encode"):
            row = metrics[metric]["B_to_H"]
            promotion_checks.append({
                "cell": cell, "metric": metric,
                "mean_negative": row["mean_percent"] < 0,
                "upper_ci_nonpositive": row["bootstrap_mean_ci95_percent"][1] <= 0,
                "no_material_paired_regression": row["maximum_percent"] <= material,
            })
    production = all(all(value for key, value in row.items()
                         if key not in ("cell", "metric"))
                     for row in promotion_checks)
    lease = load_json(evidence / "lease-record.json")
    if not (lease.get("acquired") and lease.get("released")):
        raise RuntimeError("exclusive lease release proof absent")
    operator_status = load_json(evidence / "operator-status.json")
    if operator_status.get("status") != "complete":
        raise RuntimeError("operator did not complete")
    return {
        "schema": "libwebp-backref-cost-specialization-factorization-v1-evaluation-v1",
        "status": "PASS_DIAGNOSTIC",
        "integrity": integrity,
        "raw_counts": {"profile_processes": 36, "stage_records": 180,
                       "runner_records": 180, "retained_stage_records": 144,
                       "work_rows": 12, "correctness_cells": 4},
        "statistics": statistics_rows,
        "classifications": classifications,
        "repeatability_ratios": ratios,
        "repeatability_required_stage_share_ranges": share_ranges,
        "production_promotion": {
            "passes": production, "checks": promotion_checks,
            "consequence": "ELIGIBLE_FOR_REVIEW" if production else
                           "NO_PRODUCTION_PROMOTION"},
        "no_v16_samples_loaded": True,
        "external_profiler_invocations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.evidence.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "production_promotion": result[
                          "production_promotion"]["passes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
