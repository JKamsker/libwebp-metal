#!/usr/bin/env python3
"""Untimed, workload-free contract tests for attribution v4."""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

import execute_backref_cost_attribution_v4 as executor
import run_backref_cost_attribution_v4_experiment as operator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_attribution_v4_manifest.json"


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
    normalize = lambda value: re.sub(r"\s+", "", value)
    assert normalize(extract_body(frozen, "PushIntervalSpecialized")) == \
        normalize(extract_body(current, "PushIntervalSpecialized"))
    v4_boundary = current.split(
        "// V4 preserves V3's frozen control flow outside every predecessor chain.",
        1)[1]
    v4_boundary = v4_boundary.split("#else", 1)[0]
    assert v4_boundary.count(
        "VP8LBackrefCostAttributionV4ExperimentEnabled()") == 1
    assert v4_boundary.count(
        "BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert v4_boundary.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert "VP8LBackrefCostAttributionV4RecordSelector();" in v4_boundary
    assert "if (use_candidate)" in v4_boundary and "} else {" in v4_boundary
    assert "BACKREF_DP_RECORD_CALL();" in (
        ROOT / "src/enc/backward_references_cost_distance_only_enc.inc"
    ).read_text()
    preprocessed = subprocess.check_output(
        [os.environ.get("CC", "cc"), "-E", "-P", f"-I{ROOT}",
         "-DWEBP_USE_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT=1",
         "src/enc/backward_references_cost_enc.c"], cwd=ROOT, text=True)
    traceback = extract_body(
        preprocessed, "VP8LBackwardReferencesTraceBackwards")
    assert traceback.count(
        "BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert traceback.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert traceback.count("WebPProfileStageBegin("
                           "WEBP_PROFILE_BACKREF_COST_DP_TOTAL)") == 1


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


def lease_transfer_truth_table() -> None:
    requests = []

    def forbidden_fetch():
        requests.append("unexpected")
        raise AssertionError("not-attempted transfer requested a receipt")

    record, value = executor.lease_transfer_contract(
        "rehearse", False, False, forbidden_fetch)
    assert record["state"] == "not-attempted"
    assert not record["receipt_required"] and not record["receipt_requested"]
    assert value is None and requests == []

    def completed_fetch():
        requests.append("verified")
        return ({"hashes_match": True}, {
            "schema": "libwebp-backref-cost-attribution-v4-lease-v1",
            "acquisition_attempted": True, "acquired": True,
            "released": True})

    record, value = executor.lease_transfer_contract(
        "run", True, True, completed_fetch)
    assert record["state"] == "verified" and record["receipt_requested"]
    assert value is not None and value["released"]

    record, value = executor.lease_transfer_contract(
        "run", True, False, forbidden_fetch)
    assert record["state"] == "unavailable-after-attempt"
    assert record["receipt_required"] and not record["receipt_requested"]
    assert value is None and requests == ["verified"]

    def completed_refusal():
        requests.append("refused")
        raise RuntimeError("natural missing-artifact refusal")

    record, value = executor.lease_transfer_contract(
        "run", True, True, completed_refusal)
    assert record["state"] == "unavailable-after-attempt"
    assert record["receipt_required"] and record["receipt_requested"]
    assert value is None and requests == ["verified", "refused"]
    assert record["transfer_timeout_seconds"] == 30


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
    decision = manifest["phase_1_decision"]
    assert decision["status"] in (
        "PENDING_REMOTE_REHEARSAL", "AUTHORIZE_DIAGNOSTIC")
    assert decision["timed_execution_authorized"] is \
        (decision["status"] == "AUTHORIZE_DIAGNOSTIC")
    assert manifest["base_commit"] == \
        "d8e015e8395a1ae3d5d17637cacf8b99bd084901"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT"
    assert set(manifest["candidate"]) & {"build_flag", "compile_macro",
                                         "runtime_flag"} == {
        "build_flag", "compile_macro", "runtime_flag"}
    assert "marker_macro" not in manifest["candidate"]
    assert manifest["protocol"]["profile_processes"] == 24
    assert manifest["protocol"]["retained_stage_records"] == 96
    assert manifest["acceptance"]["production_promotion_forbidden"]
    assert manifest["acceptance"]["maximum_mean_clock_read_delta_ns"] == 10000
    assert manifest["return_contract"]["lease_transfer_states"] == [
        "not-attempted", "unavailable-after-attempt", "verified"]
    assert manifest["resources"]["transfer_timeout_seconds"] == 30
    assert manifest["resources"]["archive_build_timeout_seconds"] == 180
    assert manifest["diagnostic"]["primary"] == "coarse monotonic stage timers"
    assert manifest["diagnostic"]["fallback"] is None
    assert manifest["diagnostic"]["external_profiler_invocations"] == 0
    expected_command = (
        'env WEBP_BENCHMARK_SESSION=exclusive '
        'WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V4_COMMIT="$(git rev-parse HEAD)" '
        'python3 scripts/execute_backref_cost_attribution_v4.py run '
        '"$PWD/evidence/backref-cost-attribution-v4-execution-20260819"')
    assert manifest["frozen_phase_2_command"] == expected_command
    for row in manifest["frozen_artifacts"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    semantic_identity()
    mode_truth_table()
    lease_transfer_truth_table()
    plan_contract(manifest)
    source = (ROOT / "scripts/run_backref_cost_attribution_v4_experiment.py").read_text()
    rehearsal = source.split("if mode == \"rehearse\":", 1)[1].split(
        "else:", 1)[0]
    assert "execute_profiles" not in rehearsal
    assert "correctness_gate" not in rehearsal
    assert "profiler_invocations\": 0" in rehearsal
    executor_source = (
        ROOT / "scripts/execute_backref_cost_attribution_v4.py").read_text()
    assert "finally:" in executor_source
    assert "cleanup = admission.finish_admission(record)" in executor_source
    assert '"remote_cleanup_absence_proved"' in executor_source
    assert 'timeout=TRANSFER_TIMEOUT_SECONDS' in executor_source
    print("PASS: attribution v4 exact specialization identity, one selected DP "
          "body without predecessor fallthrough, disjoint modes, 24-command "
          "coarse-timer plan, bounded three-state lease return, no-workload "
          "rehearsal, and diagnostic-only policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
