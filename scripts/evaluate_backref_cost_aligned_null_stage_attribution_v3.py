#!/usr/bin/env python3
"""Frozen independent evaluator for aligned-null stage-attribution V2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v3_identity as identity

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_manifest.json"
EXPECTED_RECEIPT = (ROOT /
    "evidence/backref-cost-aligned-null-stage-attribution-v3-design/four-body-expected-receipt.json")
TOP_LEVEL = (
    "pre_lossless_setup_input", "analysis_transforms",
    "backward_reference_generation", "histogram_construction",
    "entropy_huffman_preparation", "bitstream_serialization",
    "container_output_finalization", "allocation_cleanup_orchestration",
    "residual_unattributed",
)
NESTED = (
    "lossless_hash_chain", "lossless_backward_refs",
    "backref_cost_dp_total", "backref_cost_dp_setup",
    "backref_cost_dp_steady", "backref_cost_traceback",
    "backref_cost_materialize",
)
BOOTSTRAP_RESAMPLES = 100000
BOOTSTRAP_SEED = 0x4E554C33


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
    actual = sorted(path.relative_to(evidence).as_posix()
                    for path in evidence.rglob("*") if path.is_file() and
                    path.name != "artifact-hashes.json")
    if names != sorted(set(names)) or names != actual:
        raise RuntimeError("artifact index membership/order mismatch")
    for row in rows:
        path = evidence / row["path"]
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise RuntimeError(f"artifact hash mismatch: {row['path']}")
    return {"indexed_artifacts": len(rows),
            "index_sha256": sha256(evidence / "artifact-hashes.json")}


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    location = probability * (len(ordered) - 1)
    lower, upper = math.floor(location), math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize(percentages: list[float], deltas_ns: list[float], seed: int,
              alpha: float = 0.05) -> dict:
    if len(percentages) != 16 or len(deltas_ns) != 16:
        raise RuntimeError("every frozen paired statistic requires 16 rows")
    generator = random.Random(seed)
    boot = [sum(percentages[generator.randrange(16)] for _ in range(16)) / 16
            for _ in range(BOOTSTRAP_RESAMPLES)]
    return {
        "paired_percentages": percentages, "paired_deltas_ns": deltas_ns,
        "count": 16, "mean_percent": statistics.fmean(percentages),
        "mean_delta_ns": statistics.fmean(deltas_ns),
        "median_percent": statistics.median(percentages),
        "sample_stddev_percent": statistics.stdev(percentages),
        "minimum_percent": min(percentages), "maximum_percent": max(percentages),
        "negative_count": sum(value < 0 for value in percentages),
        "zero_count": sum(value == 0 for value in percentages),
        "positive_count": sum(value > 0 for value in percentages),
        "bootstrap_mean_ci_percent": [percentile(boot, alpha / 2),
                                       percentile(boot, 1 - alpha / 2)],
        "bootstrap_confidence": 1 - alpha,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": seed,
    }


def null_control(row: dict, bounds: dict) -> dict:
    low, high = row["bootstrap_mean_ci_percent"]
    checks = {
        "absolute_mean_within_bound": abs(row["mean_percent"]) <= 0.75,
        "bootstrap_ci_contains_zero": low <= 0 <= high,
        "bootstrap_ci_endpoints_within_bound": max(abs(low), abs(high)) <= 1.50,
        "all_paired_rows_within_bound":
            max(abs(value) for value in row["paired_percentages"]) <= 3.00,
    }
    return {"passes": all(checks.values()), "checks": checks, "bounds": bounds}


def value(row: dict, metric: str) -> int:
    if metric == "whole_encode":
        return row["total_ns"]
    if metric in TOP_LEVEL:
        return row["top_level_ledger"][metric]["ns"]
    return row["stages"][metric]["ns"]


def evaluate(evidence: Path) -> dict:
    manifest = load_json(MANIFEST)
    expected_receipt = load_json(EXPECTED_RECEIPT)
    identity.validate_machine_receipt(
        expected_receipt, manifest["four_body_receipt_bindings"])
    if manifest["four_body_identity"] != identity.generator_binding():
        raise RuntimeError("Phase 3 canonical four-body domain mismatch")
    integrity = verify_index(evidence)
    plan = load_json(evidence / "profile-plan.json")
    if len(plan) != 32 or [row["ordinal"] for row in plan] != list(range(32)):
        raise RuntimeError("profile plan count/order mismatch")
    expected = []
    ordinal = 0
    for case in manifest["corpus"]:
        for method in manifest["protocol"]["methods"]:
            for repetition, variants in enumerate(manifest["protocol"]["variant_order"]):
                for variant in variants:
                    expected.append((ordinal, case["case_id"], method,
                                     repetition, variant))
                    ordinal += 1
    observed = [(row["ordinal"], row["case_id"], row["method"],
                 row["repetition"], row["variant"]) for row in plan]
    if observed != expected or any(row["variant"] not in ("B", "L") for row in plan):
        raise RuntimeError("profile plan differs from frozen B/L order")

    retained = {}
    stage_records = runner_records = retained_records = 0
    repeat_medians, repeat_shares, output_digests = {}, {}, {}
    for profile in plan:
        stages = load_jsonl(evidence / "stages" / f"{profile['profile_id']}.jsonl")
        outputs = load_jsonl(evidence / "runner" / f"{profile['profile_id']}.jsonl")
        stderr = evidence / "runner" / f"{profile['profile_id']}.stderr"
        if stderr.read_bytes() or len(stages) != 5 or len(outputs) != 5:
            raise RuntimeError("profile stream inventory/stderr mismatch")
        if [row.get("sample_role") for row in outputs] != \
                ["warmup", "retained", "retained", "retained", "retained"] or \
                [row.get("sample_role") for row in stages] != \
                ["warmup", "warm", "warm", "warm", "warm"]:
            raise RuntimeError("warmup/retained lifecycle mismatch")
        stage_records += 5
        runner_records += 5
        retained_records += 4
        warm = stages[1:]
        repeat_key = (profile["case_id"], profile["method"], profile["variant"])
        median_total = statistics.median(row["total_ns"] for row in warm)
        repeat_medians.setdefault(repeat_key, []).append(median_total)
        repeat_shares.setdefault(repeat_key, []).append({
            metric: statistics.median(value(row, metric) for row in warm) /
                    median_total for metric in TOP_LEVEL})
        for retained_ordinal, (stage, output) in enumerate(zip(warm, outputs[1:])):
            if stage.get("schema") != \
                    "libwebp-backref-cost-aligned-null-stage-attribution-v3-stage-ledger-v1" or \
                    stage.get("ledger_valid") is not True or \
                    stage.get("reconciliation_delta_ns") != 0 or \
                    stage.get("ledger_sum_ns") != stage.get("total_ns") or \
                    stage.get("clock_reads") != stage.get("expected_clock_reads") or \
                    stage.get("nested_timers_additive") is not False or \
                    stage.get("backend") != profile["variant"] or \
                    stage.get("ok") is not True:
                raise RuntimeError("ledger/schema/identity gate failed")
            if any(name not in stage["top_level_ledger"] for name in TOP_LEVEL) or \
                    any(name not in stage["stages"] for name in NESTED):
                raise RuntimeError("required ledger or nested timer missing")
            if sum(stage["top_level_ledger"][name]["ns"] for name in TOP_LEVEL) != \
                    stage["total_ns"]:
                raise RuntimeError("top-level ledger does not cover whole encode")
            key = (profile["case_id"], profile["method"], profile["repetition"],
                   profile["variant"], retained_ordinal)
            retained[key] = stage
            digest_key = (profile["case_id"], profile["method"],
                          profile["repetition"], retained_ordinal)
            output_digests.setdefault(digest_key, set()).add(
                (output["bitstream_bytes"], output["bitstream_fnv1a64"]))
    if (stage_records, runner_records, retained_records) != (160, 160, 128):
        raise RuntimeError("global raw row count mismatch")
    if any(len(items) != 1 for items in output_digests.values()):
        raise RuntimeError("B/L timed bitstreams differ")

    ratios, share_ranges = {}, {}
    repeatability_pass = True
    for key, medians in repeat_medians.items():
        ratio = max(medians) / min(medians)
        ratios["/".join(map(str, key))] = ratio
        ranges = {metric: max(row[metric] for row in repeat_shares[key]) -
                          min(row[metric] for row in repeat_shares[key])
                  for metric in TOP_LEVEL}
        share_ranges["/".join(map(str, key))] = ranges
        repeatability_pass &= ratio <= 2.0 and all(v < 0.10 for v in ranges.values())

    work = load_jsonl(evidence / "work-metrics.jsonl")
    work_summary = load_json(evidence / "work-metric-summary.json")
    correctness = load_json(evidence / "correctness.json")
    codegen = load_json(evidence / "codegen.json")
    build_identity = load_json(evidence / "build-identity.json")
    exact_receipt_match = (
        codegen.get("four_body_identity") == identity.generator_binding() and
        codegen.get("symbol_addresses") == expected_receipt["symbol_addresses"] and
        codegen.get("facts") == expected_receipt["facts"] and
        codegen.get("section") == expected_receipt["section"] and
        codegen.get("inter_entry_padding_bytes") == expected_receipt["padding_bytes"] and
        codegen.get("linker_map_sha256") == expected_receipt["linker_map_sha256"] and
        codegen.get("linker_map_extract_sha256") ==
            expected_receipt["linker_map_extract_sha256"] and
        build_identity.get("timed_runner_sha256") ==
            expected_receipt["binary_sha256"] and
        build_identity.get("timed_runner_bytes") == expected_receipt["binary_bytes"] and
        build_identity.get("alignment_section_size_bytes") ==
            expected_receipt["section"]["size_bytes"] and
        build_identity.get("alignment_body_bytes") == expected_receipt["body_bytes"] and
        build_identity.get("alignment_padding_bytes") ==
            expected_receipt["padding_bytes"])
    if len(work) != 8 or work_summary.get("rows") != 8 or \
            not work_summary.get("baseline_layout_work_equal") or \
            not work_summary.get("no_h_variant_present") or \
            len(correctness) != 4 or \
            not exact_receipt_match or \
            not codegen.get("baseline_layout_canonical_instructions_equal") or \
            not codegen.get("all_four_private_addresses_distinct") or \
            not codegen.get("no_h_body_in_candidate_scope"):
        raise RuntimeError("correctness/work/codegen gate failed")

    metrics = ("whole_encode",) + TOP_LEVEL + NESTED
    results = {}
    cell_index = 0
    for case in manifest["corpus"]:
        for method in manifest["protocol"]["methods"]:
            cell = f"{case['category']}-m{method}"
            results[cell] = {}
            for metric_index, metric in enumerate(metrics):
                percentages, deltas, repetition_directions = [], [], []
                for repetition in range(4):
                    repetition_delta = []
                    for retained_ordinal in range(4):
                        lhs = value(retained[(case["case_id"], method, repetition,
                                              "B", retained_ordinal)], metric)
                        rhs = value(retained[(case["case_id"], method, repetition,
                                              "L", retained_ordinal)], metric)
                        if lhs <= 0 and metric != "residual_unattributed":
                            raise RuntimeError("nonpositive timing denominator")
                        delta = rhs - lhs
                        deltas.append(delta)
                        repetition_delta.append(delta)
                        percentages.append(0.0 if lhs == 0 and rhs == 0 else
                                           100.0 * delta / lhs)
                    repetition_directions.append(statistics.fmean(repetition_delta))
                alpha = 0.05 / len(TOP_LEVEL) if metric in TOP_LEVEL else 0.05
                row = summarize(percentages, deltas,
                                BOOTSTRAP_SEED + cell_index * 100 + metric_index,
                                alpha)
                row["direction_consistent_repetitions"] = max(
                    sum(v < 0 for v in repetition_directions),
                    sum(v > 0 for v in repetition_directions))
                results[cell][metric] = row
            cell_index += 1

    primary = results["graphic-m4"]["whole_encode"]
    primary_null = null_control(
        primary, manifest["acceptance"]["mandatory_b_to_l_null_control"])
    reproduced = not primary_null["passes"]
    accounting_pass = repeatability_pass
    attribution_candidates = []
    if reproduced and accounting_pass and primary["mean_delta_ns"] != 0:
        whole_sign = -1 if primary["mean_delta_ns"] < 0 else 1
        for metric in TOP_LEVEL:
            row = results["graphic-m4"][metric]
            low, high = row["bootstrap_mean_ci_percent"]
            fraction = abs(row["mean_delta_ns"]) / abs(primary["mean_delta_ns"])
            direction = -1 if row["mean_delta_ns"] < 0 else \
                        (1 if row["mean_delta_ns"] > 0 else 0)
            checks = {
                "same_direction_as_whole": direction == whole_sign,
                "multiplicity_adjusted_ci_excludes_zero": high < 0 or low > 0,
                "absolute_mean_effect_at_least_0_20_percent":
                    abs(row["mean_percent"]) >= 0.20,
                "absolute_whole_delta_fraction_at_least_0_20": fraction >= 0.20,
                "same_direction_in_at_least_three_of_four_repetitions":
                    row["direction_consistent_repetitions"] >= 3,
            }
            attribution_candidates.append({"bucket": metric,
                                           "whole_delta_fraction": fraction,
                                           "passes": all(checks.values()),
                                           "checks": checks})
    attributed = [row["bucket"] for row in attribution_candidates if row["passes"]]
    if not reproduced:
        decision = "V4_WHOLE_FAILURE_NOT_REPLICATED_NO_STAGE_CAUSE"
    elif not accounting_pass:
        decision = "REPRODUCED_BUT_ACCOUNTING_OR_REPEATABILITY_INCONCLUSIVE"
    elif attributed:
        decision = "REPRODUCED_AND_LOCALIZED"
    else:
        decision = "REPRODUCED_BUT_UNACCOUNTED_INCONCLUSIVE"

    lease = load_json(evidence / "lease-record.json")
    if not (lease.get("acquired") and lease.get("released")):
        raise RuntimeError("exclusive lease proof absent")
    return {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v3-evaluation-v1",
        "status": "PASS_RESEARCH_DIAGNOSTIC", "decision": decision,
        "integrity": integrity,
        "raw_counts": {"profile_processes": 32, "warmups": 32,
                       "retained_rows": 128, "stage_rows": 160,
                       "runner_rows": 160, "work_rows": 8,
                       "correctness_encodes": 16,
                       "bootstrap_resamples_per_statistic": BOOTSTRAP_RESAMPLES},
        "primary_reproduction_test": {"cell": "graphic-m4",
                                      "metric": "whole_encode",
                                      "reproduced": reproduced,
                                      "null_control": primary_null},
        "attribution": {"accounting_and_repeatability_pass": accounting_pass,
                        "multiplicity": "Bonferroni 95% family-wise over 9 top-level buckets",
                        "candidates": attribution_candidates,
                        "localized_buckets": attributed},
        "statistics": results, "repeatability_ratios": ratios,
        "top_level_share_ranges": share_ranges,
        "nested_timers_are_descriptive_non_additive": True,
        "v4_timing_rows_loaded": 0, "h_interpreted": False,
        "production_promotion_authorized": False,
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
                      "decision": result["decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
