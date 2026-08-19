#!/usr/bin/env python3
"""Workload-free full-duplex and online-stream stress fixtures for v12."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import backref_cost_attribution_v12_admission as admission
import backref_cost_attribution_v12_transport as transport


ROOT = Path(__file__).resolve().parents[1]
STRESS_BYTES = 16 * 1024 * 1024 + 4096

CHILD_SOURCE = r'''
import json
import sys
import threading
import time
sys.path.insert(0, "scripts")
import backref_cost_attribution_v12_transport as transport

mode = sys.argv[1]
size = int(sys.argv[2])
received = [0]

def drain():
    while True:
        chunk = sys.stdin.buffer.read(65536)
        if not chunk:
            return
        received[0] += len(chunk)

def emit(kind, value, sequence):
    sys.stdout.buffer.write(transport.encode_frame(
        kind, transport.canonical_json(value), sequence=sequence))
    sys.stdout.buffer.flush()

reader = threading.Thread(target=drain)
reader.start()
if mode == "silent":
    reader.join()
    time.sleep(0.20)
sys.stdout.buffer.write(transport.MAGIC)
sys.stdout.buffer.flush()
emit("source-admission", {"status": "verified"}, 0)
emit("operator-status", {"status": "complete",
     "benchmark_lease_acquisition_attempted": False}, 1)
emit("archive-build", {"status": "accepted"}, 2)
emit("lease-state", {"state": "not-attempted"}, 3)
if mode == "control-stall":
    time.sleep(5)
archive_sha = transport.deterministic_payload_sha256(size)
declaration = {
    "archive_bytes": size, "archive_sha256": archive_sha,
    "chunk_bytes": transport.CHUNK_BYTES,
    "chunk_count": (size + transport.CHUNK_BYTES - 1) //
                   transport.CHUNK_BYTES,
    "inventory": {"status": "accepted", "members": []}}
emit("bulk-declaration", declaration, 4)
sequence = 5
chunks = transport.deterministic_payload_chunks(
    size, transport.CHUNK_BYTES)
if mode == "stall":
    first = next(chunks)
    sys.stdout.buffer.write(transport._frame_prefix(
        "bulk-chunk", len(first), transport.sha256_bytes(first),
        sequence=sequence, chunk_index=0))
    sys.stdout.buffer.write(first[:1024])
    sys.stdout.buffer.flush()
    time.sleep(5)
else:
    for index, chunk in enumerate(chunks):
        sys.stdout.buffer.write(transport.encode_frame(
            "bulk-chunk", chunk, sequence=sequence, chunk_index=index))
        sys.stdout.buffer.flush()
        sequence += 1
    emit("integrity-footer", {"status": "complete",
         "archive_sha256": archive_sha, "process_refusal": None,
         "process_refusal_sha256": None}, sequence)
    sequence += 1
    emit("cleanup-footer", {"status": "complete",
         "removed_exact_validated_child": True,
         "absence_proved": True}, sequence)
    reader.join()
    if received[0] < size:
        raise SystemExit(7)
'''


def request_chunks(size: int):
    chunk = b"R" * transport.IO_CHUNK_BYTES
    remaining = size
    while remaining:
        value = chunk[:min(len(chunk), remaining)]
        yield value
        remaining -= len(value)


def pump_fixture(mode: str, *, request_bytes: int, response_bytes: int,
                 silent_timeout: float = 2.0,
                 progress_timeout: float = 1.0):
    temporary = tempfile.TemporaryDirectory(prefix="attribution-v12-pump-")
    root = Path(temporary.name)
    observer = transport.OnlineResponseValidator(require_success=True)
    command = [sys.executable, "-c", CHILD_SOURCE, mode,
               str(response_bytes)]
    try:
        result = admission.pump_owned_full_duplex(
            command, request_chunks(request_bytes),
            stdout_path=root / "stdout.bin", stderr_path=root / "stderr.bin",
            absolute_timeout=20, silent_operator_timeout=silent_timeout,
            progress_timeout=progress_timeout, stdout_observer=observer)
    except Exception:
        temporary.cleanup()
        raise
    return temporary, root, observer, result


def simultaneous_duplex_contract() -> None:
    temporary, root, observer, result = pump_fixture(
        "duplex", request_bytes=STRESS_BYTES, response_bytes=STRESS_BYTES)
    try:
        parsed = observer.finalize()
        assert parsed["archive_bytes"] == STRESS_BYTES
        assert result.request_bytes == STRESS_BYTES
        assert result.stdout_bytes == (root / "stdout.bin").stat().st_size
        assert result.stderr_bytes == 0
        assert result.stdin_half_closed
        assert result.stdout_sha256 == hashlib.sha256(
            (root / "stdout.bin").read_bytes()).hexdigest()
        archive = root / "archive.bin"
        reparsed = transport.parse_response_file(
            root / "stdout.bin", archive, require_success=True)
        assert archive.stat().st_size == STRESS_BYTES
        assert reparsed["archive_sha256"] == hashlib.sha256(
            archive.read_bytes()).hexdigest()
    finally:
        temporary.cleanup()


def silent_operator_then_stream_contract() -> None:
    temporary, _, observer, result = pump_fixture(
        "silent", request_bytes=STRESS_BYTES,
        response_bytes=transport.CHUNK_BYTES,
        silent_timeout=1.0, progress_timeout=0.5)
    try:
        assert result.returncode == 0
        assert observer.finalize()["success"]
    finally:
        temporary.cleanup()


def partial_chunk_stall_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="attribution-v12-stall-") as raw:
        root = Path(raw)
        observer = transport.OnlineResponseValidator(require_success=True)
        try:
            admission.pump_owned_full_duplex(
                [sys.executable, "-c", CHILD_SOURCE, "stall",
                 str(transport.CHUNK_BYTES)],
                request_chunks(transport.CHUNK_BYTES),
                stdout_path=root / "stdout.bin",
                stderr_path=root / "stderr.bin", absolute_timeout=5,
                silent_operator_timeout=2, progress_timeout=0.20,
                stdout_observer=observer)
        except admission.OwnedTransportTimeout as error:
            assert error.phase == "bulk-progress"
            assert error.stdout_bytes == (root / "stdout.bin").stat().st_size
            assert observer.bulk_started
        else:
            raise AssertionError("partial bulk chunk stall was accepted")


def control_stream_stall_contract() -> None:
    with tempfile.TemporaryDirectory(
            prefix="attribution-v12-control-stall-") as raw:
        root = Path(raw)
        observer = transport.OnlineResponseValidator(require_success=True)
        try:
            admission.pump_owned_full_duplex(
                [sys.executable, "-c", CHILD_SOURCE, "control-stall",
                 str(transport.CHUNK_BYTES)],
                request_chunks(transport.CHUNK_BYTES),
                stdout_path=root / "stdout.bin",
                stderr_path=root / "stderr.bin", absolute_timeout=5,
                silent_operator_timeout=2, progress_timeout=0.20,
                stdout_observer=observer)
        except admission.OwnedTransportTimeout as error:
            assert error.phase == "response-progress"
            assert error.stdout_bytes == (root / "stdout.bin").stat().st_size
            assert not observer.bulk_started
        else:
            raise AssertionError("stalled control-plane stream was accepted")


def compact_response(*, cleanup: bool = True,
                     oversized: bool = False) -> bytes:
    archive = b"fixture"
    archive_bytes = (transport.MAX_ARCHIVE_BYTES + 1
                     if oversized else len(archive))
    archive_sha = transport.sha256_bytes(archive)
    frames = [
        ("source-admission", transport.canonical_json({"status": "verified"}),
         {"sequence": 0}),
        ("operator-status", transport.canonical_json({"status": "complete",
         "benchmark_lease_acquisition_attempted": False}), {"sequence": 1}),
        ("archive-build", transport.canonical_json({"status": "accepted"}),
         {"sequence": 2}),
        ("lease-state", transport.canonical_json({"state": "not-attempted"}),
         {"sequence": 3}),
        ("bulk-declaration", transport.canonical_json({
         "archive_bytes": archive_bytes, "archive_sha256": archive_sha,
         "chunk_bytes": transport.CHUNK_BYTES,
         "chunk_count": ((archive_bytes + transport.CHUNK_BYTES - 1) //
                         transport.CHUNK_BYTES), "inventory": {}}),
         {"sequence": 4}),
    ]
    if not oversized:
        frames.append(("bulk-chunk", archive,
                       {"sequence": 5, "chunk_index": 0}))
        sequence = 6
    else:
        sequence = 5
    frames.append(("integrity-footer", transport.canonical_json({
        "status": "complete", "archive_sha256": archive_sha,
        "process_refusal": None, "process_refusal_sha256": None}),
        {"sequence": sequence}))
    if cleanup:
        frames.append(("cleanup-footer", transport.canonical_json({
            "status": "complete", "removed_exact_validated_child": True,
            "absence_proved": True}), {"sequence": sequence + 1}))
    return transport.encode_stream(frames)


def rejected_online(value: bytes) -> None:
    validator = transport.OnlineResponseValidator(require_success=True)
    for offset in range(0, len(value), 37):
        validator.feed(value[offset:offset + 37])
    try:
        validator.finalize()
    except transport.FrameRefusal:
        return
    raise AssertionError("unsafe online response was accepted")


def online_refusal_contracts() -> None:
    complete = compact_response()
    truncated = complete[:-11]
    corrupt = bytearray(complete)
    marker = b"fixture"
    corrupt[bytes(corrupt).index(marker)] ^= 1
    rejected_online(truncated)
    rejected_online(bytes(corrupt))
    rejected_online(compact_response(cleanup=False))
    rejected_online(compact_response(oversized=True))


def main() -> int:
    simultaneous_duplex_contract()
    silent_operator_then_stream_contract()
    control_stream_stall_contract()
    partial_chunk_stall_contract()
    online_refusal_contracts()
    print("PASS: v12 incrementally pumps >=16 MiB in both directions, survives "
          "simultaneous duplex pressure, distinguishes silent operator, "
          "control-stream, and bulk progress, persists online hashes/counts, "
          "and rejects stalls/truncation/corruption/oversize/missing cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
