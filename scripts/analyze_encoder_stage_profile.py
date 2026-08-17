#!/usr/bin/env python3
"""Validate and analyze an existing encoder stage-profile JSONL run.

This script performs no encoding.  It reconstructs all robust summaries from
the raw records, checks them against the operator-produced baseline, and emits
machine-readable tables for the subsequent human interpretation.
"""

import argparse
import csv
import hashlib
import json
import math
import pathlib
import statistics


RECORD_SCHEMA = "libwebp-encoder-stage-v1"
DATASET_SCHEMA = "libwebp-stage-profile-dataset-v1"
ANALYSIS_SCHEMA = "libwebp-encoder-stage-analysis-v1"
METHODS = (4, 6)
BACKENDS = ("cpu", "metal")
MEASURED_ROLES = ("cold", "warm")
EXPECTED_ROLE_COUNTS = {"cold": 3, "warmup": 1, "warm": 3}
KEY_STAGES = (
    "metal_init",
    "lossless_palette",
    "lossless_predictor",
    "lossless_cross_color",
    "metal_cross_color_dispatch",
    "lossless_hash_chain",
    "metal_hash_pipeline_init",
    "metal_hash_dispatch",
    "lossless_backward_refs",
    "lossless_histogram",
    "lossless_huffman",
    "lossless_bitstream",
)


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_jsonl(path):
    records = []
    with path.open() as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
    return records


def distribution(values):
    if not values:
        raise ValueError("cannot summarize an empty sample")
    median = statistics.median(values)
    return {
        "n": len(values),
        "min": min(values),
        "median": median,
        "max": max(values),
        "mad": statistics.median(abs(value - median) for value in values),
    }


def group_records(records):
    groups = {}
    for record in records:
        if record["sample_role"] == "warmup":
            continue
        key = (record["case_id"], record["method"], record["backend"],
               record["sample_role"])
        groups.setdefault(key, []).append(record)
    return groups


def summarize_group(key, records):
    case_id, method, backend, sample_role = key
    first = records[0]
    total = distribution([record["total_ns"] for record in records])
    stage_names = sorted({name for record in records
                          for name in record["stages"]})
    stages = {}
    for name in stage_names:
        summary = distribution([
            record["stages"].get(name, {}).get("ns", 0)
            for record in records
        ])
        summary["median_share_total"] = summary["median"] / total["median"]
        summary["median_calls"] = statistics.median([
            record["stages"].get(name, {}).get("calls", 0)
            for record in records
        ])
        stages[name] = summary
    return {
        "case_id": case_id,
        "method": method,
        "backend": backend,
        "sample_role": sample_role,
        "quality": first["quality"],
        "exact": first["exact"],
        "thread_level": first["thread_level"],
        "width": first["width"],
        "height": first["height"],
        "pixels": first["pixels"],
        "total_ns": total,
        "output_bytes": distribution([
            record["output_bytes"] for record in records
        ]),
        "metal_cross_color_rate": sum(
            record["metal_cross_color"] for record in records
        ) / len(records),
        "metal_hash_rate": sum(
            record["metal_hash"] for record in records
        ) / len(records),
        "stages": stages,
    }


def compare_json(actual, expected, path="$"):
    """Return paths that differ, using strict keys and tolerant floats."""
    mismatches = []
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            mismatches.append(
                f"{path}: keys {sorted(actual)} != {sorted(expected)}")
            return mismatches
        for key in actual:
            mismatches.extend(compare_json(actual[key], expected[key],
                                           f"{path}.{key}"))
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            mismatches.append(f"{path}: length {len(actual)} != {len(expected)}")
        else:
            for index, (left, right) in enumerate(zip(actual, expected)):
                mismatches.extend(compare_json(left, right,
                                               f"{path}[{index}]"))
    elif (isinstance(actual, (int, float)) and
          isinstance(expected, (int, float)) and
          not isinstance(actual, bool) and not isinstance(expected, bool)):
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9):
            mismatches.append(f"{path}: {actual!r} != {expected!r}")
    elif actual != expected:
        mismatches.append(f"{path}: {actual!r} != {expected!r}")
    return mismatches


