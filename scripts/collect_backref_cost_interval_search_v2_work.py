#!/usr/bin/env python3
"""Collect untimed publication-corpus interval-search work evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT"
SCHEMA = "libwebp-backref-cost-interval-search-v2-work-v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(
        (ROOT / "benchmarks/publication-corpus/manifest.json").read_text())
    rows = []
    for case in manifest["cases"]:
        source = args.corpus / case["file"]
        if sha256(source) != case["sha256"]:
            raise RuntimeError(f"corpus hash mismatch: {case['case_id']}")
        for method in (4, 6):
            pair = {}
            for variant in ("baseline", "candidate"):
                env = os.environ.copy()
                env.pop(RUNTIME, None)
                if variant == "candidate":
                    env[RUNTIME] = "1"
                result = subprocess.run(
                    [str(args.runner), "diagnostic", str(source),
                     case["case_id"], str(method), variant],
                    cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, check=False)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr or result.stdout)
                row = json.loads(result.stdout)
                if row.get("schema") != SCHEMA:
                    raise RuntimeError("work schema mismatch")
                rows.append(row)
                pair[variant] = row
            baseline, candidate = pair["baseline"], pair["candidate"]
            immutable = (
                "bitstream_bytes", "bitstream_fnv1a64", "push_calls",
                "short_push_calls", "cache_segments", "overlap_scans",
                "disjoint_prefix_scans", "insert_calls",
                "null_hint_insert_calls", "position_backward_steps",
                "interval_updates", "interval_pops", "max_live_intervals",
            )
            if any(baseline[name] != candidate[name] for name in immutable):
                raise RuntimeError("candidate changed non-search work")
            if baseline["position_forward_steps"]:
                before = (baseline["position_forward_steps"] +
                          baseline["position_backward_steps"])
                after = (candidate["position_forward_steps"] +
                         candidate["position_backward_steps"])
                if (after * 10 > before or
                        candidate["append_hint_fast_paths"] <= 0 or
                        candidate["runtime_activations"] <= 0):
                    raise RuntimeError("work-reduction criterion failed")
    args.output.mkdir(parents=True, exist_ok=False)
    records = args.output / "work-metrics.jsonl"
    records.write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                               for row in rows))
    baseline = [row for row in rows if row["variant"] == "baseline"]
    candidate = [row for row in rows if row["variant"] == "candidate"]
    summary = {
        "schema": "libwebp-backref-cost-interval-search-v2-design-work-summary-v1",
        "status": "PASS",
        "rows": len(rows),
        "case_method_pairs": len(rows) // 2,
        "active_case_method_pairs": sum(
            row["position_forward_steps"] > 0 for row in baseline),
        "inactive_case_method_pairs": sum(
            row["position_forward_steps"] == 0 for row in baseline),
        "baseline_position_forward_steps": sum(
            row["position_forward_steps"] for row in baseline),
        "candidate_position_forward_steps": sum(
            row["position_forward_steps"] for row in candidate),
        "baseline_position_backward_steps": sum(
            row["position_backward_steps"] for row in baseline),
        "candidate_position_backward_steps": sum(
            row["position_backward_steps"] for row in candidate),
        "candidate_append_hint_fast_paths": sum(
            row["append_hint_fast_paths"] for row in candidate),
        "candidate_append_hint_branch_checks": sum(
            row["append_hint_branch_checks"] for row in candidate),
        "candidate_append_hint_loads": sum(
            row["append_hint_loads"] for row in candidate),
        "candidate_append_hint_start_loads": sum(
            row["append_hint_start_loads"] for row in candidate),
        "candidate_append_hint_update_checks": sum(
            row["append_hint_update_checks"] for row in candidate),
        "candidate_append_hint_updates": sum(
            row["append_hint_updates"] for row in candidate),
        "candidate_pop_tail_branch_checks": sum(
            row["pop_tail_branch_checks"] for row in candidate),
        "candidate_pop_tail_updates": sum(
            row["pop_tail_updates"] for row in candidate),
        "candidate_runtime_activations": sum(
            row["runtime_activations"] for row in candidate),
        "records_sha256": sha256(records),
        "timing_fields_recorded": False,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
