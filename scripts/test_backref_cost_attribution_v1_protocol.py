#!/usr/bin/env python3
"""Untimed, workload-free contract tests for attribution v1."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import execute_backref_cost_attribution_v1 as executor
import run_backref_cost_attribution_v1_experiment as operator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_attribution_v1_manifest.json"


def rejected(function, *args) -> None:
    try:
        function(*args)
    except (OSError, RuntimeError, ValueError):
        return
    raise AssertionError(f"unsafe contract accepted: {function.__name__}{args}")


def extract_body(text: str, name: str) -> str:
    marker = name + "("
    start = text.index(marker)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[brace:index + 1]
    raise AssertionError(f"unterminated function: {name}")


def semantic_identity() -> None:
    frozen = subprocess.check_output(
        ["git", "show", "673bc3fa:src/enc/backward_references_cost_enc.c"],
        cwd=ROOT, text=True)
    current = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    assert extract_body(frozen, "PushIntervalSpecialized") == \
        extract_body(current, "PushIntervalSpecialized")
    assert "? BackwardReferencesHashChainDistanceOnlySpecialized(" in current
    attribution_branch = current.split(
        "#if defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT)", 1)[1]
    assert "VP8LBackrefCostAttributionV1ExperimentEnabled()" in attribution_branch
    assert "ExperimentInjectFallback" not in attribution_branch.split("#elif", 1)[0]


def mode_truth_table() -> None:
    values = (None, "", "exclusive", "shared", "1")
    for mode in ("validate", "rehearse", "run"):
        for value in values:
            environment = {} if value is None else {
                "WEBP_BENCHMARK_SESSION": value}
            accepted = ((mode in ("validate", "rehearse") and value is None) or
                        (mode == "run" and value == "exclusive"))
            if accepted:
                executor.validate_mode_environment(mode, environment)
            else:
                rejected(executor.validate_mode_environment, mode, environment)


def plan_contract(manifest: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="attribution-plan-") as raw:
        temporary = Path(raw)
        corpus = temporary / "corpus"
        output = temporary / "output"
        corpus.mkdir()
        for directory in ("profiles", "stages", "runner", "exports"):
            (output / directory).mkdir(parents=True, exist_ok=True)
        cases = {}
        for row in manifest["corpus"]:
            (corpus / row["file"]).touch()
            cases[row["case_id"]] = row
        plan = operator.frozen_profile_plan(
            manifest, Path("/frozen/runner"), corpus, cases, output)
        assert len(plan) == 24
        assert [row["ordinal"] for row in plan] == list(range(24))
        assert all(row["command"][:7] == [
            "/usr/bin/xcrun", "xctrace", "record", "--no-prompt",
            "--template", "Time Profiler", "--output"] for row in plan)
        assert all(row["command"].count("--launch") == 1 for row in plan)
        assert all(row["command"][-2:] == ["1", "4"] for row in plan)
        assert not any("sample" in token for row in plan for token in row["command"])


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["base_commit"] == \
        "db1d9e8e66055ff943f57664733316df83b0a965"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT"
    assert manifest["protocol"]["profile_processes"] == 24
    assert manifest["protocol"]["retained_stage_records"] == 96
    assert manifest["acceptance"]["production_promotion_forbidden"]
    assert manifest["profiler"]["fallback"] is None
    semantic_identity()
    mode_truth_table()
    plan_contract(manifest)
    source = (ROOT / "scripts/run_backref_cost_attribution_v1_experiment.py").read_text()
    rehearsal = source.split("if mode == \"rehearse\":", 1)[1].split(
        "else:", 1)[0]
    assert "execute_profiles" not in rehearsal
    assert "correctness_gate" not in rehearsal
    assert "profiler_invocations\": 0" in rehearsal
    print("PASS: attribution v1 exact specialization identity, disjoint modes, "
          "24-command serial plan, no-workload rehearsal, and diagnostic-only policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
