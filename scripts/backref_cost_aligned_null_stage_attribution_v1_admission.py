#!/usr/bin/env python3
"""Local identity and direct-child ownership for stage-attribution-v1."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import re
import selectors
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v1_transport as transport


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
    "src/enc/backref_cost_aligned_null_stage_attribution_v1_experiment_enc.c",
    "src/enc/backref_cost_aligned_null_stage_attribution_v1_experiment_enc.h",
    "src/enc/backref_cost_alignment_v4_layout_clone_enc.inc",
    "tools/backref_cost_aligned_null_stage_attribution_v1_experiment_runner.c",
    "scripts/backref_cost_aligned_null_stage_attribution_v1_paths.py",
    "scripts/backref_cost_aligned_null_stage_attribution_v1_admission.py",
    "scripts/backref_cost_aligned_null_stage_attribution_v1_transport.py",
    "scripts/backref_cost_aligned_null_stage_attribution_v1_bootstrap.py",
    "scripts/backref_cost_aligned_null_stage_attribution_v1_payload.py",
    "scripts/execute_backref_cost_aligned_null_stage_attribution_v1.py",
)
PROTOCOL_MANIFEST = ROOT / "scripts" / "backref_cost_aligned_null_stage_attribution_v1_manifest.json"
SOURCE_RECEIPT_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v1-source-admission-receipt-v1"
SOURCE_RECEIPT_VERSION = 1
FORBIDDEN_TERMINATION_COMMANDS = ("kill", "pkill", "killall")
OBSERVE_ONLY_EXTERNAL_PROCESS_CLASSES = (
    "ssh", "runner", "profiler", "editor", "user-shell", "service")
PROCESS_CREATED = "PROCESS_CREATED"
CONNECT_CHANNEL_READY = "CONNECT_CHANNEL_READY"
REQUEST_DECLARATION = "REQUEST_DECLARATION"
REQUEST_CHUNK = "REQUEST_CHUNK"
REQUEST_COMPLETE = "REQUEST_COMPLETE"
SILENT_OPERATOR = "SILENT_OPERATOR"
RESPONSE_STREAM = "RESPONSE_STREAM"
COMPLETE = "COMPLETE"
PROTOCOL_REFUSAL_DRAIN = "PROTOCOL_REFUSAL_DRAIN"
ABSOLUTE_TRANSACTION = "ABSOLUTE_TRANSACTION"
MAX_TRANSPORT_STDERR_BYTES = 256 * 1024


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
    transport_child: bool = False

    @classmethod
    def spawn(cls, argv: list[str], *, transport_child: bool = False,
              **kwargs) -> "_OwnedChild":
        _reject_generic_termination(argv)
        process = subprocess.Popen(argv, **kwargs)
        return cls(process=process, pid=process.pid,
                   creation_identity=id(process),
                   transport_child=transport_child)

    def _assert_creation_identity(self) -> None:
        if id(self.process) != self.creation_identity or \
                self.process.pid != self.pid:
            raise RuntimeError("owned-child creation identity changed")

    def stop_after_timeout(self) -> None:
        """Signal only this retained direct-child handle, never a found PID."""
        self._assert_creation_identity()
        if not self.transport_child:
            raise RuntimeError("only the retained transport child may be stopped")
        if self.process.poll() is None:
            self.process.kill()


@dataclass(frozen=True)
class ChannelPumpResult:
    """Phase-observable accounting for one directly owned SSH child."""

    args: list[str]
    returncode: int
    process_created: bool
    process_pid: int
    ready_receipt: dict
    channel_established: bool
    request_payload_bytes: int
    request_payload_sha256: str
    request_wire_bytes: int
    request_wire_sha256: str
    request_declaration_bytes: int
    request_declaration_sha256: str
    request_chunks_written: int
    request_chunks_acked: int
    request_bytes_acked: int
    request_complete_receipt: dict
    response_declaration: dict
    response_complete_receipt: dict
    response_bytes: int
    response_sha256: str
    stdout_bytes: int
    stdout_sha256: str
    stderr_bytes: int
    stderr_sha256: str
    elapsed_ns: int
    stdin_half_closed: bool


class OwnedTransportTimeout(subprocess.TimeoutExpired):
    """A bounded timeout carrying the exact phase and online byte counts."""

    def __init__(self, cmd: list[str], timeout: float, *, phase: str,
                 deadline_kind: str,
                 request_bytes: int, stdout_bytes: int, stderr_bytes: int,
                 channel_established: bool):
        super().__init__(cmd, timeout)
        self.phase = phase
        self.deadline_kind = deadline_kind
        self.request_bytes = request_bytes
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.channel_established = channel_established


class TransportDeadlineStateMachine:
    """Pure V3 phase deadlines; no request byte may precede READY."""

    def __init__(self, started: float, *, absolute_timeout: float,
                 ready_timeout: float, request_progress_timeout: float,
                 silent_operator_timeout: float,
                 response_progress_timeout: float):
        if min(absolute_timeout, ready_timeout, request_progress_timeout,
               silent_operator_timeout, response_progress_timeout) <= 0:
            raise ValueError("transport deadlines must be positive")
        self.state = CONNECT_CHANNEL_READY
        self.absolute_deadline = started + absolute_timeout
        self.phase_deadline = started + ready_timeout
        self.deadline_kind = "connect-channel-ready"
        self.request_progress_timeout = request_progress_timeout
        self.silent_operator_timeout = silent_operator_timeout
        self.response_progress_timeout = response_progress_timeout

    def transition(self, now: float, state: str) -> None:
        allowed = {
            CONNECT_CHANNEL_READY: {REQUEST_DECLARATION, PROTOCOL_REFUSAL_DRAIN},
            REQUEST_DECLARATION: {REQUEST_CHUNK, PROTOCOL_REFUSAL_DRAIN},
            REQUEST_CHUNK: {REQUEST_CHUNK, REQUEST_COMPLETE,
                            PROTOCOL_REFUSAL_DRAIN},
            REQUEST_COMPLETE: {SILENT_OPERATOR, PROTOCOL_REFUSAL_DRAIN},
            SILENT_OPERATOR: {RESPONSE_STREAM, PROTOCOL_REFUSAL_DRAIN},
            RESPONSE_STREAM: {RESPONSE_STREAM, COMPLETE,
                              PROTOCOL_REFUSAL_DRAIN},
            COMPLETE: {COMPLETE, PROTOCOL_REFUSAL_DRAIN},
            PROTOCOL_REFUSAL_DRAIN: {PROTOCOL_REFUSAL_DRAIN},
        }
        if state not in allowed.get(self.state, set()):
            raise RuntimeError(f"invalid request-channel transition: {self.state}->{state}")
        self.state = state
        if state == SILENT_OPERATOR:
            self.phase_deadline = now + self.silent_operator_timeout
            self.deadline_kind = "silent-operator"
        elif state == RESPONSE_STREAM:
            self.phase_deadline = now + self.response_progress_timeout
            self.deadline_kind = "response-progress"
        elif state == COMPLETE:
            self.phase_deadline = now + self.response_progress_timeout
            self.deadline_kind = "response-process-exit"
        elif state == PROTOCOL_REFUSAL_DRAIN:
            self.phase_deadline = now + self.request_progress_timeout
            self.deadline_kind = "protocol-refusal-drain"
        else:
            self.phase_deadline = now + self.request_progress_timeout
            self.deadline_kind = (
                "request-declaration-progress" if state == REQUEST_DECLARATION
                else "request-chunk-progress" if state == REQUEST_CHUNK
                else "request-complete-ack")

    def progress(self, now: float) -> None:
        if self.state in (REQUEST_DECLARATION, REQUEST_CHUNK, REQUEST_COMPLETE,
                          PROTOCOL_REFUSAL_DRAIN):
            self.phase_deadline = now + self.request_progress_timeout
        elif self.state in (RESPONSE_STREAM, COMPLETE):
            self.phase_deadline = now + self.response_progress_timeout

    def deadline_and_kind(self) -> tuple[float, str]:
        return min((self.absolute_deadline, ABSOLUTE_TRANSACTION),
                   (self.phase_deadline, self.deadline_kind))

    def expired(self, now: float) -> bool:
        return now >= self.deadline_and_kind()[0]


def pump_owned_request_channel(
        argv: list[str], request: transport.ChannelRequest, *,
        observer: transport.OnlineChannelValidator, stdout_path: Path,
        stderr_path: Path, response_path: Path, absolute_timeout: float,
        ready_timeout: float, request_progress_timeout: float,
        silent_operator_timeout: float, response_progress_timeout: float,
        cwd: Path = ROOT, env: dict[str, str] | None = None) -> ChannelPumpResult:
    """Wait for READY, then ACK-gate every write while draining both outputs."""
    if stdout_path.exists() or stderr_path.exists():
        raise RuntimeError("raw transport outputs must be new files")
    if response_path.exists():
        raise RuntimeError("reconstructed response target must be new")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    owned = _OwnedChild.spawn(
        argv, cwd=cwd, env=env, bufsize=0, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        transport_child=True)
    process = owned.process
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise RuntimeError("direct transport child lacks required pipes")
    selector = selectors.DefaultSelector()
    for stream in (process.stdin, process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    pending = memoryview(b"")
    pending_label: str | None = None
    wire_digest = hashlib.sha256()
    stdout_digest = hashlib.sha256()
    stderr_digest = hashlib.sha256()
    wire_count = stdout_count = stderr_count = 0
    stdin_half_closed = False
    declaration_queued = False
    chunks_queued = 0
    chunks_written = 0
    local_error: str | None = None
    started = time.monotonic()
    deadlines = TransportDeadlineStateMachine(
        started, absolute_timeout=absolute_timeout,
        ready_timeout=ready_timeout,
        request_progress_timeout=request_progress_timeout,
        silent_operator_timeout=silent_operator_timeout,
        response_progress_timeout=response_progress_timeout)

    def close_stdin() -> None:
        nonlocal stdin_half_closed
        if stdin_half_closed:
            return
        try:
            selector.unregister(process.stdin)
        except KeyError:
            pass
        process.stdin.close()
        stdin_half_closed = True

    def queue(value: bytes, label: str) -> None:
        nonlocal pending, pending_label
        if pending or stdin_half_closed:
            raise RuntimeError("request channel attempted overlapping writes")
        pending = memoryview(value)
        pending_label = label
        try:
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        except KeyError:
            pass

    def adopt_observer(now: float) -> None:
        nonlocal declaration_queued, chunks_queued, local_error
        if observer.error is not None and local_error is None:
            local_error = observer.error
            close_stdin()
            if deadlines.state != PROTOCOL_REFUSAL_DRAIN:
                deadlines.transition(now, PROTOCOL_REFUSAL_DRAIN)
            return
        if observer.ready is not None and not declaration_queued:
            declaration_queued = True
            deadlines.transition(now, REQUEST_DECLARATION)
            queue(transport.CHANNEL_MAGIC + transport.encode_frame(
                "request-declaration", request.declaration_payload,
                sequence=0), "declaration")
            return
        if observer.declaration_acked and chunks_queued == 0 and not pending:
            deadlines.transition(now, REQUEST_CHUNK)
            chunk = request.value[:transport.REQUEST_CHUNK_BYTES]
            chunks_queued = 1
            queue(transport.encode_frame(
                "request-chunk", chunk, sequence=1, chunk_index=0), "chunk")
            return
        if observer.request_chunks_acked == chunks_queued and \
                0 < chunks_queued < request.chunk_count and not pending:
            deadlines.transition(now, REQUEST_CHUNK)
            offset = chunks_queued * transport.REQUEST_CHUNK_BYTES
            chunk = request.value[offset:offset + transport.REQUEST_CHUNK_BYTES]
            index = chunks_queued
            chunks_queued += 1
            queue(transport.encode_frame(
                "request-chunk", chunk, sequence=index + 1,
                chunk_index=index), "chunk")
            return
        if chunks_queued == request.chunk_count and not pending and \
                not stdin_half_closed:
            close_stdin()
            deadlines.transition(now, REQUEST_COMPLETE)
        if observer.request_complete is not None and \
                deadlines.state == REQUEST_COMPLETE:
            deadlines.transition(now, SILENT_OPERATOR)
        if observer.response_declaration is not None and \
                deadlines.state == SILENT_OPERATOR:
            deadlines.transition(now, RESPONSE_STREAM)
        if observer.complete and deadlines.state == RESPONSE_STREAM:
            deadlines.transition(now, COMPLETE)

    try:
        with stdout_path.open("xb") as stdout_file, \
                stderr_path.open("xb") as stderr_file:
            while selector.get_map():
                adopt_observer(time.monotonic())
                deadline, deadline_kind = deadlines.deadline_and_kind()
                phase = deadlines.state
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OwnedTransportTimeout(
                        argv, absolute_timeout, phase=phase,
                        deadline_kind=deadline_kind,
                        request_bytes=observer.request_bytes_acked,
                        stdout_bytes=stdout_count,
                        stderr_bytes=stderr_count,
                        channel_established=observer.ready is not None)
                events = selector.select(remaining)
                if not events:
                    deadline, deadline_kind = deadlines.deadline_and_kind()
                    phase = deadlines.state
                    if time.monotonic() >= deadline:
                        raise OwnedTransportTimeout(
                            argv, absolute_timeout, phase=phase,
                            deadline_kind=deadline_kind,
                            request_bytes=observer.request_bytes_acked,
                            stdout_bytes=stdout_count,
                            stderr_bytes=stderr_count,
                            channel_established=observer.ready is not None)
                    continue
                for key, _ in events:
                    stream = key.fileobj
                    if key.data == "stdin":
                        if not pending or stdin_half_closed:
                            continue
                        try:
                            written = os.write(stream.fileno(), pending)
                        except BrokenPipeError:
                            selector.unregister(stream)
                            stream.close()
                            stdin_half_closed = True
                            local_error = "request channel broke stdin before completion"
                            deadlines.transition(
                                time.monotonic(), PROTOCOL_REFUSAL_DRAIN)
                            continue
                        if written:
                            piece = pending[:written]
                            wire_digest.update(piece)
                            wire_count += written
                            pending = pending[written:]
                            deadlines.progress(time.monotonic())
                            if not pending:
                                selector.unregister(stream)
                                if pending_label == "chunk":
                                    chunks_written += 1
                                pending_label = None
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
                            previous_response = len(observer.response)
                            observer.feed(data)
                            adopt_observer(time.monotonic())
                            if len(observer.response) > previous_response and \
                                    deadlines.state == RESPONSE_STREAM:
                                deadlines.progress(time.monotonic())
                        else:
                            stderr_file.write(data)
                            stderr_file.flush()
                            stderr_digest.update(data)
                            stderr_count += len(data)
                            if stderr_count > MAX_TRANSPORT_STDERR_BYTES and \
                                    local_error is None:
                                local_error = "transport stderr exceeds frozen cap"
                                close_stdin()
                                if deadlines.state != PROTOCOL_REFUSAL_DRAIN:
                                    deadlines.transition(
                                        time.monotonic(),
                                        PROTOCOL_REFUSAL_DRAIN)
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
    if local_error is not None:
        raise transport.FrameRefusal(local_error)
    channel = observer.finalize()
    response = channel["response"]
    response_path.write_bytes(response)
    return ChannelPumpResult(
        args=argv, returncode=returncode, process_created=True,
        process_pid=owned.pid, ready_receipt=channel["ready"],
        channel_established=True,
        request_payload_bytes=len(request.value),
        request_payload_sha256=request.declaration["request_sha256"],
        request_wire_bytes=wire_count,
        request_wire_sha256=wire_digest.hexdigest(),
        request_declaration_bytes=len(request.declaration_payload),
        request_declaration_sha256=request.declaration_sha256,
        request_chunks_written=chunks_written,
        request_chunks_acked=channel["request_chunks_acked"],
        request_bytes_acked=channel["request_bytes_acked"],
        request_complete_receipt=channel["request_complete"],
        response_declaration=channel["response_declaration"],
        response_complete_receipt=channel["response_complete"],
        response_bytes=len(response), response_sha256=hashlib.sha256(
            response).hexdigest(), stdout_bytes=stdout_count,
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
    # Non-transport children are never signaled. The single locally retained
    # SSH transport has the separately bounded pump above; ordinary local and
    # remote operator commands run to natural completion under that outer bound.
    stdout, stderr = owned.process.communicate(input_data)
    return subprocess.CompletedProcess(argv, owned.process.returncode,
                                       stdout, stderr)


CHILD_START_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v1-child-start-v1"
CHILD_RECEIPT_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v1-child-receipt-v1"


def validate_runner_start_receipt(receipt: dict, *, ordinal: int, pid: int,
                                  parent_pid: int, creation_identity: str,
                                  variant: str, case_id: str, method: int,
                                  lifecycle: str, purpose: str,
                                  prior: list[dict]) -> None:
    """Validate a child-authored start receipt before authorizing any work."""
    exact = {
        "schema": CHILD_START_SCHEMA, "ordinal": ordinal, "pid": pid,
        "ppid_observed": parent_pid, "creation_identity": creation_identity,
        "variant": variant, "case_id": case_id, "method": method,
        "lifecycle": lifecycle, "purpose": purpose, "shell": False,
        "wrapper": False, "grandchild": False,
    }
    for name, value in exact.items():
        if receipt.get(name) != value:
            raise RuntimeError(f"direct-child start receipt mismatch: {name}")
    start_token = receipt.get("start_token")
    if not isinstance(start_token, str) or not start_token.isdigit() or \
            int(start_token) <= 0:
        raise RuntimeError("direct-child start token is invalid")
    if any(row.get("ordinal") == ordinal for row in prior):
        raise RuntimeError("duplicate direct-child ordinal")
    if any(row.get("pid") == pid and row.get("start_token") == start_token
           for row in prior):
        raise RuntimeError("reused direct-child PID/start identity")


class DirectRunnerLedger:
    """Online fail-closed serial ownership for encoder-runner children only."""

    def __init__(self, path: Path, expected_executables: tuple[Path, ...]):
        self.path = path
        self.expected_executables = tuple(path.resolve()
                                          for path in expected_executables)
        self.receipts: list[dict] = []
        self.live: subprocess.Popen[str] | None = None
        if path.exists():
            raise RuntimeError("direct-child receipt ledger must be new")
        path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, value: dict) -> None:
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")

    def run(self, argv: list[str], *, cwd: Path, env: dict[str, str],
            variant: str, case_id: str, method: int, lifecycle: str,
            purpose: str, start_timeout: float = 15.0
            ) -> subprocess.CompletedProcess[str]:
        if self.live is not None:
            if self.live.poll() is None:
                raise RuntimeError("direct-child overlap attempt")
            raise RuntimeError("previous direct child was not reaped")
        if not argv or Path(argv[0]).resolve() not in self.expected_executables:
            raise RuntimeError("runner child executable/wrapper mismatch")
        if any(token in ("sh", "bash", "zsh", "env")
               for token in (Path(argv[0]).name,)):
            raise RuntimeError("shell/wrapper runner launch is forbidden")
        ordinal = len(self.receipts)
        creation_identity = secrets.token_hex(24)
        child_env = dict(env)
        child_env.update({
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_DIRECT_CHILD": "1",
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_ORDINAL": str(ordinal),
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_CREATION_TOKEN": creation_identity,
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_PURPOSE": purpose,
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_LIFECYCLE": lifecycle,
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_CASE_ID": case_id,
            "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V1_CHILD_METHOD": str(method),
        })
        started_ns = time.monotonic_ns()
        process = subprocess.Popen(
            argv, cwd=cwd, env=child_env, shell=False, text=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True, start_new_session=False)
        self.live = process
        if process.stdin is None or process.stdout is None or \
                process.stderr is None:
            raise RuntimeError("direct child lacks retained standard streams")
        selector = selectors.DefaultSelector()
        selector.register(process.stderr, selectors.EVENT_READ)
        try:
            events = selector.select(start_timeout)
        finally:
            selector.close()
        if not events:
            process.stdin.close()  # EOF releases the unadmitted child; no signal.
            process.wait()
            self.live = None
            raise RuntimeError("direct-child start receipt timeout")
        line = process.stderr.readline()
        try:
            start_receipt = json.loads(line)
            validate_runner_start_receipt(
                start_receipt, ordinal=ordinal, pid=process.pid,
                parent_pid=os.getpid(), creation_identity=creation_identity,
                variant=variant, case_id=case_id, method=method,
                lifecycle=lifecycle, purpose=purpose, prior=self.receipts)
        except Exception:
            process.stdin.close()  # Fail before workload; child observes EOF.
            process.wait()
            self.live = None
            raise
        process.stdin.write(f"GO {creation_identity}\n")
        process.stdin.flush()
        process.stdin.close()
        stdout = process.stdout.read()
        stderr = process.stderr.read()
        returncode = process.wait()
        ended_ns = time.monotonic_ns()
        receipt = {
            **start_receipt, "start_receipt_schema": start_receipt["schema"],
            "schema": CHILD_RECEIPT_SCHEMA,
            "operator_pid": os.getpid(), "ppid_expected": os.getpid(),
            "argv": list(argv), "env": dict(sorted(child_env.items())),
            "cwd": str(cwd.resolve()), "shell_disabled": True,
            "start_new_session": False, "authorized_before_work": True,
            "started_monotonic_ns": started_ns,
            "ended_monotonic_ns": ended_ns, "exit_code": returncode,
            "exited": True, "reaped": True,
            "stdout_bytes": len(stdout.encode()),
            "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
            "stderr_bytes": len(stderr.encode()),
            "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
            "at_most_one_owned_child_live": True,
            "previous_child_exited_and_reaped": True,
            "discovery_used_for_ownership": False,
        }
        self.receipts.append(receipt)
        self._append(receipt)
        self.live = None
        return subprocess.CompletedProcess(argv, returncode, stdout, stderr)

    def finalize(self, expected_count: int) -> dict:
        if self.live is not None:
            raise RuntimeError("direct-child ledger finalized with live child")
        if len(self.receipts) != expected_count or \
                [row["ordinal"] for row in self.receipts] != \
                list(range(expected_count)) or \
                any(not row["exited"] or not row["reaped"]
                    for row in self.receipts):
            raise RuntimeError("direct-child receipt inventory is incomplete")
        return {"schema":
                "libwebp-backref-cost-aligned-null-stage-attribution-v1-child-summary-v1",
                "status": "PASS", "receipts": len(self.receipts),
                "ordinals_contiguous": True, "maximum_live_children": 1,
                "all_direct_parent_edges_verified_online": True,
                "all_exited_and_reaped_before_successor": True,
                "shell_wrapper_grandchild_launches": 0,
                "discovered_pid_signals": 0}


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
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v1-bundle-") as raw:
        path = Path(raw) / "source.bundle"
        run(["git", "bundle", "create", str(path), "HEAD"])
        value = path.read_bytes()
    return value, sha256_bytes(value)