def validate(records, cases):
    errors = []
    case_ids = set(cases)
    role_counts = {role: 0 for role in EXPECTED_ROLE_COUNTS}
    combination_counts = {}
    for index, record in enumerate(records):
        prefix = f"record[{index}]"
        if record.get("schema") != RECORD_SCHEMA:
            errors.append(f"{prefix}: unexpected schema")
        if record.get("case_id") not in case_ids:
            errors.append(f"{prefix}: unknown case_id")
        if record.get("method") not in METHODS:
            errors.append(f"{prefix}: unexpected method")
        if record.get("backend") not in BACKENDS:
            errors.append(f"{prefix}: unexpected backend")
        role = record.get("sample_role")
        if role not in EXPECTED_ROLE_COUNTS:
            errors.append(f"{prefix}: unexpected sample_role")
            continue
        role_counts[role] += 1
        if not record.get("ok") or record.get("error_code") != 0:
            errors.append(f"{prefix}: unsuccessful encode")
        case = cases.get(record.get("case_id"), {})
        expected_shape = (case.get("width"), case.get("height"),
                          case.get("pixels"))
        actual_shape = (record.get("width"), record.get("height"),
                        record.get("pixels"))
        if actual_shape != expected_shape:
            errors.append(f"{prefix}: dimensions do not match manifest")
        if record.get("quality") != 75.0 or not record.get("exact") or \
                record.get("thread_level") != 0:
            errors.append(f"{prefix}: unexpected encoder configuration")
        backend = record.get("backend")
        content = case.get("content_class")
        expected_cross = backend == "metal" and content == "photo"
        expected_hash = backend == "metal"
        if record.get("metal_cross_color") != expected_cross:
            errors.append(f"{prefix}: unexpected cross-color dispatch flag")
        if record.get("metal_hash") != expected_hash:
            errors.append(f"{prefix}: unexpected hash dispatch flag")
        key = (record.get("case_id"), record.get("method"), backend, role)
        combination_counts[key] = combination_counts.get(key, 0) + 1

    expected_combinations = len(cases) * len(METHODS) * len(BACKENDS)
    for case_id in sorted(cases):
        for method in METHODS:
            for backend in BACKENDS:
                for role, count in EXPECTED_ROLE_COUNTS.items():
                    key = (case_id, method, backend, role)
                    if combination_counts.get(key, 0) != count:
                        errors.append(
                            f"{key}: count {combination_counts.get(key, 0)} != {count}")
    return {
        "valid": not errors,
        "errors": errors,
        "record_count": len(records),
        "role_counts": role_counts,
        "expected_case_method_backend_combinations": expected_combinations,
        "measured_group_count": len(group_records(records)),
    }


def stage_median(group, name):
    return group["stages"].get(name, {}).get("median", 0)


def stage_share(group, name):
    return group["stages"].get(name, {}).get("median_share_total", 0.0)


