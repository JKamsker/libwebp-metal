#!/usr/bin/env python3
"""Disjoint validation, rehearsal, and frozen interval-specialization execution."""

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

import backref_cost_attribution_v6_admission as admission
import backref_cost_attribution_v6_archive as archive_protocol


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_attribution_v6_manifest.json"
PROTOCOL_PATH = ROOT / "doc" / "backref-cost-attribution-v6-protocol-20260819.md"
AUTHORIZATION_PATH = (ROOT / "evidence" / "backref-cost-attribution-v6-design" /
                      "phase1b-authorization.json")
REHEARSAL_HASH_INDEX_PATH = (
    ROOT / "evidence" / "backref-cost-attribution-v6-design" /
    "phase1b-rehearsal-hashes.json")
REHEARSAL_ROOT = (ROOT / "evidence" / "backref-cost-attribution-v6-design" /
                  "rehearsal")
EXPECTED_ENV = "EXPECTED_FREEZE_COMMIT"
AUTHORIZATION_SCHEMA = \
    "libwebp-backref-cost-attribution-v6-authorization-v1"
REHEARSAL_HASH_INDEX_SCHEMA = \
    "libwebp-backref-cost-attribution-v6-phase1b-hash-index-v1"
CONTROL_TIMEOUT_SECONDS = 20
# Frozen after the Phase-1 representative transfer. See the manifest's
# transport_timeout_derivation; this is deliberately not a generic default.
TRANSFER_TIMEOUT_SECONDS = 60
BULK_CHUNK_BYTES = 512 * 1024
BULK_CHUNK_TIMEOUT_SECONDS = 20
ARCHIVE_BUILD_TIMEOUT_SECONDS = 180
MAXIMUM_TRANSFER_ARCHIVE_BYTES = 8 * 1024 * 1024


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def serializable_admission(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "temporary"}


def _git_file_sha256(commit: str, relative: str) -> str:
    return hashlib.sha256(
        admission.git_bytes("show", f"{commit}:{relative}")).hexdigest()


def _allowed_phase1b_path(path: str) -> bool:
    prefix = "evidence/backref-cost-attribution-v6-design/rehearsal/"
    return path.startswith(prefix) or path in {
        "evidence/backref-cost-attribution-v6-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-attribution-v6-design/phase1b-authorization.json",
    }


