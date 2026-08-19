#!/usr/bin/env python3
"""Frozen local driver for one attribution-v7 single-session transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import backref_cost_attribution_v7_admission as admission
import backref_cost_attribution_v7_archive as archive_protocol
import backref_cost_attribution_v7_transport as transport


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_attribution_v7_manifest.json"
PROTOCOL_PATH = ROOT / "doc" / "backref-cost-attribution-v7-protocol-20260819.md"
TRANSPORT_PATH = ROOT / "scripts" / "backref_cost_attribution_v7_transport.py"
AUTHORIZATION_PATH = (ROOT / "evidence" / "backref-cost-attribution-v7-design" /
                      "phase1b-authorization.json")
REHEARSAL_HASH_INDEX_PATH = (
    ROOT / "evidence" / "backref-cost-attribution-v7-design" /
    "phase1b-rehearsal-hashes.json")
REHEARSAL_ROOT = (ROOT / "evidence" / "backref-cost-attribution-v7-design" /
                  "rehearsal")
EXPECTED_ENV = "EXPECTED_FREEZE_COMMIT"
AUTHORIZATION_SCHEMA = \
    "libwebp-backref-cost-attribution-v7-authorization-v1"
REHEARSAL_HASH_INDEX_SCHEMA = \
    "libwebp-backref-cost-attribution-v7-phase1b-hash-index-v1"
REMOTE_TRANSACTION_TIMEOUT_SECONDS = 7200
REPRESENTATIVE_PAYLOAD_BYTES = 5 * 1024 * 1024
MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES = 4 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _git_file_sha256(commit: str, relative: str) -> str:
    return hashlib.sha256(
        admission.git_bytes("show", f"{commit}:{relative}")).hexdigest()


def _allowed_phase1b_path(path: str) -> bool:
    prefix = "evidence/backref-cost-attribution-v7-design/rehearsal/"
    return path.startswith(prefix) or path in {
        "evidence/backref-cost-attribution-v7-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-attribution-v7-design/phase1b-authorization.json",
    }


def validate_authority_values(*, envelope: dict | None, head_commit: str,
                              head_tree: str, parents: list[str],
                              source_tree: str,
                              diff_entries: list[tuple[str, str]],
                              source_hashes: dict[str, str],
                              hash_index_sha256: str,
                              receipt_identities: dict[str, tuple[str, str]]) -> str:
    """Pure fail-closed 1A/1B identity contract used by rejection fixtures."""
    if envelope is None or envelope.get("schema") != AUTHORIZATION_SCHEMA:
        raise RuntimeError("Phase-1B authorization envelope is missing or wrong")
    if not envelope.get("timed_execution_authorized") or \
            envelope.get("authorization_status") != "AUTHORIZED":
        raise RuntimeError("Phase-1B did not authorize timed execution")
    source_commit = envelope.get("source_commit")
    if len(parents) != 1 or parents[0] != source_commit:
        raise RuntimeError("Phase-1B parent is not the recorded Phase-1A commit")
    if len(head_commit) != 40 or len(head_tree) != 40:
        raise RuntimeError("Phase-1B HEAD commit/tree identity is malformed")
    if envelope.get("source_tree") != source_tree:
        raise RuntimeError("authorization source tree mismatch")
    if not diff_entries:
        raise RuntimeError("Phase-1B evidence diff is empty")
    for status, path in diff_entries:
        if status != "A" or not _allowed_phase1b_path(path):
            raise RuntimeError(
                f"Phase-1B modified a frozen or unapproved path: {status} {path}")
    required_added = {
        "evidence/backref-cost-attribution-v7-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-attribution-v7-design/phase1b-authorization.json",
    }
    if not required_added.issubset({path for _, path in diff_entries}):
        raise RuntimeError("Phase-1B evidence index or envelope is absent")
    expected_hashes = {
        "manifest": envelope.get("manifest_sha256"),
        "protocol": envelope.get("protocol_sha256"),
        "schemas": envelope.get("schema_catalog_sha256"),
        "transport": envelope.get("transport_source_sha256"),
    }
    if source_hashes != expected_hashes or any(
            not isinstance(value, str) or len(value) != 64
            for value in expected_hashes.values()):
        raise RuntimeError("frozen source hash mismatch")
    if envelope.get("rehearsal_hash_index_sha256") != hash_index_sha256:
        raise RuntimeError("Phase-1B rehearsal hash-index mismatch")
    declared = envelope.get("rehearsal_receipt_hashes")
    if not isinstance(declared, dict) or not declared:
        raise RuntimeError("authorization lacks rehearsal receipt hashes")
    for path, (receipt_commit, receipt_tree) in receipt_identities.items():
        if path not in declared or receipt_commit != source_commit or \
                receipt_tree != source_tree:
            raise RuntimeError(f"stale or wrong-tree rehearsal receipt: {path}")
    calibration = envelope.get("observed_transport_calibration")
    if not isinstance(calibration, dict) or \
            calibration.get("representative_payload_bytes", 0) < \
            MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES or \
            calibration.get("archive_bytes", 0) < \
            MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES or \
            calibration.get("chunk_count", 0) < 1 or \
            calibration.get("transaction_elapsed_ns", 0) < 1 or \
            calibration.get("finite_margin_ratio", 0) < 1:
        raise RuntimeError("observed transport calibration is incomplete")
    if envelope.get("cleanup_footer_verified") is not True or \
            envelope.get("post_run_remote_cleanup_operations") != 0:
        raise RuntimeError("single-session cleanup authority is absent")
    return source_commit


def verify_rehearsal_hash_index() -> tuple[str, dict[str, str]]:
    if not REHEARSAL_HASH_INDEX_PATH.is_file() or not REHEARSAL_ROOT.is_dir():
        raise RuntimeError("Phase-1B rehearsal evidence or hash index is absent")
    value = json.loads(REHEARSAL_HASH_INDEX_PATH.read_text(encoding="utf-8"))
    if value.get("schema") != REHEARSAL_HASH_INDEX_SCHEMA:
        raise RuntimeError("Phase-1B rehearsal hash-index schema mismatch")
    rows = value.get("artifacts")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Phase-1B rehearsal hash index is empty")
    observed = {}
    prior = ""
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str) or relative <= prior or \
                relative.startswith("/") or ".." in Path(relative).parts:
            raise RuntimeError("Phase-1B rehearsal hash index is unsafe/unordered")
        path = REHEARSAL_ROOT / relative
        if not path.is_file() or path.is_symlink() or \
                path.stat().st_size != row.get("bytes") or \
                sha256(path) != row.get("sha256"):
            raise RuntimeError(f"Phase-1B rehearsal artifact mismatch: {relative}")
        observed[relative] = row["sha256"]
        prior = relative
    actual = {path.relative_to(REHEARSAL_ROOT).as_posix()
              for path in REHEARSAL_ROOT.rglob("*") if path.is_file()}
    if actual != set(observed):
        raise RuntimeError("Phase-1B rehearsal hash index membership mismatch")
    return sha256(REHEARSAL_HASH_INDEX_PATH), observed


def validate_authorized_handoff(head: str) -> str:
    envelope = (json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
                if AUTHORIZATION_PATH.is_file() else None)
    parents = admission.git("rev-list", "--parents", "-n", "1", head).split()[1:]
    source_commit = envelope.get("source_commit") if envelope else head
    source_tree = admission.git("rev-parse", f"{source_commit}^{{tree}}")
    head_tree = admission.git("rev-parse", "HEAD^{tree}")
    lines = admission.git("diff", "--name-status", source_commit, head).splitlines()
    diff_entries = [(line.split("\t", 1)[0], line.split("\t", 1)[1])
                    for line in lines if "\t" in line]
    index_sha, rehearsal_hashes = verify_rehearsal_hash_index()
    source_control = json.loads((REHEARSAL_ROOT / "return-protocol" /
                                 "source-admission.json").read_text())
    transfer = json.loads((REHEARSAL_ROOT / "transfer-cleanup.json").read_text())
    rehearsal = json.loads((REHEARSAL_ROOT / "rehearsal.json").read_text())
    cleanup = json.loads((REHEARSAL_ROOT / "return-protocol" /
                          "cleanup-footer.json").read_text())
    receipts = {
        "transfer-cleanup.json": (transfer.get("source_commit"),
                                   transfer.get("source_tree")),
        "rehearsal.json": (rehearsal.get("source_commit"),
                            rehearsal.get("source_tree")),
        "return-protocol/source-admission.json": (
            source_control.get("source_commit"), source_control.get("source_tree")),
        "return-protocol/cleanup-footer.json": (
            transfer.get("source_commit"), transfer.get("source_tree")),
    }
    for path in receipts:
        if envelope and envelope.get("rehearsal_receipt_hashes", {}).get(path) != \
                rehearsal_hashes.get(path):
            raise RuntimeError(f"rehearsal receipt digest mismatch: {path}")
    if cleanup.get("status") != "complete" or not cleanup.get("absence_proved"):
        raise RuntimeError("rehearsal cleanup footer is not complete")
    hashes = {
        "manifest": _git_file_sha256(
            source_commit, "scripts/backref_cost_attribution_v7_manifest.json"),
        "protocol": _git_file_sha256(
            source_commit, "doc/backref-cost-attribution-v7-protocol-20260819.md"),
        "schemas": _git_file_sha256(
            source_commit, "scripts/backref_cost_attribution_v7_schemas.json"),
        "transport": _git_file_sha256(
            source_commit, "scripts/backref_cost_attribution_v7_transport.py"),
    }
    return validate_authority_values(
        envelope=envelope, head_commit=head, head_tree=head_tree,
        parents=parents, source_tree=source_tree, diff_entries=diff_entries,
        source_hashes=hashes, hash_index_sha256=index_sha,
        receipt_identities=receipts)


def validate_local_handoff(mode: str) -> tuple[str, str]:
    expected = os.environ.get(EXPECTED_ENV)
    if not expected:
        raise RuntimeError(f"{EXPECTED_ENV} is required")
    head = admission.git("rev-parse", "HEAD")
    if admission.git("status", "--porcelain"):
        raise RuntimeError("handoff validation requires a clean worktree")
    if head != expected:
        raise RuntimeError("HEAD is not EXPECTED_FREEZE_COMMIT")
    if mode == "run" or (mode == "validate" and AUTHORIZATION_PATH.exists()):
        source_commit = validate_authorized_handoff(head)
    else:
        if AUTHORIZATION_PATH.exists():
            raise RuntimeError("rehearsal is allowed only at exact Phase-1A")
        source_commit = head
    return head, source_commit


def validate_run_environment(environment: dict[str, str]) -> None:
    if environment.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")


def validate_untimed_environment(mode: str,
                                 environment: dict[str, str]) -> None:
    if mode not in ("validate", "rehearse"):
        raise RuntimeError("unknown untimed mode")
    if "WEBP_BENCHMARK_SESSION" in environment:
        raise RuntimeError(f"{mode} requires WEBP_BENCHMARK_SESSION unset")


def validate_mode_environment(mode: str, environment: dict[str, str]) -> None:
    if mode == "run":
        validate_run_environment(environment)
    elif mode in ("validate", "rehearse"):
        validate_untimed_environment(mode, environment)
    else:
        raise RuntimeError("unknown execution mode")


def validate_admission_receipt(record: dict,
                               local_bundle_sha256: str) -> None:
    if not isinstance(record, dict) or \
            record.get("schema") != admission.SOURCE_RECEIPT_SCHEMA or \
            record.get("receipt_version") != admission.SOURCE_RECEIPT_VERSION:
        raise RuntimeError("unexpected source admission receipt version")
    nested = record.get("admission")
    if not isinstance(record.get("source_bundle_sha256"), str) or \
            not isinstance(nested, dict) or \
            not isinstance(nested.get("bundle_sha256"), str) or \
            record["source_bundle_sha256"] != nested["bundle_sha256"] or \
            record["source_bundle_sha256"] != local_bundle_sha256:
        raise RuntimeError("source admission bundle hashes differ")


def lease_transfer_contract(mode: str, attempted: bool,
                            remote_receipt_available: bool,
                            fetch_receipt) -> tuple[dict, dict | None]:
    if not attempted:
        return ({"schema": "libwebp-backref-cost-attribution-v7-lease-transfer-v1",
                 "state": "not-attempted", "status": "not-attempted",
                 "acquisition_attempted": False, "receipt_required": False,
                 "receipt_requested": False, "mode": mode}, None)
    if not remote_receipt_available:
        return ({"schema": "libwebp-backref-cost-attribution-v7-lease-transfer-v1",
                 "state": "unavailable-after-attempt",
                 "status": "unavailable-after-attempt",
                 "acquisition_attempted": True, "receipt_required": True,
                 "receipt_requested": False, "mode": mode}, None)
    try:
        receipt = fetch_receipt()
    except Exception as error:
        return ({"schema": "libwebp-backref-cost-attribution-v7-lease-transfer-v1",
                 "state": "unavailable-after-attempt",
                 "status": "unavailable-after-attempt",
                 "acquisition_attempted": True, "receipt_required": True,
                 "receipt_requested": True, "mode": mode,
                 "reason": str(error)}, None)
    return ({"schema": "libwebp-backref-cost-attribution-v7-lease-transfer-v1",
             "state": "verified", "status": "verified",
             "acquisition_attempted": True, "receipt_required": True,
             "receipt_requested": True, "mode": mode}, receipt)


def _transport_command() -> list[str]:
    source = TRANSPORT_PATH.read_text(encoding="utf-8")
    remote = f"exec python3 -c {shlex.quote(source)}"
    return ["ssh", "-T", "-o", "BatchMode=yes", "-o",
            "NumberOfPasswordPrompts=0", "-o", "ConnectTimeout=10", "-o",
            "RequestTTY=no", HOST, remote]


def _metadata(mode: str, source_commit: str, source_tree: str,
              source_hashes: dict[str, str], bundle_sha: str,
              payload: bytes) -> dict:
    return {
        "protocol_version": transport.PROTOCOL_VERSION, "mode": mode,
        "source_commit": source_commit, "source_tree": source_tree,
        "source_hashes": source_hashes, "source_bundle_sha256": bundle_sha,
        "representative_payload_bytes": len(payload),
        "representative_payload_sha256": admission.sha256_bytes(payload),
        "maximum_expected_run_archive_bytes": MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES,
    }


def remote_pipeline(output: Path, mode: str) -> dict:
    validate_mode_environment(mode, os.environ)
    _, source_commit = validate_local_handoff(mode)
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    commit, tree, source_hashes = admission.local_identity(source_commit)
    bundle, bundle_sha = admission.create_source_bundle()
    payload = (transport.deterministic_payload(REPRESENTATIVE_PAYLOAD_BYTES)
               if mode == "rehearse" else b"")
    request = transport.request_bytes(
        _metadata(mode, commit, tree, source_hashes, bundle_sha, payload),
        bundle, payload)
    started = time.monotonic_ns()
    try:
        result = admission.run(
            _transport_command(), input_bytes=request,
            timeout=REMOTE_TRANSACTION_TIMEOUT_SECONDS, check=False)
        elapsed_ns = time.monotonic_ns() - started
    except subprocess.TimeoutExpired as error:
        output.mkdir(parents=True)
        protocol = output / "return-protocol"
        protocol.mkdir()
        partial_stdout = error.stdout or b""
        partial_stderr = error.stderr or b""
        (protocol / "framed-stdout.bin").write_bytes(partial_stdout)
        (protocol / "transport-stderr.bin").write_bytes(partial_stderr)
        write_json(output / "transfer-cleanup.json", {
            "schema": "libwebp-backref-cost-attribution-v7-transfer-cleanup-v1",
            "status": "refused", "mode": mode,
            "failure": "directly owned transport timed out",
            "direct_transport_child_timed_out": True,
            "cleanup_footer_verified": False,
            "remote_cleanup_state": "unknown-after-truncation",
            "post_run_remote_cleanup_operations": 0})
        raise RuntimeError(
            "single remote transaction timed out; cleanup state is unknown and "
            "no second remote cleanup is permitted") from error
    with tempfile.TemporaryDirectory(prefix="attribution-v7-return-") as raw:
        temporary = Path(raw)
        (temporary / "framed-stdout.bin").write_bytes(result.stdout)
        (temporary / "transport-stderr.bin").write_bytes(result.stderr)
        try:
            parsed = transport.parse_response(result.stdout, require_success=True)
            source = parsed["controls"]["source-admission"]
            validate_admission_receipt(source, bundle_sha)
            if source.get("source_commit") != commit or source.get(
                    "source_tree") != tree:
                raise RuntimeError("remote source receipt identity mismatch")
            operator = parsed["controls"]["operator-status"]
            attempted = operator.get("benchmark_lease_acquisition_attempted")
            lease = parsed["controls"]["lease-state"]
            expected_lease = "verified" if mode == "run" else "not-attempted"
            if attempted != (mode == "run") or lease.get("state") != expected_lease:
                raise RuntimeError("mode/lease state mismatch")
            archive_path = temporary / "evidence.tar.gz"
            archive_path.write_bytes(parsed["archive"])
            inspected = archive_protocol.inspect_archive(archive_path)
            declaration = parsed["declaration"]
            if inspected != declaration.get("inventory"):
                raise RuntimeError("local and remote archive inventories differ")
            extracted = temporary / "extracted-evidence"
            archive_protocol.extract_archive(archive_path, extracted)
            extracted.rename(output)
        except Exception:
            output.mkdir(parents=True, exist_ok=True)
            protocol = output / "return-protocol"
            protocol.mkdir(exist_ok=True)
            shutil.copy2(temporary / "framed-stdout.bin",
                         protocol / "framed-stdout.bin")
            shutil.copy2(temporary / "transport-stderr.bin",
                         protocol / "transport-stderr.bin")
            raise
        protocol = output / "return-protocol"
        protocol.mkdir()
        shutil.copy2(temporary / "framed-stdout.bin",
                     protocol / "framed-stdout.bin")
        shutil.copy2(temporary / "transport-stderr.bin",
                     protocol / "transport-stderr.bin")
    controls = parsed["controls"]
    write_json(protocol / "source-admission.json", controls["source-admission"])
    write_json(protocol / "operator-status.json", controls["operator-status"])
    write_json(protocol / "archive-build.json", controls["archive-build"])
    write_json(protocol / "lease-state.json", controls["lease-state"])
    write_json(protocol / "bulk-declaration.json", parsed["declaration"])
    write_json(protocol / "integrity-footer.json", parsed["integrity"])
    write_json(protocol / "cleanup-footer.json", parsed["cleanup"])
    calibration = {
        "status": "OBSERVED", "representative_payload_bytes": len(payload),
        "maximum_expected_run_archive_bytes": MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES,
        "finite_margin_ratio": len(payload) / MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES
        if payload else None,
        "archive_bytes": len(parsed["archive"]),
        "archive_sha256": admission.sha256_bytes(parsed["archive"]),
        "chunk_bytes": parsed["declaration"]["chunk_bytes"],
        "chunk_count": parsed["declaration"]["chunk_count"],
        "transaction_elapsed_ns": elapsed_ns,
        "throughput_bytes_per_second":
            len(parsed["archive"]) * 1_000_000_000 // max(1, elapsed_ns),
        "transaction_timeout_seconds": REMOTE_TRANSACTION_TIMEOUT_SECONDS,
    }
    receipt = {
        "schema": "libwebp-backref-cost-attribution-v7-transfer-cleanup-v1",
        "status": "complete", "mode": mode, "source_commit": commit,
        "source_tree": tree, "remote_host_alias": HOST,
        "single_noninteractive_remote_session_count": 1,
        "post_run_remote_cleanup_operations": 0,
        "framed_request_sha256": admission.sha256_bytes(request),
        "framed_stdout_sha256": sha256(protocol / "framed-stdout.bin"),
        "transport_stderr_sha256": sha256(protocol / "transport-stderr.bin"),
        "transport_exit_code": result.returncode,
        "operator_status": controls["operator-status"].get("status"),
        "benchmark_lease_acquisition_attempted":
            controls["operator-status"].get(
                "benchmark_lease_acquisition_attempted"),
        "lease_transfer_state": controls["lease-state"].get("state"),
        "cleanup_footer_verified": True,
        "remote_cleanup_complete": True,
        "remote_cleanup_absence_proved": True,
        "remote_cleanup_proof": parsed["cleanup"],
        "transport_calibration": calibration,
        "timed_binary_invoked": mode == "run",
        "encoder_workloads": 0 if mode == "rehearse" else 120,
        "profiler_workloads": 0,
        "installed_runner_directory_touched": False,
    }
    write_json(output / "transfer-cleanup.json", receipt)
    archive_protocol.write_returned_index(output, ["transfer-cleanup.json"])
    if result.returncode != 0:
        raise RuntimeError("remote session returned nonzero after complete frames")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    rehearse = sub.add_parser("rehearse")
    rehearse.add_argument("output", type=Path)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        validate_untimed_environment("validate", os.environ)
        head, commit = validate_local_handoff("validate")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        print(json.dumps({
            "status": "PASS", "mode": "validate", "source_commit": commit,
            "freeze_commit": head, "manifest_sha256": sha256(MANIFEST_PATH),
            "schema_catalog_sha256": sha256(ROOT / manifest["schemas"]["catalog"]),
            "benchmark_lease_acquisition_attempted": False,
            "timed_binary_invoked": False}, sort_keys=True))
        return 0
    result = remote_pipeline(args.output, args.command)
    print(json.dumps({"status": result["status"], "output": str(args.output)},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, archive_protocol.ArchiveRefusal,
            transport.FrameRefusal) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
