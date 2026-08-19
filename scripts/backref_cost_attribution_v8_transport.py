#!/usr/bin/env python3
"""Framed single-session transport for backref-cost attribution v8.

The same frozen source is used by the local client codec and as the remote
noninteractive ``python3 -c`` transaction.  The transaction creates and later
removes exactly one validated v8 safe-root child.  It never discovers a PID for
control and never invokes a termination command.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time


MAGIC = b"LIBWEBP-BACKREF-COST-ATTRIBUTION-V8-FRAMES\x00\x01\n"
PROTOCOL_VERSION = 1
SAFE_ROOT_BASENAME = ".libwebp-metal-backref-cost-attribution-v8"
RUN_PREFIX = "run."
MAX_HEADER_BYTES = 64 * 1024
MAX_REQUEST_PAYLOAD_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 12 * 1024 * 1024
CHUNK_BYTES = 512 * 1024
RESPONSE_ORDER = (
    "source-admission", "operator-status", "archive-build", "lease-state",
    "bulk-declaration", "bulk-chunk", "integrity-footer", "cleanup-footer")
CONTROL_KINDS = RESPONSE_ORDER[:4]
PROCESS_SNAPSHOT_COMMAND = ("/bin/ps", "-axo", "pid=,ppid=,comm=")

# Executable identity is the only conflict key.  This frozen set intentionally
# contains exact basenames: neither argv nor a substring/prefix/suffix match can
# create a conflict.
DENIED_EXECUTABLE_BASENAMES = frozenset({
    "Runner.Worker", "Agent.Worker",
    "backref_cost_attribution_v1_experiment_runner",
    "backref_cost_attribution_v2_experiment_runner",
    "backref_cost_attribution_v3_experiment_runner",
    "backref_cost_attribution_v4_experiment_runner",
    "backref_cost_attribution_v5_experiment_runner",
    "backref_cost_attribution_v6_experiment_runner",
    "backref_cost_attribution_v7_experiment_runner",
    "backref_cost_attribution_v8_experiment_runner",
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

# Every member of this transaction's self-to-PID-1 chain must be one of these
# exact executable paths.  Non-ancestor processes do not gain an allow-list
# exemption; they remain subject to the exact deny set above.
EXPECTED_TRANSPORT_ANCESTOR_PATHS = frozenset({
    "/Applications/Xcode-26.3.0.app/Contents/Developer/Library/Frameworks/"
    "Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python",
    "/usr/bin/python3", "/usr/bin/python",
    "/usr/bin/ssh", "/usr/sbin/sshd", "/usr/libexec/sshd-session",
    "/bin/sh", "/bin/bash", "/bin/zsh", "/sbin/launchd",
})


class FrameRefusal(RuntimeError):
    pass


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
    domain = b"libwebp-backref-cost-attribution-v8-rehearsal\x00"
    output = bytearray()
    counter = 0
    while len(output) < size:
        output.extend(hashlib.sha256(domain + counter.to_bytes(8, "big")).digest())
        counter += 1
    return bytes(output[:size])


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
        raise FrameRefusal("v8 safe root is not a canonical real HOME child")
    return root


def _validate_child(home: Path, root: Path, child: Path) -> None:
    if root != home / SAFE_ROOT_BASENAME or child.parent != root or \
            not child.name.startswith(RUN_PREFIX) or len(child.name) != 12:
        raise FrameRefusal("run directory is not the exact v8 safe-root child")
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
    """Parse exact PID/PPID/comm rows and fail closed on ambiguity."""
    try:
        text = snapshot.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise FrameRefusal("process identity snapshot is not UTF-8") from error
    if not text or not text.endswith("\n"):
        raise FrameRefusal("process identity snapshot is empty or truncated")
    rows = {}
    for line in text.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            raise FrameRefusal("process identity row is malformed")
        pid, ppid = int(parts[0]), int(parts[1])
        comm = parts[2]
        if pid < 1 or ppid < 0 or pid == ppid or pid in rows or \
                comm != comm.strip() or not comm or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in comm):
            raise FrameRefusal("process identity row is ambiguous")
        if comm.startswith("/"):
            if os.path.normpath(comm) != comm or "//" in comm:
                raise FrameRefusal("absolute executable identity is noncanonical")
        elif "/" in comm:
            raise FrameRefusal("relative executable identity is ambiguous")
        basename = comm.rsplit("/", 1)[-1]
        if basename in ("", ".", ".."):
            raise FrameRefusal("executable basename is ambiguous")
        rows[pid] = {"pid": pid, "ppid": ppid, "comm": comm,
                     "executable_basename": basename}
    return rows


def classify_process_snapshot(snapshot: bytes, self_pid: int) -> dict:
    """Classify exact executable identities from one frozen snapshot."""
    rows = parse_process_snapshot(snapshot)
    if not isinstance(self_pid, int) or self_pid < 1 or self_pid not in rows:
        raise FrameRefusal("transaction PID is absent from process snapshot")
    ancestor_pids = []
    seen = set()
    current = self_pid
    while True:
        if current in seen or current not in rows:
            raise FrameRefusal("transaction ancestor chain is cyclic or incomplete")
        seen.add(current)
        row = rows[current]
        ancestor_pids.append(current)
        if row["comm"] not in EXPECTED_TRANSPORT_ANCESTOR_PATHS:
            raise FrameRefusal("transaction ancestor executable is not allowed")
        if row["ppid"] == 0:
            if current != 1:
                raise FrameRefusal("transaction ancestor chain does not end at PID 1")
            break
        current = row["ppid"]
    conflicts = [row for row in rows.values()
                 if row["executable_basename"] in
                 DENIED_EXECUTABLE_BASENAMES]
    if conflicts:
        raise FrameRefusal(
            "conflicting runner, benchmark, profiler, or CUDA executable identity detected; untouched")
    return {
        "process_snapshot_sha256": sha256_bytes(snapshot),
        "identity_fields": ["pid", "ppid", "comm"],
        "argument_text_collected": False,
        "parsed_process_count": len(rows),
        "verified_ancestor_chain": [rows[pid] for pid in ancestor_pids],
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
        "schema": "libwebp-backref-cost-attribution-v8-source-admission-receipt-v1",
        "receipt_version": 1, "status": "verified", "source_commit": commit,
        "source_tree": tree, "source_bundle_sha256": _file_sha256(bundle),
        "admission": {"bundle_sha256": _file_sha256(bundle),
                      "bundle_verified_in_repository_context": True,
                      "verification_repository_removed": not verify.exists(),
                      "clean_status": True, "source_hashes": observed},
    }


def _emit_json(stream, kind: str, value: dict, sequence: int) -> int:
    stream.write(encode_frame(kind, canonical_json(value), sequence=sequence))
    stream.flush()
    return sequence + 1


def remote_main() -> int:
    output = sys.stdout.buffer
    output.write(MAGIC)
    output.flush()
    child = None
    home = root = None
    sequence = 0
    success = False
    cleanup = {"schema": "libwebp-backref-cost-attribution-v8-cleanup-receipt-v1",
               "status": "not-attempted", "absence_proved": False}
    source_receipt = {"status": "unavailable", "source_commit": None,
                      "source_tree": None}
    operator_status = {"status": "unavailable",
                       "benchmark_lease_acquisition_attempted": None}
    archive_status = {"status": "not-attempted", "builder_exit_code": None}
    lease_state = {"schema": "libwebp-backref-cost-attribution-v8-lease-transfer-v1",
                   "state": "unavailable-after-attempt",
                   "acquisition_attempted": None}
    archive = None
    declaration = None
    error = None
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
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V8_REHEARSAL_PAYLOAD"] = str(payload_path)
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V8_REHEARSAL_PAYLOAD_SHA256"] = sha256_bytes(payload)
            environment["WEBP_BACKREF_COST_ATTRIBUTION_V8_REHEARSAL_PAYLOAD_BYTES"] = str(len(payload))
        operator = _run([
            sys.executable,
            "scripts/run_backref_cost_attribution_v8_experiment.py", mode,
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
        attempted = operator_status.get("benchmark_lease_acquisition_attempted")
        lease_path = evidence / "lease-record.json"
        if attempted is False:
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v8-lease-transfer-v1",
                "state": "not-attempted", "status": "not-attempted",
                "acquisition_attempted": False, "receipt_required": False,
                "receipt_available": False}
        elif attempted is True and lease_path.is_file():
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            state = "verified" if lease.get("released") else "unavailable-after-attempt"
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v8-lease-transfer-v1",
                "state": state, "status": state, "acquisition_attempted": True,
                "receipt_required": True, "receipt_available": True,
                "receipt": lease}
        else:
            lease_state = {
                "schema": "libwebp-backref-cost-attribution-v8-lease-transfer-v1",
                "state": "unavailable-after-attempt",
                "status": "unavailable-after-attempt",
                "acquisition_attempted": attempted,
                "receipt_required": attempted is True,
                "receipt_available": False}
        archive_path = child / "evidence.tar.gz"
        inventory_path = child / "archive-inventory.json"
        digest_path = child / "archive-digest.json"
        builder = _run([
            sys.executable, "scripts/backref_cost_attribution_v8_archive.py", "build",
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
            declaration = {**digest, "inventory": inventory,
                           "chunk_bytes": CHUNK_BYTES,
                           "chunk_count": (len(archive) + CHUNK_BYTES - 1) // CHUNK_BYTES}
        success = (operator.returncode == 0 and
                   operator_status.get("status") == "complete" and
                   archive_status["status"] == "accepted" and
                   (lease_state["state"] == "not-attempted" if mode == "rehearse"
                    else lease_state["state"] == "verified"))
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    try:
        sequence = _emit_json(output, "source-admission", source_receipt, sequence)
        sequence = _emit_json(output, "operator-status", operator_status, sequence)
        sequence = _emit_json(output, "archive-build", archive_status, sequence)
        sequence = _emit_json(output, "lease-state", lease_state, sequence)
        if archive is not None and declaration is not None:
            sequence = _emit_json(output, "bulk-declaration", declaration, sequence)
            for chunk_index, offset in enumerate(range(0, len(archive), CHUNK_BYTES)):
                chunk = archive[offset:offset + CHUNK_BYTES]
                output.write(encode_frame("bulk-chunk", chunk, sequence=sequence,
                                          chunk_index=chunk_index))
                output.flush()
                sequence += 1
        integrity = {"schema": "libwebp-backref-cost-attribution-v8-integrity-footer-v1",
                     "status": "complete" if success else "refused",
                     "archive_sha256": sha256_bytes(archive) if archive is not None else None,
                     "archive_bytes": len(archive) if archive is not None else 0,
                     "elapsed_before_cleanup_ns": time.monotonic_ns() - started,
                     "error": error}
        sequence = _emit_json(output, "integrity-footer", integrity, sequence)
    except (BrokenPipeError, OSError) as caught:
        error = f"{type(caught).__name__}: {caught}"
        success = False
    finally:
        if child is not None:
            try:
                _validate_child(home, root, child)
                target = str(child)
                shutil.rmtree(child)
                absent = not os.path.lexists(child)
                if not absent:
                    raise FrameRefusal("exact v8 child remains after cleanup")
                cleanup = {
                    "schema": "libwebp-backref-cost-attribution-v8-cleanup-receipt-v1",
                    "status": "complete", "run_directory": target,
                    "safe_root": str(root), "removed_exact_validated_child": True,
                    "absence_proved": True,
                    "elapsed_transaction_ns": time.monotonic_ns() - started}
            except Exception as caught:
                cleanup = {
                    "schema": "libwebp-backref-cost-attribution-v8-cleanup-receipt-v1",
                    "status": "refused", "removed_exact_validated_child": False,
                    "absence_proved": False,
                    "reason": f"{type(caught).__name__}: {caught}"}
                success = False
        try:
            _emit_json(output, "cleanup-footer", cleanup, sequence)
        except (BrokenPipeError, OSError):
            success = False
    return 0 if success and cleanup.get("status") == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(remote_main())
