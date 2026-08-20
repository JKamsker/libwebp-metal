#!/usr/bin/env python3
"""Deterministic Aligned Null Stage Attribution V3 READY/request-ACK/full-duplex fixtures."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import backref_cost_aligned_null_stage_attribution_v3_admission as admission
import backref_cost_aligned_null_stage_attribution_v3_transport as transport


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_bootstrap.py"
NONCE = "a" * 64
BOOTSTRAP_SHA = hashlib.sha256(BOOTSTRAP.read_bytes()).hexdigest()


def request(*, business_bytes: int = 1, response_bytes: int = 17,
            stderr_bytes: int = 0) -> transport.ChannelRequest:
    remote = f'''\
import sys
def remote_transaction(stream):
    stream.read()
    sys.stderr.buffer.write(b"E" * {stderr_bytes})
    sys.stderr.buffer.flush()
    return 0, b"R" * {response_bytes}
'''.encode()
    return transport.build_channel_request(
        remote, b"PAYLOAD_IDENTITY = 1\n", b"B" * business_bytes,
        transaction_nonce=NONCE, bootstrap_sha256=BOOTSTRAP_SHA)


def environment(channel_request: transport.ChannelRequest) -> dict[str, str]:
    result = dict(os.environ)
    result.update({
        "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_TRANSACTION_NONCE": NONCE,
        "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_REQUEST_DECLARATION_SHA256":
            channel_request.declaration_sha256,
        "WEBP_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_BOOTSTRAP_SHA256": BOOTSTRAP_SHA,
    })
    return result


def observer(channel_request: transport.ChannelRequest):
    return transport.OnlineChannelValidator(
        channel_request, transaction_nonce=NONCE,
        bootstrap_sha256=BOOTSTRAP_SHA)


def pump(command: list[str], channel_request: transport.ChannelRequest, *,
         ready_timeout: float = 1.0, request_timeout: float = 1.0,
         response_timeout: float = 1.0,
         env_overrides: dict[str, str] | None = None):
    temporary = tempfile.TemporaryDirectory(prefix="stage-attribution-v3-channel-")
    root = Path(temporary.name)
    watched = observer(channel_request)
    try:
        child_env = environment(channel_request)
        child_env.update(env_overrides or {})
        result = admission.pump_owned_request_channel(
            command, channel_request, observer=watched,
            stdout_path=root / "channel.bin", stderr_path=root / "stderr.bin",
            response_path=root / "response.bin", absolute_timeout=10,
            ready_timeout=ready_timeout,
            request_progress_timeout=request_timeout,
            silent_operator_timeout=3,
            response_progress_timeout=response_timeout,
            env=child_env)
    except Exception:
        temporary.cleanup()
        raise
    return temporary, root, watched, result


def delayed_ready_and_large_duplex() -> None:
    channel_request = request(
        business_bytes=2 * 1024 * 1024 + 4096,
        response_bytes=700 * 1024, stderr_bytes=128 * 1024)
    wrapper = (
        "import runpy,time;time.sleep(0.05);"
        f"runpy.run_path({str(BOOTSTRAP)!r},run_name='__main__')")
    temporary, root, watched, result = pump(
        [sys.executable, "-c", wrapper], channel_request,
        ready_timeout=1.0, request_timeout=2.0, response_timeout=2.0)
    try:
        parsed = watched.finalize()
        assert result.channel_established
        assert result.request_chunks_written == channel_request.chunk_count
        assert result.request_chunks_acked == channel_request.chunk_count
        assert result.request_bytes_acked == len(channel_request.value)
        assert result.response_bytes == 700 * 1024
        assert result.stderr_bytes == 128 * 1024
        assert parsed["response"] == (root / "response.bin").read_bytes()
        assert result.stdout_sha256 == hashlib.sha256(
            (root / "channel.bin").read_bytes()).hexdigest()
        assert result.stderr_sha256 == hashlib.sha256(
            (root / "stderr.bin").read_bytes()).hexdigest()
    finally:
        temporary.cleanup()


def timeout_fixture(command: list[str], channel_request: transport.ChannelRequest,
                    *, expected_phase: str, established: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-timeout-") as raw:
        root = Path(raw)
        try:
            admission.pump_owned_request_channel(
                command, channel_request, observer=observer(channel_request),
                stdout_path=root / "channel.bin",
                stderr_path=root / "stderr.bin",
                response_path=root / "response.bin", absolute_timeout=3,
                ready_timeout=0.15, request_progress_timeout=0.15,
                silent_operator_timeout=1, response_progress_timeout=0.15,
                env=environment(channel_request))
        except admission.OwnedTransportTimeout as error:
            assert error.phase == expected_phase
            assert error.channel_established is established
            assert error.stdout_bytes == (root / "channel.bin").stat().st_size
        else:
            raise AssertionError(f"{expected_phase} timeout was accepted")


def no_and_partial_ready() -> None:
    channel_request = request()
    timeout_fixture(
        [sys.executable, "-c", "import time;time.sleep(3)"], channel_request,
        expected_phase=admission.CONNECT_CHANNEL_READY, established=False)
    partial = (
        "import sys,time;"
        f"sys.stdout.buffer.write({transport.CHANNEL_MAGIC!r}+b'\\x00\\x00');"
        "sys.stdout.buffer.flush();time.sleep(3)")
    timeout_fixture(
        [sys.executable, "-c", partial], channel_request,
        expected_phase=admission.CONNECT_CHANNEL_READY, established=False)


def ready_value(channel_request: transport.ChannelRequest) -> dict:
    binding = transport.sha256_bytes(transport.canonical_json({
        "schema": transport.CHANNEL_READY_SCHEMA,
        "protocol_version": transport.PROTOCOL_VERSION,
        "transaction_nonce": NONCE,
        "request_declaration_sha256": channel_request.declaration_sha256,
        "bootstrap_sha256": BOOTSTRAP_SHA}))
    return {
        "schema": transport.CHANNEL_READY_SCHEMA,
        "protocol_version": transport.PROTOCOL_VERSION,
        "transaction_nonce": NONCE,
        "request_declaration_sha256": channel_request.declaration_sha256,
        "bootstrap_sha256": BOOTSTRAP_SHA,
        "channel_binding_sha256": binding,
        "remote_process_pid": 123,
        "remote_process_ppid": 1,
        "request_payload_read_before_ready": False,
        "remote_files_created_before_ready": 0,
    }


def ready_then_request_stall() -> None:
    channel_request = request()
    ready = transport.CHANNEL_MAGIC + transport.encode_frame(
        "ready", transport.canonical_json(ready_value(channel_request)),
        sequence=0)
    source = (
        "import sys,time;"
        f"sys.stdout.buffer.write({ready!r});sys.stdout.buffer.flush();"
        "time.sleep(3)")
    timeout_fixture(
        [sys.executable, "-c", source], channel_request,
        expected_phase=admission.REQUEST_DECLARATION, established=True)


def remote_ack_stall_source(channel_request: transport.ChannelRequest,
                            acknowledged_chunks: int) -> str:
    ready = ready_value(channel_request)
    return f'''\
import hashlib,json,sys,time
import backref_cost_aligned_null_stage_attribution_v3_transport as t
def chained(value, prior):
    core=dict(value);core["prior_ack_digest"]=prior
    result=dict(core);result["ack_digest"]=t.sha256_bytes(t.canonical_json(core))
    return result
def emit(kind,value,sequence,**fields):
    sys.stdout.buffer.write(t.encode_frame(kind,t.canonical_json(value),sequence=sequence,**fields));sys.stdout.buffer.flush()
sys.stdout.buffer.write(t.CHANNEL_MAGIC);sys.stdout.buffer.flush()
emit("ready",{ready!r},0)
assert t._read_exact(sys.stdin.buffer,len(t.CHANNEL_MAGIC)) == t.CHANNEL_MAGIC
header,declaration_payload=t.read_frame(sys.stdin.buffer,payload_cap=t.MAX_CONTROL_PAYLOAD_BYTES)
declaration=t.strict_json_loads(declaration_payload)
ack=chained({{"schema":t.REQUEST_ACK_SCHEMA,"status":"accepted","ack_kind":"declaration","transaction_nonce":{NONCE!r},"request_bytes_acked":0,"request_chunks_acked":0,"request_declaration_sha256":{channel_request.declaration_sha256!r},"remote_receipt_sequence":0}},"0"*64)
emit("request-ack",ack,1,ack_index=0)
prior=ack["ack_digest"]
cumulative=0
for index in range({acknowledged_chunks}):
    header,chunk=t.read_frame(sys.stdin.buffer,payload_cap=t.REQUEST_CHUNK_BYTES)
    start=cumulative;cumulative+=len(chunk)
    ack=chained({{"schema":t.REQUEST_CHUNK_ACK_SCHEMA,"ack_kind":"chunk","chunk_sha256":t.sha256_bytes(chunk),"cumulative_bytes":cumulative,"remote_receipt_sequence":index+1}},prior)
    emit("request-ack",ack,index+2,ack_index=index+1);prior=ack["ack_digest"]
if {acknowledged_chunks} < declaration["request_chunk_count"]:
    t.read_frame(sys.stdin.buffer,payload_cap=t.REQUEST_CHUNK_BYTES)
time.sleep(3)
'''


def chunk_stall_matrix() -> None:
    channel_request = request(business_bytes=12 * transport.REQUEST_CHUNK_BYTES)
    points = (0, 5, channel_request.chunk_count // 2,
              channel_request.chunk_count - 1)
    for acknowledged in points:
        with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-stall-") as raw:
            root = Path(raw)
            watched = observer(channel_request)
            try:
                admission.pump_owned_request_channel(
                    [sys.executable, "-c", remote_ack_stall_source(
                        channel_request, acknowledged)],
                    channel_request, observer=watched,
                    stdout_path=root / "channel.bin",
                    stderr_path=root / "stderr.bin",
                    response_path=root / "response.bin", absolute_timeout=3,
                    ready_timeout=1, request_progress_timeout=0.15,
                    silent_operator_timeout=1, response_progress_timeout=1,
                    env=environment(channel_request))
            except admission.OwnedTransportTimeout as error:
                expected_phase = (admission.REQUEST_COMPLETE
                                  if acknowledged == channel_request.chunk_count - 1
                                  else admission.REQUEST_CHUNK)
                assert error.phase == expected_phase
                assert watched.request_chunks_acked == acknowledged
                assert len(watched.progress_chain_snapshot()) == acknowledged
                assert watched.client_transport_state["request_chunks_written"] == \
                    acknowledged + 1
            else:
                raise AssertionError(f"chunk stall after {acknowledged} ACKs passed")


def ack_value(channel_request: transport.ChannelRequest, *, ordinal: int,
              prior: str, **changes: object) -> dict:
    start = (ordinal - 1) * transport.REQUEST_CHUNK_BYTES
    end = min(ordinal * transport.REQUEST_CHUNK_BYTES,
              len(channel_request.value))
    chunk = channel_request.value[start:end]
    core = {
        "schema": transport.REQUEST_CHUNK_ACK_SCHEMA, "ack_kind": "chunk",
        "chunk_sha256": transport.sha256_bytes(chunk),
        "cumulative_bytes": end,
        "remote_receipt_sequence": ordinal, "prior_ack_digest": prior,
    }
    core.update(changes)
    return {**core, "ack_digest": transport.sha256_bytes(
        transport.canonical_json(core))}


def ack_chain_negative_matrix() -> None:
    channel_request = request(business_bytes=2 * transport.REQUEST_CHUNK_BYTES)
    ready_frame = transport.CHANNEL_MAGIC + transport.encode_frame(
        "ready", transport.canonical_json(ready_value(channel_request)),
        sequence=0)
    declaration_core = {
        "schema": transport.REQUEST_ACK_SCHEMA, "status": "accepted",
        "ack_kind": "declaration", "transaction_nonce": NONCE,
        "request_bytes_acked": 0, "request_chunks_acked": 0,
        "request_declaration_sha256": channel_request.declaration_sha256,
        "remote_receipt_sequence": 0, "prior_ack_digest": "0" * 64,
    }
    declaration = {**declaration_core, "ack_digest": transport.sha256_bytes(
        transport.canonical_json(declaration_core))}
    declaration_frame = transport.encode_frame(
        "request-ack", transport.canonical_json(declaration),
        sequence=1, ack_index=0)
    mutations = (
        {"cumulative_bytes": 1},
        {"chunk_sha256": "0" * 64}, {"prior_ack_digest": "1" * 64},
        {"remote_receipt_sequence": 2}, {"ack_kind": "wrong"},
    )
    for mutation in mutations:
        watched = observer(channel_request)
        watched.feed(ready_frame + declaration_frame)
        now = time.monotonic_ns()
        watched.note_chunk_write_start(1, now)
        watched.note_chunk_write_complete(1, now)
        invalid = ack_value(channel_request, ordinal=1,
                            prior=declaration["ack_digest"], **mutation)
        rejected(watched, transport.encode_frame(
            "request-ack", transport.canonical_json(invalid),
            sequence=2, ack_index=1))
    watched = observer(channel_request)
    watched.feed(ready_frame + declaration_frame)
    now = time.monotonic_ns()
    watched.note_chunk_write_start(1, now)
    watched.note_chunk_write_complete(1, now)
    valid = ack_value(channel_request, ordinal=1,
                      prior=declaration["ack_digest"])
    valid_frame = transport.encode_frame(
        "request-ack", transport.canonical_json(valid), sequence=2, ack_index=1)
    watched.feed(valid_frame)
    rejected(watched, transport.encode_frame(
        "request-ack", transport.canonical_json(valid), sequence=3, ack_index=1))


def early_exit_absolute_timeout_and_cleanup_footer() -> None:
    channel_request = request()
    ready = transport.CHANNEL_MAGIC + transport.encode_frame(
        "ready", transport.canonical_json(ready_value(channel_request)),
        sequence=0)
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-early-exit-") as raw:
        root = Path(raw)
        command = [sys.executable, "-c",
                   f"import sys;sys.stdout.buffer.write({ready!r});sys.stdout.buffer.flush()"]
        try:
            admission.pump_owned_request_channel(
                command, channel_request, observer=observer(channel_request),
                stdout_path=root / "channel.bin", stderr_path=root / "stderr.bin",
                response_path=root / "response.bin", absolute_timeout=2,
                ready_timeout=1, request_progress_timeout=0.2,
                silent_operator_timeout=1, response_progress_timeout=1,
                env=environment(channel_request))
        except transport.FrameRefusal:
            pass
        else:
            raise AssertionError("remote early exit passed")
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-absolute-") as raw:
        root = Path(raw)
        try:
            admission.pump_owned_request_channel(
                [sys.executable, "-c", "import time;time.sleep(3)"],
                channel_request, observer=observer(channel_request),
                stdout_path=root / "channel.bin", stderr_path=root / "stderr.bin",
                response_path=root / "response.bin", absolute_timeout=0.1,
                ready_timeout=1, request_progress_timeout=1,
                silent_operator_timeout=1, response_progress_timeout=1,
                env=environment(channel_request))
        except admission.OwnedTransportTimeout as error:
            assert error.deadline_kind == admission.ABSOLUTE_TRANSACTION
        else:
            raise AssertionError("absolute timeout passed")
    response = transport.encode_stream([])
    try:
        transport.parse_response(response, require_success=False)
    except transport.FrameRefusal:
        pass
    else:
        raise AssertionError("missing cleanup footer passed")


def rejected(watched: transport.OnlineChannelValidator, value: bytes) -> None:
    watched.feed(value)
    try:
        watched.finalize()
    except transport.FrameRefusal:
        return
    raise AssertionError("unsafe request-channel stream was accepted")


def partial_ack_corruption_and_order() -> None:
    channel_request = request()
    ready = transport.CHANNEL_MAGIC + transport.encode_frame(
        "ready", transport.canonical_json(ready_value(channel_request)),
        sequence=0)
    ack = transport.encode_frame("request-ack", transport.canonical_json({
        "schema": transport.REQUEST_ACK_SCHEMA,
        "status": "accepted", "ack_kind": "declaration",
        "transaction_nonce": NONCE, "request_bytes_acked": 0,
        "request_chunks_acked": 0,
        "request_declaration_sha256": channel_request.declaration_sha256,
    }), sequence=1, ack_index=0)
    rejected(observer(channel_request), ready + ack[:-3])
    corrupt = bytearray(ready)
    corrupt[-1] ^= 1
    rejected(observer(channel_request), bytes(corrupt))
    duplicate = ready + transport.encode_frame(
        "ready", transport.canonical_json(ready_value(channel_request)),
        sequence=1)
    rejected(observer(channel_request), duplicate)
    early = transport.CHANNEL_MAGIC + transport.encode_frame(
        "response-chunk", b"early", sequence=0, chunk_index=0)
    rejected(observer(channel_request), early)


def timeout_boundary_contract() -> None:
    state = admission.TransportDeadlineStateMachine(
        0.0, absolute_timeout=100, ready_timeout=30,
        request_progress_timeout=5, silent_operator_timeout=60,
        response_progress_timeout=7)
    assert state.deadline_and_kind() == (30, "connect-channel-ready")
    assert not state.expired(29.999)
    assert state.expired(30)
    state.transition(1, admission.REQUEST_DECLARATION)
    assert state.deadline_and_kind() == (6, "request-declaration-progress")
    state.progress(5)
    assert state.deadline_and_kind() == (10, "request-declaration-progress")
    state.transition(6, admission.REQUEST_CHUNK)
    state.transition(7, admission.REQUEST_COMPLETE)
    state.transition(8, admission.SILENT_OPERATOR)
    assert state.deadline_and_kind() == (68, "silent-operator")
    state.transition(9, admission.RESPONSE_STREAM)
    state.progress(15)
    assert state.deadline_and_kind() == (22, "response-progress")


def source_refusal_is_not_success() -> None:
    # Full channel success remains distinct from remote source admission.
    source = (ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_transport.py").read_bytes()
    payload = (ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_payload.py").read_bytes()
    bundle = b"not-a-git-bundle"
    representative = b"R"
    metadata = {
        "protocol_version": transport.PROTOCOL_VERSION,
        "mode": "rehearse", "source_commit": "1" * 40,
        "source_tree": "2" * 40, "source_hashes": {"README": "3" * 64},
        "source_bundle_sha256": transport.sha256_bytes(bundle),
        "source_bundle_bytes": len(bundle),
        "representative_payload_bytes": len(representative),
        "representative_payload_sha256": transport.sha256_bytes(representative),
        "maximum_expected_run_archive_bytes": 0,
    }
    business = transport.request_bytes(metadata, bundle, representative)
    channel_request = transport.build_channel_request(
        source, payload, business, transaction_nonce=NONCE,
        bootstrap_sha256=BOOTSTRAP_SHA)
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-remote-home-") as remote_home:
        temporary, root, _, result = pump(
            [sys.executable, str(BOOTSTRAP)], channel_request,
            request_timeout=2, response_timeout=2,
            env_overrides={"HOME": str(Path(remote_home).resolve())})
        try:
            assert result.channel_established
            parsed = transport.parse_response(
                (root / "response.bin").read_bytes(), require_success=False)
            assert parsed["success"] is False
            assert parsed["cleanup"]["status"] == "complete"
            assert parsed["cleanup"]["absence_proved"] is True
            try:
                transport.parse_response(
                    (root / "response.bin").read_bytes(), require_success=True)
            except transport.FrameRefusal:
                pass
            else:
                raise AssertionError("source-admission refusal became success")
        finally:
            temporary.cleanup()


def exact_size_freeze() -> None:
    channel_request = request(business_bytes=2 * 1024 * 1024)
    assert len(channel_request.declaration_payload) <= \
        transport.MAX_REQUEST_DECLARATION_BYTES
    assert len(channel_request.value) <= transport.MAX_REQUEST_BYTES
    assert channel_request.chunk_count == ((
        len(channel_request.value) + transport.REQUEST_CHUNK_BYTES - 1) //
        transport.REQUEST_CHUNK_BYTES)
    assert len(BOOTSTRAP.read_bytes()) <= transport.MAX_BOOTSTRAP_SOURCE_BYTES


def main() -> int:
    delayed_ready_and_large_duplex()
    no_and_partial_ready()
    ready_then_request_stall()
    chunk_stall_matrix()
    ack_chain_negative_matrix()
    early_exit_absolute_timeout_and_cleanup_footer()
    partial_ack_corruption_and_order()
    timeout_boundary_contract()
    source_refusal_is_not_success()
    exact_size_freeze()
    print(json.dumps({
        "status": "PASS",
        "fixtures": [
            "delayed-ready", "no-ready", "partial-ready",
            "ready-request-stall", "large-request-duplex-stdout-stderr",
            "chunk-1-stall", "chunk-6-stall", "middle-chunk-stall",
            "final-chunk-stall", "ack-loss", "ack-duplicate", "ack-reorder",
            "ack-corruption", "ack-wrong-range", "ack-wrong-digest",
            "ack-wrong-chain", "partial-write", "remote-early-exit",
            "absolute-timeout", "cleanup-footer-refusal",
            "partial-ack", "duplicate-out-of-order", "early-payload",
            "response-backpressure", "timeout-boundaries",
            "corruption-truncation", "source-admission-refusal"],
        "request_chunk_bytes": transport.REQUEST_CHUNK_BYTES,
        "request_cap_bytes": transport.MAX_REQUEST_BYTES,
        "response_chunk_bytes": transport.CHUNK_BYTES,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
