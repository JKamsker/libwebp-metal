#!/usr/bin/env python3
"""Untimed static validation of the frozen remote-v2 protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "backref_cost_workspace_remote_v2_manifest.json"
CATALOG = ROOT / "scripts" / "backref_cost_workspace_remote_v2_schemas.json"
EXPECTED = "WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V2_COMMIT"


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
        "libwebp-backref-cost-workspace-remote-v2-frozen-protocol-v1"
    assert manifest["protocol_version"] == 2
    assert manifest["base_commit"] == "d12036f790cce1dd4bef9fe3c963b0ef294d4c4a"
    assert manifest["design_commit"] == "66c5bca06e4371923ebd038e0776524b7c78bb9e"
    assert manifest["independence"]["performance_inputs"] == []
    assert manifest["remote_host"]["ssh_alias"] == "pandocs-agent"
    assert manifest["remote_host"]["safe_root_basename"] == \
        ".libwebp-metal-backref-cost-workspace-remote-v2"
    assert manifest["remote_host"]["architecture"] == "arm64"
    assert manifest["remote_host"]["cpu_brand"] == "Apple M4"
    assert manifest["builds"]["forbidden_backend"] == "CUDA"
    assert manifest["protocol"]["methods"] == [4, 6]
    assert manifest["protocol"]["recorders"] == "none"
    assert manifest["resources"]["parallel_timed_processes"] == 1

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
                "run_backref_cost_workspace_remote_v2_experiment.py").read_text()
    driver = (ROOT / "scripts" /
              "execute_backref_cost_workspace_remote_v2.py").read_text()
    path_guard = (ROOT / "scripts" /
                  "backref_cost_workspace_remote_v2_paths.py").read_text()
    runtime = manifest["candidate"]["runtime_flag"]
    fault = manifest["candidate"]["failure_injection_flag"]
    assert runtime in source + runner and fault in source
    assert "WEBP_BENCHMARK_SESSION" in runner + operator + driver
    assert "Runner.Worker" in operator + driver
    assert "Runner.Listener" in operator
    assert "timed-child-stderr.log" in operator
    assert "pandocs-agent" in driver
    assert "rm -rf" not in driver + path_guard
    assert "mktemp" in path_guard and "shutil.rmtree(candidate)" in path_guard
    assert "os.path.realpath" in path_guard and "os.path.dirname" in path_guard
    assert "RUN_TOKEN.fullmatch" in path_guard
    assert "git bundle verify" in driver
    assert "PATH_GUARD.read_bytes()" in driver
    assert "tar.extractall" not in driver

    with tempfile.TemporaryDirectory(prefix="remote-v2-refusal-") as raw:
        output = Path(raw) / "must-not-exist"
        refused = execute([
            sys.executable,
            "scripts/run_backref_cost_workspace_remote_v2_experiment.py",
            "run", str(output)])
        assert refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in refused.stdout
        assert not output.exists()
        remote_refused = execute([
            sys.executable,
            "scripts/execute_backref_cost_workspace_remote_v2.py",
            "run", str(output)])
        assert remote_refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in remote_refused.stdout
        assert not output.exists()

    print("PASS: v2 schemas, hashes, matrix inventory, session refusals, "
          "runner isolation, exact path guard, safe transfer, and cleanup scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
