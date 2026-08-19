#!/usr/bin/env python3
"""Static, workload-free ownership guards for attribution v8."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import backref_cost_attribution_v8_admission as admission
import backref_cost_attribution_v8_transport as transport
import execute_backref_cost_attribution_v8 as executor


ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v8_admission.py",
    "scripts/backref_cost_attribution_v8_archive.py",
    "scripts/backref_cost_attribution_v8_paths.py",
    "scripts/backref_cost_attribution_v8_transport.py",
    "scripts/execute_backref_cost_attribution_v8.py",
    "scripts/run_backref_cost_attribution_v8_experiment.py",
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
        ("scripts/backref_cost_attribution_v8_admission.py", "self.process.kill")]
    assert popen_sites == ["scripts/backref_cost_attribution_v8_admission.py"]


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
    allowed = snapshot(
        (1, 0, "/sbin/launchd"),
        (80, 1, "/usr/bin/ssh"),
        (90, 80, "/bin/zsh"),
        (100, 90, "/usr/bin/python3"),
        (110, 1, "/Users/example/Runner.Listener"),
    )
    # These are deliberately hostile argv/source strings.  They are not part
    # of the frozen pid/ppid/comm snapshot and therefore cannot affect identity.
    ignored_ancestor_argv_and_source = (
        "python3 -c 'backref_cost_attribution_v8_experiment_runner "
        "CUDA nvidia-smi benchmark_metal Runner.Worker'"
    )
    assert "CUDA" in ignored_ancestor_argv_and_source
    observed = transport.classify_process_snapshot(allowed, 100)
    assert observed["argument_text_collected"] is False
    assert [row["pid"] for row in observed["verified_ancestor_chain"]] == \
        [100, 90, 80, 1]
    assert observed["exact_identity_conflicts"] == []

    benign_argv = "--help --quiet"
    assert benign_argv
    exact_conflicts = (
        "backref_cost_attribution_v8_experiment_runner",
        "metal_benchmark", "nvidia-smi", "Runner.Worker",
    )
    for index, identity in enumerate(exact_conflicts, start=200):
        fixture = allowed + f"{index} 1 /tmp/{identity}\n".encode()
        try:
            transport.classify_process_snapshot(fixture, 100)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError(f"exact executable identity was allowed: {identity}")

    lookalikes = (
        "prefix_backref_cost_attribution_v8_experiment_runner",
        "backref_cost_attribution_v8_experiment_runner_suffix",
        "metal_benchmark-helper", "xnvidia-smi", "Runner.Worker.backup",
        "cuda-helper",
    )
    lookalike_snapshot = allowed + b"".join(
        f"{300 + index} 1 /tmp/{identity}\n".encode()
        for index, identity in enumerate(lookalikes))
    assert transport.classify_process_snapshot(
        lookalike_snapshot, 100)["exact_identity_conflicts"] == []

    malformed = (
        b"", allowed[:-1],
        allowed + b"100 90 /usr/bin/python3\n",
        snapshot((1, 0, "/sbin/launchd"), (100, 99, "/usr/bin/python3")),
        snapshot((1, 0, "/sbin/launchd"), (90, 100, "/bin/zsh"),
                 (100, 90, "/usr/bin/python3")),
        snapshot((1, 0, "/sbin/launchd"), (100, 1, "/tmp/python3")),
        snapshot((1, 0, "/sbin/launchd"), (100, 1, "relative/python3")),
        b"1 0 /sbin/launchd\n100 1 /usr/bin/python3\xff\n",
    )
    for fixture in malformed:
        try:
            transport.classify_process_snapshot(fixture, 100)
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError("malformed or ambiguous identity was allowed")


def single_session_contract() -> None:
    command = executor._transport_command()
    assert command[0] == "ssh" and command.count("ssh") == 1
    assert "BatchMode=yes" in command and "ConnectTimeout=10" in command
    source = (ROOT / "scripts/execute_backref_cost_attribution_v8.py").read_text()
    assert "scp" not in source
    assert "cleanup_remote" not in source and "finish_admission" not in source
    assert '"post_run_remote_cleanup_operations": 0' in source
    remote = (ROOT / "scripts/backref_cost_attribution_v8_transport.py").read_text()
    assert "shutil.rmtree(child)" in remote
    assert '"cleanup-footer"' in remote
    assert "_validate_child(home, root, child)" in remote


def main() -> int:
    static_guards()
    direct_child_contract()
    identity_only_process_contract()
    single_session_contract()
    print("PASS: attribution v8 uses exact executable identity from frozen "
          "pid/ppid/comm snapshots, verifies its transport ancestors, keeps "
          "discovered PIDs out of signal APIs, and has one in-session cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