def validate_authority_values(*, envelope: dict | None, head_commit: str,
                              head_tree: str, parents: list[str],
                              source_tree: str,
                              diff_entries: list[tuple[str, str]],
                              source_hashes: dict[str, str],
                              hash_index_sha256: str,
                              receipt_identities: dict[str, tuple[str, str]]) -> str:
    """Pure fail-closed 1A/1B identity contract used by rejection fixtures."""
    if envelope is None:
        raise RuntimeError("Phase-1B authorization envelope is missing")
    if envelope.get("schema") != AUTHORIZATION_SCHEMA:
        raise RuntimeError("authorization envelope schema mismatch")
    if not envelope.get("timed_execution_authorized"):
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
        "evidence/backref-cost-attribution-v6-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-attribution-v6-design/phase1b-authorization.json",
    }
    if not required_added.issubset({path for _, path in diff_entries}):
        raise RuntimeError("Phase-1B evidence index or envelope is absent")
    expected_source_hashes = {
        "manifest": envelope.get("manifest_sha256"),
        "protocol": envelope.get("protocol_sha256"),
        "schemas": envelope.get("schema_catalog_sha256"),
    }
    if source_hashes != expected_source_hashes or any(
            not isinstance(value, str) or len(value) != 64
            for value in expected_source_hashes.values()):
        raise RuntimeError("frozen manifest/protocol/schema hash mismatch")
    if envelope.get("rehearsal_hash_index_sha256") != hash_index_sha256:
        raise RuntimeError("Phase-1B rehearsal hash-index mismatch")
    declared_receipts = envelope.get("rehearsal_receipt_hashes")
    if not isinstance(declared_receipts, dict) or not declared_receipts:
        raise RuntimeError("authorization lacks rehearsal receipt hashes")
    for path, (receipt_commit, receipt_tree) in receipt_identities.items():
        if path not in declared_receipts or receipt_commit != source_commit or \
                receipt_tree != source_tree:
            raise RuntimeError(f"stale or wrong-tree rehearsal receipt: {path}")
    calibration = envelope.get("observed_transport_calibration")
    if not isinstance(calibration, dict) or \
            calibration.get("archive_bytes", 0) < 4 * 1024 * 1024 or \
            calibration.get("chunk_count", 0) < 1 or \
            calibration.get("elapsed_ns", 0) < 1:
        raise RuntimeError("observed transport calibration is incomplete")
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
    observed: dict[str, str] = {}
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
    receipts = {
        "transfer-cleanup.json": json.loads(
            (REHEARSAL_ROOT / "transfer-cleanup.json").read_text()),
        "rehearsal.json": json.loads(
            (REHEARSAL_ROOT / "rehearsal.json").read_text()),
        "return-protocol/source-admission-receipt.json": json.loads(
            (REHEARSAL_ROOT / "return-protocol" /
             "source-admission-receipt.json").read_text()),
        "return-protocol/operator-status.json": json.loads(
            (REHEARSAL_ROOT / "return-protocol" /
             "operator-status.json").read_text()),
    }
    identities = {}
    for path, receipt in receipts.items():
        commit = receipt.get("source_commit")
        tree = receipt.get("source_tree")
        if path == "transfer-cleanup.json":
            tree = receipt.get("admission", {}).get("source_tree")
        identities[path] = (commit, tree)
        if envelope and envelope.get("rehearsal_receipt_hashes", {}).get(path) != \
                rehearsal_hashes.get(path):
            raise RuntimeError(f"rehearsal receipt digest mismatch: {path}")
    source_hashes = {
        "manifest": _git_file_sha256(
            source_commit, "scripts/backref_cost_attribution_v6_manifest.json"),
        "protocol": _git_file_sha256(
            source_commit, "doc/backref-cost-attribution-v6-protocol-20260819.md"),
        "schemas": _git_file_sha256(
            source_commit, "scripts/backref_cost_attribution_v6_schemas.json"),
    }
    return validate_authority_values(
        envelope=envelope, head_commit=head, head_tree=head_tree,
        parents=parents, source_tree=source_tree, diff_entries=diff_entries,
        source_hashes=source_hashes, hash_index_sha256=index_sha,
        receipt_identities=identities)


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
    """The run-only session admission; it has no rehearsal dependency."""
    if environment.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")


def validate_untimed_environment(mode: str,
                                 environment: dict[str, str]) -> None:
    """The validate/rehearse guard; exact absence, including empty values."""
    if mode not in ("validate", "rehearse"):
        raise RuntimeError("unknown untimed execution mode")
    if "WEBP_BENCHMARK_SESSION" in environment:
        raise RuntimeError(
            f"{mode} requires WEBP_BENCHMARK_SESSION to be unset")


def validate_mode_environment(mode: str, environment: dict[str, str]) -> None:
    """Truth-table entry point used by contract tests."""
    session_present = "WEBP_BENCHMARK_SESSION" in environment
    if mode == "run":
        validate_run_environment(environment)
    elif mode in ("validate", "rehearse"):
        validate_untimed_environment(mode, environment)
    else:
        raise RuntimeError("unknown execution mode")


def validate_admission_receipt(record: dict,
                               local_bundle_sha256: str) -> None:
    """Validate the versioned source receipt and its two authoritative hashes."""
    if not isinstance(record, dict):
        raise RuntimeError("source admission receipt must be an object")
    if record.get("schema") != admission.SOURCE_RECEIPT_SCHEMA or \
            record.get("receipt_version") != admission.SOURCE_RECEIPT_VERSION:
        raise RuntimeError("unexpected source admission receipt version")
    if "source_bundle_sha256" not in record or not isinstance(
            record["source_bundle_sha256"], str):
        raise RuntimeError(
            "source_bundle_sha256 must exist and be a string")
    nested = record.get("admission")
    if not isinstance(nested, dict) or "bundle_sha256" not in nested or \
            not isinstance(nested["bundle_sha256"], str):
        raise RuntimeError(
            "admission.bundle_sha256 must exist and be a string")
    source_hash = record["source_bundle_sha256"]
    admission_hash = nested["bundle_sha256"]
    if source_hash != admission_hash:
        raise RuntimeError("source and admission bundle hashes differ")
    if source_hash != local_bundle_sha256:
        raise RuntimeError("source bundle hash differs from local bundle")


