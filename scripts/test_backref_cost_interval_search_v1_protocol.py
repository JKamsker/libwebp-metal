#!/usr/bin/env python3
"""Untimed static validation of the frozen interval-search-v1 protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import backref_cost_interval_search_v1_archive as archive_protocol


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "backref_cost_interval_search_v1_manifest.json"
CATALOG = ROOT / "scripts" / "backref_cost_interval_search_v1_schemas.json"
EXPECTED = "WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V1_COMMIT"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in ("WEBP_BENCHMARK_SESSION", EXPECTED):
        env.pop(name, None)
    return subprocess.run(argv, cwd=ROOT, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          check=False)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads(CATALOG.read_text())
    assert manifest["schema"] == \
        "libwebp-backref-cost-interval-search-v1-frozen-protocol-v1"
    assert manifest["protocol_version"] == 1
    assert catalog["protocol_version"] == 1
    assert manifest["base_commit"] == "568d2476afef3465294bec6a4e099d1b598135f7"
    assert "required environment" in manifest["design_commit"]
    assert manifest["independence"]["performance_inputs"] == []
    assert manifest["remote_host"]["ssh_alias"] == "pandocs-agent"
    assert manifest["remote_host"]["safe_root_basename"] == \
        ".libwebp-metal-backref-cost-interval-search-v1"
    assert manifest["remote_host"]["architecture"] == "arm64"
    assert manifest["remote_host"]["cpu_brand"] == "Apple M4"
    assert manifest["builds"]["forbidden_backend"] == "CUDA"
    assert "makefile.unix" in manifest["builds"]["system"]
    assert "cmake" in manifest["builds"]["system"]
    assert manifest["toolchain"]["environment"]["PATH"] == \
        "/usr/bin:/bin:/usr/sbin:/sbin"
    assert manifest["protocol"]["methods"] == [4, 6]
    assert "separate untimed diagnostic build" in manifest["protocol"]["recorders"]
    assert manifest["resources"]["parallel_timed_processes"] == 1
    assert manifest["protocol"]["acceptance"][
        "paired_median_ratio_maximum"] == 0.995
    assert manifest["protocol"]["acceptance"]["p95_ratio_maximum"] == 1.005
    state_fields = set(manifest["protocol"]["execution_state_fields"])
    assert {"effective compiler", "effective SDK", "power source",
            "Low Power Mode", "thermal/performance warnings", "available disk",
            "available memory", "process table", "child stderr",
            "sole synchronous execution"} <= state_fields

    life = manifest["protocol"]["lifecycles"]
    cases = len(manifest["corpus"]["timed"])
    methods = len(manifest["protocol"]["methods"])
    commands = cases * methods * sum(
        2 * life[name]["process_pairs"] for name in ("cold", "warm"))
    cold = cases * methods * 2 * life["cold"]["process_pairs"]
    warmups = (cases * methods * 2 * life["warm"]["process_pairs"] *
               life["warm"]["discarded_warmups_per_process"])
    warm = (cases * methods * 2 * life["warm"]["process_pairs"] *
            life["warm"]["measured_encodes_per_process"])
    inventory = manifest["protocol"]["expected_inventory"]
    assert commands == inventory["command_processes"] == 272
    assert cold == inventory["cold_measured_samples"] == 176
    assert warmups == inventory["warmup_samples"] == 192
    assert warm == inventory["warm_measured_samples"] == 864
    assert cold + warm == inventory["total_measured_samples"] == 1040
    assert inventory["variant_measured_samples"] == 520
    assert inventory["correctness_cells"] == 26
    assert inventory["work_metric_rows"] == 16
    assert inventory["evaluation_cells"] == 16
    assert inventory["required_holdout_cells"] == 8
    assert len(manifest["protocol"]["pair_order"]) == 11
    design_inventory = manifest["protocol"]["design_validation_inventory"]
    assert design_inventory["remote_exact_build_commands"] == 10
    assert design_inventory["remote_correctness_cells"] == 26
    assert design_inventory["toolchain_refusal_fixtures"] == 2
    assert design_inventory["remote_build_archive_members"] == 9
    assert design_inventory["early_refusal_archive_members"] == 4

    schema_ids = set(catalog["schemas"])
    for name, schema_id in manifest["schemas"].items():
        if name != "catalog":
            assert schema_id in schema_ids
    assert manifest["schemas"]["catalog"] == str(CATALOG.relative_to(ROOT))
    assert manifest["frozen_artifacts"]
    for artifact in manifest["frozen_artifacts"]:
        assert digest(ROOT / artifact["path"]) == artifact["sha256"], artifact

    source = (ROOT / manifest["candidate"]["source"]).read_text()
    runner = (ROOT / manifest["candidate"]["runner"]).read_text()
    operator = (ROOT / "scripts" /
                "run_backref_cost_interval_search_v1_experiment.py").read_text()
    driver = (ROOT / "scripts" /
              "execute_backref_cost_interval_search_v1.py").read_text()
    path_guard = (ROOT / "scripts" /
                  "backref_cost_interval_search_v1_paths.py").read_text()
    admission = (ROOT / "scripts" /
                 "backref_cost_interval_search_v1_admission.py").read_text()
    archive = (ROOT / "scripts" /
               "backref_cost_interval_search_v1_archive.py").read_text()
    runtime = manifest["candidate"]["runtime_flag"]
    fault = manifest["candidate"]["failure_injection_flag"]
    assert runtime in source + runner and fault in source
    assert "WEBP_BENCHMARK_SESSION" in runner + operator + driver
    assert "work_metric_gate" in operator
    assert "recorder build refuses timed samples" in runner
    assert "WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_RECORDER=1" in operator
    assert "Runner.Worker" in operator + admission
    assert "Runner.Listener" in operator
    assert "timed-child-stderr.log" in operator
    assert "statistics.median(ratios)" in operator
    assert "toolchain_admission" in operator
    assert '"cmake_used": False' in operator
    assert "artifact-hashes.json" in operator and "controlled_run" in operator
    assert "math.ceil(0.95 * len(values)) - 1" in operator
    assert 'if role == "holdout"' in operator
    assert "fcntl.LOCK_UN" in operator and 'lease_record["released"] = True' in operator
    assert "pandocs-agent" in admission
    assert "rm -rf" not in driver + path_guard + admission
    assert "mktemp" in path_guard and "shutil.rmtree(candidate)" in path_guard
    assert "os.path.realpath" in path_guard and "os.path.dirname" in path_guard
    assert "RUN_TOKEN.fullmatch" in path_guard
    assert '["git", "init", "--bare"' in admission
    assert '"git", "-C", str(verification_repository), "bundle", "verify"' in admission
    assert "bundle_verified_in_repository_context" in admission
    assert "verification_repository_removed" in admission
    assert "source_tree" in admission and "source_hashes" in admission
    assert "PATH_GUARD.read_bytes()" in admission
    assert "exercise_malformed=(mode == \"admission-only\")" in driver
    assert "benchmark_lease_acquisition_attempted\": False" in driver
    assert "timed_binary_invoked\": False" in driver
    assert "admission.admit_source" in driver
    assert "tar.extractall" not in driver
    assert "tar -czf" not in driver and "tar.extractall" not in archive
    assert "tarfile.GNU_FORMAT" in archive
    assert "st_nlink != 1" in archive
    assert "os.path.realpath" in archive and "os.path.commonpath" in archive
    assert "artifact index/tree membership mismatch" in archive
    assert "inspect_archive" in driver and "quarantine" in driver
    assert driver.index("fetch_regular(record, \"evidence/lease-record.json\"") < \
        driver.index("extract_archive")
    assert driver.index("admission.finish_admission(record)") < \
        driver.index("cleanup-receipt.json")

    design = ROOT / "evidence" / "backref-cost-interval-search-v1-design"
    live = json.loads((design / "live-validation.json").read_text())
    required_live = catalog["schemas"][
        "libwebp-backref-cost-interval-search-v1-live-return-validation-v1"][
            "required"]
    assert all(field in live for field in required_live)
    assert live["status"] == "PASS"
    assert not live["benchmark_lease_acquisition_attempted"]
    assert not live["timed_binary_invoked"]
    assert live["artifact_index_verified_after_extraction"]
    assert live["cleanup_receipt"]["absence_proved"]
    assert len(live["builder_rejections"]) == 3
    assert len(live["malicious_rejections"]) == 5
    assert all(row["no_content_extracted"]
               for row in live["malicious_rejections"].values())
    assert all(row["hashes_match"] for row in live["transfers"].values())
    toolchain_inspection = json.loads(
        (design / "runner-toolchain-inspection.json").read_text())
    assert toolchain_inspection["status"] == "PASS"
    assert toolchain_inspection["noninteractive_path"] == \
        "/usr/bin:/bin:/usr/sbin:/sbin"
    assert not toolchain_inspection["cmake_selected"]
    remote = json.loads((design / "remote-rehearsal.json").read_text())
    assert all(field in remote for field in catalog["schemas"][
        manifest["schemas"]["remote_rehearsal"]]["required"])
    assert remote["status"] == "PASS"
    assert not remote["benchmark_session_present"]
    assert not remote["benchmark_lease_attempted"]
    assert not remote["timed_runner_invoked"]
    assert remote["cleanup_receipt"]["absence_proved"]
    rehearsal = json.loads(
        (design / "remote-rehearsal-returned/rehearsal.json").read_text())
    assert rehearsal["correctness_cells"] == 26
    assert rehearsal["work_metric_rows"] == 16
    assert all(row["refused"] for row in
               rehearsal["toolchain_refusal_fixtures"].values())
    assert len(json.loads(
        (design / "remote-rehearsal-returned/build-commands.json").read_text())[
            "commands"]) == 10
    early = json.loads((design / "early-refusal-return.json").read_text())
    assert all(field in early for field in catalog["schemas"][
        manifest["schemas"]["refusal_return_rehearsal"]]["required"])
    assert early["status"] == "PASS"
    assert early["refusal"]["stage"] == "toolchain-admission"
    assert early["artifact_index_verified_after_extraction"]
    assert early["cleanup_receipt"]["absence_proved"]
    archive_protocol.verify_returned_index(
        design / "returned-evidence-hashes.json", design)

    with tempfile.TemporaryDirectory(prefix="interval-search-v1-refusal-") as raw:
        output = Path(raw) / "must-not-exist"
        refused = execute([
            sys.executable,
            "scripts/run_backref_cost_interval_search_v1_experiment.py",
            "run", str(output)])
        assert refused.returncode != 0
        assert (output / "artifact-hashes.json").is_file()
        assert (output / "refusal.json").is_file()
        assert (output / "lease-record.json").is_file()
        assert "WEBP_BENCHMARK_SESSION=exclusive" in json.loads(
            (output / "refusal.json").read_text())["reason"]
        for child in output.iterdir():
            if child.is_file():
                child.unlink()
        output.rmdir()
        remote_refused = execute([
            sys.executable,
            "scripts/execute_backref_cost_interval_search_v1.py",
            "run", str(output)])
        assert remote_refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in remote_refused.stdout
        assert not output.exists()
        admission_refused = execute([
            sys.executable,
            "scripts/execute_backref_cost_interval_search_v1.py",
            "admission-only", str(output)])
        assert admission_refused.returncode != 0
        assert EXPECTED in admission_refused.stdout
        assert not output.exists()

    print("PASS: interval-search v1 schemas, hashes, matrix inventory, session refusals, "
          "runner isolation, repository-context admission, indexed archive, "
          "malicious rejection, independent lease/cleanup, returned hashes, "
          "shared admission-only path, and exact cleanup scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
