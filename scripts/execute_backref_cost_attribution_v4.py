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
from pathlib import Path

import backref_cost_attribution_v4_admission as admission
import backref_cost_attribution_v4_archive as archive_protocol


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_attribution_v4_manifest.json"
EXPECTED_ENV = "WEBP_EXPECTED_BACKREF_COST_ATTRIBUTION_V4_COMMIT"
TRANSFER_TIMEOUT_SECONDS = 30
ARCHIVE_BUILD_TIMEOUT_SECONDS = 180


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


def validate_local_handoff() -> str:
    expected = os.environ.get(EXPECTED_ENV)
    if not expected:
        raise RuntimeError(f"{EXPECTED_ENV} is required")
    commit, _, _ = admission.local_identity()
    if commit != expected:
        raise RuntimeError("local source must be the exact clean handoff commit")
    return commit


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


def prepare_remote(mode: str) -> dict:
    """The single admission path shared by rehearsal and timed execution."""
    if mode not in ("rehearse", "run"):
        raise RuntimeError("unknown execution mode")
    record = admission.admit_source(exercise_malformed=(mode == "rehearse"))
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
        timeout=TRANSFER_TIMEOUT_SECONDS)
    remote_sha = checked.stdout.decode().strip()
    admission.run(["scp", "-q", f"{HOST}:{remote_file}", str(destination)],
                  timeout=TRANSFER_TIMEOUT_SECONDS)
    local_sha = sha256(destination)
    if local_sha != remote_sha:
        raise RuntimeError(f"independent {relative} transfer hash mismatch")
    return {"path": relative, "remote_sha256": remote_sha,
            "local_sha256": local_sha, "hashes_match": True,
            "bytes": destination.stat().st_size}


def build_and_fetch_archive(record: dict, temporary: Path) -> dict:
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
        transfers["inventory"] = fetch_regular(
            record, "archive-inventory.json", inventory_path)
        transfers["digest"] = fetch_regular(
            record, "archive-digest.json", digest_path)
        transfers["archive"] = fetch_regular(
            record, "evidence.tar.gz", archive_path)
        digest = json.loads(digest_path.read_text(encoding="utf-8"))
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inspected = archive_protocol.inspect_archive(archive_path)
        refusal = None
        if digest.get("archive_sha256") != transfers["archive"]["local_sha256"]:
            refusal = "archive digest record mismatch"
        elif digest.get("inventory_sha256") != sha256(inventory_path):
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
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        inspected = (archive_protocol.inspect_archive(archive_path)
                     if archive_path.is_file() else None)
        return {"status": "rejected-before-extraction", "reason": str(error),
                "builder_exit_code": 0, "builder_stdout": build_stdout,
                "builder_stderr": build_stderr, "transfers": transfers,
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
                "libwebp-backref-cost-attribution-v4-lease-transfer-v1",
            "state": "not-attempted", "status": "not-attempted",
            "acquisition_attempted": False,
            "receipt_required": False, "receipt_requested": False,
            "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "mode": mode,
        }, None)
    if not remote_receipt_available:
        return ({
            "schema":
                "libwebp-backref-cost-attribution-v4-lease-transfer-v1",
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
                "libwebp-backref-cost-attribution-v4-lease-transfer-v1",
            "state": "unavailable-after-attempt",
            "status": "unavailable-after-attempt",
            "acquisition_attempted": True,
            "receipt_required": True, "receipt_requested": True,
            "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
            "mode": mode, "reason": str(error),
        }, None)
    return ({
        "schema": "libwebp-backref-cost-attribution-v4-lease-transfer-v1",
        "state": "verified", "status": "verified",
        "acquisition_attempted": True,
        "receipt_required": True, "receipt_requested": True,
        "transfer_timeout_seconds": TRANSFER_TIMEOUT_SECONDS,
        "mode": mode, "transfer": transfer,
    }, value)