def prepare_remote(mode: str, source_commit: str) -> dict:
    """The single admission path shared by rehearsal and timed execution."""
    if mode not in ("rehearse", "run"):
        raise RuntimeError("unknown execution mode")
    record = admission.admit_source(
        exercise_malformed=(mode == "rehearse"), source_commit=source_commit)
    validate_admission_receipt(record, record["source_bundle_sha256"])
    return record


def fetch_regular(record: dict, relative: str, destination: Path) -> dict:
    admission.remote_path_guard("validate", record["home"], record["safe_root"],
                                record["run_directory"])
    remote = record["run_directory"]
    if relative.startswith("/") or ".." in Path(relative).parts:
        raise RuntimeError("independent fetch path is unsafe")
    remote_file = f"{remote}/{relative}"
    remote_q = shlex.quote(remote_file)
    checked = admission.ssh(
        f"set -eu; test -f {remote_q}; test ! -L {remote_q}; "
        f"shasum -a 256 {remote_q} | awk '{{print $1}}'",
        timeout=CONTROL_TIMEOUT_SECONDS)
    remote_sha = checked.stdout.decode().strip()
    admission.run(["scp", "-q", f"{HOST}:{remote_file}", str(destination)],
                  timeout=CONTROL_TIMEOUT_SECONDS)
    local_sha = sha256(destination)
    if local_sha != remote_sha:
        raise RuntimeError(f"independent {relative} transfer hash mismatch")
    return {"path": relative, "remote_sha256": remote_sha,
            "local_sha256": local_sha, "hashes_match": True,
            "bytes": destination.stat().st_size}


