#!/usr/bin/env python3
"""Static, workload-free ownership guards for attribution v9."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
from unittest import mock

import backref_cost_attribution_v9_admission as admission
import backref_cost_attribution_v9_transport as transport
import execute_backref_cost_attribution_v9 as executor


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = (
    ROOT / "evidence/backref-cost-attribution-v9-design/phase1b-authorization.json")
MANIFEST = ROOT / "scripts/backref_cost_attribution_v9_manifest.json"
POST_CYCLE_REMEDIATION = (
    ROOT / "evidence/backref-cost-attribution-v9-post-cycle-remediation-20260819"
    / "remediation.json")
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v9_admission.py",
    "scripts/backref_cost_attribution_v9_archive.py",
    "scripts/backref_cost_attribution_v9_paths.py",
    "scripts/backref_cost_attribution_v9_transport.py",
    "scripts/execute_backref_cost_attribution_v9.py",
    "scripts/run_backref_cost_attribution_v9_experiment.py",
)
SIGNAL_ATTRIBUTES = {"kill", "killpg", "terminate", "send_signal"}


class FinishedProcess:
    pid = 41731

    @staticmethod
    def poll() -> int:
        return 0

    @staticmethod
    def kill() -> None:
        raise AssertionError("finished child must not be signaled")


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def static_guards() -> None:
    signal_sites = []
    popen_sites = []
    for relative in INFRASTRUCTURE:
        tree = ast.parse((ROOT / relative).read_text(), filename=relative)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node.func)
            assert name not in {"os.kill", "os.killpg", "signal.pthread_kill"}
            if name.rsplit(".", 1)[-1] in SIGNAL_ATTRIBUTES:
                signal_sites.append((relative, name))
            if name == "subprocess.Popen":
                popen_sites.append(relative)
    assert signal_sites == [
        ("scripts/backref_cost_attribution_v9_admission.py", "self.process.kill")]
    assert popen_sites == ["scripts/backref_cost_attribution_v9_admission.py"]


def direct_child_contract() -> None:
    assert inspect.signature(admission._OwnedChild.stop_after_timeout).parameters.keys() == {"self"}
    process = FinishedProcess()
    owned = admission._OwnedChild(process, process.pid, id(process))
    owned.stop_after_timeout()
    changed = admission._OwnedChild(process, process.pid + 1, id(process))
    try:
        changed.stop_after_timeout()
    except RuntimeError:
        pass
    else:
        raise AssertionError("changed direct-child creation identity was accepted")


def snapshot(*rows: tuple[int, int, str]) -> bytes:
    return "".join(f"{pid} {ppid} {comm}\n" for pid, ppid, comm in rows).encode()


def identity_only_process_contract() -> None:
    # Live shape of the v8 refusal: slashless comm tokens from the raw
    # pid/ppid/comm snapshot are valid identities, never relative paths.
    allowed = snapshot(
        (1, 0, "launchd"),
        (80, 1, "sshd-session"),
        (90, 80, "zsh"),
        (100, 90, "python3"),
        (110, 1, "Runner.Listener"),
        (111, 1, "unrelated-opaque-worker"),
    )
    # These are deliberately hostile argv/source strings.  They are not part
    # of the frozen pid/ppid/comm snapshot and therefore cannot affect identity.
    ignored_ancestor_argv_and_source = (
        "python3 -c 'backref_cost_attribution_v9_experiment_runner "
        "CUDA nvidia-smi benchmark_metal Runner.Worker'"
    )
    assert "CUDA" in ignored_ancestor_argv_and_source
    observed = transport.classify_process_snapshot(allowed, 100)
    assert observed["argument_text_collected"] is False
    assert observed["resolved_executable_paths"] == []
    assert observed["comm_semantics"].endswith("never a path")
    assert [row["pid"] for row in observed["verified_ancestor_chain"]] == \
        [100, 90, 80, 1]
    assert observed["exact_identity_conflicts"] == []

    benign_argv = "--help --quiet"
    assert benign_argv
    exact_conflicts = (
        "backref_cost_attribution_v9_experiment_runner",
        "metal_benchmark", "nvidia-smi", "Runner.Worker",
    )
    for index, identity in enumerate(exact_conflicts, start=200):
        fixture = allowed + f"{index} 1 {identity}\n".encode()
        try:
            transport.classify_process_snapshot(fixture, 100)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError(f"exact executable identity was allowed: {identity}")

    lookalikes = (
        "prefix_backref_cost_attribution_v9_experiment_runner",
        "backref_cost_attribution_v9_experiment_runner_suffix",
        "metal_benchmark-helper", "xnvidia-smi", "Runner.Worker.backup",
        "cuda-helper",
    )
    lookalike_snapshot = allowed + b"".join(
        f"{300 + index} 1 {identity}\n".encode()
        for index, identity in enumerate(lookalikes))
    assert transport.classify_process_snapshot(
        lookalike_snapshot, 100)["exact_identity_conflicts"] == []

    # Frozen v9 also rejects a nominal absolute path when realpath resolves it
    # elsewhere.  That host-dependent rejection surfaced in post-cycle CI.  Do
    # not turn this frozen fixture into an authority-bearing success case; v10
    # must establish corrected identity semantics under fresh gates.
    path_ancestor = snapshot(
        (1, 0, "launchd"), (90, 1, "opaque-python-name"))
    with mock.patch.object(transport.os.path, "realpath",
                           return_value="/usr/bin/python3.13"):
        try:
            transport.classify_process_snapshot(path_ancestor, 90, {
                90: {"path": "/usr/bin/python3",
                     "provenance": "fixture:proc_pidpath",
                     "read_only": True}})
        except transport.FrameRefusal as error:
            assert str(error) == (
                "resolved executable path is not "
                "absolute/canonical/provenanced")
        else:
            raise AssertionError("frozen noncanonical path rejection changed")

    for unresolved_denied in ("metal_benchmark", "Runner.Worker"):
        try:
            transport.classify_process_snapshot(
                allowed + f"400 1 {unresolved_denied}\n".encode(), 100)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError("denied comm was accepted without path evidence")

    try:
        transport.classify_process_snapshot(
            allowed + b"401 1 benign-tool\n", 100, {
                401: {"path": "/tmp/metal_benchmark",
                      "provenance": "fixture:read-only-resolver",
                      "read_only": True}})
    except transport.FrameRefusal:
        pass
    else:
        raise AssertionError("exact denied verified path was accepted")

    malformed = (
        b"", allowed[:-1],
        allowed + b"100 90 python3\n",
        snapshot((1, 0, "launchd"), (100, 99, "python3")),
        snapshot((1, 0, "launchd"), (90, 100, "zsh"),
                 (100, 90, "python3")),
        snapshot((1, 0, "launchd"), (100, 1, "unknown-ancestor")),
        snapshot((1, 0, "launchd"), (100, 1, "relative/python3")),
        b"1 0 launchd\n100 1 python3\xff\n",
    )
    for fixture in malformed:
        try:
            transport.classify_process_snapshot(fixture, 100)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError("malformed or ambiguous identity was allowed")

    malformed_path_records = (
        {100: {"path": "python3", "provenance": "fixture", "read_only": True}},
        {100: {"path": "/tmp/../usr/bin/python3", "provenance": "fixture",
               "read_only": True}},
        {100: {"path": "/usr/bin/python3", "provenance": "", "read_only": True}},
        {999: {"path": "/usr/bin/python3", "provenance": "fixture",
               "read_only": True}},
    )
    for records in malformed_path_records:
        try:
            transport.classify_process_snapshot(allowed, 100, records)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError("malformed resolved path evidence was allowed")


def single_session_contract() -> None:
    command = executor._transport_command()
    assert command[0] == "ssh" and command.count("ssh") == 1
    assert "BatchMode=yes" in command and "ConnectTimeout=10" in command
    source = (ROOT / "scripts/execute_backref_cost_attribution_v9.py").read_text()
    assert "scp" not in source
    assert "cleanup_remote" not in source and "finish_admission" not in source
    assert '"post_run_remote_cleanup_operations": 0' in source
    remote = (ROOT / "scripts/backref_cost_attribution_v9_transport.py").read_text()
    assert "shutil.rmtree(child)" in remote
    assert '"cleanup-footer"' in remote
    assert "_validate_child(home, root, child)" in remote


def post_cycle_authorization_contract() -> None:
    authorization = json.loads(AUTHORIZATION.read_text())
    assert authorization["authorization_status"] == "REFUSED"
    assert authorization["timed_execution_authorized"] is False
    assert authorization["phase_2_authority"] == "NONE"

    remediation = json.loads(POST_CYCLE_REMEDIATION.read_text())
    assert remediation["status"] == "FIXTURE_CORRECTED_FROZEN_V9_UNCHANGED"
    assert remediation["authorization"] == {
        "timed_execution_authorized": False,
        "phase_2_authority": "NONE",
        "v9_execution_authority_after_remediation": False,
    }
    assert remediation["frozen_artifact_hashes"]["status"] == \
        "INTENTIONALLY_SUPERSEDED_INVALIDATED"
    frozen = next(
        row for row in json.loads(MANIFEST.read_text())["frozen_artifacts"]
        if row["path"] ==
        "scripts/test_backref_cost_attribution_v9_process_ownership.py")
    current_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert frozen["sha256"] == remediation["frozen_artifact_hashes"][
        "frozen_sha256"]
    assert current_sha256 == remediation["frozen_artifact_hashes"][
        "post_cycle_sha256"]
    assert current_sha256 != frozen["sha256"]
    assert remediation["future_v10"]["fresh_gates_required"] is True
    assert remediation["conclusion"] == {
        "interval_family": "UNASSESSED",
        "production_consequence": "NONE",
    }


def main() -> int:
    static_guards()
    direct_child_contract()
    identity_only_process_contract()
    single_session_contract()
    post_cycle_authorization_contract()
    print("PASS: attribution v9 treats comm as an opaque exact token, accepts "
          "slashless v8 live-shape identities, records the frozen path rejection "
          "and false/NONE authorization, keeps "
          "discovered PIDs out of signal APIs, and has one in-session cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
