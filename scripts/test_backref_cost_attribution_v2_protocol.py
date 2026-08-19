#!/usr/bin/env python3
"""Untimed, workload-free contract tests for attribution v2."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

import execute_backref_cost_attribution_v2 as executor
import run_backref_cost_attribution_v2_experiment as operator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_attribution_v2_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        "#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT)", 1)[1]
    assert "VP8LBackrefCostAttributionV2ExperimentEnabled" in attribution_branch
    assert "VP8LBackrefCostAttributionExperimentEnabled()" in current


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
        for directory in ("stages", "runner"):
            (output / directory).mkdir(parents=True, exist_ok=True)
        cases = {}
        for row in manifest["corpus"]:
            (corpus / row["file"]).touch()
            cases[row["case_id"]] = row
        plan = operator.frozen_profile_plan(
            manifest, Path("/frozen/runner"), corpus, cases, output)
        assert len(plan) == 24
        assert [row["ordinal"] for row in plan] == list(range(24))
        assert all(row["command"][0] == "/usr/bin/env" for row in plan)
        assert all(row["command"][-2:] == ["1", "4"] for row in plan)
        assert not any(token in ("xctrace", "sample")
                       for row in plan for token in row["command"])


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["phase_1_decision"]["timed_execution_authorized"] is True
    assert manifest["phase_1_decision"]["status"] == "AUTHORIZE_DIAGNOSTIC"
    assert manifest["base_commit"] == \
        "d63c9ed99e2d72e3f0aca1d375d31fad19e13455"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT"
    assert set(manifest["candidate"]) & {"build_flag", "compile_macro",
                                         "runtime_flag"} == {
        "build_flag", "compile_macro", "runtime_flag"}
    assert "marker_macro" not in manifest["candidate"]
    assert manifest["protocol"]["profile_processes"] == 24
    assert manifest["protocol"]["retained_stage_records"] == 96
    assert manifest["acceptance"]["production_promotion_forbidden"]
    assert manifest["diagnostic"]["primary"] == "coarse monotonic stage timers"
    assert manifest["diagnostic"]["fallback"] is None
    assert manifest["diagnostic"]["external_profiler_invocations"] == 0
    expected_command = (
        'env WEBP_BENCHMARK_SESSION=exclusive '
        'WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V2_COMMIT="$(git rev-parse HEAD)" '
        'python3 scripts/execute_backref_cost_attribution_v2.py run '
        '"$PWD/evidence/backref-cost-attribution-v2-execution-20260819"')
    assert manifest["frozen_phase_2_command"] == expected_command
    for row in manifest["frozen_artifacts"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    semantic_identity()
    mode_truth_table()
    plan_contract(manifest)
    source = (ROOT / "scripts/run_backref_cost_attribution_v2_experiment.py").read_text()
    rehearsal = source.split("if mode == \"rehearse\":", 1)[1].split(
        "else:", 1)[0]
    assert "execute_profiles" not in rehearsal
    assert "correctness_gate" not in rehearsal
    assert "profiler_invocations\": 0" in rehearsal
    print("PASS: attribution v2 exact specialization identity, disjoint modes, "
          "24-command coarse-timer plan, no-workload rehearsal, and diagnostic-only policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
