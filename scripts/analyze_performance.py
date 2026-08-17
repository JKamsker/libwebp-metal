#!/usr/bin/env python3
"""Compare benchmark samples with robust medians and bootstrap intervals."""

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


BOOTSTRAPS = 10000


def load_samples(path):
    grouped = defaultdict(list)
    with path.open(encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            if record.get("measured", True):
                key = (record["case"], record["variant"])
                grouped[key].append(float(record["seconds"]))
    return grouped


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def ratio_interval(current, baseline, seed):
    randomizer = random.Random(seed)
    ratios = []
    for _ in range(BOOTSTRAPS):
        current_median = statistics.median(
            randomizer.choices(current, k=len(current)))
        baseline_median = statistics.median(
            randomizer.choices(baseline, k=len(baseline)))
        ratios.append(current_median / baseline_median)
    ratio = statistics.median(current) / statistics.median(baseline)
    return ratio, percentile(ratios, 0.025), percentile(ratios, 0.975)


def speedup_ratio_interval(current, baseline, seed):
    randomizer = random.Random(seed)
    ratios = []
    for _ in range(BOOTSTRAPS):
        current_cpu = randomizer.choices(
            current["baseline"], k=len(current["baseline"]))
        current_gpu = randomizer.choices(
            current["accelerated"], k=len(current["accelerated"]))
        baseline_cpu = randomizer.choices(
            baseline["baseline"], k=len(baseline["baseline"]))
        baseline_gpu = randomizer.choices(
            baseline["accelerated"], k=len(baseline["accelerated"]))
        current_speedup = (
            statistics.median(current_cpu) / statistics.median(current_gpu))
        baseline_speedup = (
            statistics.median(baseline_cpu) / statistics.median(baseline_gpu))
        ratios.append(current_speedup / baseline_speedup)
    current_speedup = (
        statistics.median(current["baseline"]) /
        statistics.median(current["accelerated"]))
    baseline_speedup = (
        statistics.median(baseline["baseline"]) /
        statistics.median(baseline["accelerated"]))
    ratio = current_speedup / baseline_speedup
    return ratio, percentile(ratios, 0.025), percentile(ratios, 0.975)


def compatibility(current_dir, baseline_dir):
    current_env = json.loads((current_dir / "environment.json").read_text())
    baseline_env = json.loads((baseline_dir / "environment.json").read_text())
    fields = [
        ("runner name", current_env["runner"].get("RUNNER_NAME"),
         baseline_env["runner"].get("RUNNER_NAME")),
        ("runner arch", current_env["runner"].get("RUNNER_ARCH"),
         baseline_env["runner"].get("RUNNER_ARCH")),
        ("hardware model", current_env["sysctl"].get("hw.model"),
         baseline_env["sysctl"].get("hw.model")),
        ("corpus", current_env.get("corpus_manifest_sha256"),
         baseline_env.get("corpus_manifest_sha256")),
        ("protocol", current_env.get("protocol_sha256"),
         baseline_env.get("protocol_sha256")),
        ("schema", current_env.get("schema_version"),
         baseline_env.get("schema_version")),
    ]
    return [name for name, current, baseline in fields if current != baseline]


def write_outputs(status, markdown, result, args):
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown, encoding="utf-8")
    args.json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"status={status}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument(
        "--fail-level", choices=("never", "critical"), default="never")
    args = parser.parse_args()

    baseline_samples = args.baseline / "samples.jsonl"
    if not baseline_samples.is_file():
        status = "baseline_missing"
        markdown = (
            "# Performance comparison\n\nNo accepted baseline exists for this "
            "runner; this run initializes it.\n")
        write_outputs(status, markdown, {"status": status, "cases": []}, args)
        return
    mismatches = compatibility(args.current, args.baseline)
    if mismatches:
        status = "incompatible"
        markdown = (
            "# Performance comparison\n\nBaseline is incompatible (" +
            ", ".join(mismatches) + "); this run starts a new series.\n")
        result = {"status": status, "mismatches": mismatches, "cases": []}
        write_outputs(status, markdown, result, args)
        return

    current = load_samples(args.current / "samples.jsonl")
    baseline = load_samples(baseline_samples)
    case_names = sorted({case for case, _ in current})
    rows, results = [], []
    overall = "pass"
    for index, case in enumerate(case_names):
        needed = [(case, "baseline"), (case, "accelerated")]
        if any(key not in current or key not in baseline for key in needed):
            overall = "incompatible"
            continue
        accelerated_ratio, accelerated_low, accelerated_high = ratio_interval(
            current[(case, "accelerated")],
            baseline[(case, "accelerated")],
            1000 + index,
        )
        current_speedup = (
            statistics.median(current[(case, "baseline")]) /
            statistics.median(current[(case, "accelerated")]))
        baseline_speedup = (
            statistics.median(baseline[(case, "baseline")]) /
            statistics.median(baseline[(case, "accelerated")]))
        # Treat variant samples as independent; alternating order already
        # balances monotonic drift between the two variants.
        speedup_ratio, speedup_low, speedup_high = speedup_ratio_interval(
            {
                variant: current[(case, variant)]
                for variant in ("baseline", "accelerated")
            },
            {
                variant: baseline[(case, variant)]
                for variant in ("baseline", "accelerated")
            },
            19000 + index,
        )

        level = "pass"
        critical_time = accelerated_ratio >= 1.10 and accelerated_low > 1.05
        critical_speedup = speedup_ratio <= 0.88 and speedup_high < 0.95
        warning_time = accelerated_ratio >= 1.05 and accelerated_low > 1.02
        warning_speedup = speedup_ratio <= 0.93 and speedup_high < 0.97
        if critical_time or critical_speedup:
            level = "critical"
            overall = "critical"
        elif warning_time or warning_speedup:
            level = "warning"
            if overall == "pass":
                overall = "warning"
        result = {
            "case": case,
            "level": level,
            "accelerated_time_ratio": accelerated_ratio,
            "accelerated_time_ratio_ci95": [accelerated_low, accelerated_high],
            "current_speedup": current_speedup,
            "baseline_speedup": baseline_speedup,
            "speedup_ratio": speedup_ratio,
            "speedup_ratio_ci95": [speedup_low, speedup_high],
        }
        results.append(result)
        rows.append(
            f"| {case} | {accelerated_ratio:.3f} "
            f"({accelerated_low:.3f}–{accelerated_high:.3f}) | "
            f"{current_speedup:.3f}x | {baseline_speedup:.3f}x | {level} |")

    markdown = "\n".join([
        "# Performance comparison", "", f"Overall signal: **{overall}**", "",
        "Ratios above 1.0 are slower than the accepted baseline.", "",
        "| Case | Accelerated time ratio (95% CI) | Current speedup | "
        "Baseline speedup | Signal |",
        "|---|---:|---:|---:|---|", *rows, "",
    ])
    write_outputs(overall, markdown, {
        "status": overall,
        "cases": results
    }, args)
    if overall == "critical" and args.fail_level == "critical":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
