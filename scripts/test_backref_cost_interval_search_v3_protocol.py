#!/usr/bin/env python3
"""Untimed contract validation for the frozen interval-search-v3 handoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import backref_cost_interval_search_v3_archive as archive_protocol
import backref_cost_interval_search_v3_admission as admission
import execute_backref_cost_interval_search_v3 as executor


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_interval_search_v3_manifest.json"
SCHEMAS_PATH = ROOT / "scripts/backref_cost_interval_search_v3_schemas.json"
DESIGN = ROOT / "evidence/backref-cost-interval-search-v3-design"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_return(output: Path, *, refused: bool) -> None:
    transfer = json.loads((output / "transfer-cleanup.json").read_text())
    assert transfer["status"] == "complete"
    assert transfer["mode"] == "rehearse"
    assert transfer["rehearsal_refusal_fixture"] == \
        ("missing" if refused else None)
    assert not transfer["benchmark_lease_acquisition_attempted"]
    assert not transfer["timed_binary_invoked"]
    assert transfer["remote_cleanup_complete"]
    assert transfer["remote_cleanup_proof"]["absence_proved"]
    assert transfer["pipeline_exit_code"] == 0
    source_hash = transfer["source_bundle_sha256"]
    source_receipt = transfer["admission"]
    executor.validate_admission_receipt(source_receipt, source_hash)
    assert source_receipt["source_bundle_sha256"] == \
        source_receipt["admission"]["bundle_sha256"]
    lease = json.loads((output / "return-protocol/lease-record.json").read_text())
    assert not lease["acquisition_attempted"]
    assert not lease["acquired"] and not lease["released"]
    assert not (output / "records.jsonl").exists()
    assert not (output / "commands.jsonl").exists()
    archive_protocol.verify_returned_index(
        output / "returned-evidence-hashes.json", output)
    status = json.loads((output / "operator-status.json").read_text())
    assert status["status"] == ("refused" if refused else "complete")
    if refused:
        refusal = json.loads((output / "refusal.json").read_text())
        assert refusal["status"] == "refused"
        assert refusal["stage"] == "toolchain-admission"
        assert not refusal["timing_samples_present"]
    else:
        rehearsal = json.loads((output / "rehearsal.json").read_text())
        assert rehearsal["status"] == "PASS"
        assert rehearsal["correctness_cells"] == 26
        assert rehearsal["work_metric_rows"] == 16
        assert not rehearsal["benchmark_session_present"]
        assert not rehearsal["benchmark_lease_attempted"]
        assert not rehearsal["timed_runner_invoked"]
        assert rehearsal["timed_samples"] == 0
        correctness = json.loads((output / "correctness.json").read_text())
        assert len(correctness) == 26
        summary = json.loads((output / "work-metric-summary.json").read_text())
        assert summary["status"] == "PASS"


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    catalog = json.loads(SCHEMAS_PATH.read_text())
    assert manifest["schema"] == \
        "libwebp-backref-cost-interval-search-v3-frozen-protocol-v1"
    assert manifest["protocol_version"] == catalog["protocol_version"] == 1
    assert manifest["base_commit"] == \
        "c472599ce8d3aee1e4f5bcf70b56b9c354351660"
    decision = manifest["phase_1_decision"]
    assert decision["status"] == "AUTHORIZE_TIMING"
    assert decision["timed_execution_authorized"] is True
    assert manifest["independence"]["performance_inputs"] == []
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
    assert manifest["candidate"]["compile_macro"] == \
        "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
    assert manifest["candidate"]["runtime_value"] == "1"
    assert set(manifest["execution_modes"]) == {"validate", "rehearse", "run"}
    frozen_run = (
        "env WEBP_BENCHMARK_SESSION=exclusive "
        "WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V3_COMMIT=\"$(git rev-parse HEAD)\" "
        "python3 scripts/execute_backref_cost_interval_search_v3.py run "
        "/Users/jonaskamsker/.codex/worktrees/f379/libwebp-metal/evidence/"
        "backref-cost-interval-search-v3-execution-20260819")
    assert manifest["frozen_phase_2_command"] == frozen_run
    assert manifest["remote_host"]["ssh_alias"] == "pandocs-agent"
    assert manifest["remote_host"]["safe_root_basename"] == \
        ".libwebp-metal-backref-cost-interval-search-v3"
    assert manifest["builds"]["forbidden_backend"] == "CUDA"
    assert manifest["toolchain"]["environment"]["PATH"] == \
        "/usr/bin:/bin:/usr/sbin:/sbin"
    assert manifest["protocol"]["methods"] == [4, 6]
    assert manifest["resources"]["parallel_timed_processes"] == 1
    limits = manifest["protocol"]["acceptance"]
    assert limits["paired_median_ratio_maximum"] == 0.995
    assert limits["p95_ratio_maximum"] == 1.005
    inventory = manifest["protocol"]["expected_inventory"]
    assert inventory == {
        "command_processes": 272,
        "cold_measured_samples": 176,
        "warmup_samples": 192,
        "warm_measured_samples": 864,
        "total_measured_samples": 1040,
        "variant_measured_samples": 520,
        "correctness_cells": 26,
        "work_metric_rows": 16,
        "evaluation_cells": 16,
        "required_holdout_cells": 8,
    }
    schema_ids = set(catalog["schemas"])
    for key, schema_id in manifest["schemas"].items():
        if key != "catalog":
            assert schema_id in schema_ids
    assert manifest["schemas"]["source_admission_receipt"] == \
        admission.SOURCE_RECEIPT_SCHEMA
    for artifact in manifest["frozen_artifacts"]:
        assert sha256(ROOT / artifact["path"]) == artifact["sha256"], artifact

    source = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    driver = (ROOT / "scripts/execute_backref_cost_interval_search_v3.py").read_text()
    runner = (ROOT / "tools/backref_cost_interval_search_v3_experiment_runner.c").read_text()
    assert "CostInterval* append_hint = NULL" in source
    assert "start > append_hint->start" in source
    assert "CostInterval* append_hint;" not in source
    assert 'record["bundle_sha256"]' not in driver
    assert "validate_run_environment(os.environ)" in driver
    assert "validate_untimed_environment(mode, os.environ)" in driver
    assert "recorder build refuses timed samples" in runner
    assert "mach_continuous_time" in runner

    local = json.loads((DESIGN / "local-validation.json").read_text())
    assert local["status"] == "PASS"
    assert local["normalized_v2_v3_identity"]
    assert local["cost_manager_size_bytes"] == 33224
    identity = json.loads((ROOT /
        "evidence/backref-cost-interval-search-v3-design-work/identity.json").read_text())
    assert identity["normalized_v2_v3_candidate_identical"]
    assert identity["cost_manager_v2_bytes"] == identity["cost_manager_v3_bytes"]
    summary = json.loads((ROOT /
        "evidence/backref-cost-interval-search-v3-design-work/summary.json").read_text())
    assert summary["status"] == "PASS"
    assert summary["candidate_position_forward_steps"] == 0
    assert summary["candidate_position_backward_steps"] == \
        summary["baseline_position_backward_steps"]
    assert summary["candidate_append_hint_fast_paths"] > 0
    assert not summary["timing_fields_recorded"]

    validate_return(DESIGN / "remote-rehearsal-success", refused=False)
    validate_return(DESIGN / "remote-rehearsal-refusal", refused=True)
    freeze = json.loads((DESIGN / "phase-1-freeze.json").read_text())
    assert freeze["status"] == "PASS"
    assert freeze["schema"] == manifest["schemas"]["phase_1_freeze"]
    assert freeze["manifest_sha256"] == sha256(MANIFEST_PATH)
    assert freeze["schema_catalog_sha256"] == sha256(SCHEMAS_PATH)
    assert freeze["commands"]["phase_2_run"] == frozen_run
    for relative, expected in freeze["source_hashes"].items():
        assert sha256(ROOT / relative) == expected, relative
    assert freeze["timed_execution_authorized"]
    assert freeze["timed_samples"] == 0
    assert freeze["benchmark_leases"] == 0
    print("PASS: v3 frozen hashes, receipt/mode contracts, local gates, exact "
          "untimed success/refusal returns, matrix, and timing authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
