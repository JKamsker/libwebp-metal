#!/usr/bin/env python3
"""Transfer and execute the frozen remote-v2 pipeline once on ssh pandocs-agent."""

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


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_remote_v2_manifest.json"
HOST = "pandocs-agent"
PATH_GUARD = ROOT / "scripts" / "backref_cost_workspace_remote_v2_paths.py"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def run(argv: list[str], *, input_bytes: bytes | None = None,
        timeout: int = 1200, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=ROOT, input=input_bytes, timeout=timeout,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{result.stdout.decode(errors='replace')}\n"
            f"stderr:\n{result.stderr.decode(errors='replace')}")
    return result


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT,
                                   text=True).strip()


def ssh(script: str, *, input_bytes: bytes | None = None, timeout: int = 1200,
        check: bool = True) -> subprocess.CompletedProcess:
    return run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                HOST, script], input_bytes=input_bytes, timeout=timeout,
               check=check)


def remote_path_guard(command: str, *arguments: str) -> dict:
    argv = " ".join(shlex.quote(value) for value in (command, *arguments))
    result = ssh(f"python3 - {argv}", input_bytes=PATH_GUARD.read_bytes())
    return json.loads(result.stdout.decode())


def remote_process_guard() -> dict:
    result = ssh("ps -axo pid=,ppid=,state=,etime=,command=")
    text = result.stdout.decode(errors="replace")
    workers = [line for line in text.splitlines() if "Runner.Worker" in line]
    if workers:
        raise RuntimeError("active Runner.Worker/job detected; services are untouched")
    return {"process_table_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "runner_worker_matches": workers,
            "runner_listener_present": "Runner.Listener" in text}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def retrieve_evidence(home: str, safe_root: str, remote: str, archive: Path,
                      output: Path,
                      temporary: Path, *, complete: bool) -> tuple[str, str]:
    remote_path_guard("validate", home, safe_root, remote)
    remote_q = shlex.quote(remote)
    ssh(f"set -eu; cd {remote_q}; mkdir -p evidence; "
        "tar -czf evidence.tar.gz evidence; "
        "shasum -a 256 evidence.tar.gz > evidence.tar.gz.sha256")
    remote_sha = ssh(
        f"set -eu; awk '{{print $1}}' {remote_q}/evidence.tar.gz.sha256").stdout.decode().strip()
    run(["scp", "-q", f"{HOST}:{remote}/evidence.tar.gz", str(archive)])
    local_sha = sha256(archive)
    if local_sha != remote_sha:
        raise RuntimeError("returned evidence archive hash mismatch")
    returned = temporary / "returned"
    returned.mkdir()
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if any(member.name.startswith("/") or ".." in Path(member.name).parts or
               not (member.isdir() or member.isfile()) or
               not Path(member.name).parts or
               Path(member.name).parts[0] != "evidence" for member in members):
            raise RuntimeError("unsafe returned archive member")
        for member in members:
            destination = returned.joinpath(*Path(member.name).parts)
            if os.path.commonpath((str(returned), str(destination))) != str(returned):
                raise RuntimeError("returned archive member escaped destination")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                if source is None:
                    raise RuntimeError("returned regular file is unreadable")
                with source, destination.open("wb") as target:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        target.write(chunk)
    output.parent.mkdir(parents=True, exist_ok=True)
    (returned / "evidence").rename(output)
    if complete:
        remote_index = json.loads((output / "artifact-hashes.json").read_text())
        for artifact in remote_index["artifacts"]:
            path = output / artifact["path"]
            if path.stat().st_size != artifact["bytes"] or \
                    sha256(path) != artifact["sha256"]:
                raise RuntimeError("returned artifact integrity mismatch")
    return remote_sha, local_sha


def cleanup_remote(home: str, safe_root: str, remote: str) -> dict:
    result = remote_path_guard("cleanup", home, safe_root, remote)
    if not result.get("removed_exact_validated_child") or \
            not result.get("absence_proved"):
        raise RuntimeError("remote exact-child cleanup proof failed")
    return result


