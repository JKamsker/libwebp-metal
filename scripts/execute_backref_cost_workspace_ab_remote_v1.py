#!/usr/bin/env python3
"""Transfer and execute the frozen v1 pipeline once on ssh pandocs-agent."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_ab_experiment_v1.json"
HOST = "pandocs-agent"
REMOTE_ROOT = ".cache/libwebp-metal-experiments/backref-cost-workspace-ab-v1"


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


def ssh(script: str, *, timeout: int = 1200,
        check: bool = True) -> subprocess.CompletedProcess:
    return run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                HOST, script], timeout=timeout, check=check)


def safe_remote_path(remote: str) -> None:
    prefix = f"/Users/{remote.split('/')[2]}/{REMOTE_ROOT}/run."
    if not remote.startswith(prefix) or remote.count("/") < 7:
        raise RuntimeError(f"unsafe remote experiment path: {remote}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def retrieve_evidence(remote: str, archive: Path, output: Path,
                      temporary: Path, *, complete: bool) -> tuple[str, str]:
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
        if any(member.name.startswith("/") or
               ".." in Path(member.name).parts or member.issym() or
               member.islnk() or member.isdev() for member in members):
            raise RuntimeError("unsafe returned archive member")
        tar.extractall(returned)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(returned / "evidence"), str(output))
    if complete:
        remote_index = json.loads((output / "artifact-hashes.json").read_text())
        for artifact in remote_index["artifacts"]:
            path = output / artifact["path"]
            if path.stat().st_size != artifact["bytes"] or \
                    sha256(path) != artifact["sha256"]:
                raise RuntimeError("returned artifact integrity mismatch")
    return remote_sha, local_sha


def cleanup_remote(remote: str) -> None:
    safe_remote_path(remote)
    remote_q = shlex.quote(remote)
    ssh(f"set -eu; case {remote_q} in "
        f"/Users/*/{REMOTE_ROOT}/run.*) rm -rf -- {remote_q} ;; "
        "*) exit 90 ;; esac")
    if ssh(f"test ! -e {remote_q}", check=False).returncode != 0:
        raise RuntimeError("remote temporary directory cleanup failed")


def write_returned_index(manifest: dict, output: Path) -> None:
    rows = [{"path": str(path.relative_to(output)),
             "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(output.rglob("*")) if path.is_file()]
    write_json(output / "returned-evidence-hashes.json", {
        "schema": manifest["schemas"]["returned_evidence_hashes"],
        "artifacts": rows})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path,
                        help="new absolute local evidence directory")
    args = parser.parse_args()
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
    remote_archive_sha = ""
    local_archive_sha = ""
    cleanup = False
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with tempfile.TemporaryDirectory(prefix="backref-workspace-remote-transfer-") as raw:
        temporary = Path(raw)
        bundle = temporary / "source.bundle"
        archive = temporary / "evidence.tar.gz"
        run(["git", "bundle", "create", str(bundle), "HEAD"])
        bundle_sha = sha256(bundle)
        base = f"$HOME/{REMOTE_ROOT}"
        created = ssh(
            f"set -eu; mkdir -p {base}; mktemp -d {base}/run.XXXXXX")
        remote = created.stdout.decode().strip()
        safe_remote_path(remote)
        try:
            remote_q = shlex.quote(remote)
            run(["scp", "-q", str(bundle), f"{HOST}:{remote}/source.bundle"])
            remote_bundle_sha = ssh(
                f"set -eu; shasum -a 256 {remote_q}/source.bundle | awk '{{print $1}}'")
            if remote_bundle_sha.stdout.decode().strip() != bundle_sha:
                raise RuntimeError("source bundle transfer hash mismatch")
            ssh(f"set -eu; git clone -q {remote_q}/source.bundle {remote_q}/source; "
                f"cd {remote_q}/source; git checkout -q {shlex.quote(commit)}; "
                "test -z \"$(git status --porcelain)\"")
            operator = "scripts/run_backref_cost_workspace_ab_experiment.py"
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
                    remote, archive, output, temporary, complete=False)
                lease_released = False
                lease_path = output / "lease-record.json"
                if lease_path.exists():
                    lease_released = json.loads(
                        lease_path.read_text()).get("released", False)
                cleanup_remote(remote)
                cleanup = True
                write_json(output / "transfer-cleanup.json", {
                    "schema": manifest["schemas"]["transfer_cleanup"],
                    "status": "remote_pipeline_refused",
                    "source_commit": commit, "remote_host_alias": HOST,
                    "remote_temporary_directory": remote,
                    "source_bundle_sha256": bundle_sha,
                    "remote_validation": validation_json,
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
                remote, archive, output, temporary, complete=True)
            cleanup_remote(remote)
            cleanup = True
            receipt = {
                "schema": manifest["schemas"]["transfer_cleanup"],
                "source_commit": commit, "remote_host_alias": HOST,
                "remote_temporary_directory": remote,
                "source_bundle_sha256": bundle_sha,
                "remote_validation": validation_json,
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
                safe_remote_path(remote)
                remote_q = shlex.quote(remote)
                # Cleanup is permitted only after the remote operator exits; no
                # runner service or unrelated directory is inspected or changed.
                ssh(f"case {remote_q} in /Users/*/{REMOTE_ROOT}/run.*) "
                    f"rm -rf -- {remote_q} ;; *) exit 90 ;; esac", check=False)
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