def remote_pipeline(output: Path, mode: str,
                    refusal_fixture: str | None = None) -> dict:
    if mode == "run":
        validate_run_environment(os.environ)
    else:
        validate_untimed_environment(mode, os.environ)
    if mode == "run" and refusal_fixture is not None:
        raise RuntimeError("run does not accept a rehearsal refusal fixture")
    commit = validate_local_handoff()
    if not MANIFEST_PATH.is_file():
        raise RuntimeError("frozen attribution-v4 manifest is absent")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if mode == "run" and not manifest.get("phase_1_decision", {}).get(
            "timed_execution_authorized", False):
        raise RuntimeError(
            "phase-1 handoff rejected timing; see frozen blocker evidence")
    record = prepare_remote(mode)
    pipeline = None
    archive_record: dict = {"status": "not-attempted"}
    lease_transfer, lease_value = lease_transfer_contract(
        mode, attempted=False, remote_receipt_available=False,
        fetch_receipt=lambda: (_ for _ in ()).throw(
            AssertionError("not-attempted lease must not be requested")))
    cleanup: dict = {"status": "not-attempted"}
    extraction: dict = {"status": "not-attempted"}
    acquisition_attempted = False
    failure: Exception | None = None
    temporary_holder = tempfile.TemporaryDirectory(prefix="attribution-v4-return-")
    temporary = Path(temporary_holder.name)
    try:
        remote_q = shlex.quote(record["run_directory"])
        operator = "scripts/run_backref_cost_attribution_v4_experiment.py"
        remote_env = f"{EXPECTED_ENV}={shlex.quote(commit)}"
        if mode == "run":
            remote_env += " WEBP_BENCHMARK_SESSION=exclusive"
            operator_argv = f"run {remote_q}/evidence"
        elif refusal_fixture is None:
            operator_argv = f"rehearse {remote_q}/evidence"
        else:
            operator_argv = (
                f"refusal-fixture {remote_q}/evidence "
                f"{shlex.quote(refusal_fixture)}")
        pipeline = admission.ssh(
            f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} "
            f"{operator_argv}", timeout=7200, check=False)
        archive_record = build_and_fetch_archive(record, temporary)
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
        archived_lease_path = extracted / "lease-record.json"
        archived_lease = None
        if archived_lease_path.is_file():
            archived_lease = json.loads(
                archived_lease_path.read_text(encoding="utf-8"))
        operator_status = json.loads(
            (extracted / "operator-status.json").read_text(encoding="utf-8"))
        acquisition_attempted = bool(
            operator_status.get("benchmark_lease_acquisition_attempted") or
            (archived_lease and
             archived_lease.get("acquisition_attempted")))
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
            mode, acquisition_attempted, archived_lease_path.is_file(),
            fetch_lease_receipt)
        if acquisition_attempted and lease_transfer["state"] != "verified":
            raise RuntimeError("attempted lease lacks verified independent receipt")
        if lease_value is not None:
            if lease_value.get("acquired") and not lease_value.get("released"):
                raise RuntimeError("independently returned lease was not released")
            if pipeline.returncode == 0 and not lease_value.get("released"):
                raise RuntimeError("successful pipeline lacks lease release proof")
        output.parent.mkdir(parents=True, exist_ok=True)
        extracted.rename(output)
        expected_status = "refused" if refusal_fixture is not None else "complete"
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
    protocol = output / "return-protocol"
    protocol.mkdir(exist_ok=True)
    if (temporary / "independent-lease-record.json").is_file():
        (protocol / "lease-record.json").write_bytes(
            (temporary / "independent-lease-record.json").read_bytes())
    write_json(protocol / "lease-transfer.json", lease_transfer)
    write_json(protocol / "cleanup-receipt.json", cleanup)
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
    archive_protocol.write_returned_index(output, ["transfer-cleanup.json"])
    receipt = {
        "schema": manifest["schemas"]["transfer_cleanup"],
        "status": "complete" if failure is None and pipeline is not None and
                  pipeline.returncode == 0 else "refused",
        "mode": mode,
        "rehearsal_refusal_fixture": refusal_fixture,
        "return_contract_status": lease_transfer["state"],
        "source_commit": commit, "remote_host_alias": HOST,
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
    rehearsal.add_argument("--refusal-fixture", choices=("missing", "wrong"))
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        validate_untimed_environment("validate", os.environ)
        commit = validate_local_handoff()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        print(json.dumps({
            "status": "PASS", "mode": "validate", "source_commit": commit,
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
