#!/usr/bin/env python3
"""Remote-v3 admission-only rehearsal and frozen pipeline executor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import backref_cost_workspace_remote_v3_admission as admission


ROOT = Path(__file__).resolve().parents[1]
HOST = admission.HOST
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_remote_v3_manifest.json"
EXPECTED_ENV = "WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V3_COMMIT"


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


def safe_extract(archive: Path, destination: Path) -> Path:
    returned = destination / "returned"
    returned.mkdir()
    with tarfile.open(archive, "r:gz") as opened:
        members = opened.getmembers()
        for member in members:
            parts = Path(member.name).parts
            if (member.name.startswith("/") or ".." in parts or not parts or
                    parts[0] != "evidence" or
                    not (member.isdir() or member.isfile())):
                raise RuntimeError("unsafe returned archive member")
            target = returned.joinpath(*parts)
            if os.path.commonpath((str(returned), str(target))) != str(returned):
                raise RuntimeError("returned archive member escaped destination")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = opened.extractfile(member)
                if source is None:
                    raise RuntimeError("returned regular file is unreadable")
                with source, target.open("wb") as output:
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
    return returned / "evidence"


def retrieve_evidence(record: dict, output: Path, *, complete: bool) -> dict:
    admission.remote_path_guard("validate", record["home"], record["safe_root"],
                                record["run_directory"])
    remote = record["run_directory"]
    remote_q = shlex.quote(remote)
    admission.ssh(
        f"set -eu; cd {remote_q}; test -d evidence; "
        "tar -czf evidence.tar.gz evidence; "
        "shasum -a 256 evidence.tar.gz > evidence.tar.gz.sha256")
    remote_sha = admission.ssh(
        f"awk '{{print $1}}' {remote_q}/evidence.tar.gz.sha256").stdout.decode().strip()
    with tempfile.TemporaryDirectory(prefix="remote-v3-return-") as raw:
        temporary = Path(raw)
        archive = temporary / "evidence.tar.gz"
        admission.run(["scp", "-q", f"{HOST}:{remote}/evidence.tar.gz",
                       str(archive)])
        local_sha = sha256(archive)
        if local_sha != remote_sha:
            raise RuntimeError("returned evidence archive hash mismatch")
        extracted = safe_extract(archive, temporary)
        if output.exists():
            raise RuntimeError("output appeared during evidence return")
        output.parent.mkdir(parents=True, exist_ok=True)
        extracted.rename(output)
    if complete:
        index = json.loads((output / "artifact-hashes.json").read_text())
        for artifact in index["artifacts"]:
            path = output / artifact["path"]
            if path.stat().st_size != artifact["bytes"] or \
                    sha256(path) != artifact["sha256"]:
                raise RuntimeError("returned artifact integrity mismatch")
    return {"remote_sha256": remote_sha, "local_sha256": local_sha,
            "hashes_match": True}


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
        "schema": "libwebp-backref-cost-workspace-remote-v3-admission-rehearsal-v1",
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
        raise RuntimeError("frozen v3 manifest is absent")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    record = prepare_remote("run")
    returned = False
    try:
        remote_q = shlex.quote(record["run_directory"])
        operator = "scripts/run_backref_cost_workspace_remote_v3_experiment.py"
        remote_env = (f"{EXPECTED_ENV}={shlex.quote(commit)} "
                      "WEBP_BENCHMARK_SESSION=exclusive")
        pipeline = admission.ssh(
            f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} "
            f"run {remote_q}/evidence", timeout=7200, check=False)
        transfer = retrieve_evidence(record, output,
                                     complete=pipeline.returncode == 0)
        returned = True
        lease_path = output / "lease-record.json"
        lease_released = lease_path.is_file() and json.loads(
            lease_path.read_text()).get("released", False)
        if pipeline.returncode == 0 and not lease_released:
            raise RuntimeError("remote lease release was not recorded")
        cleanup = admission.finish_admission(record)
        receipt = {
            "schema": manifest["schemas"]["transfer_cleanup"],
            "status": "complete" if pipeline.returncode == 0 else "refused",
            "source_commit": commit, "remote_host_alias": HOST,
            "admission": serializable_admission(record),
            "evidence_transfer": transfer, "lease_released": lease_released,
            "remote_cleanup_proof": cleanup,
            "remote_cleanup_complete": True,
            "installed_runner_directory_touched": False,
            "pipeline_exit_code": pipeline.returncode,
            "pipeline_stdout": pipeline.stdout.decode(errors="replace"),
            "pipeline_stderr": pipeline.stderr.decode(errors="replace"),
        }
        write_json(output / "transfer-cleanup.json", receipt)
        if pipeline.returncode != 0:
            raise RuntimeError(
                "remote pipeline refused; partial evidence returned and cleanup completed")
        return receipt
    finally:
        if not record.get("finished"):
            try:
                admission.finish_admission(record)
            except (OSError, RuntimeError, subprocess.SubprocessError):
                if sys.exc_info()[0] is None:
                    raise


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
            json.JSONDecodeError, tarfile.TarError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
