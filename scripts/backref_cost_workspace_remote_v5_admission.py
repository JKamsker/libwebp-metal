#!/usr/bin/env python3
"""Shared fail-closed source admission for remote-v5 rehearsal and execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = "pandocs-agent"
PATH_GUARD = ROOT / "scripts" / "backref_cost_workspace_remote_v5_paths.py"
IDENTITY_PATHS = (
    "CMakeLists.txt",
    "makefile.unix",
    "src/enc/backward_references_cost_enc.c",
    "src/enc/backref_cost_workspace_remote_v5_experiment_enc.c",
    "src/enc/backref_cost_workspace_remote_v5_experiment_enc.h",
    "tools/backref_cost_workspace_remote_v5_experiment_runner.c",
    "scripts/backref_cost_workspace_remote_v5_paths.py",
    "scripts/backref_cost_workspace_remote_v5_admission.py",
    "scripts/execute_backref_cost_workspace_remote_v5.py",
)
PROTOCOL_MANIFEST = ROOT / "scripts" / "backref_cost_workspace_remote_v5_manifest.json"
SCOPED_NAMES = {
    "source.bundle": ("verify.git", "source"),
    "malformed.bundle": ("malformed-verify.git", "malformed-source"),
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def run(argv: list[str], *, input_bytes: bytes | None = None,
        timeout: int = 1200, check: bool = True,
        cwd: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(argv, cwd=cwd, input=input_bytes, timeout=timeout,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{result.stdout.decode(errors='replace')}\n"
            f"stderr:\n{result.stderr.decode(errors='replace')}")
    return result


def ssh(script: str, *, input_bytes: bytes | None = None,
        timeout: int = 1200, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                HOST, script], input_bytes=input_bytes, timeout=timeout,
               check=check)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT,
                                   text=True).strip()


def remote_path_guard(command: str, *arguments: str) -> dict:
    argv = " ".join(shlex.quote(value) for value in (command, *arguments))
    result = ssh(f"python3 - {argv}", input_bytes=PATH_GUARD.read_bytes())
    return json.loads(result.stdout.decode())


def remote_process_guard() -> dict:
    result = ssh("ps -axo pid=,ppid=,state=,etime=,command=")
    text = result.stdout.decode(errors="replace")
    lines = text.splitlines()
    workers = [line for line in lines if "Runner.Worker" in line]
    patterns = (
        "_experiment_runner", "cache_size_serial_sweep_runner",
        "cache_size_single_pass_slab_runner", "metal_benchmark",
        "benchmark_metal", "metal_encode_batch_experiment",
        "metal_import_bench", "nvidia-smi", "nvcc", "cuda-memcheck",
    )
    conflicts = [line for line in lines
                 if any(pattern.lower() in line.lower() for pattern in patterns)]
    if workers:
        raise RuntimeError(
            "active Runner.Worker/job detected; runner services are untouched")
    if conflicts:
        raise RuntimeError("competing benchmark or CUDA process detected")
    return {
        "process_table_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "runner_worker_matches": workers,
        "benchmark_or_cuda_matches": conflicts,
        "runner_listener_present": "Runner.Listener" in text,
    }


def local_identity() -> tuple[str, str, dict[str, str]]:
    commit = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    if git("status", "--porcelain"):
        raise RuntimeError("source admission requires a clean local worktree")
    identity_paths = list(IDENTITY_PATHS)
    if PROTOCOL_MANIFEST.exists():
        protocol = json.loads(PROTOCOL_MANIFEST.read_text(encoding="utf-8"))
        identity_paths.extend(protocol["admission_identity_paths"])
    hashes = {}
    for relative in dict.fromkeys(identity_paths):
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"identity source is absent: {relative}")
        hashes[relative] = sha256(path)
    return commit, tree, hashes


def _validated_scoped_paths(run_directory: str, bundle_name: str) -> tuple[Path, Path, Path]:
    if bundle_name not in SCOPED_NAMES:
        raise RuntimeError("unrecognized scoped bundle name")
    run_path = Path(run_directory)
    if not run_path.is_absolute() or run_path.resolve() != run_path:
        raise RuntimeError("run directory must be absolute and canonical")
    verify_name, clone_name = SCOPED_NAMES[bundle_name]
    bundle = run_path / bundle_name
    verify = run_path / verify_name
    clone = run_path / clone_name
    for path in (bundle, verify, clone):
        if path.parent != run_path or path.name in ("", ".", ".."):
            raise RuntimeError("scoped admission path escaped run directory")
    return bundle, verify, clone


def remote_admit(run_directory: str, bundle_name: str, expected_sha256: str,
                 expected_commit: str, expected_tree: str,
                 expected_source_hashes: dict[str, str]) -> dict:
    bundle, verification_repository, clone = _validated_scoped_paths(
        run_directory, bundle_name)
    info = os.lstat(bundle)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("transferred bundle must be a regular non-symlink file")
    actual_bundle_sha = sha256(bundle)
    if actual_bundle_sha != expected_sha256:
        raise RuntimeError("transferred bundle SHA-256 mismatch")
    if os.path.lexists(verification_repository) or os.path.lexists(clone):
        raise RuntimeError("scoped verification repository or clone already exists")
    initialized = False
    try:
        run(["git", "init", "--bare", str(verification_repository)],
            cwd=Path(run_directory))
        initialized = True
        verify_result = run(
            ["git", "-C", str(verification_repository), "bundle", "verify",
             str(bundle)], check=False, cwd=Path(run_directory))
        if verify_result.returncode != 0:
            raise RuntimeError(
                "repository-context bundle verification rejected transfer: "
                + verify_result.stderr.decode(errors="replace").strip())
        shutil.rmtree(verification_repository)
        initialized = False
        run(["git", "clone", "--no-checkout", str(bundle), str(clone)],
            cwd=Path(run_directory))
        run(["git", "-C", str(clone), "checkout", "--detach", expected_commit],
            cwd=Path(run_directory))
        actual_commit = run(
            ["git", "-C", str(clone), "rev-parse", "HEAD"],
            cwd=Path(run_directory)).stdout.decode().strip()
        actual_tree = run(
            ["git", "-C", str(clone), "rev-parse", "HEAD^{tree}"],
            cwd=Path(run_directory)).stdout.decode().strip()
        status = run(
            ["git", "-C", str(clone), "status", "--porcelain=v1",
             "--untracked-files=all"], cwd=Path(run_directory)).stdout.decode()
        if actual_commit != expected_commit or actual_tree != expected_tree or status:
            raise RuntimeError("exact commit/tree/clean-status admission failed")
        actual_hashes = {}
        for relative, expected_hash in expected_source_hashes.items():
            path = clone / relative
            if not path.is_file():
                raise RuntimeError(f"admitted source is absent: {relative}")
            actual_hash = sha256(path)
            if actual_hash != expected_hash:
                raise RuntimeError(f"admitted source hash mismatch: {relative}")
            actual_hashes[relative] = actual_hash
        return {
            "bundle_path": str(bundle),
            "bundle_sha256": actual_bundle_sha,
            "bundle_hash_match": True,
            "bundle_verify_repository": str(verification_repository),
            "bundle_verify_command": [
                "git", "-C", str(verification_repository), "bundle", "verify",
                str(bundle),
            ],
            "bundle_verified_in_repository_context": True,
            "verification_repository_removed": not os.path.lexists(
                verification_repository),
            "clone": str(clone), "source_commit": actual_commit,
            "source_tree": actual_tree, "clean_status": True,
            "source_hashes": actual_hashes,
        }
    except Exception:
        if initialized and os.path.isdir(verification_repository):
            shutil.rmtree(verification_repository)
        if os.path.isdir(clone):
            shutil.rmtree(clone)
        raise


def invoke_remote_admit(run_directory: str, bundle_name: str,
                        bundle_sha256: str, commit: str, tree: str,
                        source_hashes: dict[str, str], *,
                        check: bool = True) -> subprocess.CompletedProcess[bytes]:
    arguments = (
        "remote-admit", run_directory, bundle_name, bundle_sha256, commit, tree,
        json.dumps(source_hashes, sort_keys=True, separators=(",", ":")),
    )
    argv = " ".join(shlex.quote(value) for value in arguments)
    return ssh(f"python3 - {argv}", input_bytes=Path(__file__).read_bytes(),
               check=check)


def cleanup_remote(home: str, safe_root: str, run_directory: str) -> dict:
    result = remote_path_guard("cleanup", home, safe_root, run_directory)
    if not result.get("removed_exact_validated_child") or not result.get(
            "absence_proved"):
        raise RuntimeError("remote exact-child cleanup proof failed")
    return result


def admit_source(*, exercise_malformed: bool) -> dict:
    commit, tree, source_hashes = local_identity()
    temporary = tempfile.TemporaryDirectory(prefix="remote-v5-admission-")
    temporary_path = Path(temporary.name)
    bundle = temporary_path / "source.bundle"
    malformed = temporary_path / "malformed.bundle"
    pretransfer_process = remote_process_guard()
    run(["git", "bundle", "create", str(bundle), "HEAD"])
    bundle_sha = sha256(bundle)
    generated = remote_path_guard("generate")
    home = generated["home"]
    safe_root = generated["safe_root"]
    remote = generated["run_directory"]
    remote_path_guard("validate", home, safe_root, remote)
    record = {
        "temporary": temporary,
        "home": home, "safe_root": safe_root, "run_directory": remote,
        "source_commit": commit, "source_tree": tree,
        "source_hashes": source_hashes, "source_bundle_sha256": bundle_sha,
        "path_generation": generated,
        "pretransfer_process_isolation": pretransfer_process,
    }
    try:
        run(["scp", "-q", str(bundle), f"{HOST}:{remote}/source.bundle"])
        remote_q = shlex.quote(remote)
        remote_bundle_sha = ssh(
            f"shasum -a 256 {remote_q}/source.bundle | awk '{{print $1}}'")
        observed = remote_bundle_sha.stdout.decode().strip()
        if observed != bundle_sha:
            raise RuntimeError("source bundle transfer hash mismatch")
        admission_result = invoke_remote_admit(
            remote, "source.bundle", bundle_sha, commit, tree, source_hashes)
        record["admission"] = json.loads(admission_result.stdout.decode())
        record["remote_source_bundle_sha256"] = observed
        if exercise_malformed:
            malformed.write_bytes(b"not a git bundle\n")
            malformed_sha = sha256(malformed)
            run(["scp", "-q", str(malformed),
                 f"{HOST}:{remote}/malformed.bundle"])
            remote_malformed_sha = ssh(
                f"shasum -a 256 {remote_q}/malformed.bundle | awk '{{print $1}}'")
            malformed_observed = remote_malformed_sha.stdout.decode().strip()
            if malformed_observed != malformed_sha:
                raise RuntimeError("malformed bundle transfer hash mismatch")
            rejected = invoke_remote_admit(
                remote, "malformed.bundle", malformed_sha, commit, tree,
                source_hashes, check=False)
            if rejected.returncode == 0:
                raise RuntimeError("malformed bundle was accepted")
            absence = ssh(
                f"test ! -e {remote_q}/malformed-verify.git && "
                f"test ! -e {remote_q}/malformed-source")
            record["malformed_bundle"] = {
                "local_sha256": malformed_sha,
                "remote_sha256": malformed_observed,
                "hash_match": True, "rejected": True,
                "exit_code": rejected.returncode,
                "stderr": rejected.stderr.decode(errors="replace"),
                "verification_repository_absent": absence.returncode == 0,
                "clone_absent": absence.returncode == 0,
            }
        record["post_admission_process_isolation"] = remote_process_guard()
        return record
    except Exception:
        cleanup_remote(home, safe_root, remote)
        temporary.cleanup()
        raise


def finish_admission(record: dict) -> dict:
    cleanup = cleanup_remote(record["home"], record["safe_root"],
                             record["run_directory"])
    record["temporary"].cleanup()
    record["finished"] = True
    return cleanup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    remote_parser = sub.add_parser("remote-admit")
    remote_parser.add_argument("run_directory")
    remote_parser.add_argument("bundle_name")
    remote_parser.add_argument("bundle_sha256")
    remote_parser.add_argument("expected_commit")
    remote_parser.add_argument("expected_tree")
    remote_parser.add_argument("source_hashes_json")
    args = parser.parse_args()
    if args.command == "remote-admit":
        result = remote_admit(
            args.run_directory, args.bundle_name, args.bundle_sha256,
            args.expected_commit, args.expected_tree,
            json.loads(args.source_hashes_json))
        print(json.dumps(result, sort_keys=True))
        return 0
    raise RuntimeError("unsupported admission command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
