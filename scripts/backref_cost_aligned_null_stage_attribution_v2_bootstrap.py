#!/usr/bin/env python3
"""Minimal remote request-channel bootstrap for Aligned Null Stage Attribution V2.

This source is the only program embedded in the SSH command.  It emits READY
before reading or writing any request payload, receives one bounded declared
request in fixed-size acknowledged chunks, then executes the hash-bound
transport source carried by that request.  It creates no remote filesystem
object and never performs process discovery or signalling.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import struct
import sys
import types


CHANNEL_MAGIC = b"LIBWEBP-BACKREF-COST-ALIGNED-NULL-STAGE-ATTRIBUTION-V2-CHANNEL\x00\x01\n"
PROTOCOL_VERSION = 1
CONTROL_CAP = 8192
HEADER_CAP = 8192
REQUEST_CAP = 32 * 1024 * 1024
REQUEST_CHUNK_BYTES = 64 * 1024
RESPONSE_CAP = 1024 * 1024
RESPONSE_CHUNK_BYTES = 256 * 1024
COMPONENT_NAMES = ("transport-source", "payload-source", "business-request")
COMPONENT_CAPS = (256 * 1024, 64 * 1024, 31 * 1024 * 1024)
READY_SCHEMA = "libwebp-backref-cost-aligned-null-stage-attribution-v2-ready-v1"
DECLARATION_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v2-request-declaration-v1"
ACK_SCHEMA = "libwebp-backref-cost-aligned-null-stage-attribution-v2-request-ack-v1"
RESPONSE_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v2-response-declaration-v1"
COMPLETE_SCHEMA = \
    "libwebp-backref-cost-aligned-null-stage-attribution-v2-response-complete-v1"


class BootstrapRefusal(RuntimeError):
    pass


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def strict_json(value: bytes) -> object:
    def no_collisions(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise BootstrapRefusal("duplicate JSON object name")
            result[key] = item
        return result
    try:
        return json.loads(value, object_pairs_hook=no_collisions)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BootstrapRefusal("malformed JSON") from error


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_exact(stream, size: int) -> bytes:
    value = stream.read(size)
    if len(value) != size:
        raise BootstrapRefusal("truncated channel input")
    return value


def encode_frame(kind: str, payload: bytes, *, sequence: int,
                 **fields: object) -> bytes:
    header = {
        "kind": kind, "sequence": sequence, "payload_bytes": len(payload),
        "payload_sha256": sha256(payload), **fields}
    raw = canonical_json(header)
    if len(raw) > HEADER_CAP:
        raise BootstrapRefusal("channel header exceeds cap")
    return struct.pack(">I", len(raw)) + raw + struct.pack(">Q", len(payload)) + payload


def read_frame(stream, *, payload_cap: int) -> tuple[dict, bytes]:
    header_size = struct.unpack(">I", read_exact(stream, 4))[0]
    if header_size < 2 or header_size > HEADER_CAP:
        raise BootstrapRefusal("invalid channel header length")
    header = strict_json(read_exact(stream, header_size))
    if not isinstance(header, dict) or not isinstance(header.get("kind"), str):
        raise BootstrapRefusal("channel header shape is invalid")
    payload_size = struct.unpack(">Q", read_exact(stream, 8))[0]
    if payload_size > payload_cap or header.get("payload_bytes") != payload_size:
        raise BootstrapRefusal("channel payload length exceeds declaration")
    payload = read_exact(stream, payload_size)
    if header.get("payload_sha256") != sha256(payload):
        raise BootstrapRefusal("channel payload digest mismatch")
    return header, payload


def emit(output, kind: str, value: dict | bytes, sequence: int,
         **fields: object) -> int:
    payload = canonical_json(value) if isinstance(value, dict) else value
    if kind != "response-chunk" and len(payload) > CONTROL_CAP:
        raise BootstrapRefusal("channel control exceeds cap")
    output.write(encode_frame(kind, payload, sequence=sequence, **fields))
    output.flush()
    return sequence + 1


def _hex(value: object, size: int) -> bool:
    return isinstance(value, str) and len(value) == size and \
        re.fullmatch(r"[0-9a-f]+", value) is not None


def validate_declaration(value: object, expected_sha: str, nonce: str,
                         bootstrap_sha: str) -> dict:
    keys = {
        "schema", "protocol_version", "transaction_nonce", "bootstrap_sha256",
        "request_bytes", "request_sha256", "request_chunk_bytes",
        "request_chunk_count", "components"}
    if not isinstance(value, dict) or set(value) != keys or \
            value.get("schema") != DECLARATION_SCHEMA or \
            value.get("protocol_version") != PROTOCOL_VERSION or \
            value.get("transaction_nonce") != nonce or \
            value.get("bootstrap_sha256") != bootstrap_sha or \
            not _hex(value.get("request_sha256"), 64):
        raise BootstrapRefusal("request declaration identity is invalid")
    request_bytes = value.get("request_bytes")
    chunk_count = value.get("request_chunk_count")
    if not isinstance(request_bytes, int) or isinstance(request_bytes, bool) or \
            request_bytes < 1 or request_bytes > REQUEST_CAP or \
            value.get("request_chunk_bytes") != REQUEST_CHUNK_BYTES or \
            not isinstance(chunk_count, int) or isinstance(chunk_count, bool) or \
            chunk_count != (request_bytes + REQUEST_CHUNK_BYTES - 1) // REQUEST_CHUNK_BYTES:
        raise BootstrapRefusal("request declaration bounds are invalid")
    if sha256(canonical_json(value)) != expected_sha:
        raise BootstrapRefusal("request declaration challenge mismatch")
    components = value.get("components")
    if not isinstance(components, list) or len(components) != len(COMPONENT_NAMES):
        raise BootstrapRefusal("request components are absent")
    offset = 0
    for expected_name, component_cap, row in zip(
            COMPONENT_NAMES, COMPONENT_CAPS, components):
        if not isinstance(row, dict) or set(row) != {
                "name", "offset", "bytes", "sha256"} or \
                row.get("name") != expected_name or row.get("offset") != offset or \
                not isinstance(row.get("bytes"), int) or \
                isinstance(row.get("bytes"), bool) or row["bytes"] < 1 or \
                row["bytes"] > component_cap or \
                not _hex(row.get("sha256"), 64):
            raise BootstrapRefusal("request component declaration is invalid")
        offset += row["bytes"]
    if offset != request_bytes:
        raise BootstrapRefusal("request components do not reconstruct request")
    return value


def component_values(request: bytes, declaration: dict) -> dict[str, bytes]:
    result = {}
    for row in declaration["components"]:
        start = row["offset"]
        value = request[start:start + row["bytes"]]
        if len(value) != row["bytes"] or sha256(value) != row["sha256"]:
            raise BootstrapRefusal("request component integrity mismatch")
        result[row["name"]] = value
    return result


def main() -> int:
    input_stream = sys.stdin.buffer
    output = sys.stdout.buffer
    sequence = 0
    nonce = os.environ.get("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V2_TRANSACTION_NONCE", "")
    expected_declaration_sha = os.environ.get(
        "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V2_REQUEST_DECLARATION_SHA256", "")
    bootstrap_sha = os.environ.get("WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V2_BOOTSTRAP_SHA256", "")
    if not _hex(nonce, 64) or not _hex(expected_declaration_sha, 64) or \
            not _hex(bootstrap_sha, 64):
        return 111
    binding = sha256(canonical_json({
        "schema": READY_SCHEMA, "protocol_version": PROTOCOL_VERSION,
        "transaction_nonce": nonce,
        "request_declaration_sha256": expected_declaration_sha,
        "bootstrap_sha256": bootstrap_sha}))
    output.write(CHANNEL_MAGIC)
    output.flush()
    sequence = emit(output, "ready", {
        "schema": READY_SCHEMA,
        "protocol_version": PROTOCOL_VERSION,
        "transaction_nonce": nonce,
        "request_declaration_sha256": expected_declaration_sha,
        "bootstrap_sha256": bootstrap_sha,
        "channel_binding_sha256": binding,
        "remote_process_pid": os.getpid(),
        "remote_process_ppid": os.getppid(),
        "request_payload_read_before_ready": False,
        "remote_files_created_before_ready": 0,
    }, sequence)
    try:
        if read_exact(input_stream, len(CHANNEL_MAGIC)) != CHANNEL_MAGIC:
            raise BootstrapRefusal("request channel magic mismatch")
        header, payload = read_frame(input_stream, payload_cap=CONTROL_CAP)
        if header.get("kind") != "request-declaration" or \
                header.get("sequence") != 0:
            raise BootstrapRefusal("request declaration is absent or out of order")
        declaration = strict_json(payload)
        if canonical_json(declaration) != payload:
            raise BootstrapRefusal("request declaration is not canonical")
        declaration = validate_declaration(
            declaration, expected_declaration_sha, nonce, bootstrap_sha)
        sequence = emit(output, "request-ack", {
            "schema": ACK_SCHEMA, "status": "accepted", "ack_kind": "declaration",
            "transaction_nonce": nonce, "request_bytes_acked": 0,
            "request_chunks_acked": 0,
            "request_declaration_sha256": expected_declaration_sha,
        }, sequence, ack_index=0)
        request = bytearray()
        digest = hashlib.sha256()
        for chunk_index in range(declaration["request_chunk_count"]):
            header, chunk = read_frame(input_stream, payload_cap=REQUEST_CHUNK_BYTES)
            expected_size = min(
                REQUEST_CHUNK_BYTES, declaration["request_bytes"] - len(request))
            if header.get("kind") != "request-chunk" or \
                    header.get("sequence") != chunk_index + 1 or \
                    header.get("chunk_index") != chunk_index or \
                    len(chunk) != expected_size:
                raise BootstrapRefusal("request chunk is partial or out of order")
            request.extend(chunk)
            digest.update(chunk)
            sequence = emit(output, "request-ack", {
                "schema": ACK_SCHEMA, "status": "accepted", "ack_kind": "chunk",
                "transaction_nonce": nonce,
                "request_bytes_acked": len(request),
                "request_chunks_acked": chunk_index + 1,
                "request_declaration_sha256": expected_declaration_sha,
            }, sequence, ack_index=chunk_index + 1)
        if input_stream.read(1) != b"":
            raise BootstrapRefusal("request channel contains trailing data")
        request_bytes = bytes(request)
        if len(request_bytes) != declaration["request_bytes"] or \
                digest.hexdigest() != declaration["request_sha256"]:
            raise BootstrapRefusal("complete request integrity mismatch")
        sequence = emit(output, "request-complete", {
            "schema": ACK_SCHEMA, "status": "complete", "ack_kind": "request",
            "transaction_nonce": nonce,
            "request_bytes_acked": len(request_bytes),
            "request_chunks_acked": declaration["request_chunk_count"],
            "request_sha256": digest.hexdigest(),
            "request_declaration_sha256": expected_declaration_sha,
        }, sequence)
        values = component_values(request_bytes, declaration)
        payload_module = types.ModuleType(
            "backref_cost_aligned_null_stage_attribution_v2_payload")
        exec(compile(values["payload-source"].decode(), "<stage-attribution-v2-payload>",
                     "exec"), payload_module.__dict__)
        sys.modules[payload_module.__name__] = payload_module
        transport_module = types.ModuleType(
            "backref_cost_aligned_null_stage_attribution_v2_remote")
        sys.modules[transport_module.__name__] = transport_module
        exec(compile(values["transport-source"].decode(),
                     "<stage-attribution-v2-transport>", "exec"),
             transport_module.__dict__)
        code, response = transport_module.remote_transaction(
            io.BytesIO(values["business-request"]))
        if not isinstance(code, int) or not isinstance(response, bytes) or \
                len(response) >= RESPONSE_CAP:
            raise BootstrapRefusal("remote transaction response is invalid")
        response_sha = sha256(response)
        response_chunks = (len(response) + RESPONSE_CHUNK_BYTES - 1) // \
            RESPONSE_CHUNK_BYTES
        sequence = emit(output, "response-declaration", {
            "schema": RESPONSE_SCHEMA, "status": "started",
            "transaction_nonce": nonce, "response_bytes": len(response),
            "response_sha256": response_sha,
            "response_chunk_bytes": RESPONSE_CHUNK_BYTES,
            "response_chunk_count": response_chunks,
            "transaction_exit_code": code,
        }, sequence)
        for chunk_index, offset in enumerate(
                range(0, len(response), RESPONSE_CHUNK_BYTES)):
            sequence = emit(
                output, "response-chunk",
                response[offset:offset + RESPONSE_CHUNK_BYTES], sequence,
                chunk_index=chunk_index)
        emit(output, "response-complete", {
            "schema": COMPLETE_SCHEMA, "status": "complete",
            "transaction_nonce": nonce, "response_bytes": len(response),
            "response_sha256": response_sha,
            "response_chunk_count": response_chunks,
            "transaction_exit_code": code,
        }, sequence)
        return code
    except Exception as error:
        try:
            emit(output, "channel-refusal", {
                "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-channel-refusal-v1",
                "status": "refused", "transaction_nonce": nonce,
                "error_type": type(error).__name__, "error": str(error)[:1024],
            }, sequence)
        except Exception:
            pass
        return 112


if __name__ == "__main__":
    raise SystemExit(main())
