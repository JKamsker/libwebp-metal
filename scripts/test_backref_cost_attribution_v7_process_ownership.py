#!/usr/bin/env python3
"""Static, workload-free ownership guards for attribution v7."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import backref_cost_attribution_v7_admission as admission
import execute_backref_cost_attribution_v7 as executor


ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v7_admission.py",
    "scripts/backref_cost_attribution_v7_archive.py",
    "scripts/backref_cost_attribution_v7_paths.py",
    "scripts/backref_cost_attribution_v7_transport.py",
    "scripts/execute_backref_cost_attribution_v7.py",
    "scripts/run_backref_cost_attribution_v7_experiment.py",
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
        ("scripts/backref_cost_attribution_v7_admission.py", "self.process.kill")]
    assert popen_sites == ["scripts/backref_cost_attribution_v7_admission.py"]


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


def single_session_contract() -> None:
    command = executor._transport_command()
    assert command[0] == "ssh" and command.count("ssh") == 1
    assert "BatchMode=yes" in command and "ConnectTimeout=10" in command
    source = (ROOT / "scripts/execute_backref_cost_attribution_v7.py").read_text()
    assert "scp" not in source
    assert "cleanup_remote" not in source and "finish_admission" not in source
    assert '"post_run_remote_cleanup_operations": 0' in source
    remote = (ROOT / "scripts/backref_cost_attribution_v7_transport.py").read_text()
    assert "shutil.rmtree(child)" in remote
    assert '"cleanup-footer"' in remote
    assert "_validate_child(home, root, child)" in remote


def main() -> int:
    static_guards()
    direct_child_contract()
    single_session_contract()
    print("PASS: attribution v7 has one directly owned SSH transport signal site, "
          "observe-only discovery, in-session exact-child cleanup, and no SCP/reconnect")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
