#!/usr/bin/env python3
"""Remote-v5 admission-only rehearsal and frozen pipeline executor."""

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

import backref_cost_workspace_remote_v5_admission as admission
import backref_cost_workspace_remote_v5_archive as archive_protocol


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_remote_v5_manifest.json"
EXPECTED_ENV = "WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V5_COMMIT"


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


def prepare_remote(mode: str) -> dict:
    """The single admission path shared by rehearsal and timed execution."""
    if mode not in ("admission-only", "run"):
        raise RuntimeError("unknown execution mode")
    return admission.admit_source(exercise_malformed=(mode == "admission-only"))


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
        f"shasum -a 256 {remote_q} | awk '{{print $1}}'")
    remote_sha = checked.stdout.decode().strip()
    admission.run(["scp", "-q", f"{HOST}:{remote_file}", str(destination)])
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
                          check=False)
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


def admission_only(output: Path) -> dict:
    if os.environ.get("WEBP_BENCHMARK_SESSION") is not None:
        raise RuntimeError(
            "admission-only requires WEBP_BENCHMARK_SESSION to be unset")
    commit = validate_local_handoff()
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    record = prepare_remote("admission-only")
    try:
        cleanup = admission.finish_admission(record)
    except Exception:
        raise
    receipt = {
        "schema": "libwebp-backref-cost-workspace-remote-v5-admission-rehearsal-v1",
        "status": "PASS", "mode": "admission-only", "source_commit": commit,
        "shared_implementation": "admission.admit_source",
        "benchmark_lease_acquisition_attempted": False,
        "timed_binary_invoked": False,
        "runner_directories_or_services_touched": False,
        "host_settings_changed": False,
        "admission": serializable_admission(record),
        "cleanup": cleanup,
    }
    output.mkdir(parents=True)
    write_json(output / "admission-rehearsal.json", receipt)
    return receipt


def timed_run(output: Path) -> dict:
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("remote timed run requires WEBP_BENCHMARK_SESSION=exclusive")
    commit = validate_local_handoff()
    if not MANIFEST_PATH.is_file():
        raise RuntimeError("frozen v5 manifest is absent")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    record = prepare_remote("run")
    pipeline = None
    archive_record: dict = {"status": "not-attempted"}
    lease_transfer: dict = {"status": "not-attempted"}
    cleanup: dict = {"status": "not-attempted"}
    extraction: dict = {"status": "not-attempted"}
    failure: Exception | None = None
    temporary_holder = tempfile.TemporaryDirectory(prefix="remote-v5-return-")
    temporary = Path(temporary_holder.name)
    try:
        remote_q = shlex.quote(record["run_directory"])
        operator = "scripts/run_backref_cost_workspace_remote_v5_experiment.py"
        remote_env = (f"{EXPECTED_ENV}={shlex.quote(commit)} "
                      "WEBP_BENCHMARK_SESSION=exclusive")
        pipeline = admission.ssh(
            f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} "
            f"run {remote_q}/evidence", timeout=7200, check=False)
        lease_path = temporary / "lease-record.json"
        lease_transfer = fetch_regular(record, "evidence/lease-record.json",
                                       lease_path)
        lease_transfer["status"] = "accepted"
        lease_value = json.loads(lease_path.read_text(encoding="utf-8"))
        if lease_value.get("schema") != manifest["schemas"]["lease"]:
            raise RuntimeError("independently returned lease schema mismatch")
        if lease_value.get("acquired") and not lease_value.get("released"):
            raise RuntimeError("independently returned lease was not released")
        if pipeline.returncode == 0 and not lease_value.get("released"):
            raise RuntimeError("successful pipeline lacks lease release proof")
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
        output.parent.mkdir(parents=True, exist_ok=True)
        extracted.rename(output)
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
    if (temporary / "lease-record.json").is_file():
        (protocol / "lease-record.json").write_bytes(
            (temporary / "lease-record.json").read_bytes())
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
        "source_commit": commit, "remote_host_alias": HOST,
        "admission": serializable_admission(record),
        "evidence_transfer": {
            "archive": {key: value for key, value in archive_record.items()
                        if not isinstance(value, Path)},
            "extraction": extraction,
            "lease": lease_transfer,
        },
        "lease_released": bool((temporary / "lease-record.json").is_file() and
            json.loads((temporary / "lease-record.json").read_text()).get(
                "released", False)),
        "remote_cleanup_proof": cleanup,
        "remote_cleanup_complete": cleanup.get("status") == "complete",
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
    sub.add_parser("path-round-trip")
    for name in ("admission-only", "run"):
        child = sub.add_parser(name)
        child.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "path-round-trip":
        if os.environ.get("WEBP_BENCHMARK_SESSION") is not None:
            raise RuntimeError("path round-trip requires benchmark session unset")
        result = admission.remote_path_guard("round-trip")
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.command == "admission-only":
        result = admission_only(args.output)
    else:
        result = timed_run(args.output)
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