def build_and_fetch_archive(record: dict, temporary: Path,
                            bulk_fixture: str | None = None) -> dict:
    remote = record["run_directory"]
    arguments = [
        "build", f"{remote}/evidence", f"{remote}/evidence/artifact-hashes.json",
        f"{remote}/evidence.tar.gz", f"{remote}/archive-inventory.json",
        f"{remote}/archive-digest.json",
    ]
    argv = " ".join(shlex.quote(value) for value in arguments)
    built = admission.ssh(f"python3 - {argv}",
                          input_bytes=Path(archive_protocol.__file__).read_bytes(),
                          timeout=ARCHIVE_BUILD_TIMEOUT_SECONDS, check=False)
    build_stdout = built.stdout.decode(errors="replace")
    build_stderr = built.stderr.decode(errors="replace")
    if built.returncode != 0:
        return {"status": "rejected", "builder_exit_code": built.returncode,
                "builder_stdout": build_stdout, "builder_stderr": build_stderr}
    inventory_path = temporary / "archive-inventory.json"
    digest_path = temporary / "archive-digest.json"
    archive_path = temporary / "evidence.tar.gz"
    transfers = {}
    try:
        # Compact DATA-PLANE declaration is returned before bulk transfer.
        transfers["inventory"] = fetch_regular(
            record, "archive-inventory.json", inventory_path)
        transfers["digest"] = fetch_regular(
            record, "archive-digest.json", digest_path)
        digest = json.loads(digest_path.read_text(encoding="utf-8"))
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        if digest.get("compression_format") != "tar+gzip":
            raise RuntimeError("archive compression format is not predeclared")
        if digest.get("archive_bytes", -1) < 0 or not isinstance(
                digest.get("archive_sha256"), str):
            raise RuntimeError("archive hash/size declaration is incomplete")
        if digest["archive_bytes"] > MAXIMUM_TRANSFER_ARCHIVE_BYTES:
            raise RuntimeError("archive exceeds frozen transport safety cap")
        if bulk_fixture == "missing-artifact":
            raise RuntimeError("fixture: optional bulk archive missing")
        if bulk_fixture == "timeout":
            raise TimeoutError("fixture: bulk transport timeout")
        remote_file = f"{record['run_directory']}/evidence.tar.gz"
        started = time.monotonic_ns()
        chunk_count = (digest["archive_bytes"] + BULK_CHUNK_BYTES - 1) // \
            BULK_CHUNK_BYTES
        with archive_path.open("xb") as destination:
            for chunk_index in range(chunk_count):
                if time.monotonic_ns() - started > \
                        TRANSFER_TIMEOUT_SECONDS * 1_000_000_000:
                    raise TimeoutError("bulk archive total timeout")
                returned = admission.ssh(
                    f"dd if={shlex.quote(remote_file)} bs={BULK_CHUNK_BYTES} "
                    f"skip={chunk_index} count=1 2>/dev/null",
                    timeout=BULK_CHUNK_TIMEOUT_SECONDS)
                expected = min(
                    BULK_CHUNK_BYTES,
                    digest["archive_bytes"] - chunk_index * BULK_CHUNK_BYTES)
                if len(returned.stdout) != expected:
                    raise RuntimeError("bulk archive chunk size mismatch")
                destination.write(returned.stdout)
        elapsed_ns = time.monotonic_ns() - started
        if bulk_fixture in ("truncated-archive", "corrupt-archive"):
            raw = archive_path.read_bytes()
            archive_path.write_bytes(raw[:-1] if bulk_fixture ==
                                     "truncated-archive" else
                                     bytes([raw[0] ^ 1]) + raw[1:])
        transfers["archive"] = {
            "path": "evidence.tar.gz", "remote_sha256": digest["archive_sha256"],
            "local_sha256": sha256(archive_path),
            "hashes_match": sha256(archive_path) == digest["archive_sha256"],
            "bytes": archive_path.stat().st_size,
            "elapsed_ns": elapsed_ns,
            "throughput_bytes_per_second":
                archive_path.stat().st_size * 1_000_000_000 // max(1, elapsed_ns),
            "timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "chunk_bytes": BULK_CHUNK_BYTES,
            "chunk_count": chunk_count,
            "chunk_timeout_seconds": BULK_CHUNK_TIMEOUT_SECONDS,
        }
        if transfers["archive"]["bytes"] != digest["archive_bytes"]:
            raise RuntimeError("archive byte-size declaration mismatch")
        if not transfers["archive"]["hashes_match"]:
            raise RuntimeError("archive digest record mismatch")
        inspected = archive_protocol.inspect_archive(archive_path)
        refusal = None
        if digest.get("inventory_sha256") != sha256(inventory_path):
            refusal = "archive inventory digest mismatch"
        elif inspected != inventory:
            refusal = "local and remote full archive inventories differ"
        if refusal is not None:
            return {"status": "rejected-before-extraction", "reason": refusal,
                    "builder_exit_code": 0, "builder_stdout": build_stdout,
                    "builder_stderr": build_stderr, "transfers": transfers,
                    "digest_record": digest, "member_inventory": inspected,
                    "remote_member_inventory": inventory,
                    "archive_path": archive_path,
                    "inventory_path": inventory_path, "digest_path": digest_path}
    except (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        inspected = (archive_protocol.inspect_archive(archive_path)
                     if archive_path.is_file() else None)
        return {"status": "rejected-before-extraction", "reason": str(error),
                "builder_exit_code": 0, "builder_stdout": build_stdout,
                "builder_stderr": build_stderr, "transfers": transfers,
                "archive_build_receipt": (
                    json.loads(digest_path.read_text(encoding="utf-8"))
                    if digest_path.is_file() else None),
                "remote_member_inventory": (
                    json.loads(inventory_path.read_text(encoding="utf-8"))
                    if inventory_path.is_file() else None),
                "member_inventory": inspected, "archive_path": archive_path,
                "inventory_path": inventory_path, "digest_path": digest_path}
    return {"status": "accepted", "builder_exit_code": 0,
            "builder_stdout": build_stdout, "builder_stderr": build_stderr,
            "archive": transfers["archive"], "inventory": transfers["inventory"],
            "digest": transfers["digest"], "digest_record": digest,
            "member_inventory": inventory, "archive_path": archive_path,
            "inventory_path": inventory_path, "digest_path": digest_path}


def lease_transfer_contract(mode: str, attempted: bool,
                            remote_receipt_available: bool,
                            fetch_receipt) -> tuple[dict, dict | None]:
    """Return the frozen lease-transfer state without optional long waits."""
    if not attempted:
        return ({
            "schema":
                "libwebp-backref-cost-attribution-v6-lease-transfer-v1",
            "state": "not-attempted", "status": "not-attempted",
            "acquisition_attempted": False,
            "receipt_required": False, "receipt_requested": False,
            "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "mode": mode,
        }, None)
    if not remote_receipt_available:
        return ({
            "schema":
                "libwebp-backref-cost-attribution-v6-lease-transfer-v1",
            "state": "unavailable-after-attempt",
            "status": "unavailable-after-attempt",
            "acquisition_attempted": True,
            "receipt_required": True, "receipt_requested": False,
            "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "mode": mode, "reason": "lease receipt absent after acquisition attempt",
        }, None)
    try:
        transfer, value = fetch_receipt()
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        return ({
            "schema":
                "libwebp-backref-cost-attribution-v6-lease-transfer-v1",
            "state": "unavailable-after-attempt",
            "status": "unavailable-after-attempt",
            "acquisition_attempted": True,
            "receipt_required": True, "receipt_requested": True,
            "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "mode": mode, "reason": str(error),
        }, None)
    return ({
        "schema": "libwebp-backref-cost-attribution-v6-lease-transfer-v1",
        "state": "verified", "status": "verified",
        "acquisition_attempted": True,
        "receipt_required": True, "receipt_requested": True,
        "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
        "mode": mode, "transfer": transfer,
    }, value)


def validate_control_plane(operator_status: dict | None,
                           lease_transfer: dict, cleanup: dict,
                           archive_record: dict) -> None:
    """Conjunctive compact-receipt contract, independent of bulk success."""
    if operator_status is None:
        raise RuntimeError("operator status control receipt is mandatory")
    attempted = operator_status.get("benchmark_lease_acquisition_attempted")
    if not isinstance(attempted, bool):
        raise RuntimeError("operator status lacks boolean lease-attempt state")
    required_state = "verified" if attempted else "not-attempted"
    if lease_transfer.get("state") != required_state:
        raise RuntimeError("lease return state disagrees with operator receipt")
    if cleanup.get("status") != "complete" or not cleanup.get(
            "absence_proved"):
        raise RuntimeError("exact-child cleanup/absence receipt is mandatory")
    if archive_record.get("builder_exit_code") is None:
        raise RuntimeError("archive-build receipt is mandatory")


def remote_pipeline(output: Path, mode: str,
                    refusal_fixture: str | None = None) -> dict:
    if mode == "run":
        validate_run_environment(os.environ)
    else:
        validate_untimed_environment(mode, os.environ)
    if mode == "run" and refusal_fixture is not None:
        raise RuntimeError("run does not accept a rehearsal refusal fixture")
    _, commit = validate_local_handoff(mode)
    if not MANIFEST_PATH.is_file():
        raise RuntimeError("frozen attribution-v6 manifest is absent")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    record = prepare_remote(mode, commit)
    pipeline = None
    archive_record: dict = {"status": "not-attempted"}
    lease_transfer, lease_value = ({
        "schema": "libwebp-backref-cost-attribution-v6-lease-transfer-v1",
        "state": "unavailable-after-attempt",
        "status": "unavailable-after-attempt",
        "acquisition_attempted": None,
        "receipt_required": None, "receipt_requested": False,
        "mode": mode,
        "reason": "operator status not yet independently returned",
    }, None)
    cleanup: dict = {"status": "not-attempted"}
    extraction: dict = {"status": "not-attempted"}
    operator_status: dict | None = None
    operator_status_transfer: dict | None = None
    acquisition_attempted: bool | None = None
    failure: Exception | None = None
    temporary_holder = tempfile.TemporaryDirectory(prefix="attribution-v6-return-")
    temporary = Path(temporary_holder.name)
    try:
        remote_q = shlex.quote(record["run_directory"])
        operator = "scripts/run_backref_cost_attribution_v6_experiment.py"
        remote_env = f"{EXPECTED_ENV}={shlex.quote(commit)}"
        if mode == "run":
            remote_env += " WEBP_BENCHMARK_SESSION=exclusive"
            operator_argv = f"run {remote_q}/evidence"
        elif refusal_fixture not in ("missing", "wrong"):
            operator_argv = f"rehearse {remote_q}/evidence"
        else:
            operator_argv = (
                f"refusal-fixture {remote_q}/evidence "
                f"{shlex.quote(refusal_fixture)}")
        pipeline = admission.ssh(
            f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} "
            f"{operator_argv}", timeout=7200, check=False)
        # CONTROL PLANE: source identity is already locally verified by
        # prepare_remote(). Operator status is independently fetched before
        # any optional bulk transfer and is authoritative for lease state.
        independent_status_path = temporary / "operator-status.json"
        operator_status_transfer = fetch_regular(
            record, "evidence/operator-status.json", independent_status_path)
        operator_status = json.loads(
            independent_status_path.read_text(encoding="utf-8"))
        if operator_status.get("schema") != manifest["schemas"]["operator_status"]:
            raise RuntimeError("independent operator-status schema mismatch")
        acquisition_attempted = bool(
            operator_status.get("benchmark_lease_acquisition_attempted"))
        if mode != "run" and acquisition_attempted:
            raise RuntimeError("untimed mode touched the benchmark lease")
        independent_lease_path = temporary / "independent-lease-record.json"

        def fetch_lease_receipt() -> tuple[dict, dict]:
            transfer = fetch_regular(record, "evidence/lease-record.json",
                                     independent_lease_path)
            value = json.loads(
                independent_lease_path.read_text(encoding="utf-8"))
            if value.get("schema") != manifest["schemas"]["lease"]:
                raise RuntimeError("independently returned lease schema mismatch")
            return transfer, value

        lease_transfer, lease_value = lease_transfer_contract(
            mode, acquisition_attempted, acquisition_attempted,
            fetch_lease_receipt)
        if acquisition_attempted and lease_transfer["state"] != "verified":
            raise RuntimeError("attempted lease lacks verified independent receipt")
        if lease_value is not None and lease_value.get("acquired") and not \
                lease_value.get("released"):
            raise RuntimeError("independently returned lease was not released")

        bulk_fixture = refusal_fixture if refusal_fixture not in (
            None, "missing", "wrong") else None
        archive_record = build_and_fetch_archive(
            record, temporary, bulk_fixture=bulk_fixture)
        if archive_record["status"] != "accepted":
            extraction = {
                "status": "rejected-before-extraction",
                "reason": archive_record.get("reason", "remote builder refused"),
                "member_inventory": archive_record.get("member_inventory"),
                "no_content_extracted": True,
            }
            raise RuntimeError("indexed remote archive builder refused evidence")
        extracted = temporary / "extracted-evidence"
        try:
            member_inventory = archive_protocol.extract_archive(
                archive_record["archive_path"], extracted)
            extraction = {"status": "accepted", "member_inventory": member_inventory}
        except archive_protocol.ArchiveRefusal as error:
            extraction = {"status": "rejected", "offending_member": error.member,
                          "reason": error.reason,
                          "member_inventory": archive_protocol.inspect_archive(
                              archive_record["archive_path"])}
            raise
        archived_status = json.loads(
            (extracted / "operator-status.json").read_text(encoding="utf-8"))
        if archived_status != operator_status:
            raise RuntimeError("bulk and independent operator status differ")
        output.parent.mkdir(parents=True, exist_ok=True)
        extracted.rename(output)
        expected_status = "refused" if refusal_fixture in (
            "missing", "wrong") else "complete"
        if operator_status.get("status") != expected_status:
            raise RuntimeError("remote operator status differs from requested mode")
    except Exception as error:
        failure = error
    finally:
        if not record.get("finished"):
            try:
                cleanup = admission.finish_admission(record)
                cleanup["schema"] = manifest["schemas"]["cleanup_receipt"]
                cleanup["status"] = "complete"
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                cleanup = {"schema": manifest["schemas"]["cleanup_receipt"],
                           "status": "rejected", "reason": str(error)}
                if failure is None:
                    failure = error

    if not output.exists():
        output.mkdir(parents=True)
    try:
        validate_control_plane(operator_status, lease_transfer, cleanup,
                               archive_record)
    except RuntimeError as error:
        if failure is None:
            failure = error
    protocol = output / "return-protocol"
    protocol.mkdir(exist_ok=True)
    source_receipt = serializable_admission(record)
    write_json(protocol / "source-admission-receipt.json", source_receipt)
    if operator_status is not None:
        write_json(protocol / "operator-status.json", operator_status)
    if operator_status_transfer is not None:
        write_json(protocol / "operator-status-transfer.json",
                   operator_status_transfer)
    if (temporary / "independent-lease-record.json").is_file():
        (protocol / "lease-record.json").write_bytes(
            (temporary / "independent-lease-record.json").read_bytes())
    write_json(protocol / "lease-transfer.json", lease_transfer)
    write_json(protocol / "archive-return.json", {
        key: value for key, value in archive_record.items()
        if not isinstance(value, Path)
    })
    write_json(protocol / "extraction.json", extraction)
    if pipeline is not None:
        (protocol / "pipeline.stdout").write_bytes(pipeline.stdout)
        (protocol / "pipeline.stderr").write_bytes(pipeline.stderr)
    if extraction.get("status", "").startswith("rejected") and archive_record.get(
            "archive_path", Path()).is_file():
        quarantine = protocol / "quarantine"
        quarantine.mkdir()
        shutil.copy2(archive_record["archive_path"], quarantine / "evidence.tar.gz")
        if archive_record.get("inventory_path", Path()).is_file():
            shutil.copy2(archive_record["inventory_path"],
                         quarantine / "archive-inventory.json")
        if archive_record.get("digest_path", Path()).is_file():
            shutil.copy2(archive_record["digest_path"],
                         quarantine / "archive-digest.json")
    control_members = [
        "source-admission-receipt.json", "operator-status.json",
        "operator-status-transfer.json", "lease-transfer.json",
        "archive-return.json", "cleanup-receipt.json"]
    write_json(protocol / "control-plane-order.json", {
        "schema": "libwebp-backref-cost-attribution-v6-control-plane-v1",
        "order": control_members,
        "bulk_transfer_optional_for_control_receipts": True,
        "lease_state_derived_from_operator_status": operator_status is not None,
        "cleanup_last_after_exact_child_absence_proof": True,
    })
    # Last mandatory control receipt: finish_admission already performed the
    # exact-child cleanup and remote absence proof in the finally block.
    write_json(protocol / "cleanup-receipt.json", cleanup)
    archive_protocol.write_returned_index(output, ["transfer-cleanup.json"])
    receipt = {
        "schema": manifest["schemas"]["transfer_cleanup"],
        "status": "complete" if failure is None and pipeline is not None and
                  pipeline.returncode == 0 else "refused",
        "mode": mode,
        "rehearsal_refusal_fixture": refusal_fixture,
        "return_contract_status": lease_transfer["state"],
        "source_commit": commit, "source_tree": record["source_tree"],
        "remote_host_alias": HOST,
        "source_bundle_sha256": record["source_bundle_sha256"],
        "admission": serializable_admission(record),
        "evidence_transfer": {
            "archive": {key: value for key, value in archive_record.items()
                        if not isinstance(value, Path)},
            "extraction": extraction,
            "lease": lease_transfer,
        },
        "lease_transfer_state": lease_transfer["state"],
        "lease_released": bool(lease_value and lease_value.get("released")),
        "benchmark_lease_acquisition_attempted": acquisition_attempted,
        "timed_binary_invoked": mode == "run" and pipeline is not None,
        "remote_cleanup_proof": cleanup,
        "remote_cleanup_complete": cleanup.get("status") == "complete",
        "remote_cleanup_absence_proved": bool(cleanup.get("absence_proved")),
        "installed_runner_directory_touched": False,
        "pipeline_exit_code": pipeline.returncode if pipeline is not None else None,
        "pipeline_stdout_path": "return-protocol/pipeline.stdout",
        "pipeline_stderr_path": "return-protocol/pipeline.stderr",
        "failure": str(failure) if failure else None,
    }
    write_json(output / "transfer-cleanup.json", receipt)
    archive_protocol.verify_returned_index(
        output / "returned-evidence-hashes.json", output)
    temporary_holder.cleanup()
    if receipt["status"] != "complete":
        raise RuntimeError(
            "remote pipeline or evidence return refused; independent lease and "
            "cleanup evidence retained")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    rehearsal = sub.add_parser("rehearse")
    rehearsal.add_argument("output", type=Path)
    rehearsal.add_argument("--refusal-fixture", choices=(
        "missing", "wrong", "timeout", "missing-artifact",
        "truncated-archive", "corrupt-archive"))
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        validate_untimed_environment("validate", os.environ)
        head, commit = validate_local_handoff("validate")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        print(json.dumps({
            "status": "PASS", "mode": "validate", "source_commit": commit,
            "freeze_commit": head,
            "manifest_sha256": sha256(MANIFEST_PATH),
            "schema_catalog_sha256": sha256(
                ROOT / manifest["schemas"]["catalog"]),
            "benchmark_lease_acquisition_attempted": False,
            "timed_binary_invoked": False,
        }, sort_keys=True))
        return 0
    if args.command == "rehearse":
        result = remote_pipeline(
            args.output, "rehearse", args.refusal_fixture)
    else:
        result = remote_pipeline(args.output, "run")
    print(json.dumps({"status": result["status"],
                      "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, archive_protocol.ArchiveRefusal) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
