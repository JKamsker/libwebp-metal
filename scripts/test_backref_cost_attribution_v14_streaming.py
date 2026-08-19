#!/usr/bin/env python3
"""Workload-free V14 duplex, deadline-state, and online-stream fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

import backref_cost_attribution_v14_admission as admission
import backref_cost_attribution_v14_transport as transport


REQUEST_STRESS_BYTES = 2 * 1024 * 1024 + 4096
RESPONSE_STRESS_BYTES = 512 * 1024 + 4096

CHILD_SOURCE = r'''
import sys
import threading
import time
sys.path.insert(0, "scripts")
import backref_cost_attribution_v14_transport as transport

mode = sys.argv[1]
size = int(sys.argv[2])
expected_request = int(sys.argv[3])
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
archive_sha = transport.deterministic_payload_sha256(size)
declaration = {
    "schema": transport.BULK_DECLARATION_SCHEMA,
    "status": "accepted", "compression_format": "tar+gzip",
    "archive_bytes": size, "archive_sha256": archive_sha,
    "chunk_bytes": transport.CHUNK_BYTES,
    "chunk_count": (size + transport.CHUNK_BYTES - 1) //
                   transport.CHUNK_BYTES,
    "inventory": {
        "schema": "libwebp-backref-cost-attribution-v14-archive-inventory-v1",
        "status": "accepted", "member_count": 1,
        "inventory_sha256": "0" * 64}}
emit("bulk-declaration", declaration, 4)
sequence = 5
chunks = transport.deterministic_payload_chunks(size, transport.CHUNK_BYTES)
if mode == "stall":
    time.sleep(5)
else:
    for index, chunk in enumerate(chunks):
        sys.stdout.buffer.write(transport.encode_frame(
            "bulk-chunk", chunk, sequence=sequence, chunk_index=index))
        sys.stdout.buffer.flush()
        sequence += 1
    if mode == "footer-stall":
        time.sleep(5)
    emit("integrity-footer", {"status": "complete",
         "archive_sha256": archive_sha, "process_refusal": None,
         "process_refusal_sha256": None}, sequence)
    sequence += 1
    emit("cleanup-footer", {"status": "complete",
         "removed_exact_validated_child": True,
         "absence_proved": True}, sequence)
    reader.join()
    if received[0] != expected_request:
        raise SystemExit(7)
'''


def request_chunks(size: int):
    chunk = b"R" * transport.IO_CHUNK_BYTES
    remaining = size
    while remaining:
        value = chunk[:min(len(chunk), remaining)]
        yield value
        remaining -= len(value)


def controls() -> bytes:
    return b"".join([
        transport.encode_frame(
            "source-admission", transport.canonical_json({"status": "verified"}),
            sequence=0),
        transport.encode_frame(
            "operator-status", transport.canonical_json({
                "status": "complete",
                "benchmark_lease_acquisition_attempted": False}), sequence=1),
        transport.encode_frame(
            "archive-build", transport.canonical_json({"status": "accepted"}),
            sequence=2),
        transport.encode_frame(
            "lease-state", transport.canonical_json({"state": "not-attempted"}),
            sequence=3),
    ])


def declaration(archive: bytes) -> dict:
    return {
        "schema": transport.BULK_DECLARATION_SCHEMA,
        "status": "accepted", "compression_format": "tar+gzip",
        "archive_bytes": len(archive),
        "archive_sha256": transport.sha256_bytes(archive),
        "chunk_bytes": transport.CHUNK_BYTES,
        "chunk_count": (len(archive) + transport.CHUNK_BYTES - 1) //
                       transport.CHUNK_BYTES,
        "inventory": {
            "schema":
                "libwebp-backref-cost-attribution-v14-archive-inventory-v1",
            "status": "accepted", "member_count": 1,
            "inventory_sha256": "0" * 64},
    }


def declaration_frame(archive: bytes) -> bytes:
    return transport.encode_frame(
        "bulk-declaration", transport.canonical_json(declaration(archive)),
        sequence=4)


def deadline_fixture() -> tuple[transport.OnlineResponseValidator,
                                admission.TransportDeadlineStateMachine]:
    observer = transport.OnlineResponseValidator(require_success=False)
    deadlines = admission.TransportDeadlineStateMachine(
        0.0, absolute_timeout=1800.0, silent_operator_timeout=900.0,
        bulk_progress_timeout=15.0, footer_timeout=15.0)
    deadlines.request_half_closed(1.0, observer.transport_state)
    assert deadlines.state == admission.SILENT_OPERATOR
    return observer, deadlines


def feed_at(observer, deadlines, value: bytes, now: float) -> None:
    observer.feed(value)
    deadlines.response_progress(now, observer.transport_state)


def deterministic_deadline_state_contracts() -> None:
    observer = transport.OnlineResponseValidator(require_success=False)
    request_deadlines = admission.TransportDeadlineStateMachine(
        0.0, absolute_timeout=1800.0, silent_operator_timeout=900.0,
        bulk_progress_timeout=15.0, footer_timeout=15.0)
    request_deadlines.request_progress(10.0)
    observer.feed(transport.MAGIC)
    request_deadlines.response_progress(11.0, observer.transport_state)
    assert request_deadlines.state == admission.REQUEST_WRITE
    assert request_deadlines.deadline_and_kind() == (25.0, "request-progress")

    # The 46-byte V12 magic-only response started response-progress. V14 magic
    # and every complete or partial control retain the original silent bound.
    observer, deadlines = deadline_fixture()
    feed_at(observer, deadlines, transport.MAGIC, 2.0)
    assert observer.transport_state == transport.TRANSPORT_SILENT_OPERATOR
    assert deadlines.deadline_and_kind() == (901.0, "silent-operator")
    assert not deadlines.expired(900.999)

    observer, deadlines = deadline_fixture()
    feed_at(observer, deadlines, transport.MAGIC + controls()[:19], 100.0)
    assert deadlines.deadline_and_kind() == (901.0, "silent-operator")

    observer, deadlines = deadline_fixture()
    feed_at(observer, deadlines, transport.MAGIC + controls(), 400.0)
    assert deadlines.deadline_and_kind() == (901.0, "silent-operator")

    archive = b"A" * (transport.CHUNK_BYTES + 7)
    encoded_declaration = declaration_frame(archive)
    prefix = transport.MAGIC + controls()
    observer, deadlines = deadline_fixture()
    feed_at(observer, deadlines, prefix + encoded_declaration[:-7], 500.0)
    assert observer.declaration is None
    assert deadlines.deadline_and_kind() == (901.0, "silent-operator")

    observer, deadlines = deadline_fixture()
    feed_at(observer, deadlines, prefix + encoded_declaration, 600.0)
    assert observer.transport_state == transport.TRANSPORT_BULK_STREAM
    assert deadlines.deadline_and_kind() == (615.0, "bulk-progress")
    assert deadlines.expired(615.0)

    first = archive[:transport.CHUNK_BYTES]
    second = archive[transport.CHUNK_BYTES:]
    feed_at(observer, deadlines, transport.encode_frame(
        "bulk-chunk", first, sequence=5, chunk_index=0), 610.0)
    assert deadlines.deadline_and_kind() == (625.0, "bulk-progress")
    second_frame = transport.encode_frame(
        "bulk-chunk", second, sequence=6, chunk_index=1)
    feed_at(observer, deadlines, second_frame[:-2], 620.0)
    assert deadlines.deadline_and_kind() == (635.0, "bulk-progress")
    feed_at(observer, deadlines, second_frame[-2:], 634.0)
    assert observer.transport_state == transport.TRANSPORT_FOOTERS
    assert deadlines.deadline_and_kind() == (649.0, "footer-progress")
    assert deadlines.expired(649.0)

    # A control-only refusal reaches FOOTERS immediately and cleanup completes
    # the state machine; no silent wait is involved.
    observer, deadlines = deadline_fixture()
    refusal = transport.encode_frame("integrity-footer", transport.canonical_json({
        "status": "refused", "archive_sha256": None,
        "process_refusal": None, "process_refusal_sha256": None}), sequence=4)
    feed_at(observer, deadlines, transport.MAGIC + controls() + refusal, 20.0)
    assert deadlines.state == admission.FOOTERS
    cleanup = transport.encode_frame("cleanup-footer", transport.canonical_json({
        "status": "complete", "removed_exact_validated_child": True,
        "absence_proved": True}), sequence=5)
    feed_at(observer, deadlines, cleanup, 21.0)
    assert deadlines.state == admission.COMPLETE
    assert observer.finalize()["success"] is False


def pump_fixture(mode: str, *, request_bytes: int, response_bytes: int,
                 silent_timeout: float = 2.0,
                 progress_timeout: float = 1.0):
    temporary = tempfile.TemporaryDirectory(prefix="attribution-v14-pump-")
    root = Path(temporary.name)
    observer = transport.OnlineResponseValidator(require_success=True)
    command = [sys.executable, "-c", CHILD_SOURCE, mode,
               str(response_bytes), str(request_bytes)]
    try:
        result = admission.pump_owned_full_duplex(
            command, request_chunks(request_bytes),
            stdout_path=root / "stdout.bin", stderr_path=root / "stderr.bin",
            absolute_timeout=20, silent_operator_timeout=silent_timeout,
            progress_timeout=progress_timeout,
            footer_timeout=progress_timeout, stdout_observer=observer)
    except Exception:
        temporary.cleanup()
        raise
    return temporary, root, observer, result


def simultaneous_duplex_contract() -> None:
    temporary, root, observer, result = pump_fixture(
        "duplex", request_bytes=REQUEST_STRESS_BYTES,
        response_bytes=RESPONSE_STRESS_BYTES)
    try:
        parsed = observer.finalize()
        assert parsed["archive_bytes"] == RESPONSE_STRESS_BYTES
        assert result.request_bytes == REQUEST_STRESS_BYTES
        assert result.request_bytes > transport.MAX_RESPONSE_BYTES
        assert result.stdout_bytes < transport.MAX_RESPONSE_BYTES
        assert result.stdout_bytes == (root / "stdout.bin").stat().st_size
        assert result.stderr_bytes == 0
        assert result.stdin_half_closed
        assert result.stdout_sha256 == hashlib.sha256(
            (root / "stdout.bin").read_bytes()).hexdigest()
        archive = root / "archive.bin"
        reparsed = transport.parse_response_file(
            root / "stdout.bin", archive, require_success=True)
        assert archive.stat().st_size == RESPONSE_STRESS_BYTES
        assert reparsed["archive_sha256"] == hashlib.sha256(
            archive.read_bytes()).hexdigest()
        print(json.dumps({
            "fixture": "independent-request-response-direction",
            "request_bytes": result.request_bytes,
            "response_bytes": result.stdout_bytes,
            "response_archive_bytes": parsed["archive_bytes"],
            "response_cap_bytes": transport.MAX_RESPONSE_BYTES,
            "archive_cap_bytes": transport.MAX_ARCHIVE_BYTES},
            sort_keys=True))
    finally:
        temporary.cleanup()


def silent_operator_then_stream_contract() -> None:
    temporary, _, observer, result = pump_fixture(
        "silent", request_bytes=REQUEST_STRESS_BYTES,
        response_bytes=transport.CHUNK_BYTES,
        silent_timeout=1.0, progress_timeout=0.5)
    try:
        assert result.returncode == 0
        assert observer.finalize()["success"]
    finally:
        temporary.cleanup()


def retained_child_timeout_contract(mode: str, expected_state: str,
                                    deadline_kind: str) -> None:
    with tempfile.TemporaryDirectory(prefix="attribution-v14-stall-") as raw:
        root = Path(raw)
        observer = transport.OnlineResponseValidator(require_success=True)
        try:
            admission.pump_owned_full_duplex(
                [sys.executable, "-c", CHILD_SOURCE, mode,
                 str(transport.CHUNK_BYTES), str(transport.CHUNK_BYTES)],
                request_chunks(transport.CHUNK_BYTES),
                stdout_path=root / "stdout.bin",
                stderr_path=root / "stderr.bin", absolute_timeout=5,
                silent_operator_timeout=2, progress_timeout=0.20,
                footer_timeout=0.20, stdout_observer=observer)
        except admission.OwnedTransportTimeout as error:
            assert error.phase == expected_state
            assert error.deadline_kind == deadline_kind
            assert error.stdout_bytes == (root / "stdout.bin").stat().st_size
        else:
            raise AssertionError(f"{mode} timeout was accepted")


def compact_response(*, cleanup: bool = True,
                     oversized: bool = False) -> bytes:
    archive = b"fixture"
    declaration_value = declaration(archive)
    if oversized:
        declaration_value["archive_bytes"] = transport.MAX_ARCHIVE_BYTES + 1
        declaration_value["chunk_count"] = (
            declaration_value["archive_bytes"] + transport.CHUNK_BYTES - 1) // \
            transport.CHUNK_BYTES
    frames = [
        ("source-admission", transport.canonical_json({"status": "verified"}),
         {"sequence": 0}),
        ("operator-status", transport.canonical_json({"status": "complete",
         "benchmark_lease_acquisition_attempted": False}), {"sequence": 1}),
        ("archive-build", transport.canonical_json({"status": "accepted"}),
         {"sequence": 2}),
        ("lease-state", transport.canonical_json({"state": "not-attempted"}),
         {"sequence": 3}),
        ("bulk-declaration", transport.canonical_json(declaration_value),
         {"sequence": 4}),
    ]
    if not oversized:
        frames.append(("bulk-chunk", archive,
                       {"sequence": 5, "chunk_index": 0}))
        sequence = 6
    else:
        sequence = 5
    frames.append(("integrity-footer", transport.canonical_json({
        "status": "complete", "archive_sha256":
            transport.sha256_bytes(archive),
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
    rejected_online(b"X" * (transport.MAX_RESPONSE_BYTES + 1))
    oversized_control = transport.MAGIC + transport.encode_frame(
        "source-admission",
        b"X" * (transport.MAX_CONTROL_PAYLOAD_BYTES + 1), sequence=0)
    rejected_online(oversized_control)
    validator = transport.OnlineResponseValidator(require_success=True)
    validator.feed(complete)
    validator.feed(b"after-cleanup")
    try:
        validator.finalize()
    except transport.FrameRefusal:
        pass
    else:
        raise AssertionError("bytes after mandatory-last cleanup were accepted")


def main() -> int:
    deterministic_deadline_state_contracts()
    simultaneous_duplex_contract()
    silent_operator_then_stream_contract()
    retained_child_timeout_contract(
        "stall", admission.BULK_STREAM, "bulk-progress")
    retained_child_timeout_contract(
        "footer-stall", admission.FOOTERS, "footer-progress")
    online_refusal_contracts()
    print("PASS: V14 keeps magic/control/partial declarations SILENT_OPERATOR, "
          "enters BULK_STREAM only on a valid complete declaration, resets "
          "chunk progress, bounds FOOTERS, parses refusal/cleanup immediately, "
          "persists duplex hashes/counts, and times out only its retained child")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
