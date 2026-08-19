#!/usr/bin/env python3
"""Frozen local driver for one specialization-factorization-v4 single-session transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import backref_cost_specialization_factorization_v4_admission as admission
import backref_cost_specialization_factorization_v4_archive as archive_protocol
import backref_cost_specialization_factorization_v4_transport as transport


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_specialization_factorization_v4_manifest.json"
PROTOCOL_PATH = ROOT / "doc" / "backref-cost-specialization-factorization-v4-protocol-20260820.md"
TRANSPORT_PATH = ROOT / "scripts" / "backref_cost_specialization_factorization_v4_transport.py"
PAYLOAD_GENERATOR_PATH = \
    ROOT / "scripts" / "backref_cost_specialization_factorization_v4_payload.py"
AUTHORIZATION_PATH = (ROOT / "evidence" / "backref-cost-specialization-factorization-v4-design" /
                      "phase1b-authorization.json")
REHEARSAL_HASH_INDEX_PATH = (
    ROOT / "evidence" / "backref-cost-specialization-factorization-v4-design" /
    "phase1b-rehearsal-hashes.json")
REHEARSAL_ROOT = (ROOT / "evidence" / "backref-cost-specialization-factorization-v4-design" /
                  "rehearsal")
EXPECTED_ENV = "EXPECTED_FREEZE_COMMIT"
AUTHORIZATION_SCHEMA = \
    "libwebp-backref-cost-specialization-factorization-v4-authorization-v1"
REHEARSAL_HASH_INDEX_SCHEMA = \
    "libwebp-backref-cost-specialization-factorization-v4-phase1b-hash-index-v1"
REMOTE_TRANSACTION_TIMEOUT_SECONDS = 1800
SILENT_OPERATOR_TIMEOUT_SECONDS = 900
STREAM_PROGRESS_TIMEOUT_SECONDS = 15
FOOTER_PROGRESS_TIMEOUT_SECONDS = 15
REPRESENTATIVE_PAYLOAD_BYTES = 2 * 1024 * 1024
MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES = 512 * 1024


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
    prefix = "evidence/backref-cost-specialization-factorization-v4-design/rehearsal/"
    return path.startswith(prefix) or path in {
        "evidence/backref-cost-specialization-factorization-v4-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-specialization-factorization-v4-design/phase1b-authorization.json",
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
            envelope.get("authorization_status") != "AUTHORIZED" or \
            envelope.get("phase_2_authority") != "FACTORIZATION_V4_DIAGNOSTIC_ONLY":
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
        "evidence/backref-cost-specialization-factorization-v4-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-specialization-factorization-v4-design/phase1b-authorization.json",
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
            not 0 < calibration.get("archive_bytes", 0) <= \
            transport.MAX_ARCHIVE_BYTES or \
            calibration.get("chunk_count", 0) < 1 or \
            calibration.get("transaction_elapsed_ns", 0) < 1 or \
            calibration.get("finite_margin_ratio", 0) < 1:
        raise RuntimeError("observed transport calibration is incomplete")
    if envelope.get("cleanup_footer_verified") is not True or \
            envelope.get("remote_cleanup_absence_proved") is not True or \
            envelope.get("integrity_footer_verified") is not True or \
            envelope.get("source_admission_verified") is not True or \
            envelope.get("archive_integrity_verified") is not True or \
            envelope.get("process_isolation_verified") is not True or \
            envelope.get("framed_response_cap_verified") is not True or \
            envelope.get("archive_cap_verified") is not True or \
            envelope.get("benchmark_lease_acquisition_attempted") is not False or \
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
    validate_rehearsal_hash_row_order(rows)
    observed = {}
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        path = REHEARSAL_ROOT / relative
        if not path.is_file() or path.is_symlink() or \
                path.stat().st_size != row.get("bytes") or \
                sha256(path) != row.get("sha256"):
            raise RuntimeError(f"Phase-1B rehearsal artifact mismatch: {relative}")
        observed[relative] = row["sha256"]
    actual = {path.relative_to(REHEARSAL_ROOT).as_posix()
              for path in REHEARSAL_ROOT.rglob("*") if path.is_file()}
    if actual != set(observed):
        raise RuntimeError("Phase-1B rehearsal hash index membership mismatch")
    return sha256(REHEARSAL_HASH_INDEX_PATH), observed


def validate_rehearsal_hash_row_order(rows: list[dict]) -> list[str]:
    """Require strict Unicode lexical path order before any hash authority."""
    paths: list[str] = []
    prior = ""
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str) or relative <= prior or \
                relative.startswith("/") or ".." in Path(relative).parts:
            raise RuntimeError("Phase-1B rehearsal hash index is unsafe/unordered")
        paths.append(relative)
        prior = relative
    return paths


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
            cleanup.get("source_commit"), cleanup.get("source_tree")),
    }
    for path in receipts:
        if envelope and envelope.get("rehearsal_receipt_hashes", {}).get(path) != \
                rehearsal_hashes.get(path):
            raise RuntimeError(f"rehearsal receipt digest mismatch: {path}")
    if cleanup.get("status") != "complete" or not cleanup.get("absence_proved"):
        raise RuntimeError("rehearsal cleanup footer is not complete")
    hashes = {
        "manifest": _git_file_sha256(
            source_commit, "scripts/backref_cost_specialization_factorization_v4_manifest.json"),
        "protocol": _git_file_sha256(
            source_commit, "doc/backref-cost-specialization-factorization-v4-protocol-20260820.md"),
        "schemas": _git_file_sha256(
            source_commit, "scripts/backref_cost_specialization_factorization_v4_schemas.json"),
        "transport": _git_file_sha256(
            source_commit, "scripts/backref_cost_specialization_factorization_v4_transport.py"),
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


def validate_compact_inventory(compact: dict, inspected: dict) -> None:
    """Require the declaration to commit to the exact local full inventory."""
    if not isinstance(compact, dict) or \
            compact.get("member_count") != inspected.get("member_count") or \
            compact.get("inventory_sha256") != transport.sha256_bytes(
                transport.canonical_json(inspected)):
        raise RuntimeError("local and remote archive inventories differ")


def lease_transfer_contract(mode: str, attempted: bool,
                            remote_receipt_available: bool,
                            fetch_receipt) -> tuple[dict, dict | None]:
    if not attempted:
        return ({"schema": "libwebp-backref-cost-specialization-factorization-v4-lease-transfer-v1",
                 "state": "not-attempted", "status": "not-attempted",
                 "acquisition_attempted": False, "receipt_required": False,
                 "receipt_requested": False, "mode": mode}, None)
    if not remote_receipt_available:
        return ({"schema": "libwebp-backref-cost-specialization-factorization-v4-lease-transfer-v1",
                 "state": "unavailable-after-attempt",
                 "status": "unavailable-after-attempt",
                 "acquisition_attempted": True, "receipt_required": True,
                 "receipt_requested": False, "mode": mode}, None)
    try:
        receipt = fetch_receipt()
    except Exception as error:
        return ({"schema": "libwebp-backref-cost-specialization-factorization-v4-lease-transfer-v1",
                 "state": "unavailable-after-attempt",
                 "status": "unavailable-after-attempt",
                 "acquisition_attempted": True, "receipt_required": True,
                 "receipt_requested": True, "mode": mode,
                 "reason": str(error)}, None)
    return ({"schema": "libwebp-backref-cost-specialization-factorization-v4-lease-transfer-v1",
             "state": "verified", "status": "verified",
             "acquisition_attempted": True, "receipt_required": True,
             "receipt_requested": True, "mode": mode}, receipt)


def _transport_command(mode: str) -> list[str]:
    # Rehearsal and run use the same single synchronous remote transaction.
    # Rehearsal remains workload-free and lease-free inside the frozen operator.
    # The 30-second connect admission is solely for overlay first-session setup;
    # it is separate from ServerAlive and transaction/progress deadlines.
    source = TRANSPORT_PATH.read_text(encoding="utf-8")
    payload_source = PAYLOAD_GENERATOR_PATH.read_text(encoding="utf-8")
    bootstrap = (
        "import sys,types;"
        "m=types.ModuleType('backref_cost_specialization_factorization_v4_payload');"
        f"exec({payload_source!r},m.__dict__);"
        "sys.modules[m.__name__]=m;"
        f"exec({source!r})")
    remote = f"exec python3 -c {shlex.quote(bootstrap)}"
    return ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o",
            "NumberOfPasswordPrompts=0", "-o", "ConnectionAttempts=1", "-o",
            "ConnectTimeout=30", "-o",
            "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3", "-o",
            "RequestTTY=no", HOST, remote]


def _metadata(mode: str, source_commit: str, source_tree: str,
              source_hashes: dict[str, str], bundle_sha: str,
              payload_bytes: int) -> dict:
    return {
        "protocol_version": transport.PROTOCOL_VERSION, "mode": mode,
        "source_commit": source_commit, "source_tree": source_tree,
        "source_hashes": source_hashes, "source_bundle_sha256": bundle_sha,
        "representative_payload_bytes": payload_bytes,
        "representative_payload_sha256":
            transport.deterministic_payload_sha256(payload_bytes),
        "maximum_expected_run_archive_bytes": MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES,
    }


def remote_pipeline(output: Path, mode: str) -> dict:
    validate_mode_environment(mode, os.environ)
    _, source_commit = validate_local_handoff(mode)
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    commit, tree, source_hashes = admission.local_identity(source_commit)
    bundle, bundle_sha = admission.create_source_bundle()
    payload_bytes = REPRESENTATIVE_PAYLOAD_BYTES if mode == "rehearse" else 0
    metadata = _metadata(
        mode, commit, tree, source_hashes, bundle_sha, payload_bytes)
    request_chunks = transport.iter_request(metadata, bundle, payload_bytes)
    output.mkdir(parents=True)
    protocol = output / "return-protocol"
    protocol.mkdir()
    raw_stdout = protocol / "framed-stdout.bin"
    raw_stderr = protocol / "transport-stderr.bin"
    observer = transport.OnlineResponseValidator(require_success=True)
    try:
        result = admission.pump_owned_full_duplex(
            _transport_command(mode), request_chunks,
            stdout_path=raw_stdout, stderr_path=raw_stderr,
            absolute_timeout=REMOTE_TRANSACTION_TIMEOUT_SECONDS,
            silent_operator_timeout=SILENT_OPERATOR_TIMEOUT_SECONDS,
            progress_timeout=STREAM_PROGRESS_TIMEOUT_SECONDS,
            footer_timeout=FOOTER_PROGRESS_TIMEOUT_SECONDS,
            stdout_observer=observer)
    except admission.OwnedTransportTimeout as error:
        write_json(output / "transfer-cleanup.json", {
            "schema": "libwebp-backref-cost-specialization-factorization-v4-transfer-cleanup-v1",
            "status": "refused", "mode": mode,
            "failure": "directly owned transport phase timed out",
            "timeout_phase": error.phase,
            "timeout_deadline_kind": error.deadline_kind,
            "direct_transport_child_timed_out": True,
            "framed_stdout_bytes": raw_stdout.stat().st_size,
            "framed_stdout_sha256": sha256(raw_stdout),
            "transport_stderr_bytes": raw_stderr.stat().st_size,
            "transport_stderr_sha256": sha256(raw_stderr),
            "cleanup_footer_verified": False,
            "remote_cleanup_state": "unknown-after-truncation",
            "post_run_remote_cleanup_operations": 0})
        raise RuntimeError(
            f"single remote transaction {error.phase} timed out; cleanup state "
            "is unknown and "
            "no second remote cleanup is permitted") from error
    with tempfile.TemporaryDirectory(prefix="specialization-factorization-v4-return-") as raw:
        temporary = Path(raw)
        try:
            parsed = transport.parse_response_file(
                raw_stdout, temporary / "evidence.tar.gz",
                require_success=True)
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
            archive_path = parsed["archive_path"]
            inspected = archive_protocol.inspect_archive(archive_path)
            declaration = parsed["declaration"]
            compact_inventory = declaration.get("inventory", {})
            validate_compact_inventory(compact_inventory, inspected)
            extracted = temporary / "extracted-evidence"
            archive_protocol.extract_archive(archive_path, extracted)
            for child in extracted.iterdir():
                child.rename(output / child.name)
            extracted.rmdir()
        except Exception:
            raise
    controls = parsed["controls"]
    write_json(protocol / "source-admission.json", controls["source-admission"])
    write_json(protocol / "operator-status.json", controls["operator-status"])
    write_json(protocol / "archive-build.json", controls["archive-build"])
    write_json(protocol / "lease-state.json", controls["lease-state"])
    write_json(protocol / "bulk-declaration.json", parsed["declaration"])
    write_json(protocol / "integrity-footer.json", parsed["integrity"])
    write_json(protocol / "cleanup-footer.json", parsed["cleanup"])
    calibration = {
        "status": "OBSERVED", "representative_payload_bytes": payload_bytes,
        "maximum_expected_run_archive_bytes": MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES,
        "finite_margin_ratio":
            payload_bytes / MAXIMUM_EXPECTED_RUN_ARCHIVE_BYTES
            if payload_bytes else None,
        "archive_cap_bytes": transport.MAX_ARCHIVE_BYTES,
        "archive_cap_margin_ratio":
            transport.MAX_ARCHIVE_BYTES / parsed["archive_bytes"],
        "archive_bytes": parsed["archive_bytes"],
        "archive_sha256": parsed["archive_sha256"],
        "chunk_bytes": parsed["declaration"]["chunk_bytes"],
        "chunk_count": parsed["declaration"]["chunk_count"],
        "transaction_elapsed_ns": result.elapsed_ns,
        "throughput_bytes_per_second":
            parsed["archive_bytes"] * 1_000_000_000 //
            max(1, result.elapsed_ns),
        "transaction_timeout_seconds": REMOTE_TRANSACTION_TIMEOUT_SECONDS,
        "silent_operator_timeout_seconds": SILENT_OPERATOR_TIMEOUT_SECONDS,
        "stream_progress_timeout_seconds": STREAM_PROGRESS_TIMEOUT_SECONDS,
        "footer_progress_timeout_seconds": FOOTER_PROGRESS_TIMEOUT_SECONDS,
    }
    receipt = {
        "schema": "libwebp-backref-cost-specialization-factorization-v4-transfer-cleanup-v1",
        "status": "complete", "mode": mode, "source_commit": commit,
        "source_tree": tree, "remote_host_alias": HOST,
        "single_noninteractive_remote_session_count": 1,
        "post_run_remote_cleanup_operations": 0,
        "framed_request_bytes": result.request_bytes,
        "framed_request_sha256": result.request_sha256,
        "stdin_half_closed_after_request": result.stdin_half_closed,
        "framed_stdout_bytes": result.stdout_bytes,
        "framed_stdout_sha256": result.stdout_sha256,
        "framed_response_cap_bytes": transport.MAX_RESPONSE_BYTES,
        "framed_response_cap_verified":
            result.stdout_bytes < transport.MAX_RESPONSE_BYTES,
        "transport_stderr_bytes": result.stderr_bytes,
        "transport_stderr_sha256": result.stderr_sha256,
        "transport_exit_code": result.returncode,
        "transport_online_persistence_hash_count_verified":
            result.stdout_bytes == raw_stdout.stat().st_size and
            result.stdout_sha256 == sha256(raw_stdout) and
            result.stderr_bytes == raw_stderr.stat().st_size and
            result.stderr_sha256 == sha256(raw_stderr),
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
        "encoder_workloads": 0 if mode == "rehearse" else 216,
        "profile_encoder_workloads": 0 if mode == "rehearse" else 180,
        "untimed_correctness_workloads": 0 if mode == "rehearse" else 24,
        "untimed_counter_workloads": 0 if mode == "rehearse" else 12,
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