def pair_summaries(summaries, cases):
    indexed = {
        (item["case_id"], item["method"], item["backend"],
         item["sample_role"]): item
        for item in summaries
    }
    pairs = []
    for case_id in sorted(cases, key=lambda name: (
            cases[name]["content_class"], cases[name]["pixels"])):
        case = cases[case_id]
        for method in METHODS:
            for role in MEASURED_ROLES:
                cpu = indexed[(case_id, method, "cpu", role)]
                metal = indexed[(case_id, method, "metal", role)]
                cpu_total = cpu["total_ns"]
                metal_total = metal["total_ns"]
                metal_stages = {
                    name: {
                        "median_ns": stage_median(metal, name),
                        "median_share_total": stage_share(metal, name),
                    }
                    for name in KEY_STAGES
                }
                hash_parent_remainder = (
                    stage_median(metal, "lossless_hash_chain") -
                    stage_median(metal, "metal_hash_dispatch") -
                    stage_median(metal, "metal_hash_pipeline_init"))
                cross_parent_remainder = (
                    stage_median(metal, "lossless_cross_color") -
                    stage_median(metal, "metal_cross_color_dispatch"))
                pairs.append({
                    "case_id": case_id,
                    "content_class": case["content_class"],
                    "size_class": case["size_class"],
                    "pixels": case["pixels"],
                    "method": method,
                    "sample_role": role,
                    "cpu_total_ns": cpu_total,
                    "metal_total_ns": metal_total,
                    "cpu_over_metal_median_ratio": (
                        cpu_total["median"] / metal_total["median"]),
                    # These are descriptive bounds from the three observations,
                    # not a confidence interval and not a paired-sample estimate.
                    "cpu_over_metal_observed_ratio_bounds": {
                        "low": cpu_total["min"] / metal_total["max"],
                        "high": cpu_total["max"] / metal_total["min"],
                    },
                    "median_total_delta_ns_cpu_minus_metal": (
                        cpu_total["median"] - metal_total["median"]),
                    "metal_cross_color_rate": metal["metal_cross_color_rate"],
                    "metal_hash_rate": metal["metal_hash_rate"],
                    "metal_stages": metal_stages,
                    # Parent-minus-child is intentionally not called CPU time:
                    # it can include uninstrumented setup and nested encodes.
                    "hash_parent_minus_direct_metal_ns": hash_parent_remainder,
                    "cross_parent_minus_dispatch_ns": cross_parent_remainder,
                })
    return pairs


def cold_warm_summaries(summaries, cases):
    indexed = {
        (item["case_id"], item["method"], item["backend"],
         item["sample_role"]): item
        for item in summaries
    }
    results = []
    for case_id in sorted(cases):
        for method in METHODS:
            for backend in BACKENDS:
                cold = indexed[(case_id, method, backend, "cold")]
                warm = indexed[(case_id, method, backend, "warm")]
                results.append({
                    "case_id": case_id,
                    "content_class": cases[case_id]["content_class"],
                    "size_class": cases[case_id]["size_class"],
                    "method": method,
                    "backend": backend,
                    "cold_total_median_ns": cold["total_ns"]["median"],
                    "warm_total_median_ns": warm["total_ns"]["median"],
                    "cold_minus_warm_total_median_ns": (
                        cold["total_ns"]["median"] -
                        warm["total_ns"]["median"]),
                    "cold_metal_init_median_ns": stage_median(cold, "metal_init"),
                    "warm_metal_init_median_ns": stage_median(warm, "metal_init"),
                    "cold_minus_warm_metal_init_median_ns": (
                        stage_median(cold, "metal_init") -
                        stage_median(warm, "metal_init")),
                })
    return results


