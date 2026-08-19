#!/usr/bin/env python3
"""Static, workload-free ownership guards for attribution v12."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import tempfile

import backref_cost_attribution_v12_admission as admission
import backref_cost_attribution_v12_transport as transport
import execute_backref_cost_attribution_v12 as executor
import run_backref_cost_attribution_v12_experiment as operator_module


ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE = (
    "scripts/backref_cost_attribution_v12_admission.py",
    "scripts/backref_cost_attribution_v12_archive.py",
    "scripts/backref_cost_attribution_v12_paths.py",
    "scripts/backref_cost_attribution_v12_transport.py",
    "scripts/execute_backref_cost_attribution_v12.py",
    "scripts/run_backref_cost_attribution_v12_experiment.py",
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
        ("scripts/backref_cost_attribution_v12_admission.py", "self.process.kill")]
    assert popen_sites == ["scripts/backref_cost_attribution_v12_admission.py"]


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


def refused(value: bytes, self_pid: int, code: str | None = None) -> dict:
    try:
        transport.classify_process_snapshot(value, self_pid)
    except transport.ProcessRefusal as error:
        diagnostic = error.diagnostic
        assert set(diagnostic) == {
            "schema", "failure_code", "pid", "ppid", "raw_comm",
            "lexical_basename", "is_ancestor", "is_conflict"}
        assert diagnostic["schema"].endswith("process-refusal-v1")
        if code is not None:
            assert diagnostic["failure_code"] == code
        return diagnostic
    else:
        raise AssertionError("unsafe process snapshot was accepted")


def identity_only_process_contract() -> None:
    # Arbitrary slashless, slash-bearing, path-like, and space-bearing ancestor
    # identities pass solely because the self-to-PID1 graph is complete.
    allowed = snapshot(
        (1, 0, "arbitrary pid one"),
        (80, 1, "relative/path-like token"),
        (90, 80, "/unlisted/location/unlisted shell with spaces"),
        (100, 90, "opaque-unlisted-transaction"),
        (110, 1, "Runner.Listener"),
        (111, 1, "unrelated-opaque-worker"),
        (112, 1, "unrelated comm with spaces"),
        (113, 1, "/another/path-like/nonancestor"),
    )
    # These are deliberately hostile argv/source strings.  They are not part
    # of the frozen pid/ppid/comm snapshot and therefore cannot affect identity.
    ignored_ancestor_argv_and_source = (
        "python3 -c 'backref_cost_attribution_v12_experiment_runner "
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
        "pid": 1, "ppid": 0, "raw_comm": "arbitrary pid one",
        "lexical_basename": "arbitrary pid one",
        "raw_comm_identity_kind": "opaque-process-table-string",
        "lexical_basename_identity_kind":
            "final-slash-component-without-filesystem-access",
    }
    assert "no positive identity allowlist" in \
        observed["ancestor_identity_policy"]
    assert observed["exact_identity_conflicts"] == []
    assert "Runner.Listener" not in transport.DENIED_RAW_COMM_IDENTITIES
    assert not hasattr(transport, "EXPECTED_TRANSPORT_ANCESTOR_RAW_COMM_IDENTITIES")
    assert not hasattr(transport,
                       "EXPECTED_TRANSPORT_ANCESTOR_LEXICAL_BASENAMES")

    slashless = snapshot(
        (1, 0, "any-init"), (80, 1, "any-parent"),
        (90, 80, "any-shell"), (100, 90, "any-interpreter"))
    assert transport.classify_process_snapshot(
        slashless, 100)["verified_ancestor_chain"][0]["raw_comm"] == \
        "any-interpreter"

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
        "backref_cost_attribution_v11_experiment_runner",
        "backref_cost_attribution_v12_experiment_runner",
        "backref_cost_attribution_v9_experiment_runner",
        "metal_benchmark", "nvidia-smi", "/usr/local/bin/nvidia-smi",
        "Runner.Worker", "/opt/runner/Runner.Worker",
    )
    for index, identity in enumerate(exact_conflicts, start=200):
        fixture = allowed + f"{index} 1 {identity}\n".encode()
        diagnostic = refused(fixture, 100, "exact-denied-process-identity")
        assert diagnostic == {
            "schema":
                "libwebp-backref-cost-attribution-v12-process-refusal-v1",
            "failure_code": "exact-denied-process-identity",
            "pid": index, "ppid": 1, "raw_comm": identity,
            "lexical_basename": identity.rsplit("/", 1)[-1],
            "is_ancestor": False, "is_conflict": True}

    denied_ancestor = snapshot(
        (1, 0, "unlisted-init"), (90, 1, "Runner.Worker"),
        (100, 90, "unlisted-self"))
    diagnostic = refused(
        denied_ancestor, 100, "exact-denied-process-identity")
    assert diagnostic["pid"] == 90 and diagnostic["ppid"] == 1
    assert diagnostic["raw_comm"] == "Runner.Worker"
    assert diagnostic["lexical_basename"] == "Runner.Worker"
    assert diagnostic["is_ancestor"] is True
    assert diagnostic["is_conflict"] is True

    lookalikes = (
        "prefix_backref_cost_attribution_v11_experiment_runner",
        "prefix_backref_cost_attribution_v12_experiment_runner",
        "backref_cost_attribution_v12_experiment_runner_suffix",
        "metal_benchmark-helper", "xnvidia-smi", "Runner.Worker.backup",
        "cuda-helper", "/tmp/prefix_nvidia-smi", "/tmp/Runner.Worker.suffix",
    )
    lookalike_snapshot = allowed + b"".join(
        f"{300 + index} 1 {identity}\n".encode()
        for index, identity in enumerate(lookalikes))
    assert transport.classify_process_snapshot(
        lookalike_snapshot, 100)["exact_identity_conflicts"] == []

    # Benign lexical collisions are valid because no positive basename match
    # is used for ancestor admission.
    unrelated_collision = allowed + snapshot(
        (400, 1, "/one/benign-tool"), (401, 1, "/two/benign-tool"))
    assert transport.classify_process_snapshot(
        unrelated_collision, 100)["exact_identity_conflicts"] == []
    ancestor_collision = snapshot(
        (1, 0, "anything"), (90, 1, "/one/benign-tool"),
        (91, 1, "/two/benign-tool"), (100, 90, "self"))
    assert transport.classify_process_snapshot(
        ancestor_collision, 100)["verified_ancestor_chain"][1][
            "lexical_basename"] == "benign-tool"

    malformed = (
        (b"", "snapshot-empty-or-truncated"),
        (allowed[:-1], "snapshot-empty-or-truncated"),
        (allowed + b"100 90 duplicate\n", "row-duplicate-pid"),
        (snapshot((1, 0, "init"), (100, 99, "self")),
         "ancestor-parent-missing"),
        (snapshot((1, 0, "init"), (90, 100, "parent"),
                  (100, 90, "self")), "ancestor-cycle"),
        (snapshot((1, 0, "init"), (100, 0, "self")),
         "non-pid1-ppid0"),
        (snapshot((1, 0, "init"), (90, 90, "self-parent"),
                  (100, 90, "self")), "row-self-parent"),
        (snapshot((1, 0, "init"), (100, 1, "trailing/")),
         "row-invalid-opaque-identity"),
        (b"1 0 init\n100 self\n", "row-malformed"),
        (b"1 0 init\n100 1 self\xff\n", "snapshot-not-utf8"),
        (snapshot((1, 0, "init"),
                  (100, 1, "x" * (transport.MAX_PROCESS_IDENTITY_BYTES + 1))),
         "row-invalid-opaque-identity"),
    )
    for fixture, code in malformed:
        diagnostic = refused(fixture, 100, code)
        assert set(diagnostic).isdisjoint(
            {"argv", "environment", "source", "command", "path"})


def refusal_frame_contract() -> None:
    diagnostic = refused(
        snapshot((1, 0, "unlisted-init"),
                 (100, 1, "/opt/runner/Runner.Worker")),
        100, "exact-denied-process-identity")
    digest = transport.sha256_bytes(transport.canonical_json(diagnostic))

    def response(process_digest: str) -> bytes:
        frames = [
            ("source-admission", transport.canonical_json(
                {"status": "unavailable"}), {"sequence": 0}),
            ("operator-status", transport.canonical_json({
                "status": "unavailable",
                "benchmark_lease_acquisition_attempted": False}),
             {"sequence": 1}),
            ("archive-build", transport.canonical_json(
                {"status": "not-attempted"}), {"sequence": 2}),
            ("lease-state", transport.canonical_json(
                {"state": "not-attempted"}), {"sequence": 3}),
            ("integrity-footer", transport.canonical_json({
                "status": "refused", "archive_sha256": None,
                "process_refusal": diagnostic,
                "process_refusal_sha256": process_digest}), {"sequence": 4}),
            ("cleanup-footer", transport.canonical_json({
                "status": "complete", "removed_exact_validated_child": True,
                "absence_proved": True}), {"sequence": 5}),
        ]
        return transport.encode_stream(frames)

    parsed = transport.parse_response(response(digest), require_success=False)
    assert parsed["integrity"]["process_refusal"] == diagnostic
    assert parsed["integrity"]["process_refusal_sha256"] == digest
    try:
        transport.parse_response(response("0" * 64), require_success=False)
    except transport.FrameRefusal as error:
        assert str(error) == "process refusal diagnostic/hash is invalid"
    else:
        raise AssertionError("invalid process refusal hash was accepted")


def operator_refusal_control_contract() -> None:
    row = {"pid": 212, "ppid": 1, "raw_comm": "Runner.Worker",
           "lexical_basename": "Runner.Worker"}
    original = operator_module.operator

    def process_refusal(_mode: str, _output: Path) -> None:
        raise transport.ProcessRefusal(
            "exact-denied-process-identity", row=row,
            is_ancestor=False, is_conflict=True)

    with tempfile.TemporaryDirectory(prefix="attribution-v12-refusal-") as raw:
        output = Path(raw) / "evidence"
        operator_module.operator = process_refusal
        try:
            operator_module.controlled("rehearse", output)
        except RuntimeError:
            pass
        else:
            raise AssertionError("controlled process refusal unexpectedly passed")
        finally:
            operator_module.operator = original
        status = json.loads((output / "operator-status.json").read_text())
        diagnostic = status["process_refusal"]
        assert diagnostic["pid"] == 212 and diagnostic["ppid"] == 1
        assert diagnostic["raw_comm"] == "Runner.Worker"
        assert status["process_refusal_sha256"] == transport.sha256_bytes(
            transport.canonical_json(diagnostic))
        assert set(diagnostic).isdisjoint(
            {"argv", "environment", "source", "command", "path"})


def single_session_contract() -> None:
    command = executor._transport_command()
    assert command[0] == "ssh" and command.count("ssh") == 1
    assert "BatchMode=yes" in command and "ConnectTimeout=10" in command
    assert "ServerAliveInterval=15" in command
    assert "ServerAliveCountMax=3" in command
    source = (ROOT / "scripts/execute_backref_cost_attribution_v12.py").read_text()
    assert "scp" not in source
    assert "cleanup_remote" not in source and "finish_admission" not in source
    assert '"post_run_remote_cleanup_operations": 0' in source
    remote = (ROOT / "scripts/backref_cost_attribution_v12_transport.py").read_text()
    assert "shutil.rmtree(child)" in remote
    assert '"cleanup-footer"' in remote
    assert "_validate_child(home, root, child)" in remote
    assert "communicate(" not in source
    assert "pump_owned_full_duplex" in source


def main() -> int:
    static_guards()
    direct_child_contract()
    identity_only_process_contract()
    refusal_frame_contract()
    operator_refusal_control_contract()
    single_session_contract()
    print("PASS: attribution v12 proves arbitrary opaque ancestors structurally, "
          "rejects only exact denied identities with hashed identity-only "
          "diagnostics, keeps discovered PIDs out of signal APIs, and has one "
          "in-session cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
