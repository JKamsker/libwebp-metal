#!/usr/bin/env python3
"""Framed single-session transport for backref-cost attribution v15.

The same frozen source is used by the local client codec and as the remote
noninteractive ``python3 -c`` transaction.  The transaction creates and later
removes exactly one validated v15 safe-root child.  It never discovers a PID for
control and never invokes a termination command.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time


MAGIC = b"LIBWEBP-BACKREF-COST-ATTRIBUTION-V15-FRAMES\x00\x01\n"
PROTOCOL_VERSION = 6
SAFE_ROOT_BASENAME = ".libwebp-metal-backref-cost-attribution-v15"
RUN_PREFIX = "run."
MAX_HEADER_BYTES = 64 * 1024
MAX_REQUEST_PAYLOAD_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 768 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_CONTROL_PAYLOAD_BYTES = 8 * 1024
CHUNK_BYTES = 256 * 1024
IO_CHUNK_BYTES = 64 * 1024
MAX_PROCESS_IDENTITY_BYTES = 4096
MAX_PROCESS_DIAGNOSTIC_BYTES = 16 * 1024
RESPONSE_ORDER = (
    "source-admission", "operator-status", "archive-build", "lease-state",
    "bulk-declaration", "bulk-chunk", "integrity-footer", "cleanup-footer")
CONTROL_KINDS = RESPONSE_ORDER[:4]
BULK_DECLARATION_SCHEMA = \
    "libwebp-backref-cost-attribution-v15-archive-v1"
TRANSPORT_SILENT_OPERATOR = "SILENT_OPERATOR"
TRANSPORT_BULK_STREAM = "BULK_STREAM"
TRANSPORT_FOOTERS = "FOOTERS"
TRANSPORT_COMPLETE = "COMPLETE"
PROCESS_SNAPSHOT_COMMAND = ("/bin/ps", "-axo", "pid=,ppid=,comm=")

# Kernel ``comm`` is an exact opaque process-table string, never a path.  Raw
# values and lexical final-slash components are separate identities.  The
# lexical component is derived with string operations only; no filesystem API
# participates in process classification.
DENIED_RAW_COMM_IDENTITIES = frozenset({
    "Runner.Worker", "Agent.Worker",
    "backref_cost_attribution_v1_experiment_runner",
    "backref_cost_attribution_v2_experiment_runner",
    "backref_cost_attribution_v3_experiment_runner",
    "backref_cost_attribution_v4_experiment_runner",
    "backref_cost_attribution_v5_experiment_runner",
    "backref_cost_attribution_v6_experiment_runner",
    "backref_cost_attribution_v7_experiment_runner",
    "backref_cost_attribution_v8_experiment_runner",
    "backref_cost_attribution_v9_experiment_runner",
    "backref_cost_attribution_v10_experiment_runner",
    "backref_cost_attribution_v11_experiment_runner",
    "backref_cost_attribution_v12_experiment_runner",
    "backref_cost_attribution_v13_experiment_runner",
    "backref_cost_attribution_v14_experiment_runner",
    "backref_cost_attribution_v15_experiment_runner",
    "backref_cost_interval_search_v1_experiment_runner",
    "backref_cost_interval_search_v2_experiment_runner",
    "backref_cost_interval_search_v3_experiment_runner",
    "backref_cost_interval_specialization_v1_experiment_runner",
    "backref_cost_traceback_experiment_runner",
    "backref_cost_workspace_ab_experiment_runner",
    "backref_cost_workspace_remote_v2_experiment_runner",
    "backref_cost_workspace_remote_v3_experiment_runner",
    "backref_cost_workspace_remote_v4_experiment_runner",
    "backref_cost_workspace_remote_v5_experiment_runner",
    "cache_size_serial_sweep_runner", "cache_size_single_pass_slab_runner",
    "metal_benchmark", "benchmark_metal",
    "xctrace", "sample", "nvidia-smi", "nvcc", "cuda-memcheck",
    "compute-sanitizer", "cuda-gdb", "nsys", "ncu", "cuda",
})
DENIED_LEXICAL_BASENAMES = DENIED_RAW_COMM_IDENTITIES

class FrameRefusal(RuntimeError):
    pass


class ProcessRefusal(FrameRefusal):
    """Identity-only process refusal suitable for a bounded control frame."""

    def __init__(self, failure_code: str, *, row: dict | None = None,
                 is_ancestor: bool = False, is_conflict: bool = False):
        super().__init__(failure_code)
        self.diagnostic = {
            "schema":
                "libwebp-backref-cost-attribution-v15-process-refusal-v1",
            "failure_code": failure_code,
            "pid": row.get("pid") if row is not None else None,
            "ppid": row.get("ppid") if row is not None else None,
            "raw_comm": row.get("raw_comm") if row is not None else None,
            "lexical_basename":
                row.get("lexical_basename") if row is not None else None,
            "is_ancestor": is_ancestor,
            "is_conflict": is_conflict,
        }
        if len(canonical_json(self.diagnostic)) > MAX_PROCESS_DIAGNOSTIC_BYTES:
            self.diagnostic["raw_comm"] = None
            self.diagnostic["lexical_basename"] = None


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encode_frame(kind: str, payload: bytes = b"", **fields: object) -> bytes:
    if not isinstance(payload, bytes):
        raise FrameRefusal("frame payload must be bytes")
    header = {
        "kind": kind, "payload_bytes": len(payload),
        "payload_sha256": sha256_bytes(payload), **fields}
    raw_header = canonical_json(header)
    if len(raw_header) > MAX_HEADER_BYTES:
        raise FrameRefusal("frame header exceeds safety cap")
    return (struct.pack(">I", len(raw_header)) + raw_header +
            struct.pack(">Q", len(payload)) + payload)


def _frame_prefix(kind: str, payload_bytes: int, payload_sha256: str,
                  **fields: object) -> bytes:
    header = {"kind": kind, "payload_bytes": payload_bytes,
              "payload_sha256": payload_sha256, **fields}
    raw_header = canonical_json(header)
    if len(raw_header) > MAX_HEADER_BYTES:
        raise FrameRefusal("frame header exceeds safety cap")
    return (struct.pack(">I", len(raw_header)) + raw_header +
            struct.pack(">Q", payload_bytes))


def encode_stream(frames: list[tuple[str, bytes, dict]]) -> bytes:
    return MAGIC + b"".join(
        encode_frame(kind, payload, **fields)
        for kind, payload, fields in frames)


def _read_exact(stream, size: int) -> bytes:
    value = stream.read(size)
    if len(value) != size:
        raise FrameRefusal("truncated frame stream")
    return value


def read_frame(stream, *, payload_cap: int) -> tuple[dict, bytes] | None:
    prefix = stream.read(4)
    if prefix == b"":
        return None
    if len(prefix) != 4:
        raise FrameRefusal("truncated frame-header length")
    header_size = struct.unpack(">I", prefix)[0]
    if header_size < 2 or header_size > MAX_HEADER_BYTES:
        raise FrameRefusal("invalid frame-header length")
    try:
        header = json.loads(_read_exact(stream, header_size))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrameRefusal("malformed frame header") from error
    if not isinstance(header, dict) or not isinstance(header.get("kind"), str):
        raise FrameRefusal("frame header lacks kind")
    payload_size = struct.unpack(">Q", _read_exact(stream, 8))[0]
    if payload_size > payload_cap or header.get("payload_bytes") != payload_size:
        raise FrameRefusal("frame payload length is invalid")
    payload = _read_exact(stream, payload_size)
    if header.get("payload_sha256") != sha256_bytes(payload):
        raise FrameRefusal("frame payload digest mismatch")
    return header, payload


def decode_stream(value: bytes, *, payload_cap: int) -> list[tuple[dict, bytes]]:
    stream = io.BytesIO(value)
    if _read_exact(stream, len(MAGIC)) != MAGIC:
        raise FrameRefusal("frame-stream magic/version mismatch")
    frames = []
    while True:
        frame = read_frame(stream, payload_cap=payload_cap)
        if frame is None:
            return frames
        frames.append(frame)


def request_bytes(metadata: dict, source_bundle: bytes,
                  representative_payload: bytes) -> bytes:
    metadata_bytes = canonical_json(metadata)
    return encode_stream([
        ("request-metadata", metadata_bytes, {"sequence": 0}),
        ("source-bundle", source_bundle, {"sequence": 1}),
        ("representative-payload", representative_payload, {"sequence": 2}),
    ])


def deterministic_payload_chunks(size: int,
                                 chunk_bytes: int = IO_CHUNK_BYTES):
    if size < 0 or chunk_bytes < 1:
        raise ValueError("deterministic payload bounds are invalid")
    # Preserve V12's exact representative byte stream so its observed archive
    # calibration and the V15 margin comparison remain non-circular.
    domain = b"libwebp-backref-cost-attribution-v12-rehearsal\x00"
    counter = 0
    remaining = size
    pending = bytearray()
    while remaining:
        while len(pending) < min(chunk_bytes, remaining):
            pending.extend(hashlib.sha256(
                domain + counter.to_bytes(8, "big")).digest())
            counter += 1
        length = min(chunk_bytes, remaining)
        yield bytes(pending[:length])
        del pending[:length]
        remaining -= length


def deterministic_payload_sha256(size: int) -> str:
    digest = hashlib.sha256()
    for chunk in deterministic_payload_chunks(size):
        digest.update(chunk)
    return digest.hexdigest()


def iter_request(metadata: dict, source_bundle: bytes,
                 representative_payload_bytes: int):
    """Yield a framed request without constructing one whole request buffer."""
    metadata_bytes = canonical_json(metadata)
    yield MAGIC
    for sequence, (kind, payload) in enumerate((
            ("request-metadata", metadata_bytes),
            ("source-bundle", source_bundle))):
        yield _frame_prefix(kind, len(payload), sha256_bytes(payload),
                            sequence=sequence)
        for offset in range(0, len(payload), IO_CHUNK_BYTES):
            yield payload[offset:offset + IO_CHUNK_BYTES]
    payload_sha256 = deterministic_payload_sha256(
        representative_payload_bytes)
    if metadata.get("representative_payload_bytes") != \
            representative_payload_bytes or metadata.get(
                "representative_payload_sha256") != payload_sha256:
        raise FrameRefusal("streamed representative metadata mismatch")
    yield _frame_prefix(
        "representative-payload", representative_payload_bytes,
        payload_sha256, sequence=2)
    yield from deterministic_payload_chunks(representative_payload_bytes)


class OnlineResponseValidator:
    """Allocation-bounded online framing and bulk declaration validator."""

    def __init__(self, *, require_success: bool):
        self.require_success = require_success
        self.transport_state = TRANSPORT_SILENT_OPERATOR
        self.complete = False
        self.error: str | None = None
        self.controls: dict[str, dict] = {}
        self.declaration: dict | None = None
        self.integrity: dict | None = None
        self.cleanup: dict | None = None
        self.frame_count = 0
        self.chunk_count = 0
        self.archive_bytes = 0
        self.archive_sha256 = hashlib.sha256()
        self.response_bytes = 0
        self._buffer = bytearray()
        self._state = "magic"
        self._needed = len(MAGIC)
        self._header: dict | None = None
        self._payload_remaining = 0
        self._payload_sha256 = hashlib.sha256()
        self._payload = bytearray()
        self._collect_payload = False
        self._kinds: list[str] = []

    def _reject(self, message: str) -> None:
        if self.error is None:
            self.error = message

    def _json_payload(self, payload: bytes | None, label: str) -> dict | None:
        if payload is None:
            self._reject(f"{label} exceeds bounded control payload")
            return None
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._reject(f"{label} is malformed")
            return None
        if not isinstance(value, dict):
            self._reject(f"{label} is not an object")
            return None
        return value

    def _valid_bulk_declaration(self, declaration: dict) -> bool:
        archive_bytes = declaration.get("archive_bytes")
        chunk_count = declaration.get("chunk_count")
        archive_sha256 = declaration.get("archive_sha256")
        inventory = declaration.get("inventory")
        valid_size = (
            isinstance(archive_bytes, int) and not isinstance(archive_bytes, bool)
            and 0 <= archive_bytes <= MAX_ARCHIVE_BYTES)
        valid = (
            declaration.get("schema") == BULK_DECLARATION_SCHEMA and
            declaration.get("status") == "accepted" and valid_size and
            isinstance(archive_sha256, str) and
            re.fullmatch(r"[0-9a-f]{64}", archive_sha256) is not None and
            declaration.get("compression_format") == "tar+gzip" and
            declaration.get("chunk_bytes") == CHUNK_BYTES and
            isinstance(chunk_count, int) and not isinstance(chunk_count, bool)
            and chunk_count == ((archive_bytes + CHUNK_BYTES - 1) //
                                CHUNK_BYTES if valid_size else -1) and
            isinstance(inventory, dict) and
            inventory.get("schema") ==
                "libwebp-backref-cost-attribution-v15-archive-inventory-v1" and
            inventory.get("status") == "accepted" and
            isinstance(inventory.get("member_count"), int) and
            inventory.get("member_count") >= 1 and
            isinstance(inventory.get("inventory_sha256"), str) and
            re.fullmatch(r"[0-9a-f]{64}",
                         inventory.get("inventory_sha256")) is not None)
        if not valid:
            self._reject("bulk declaration schema/shape/size is invalid")
        return valid

    def _complete_frame(self, header: dict, payload: bytes | None) -> None:
        kind = header.get("kind")
        ordinal = self.frame_count
        self.frame_count += 1
        self._kinds.append(kind)
        if header.get("sequence") != ordinal:
            self._reject("frame sequence mismatch")
        if ordinal < len(CONTROL_KINDS):
            if kind != CONTROL_KINDS[ordinal]:
                self._reject("compact control plane is absent or unordered")
            value = self._json_payload(payload, "control payload")
            if value is not None:
                self.controls[kind] = value
            return
        if kind == "bulk-declaration":
            if self.declaration is not None or self.integrity is not None:
                self._reject("bulk declaration order mismatch")
                return
            declaration = self._json_payload(payload, "bulk declaration")
            if declaration is None:
                return
            if not self._valid_bulk_declaration(declaration):
                return
            self.declaration = declaration
            self.transport_state = (TRANSPORT_FOOTERS
                                    if declaration["chunk_count"] == 0 else
                                    TRANSPORT_BULK_STREAM)
            return
        if kind == "bulk-chunk":
            if self.declaration is None or self.integrity is not None:
                self._reject("bulk chunk lacks an active declaration")
            if header.get("chunk_index") != self.chunk_count:
                self._reject("bulk chunk order mismatch")
            prior_archive_bytes = self.archive_bytes - header.get(
                "payload_bytes", 0)
            expected = min(
                CHUNK_BYTES,
                max(0, (self.declaration or {}).get("archive_bytes", 0) -
                    prior_archive_bytes))
            if header.get("payload_bytes") != expected:
                self._reject("bulk chunk size mismatch")
            self.chunk_count += 1
            if self.declaration is not None and \
                    self.chunk_count == self.declaration["chunk_count"]:
                self.transport_state = TRANSPORT_FOOTERS
            return
        if kind == "integrity-footer":
            if self.integrity is not None:
                self._reject("integrity footer is duplicated")
            self.integrity = self._json_payload(payload, "integrity footer")
            if self.integrity is not None:
                self.transport_state = TRANSPORT_FOOTERS
            return
        if kind == "cleanup-footer":
            if self.integrity is None or self.cleanup is not None:
                self._reject("cleanup footer order mismatch")
            self.cleanup = self._json_payload(payload, "cleanup footer")
            if self.cleanup is not None:
                self.transport_state = TRANSPORT_COMPLETE
            return
        self._reject("unexpected response frame kind")

    def feed(self, data: bytes) -> None:
        self.response_bytes += len(data)
        if self.response_bytes >= MAX_RESPONSE_BYTES:
            self._reject("framed response exceeds frozen total cap")
            self._buffer.clear()
            return
        if self.complete:
            self._reject("response contains bytes after completion")
            return
        self._buffer.extend(data)
        while True:
            if self._state == "magic":
                if len(self._buffer) < len(MAGIC):
                    return
                value = bytes(self._buffer[:len(MAGIC)])
                del self._buffer[:len(MAGIC)]
                if value != MAGIC:
                    self._reject("frame-stream magic/version mismatch")
                self._state = "header-size"
            elif self._state == "header-size":
                if len(self._buffer) < 4:
                    return
                header_size = struct.unpack(">I", self._buffer[:4])[0]
                del self._buffer[:4]
                if header_size < 2 or header_size > MAX_HEADER_BYTES:
                    self._reject("invalid frame-header length")
                    self._buffer.clear()
                    return
                self._needed = header_size
                self._state = "header"
            elif self._state == "header":
                if len(self._buffer) < self._needed:
                    return
                raw = bytes(self._buffer[:self._needed])
                del self._buffer[:self._needed]
                try:
                    header = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._reject("malformed frame header")
                    self._buffer.clear()
                    return
                if not isinstance(header, dict) or not isinstance(
                        header.get("kind"), str):
                    self._reject("frame header lacks kind")
                    self._buffer.clear()
                    return
                self._header = header
                self._state = "payload-size"
            elif self._state == "payload-size":
                if len(self._buffer) < 8:
                    return
                payload_size = struct.unpack(">Q", self._buffer[:8])[0]
                del self._buffer[:8]
                header = self._header or {}
                if header.get("payload_bytes") != payload_size:
                    self._reject("frame payload length is invalid")
                kind = header.get("kind")
                if kind == "bulk-chunk" and payload_size > CHUNK_BYTES:
                    self._reject("bulk chunk exceeds frozen chunk cap")
                if kind != "bulk-chunk" and \
                        payload_size > MAX_CONTROL_PAYLOAD_BYTES:
                    self._reject("control payload exceeds frozen cap")
                self._payload_remaining = payload_size
                self._payload_sha256 = hashlib.sha256()
                self._payload = bytearray()
                self._collect_payload = (
                    kind != "bulk-chunk" and
                    payload_size <= MAX_CONTROL_PAYLOAD_BYTES)
                self._state = "payload"
            else:
                if not self._buffer and self._payload_remaining:
                    return
                take = min(len(self._buffer), self._payload_remaining)
                piece = bytes(self._buffer[:take])
                del self._buffer[:take]
                self._payload_sha256.update(piece)
                if self._collect_payload:
                    self._payload.extend(piece)
                if (self._header or {}).get("kind") == "bulk-chunk":
                    self.archive_sha256.update(piece)
                    self.archive_bytes += len(piece)
                    if self.archive_bytes > MAX_ARCHIVE_BYTES:
                        self._reject("bulk stream exceeds frozen archive cap")
                self._payload_remaining -= take
                if self._payload_remaining:
                    return
                header = self._header or {}
                if header.get("payload_sha256") != \
                        self._payload_sha256.hexdigest():
                    self._reject("frame payload digest mismatch")
                payload = bytes(self._payload) if self._collect_payload else None
                self._complete_frame(header, payload)
                self._header = None
                self._state = "header-size"

    def finalize(self) -> dict:
        if self._state != "header-size" or self._buffer:
            self._reject("truncated frame stream")
        if self._kinds[:4] != list(CONTROL_KINDS):
            self._reject("compact control plane is absent or unordered")
        if not self._kinds or self._kinds[-1] != "cleanup-footer" or \
                self._kinds.count("cleanup-footer") != 1:
            self._reject("final cleanup/absence footer is missing")
        if self._kinds.count("integrity-footer") != 1 or \
                len(self._kinds) < 2 or self._kinds[-2] != "integrity-footer":
            self._reject("integrity and cleanup footers are not final")
        declaration = self.declaration
        if declaration is not None and (
                declaration.get("archive_bytes") != self.archive_bytes or
                declaration.get("archive_sha256") !=
                self.archive_sha256.hexdigest() or
                declaration.get("chunk_count") != self.chunk_count):
            self._reject("bulk size/hash/chunk declaration mismatch")
        integrity = self.integrity or {}
        expected_archive_sha = (self.archive_sha256.hexdigest()
                                if declaration is not None else None)
        if integrity.get("archive_sha256") != expected_archive_sha:
            self._reject("integrity footer disagrees with bulk plane")
        cleanup = self.cleanup or {}
        if cleanup.get("status") != "complete" or not cleanup.get(
                "removed_exact_validated_child") or not cleanup.get(
                    "absence_proved"):
            self._reject("cleanup footer lacks exact-child absence proof")
        process_refusal = integrity.get("process_refusal")
        process_refusal_sha256 = integrity.get("process_refusal_sha256")
        if process_refusal is not None:
            expected_keys = {"schema", "failure_code", "pid", "ppid",
                             "raw_comm", "lexical_basename", "is_ancestor",
                             "is_conflict"}
            if not isinstance(process_refusal, dict) or \
                    set(process_refusal) != expected_keys or \
                    process_refusal.get("schema") != (
                        "libwebp-backref-cost-attribution-v15-process-refusal-v1") or \
                    not isinstance(process_refusal.get("failure_code"), str) or \
                    not isinstance(process_refusal.get("is_ancestor"), bool) or \
                    not isinstance(process_refusal.get("is_conflict"), bool) or \
                    len(canonical_json(process_refusal)) > \
                    MAX_PROCESS_DIAGNOSTIC_BYTES or \
                    process_refusal_sha256 != sha256_bytes(
                        canonical_json(process_refusal)):
                self._reject("process refusal diagnostic/hash is invalid")
            for key in ("pid", "ppid"):
                if process_refusal.get(key) is not None and not isinstance(
                        process_refusal.get(key), int):
                    self._reject("process refusal numeric identity is invalid")
            for key in ("raw_comm", "lexical_basename"):
                if process_refusal.get(key) is not None and not isinstance(
                        process_refusal.get(key), str):
                    self._reject("process refusal opaque identity is invalid")
        elif process_refusal_sha256 is not None:
            self._reject("orphaned process refusal diagnostic hash")
        operator = self.controls.get("operator-status", {})
        lease = self.controls.get("lease-state", {})
        attempted = operator.get("benchmark_lease_acquisition_attempted")
        if attempted is False and lease.get("state") != "not-attempted":
            self._reject("not-attempted lease state mismatch")
        if attempted is True and lease.get("state") not in (
                "verified", "unavailable-after-attempt"):
            self._reject("attempted lease state mismatch")
        success = (integrity.get("status") == "complete" and
                   operator.get("status") == "complete" and
                   self.controls.get("archive-build", {}).get("status") ==
                   "accepted" and declaration is not None)
        if self.require_success and not success:
            self._reject("transaction returned a control-only refusal")
        if self.error is not None:
            raise FrameRefusal(self.error)
        self.complete = True
        return {"controls": self.controls, "declaration": declaration,
                "integrity": integrity, "cleanup": cleanup,
                "archive_bytes": self.archive_bytes,
                "archive_sha256": expected_archive_sha, "success": success,
                "frame_count": self.frame_count,
                "chunk_count": self.chunk_count}


def parse_response_file(raw_path: Path, archive_path: Path, *,
                        require_success: bool) -> dict:
    """Verify the complete persisted stream before materializing its archive."""
    if raw_path.stat().st_size >= MAX_RESPONSE_BYTES:
        raise FrameRefusal("persisted response exceeds frozen total cap")
    validator = OnlineResponseValidator(require_success=require_success)
    with raw_path.open("rb") as source:
        for chunk in iter(lambda: source.read(IO_CHUNK_BYTES), b""):
            validator.feed(chunk)
    result = validator.finalize()
    if archive_path.exists():
        raise FrameRefusal("archive materialization target already exists")
    digest = hashlib.sha256()
    count = 0
    with raw_path.open("rb") as source, archive_path.open("xb") as archive:
        if _read_exact(source, len(MAGIC)) != MAGIC:
            raise FrameRefusal("frame-stream magic/version mismatch")
        while True:
            frame = read_frame(
                source, payload_cap=max(CHUNK_BYTES, MAX_CONTROL_PAYLOAD_BYTES))
            if frame is None:
                break
            header, payload = frame
            if header["kind"] == "bulk-chunk":
                archive.write(payload)
                digest.update(payload)
                count += len(payload)
    if count != result["archive_bytes"] or \
            digest.hexdigest() != result["archive_sha256"]:
        raise FrameRefusal("materialized archive differs from verified stream")
    result["archive_path"] = archive_path
    return result


def parse_request(stream) -> tuple[dict, bytes, bytes]:
    if _read_exact(stream, len(MAGIC)) != MAGIC:
        raise FrameRefusal("request magic/version mismatch")
    expected = ("request-metadata", "source-bundle", "representative-payload")
    values = []
    for sequence, kind in enumerate(expected):
        frame = read_frame(stream, payload_cap=MAX_REQUEST_PAYLOAD_BYTES)
        if frame is None:
            raise FrameRefusal("request frame is missing")
        header, payload = frame
        if header["kind"] != kind or header.get("sequence") != sequence:
            raise FrameRefusal("request frame kind/order mismatch")
        values.append(payload)
    if stream.read(1):
        raise FrameRefusal("request contains trailing bytes")
    try:
        metadata = json.loads(values[0])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrameRefusal("request metadata is malformed") from error
    if not isinstance(metadata, dict):
        raise FrameRefusal("request metadata must be an object")
    return metadata, values[1], values[2]


def parse_response(value: bytes, *, require_success: bool) -> dict:
    if len(value) >= MAX_RESPONSE_BYTES:
        raise FrameRefusal("response exceeds frozen total cap")
    frames = decode_stream(value, payload_cap=MAX_ARCHIVE_BYTES)
    if not frames:
        raise FrameRefusal("response contains no frames")
    kinds = [header["kind"] for header, _ in frames]
    if kinds[:4] != list(CONTROL_KINDS):
        raise FrameRefusal("compact control plane is absent or unordered")
    if kinds[-1] != "cleanup-footer" or kinds.count("cleanup-footer") != 1:
        raise FrameRefusal("final cleanup/absence footer is missing")
    if kinds.count("integrity-footer") != 1:
        raise FrameRefusal("integrity footer is missing or duplicated")
    integrity_index = kinds.index("integrity-footer")
    if integrity_index != len(kinds) - 2:
        raise FrameRefusal("integrity and cleanup footers are not final")
    controls = {}
    for header, payload in frames[:4]:
        try:
            controls[header["kind"]] = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FrameRefusal("control payload is malformed") from error
    try:
        integrity = json.loads(frames[integrity_index][1])
        cleanup = json.loads(frames[-1][1])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrameRefusal("footer payload is malformed") from error
    if cleanup.get("status") != "complete" or not cleanup.get(
            "removed_exact_validated_child") or not cleanup.get(
                "absence_proved"):
        raise FrameRefusal("cleanup footer lacks exact-child absence proof")
    middle = frames[4:integrity_index]
    archive = b""
    declaration = None
    if middle:
        if middle[0][0]["kind"] != "bulk-declaration":
            raise FrameRefusal("bulk declaration does not precede chunks")
        try:
            declaration = json.loads(middle[0][1])
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FrameRefusal("bulk declaration is malformed") from error
        chunks = middle[1:]
        if any(header["kind"] != "bulk-chunk" for header, _ in chunks):
            raise FrameRefusal("unexpected frame in bulk plane")
        for index, (header, payload) in enumerate(chunks):
            if header.get("chunk_index") != index:
                raise FrameRefusal("bulk chunk order mismatch")
            archive += payload
        if declaration.get("chunk_count") != len(chunks) or \
                declaration.get("archive_bytes") != len(archive) or \
                declaration.get("archive_sha256") != sha256_bytes(archive):
            raise FrameRefusal("bulk size/hash/chunk declaration mismatch")
    if integrity.get("archive_sha256") != (
            sha256_bytes(archive) if declaration is not None else None):
        raise FrameRefusal("integrity footer disagrees with bulk plane")
    process_refusal = integrity.get("process_refusal")
    process_refusal_sha256 = integrity.get("process_refusal_sha256")
    if process_refusal is not None:
        expected_keys = {
            "schema", "failure_code", "pid", "ppid", "raw_comm",
            "lexical_basename", "is_ancestor", "is_conflict"}
        if not isinstance(process_refusal, dict) or \
                set(process_refusal) != expected_keys or \
                process_refusal.get("schema") != (
                    "libwebp-backref-cost-attribution-v15-process-refusal-v1") or \
                not isinstance(process_refusal.get("failure_code"), str) or \
                not isinstance(process_refusal.get("is_ancestor"), bool) or \
                not isinstance(process_refusal.get("is_conflict"), bool) or \
                len(canonical_json(process_refusal)) > \
                MAX_PROCESS_DIAGNOSTIC_BYTES or \
                process_refusal_sha256 != sha256_bytes(
                    canonical_json(process_refusal)):
            raise FrameRefusal("process refusal diagnostic/hash is invalid")
        for key in ("pid", "ppid"):
            if process_refusal[key] is not None and not isinstance(
                    process_refusal[key], int):
                raise FrameRefusal("process refusal numeric identity is invalid")
        for key in ("raw_comm", "lexical_basename"):
            if process_refusal[key] is not None and not isinstance(
                    process_refusal[key], str):
                raise FrameRefusal("process refusal opaque identity is invalid")
    elif process_refusal_sha256 is not None:
        raise FrameRefusal("orphaned process refusal diagnostic hash")
    lease = controls["lease-state"]
    attempted = controls["operator-status"].get(
        "benchmark_lease_acquisition_attempted")
    if attempted is False and lease.get("state") != "not-attempted":
        raise FrameRefusal("not-attempted lease state mismatch")
    if attempted is True and lease.get("state") not in (
            "verified", "unavailable-after-attempt"):
        raise FrameRefusal("attempted lease state mismatch")
    success = (integrity.get("status") == "complete" and
               controls["operator-status"].get("status") == "complete" and
               controls["archive-build"].get("status") == "accepted" and
               declaration is not None)
    if require_success and not success:
        raise FrameRefusal("transaction returned a control-only refusal")
    return {"frames": frames, "controls": controls, "declaration": declaration,
            "archive": archive, "integrity": integrity, "cleanup": cleanup,
            "success": success}


def deterministic_payload(size: int) -> bytes:
    return b"".join(deterministic_payload_chunks(size))


def _canonical_home() -> Path:
    raw = os.environ.get("HOME", "")
    if not raw or not os.path.isabs(raw) or raw == "/":
        raise FrameRefusal("remote HOME must be absolute and non-root")
    home = Path(raw)
    if Path(os.path.realpath(home)) != home or home.is_symlink() or not home.is_dir():
        raise FrameRefusal("remote HOME must be canonical and real")
    return home


def _safe_root(home: Path) -> Path:
    root = home / SAFE_ROOT_BASENAME
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = os.lstat(root)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or \
            Path(os.path.realpath(root)) != root or root.parent != home:
        raise FrameRefusal("v15 safe root is not a canonical real HOME child")
    return root


def _validate_child(home: Path, root: Path, child: Path) -> None:
    if root != home / SAFE_ROOT_BASENAME or child.parent != root or \
            not child.name.startswith(RUN_PREFIX) or len(child.name) != 12:
        raise FrameRefusal("run directory is not the exact v15 safe-root child")
    info = os.lstat(child)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or \
            Path(os.path.realpath(child)) != child:
        raise FrameRefusal("run directory is not canonical and real")


def _run(argv: list[str], *, cwd: Path | None = None,
         env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False)


def _command(argv: list[str], *, cwd: Path | None = None,
             env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    result = _run(argv, cwd=cwd, env=env)
    if result.returncode != 0:
        raise FrameRefusal(
            f"command failed ({result.returncode}): {argv[0]}: "
            f"{result.stderr.decode(errors='replace').strip()}")
    return result


def frozen_process_snapshot() -> bytes:
    """Capture one immutable identity-only snapshot; no argv is requested."""
    return _command(list(PROCESS_SNAPSHOT_COMMAND)).stdout


def parse_process_snapshot(snapshot: bytes) -> dict[int, dict]:
    """Parse PID, PPID, then the complete remaining opaque raw comm field."""
    try:
        text = snapshot.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ProcessRefusal("snapshot-not-utf8") from error
    if not text or not text.endswith("\n"):
        raise ProcessRefusal("snapshot-empty-or-truncated")
    rows = {}
    for line in text.splitlines():
        match = re.fullmatch(
            r"[ \t]*([0-9]+)[ \t]+([0-9]+)[ \t]+(.+)", line)
        if match is None:
            raise ProcessRefusal("row-malformed")
        pid, ppid = int(match.group(1)), int(match.group(2))
        raw_comm = match.group(3)
        lexical_basename = raw_comm.rsplit("/", 1)[-1]
        row = {"pid": pid, "ppid": ppid, "raw_comm": raw_comm,
               "lexical_basename": lexical_basename}
        if pid < 1 or ppid < 0:
            raise ProcessRefusal("row-invalid-pid", row=row)
        if pid == ppid:
            raise ProcessRefusal("row-self-parent", row=row)
        if pid in rows:
            raise ProcessRefusal("row-duplicate-pid", row=row)
        if not raw_comm or not lexical_basename or len(
                raw_comm.encode("utf-8")) > MAX_PROCESS_IDENTITY_BYTES or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in raw_comm):
            raise ProcessRefusal("row-invalid-opaque-identity", row=row)
        rows[pid] = {
            "pid": pid, "ppid": ppid, "raw_comm": raw_comm,
            "lexical_basename": lexical_basename,
            "raw_comm_identity_kind": "opaque-process-table-string",
            "lexical_basename_identity_kind":
                "final-slash-component-without-filesystem-access",
        }
    return rows


def classify_process_snapshot(snapshot: bytes, self_pid: int) -> dict:
    """Classify exact raw/lexical identities without filesystem access."""
    rows = parse_process_snapshot(snapshot)
    if not isinstance(self_pid, int) or self_pid < 1 or self_pid not in rows:
        raise ProcessRefusal("self-pid-absent")
    ancestor_pids = []
    seen = set()
    current = self_pid
    while True:
        if current in seen:
            raise ProcessRefusal("ancestor-cycle", row=rows.get(current),
                                 is_ancestor=True)
        if current not in rows:
            raise ProcessRefusal("ancestor-parent-missing", row=rows[ancestor_pids[-1]],
                                 is_ancestor=True)
        seen.add(current)
        row = rows[current]
        ancestor_pids.append(current)
        if row["ppid"] == 0:
            if current != 1:
                raise ProcessRefusal("non-pid1-ppid0", row=row,
                                     is_ancestor=True)
            break
        current = row["ppid"]
    for row in rows.values():
        if row["ppid"] == 0 and row["pid"] != 1:
            raise ProcessRefusal("non-pid1-ppid0", row=row,
                                 is_ancestor=row["pid"] in seen)
    for row in rows.values():
        if row["raw_comm"] in DENIED_RAW_COMM_IDENTITIES or \
                row["lexical_basename"] in DENIED_LEXICAL_BASENAMES:
            raise ProcessRefusal(
                "exact-denied-process-identity", row=row,
                is_ancestor=row["pid"] in seen, is_conflict=True)
    return {
        "process_snapshot_sha256": sha256_bytes(snapshot),
        "identity_fields": ["pid", "ppid", "comm"],
        "raw_comm_semantics":
            "complete exact opaque process-table string; never a path",
        "lexical_basename_semantics":
            "exact final slash component; string operation only",
        "argument_text_collected": False,
        "resolved_path_api_used": False,
        "filesystem_identity_operations": [],
        "parsed_process_count": len(rows),
        "verified_ancestor_chain": [rows[pid] for pid in ancestor_pids],
        "ancestor_identity_policy":
            "structural self-to-PID1 proof; no positive identity allowlist",
        "exact_identity_conflicts": [],
        "discovered_pid_signals": 0,
        "external_process_policy": "observe-only; exact-identity refusal; never signal",
    }


def _process_guard() -> dict:
    snapshot = frozen_process_snapshot()
    return classify_process_snapshot(snapshot, os.getpid())


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _admit_source(child: Path, bundle: Path, metadata: dict) -> dict:
    if bundle.is_symlink() or not bundle.is_file() or \
            _file_sha256(bundle) != metadata.get("source_bundle_sha256"):
        raise FrameRefusal("source bundle is not the declared regular file")
    verify = child / "verify.git"
    source = child / "source"
    _command(["git", "init", "--bare", str(verify)], cwd=child)
    checked = _run(["git", "-C", str(verify), "bundle", "verify", str(bundle)],
                   cwd=child)
    if checked.returncode != 0:
        raise FrameRefusal("repository-context bundle verification refused")
    shutil.rmtree(verify)
    _command(["git", "clone", "--no-checkout", str(bundle), str(source)], cwd=child)
    _command(["git", "-C", str(source), "checkout", "--detach",
              metadata["source_commit"]], cwd=child)
    commit = _command(["git", "-C", str(source), "rev-parse", "HEAD"]).stdout.decode().strip()
    tree = _command(["git", "-C", str(source), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip()
    status = _command(["git", "-C", str(source), "status", "--porcelain=v1",
                       "--untracked-files=all"]).stdout
    if commit != metadata.get("source_commit") or tree != metadata.get(
            "source_tree") or status:
        raise FrameRefusal("exact commit/tree/clean source admission failed")
    observed = {}
    for relative, expected in metadata.get("source_hashes", {}).items():
        path = source / relative
        if not path.is_file() or path.is_symlink() or _file_sha256(path) != expected:
            raise FrameRefusal(f"source identity mismatch: {relative}")
        observed[relative] = expected
    return {
        "schema": "libwebp-backref-cost-attribution-v15-source-admission-receipt-v1",
        "receipt_version": 1, "status": "verified", "source_commit": commit,
        "source_tree": tree, "source_bundle_sha256": _file_sha256(bundle),
        "admission": {"bundle_sha256": _file_sha256(bundle),
                      "bundle_verified_in_repository_context": True,
                      "verification_repository_removed": not verify.exists(),
                      "clean_status": True, "source_hashes": observed},
    }


def _encoded_json(kind: str, value: dict, sequence: int) -> bytes:
    payload = canonical_json(value)
    if len(payload) > MAX_CONTROL_PAYLOAD_BYTES:
        raise FrameRefusal(f"{kind} exceeds frozen control cap")
    return encode_frame(kind, payload, sequence=sequence)


def preflight_response(source_receipt: dict, operator_status: dict,
                       archive_status: dict, lease_state: dict,
                       archive: bytes | None, declaration: dict | None,
                       integrity: dict, cleanup: dict) -> bytes:
    """Encode and bound the complete response before its first byte is written."""
    encoded = bytearray(MAGIC)
    sequence = 0
    for kind, value in (
            ("source-admission", source_receipt),
            ("operator-status", operator_status),
            ("archive-build", archive_status),
            ("lease-state", lease_state)):
        encoded.extend(_encoded_json(kind, value, sequence))
        sequence += 1
    if archive is not None and declaration is not None:
        if len(archive) > MAX_ARCHIVE_BYTES:
            raise FrameRefusal("archive exceeds frozen transport cap")
        encoded.extend(_encoded_json("bulk-declaration", declaration, sequence))
        sequence += 1
        for chunk_index, offset in enumerate(range(0, len(archive), CHUNK_BYTES)):
            chunk = archive[offset:offset + CHUNK_BYTES]
            encoded.extend(encode_frame(
                "bulk-chunk", chunk, sequence=sequence,
                chunk_index=chunk_index))
            sequence += 1
    encoded.extend(_encoded_json("integrity-footer", integrity, sequence))
    sequence += 1
    encoded.extend(_encoded_json("cleanup-footer", cleanup, sequence))
    # The cap is exclusive: the complete response must be strictly below 1 MiB.
    if len(encoded) >= MAX_RESPONSE_BYTES:
        raise FrameRefusal("complete framed response does not fit below frozen cap")
    return bytes(encoded)


def remote_main() -> int:
    output = sys.stdout.buffer
    child = None
    home = root = None
    sequence = 0
    success = False
    cleanup = {"schema": "libwebp-backref-cost-attribution-v15-cleanup-receipt-v1",
               "status": "not-attempted", "absence_proved": False}
    source_receipt = {"status": "unavailable", "source_commit": None,
                      "source_tree": None}
    operator_status = {"status": "unavailable",
                       "benchmark_lease_acquisition_attempted": None}
    archive_status = {"status": "not-attempted", "builder_exit_code": None}
    lease_state = {"schema": "libwebp-backref-cost-attribution-v15-lease-transfer-v1",
                   "state": "unavailable-after-attempt",
                   "acquisition_attempted": None}
    archive = None
    declaration = None
    error = None
    process_refusal = None
    started = time.monotonic_ns()
    try:
        metadata, bundle_bytes, payload = parse_request(sys.stdin.buffer)
        if metadata.get("protocol_version") != PROTOCOL_VERSION or \
                metadata.get("mode") not in ("rehearse", "run"):
            raise FrameRefusal("request protocol/mode mismatch")
        if metadata.get("source_bundle_sha256") != sha256_bytes(bundle_bytes):
            raise FrameRefusal("request bundle hash mismatch")
        if metadata.get("representative_payload_bytes") != len(payload) or \
                metadata.get("representative_payload_sha256") != sha256_bytes(payload):
            raise FrameRefusal("request representative payload mismatch")
        if metadata["mode"] == "rehearse" and len(payload) < metadata.get(
                "maximum_expected_run_archive_bytes", MAX_ARCHIVE_BYTES + 1):
            raise FrameRefusal("representative payload is below expected archive bound")
        if metadata["mode"] == "run" and payload:
            raise FrameRefusal("run request must not carry a rehearsal payload")
        home = _canonical_home()
        root = _safe_root(home)
        child = Path(tempfile.mkdtemp(prefix=RUN_PREFIX, dir=root))
        _validate_child(home, root, child)
        process_state = _process_guard()
        bundle = child / "source.bundle"
        bundle.write_bytes(bundle_bytes)
        payload_path = child / "representative-input.bin"
        payload_path.write_bytes(payload)
        source_receipt = _admit_source(child, bundle, metadata)
        source_receipt["pre_operator_process_isolation"] = process_state
        source = child / "source"
        evidence = child / "evidence"
        environment = dict(os.environ)
        environment.pop("WEBP_BENCHMARK_SESSION", None)
        environment["EXPECTED_FREEZE_COMMIT"] = metadata["source_commit"]
        mode = metadata["mode"]
        if mode == "run":
            environment["WEBP_BENCHMARK_SESSION"] = "exclusive"
        else:
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V15_REHEARSAL_PAYLOAD"] = str(payload_path)
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V15_REHEARSAL_PAYLOAD_SHA256"] = sha256_bytes(payload)
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V15_REHEARSAL_PAYLOAD_BYTES"] = str(len(payload))
        operator = _run([
            sys.executable,
            "scripts/run_backref_cost_attribution_v15_experiment.py", mode,
            str(evidence)], cwd=source, env=environment)
        status_path = evidence / "operator-status.json"
        if status_path.is_file():
            operator_status = json.loads(status_path.read_text(encoding="utf-8"))
        else:
            operator_status = {"status": "unavailable", "mode": mode,
                               "benchmark_lease_acquisition_attempted": None}
        operator_status["operator_exit_code"] = operator.returncode
        operator_status["operator_stdout_sha256"] = sha256_bytes(operator.stdout)
        operator_status["operator_stderr_sha256"] = sha256_bytes(operator.stderr)
        if process_refusal is None and isinstance(
                operator_status.get("process_refusal"), dict):
            process_refusal = operator_status["process_refusal"]
        attempted = operator_status.get("benchmark_lease_acquisition_attempted")
        lease_path = evidence / "lease-record.json"
        if attempted is False:
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v15-lease-transfer-v1",
                "state": "not-attempted", "status": "not-attempted",
                "acquisition_attempted": False, "receipt_required": False,
                "receipt_available": False}
        elif attempted is True and lease_path.is_file():
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            state = "verified" if lease.get("released") else "unavailable-after-attempt"
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v15-lease-transfer-v1",
                "state": state, "status": state, "acquisition_attempted": True,
                "receipt_required": True, "receipt_available": True,
                "receipt": lease}
        else:
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v15-lease-transfer-v1",
                "state": "unavailable-after-attempt",
                "status": "unavailable-after-attempt",
                "acquisition_attempted": attempted,
                "receipt_required": attempted is True,
                "receipt_available": False}
        archive_path = child / "evidence.tar.gz"
        inventory_path = child / "archive-inventory.json"
        digest_path = child / "archive-digest.json"
        builder = _run([
            sys.executable, "scripts/backref_cost_attribution_v15_archive.py", "build",
            str(evidence), str(evidence / "artifact-hashes.json"),
            str(archive_path), str(inventory_path), str(digest_path)], cwd=source)
        archive_status = {"status": "accepted" if builder.returncode == 0 else "rejected",
                          "builder_exit_code": builder.returncode,
                          "builder_stdout_sha256": sha256_bytes(builder.stdout),
                          "builder_stderr_sha256": sha256_bytes(builder.stderr)}
        if builder.returncode == 0:
            archive = archive_path.read_bytes()
            if len(archive) > MAX_ARCHIVE_BYTES:
                raise FrameRefusal("archive exceeds frozen transport cap")
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            if digest.get("archive_bytes") != len(archive) or \
                    digest.get("archive_sha256") != sha256_bytes(archive):
                raise FrameRefusal("archive builder declaration mismatch")
            compact_inventory = {
                "schema": inventory["schema"],
                "status": inventory["status"],
                "member_count": inventory["member_count"],
                "inventory_sha256": sha256_bytes(canonical_json(inventory)),
            }
            declaration = {**digest, "inventory": compact_inventory,
                           "chunk_bytes": CHUNK_BYTES,
                           "chunk_count": (len(archive) + CHUNK_BYTES - 1) // CHUNK_BYTES}
        success = (operator.returncode == 0 and
                   operator_status.get("status") == "complete" and
                   archive_status["status"] == "accepted" and
                   (lease_state["state"] == "not-attempted" if mode == "rehearse"
                    else lease_state["state"] == "verified"))
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
        if isinstance(caught, ProcessRefusal):
            process_refusal = caught.diagnostic
    integrity = {
        "schema": "libwebp-backref-cost-attribution-v15-integrity-footer-v1",
        "status": "complete" if success else "refused",
        "archive_sha256": sha256_bytes(archive) if archive is not None else None,
        "archive_bytes": len(archive) if archive is not None else 0,
        "elapsed_before_cleanup_ns": time.monotonic_ns() - started,
        "complete_response_preflight_required": True,
        "exclusive_framed_response_cap_bytes": MAX_RESPONSE_BYTES,
        "error": error,
        "process_refusal": process_refusal,
        "process_refusal_sha256": sha256_bytes(canonical_json(process_refusal))
        if process_refusal is not None else None,
    }
    if child is not None:
        try:
            _validate_child(home, root, child)
            target = str(child)
            shutil.rmtree(child)
            absent = not os.path.lexists(child)
            if not absent:
                raise FrameRefusal("exact v15 child remains after cleanup")
            cleanup = {
                "schema": "libwebp-backref-cost-attribution-v15-cleanup-receipt-v1",
                "status": "complete", "run_directory": target,
                "safe_root": str(root), "removed_exact_validated_child": True,
                "absence_proved": True,
                "source_commit": source_receipt.get("source_commit"),
                "source_tree": source_receipt.get("source_tree"),
                "elapsed_transaction_ns": time.monotonic_ns() - started}
        except Exception as caught:
            cleanup = {
                "schema": "libwebp-backref-cost-attribution-v15-cleanup-receipt-v1",
                "status": "refused", "removed_exact_validated_child": False,
                "absence_proved": False,
                "reason": f"{type(caught).__name__}: {caught}"}
            success = False
    if cleanup.get("status") != "complete":
        integrity["status"] = "refused"
    try:
        response = preflight_response(
            source_receipt, operator_status, archive_status, lease_state,
            archive, declaration, integrity, cleanup)
    except (FrameRefusal, OSError, ValueError, TypeError) as caught:
        # No response byte has been written. Cleanup has already completed or
        # recorded its refusal, so an oversized/unencodable response fails closed.
        print(f"response preflight refused: {caught}", file=sys.stderr)
        return 1
    try:
        output.write(response)
        output.flush()
    except (BrokenPipeError, OSError):
        return 1
    return 0 if success and cleanup.get("status") == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(remote_main())