def write_csv(path, pairs):
    fields = [
        "case_id", "content_class", "size_class", "pixels", "method",
        "sample_role", "cpu_total_ms", "cpu_total_mad_ms",
        "metal_total_ms", "metal_total_mad_ms", "cpu_over_metal_ratio",
        "observed_ratio_low", "observed_ratio_high",
        "cpu_minus_metal_ms", "metal_cross_color_rate", "metal_hash_rate",
        "hash_parent_minus_direct_metal_ms",
        "cross_parent_minus_dispatch_ms",
    ]
    for stage in KEY_STAGES:
        fields.extend((f"{stage}_ms", f"{stage}_share"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for pair in pairs:
            row = {name: pair[name] for name in (
                "case_id", "content_class", "size_class", "pixels", "method",
                "sample_role", "metal_cross_color_rate", "metal_hash_rate")}
            row.update({
                "cpu_total_ms": pair["cpu_total_ns"]["median"] / 1e6,
                "cpu_total_mad_ms": pair["cpu_total_ns"]["mad"] / 1e6,
                "metal_total_ms": pair["metal_total_ns"]["median"] / 1e6,
                "metal_total_mad_ms": pair["metal_total_ns"]["mad"] / 1e6,
                "cpu_over_metal_ratio": pair["cpu_over_metal_median_ratio"],
                "observed_ratio_low": pair[
                    "cpu_over_metal_observed_ratio_bounds"]["low"],
                "observed_ratio_high": pair[
                    "cpu_over_metal_observed_ratio_bounds"]["high"],
                "cpu_minus_metal_ms": (
                    pair["median_total_delta_ns_cpu_minus_metal"] / 1e6),
                "hash_parent_minus_direct_metal_ms": (
                    pair["hash_parent_minus_direct_metal_ns"] / 1e6),
                "cross_parent_minus_dispatch_ms": (
                    pair["cross_parent_minus_dispatch_ns"] / 1e6),
            })
            for stage in KEY_STAGES:
                row[f"{stage}_ms"] = (
                    pair["metal_stages"][stage]["median_ns"] / 1e6)
                row[f"{stage}_share"] = pair[
                    "metal_stages"][stage]["median_share_total"]
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    parser.add_argument("--baseline", type=pathlib.Path, required=True)
    parser.add_argument("--output-json", type=pathlib.Path, required=True)
    parser.add_argument("--output-csv", type=pathlib.Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    if manifest.get("schema") != DATASET_SCHEMA:
        raise SystemExit(f"unexpected manifest schema: {manifest.get('schema')}")
    cases = {case["case_id"]: case for case in manifest["cases"]}
    records = read_jsonl(args.records)
    validation = validate(records, cases)
    if not validation["valid"]:
        raise SystemExit("raw record validation failed:\n" +
                         "\n".join(validation["errors"]))

    groups = group_records(records)
    summaries = [summarize_group(key, groups[key]) for key in sorted(groups)]
    baseline = json.loads(args.baseline.read_text())
    expected_groups = sorted(baseline["groups"], key=lambda item: (
        item["case_id"], item["method"], item["backend"], item["sample_role"]))
    mismatches = compare_json(summaries, expected_groups, "$.groups")
    validation["baseline_group_count"] = len(expected_groups)
    validation["baseline_reaggregation_match"] = not mismatches
    validation["baseline_reaggregation_mismatches"] = mismatches[:20]
    validation["baseline_reaggregation_mismatch_count"] = len(mismatches)
    if mismatches:
        raise SystemExit("baseline reaggregation mismatch:\n" +
                         "\n".join(mismatches[:20]))

    pairs = pair_summaries(summaries, cases)
    result = {
        "schema": ANALYSIS_SCHEMA,
        "inputs": {
            "records": str(args.records),
            "records_sha256": sha256(args.records),
            "manifest": str(args.manifest),
            "manifest_sha256": sha256(args.manifest),
            "baseline": str(args.baseline),
            "baseline_sha256": sha256(args.baseline),
        },
        "aggregation": (
            "Independent per-group median and median absolute deviation; "
            "warmups excluded; n=3 per reported group"),
        "uncertainty_note": (
            "Observed ratio bounds use CPU min/Metal max and CPU max/Metal "
            "min. They are descriptive three-sample bounds, not confidence "
            "intervals or paired estimates."),
        "accounting_note": (
            "Lossless transform and hash stages contain nested work. Stage "
            "shares are inclusive and must not be summed. Parent-minus-direct-"
            "Metal values are residual accounting buckets, not pure CPU time."),
        "validation": validation,
        "groups": summaries,
        "cpu_metal_pairs": pairs,
        "cold_warm": cold_warm_summaries(summaries, cases),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(args.output_csv, pairs)
    print(json.dumps({
        "records": len(records),
        "groups": len(summaries),
        "pairs": len(pairs),
        "baseline_reaggregation_match": True,
        "output_json": str(args.output_json),
        "output_csv": str(args.output_csv),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
