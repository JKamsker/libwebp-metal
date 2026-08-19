#!/usr/bin/env python3
"""Local identity and direct-child ownership for attribution-v9 transport."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = "pandocs-agent"
IDENTITY_PATHS = (
    "CMakeLists.txt",
    "makefile.unix",
    "src/enc/backward_references_cost_enc.c",
    "src/enc/backward_references_cost_distance_only_enc.inc",
    "src/enc/backward_references_enc.c",
    "src/enc/profile_enc.c",
    "src/enc/profile_enc.h",
    "src/enc/vp8l_enc.c",
    "src/enc/backref_cost_attribution_v9_experiment_enc.c",
    "src/enc/backref_cost_attribution_v9_experiment_enc.h",
    "tools/backref_cost_attribution_v9_experiment_runner.c",
    "scripts/backref_cost_attribution_v9_paths.py",
    "scripts/backref_cost_attribution_v9_admission.py",
    "scripts/backref_cost_attribution_v9_transport.py",
    "scripts/execute_backref_cost_attribution_v9.py",
)
PROTOCOL_MANIFEST = ROOT / "scripts" / "backref_cost_attribution_v9_manifest.json"
SOURCE_RECEIPT_SCHEMA = \
    "libwebp-backref-cost-attribution-v9-source-admission-receipt-v1"
SOURCE_RECEIPT_VERSION = 1
FORBIDDEN_TERMINATION_COMMANDS = ("kill", "pkill", "killall")
OBSERVE_ONLY_EXTERNAL_PROCESS_CLASSES = (
    "ssh", "runner", "profiler", "editor", "user-shell", "service")


def _reject_generic_termination(argv: list[str]) -> None:
    for argument in argv:
        for command in FORBIDDEN_TERMINATION_COMMANDS:
            if re.search(rf"(?<![A-Za-z0-9_.-]){command}(?![A-Za-z0-9_.-])",
                         argument):
                raise RuntimeError(
                    f"generic process termination is forbidden: {command}")


@dataclass(frozen=True)
class _OwnedChild:
    """Creation provenance retained for one directly spawned subprocess."""

    process: subprocess.Popen
    pid: int
    creation_identity: int

    @classmethod
    def spawn(cls, argv: list[str], **kwargs) -> "_OwnedChild":
        _reject_generic_termination(argv)
        process = subprocess.Popen(argv, **kwargs)
        return cls(process=process, pid=process.pid,
                   creation_identity=id(process))

    def _assert_creation_identity(self) -> None:
        if id(self.process) != self.creation_identity or \
                self.process.pid != self.pid:
            raise RuntimeError("owned-child creation identity changed")

    def stop_after_timeout(self) -> None:
        """Signal only this retained direct-child handle, never a found PID."""
        self._assert_creation_identity()
        if self.process.poll() is None:
            self.process.kill()


def run_owned(argv: list[str], *, input_data=None, timeout: int = 1200,
              cwd: Path = ROOT, env: dict[str, str] | None = None,
              text: bool = False) -> subprocess.CompletedProcess:
    owned = _OwnedChild.spawn(
        argv, cwd=cwd, env=env, text=text,
        stdin=subprocess.PIPE if input_data is not None else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = owned.process.communicate(input_data, timeout=timeout)
    except subprocess.TimeoutExpired:
        owned.stop_after_timeout()
        owned.process.wait(timeout=5)
        for stream in (owned.process.stdin, owned.process.stdout,
                       owned.process.stderr):
            if stream is not None:
                stream.close()
        raise
    return subprocess.CompletedProcess(argv, owned.process.returncode,
                                       stdout, stderr)


def run(argv: list[str], *, input_bytes: bytes | None = None,
        timeout: int = 1200, check: bool = True,
        cwd: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    result = run_owned(argv, cwd=cwd, input_data=input_bytes, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{result.stdout.decode(errors='replace')}\n"
            f"stderr:\n{result.stderr.decode(errors='replace')}")
    return result


def git(*args: str) -> str:
    result = run_owned(["git", *args], cwd=ROOT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout.strip()


def git_bytes(*args: str) -> bytes:
    result = run_owned(["git", *args], cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def local_identity(source_commit: str | None = None) -> tuple[str, str, dict[str, str]]:
    """Hash exact committed 1A source even when authority HEAD is 1B."""
    head = git("rev-parse", "HEAD")
    commit = git("rev-parse", f"{source_commit or head}^{{commit}}")
    tree = git("rev-parse", f"{commit}^{{tree}}")
    if git("status", "--porcelain"):
        raise RuntimeError("source admission requires a clean local worktree")
    identity_paths = list(IDENTITY_PATHS)
    if PROTOCOL_MANIFEST.exists():
        protocol = json.loads(PROTOCOL_MANIFEST.read_text(encoding="utf-8"))
        identity_paths.extend(protocol["admission_identity_paths"])
    hashes: dict[str, str] = {}
    for relative in dict.fromkeys(identity_paths):
        exists = run_owned(["git", "cat-file", "-e", f"{commit}:{relative}"],
                           cwd=ROOT)
        if exists.returncode != 0:
            raise RuntimeError(f"identity source is absent: {relative}")
        hashes[relative] = sha256_bytes(git_bytes("show", f"{commit}:{relative}"))
    return commit, tree, hashes


def create_source_bundle() -> tuple[bytes, str]:
    """Create an immutable bundle containing authority HEAD and its ancestry."""
    with tempfile.TemporaryDirectory(prefix="attribution-v9-bundle-") as raw:
        path = Path(raw) / "source.bundle"
        run(["git", "bundle", "create", str(path), "HEAD"])
        value = path.read_bytes()
    return value, sha256_bytes(value)
