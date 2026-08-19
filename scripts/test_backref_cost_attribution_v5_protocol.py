#!/usr/bin/env python3
"""Untimed, workload-free contract tests for attribution v5."""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

import execute_backref_cost_attribution_v5 as executor
import run_backref_cost_attribution_v5_experiment as operator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_attribution_v5_manifest.json"


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
    v5_boundary = current.split(
        "// V5 preserves V4's frozen control flow and timer ownership exactly.",
        1)[1]
    v5_boundary = v5_boundary.split("#else", 1)[0]
    assert v5_boundary.count(
        "VP8LBackrefCostAttributionV5ExperimentEnabled()") == 1
    assert v5_boundary.count(
        "BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert v5_boundary.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert "VP8LBackrefCostAttributionV5RecordSelector();" in v5_boundary
    assert "if (use_candidate)" in v5_boundary and "} else {" in v5_boundary
    assert "BACKREF_DP_RECORD_CALL();" in (
        ROOT / "src/enc/backward_references_cost_distance_only_enc.inc"
    ).read_text()
    preprocessed = subprocess.check_output(
        [os.environ.get("CC", "cc"), "-E", "-P", f"-I{ROOT}",
         "-DWEBP_USE_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT=1",
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
            "schema": "libwebp-backref-cost-attribution-v5-lease-v1",
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
    assert record["transfer_timeout_seconds"] == 1020


def two_plane_state_contract() -> None:
    cleanup = {"status": "complete", "absence_proved": True}
    archive_states = (
        {"status": "accepted", "builder_exit_code": 0},
        {"status": "rejected-before-extraction", "builder_exit_code": 0,
         "reason": "missing artifact"},
        {"status": "rejected-before-extraction", "builder_exit_code": 0,
         "reason": "truncated archive"},
        {"status": "rejected-before-extraction", "builder_exit_code": 0,
         "reason": "corrupt archive"},
        {"status": "rejected-before-extraction", "builder_exit_code": 0,
         "reason": "bulk transport timeout"},
    )
    for operator_status in (
            {"status": "complete",
             "benchmark_lease_acquisition_attempted": False},
            {"status": "refused",
             "benchmark_lease_acquisition_attempted": False}):
        lease, _ = executor.lease_transfer_contract(
            "rehearse", False, False,
            lambda: (_ for _ in ()).throw(
                AssertionError("not-attempted lease fetch")))
        for archive in archive_states:
            executor.validate_control_plane(
                operator_status, lease, cleanup, archive)
    verified, _ = executor.lease_transfer_contract(
        "run", True, True,
        lambda: ({"hashes_match": True}, {"released": True}))
    executor.validate_control_plane(
        {"status": "complete",
         "benchmark_lease_acquisition_attempted": True},
        verified, cleanup, archive_states[0])
    unavailable, _ = executor.lease_transfer_contract(
        "run", True, False, lambda: None)
    rejected(executor.validate_control_plane,
             {"status": "refused",
              "benchmark_lease_acquisition_attempted": True},
             unavailable, cleanup, archive_states[0])
    rejected(executor.validate_control_plane,
             {"status": "complete",
              "benchmark_lease_acquisition_attempted": False},
             lease, {"status": "complete", "absence_proved": False},
             archive_states[0])


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
        "a192d9b8562b497b03bf8cc83c2de5c7a6ea8cae"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT"
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
    assert manifest["resources"]["transfer_timeout_seconds"] == 1020
    assert manifest["resources"]["archive_build_timeout_seconds"] == 180
    assert manifest["diagnostic"]["primary"] == "coarse monotonic stage timers"
    assert manifest["diagnostic"]["fallback"] is None
    assert manifest["diagnostic"]["external_profiler_invocations"] == 0
    expected_command = (
        'env WEBP_BENCHMARK_SESSION=exclusive '
        'WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V5_COMMIT="$(git rev-parse HEAD)" '
        'python3 scripts/execute_backref_cost_attribution_v5.py run '
        '"$PWD/evidence/backref-cost-attribution-v5-execution-20260819"')
    assert manifest["frozen_phase_2_command"] == expected_command
    for row in manifest["frozen_artifacts"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    semantic_identity()
    mode_truth_table()
    lease_transfer_truth_table()
    two_plane_state_contract()
    plan_contract(manifest)
    source = (ROOT / "scripts/run_backref_cost_attribution_v5_experiment.py").read_text()
    rehearsal = source.split("if mode == \"rehearse\":", 1)[1].split(
        "else:", 1)[0]
    assert "execute_profiles" not in rehearsal
    assert "correctness_gate" not in rehearsal
    assert "timer_accounting_gate" not in rehearsal
    assert "profiler_invocations\": 0" in rehearsal
    executor_source = (
        ROOT / "scripts/execute_backref_cost_attribution_v5.py").read_text()
    assert "finally:" in executor_source
    assert "cleanup = admission.finish_admission(record)" in executor_source
    assert '"remote_cleanup_absence_proved"' in executor_source
    assert 'timeout=TRANSFER_TIMEOUT_SECONDS' in executor_source
    print("PASS: attribution v5 exact specialization identity, one selected DP "
          "body without predecessor fallthrough, disjoint modes, 24-command "
          "coarse-timer plan, bounded three-state lease return, no-workload "
          "rehearsal, and diagnostic-only policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
