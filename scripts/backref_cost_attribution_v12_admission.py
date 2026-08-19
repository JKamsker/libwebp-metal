#!/usr/bin/env python3
"""Local identity and direct-child ownership for attribution-v12 transport."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import re
import selectors
import subprocess
import tempfile
import time
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
    "src/enc/backref_cost_attribution_v12_experiment_enc.c",
    "src/enc/backref_cost_attribution_v12_experiment_enc.h",
    "tools/backref_cost_attribution_v12_experiment_runner.c",
    "scripts/backref_cost_attribution_v12_paths.py",
    "scripts/backref_cost_attribution_v12_admission.py",
    "scripts/backref_cost_attribution_v12_transport.py",
    "scripts/execute_backref_cost_attribution_v12.py",
)
PROTOCOL_MANIFEST = ROOT / "scripts" / "backref_cost_attribution_v12_manifest.json"
SOURCE_RECEIPT_SCHEMA = \
    "libwebp-backref-cost-attribution-v12-source-admission-receipt-v1"
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


@dataclass(frozen=True)
class PumpResult:
    """Online byte accounting for one directly owned full-duplex child."""

    args: list[str]
    returncode: int
    request_bytes: int
    request_sha256: str
    stdout_bytes: int
    stdout_sha256: str
    stderr_bytes: int
    stderr_sha256: str
    elapsed_ns: int
    stdin_half_closed: bool


class OwnedTransportTimeout(subprocess.TimeoutExpired):
    """A bounded timeout carrying the exact phase and online byte counts."""

    def __init__(self, cmd: list[str], timeout: float, *, phase: str,
                 request_bytes: int, stdout_bytes: int, stderr_bytes: int):
        super().__init__(cmd, timeout)
        self.phase = phase
        self.request_bytes = request_bytes
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes


def pump_owned_full_duplex(
        argv: list[str], request_chunks, *, stdout_path: Path,
        stderr_path: Path, absolute_timeout: float,
        silent_operator_timeout: float, progress_timeout: float,
        stdout_observer=None, cwd: Path = ROOT,
        env: dict[str, str] | None = None) -> PumpResult:
    """Incrementally write stdin while concurrently draining both outputs.

    Only a deadline expiry invokes ``stop_after_timeout``. Protocol rejection,
    child failure, and broken pipes are observed and drained without signaling.
    """
    if min(absolute_timeout, silent_operator_timeout, progress_timeout) <= 0:
        raise ValueError("transport deadlines must be positive")
    if stdout_path.exists() or stderr_path.exists():
        raise RuntimeError("raw transport outputs must be new files")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    owned = _OwnedChild.spawn(
        argv, cwd=cwd, env=env, bufsize=0, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process = owned.process
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise RuntimeError("direct transport child lacks required pipes")
    selector = selectors.DefaultSelector()
    for stream in (process.stdin, process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
    selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    iterator = iter(request_chunks)
    pending = memoryview(b"")
    request_digest = hashlib.sha256()
    stdout_digest = hashlib.sha256()
    stderr_digest = hashlib.sha256()
    request_count = stdout_count = stderr_count = 0
    stdin_half_closed = False
    started = time.monotonic()
    absolute_deadline = started + absolute_timeout
    write_deadline = started + progress_timeout
    operator_deadline = None
    response_deadline = None
    bulk_deadline = None

    def bulk_started() -> bool:
        return bool(stdout_observer is not None and
                    getattr(stdout_observer, "bulk_started", False))

    def deadline_and_phase() -> tuple[float, str]:
        candidates = [(absolute_deadline, "absolute-transaction")]
        if not stdin_half_closed:
            candidates.append((write_deadline, "request-progress"))
        elif bulk_started():
            candidates.append((bulk_deadline, "bulk-progress"))
        elif stdout_count:
            candidates.append((response_deadline, "response-progress"))
        else:
            candidates.append((operator_deadline, "silent-operator"))
        return min(candidates, key=lambda item: item[0])

    try:
        with stdout_path.open("xb") as stdout_file, \
                stderr_path.open("xb") as stderr_file:
            while selector.get_map():
                deadline, phase = deadline_and_phase()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OwnedTransportTimeout(
                        argv, absolute_timeout, phase=phase,
                        request_bytes=request_count,
                        stdout_bytes=stdout_count,
                        stderr_bytes=stderr_count)
                events = selector.select(remaining)
                if not events:
                    deadline, phase = deadline_and_phase()
                    if time.monotonic() >= deadline:
                        raise OwnedTransportTimeout(
                            argv, absolute_timeout, phase=phase,
                            request_bytes=request_count,
                            stdout_bytes=stdout_count,
                            stderr_bytes=stderr_count)
                    continue
                for key, _ in events:
                    stream = key.fileobj
                    if key.data == "stdin":
                        while not pending:
                            try:
                                pending = memoryview(next(iterator))
                            except StopIteration:
                                selector.unregister(stream)
                                stream.close()
                                stdin_half_closed = True
                                operator_deadline = (time.monotonic() +
                                                     silent_operator_timeout)
                                if stdout_count:
                                    response_deadline = (time.monotonic() +
                                                         progress_timeout)
                                break
                            if not isinstance(pending.obj, bytes):
                                raise TypeError("request chunks must be bytes")
                        if stdin_half_closed:
                            continue
                        try:
                            written = os.write(stream.fileno(), pending)
                        except BrokenPipeError:
                            selector.unregister(stream)
                            stream.close()
                            stdin_half_closed = True
                            operator_deadline = (time.monotonic() +
                                                 silent_operator_timeout)
                            continue
                        if written:
                            piece = pending[:written]
                            request_digest.update(piece)
                            request_count += written
                            pending = pending[written:]
                            write_deadline = time.monotonic() + progress_timeout
                    else:
                        try:
                            data = os.read(stream.fileno(), 256 * 1024)
                        except BlockingIOError:
                            continue
                        if not data:
                            selector.unregister(stream)
                            stream.close()
                            continue
                        if key.data == "stdout":
                            stdout_file.write(data)
                            stdout_file.flush()
                            stdout_digest.update(data)
                            stdout_count += len(data)
                            response_deadline = (time.monotonic() +
                                                 progress_timeout)
                            if stdout_observer is not None:
                                stdout_observer.feed(data)
                            if bulk_started():
                                bulk_deadline = time.monotonic() + progress_timeout
                        else:
                            stderr_file.write(data)
                            stderr_file.flush()
                            stderr_digest.update(data)
                            stderr_count += len(data)
            returncode = process.wait(timeout=5)
    except OwnedTransportTimeout:
        owned.stop_after_timeout()
        process.wait(timeout=5)
        raise
    finally:
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
    return PumpResult(
        args=argv, returncode=returncode, request_bytes=request_count,
        request_sha256=request_digest.hexdigest(), stdout_bytes=stdout_count,
        stdout_sha256=stdout_digest.hexdigest(), stderr_bytes=stderr_count,
        stderr_sha256=stderr_digest.hexdigest(),
        elapsed_ns=int((time.monotonic() - started) * 1_000_000_000),
        stdin_half_closed=stdin_half_closed)


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
    with tempfile.TemporaryDirectory(prefix="attribution-v12-bundle-") as raw:
        path = Path(raw) / "source.bundle"
        run(["git", "bundle", "create", str(path), "HEAD"])
        value = path.read_bytes()
    return value, sha256_bytes(value)
