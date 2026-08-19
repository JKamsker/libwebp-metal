#!/usr/bin/env python3
"""Static, workload-free ownership guards for attribution v10."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import backref_cost_attribution_v10_admission as admission
import backref_cost_attribution_v10_transport as transport
import execute_backref_cost_attribution_v10 as executor


ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v10_admission.py",
    "scripts/backref_cost_attribution_v10_archive.py",
    "scripts/backref_cost_attribution_v10_paths.py",
    "scripts/backref_cost_attribution_v10_transport.py",
    "scripts/execute_backref_cost_attribution_v10.py",
    "scripts/run_backref_cost_attribution_v10_experiment.py",
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
        ("scripts/backref_cost_attribution_v10_admission.py", "self.process.kill")]
    assert popen_sites == ["scripts/backref_cost_attribution_v10_admission.py"]


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


def refused(value: bytes, self_pid: int, reason: str | None = None) -> None:
    try:
        transport.classify_process_snapshot(value, self_pid)
    except transport.FrameRefusal as error:
        if reason is not None:
            assert str(error) == reason
    else:
        raise AssertionError("unsafe process snapshot was accepted")


def identity_only_process_contract() -> None:
    # Exact v9 live refusal shape plus slash-bearing and slashless ancestors.
    # These strings resemble paths but remain opaque process-table identities.
    allowed = snapshot(
        (1, 0, "/sbin/launchd"),
        (80, 1, "/usr/libexec/sshd-session"),
        (90, 80, "/bin/zsh"),
        (100, 90, "/usr/bin/python3"),
        (110, 1, "Runner.Listener"),
        (111, 1, "unrelated-opaque-worker"),
        (112, 1, "unrelated comm with spaces"),
        (113, 1, "relative/path-like token"),
    )
    # These are deliberately hostile argv/source strings.  They are not part
    # of the frozen pid/ppid/comm snapshot and therefore cannot affect identity.
    ignored_ancestor_argv_and_source = (
        "python3 -c 'backref_cost_attribution_v10_experiment_runner "
        "CUDA nvidia-smi benchmark_metal Runner.Worker'"
    )
    assert "CUDA" in ignored_ancestor_argv_and_source
    observed = transport.classify_process_snapshot(allowed, 100)
    assert observed["argument_text_collected"] is False
    assert observed["resolved_path_api_used"] is False
    assert observed["filesystem_identity_operations"] == []
    assert observed["raw_comm_semantics"].endswith("never a path")
    assert [row["pid"] for row in observed["verified_ancestor_chain"]] == \
        [100, 90, 80, 1]
    assert observed["verified_ancestor_chain"][-1] == {
        "pid": 1, "ppid": 0, "raw_comm": "/sbin/launchd",
        "lexical_basename": "launchd",
        "raw_comm_identity_kind": "opaque-process-table-string",
        "lexical_basename_identity_kind":
            "final-slash-component-without-filesystem-access",
    }
    assert observed["exact_identity_conflicts"] == []

    slashless = snapshot(
        (1, 0, "launchd"), (80, 1, "sshd-session"),
        (90, 80, "zsh"), (100, 90, "python3"))
    assert transport.classify_process_snapshot(
        slashless, 100)["verified_ancestor_chain"][0]["raw_comm"] == "python3"

    classifier_source = inspect.getsource(transport.parse_process_snapshot) + \
        inspect.getsource(transport.classify_process_snapshot)
    for forbidden in (
            "realpath", "resolve(", ".stat(", "normpath", "isabs",
            "resolved_executable", "Path("):
        assert forbidden not in classifier_source

    benign_argv = "--help --quiet"
    assert benign_argv
    exact_conflicts = (
        "backref_cost_attribution_v10_experiment_runner",
        "backref_cost_attribution_v9_experiment_runner",
        "metal_benchmark", "nvidia-smi", "/usr/local/bin/nvidia-smi",
        "Runner.Worker", "/opt/runner/Runner.Worker",
    )
    for index, identity in enumerate(exact_conflicts, start=200):
        fixture = allowed + f"{index} 1 {identity}\n".encode()
        refused(fixture, 100)

    lookalikes = (
        "prefix_backref_cost_attribution_v10_experiment_runner",
        "backref_cost_attribution_v10_experiment_runner_suffix",
        "metal_benchmark-helper", "xnvidia-smi", "Runner.Worker.backup",
        "cuda-helper", "/tmp/prefix_nvidia-smi", "/tmp/Runner.Worker.suffix",
    )
    lookalike_snapshot = allowed + b"".join(
        f"{300 + index} 1 {identity}\n".encode()
        for index, identity in enumerate(lookalikes))
    assert transport.classify_process_snapshot(
        lookalike_snapshot, 100)["exact_identity_conflicts"] == []

    # Unrelated lexical collisions are valid.  A collision matters only when
    # lexical identity is needed for a verified ancestor (denied identities
    # already fail by exact raw or lexical matching).
    unrelated_collision = allowed + snapshot(
        (400, 1, "/one/benign-tool"), (401, 1, "/two/benign-tool"))
    assert transport.classify_process_snapshot(
        unrelated_collision, 100)["exact_identity_conflicts"] == []
    ancestor_collision = snapshot(
        (1, 0, "/sbin/launchd"), (90, 1, "/one/python3"),
        (91, 1, "/two/python3"))
    refused(ancestor_collision, 90,
            "transaction ancestor lexical identity collides")

    malformed = (
        b"", allowed[:-1],
        allowed + b"100 90 /usr/bin/python3\n",
        snapshot((1, 0, "launchd"), (100, 99, "python3")),
        snapshot((1, 0, "launchd"), (90, 100, "zsh"),
                 (100, 90, "python3")),
        snapshot((1, 0, "launchd"), (100, 1, "unknown-ancestor")),
        b"1 0 launchd\n100 python3\n",
        b"1 0 launchd\n100 1 python3\xff\n",
    )
    for fixture in malformed:
        refused(fixture, 100)


def single_session_contract() -> None:
    command = executor._transport_command()
    assert command[0] == "ssh" and command.count("ssh") == 1
    assert "BatchMode=yes" in command and "ConnectTimeout=10" in command
    source = (ROOT / "scripts/execute_backref_cost_attribution_v10.py").read_text()
    assert "scp" not in source
    assert "cleanup_remote" not in source and "finish_admission" not in source
    assert '"post_run_remote_cleanup_operations": 0' in source
    remote = (ROOT / "scripts/backref_cost_attribution_v10_transport.py").read_text()
    assert "shutil.rmtree(child)" in remote
    assert '"cleanup-footer"' in remote
    assert "_validate_child(home, root, child)" in remote


def main() -> int:
    static_guards()
    direct_child_contract()
    identity_only_process_contract()
    single_session_contract()
    print("PASS: attribution v10 treats raw comm as an opaque exact token, "
          "accepts slash-bearing v9 and slashless identities plus spaces, uses "
          "only a separately recorded lexical basename, keeps "
          "discovered PIDs out of signal APIs, and has one in-session cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