def write_returned_index(manifest: dict, output: Path) -> None:
    rows = [{"path": str(path.relative_to(output)),
             "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(output.rglob("*")) if path.is_file()]
    write_json(output / "returned-evidence-hashes.json", {
        "schema": manifest["schemas"]["returned_evidence_hashes"],
        "artifacts": rows})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("path-round-trip")
    execute_parser = sub.add_parser("run")
    execute_parser.add_argument("output", type=Path,
                                help="new absolute local evidence directory")
    args = parser.parse_args()
    if args.command == "path-round-trip":
        process = remote_process_guard()
        result = remote_path_guard("round-trip")
        print(json.dumps({"status": "PASS", "remote_host_alias": HOST,
                          "process_guard": process, "path_round_trip": result},
                         sort_keys=True))
        return 0
    output = args.output
    manifest = json.loads(MANIFEST_PATH.read_text())
    expected_var = manifest["required_expected_commit_environment"]
    expected = os.environ.get(expected_var)
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("remote run requires WEBP_BENCHMARK_SESSION=exclusive")
    if not expected:
        raise RuntimeError(f"{expected_var} is required")
    commit = git("rev-parse", "HEAD")
    if commit != expected or git("status", "--porcelain"):
        raise RuntimeError("local source must be the exact clean handoff commit")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute local path")
    remote = ""
    remote_home = ""
    safe_root = ""
    remote_archive_sha = ""
    local_archive_sha = ""
    cleanup = False
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with tempfile.TemporaryDirectory(prefix="backref-workspace-remote-transfer-") as raw:
        temporary = Path(raw)
        bundle = temporary / "source.bundle"
        archive = temporary / "evidence.tar.gz"
        pretransfer_process = remote_process_guard()
        run(["git", "bundle", "create", str(bundle), "HEAD"])
        bundle_sha = sha256(bundle)
        generated = remote_path_guard("generate")
        remote_home = generated["home"]
        safe_root = generated["safe_root"]
        remote = generated["run_directory"]
        remote_path_guard("validate", remote_home, safe_root, remote)
        try:
            remote_q = shlex.quote(remote)
            run(["scp", "-q", str(bundle), f"{HOST}:{remote}/source.bundle"])
            remote_bundle_sha = ssh(
                f"set -eu; shasum -a 256 {remote_q}/source.bundle | awk '{{print $1}}'")
            if remote_bundle_sha.stdout.decode().strip() != bundle_sha:
                raise RuntimeError("source bundle transfer hash mismatch")
            ssh(f"set -eu; git bundle verify {remote_q}/source.bundle >/dev/null; "
                f"git clone -q {remote_q}/source.bundle {remote_q}/source; "
                f"cd {remote_q}/source; git checkout -q {shlex.quote(commit)}; "
                f"test \"$(git rev-parse HEAD)\" = {shlex.quote(commit)}; "
                "test -z \"$(git status --porcelain)\"")
            operator = "scripts/run_backref_cost_workspace_remote_v2_experiment.py"
            remote_env = (f"{expected_var}={shlex.quote(commit)} "
                          "WEBP_BENCHMARK_SESSION=exclusive")
            validation = ssh(
                f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} validate")
            validation_json = json.loads(validation.stdout.decode())
            if validation_json["source_commit"] != commit:
                raise RuntimeError("remote source identity mismatch")
            # This is the single authorized invocation of the timed pipeline.
            pipeline = ssh(
                f"set -eu; cd {remote_q}/source; {remote_env} python3 {operator} "
                f"run {remote_q}/evidence", timeout=7200, check=False)
            if pipeline.returncode != 0:
                remote_archive_sha, local_archive_sha = retrieve_evidence(
                    remote_home, safe_root, remote, archive, output, temporary,
                    complete=False)
                lease_released = False
                lease_path = output / "lease-record.json"
                if lease_path.exists():
                    lease_released = json.loads(
                        lease_path.read_text()).get("released", False)
                cleanup_proof = cleanup_remote(remote_home, safe_root, remote)
                cleanup = True
                write_json(output / "transfer-cleanup.json", {
                    "schema": manifest["schemas"]["transfer_cleanup"],
                    "status": "remote_pipeline_refused",
                    "source_commit": commit, "remote_host_alias": HOST,
                    "remote_temporary_directory": remote,
                    "source_bundle_sha256": bundle_sha,
                    "remote_validation": validation_json,
                    "remote_path_generation": generated,
                    "remote_cleanup_proof": cleanup_proof,
                    "pretransfer_process_isolation": pretransfer_process,
                    "remote_evidence_archive_sha256": remote_archive_sha,
                    "local_evidence_archive_sha256": local_archive_sha,
                    "archive_hashes_match": True,
                    "lease_released": lease_released,
                    "remote_cleanup_complete": True,
                    "installed_runner_directory_touched": False,
                    "pipeline_exit_code": pipeline.returncode,
                    "pipeline_stdout": pipeline.stdout.decode(errors="replace"),
                    "pipeline_stderr": pipeline.stderr.decode(errors="replace"),
                    "started_at_utc": started,
                    "completed_at_utc": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                write_returned_index(manifest, output)
                raise RuntimeError(
                    "remote pipeline refused; partial evidence returned and cleanup completed")
            lease = json.loads(ssh(
                f"set -eu; test -f {remote_q}/evidence/lease-record.json; "
                f"cat {remote_q}/evidence/lease-record.json").stdout.decode())
            if not lease.get("released"):
                raise RuntimeError("remote lease release was not recorded")
            remote_archive_sha, local_archive_sha = retrieve_evidence(
                remote_home, safe_root, remote, archive, output, temporary,
                complete=True)
            cleanup_proof = cleanup_remote(remote_home, safe_root, remote)
            cleanup = True
            receipt = {
                "schema": manifest["schemas"]["transfer_cleanup"],
                "source_commit": commit, "remote_host_alias": HOST,
                "remote_temporary_directory": remote,
                "source_bundle_sha256": bundle_sha,
                "remote_validation": validation_json,
                "remote_path_generation": generated,
                "remote_cleanup_proof": cleanup_proof,
                "pretransfer_process_isolation": pretransfer_process,
                "remote_evidence_archive_sha256": remote_archive_sha,
                "local_evidence_archive_sha256": local_archive_sha,
                "archive_hashes_match": True, "lease_released": True,
                "remote_cleanup_complete": True,
                "installed_runner_directory_touched": False,
                "started_at_utc": started,
                "completed_at_utc": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            write_json(output / "transfer-cleanup.json", receipt)
            write_returned_index(manifest, output)
        finally:
            if remote and not cleanup:
                # The same exact validator used at creation authorizes cleanup;
                # it removes only the canonical run child and proves absence.
                cleanup_remote(remote_home, safe_root, remote)
                cleanup = True
    print(json.dumps({"status": "complete", "source_commit": commit,
                      "output": str(output),
                      "remote_archive_sha256": remote_archive_sha,
                      "remote_cleanup_complete": cleanup}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, tarfile.TarError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
