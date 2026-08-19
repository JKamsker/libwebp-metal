#!/usr/bin/env python3
"""Static, workload-free process-ownership guards for attribution v6."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import backref_cost_attribution_v6_admission as admission


ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v6_admission.py",
    "scripts/backref_cost_attribution_v6_archive.py",
    "scripts/backref_cost_attribution_v6_paths.py",
    "scripts/execute_backref_cost_attribution_v6.py",
    "scripts/run_backref_cost_attribution_v6_experiment.py",
)
FORBIDDEN_SIGNAL_ATTRIBUTES = {"kill", "killpg", "terminate", "send_signal"}
FORBIDDEN_DISCOVERY_EXECUTABLES = {"pgrep", "pidof"}


class FinishedProcess:
    """Inert process-shaped fixture; it cannot send a signal."""

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


def literal_executable(node: ast.AST) -> str | None:
    if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
        return None
    first = node.elts[0]
    return first.value if isinstance(first, ast.Constant) and isinstance(
        first.value, str) else None


def static_source_guards() -> None:
    signal_sites = []
    for relative in INFRASTRUCTURE:
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node.func)
            executable = literal_executable(node.args[0]) if node.args else None
            assert executable not in admission.FORBIDDEN_TERMINATION_COMMANDS
            assert executable not in FORBIDDEN_DISCOVERY_EXECUTABLES
            assert name not in {"os.kill", "os.killpg", "signal.pthread_kill"}
            if name.rsplit(".", 1)[-1] in FORBIDDEN_SIGNAL_ATTRIBUTES:
                signal_sites.append((relative, node.lineno, name))
            if name == "subprocess.Popen":
                assert relative == "scripts/backref_cost_attribution_v6_admission.py"
            if name == "subprocess.run":
                assert relative == "scripts/backref_cost_attribution_v6_paths.py"
                assert executable == "mktemp"

    # The sole signaling site is the private retained-Popen timeout helper.
    assert len(signal_sites) == 1
    relative, _, name = signal_sites[0]
    assert relative == "scripts/backref_cost_attribution_v6_admission.py"
    assert name == "self.process.kill"


def owned_child_contract() -> None:
    assert tuple(admission.FORBIDDEN_TERMINATION_COMMANDS) == (
        "kill", "pkill", "killall")
    assert tuple(admission.OBSERVE_ONLY_EXTERNAL_PROCESS_CLASSES) == (
        "ssh", "runner", "profiler", "editor", "user-shell", "service")
    for command in admission.FORBIDDEN_TERMINATION_COMMANDS:
        try:
            admission._reject_generic_termination(
                ["ssh", f"set -eu; {command} -TERM 41731"])
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"generic termination accepted: {command}")

    # A process-table PID cannot enter the timeout API: it has no PID argument;
    # the private object retains the exact Popen creation handle and PID.
    signature = inspect.signature(admission._OwnedChild.stop_after_timeout)
    assert tuple(signature.parameters) == ("self",)
    process = FinishedProcess()
    owned = admission._OwnedChild(
        process=process, pid=process.pid, creation_identity=id(process))
    owned.stop_after_timeout()
    mismatched = admission._OwnedChild(
        process=process, pid=process.pid + 1, creation_identity=id(process))
    try:
        mismatched.stop_after_timeout()
    except RuntimeError:
        pass
    else:
        raise AssertionError("changed creation identity was accepted")


def cleanup_contract() -> None:
    admission_source = inspect.getsource(admission.cleanup_remote)
    assert 'remote_path_guard("cleanup", home, safe_root, run_directory)' in \
        admission_source
    assert 'result.get("removed_exact_validated_child")' in admission_source
    assert '"absence_proved"' in admission_source


def main() -> int:
    static_source_guards()
    owned_child_contract()
    cleanup_contract()
    print("PASS: attribution v6 signals only its retained direct-child handle; "
          "discovered processes are refusal-only and cleanup is receipt-scoped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
