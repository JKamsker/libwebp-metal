#!/usr/bin/env python3
"""Untimed static validation of the frozen remote-v3 protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "backref_cost_workspace_remote_v3_manifest.json"
CATALOG = ROOT / "scripts" / "backref_cost_workspace_remote_v3_schemas.json"
EXPECTED = "WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V3_COMMIT"


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
        "libwebp-backref-cost-workspace-remote-v3-frozen-protocol-v1"
    assert manifest["protocol_version"] == 3
    assert manifest["base_commit"] == "805e5ac4341ccf0d1ef960adb9107275652c973f"
    assert manifest["design_commit"] == "1b6f6b707e79bfcfc1d912bf1b4c916b3f7b58e5"
    assert manifest["independence"]["performance_inputs"] == []
    assert manifest["remote_host"]["ssh_alias"] == "pandocs-agent"
    assert manifest["remote_host"]["safe_root_basename"] == \
        ".libwebp-metal-backref-cost-workspace-remote-v3"
    assert manifest["remote_host"]["architecture"] == "arm64"
    assert manifest["remote_host"]["cpu_brand"] == "Apple M4"
    assert manifest["builds"]["forbidden_backend"] == "CUDA"
    assert manifest["protocol"]["methods"] == [4, 6]
    assert manifest["protocol"]["recorders"] == "none"
    assert manifest["resources"]["parallel_timed_processes"] == 1
    assert manifest["protocol"]["acceptance"][
        "paired_median_ratio_maximum"] == 0.99
    assert manifest["protocol"]["acceptance"]["p95_ratio_maximum"] == 1.01
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
    assert commands == inventory["command_processes"] == 408
    assert cold == inventory["cold_measured_samples"] == 264
    assert warmups == inventory["warmup_samples"] == 288
    assert warm == inventory["warm_measured_samples"] == 1296
    assert cold + warm == inventory["total_measured_samples"] == 1560
    assert inventory["variant_measured_samples"] == 780
    assert inventory["correctness_cells"] == 26
    assert inventory["evaluation_cells"] == 24
    assert inventory["required_holdout_cells"] == 12
    assert len(manifest["protocol"]["pair_order"]) == 11

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
                "run_backref_cost_workspace_remote_v3_experiment.py").read_text()
    driver = (ROOT / "scripts" /
              "execute_backref_cost_workspace_remote_v3.py").read_text()
    path_guard = (ROOT / "scripts" /
                  "backref_cost_workspace_remote_v3_paths.py").read_text()
    admission = (ROOT / "scripts" /
                 "backref_cost_workspace_remote_v3_admission.py").read_text()
    runtime = manifest["candidate"]["runtime_flag"]
    fault = manifest["candidate"]["failure_injection_flag"]
    assert runtime in source + runner and fault in source
    assert "WEBP_BENCHMARK_SESSION" in runner + operator + driver
    assert "Runner.Worker" in operator + admission
    assert "Runner.Listener" in operator
    assert "timed-child-stderr.log" in operator
    assert "statistics.median(ratios)" in operator
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

    rehearsal = json.loads((ROOT / "evidence" /
        "backref-cost-workspace-remote-v3-design" /
        "admission-rehearsal.json").read_text())
    required_rehearsal = catalog["schemas"][manifest["schemas"][
        "admission_rehearsal"]]["required"]
    assert all(field in rehearsal for field in required_rehearsal)
    assert rehearsal["status"] == "PASS"
    assert rehearsal["source_commit"] == manifest["design_commit"]
    assert not rehearsal["benchmark_lease_acquisition_attempted"]
    assert not rehearsal["timed_binary_invoked"]
    assert rehearsal["cleanup"]["absence_proved"]
    admitted = rehearsal["admission"]
    assert admitted["admission"]["bundle_verified_in_repository_context"]
    assert admitted["admission"]["verification_repository_removed"]
    assert admitted["admission"]["clean_status"]
    assert admitted["source_bundle_sha256"] == \
        admitted["remote_source_bundle_sha256"]
    assert len(admitted["admission"]["source_tree"]) == 40
    assert admitted["admission"]["source_hashes"]
    assert admitted["malformed_bundle"]["hash_match"]
    assert admitted["malformed_bundle"]["rejected"]
    assert admitted["malformed_bundle"]["verification_repository_absent"]
    assert admitted["malformed_bundle"]["clone_absent"]

    with tempfile.TemporaryDirectory(prefix="remote-v3-refusal-") as raw:
        output = Path(raw) / "must-not-exist"
        refused = execute([
            sys.executable,
            "scripts/run_backref_cost_workspace_remote_v3_experiment.py",
            "run", str(output)])
        assert refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in refused.stdout
        assert not output.exists()
        remote_refused = execute([
            sys.executable,
            "scripts/execute_backref_cost_workspace_remote_v3.py",
            "run", str(output)])
        assert remote_refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in remote_refused.stdout
        assert not output.exists()
        admission_refused = execute([
            sys.executable,
            "scripts/execute_backref_cost_workspace_remote_v3.py",
            "admission-only", str(output)])
        assert admission_refused.returncode != 0
        assert EXPECTED in admission_refused.stdout
        assert not output.exists()

    print("PASS: v3 schemas, hashes, matrix inventory, session refusals, "
          "runner isolation, repository-context admission, malformed rejection, "
          "shared admission-only path, and exact cleanup scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
