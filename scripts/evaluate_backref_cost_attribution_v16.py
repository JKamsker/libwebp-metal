#!/usr/bin/env python3
"""Independent Phase 3 evaluator for backref-cost attribution V16.

This reads only committed Phase 1/2 artifacts and repository source.  It does
not invoke an encoder, profiler, remote command, CUDA, or benchmark workload.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import re
import statistics
import struct
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "evidence/backref-cost-attribution-v16-design"
REHEARSAL = DESIGN / "rehearsal"
EXECUTION = ROOT / "evidence/backref-cost-attribution-v16-execution-20260819"
OUTPUT = ROOT / (
    "evidence/backref-cost-attribution-v16-phase3-"
    "evaluation-consequence-20260819.json")

BASE = "8ac198e565ab36eedd6e124202b78c09e5180ec1"
PHASE1A = "6f0cbbaf8a3ee527526edbd29779bd9f8c7d941c"
PHASE1B = "ef24e275a714f76bd78a04363524bc32f2e4076d"
PHASE2 = "85817c0f97ea5fe1227d0d04466736f570fba731"
SOURCE_TREE = "633eaa7df1090e9f8f6f2a82df492372a1114a4d"

MAGIC = b"LIBWEBP-BACKREF-COST-ATTRIBUTION-V16-FRAMES\x00\x01\n"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PROFILE_ID = re.compile(
    r"p([0-9]{2})-(photo-large|graphic-large)-m(4|6)-"
    r"(baseline|candidate)-r([0-2])\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path):
    return json.loads(path.read_bytes())


def load_jsonl(path: Path) -> list[dict]:
    raw = path.read_bytes()
    require(raw.endswith(b"\n"), f"JSONL lacks final newline: {path}")
    return [json.loads(line) for line in raw.splitlines() if line]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def pretty(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path, relative_to: Path = ROOT) -> dict:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest_file(path),
    }


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()


def verify_rows(root: Path, rows: list[dict]) -> set[str]:
    names: set[str] = set()
    prior = ""
    for row in rows:
        require(set(row) == {"path", "bytes", "sha256"},
                f"hash row shape mismatch under {root}")
        name = row["path"]
        require(isinstance(name, str) and name > prior and name not in names,
                f"unordered or duplicate hash row: {name}")
        pure = PurePosixPath(name)
        require(not pure.is_absolute() and ".." not in pure.parts and
                "." not in pure.parts and "\\" not in name,
                f"unsafe indexed path: {name}")
        path = root.joinpath(*pure.parts)
        require(path.is_file() and not path.is_symlink(),
                f"indexed path is not a regular file: {name}")
        require(path.stat().st_size == row["bytes"],
                f"indexed byte count mismatch: {name}")
        require(HEX64.fullmatch(row["sha256"]) is not None and
                digest_file(path) == row["sha256"],
                f"indexed digest mismatch: {name}")
        names.add(name)
        prior = name
    return names


def decode_frames(path: Path, response_cap: int, archive_cap: int,
                  control_cap: int, chunk_bytes: int) -> dict:
    raw = path.read_bytes()
    require(len(raw) < response_cap, f"response cap failed: {path}")
    require(raw.startswith(MAGIC), f"framed magic mismatch: {path}")
    stream = io.BytesIO(raw[len(MAGIC):])
    frames: list[dict] = []
    archive = bytearray()
    while stream.tell() < len(raw) - len(MAGIC):
        prefix = stream.read(4)
        require(len(prefix) == 4, "truncated frame header length")
        header_bytes = struct.unpack(">I", prefix)[0]
        require(2 <= header_bytes <= 65536, "frame header cap failed")
        encoded_header = stream.read(header_bytes)
        require(len(encoded_header) == header_bytes, "truncated frame header")
        header = json.loads(encoded_header)
        require(encoded_header == canonical(header), "noncanonical frame header")
        payload_size_raw = stream.read(8)
        require(len(payload_size_raw) == 8, "truncated payload size")
        payload_size = struct.unpack(">Q", payload_size_raw)[0]
        require(header.get("payload_bytes") == payload_size,
                "header/payload size mismatch")
        kind = header.get("kind")
        require(isinstance(kind, str), "frame kind missing")
        require(payload_size <= (chunk_bytes if kind == "bulk-chunk"
                                 else control_cap),
                f"payload cap failed for {kind}")
        payload = stream.read(payload_size)
        require(len(payload) == payload_size, f"truncated payload: {kind}")
        require(header.get("payload_sha256") == digest_bytes(payload),
                f"payload digest mismatch: {kind}")
        require(header.get("sequence") == len(frames),
                f"frame sequence mismatch: {kind}")
        if kind == "bulk-chunk":
            require(header.get("chunk_index") ==
                    sum(f["kind"] == "bulk-chunk" for f in frames),
                    "bulk chunk index mismatch")
            archive.extend(payload)
            value = None
        else:
            value = json.loads(payload)
            require(payload == canonical(value), f"noncanonical control: {kind}")
        frames.append({"kind": kind, "header": header, "value": value,
                       "payload_bytes": payload_size})
    kinds = [frame["kind"] for frame in frames]
    require(kinds[:4] == ["source-admission", "operator-status",
                          "archive-build", "lease-state"],
            "control plane order mismatch")
    require(kinds[-2:] == ["integrity-footer", "cleanup-footer"],
            "footer order mismatch")
    require(kinds.count("cleanup-footer") == 1 and
            kinds.count("integrity-footer") == 1 and
            kinds.count("bulk-declaration") == 1,
            "response frame cardinality mismatch")
    declaration = next(f["value"] for f in frames
                       if f["kind"] == "bulk-declaration")
    chunks = [f for f in frames if f["kind"] == "bulk-chunk"]
    require(len(archive) <= archive_cap and
            declaration["archive_bytes"] == len(archive) and
            declaration["archive_sha256"] == digest_bytes(archive) and
            declaration["chunk_bytes"] == chunk_bytes and
            declaration["chunk_count"] == len(chunks) ==
            math.ceil(len(archive) / chunk_bytes),
            "bulk declaration mismatch")
    for index, frame in enumerate(chunks):
        expected = min(chunk_bytes, len(archive) - index * chunk_bytes)
        require(frame["payload_bytes"] == expected, "bulk chunk shape mismatch")
    integrity = frames[-2]["value"]
    cleanup = frames[-1]["value"]
    require(integrity["archive_bytes"] == len(archive) and
            integrity["archive_sha256"] == digest_bytes(archive) and
            integrity["status"] == "complete" and
            integrity["complete_response_preflight_required"] is True and
            integrity["exclusive_framed_response_cap_bytes"] == response_cap and
            integrity["error"] is None and
            integrity["process_refusal"] is None,
            "integrity footer mismatch")
    require(cleanup["status"] == "complete" and
            cleanup["removed_exact_validated_child"] is True and
            cleanup["absence_proved"] is True and
            frames[-1]["kind"] == "cleanup-footer",
            "cleanup-last/absence proof mismatch")
    return {
        "raw": raw, "frames": frames, "archive": bytes(archive),
        "declaration": declaration,
        "identity": file_identity(path),
        "frame_count": len(frames), "frame_kinds": kinds,
    }


def inspect_archive(raw: bytes) -> tuple[dict, dict[str, bytes]]:
    members: list[dict] = []
    contents: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        seen: set[str] = set()
        for member in archive.getmembers():
            require(member.name not in seen, f"duplicate tar member: {member.name}")
            seen.add(member.name)
            pure = PurePosixPath(member.name)
            require(not pure.is_absolute() and pure.parts and
                    pure.parts[0] == "evidence" and ".." not in pure.parts and
                    not member.pax_headers and
                    (member.isdir() or member.isfile()),
                    f"unsafe tar member: {member.name}")
            kind = "directory" if member.isdir() else "regular"
            members.append({"name": member.name, "type": kind,
                            "size": member.size})
            if member.isfile():
                source = archive.extractfile(member)
                require(source is not None, f"unreadable tar member: {member.name}")
                value = source.read()
                require(len(value) == member.size, f"tar size mismatch: {member.name}")
                contents[member.name] = value
    inventory = {
        "schema": "libwebp-backref-cost-attribution-v16-archive-inventory-v1",
        "status": "accepted", "member_count": len(members),
        "members": members, "offending": None,
    }
    return inventory, contents


def verify_transaction(root: Path, expected_inner_count: int,
                       expected_returned_count: int,
                       returned_membership_current: bool,
                       manifest: dict) -> dict:
    inner = load_json(root / "artifact-hashes.json")
    require(inner["schema"] == manifest["schemas"]["artifact_hashes"],
            "inner artifact schema mismatch")
    inner_names = verify_rows(root, inner["artifacts"])
    require(len(inner_names) == expected_inner_count, "inner artifact count mismatch")

    returned = load_json(root / "returned-evidence-hashes.json")
    require(returned["schema"] ==
            "libwebp-backref-cost-attribution-v16-returned-evidence-hashes-v1",
            "returned artifact schema mismatch")
    returned_names = verify_rows(root, returned["artifacts"])
    require(len(returned_names) == expected_returned_count,
            "returned artifact count mismatch")
    excluded = set(returned["excluded_after_index"])
    require(excluded == {"transfer-cleanup.json"}, "returned exclusions mismatch")
    if returned_membership_current:
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file()}
        require(actual - excluded == returned_names |
                {"returned-evidence-hashes.json"},
                "returned index membership mismatch")

    caps = manifest["return_contract"]
    parsed = decode_frames(
        root / "return-protocol/framed-stdout.bin",
        caps["maximum_framed_response_bytes"],
        caps["maximum_response_archive_bytes"],
        caps["maximum_control_payload_bytes"], caps["bulk_chunk_bytes"])
    inventory, tar_contents = inspect_archive(parsed["archive"])
    declaration = parsed["declaration"]
    require(declaration["schema"] ==
            "libwebp-backref-cost-attribution-v16-archive-v1" and
            declaration["status"] == "accepted" and
            declaration["compression_format"] == "tar+gzip" and
            declaration["member_count"] == inventory["member_count"] and
            declaration["inventory"]["member_count"] == inventory["member_count"] and
            declaration["inventory"]["inventory_sha256"] ==
            digest_bytes(canonical(inventory)) and
            declaration["inventory_sha256"] == digest_bytes(pretty(inventory)),
            "full inventory commitment mismatch")
    expected_regular = {"evidence/artifact-hashes.json", *(
        f"evidence/{name}" for name in inner_names)}
    require(set(tar_contents) == expected_regular,
            "tar/inner index membership mismatch")
    for name, value in tar_contents.items():
        require(value == (root / name.removeprefix("evidence/")).read_bytes(),
                f"tar/extracted bytes mismatch: {name}")

    controls = {frame["kind"]: frame["value"] for frame in parsed["frames"]
                if frame["value"] is not None}
    for kind in ("source-admission", "operator-status", "archive-build",
                 "lease-state", "bulk-declaration", "integrity-footer",
                 "cleanup-footer"):
        require(controls[kind] == load_json(root / f"return-protocol/{kind}.json"),
                f"persisted control mismatch: {kind}")
    stderr = root / "return-protocol/transport-stderr.bin"
    require(stderr.stat().st_size == 0 and digest_file(stderr) == EMPTY_SHA256,
            "transport stderr is nonempty")
    transfer = load_json(root / "transfer-cleanup.json")
    require(transfer["framed_stdout_bytes"] == len(parsed["raw"]) and
            transfer["framed_stdout_sha256"] == digest_bytes(parsed["raw"]) and
            transfer["transport_stderr_bytes"] == 0 and
            transfer["transport_stderr_sha256"] == EMPTY_SHA256 and
            transfer["transport_exit_code"] == 0 and
            transfer["transport_online_persistence_hash_count_verified"] is True and
            transfer["single_noninteractive_remote_session_count"] == 1 and
            transfer["stdin_half_closed_after_request"] is True and
            transfer["post_run_remote_cleanup_operations"] == 0 and
            transfer["cleanup_footer_verified"] is True and
            transfer["remote_cleanup_absence_proved"] is True and
            transfer["remote_cleanup_proof"] == controls["cleanup-footer"],
            "transfer/cleanup receipt mismatch")
    calibration = transfer["transport_calibration"]
    recomputed_throughput = int(
        len(parsed["archive"]) / (calibration["transaction_elapsed_ns"] / 1e9))
    require(calibration["archive_bytes"] == len(parsed["archive"]) and
            calibration["archive_sha256"] == digest_bytes(parsed["archive"]) and
            calibration["archive_cap_bytes"] ==
            caps["maximum_response_archive_bytes"] and
            calibration["archive_cap_margin_ratio"] ==
            caps["maximum_response_archive_bytes"] / len(parsed["archive"]) and
            calibration["chunk_bytes"] == caps["bulk_chunk_bytes"] and
            calibration["chunk_count"] == declaration["chunk_count"] and
            calibration["throughput_bytes_per_second"] == recomputed_throughput and
            calibration["transaction_timeout_seconds"] == 1800 and
            calibration["silent_operator_timeout_seconds"] == 900 and
            calibration["stream_progress_timeout_seconds"] == 15 and
            calibration["footer_progress_timeout_seconds"] == 15,
            "transport calibration recomputation mismatch")
    return {
        "inner_index": file_identity(root / "artifact-hashes.json"),
        "inner_indexed_files": len(inner_names),
        "returned_index": file_identity(root / "returned-evidence-hashes.json"),
        "returned_indexed_files": len(returned_names),
        "archive_bytes": len(parsed["archive"]),
        "archive_sha256": digest_bytes(parsed["archive"]),
        "archive_member_count": inventory["member_count"],
        "archive_inventory_canonical_sha256": digest_bytes(canonical(inventory)),
        "archive_inventory_pretty_sha256": digest_bytes(pretty(inventory)),
        "framed_stdout": parsed["identity"],
        "frame_count": parsed["frame_count"],
        "frame_kinds": parsed["frame_kinds"],
        "transport_stderr": file_identity(stderr),
        "framed_request_digest_only_receipt": {
            "bytes": transfer["framed_request_bytes"],
            "sha256": transfer["framed_request_sha256"],
        },
        "recomputed_transport_calibration": {
            "archive_cap_margin_ratio":
                caps["maximum_response_archive_bytes"] / len(parsed["archive"]),
            "framed_response_cap_margin_ratio":
                caps["maximum_framed_response_bytes"] / len(parsed["raw"]),
            "throughput_bytes_per_second_integer": recomputed_throughput,
            "transaction_elapsed_ns": calibration["transaction_elapsed_ns"],
            "cleanup_elapsed_ns": controls["cleanup-footer"][
                "elapsed_transaction_ns"],
        },
        "cleanup_last_and_absence": True,
        "lease_transfer_state": controls["lease-state"]["state"],
    }


def expected_profiles() -> list[dict]:
    rows = []
    ordinal = 0
    orders = (("baseline", "candidate"), ("candidate", "baseline"),
              ("baseline", "candidate"))
    for case_id in ("photo-large", "graphic-large"):
        for method in (4, 6):
            for repetition, pair in enumerate(orders):
                for variant in pair:
                    profile_id = (f"p{ordinal:02d}-{case_id}-m{method}-"
                                  f"{variant}-r{repetition}")
                    rows.append({"ordinal": ordinal, "profile_id": profile_id,
                                 "case_id": case_id, "method": method,
                                 "variant": variant,
                                 "repetition": repetition})
                    ordinal += 1
    return rows


def verify_process_receipt(receipt: dict) -> None:
    require(receipt["argument_text_collected"] is False and
            receipt["discovered_pid_signals"] == 0 and
            receipt["exact_identity_conflicts"] == [] and
            receipt["filesystem_identity_operations"] == [] and
            receipt["resolved_path_api_used"] is False and
            receipt["identity_fields"] == ["pid", "ppid", "comm"] and
            receipt["parsed_process_count"] > 0 and
            receipt.get("snapshot_bytes", 1) > 0 and
            HEX64.fullmatch(receipt["process_snapshot_sha256"]) is not None,
            "process isolation receipt mismatch")
    chain = receipt["verified_ancestor_chain"]
    require(chain and chain[-1]["pid"] == 1 and chain[-1]["ppid"] == 0,
            "ancestor chain does not terminate at PID 1")
    for left, right in zip(chain, chain[1:]):
        require(left["ppid"] == right["pid"], "ancestor PPID edge mismatch")
    for row in chain:
        require(row["raw_comm"] and row["lexical_basename"] and
                row["lexical_basename"] == row["raw_comm"].rsplit("/", 1)[-1],
                "opaque comm/lexical basename mismatch")


def verify_admission(manifest: dict, phase1_transaction: dict,
                     phase2_transaction: dict) -> dict:
    source = load_json(EXECUTION / "return-protocol/source-admission.json")
    require(source["schema"] ==
            "libwebp-backref-cost-attribution-v16-source-admission-receipt-v1" and
            source["status"] == "verified" and source["receipt_version"] == 1 and
            source["source_commit"] == PHASE1A and
            source["source_tree"] == SOURCE_TREE and
            source["source_bundle_sha256"] == source["admission"]["bundle_sha256"] and
            source["admission"]["bundle_verified_in_repository_context"] is True and
            source["admission"]["verification_repository_removed"] is True and
            source["admission"]["clean_status"] is True,
            "source admission mismatch")
    expected_hashes = {row["path"]: row["sha256"]
                       for row in manifest["frozen_artifacts"]}
    expected_hashes["scripts/backref_cost_attribution_v16_manifest.json"] = (
        digest_file(ROOT / "scripts/backref_cost_attribution_v16_manifest.json"))
    require(source["admission"]["source_hashes"] == expected_hashes,
            "source admission hash set mismatch")
    for name, expected in expected_hashes.items():
        require(digest_file(ROOT / name) == expected,
                f"current frozen source digest mismatch: {name}")
    verify_process_receipt(source["pre_operator_process_isolation"])

    diagnostic = load_json(EXECUTION / "diagnostic-admission.json")
    host = manifest["remote_host"]
    require(diagnostic["clock"] == "mach_continuous_time" and
            diagnostic["compiler_version_lines"] == host["compiler_version_lines"] and
            diagnostic["developer_dir"] == host["developer_dir"] and
            diagnostic["sdk_path"] == host["sdk_path"] and
            diagnostic["sdk_version"] == host["sdk_version"] and
            diagnostic["external_profiler_invocations"] == 0 and
            diagnostic["noninteractive"] is True and
            diagnostic["permission_or_attach_rights_required"] is False,
            "diagnostic/toolchain admission mismatch")
    for name, expected in manifest["diagnostic"]["executables"].items():
        require(diagnostic["executables"][name]["path"] == expected["path"] and
                diagnostic["executables"][name]["sha256"] == expected["sha256"],
                f"executable admission mismatch: {name}")

    build = load_json(EXECUTION / "build-identity.json")
    require(build["cflags"] == manifest["build"]["cflags"] and
            build["same_binary_for_both_variants"] is True and
            build["required_symbols"] == manifest["acceptance"]["required_symbols"] and
            HEX64.fullmatch(build["runner_sha256"]) is not None and
            build["command"][0:3] == ["/usr/bin/make", "-f", "makefile.unix"] and
            "WEBP_ENABLE_METAL=0" in build["command"] and
            "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT=1" in build["command"],
            "build identity mismatch")

    resources = []
    process_receipts = 1
    for label in ("admission", "pre-profiles", "post-profiles"):
        record = load_json(EXECUTION / f"resource-admission-{label}.json")
        require(record["label"] == label and
                record["hardware_model"] == host["hardware_model"] and
                record["cpu_brand"] == host["cpu_brand"] and
                record["physical_memory_bytes"] == host["physical_memory_bytes"] and
                record["available_memory_bytes"] >=
                manifest["resources"]["minimum_available_memory_bytes"] and
                record["available_disk_bytes"] >=
                manifest["resources"]["minimum_available_disk_bytes"] and
                record["settings_changed"] is False and
                "AC Power" in record["pmset_batt"] and
                "lowpowermode         0" in record["pmset_custom"] and
                all(line in record["pmset_thermal"]
                    for line in host["required_thermal_lines"]),
                f"resource admission mismatch: {label}")
        verify_process_receipt(record["process_isolation"])
        process_receipts += 1
        resources.append({
            "label": label,
            "available_memory_bytes": record["available_memory_bytes"],
            "available_disk_bytes": record["available_disk_bytes"],
            "process_snapshot_bytes": record["process_isolation"]["snapshot_bytes"],
            "process_snapshot_sha256":
                record["process_isolation"]["process_snapshot_sha256"],
        })

    completeness = load_json(EXECUTION / "profile-completeness.json")
    require(len(completeness) == 24, "profile completeness count mismatch")
    for row in completeness:
        require(row["output_records"] == 5 and row["stage_records"] == 5 and
                row["retained_stage_records"] == 4,
                "profile completeness row mismatch")
        verify_process_receipt(row["process_before"])
        verify_process_receipt(row["process_after"])
        process_receipts += 2

    timer = load_json(EXECUTION / "timer-validation.json")
    require(timer["schema"] ==
            "libwebp-backref-cost-attribution-v16-timer-check-v1" and
            timer["clock_reads"] == 4096 and timer["monotonic"] is True and
            timer["positive_deltas"] > 0 and
            timer["mean_read_delta_ns"] <=
            manifest["acceptance"]["maximum_mean_clock_read_delta_ns"],
            "timer admission mismatch")
    lease = load_json(EXECUTION / "lease-record.json")
    lease_state = load_json(EXECUTION / "return-protocol/lease-state.json")
    require(lease["schema"] == manifest["schemas"]["lease"] and
            lease["acquisition_attempted"] is True and lease["acquired"] is True and
            lease["released"] is True and lease_state["state"] == "verified" and
            lease_state["receipt"] == lease and
            phase1_transaction["lease_transfer_state"] == "not-attempted" and
            phase2_transaction["lease_transfer_state"] == "verified",
            "lease acquisition/release/transfer mismatch")
    return {
        "source_commit": source["source_commit"],
        "source_tree": source["source_tree"],
        "source_hash_count": len(expected_hashes),
        "source_bundle_digest_only_receipt": source["source_bundle_sha256"],
        "runner_sha256": build["runner_sha256"],
        "build_stdout_digest_only": {"bytes": build["build_stdout_bytes"],
                                      "sha256": build["build_stdout_sha256"]},
        "build_stderr_digest_only": {"bytes": build["build_stderr_bytes"],
                                      "sha256": build["build_stderr_sha256"]},
        "nm_output_digest_only": {"bytes": build["nm_output_bytes"],
                                   "sha256": build["nm_output_sha256"]},
        "resources": resources,
        "process_isolation_receipts": process_receipts,
        "timer_validation": timer,
        "lease": lease,
        "metal_enabled": False,
        "cuda_invocations": 0,
        "external_profiler_invocations": 0,
    }


def verify_correctness(manifest: dict) -> dict:
    rows = load_json(EXECUTION / "correctness.json")
    counters = load_json(EXECUTION / "selected-dp-counter-check.json")
    expected_cells = [(case, method) for case in ("photo-large", "graphic-large")
                      for method in (4, 6)]
    require([(row["case_id"], row["method"]) for row in rows] == expected_cells and
            [(row["case_id"], row["method"]) for row in counters] == expected_cells,
            "correctness/counter cell order mismatch")
    corpus = {row["case_id"]: row for row in manifest["corpus"]}
    for row in rows:
        require(row["baseline_candidate_equal"] is True and
                row["repeat_deterministic"] is True and
                row["decoded_rgb_equal"] is True and
                row["input_immutable"] is True and
                row["input_sha256_before"] == row["input_sha256_after"] ==
                corpus[row["case_id"]]["sha256"] and
                row["bitstream_bytes"] > 0 and
                HEX64.fullmatch(row["bitstream_sha256"]) is not None,
                "correctness evidence mismatch")
    for row in counters:
        baseline, candidate = row["baseline"], row["candidate"]
        require(row["bitstreams_equal"] is True and
                baseline["schema"] == candidate["schema"] ==
                "libwebp-backref-cost-attribution-v16-counter-check-v1" and
                baseline["variant"] == "baseline" and
                candidate["variant"] == "candidate" and
                baseline["selector_evaluations"] > 0 and
                baseline["selector_evaluations"] == baseline["baseline_dp_calls"] and
                baseline["candidate_dp_calls"] == 0 and
                candidate["selector_evaluations"] > 0 and
                candidate["selector_evaluations"] == candidate["candidate_dp_calls"] and
                candidate["baseline_dp_calls"] == 0 and
                baseline["post_reset_zero"] is True and
                candidate["post_reset_zero"] is True and
                baseline["bitstream_bytes"] == candidate["bitstream_bytes"] and
                baseline["bitstream_fnv1a64"] == candidate["bitstream_fnv1a64"],
                "selector-once/selected-DP counter evidence mismatch")
    return {
        "cells": 4, "correctness_encodes": 16,
        "baseline_encodes": 8, "candidate_encodes": 8,
        "decoded_pixel_comparisons": 16,
        "input_hash_before_after_comparisons": 4,
        "input_hash_fields": 8,
        "bitstream_sha256_by_cell": [
            {key: row[key] for key in
             ("case_id", "method", "bitstream_bytes", "bitstream_sha256")}
            for row in rows],
        "counter_cells": 4, "counter_encodes": 8,
        "selector_once_and_one_selected_dp": True,
        "opposite_body_zero": True, "post_reset_zero": True,
        "correctness_raw": file_identity(EXECUTION / "correctness.json"),
        "counter_raw": file_identity(
            EXECUTION / "selected-dp-counter-check.json"),
        "compact_boundary": (
            "Encoded products and corpus bytes were intentionally omitted after "
            "the indexed raw equality/hash/pixel/input records were emitted."),
    }


def profile_statistics(manifest: dict) -> tuple[dict, dict]:
    plan = load_json(EXECUTION / "profile-plan.json")
    commands = load_jsonl(EXECUTION / "commands.jsonl")
    expected = expected_profiles()
    require(len(plan) == len(commands) == len(expected) == 24,
            "plan/command inventory mismatch")
    all_stage_names: set[str] = set()
    profiles: dict[tuple[str, int, str, int], dict] = {}
    pids: set[int] = set()
    timer_rows = 0
    runner_records = 0
    stage_records = 0
    retained_records = 0
    warmups = 0
    for frozen, planned, command in zip(expected, plan, commands):
        for key, value in frozen.items():
            require(planned[key] == command[key] == value,
                    f"plan/command order mismatch: {frozen['profile_id']} {key}")
        profile_id = frozen["profile_id"]
        require(PROFILE_ID.fullmatch(profile_id) is not None,
                f"malformed profile id: {profile_id}")
        argv = command["command"]
        env = argv[1:argv.index(next(arg for arg in argv if arg.endswith(
            "/backref_cost_attribution_v16_experiment_runner")))]
        require(argv[0] == "/usr/bin/env" and argv[-7:] == [
            "profile", next(arg for arg in argv if arg.endswith(
                f"/{frozen['case_id']}.ppm")), frozen["case_id"],
            str(frozen["method"]), frozen["variant"], "1", "4"],
            f"runner command mismatch: {profile_id}")
        require("WEBP_BENCHMARK_SESSION=exclusive" in env and
                "WEBP_BACKREF_COST_ATTRIBUTION_V16_TIMERS=1" in env and
                not any(item.startswith("CUDA_VISIBLE_DEVICES=") for item in env),
                f"profile environment mismatch: {profile_id}")
        candidate_flags = [item for item in env if item.startswith(
            "WEBP_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT=")]
        require(candidate_flags == ([
            "WEBP_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT=1"]
            if frozen["variant"] == "candidate" else []),
            f"runtime selector mismatch: {profile_id}")

        runner_path = EXECUTION / "runner" / f"{profile_id}.jsonl"
        stderr_path = EXECUTION / "runner" / f"{profile_id}.stderr"
        stage_path = EXECUTION / "stages" / f"{profile_id}.jsonl"
        require(command["exit_code"] == 0 and
                command["stdout_bytes"] == runner_path.stat().st_size and
                command["stdout_sha256"] == digest_file(runner_path) and
                command["stderr_bytes"] == stderr_path.stat().st_size == 0 and
                command["stderr_sha256"] == digest_file(stderr_path) == EMPTY_SHA256,
                f"runner transport mismatch: {profile_id}")
        runner = load_jsonl(runner_path)
        stages = load_jsonl(stage_path)
        require(len(runner) == len(stages) == 5, f"profile row count mismatch: {profile_id}")
        require([row["iteration"] for row in runner] == list(range(5)) and
                [row["sample_role"] for row in runner] ==
                ["warmup", "retained", "retained", "retained", "retained"] and
                [row["encode_index"] for row in stages] == list(range(5)) and
                [row["sample_role"] for row in stages] ==
                ["warmup", "warm", "warm", "warm", "warm"],
                f"warmup/retained lifecycle mismatch: {profile_id}")
        runner_identity = {(row["bitstream_bytes"], row["bitstream_fnv1a64"])
                           for row in runner}
        require(len(runner_identity) == 1, f"profile output nondeterminism: {profile_id}")
        values: dict[str, list[int]] = defaultdict(list)
        profile_stage_names: list[str] | None = None
        for index, (out, stage) in enumerate(zip(runner, stages)):
            require(out["schema"] ==
                    "libwebp-backref-cost-attribution-v16-output-v1" and
                    stage["schema"] == "libwebp-encoder-stage-v1" and
                    out["case_id"] == stage["case_id"] == frozen["case_id"] and
                    out["method"] == stage["method"] == frozen["method"] and
                    out["variant"] == stage["backend"] == frozen["variant"] and
                    out["bitstream_bytes"] == stage["output_bytes"] and
                    stage["run_id"] == profile_id and stage["ok"] is True and
                    stage["error_code"] == 0 and stage["width"] == 3000 and
                    stage["height"] == 2000 and stage["pixels"] == 6000000 and
                    stage["lossless"] is True and stage["exact"] is True and
                    stage["thread_level"] == 0 and
                    stage["metal_cross_color"] is False and
                    stage["metal_hash"] is False,
                    f"runner/stage row mismatch: {profile_id}:{index}")
            names = list(stage["stages"])
            if profile_stage_names is None:
                profile_stage_names = names
                all_stage_names.update(names)
            require(names == profile_stage_names and
                    all(name in stage["stages"]
                        for name in manifest["acceptance"]["required_timer_stages"]),
                    f"timer stage set mismatch: {profile_id}:{index}")
            nested = stage["stages"]
            selected = stage["selected_dp_calls"]
            require(selected > 0 and
                    stage["selector_evaluations"] == selected ==
                    nested["backref_cost_dp_total"]["calls"] ==
                    nested["backref_cost_dp_setup"]["calls"] ==
                    nested["backref_cost_dp_steady"]["calls"] and
                    nested["backref_cost_dp_setup"]["ns"] +
                    nested["backref_cost_dp_steady"]["ns"] <=
                    nested["backref_cost_dp_total"]["ns"] and
                    nested["backref_cost_dp_total"]["ns"] +
                    nested["backref_cost_traceback"]["ns"] +
                    nested["backref_cost_materialize"]["ns"] <=
                    nested["lossless_backward_refs"]["ns"],
                    f"timer accounting mismatch: {profile_id}:{index}")
            if frozen["variant"] == "candidate":
                require(stage["candidate_dp_calls"] == selected and
                        stage["baseline_dp_calls"] == 0,
                        f"candidate body ownership mismatch: {profile_id}:{index}")
            else:
                require(stage["baseline_dp_calls"] == selected and
                        stage["candidate_dp_calls"] == 0,
                        f"baseline body ownership mismatch: {profile_id}:{index}")
            timer_rows += 1
            if index > 0:
                values["total_ns"].append(stage["total_ns"])
                for name in profile_stage_names:
                    values[name].append(nested[name]["ns"])
        pid_set = {row["pid"] for row in stages}
        require(len(pid_set) == 1 and not (pid_set & pids),
                f"process lifecycle/PID reuse mismatch: {profile_id}")
        pids |= pid_set
        medians = {name: statistics.median(sample) for name, sample in values.items()}
        profiles[(frozen["case_id"], frozen["method"], frozen["variant"],
                  frozen["repetition"])] = {
            "profile_id": profile_id, "medians_ns": medians,
            "stage_names": profile_stage_names,
            "stage_shares": {name: medians[name] / medians["total_ns"]
                             for name in profile_stage_names},
        }
        runner_records += 5
        stage_records += 5
        retained_records += 4
        warmups += 1

    require(all_stage_names, "no stage names")
    required_stages = manifest["acceptance"]["required_timer_stages"]
    cells = []
    repeatability_pass = True
    total_ratio_comparisons = 0
    share_range_comparisons = 0
    for case_id in ("photo-large", "graphic-large"):
        for method in (4, 6):
            cell_stage_names = profiles[
                (case_id, method, "baseline", 0)]["stage_names"]
            require(all(profiles[(case_id, method, variant, repetition)][
                        "stage_names"] == cell_stage_names
                        for variant in ("baseline", "candidate")
                        for repetition in range(3)),
                    f"stage inventory differs within cell: {case_id}/m{method}")
            variants = {}
            for variant in ("baseline", "candidate"):
                rows = [profiles[(case_id, method, variant, repetition)]
                        for repetition in range(3)]
                aggregate = {
                    name: statistics.median(
                        [row["medians_ns"][name] for row in rows])
                    for name in ("total_ns", *cell_stage_names)}
                total_values = [row["medians_ns"]["total_ns"] for row in rows]
                total_ratio = max(total_values) / min(total_values)
                total_ratio_comparisons += 1
                share_ranges = {
                    name: max(row["stage_shares"][name] for row in rows) -
                    min(row["stage_shares"][name] for row in rows)
                    for name in required_stages}
                share_range_comparisons += len(share_ranges)
                passed = total_ratio <= 2.0 and all(
                    value <= 0.10 for value in share_ranges.values())
                repeatability_pass &= passed
                variants[variant] = {
                    "profile_ids": [row["profile_id"] for row in rows],
                    "profile_medians_ns": {
                        name: [row["medians_ns"][name] for row in rows]
                        for name in ("total_ns", *cell_stage_names)},
                    "median_of_profile_medians_ns": aggregate,
                    "stage_share_of_total": {
                        name: aggregate[name] / aggregate["total_ns"]
                        for name in cell_stage_names},
                    "repeatability": {
                        "retained_total_median_max_min_ratio": total_ratio,
                        "required_stage_share_ranges": share_ranges,
                        "maximum_required_stage_share_range": max(share_ranges.values()),
                        "pass": passed,
                    },
                }
            deltas = {}
            for name in ("total_ns", *cell_stage_names):
                baseline = variants["baseline"]["median_of_profile_medians_ns"][name]
                candidate = variants["candidate"]["median_of_profile_medians_ns"][name]
                paired = []
                for repetition in range(3):
                    b = profiles[(case_id, method, "baseline", repetition)][
                        "medians_ns"][name]
                    c = profiles[(case_id, method, "candidate", repetition)][
                        "medians_ns"][name]
                    paired.append({
                        "repetition": repetition, "delta_ns": c - b,
                        "delta_fraction": None if b == 0 else c / b - 1.0,
                    })
                paired_fractions = [row["delta_fraction"] for row in paired]
                deltas[name] = {
                    "aggregate_delta_ns": candidate - baseline,
                    "aggregate_delta_fraction": (
                        None if baseline == 0 else candidate / baseline - 1.0),
                    "candidate_minus_baseline_share_points": (
                        None if name == "total_ns" else
                        variants["candidate"]["stage_share_of_total"][name] -
                        variants["baseline"]["stage_share_of_total"][name]),
                    "paired_by_repetition": paired,
                    "paired_delta_fraction_median": (
                        None if any(value is None for value in paired_fractions)
                        else statistics.median(paired_fractions)),
                    "paired_direction_consistent": (
                        all(row["delta_ns"] > 0 for row in paired) or
                        all(row["delta_ns"] < 0 for row in paired) or
                        all(row["delta_ns"] == 0 for row in paired)),
                }
            cells.append({"case_id": case_id, "method": method,
                          "variants": variants, "deltas": deltas})
    inventory = {
        "profile_processes": len(profiles), "unique_runner_pids": len(pids),
        "warmups": warmups, "retained_records": retained_records,
        "runner_records": runner_records, "stage_records": stage_records,
        "timer_accounting_rows": timer_rows,
        "serial_direct_process_order": [row["profile_id"] for row in expected],
        "variant_order": [["baseline", "candidate"],
                          ["candidate", "baseline"],
                          ["baseline", "candidate"]],
        "all_recorded_stages": sorted(all_stage_names),
        "required_timer_stages": required_stages,
        "cuda_invocations": 0, "profiler_invocations": 0,
        "retries": 0, "reruns": 0, "parallel_profile_processes": 1,
        "commands_raw": file_identity(EXECUTION / "commands.jsonl"),
        "profile_plan_raw": file_identity(EXECUTION / "profile-plan.json"),
    }
    statistics_record = {
        "method": (
            "For each process, median each metric across its four retained rows; "
            "for each variant/cell, median the three process medians. Stage share "
            "is that stage median divided by whole-encode median. Deltas are "
            "candidate/baseline-1; paired deltas compare equal repetitions."),
        "uncertainty_rule": (
            "Frozen descriptive repeatability only: three retained-total process "
            "medians must have max/min <=2.0 and each required stage-share range "
            "must be <=0.10 absolute. No confidence interval, hypothesis test, "
            "pooling, prior sample, threshold, or outlier removal is authorized."),
        "total_ratio_comparisons": total_ratio_comparisons,
        "required_stage_share_range_comparisons": share_range_comparisons,
        "repeatability_pass": repeatability_pass,
        "cells": cells,
    }
    require(repeatability_pass, "frozen repeatability gate failed")
    return inventory, statistics_record


def source_static_audit() -> dict:
    backrefs = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    body = (ROOT / "src/enc/backward_references_cost_distance_only_enc.inc").read_text()
    control = (ROOT /
        "src/enc/backref_cost_attribution_v16_experiment_enc.c").read_text()
    cmake = (ROOT / "CMakeLists.txt").read_text()
    makefile = (ROOT / "makefile.unix").read_text()
    runner = (ROOT /
        "tools/backref_cost_attribution_v16_experiment_runner.c").read_text()
    marker = "// V16 preserves the frozen selector-once and one-selected-DP boundary."
    marker_offset = backrefs.index(marker)
    block_start = backrefs.rfind(
        "#elif defined(WEBP_USE_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT)",
        0, marker_offset)
    block_end = backrefs.index("#else", marker_offset)
    v16_block = backrefs[block_start:block_end]
    require(v16_block.count("VP8LBackrefCostAttributionV16ExperimentEnabled()") == 1 and
            v16_block.count("VP8LBackrefCostAttributionV16RecordSelector()") == 1 and
            v16_block.count("BackwardReferencesHashChainDistanceOnlySpecialized(") == 1 and
            v16_block.count("BackwardReferencesHashChainDistanceOnly(") == 1 and
            "if (use_candidate)" in v16_block and "} else {" in v16_block,
            "selector-once closed branch static audit failed")
    require(body.count("WEBP_PROFILE_BACKREF_COST_DP_SETUP") == 2 and
            body.count("WEBP_PROFILE_BACKREF_COST_DP_STEADY") == 2 and
            "CostManagerInit(cost_manager" in body and
            body.index("WEBP_PROFILE_BACKREF_COST_DP_STEADY") < body.index("for (i = 1;") and
            "CostManagerClear(cost_manager);" in body and
            "WebPProfileStage" not in body[body.index("for (i = 1;"):body.index(
                "WebPProfileStageEnd(WEBP_PROFILE_BACKREF_COST_DP_STEADY")],
            "DP timer boundary static audit failed")
    require("strcmp(value, \"1\") == 0" in control and
            "__thread" in control and
            "VP8LBackrefCostAttributionV16ResetCounters" in control,
            "runtime fallback/TLS counter static audit failed")
    require("option(WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT" in cmake and
            "diagnostic-only" in cmake and
            "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V16_EXPERIMENT ?= 0" in makefile and
            '"metal": false' in
            (ROOT / "scripts/backref_cost_attribution_v16_manifest.json").read_text() and
            "memcmp(decoded, expected, expected_size) != 0" in runner,
            "default-off/decoded-pixel static audit failed")
    public_diff = git("diff", "--name-only", BASE, PHASE1A, "--", "src/webp")
    require(public_diff == "", "public header changed in Phase 1A")
    return {
        "selector_evaluated_once_before_dp_mutation": True,
        "closed_if_else_exactly_one_selected_dp_body": True,
        "opposite_preprocessor_fallthrough_unreachable": True,
        "dp_total_includes_selected_body_cleanup": True,
        "dp_setup_allocation_through_cost_manager_init": True,
        "dp_steady_initial_literal_and_pixel_loop_only": True,
        "traceback_and_materialization_separate": True,
        "per_pixel_or_push_interval_clocks": 0,
        "exact_runtime_value_one_enables_candidate_other_values_fallback": True,
        "thread_local_resettable_counters": True,
        "public_header_changes_from_baseline": 0,
        "production_default": "OFF",
    }


def main() -> int:
    manifest_path = ROOT / "scripts/backref_cost_attribution_v16_manifest.json"
    schemas_path = ROOT / "scripts/backref_cost_attribution_v16_schemas.json"
    protocol_path = ROOT / "doc/backref-cost-attribution-v16-protocol-20260819.md"
    manifest = load_json(manifest_path)
    schemas = load_json(schemas_path)
    authorization = load_json(DESIGN / "phase1b-authorization.json")

    require(git("rev-parse", f"{PHASE1A}^") == BASE and
            git("rev-parse", f"{PHASE1B}^") == PHASE1A and
            git("rev-parse", f"{PHASE2}^") == PHASE1B,
            "linear ancestry mismatch")
    phase1b_diff = git("diff", "--name-status", PHASE1A, PHASE1B).splitlines()
    allowed_prefixes = (
        "evidence/backref-cost-attribution-v16-design/rehearsal/",
        "evidence/backref-cost-attribution-v16-design/phase1b-rehearsal-hashes.json",
        "evidence/backref-cost-attribution-v16-design/phase1b-authorization.json")
    require(phase1b_diff and all(row.startswith("A\t") and
            row.split("\t", 1)[1].startswith(allowed_prefixes)
            for row in phase1b_diff), "Phase 1B additions-only rule failed")
    phase2_diff = git("diff", "--name-status", PHASE1B, PHASE2).splitlines()
    require(phase2_diff and all(row.startswith("A\t") and row.split("\t", 1)[1].startswith(
        "evidence/backref-cost-attribution-v16-execution-20260819/")
        for row in phase2_diff), "Phase 2 evidence-only rule failed")

    require(manifest["schema"] ==
            "libwebp-backref-cost-attribution-v16-frozen-protocol-v1" and
            manifest["protocol_version"] == schemas["protocol_version"] == 7 and
            len(schemas["schemas"]) == len(set(schemas["schemas"])) == 19,
            "manifest/schema catalog mismatch")
    phase1_local_path = DESIGN / "phase1-local-validation.json"
    phase1_local = load_json(phase1_local_path)
    require(phase1_local["schema"] ==
            "libwebp-backref-cost-attribution-v16-phase1-local-validation-v1" and
            phase1_local["base_commit"] == BASE and
            phase1_local["performance_samples"] == 0 and
            phase1_local["timed_workloads"] == 0 and
            all(row["status"].startswith("PASS")
                for row in phase1_local["checks"]) and
            phase1_local["checks"][6]["guard_count"] == 36 and
            phase1_local["checks"][7]["correctness_encodes"] == 16 and
            phase1_local["checks"][7]["counter_cells"] == 4 and
            phase1_local["checks"][7]["boundary_fixtures"] == 16 and
            phase1_local["checks"][7]["sanitizer_configurations"] == 2 and
            phase1_local["checks"][7]["public_api_abi_equal"] is True and
            phase1_local["checks"][7]["default_omission"] is True,
            "Phase 1 local prerequisite evidence mismatch")
    for row in manifest["frozen_artifacts"]:
        require(digest_file(ROOT / row["path"]) == row["sha256"],
                f"frozen artifact hash mismatch: {row['path']}")
    require(authorization["schema"] in schemas["schemas"] and
            authorization["timed_execution_authorized"] is True and
            authorization["production_promotion_authorized"] is False and
            authorization["source_commit"] == PHASE1A and
            authorization["source_tree"] == SOURCE_TREE and
            authorization["manifest_sha256"] == digest_file(manifest_path) and
            authorization["protocol_sha256"] == digest_file(protocol_path) and
            authorization["schema_catalog_sha256"] == digest_file(schemas_path),
            "Phase 1B authorization envelope mismatch")

    phase1b_index = load_json(DESIGN / "phase1b-rehearsal-hashes.json")
    phase1_names = verify_rows(REHEARSAL, phase1b_index["artifacts"])
    actual_phase1 = {path.relative_to(REHEARSAL).as_posix()
                     for path in REHEARSAL.rglob("*") if path.is_file()}
    require(phase1b_index["schema"] ==
            "libwebp-backref-cost-attribution-v16-phase1b-hash-index-v1" and
            len(phase1_names) == 22 and phase1_names == actual_phase1 and
            authorization["rehearsal_hash_index_sha256"] == digest_file(
                DESIGN / "phase1b-rehearsal-hashes.json"),
            "Phase 1B rehearsal hash coverage mismatch")
    for mapping_name in ("rehearsal_receipt_hashes",
                         "required_control_receipt_hashes"):
        for name, expected in authorization[mapping_name].items():
            require(digest_file(REHEARSAL / name) == expected,
                    f"authorization receipt hash mismatch: {name}")

    phase1_transaction = verify_transaction(
        REHEARSAL, 7, 17, False, manifest)
    phase2_transaction = verify_transaction(
        EXECUTION, 85, 95, True, manifest)
    admission = verify_admission(manifest, phase1_transaction, phase2_transaction)
    correctness = verify_correctness(manifest)
    inventory, statistics_record = profile_statistics(manifest)
    static = source_static_audit()

    operator = load_json(EXECUTION / "operator-status.json")
    remote_operator = load_json(EXECUTION / "return-protocol/operator-status.json")
    require(operator["status"] == "complete" and operator["mode"] == "run" and
            operator["source_commit"] == remote_operator["source_commit"] == PHASE1A and
            operator["source_tree"] == remote_operator["source_tree"] == SOURCE_TREE and
            operator["benchmark_lease_acquisition_attempted"] is True and
            operator["production_promotion_authorized"] is False and
            remote_operator["operator_exit_code"] == 0 and
            remote_operator["production_promotion_authorized"] is False,
            "operator completion/status mismatch")

    gates = {
        "linear_phase_ancestry": "PASS",
        "phase1b_additions_only_and_complete_hash_index": "PASS_22_FILES",
        "frozen_manifest_protocol_schema_and_source_hashes": "PASS",
        "phase1_rehearsal_transport_archive_integrity_cleanup": "PASS",
        "phase2_inner_artifact_hashes_and_coverage": "PASS_85_FILES",
        "phase2_returned_hashes_and_coverage": "PASS_95_FILES",
        "response_archive_caps_frames_transfer_extraction_integrity": "PASS",
        "source_toolchain_device_resource_process_ownership": "PASS",
        "exclusive_lease_acquired_and_released": "PASS",
        "correctness_pixels_determinism_fallback_abi_input_immutability": "PASS",
        "selector_once_one_selected_dp_and_timer_nesting": "PASS_120_ROWS",
        "exact_profile_corpus_order_counts_serial_lifecycle": "PASS",
        "frozen_repeatability_and_uncertainty_rules": "PASS_96_COMPARISONS",
        "production_promotion_forbidden": "PASS_NO_PROMOTION",
    }
    record = {
        "schema":
            "libwebp-backref-cost-attribution-v16-phase3-evaluation-consequence-v1",
        "evaluation_date": "2026-08-19",
        "evaluator": "Sol/high",
        "input_commits": {"main_baseline": BASE, "phase1a": PHASE1A,
                          "phase1b": PHASE1B, "phase2": PHASE2},
        "frozen_identity": {
            "manifest": file_identity(manifest_path),
            "protocol": file_identity(protocol_path),
            "schema_catalog": file_identity(schemas_path),
            "schema_count": len(schemas["schemas"]),
            "phase1b_hash_index": file_identity(
                DESIGN / "phase1b-rehearsal-hashes.json"),
            "phase1b_authorization": file_identity(
                DESIGN / "phase1b-authorization.json"),
        },
        "raw_provenance": {
            "phase1_rehearsal_root": REHEARSAL.relative_to(ROOT).as_posix(),
            "phase1": phase1_transaction,
            "phase2_execution_root": EXECUTION.relative_to(ROOT).as_posix(),
            "phase2": phase2_transaction,
            "retained_hash_verdict": (
                "Every SHA-256 whose source bytes are retained was recomputed; "
                "both hash indexes have exact frozen coverage."),
            "digest_only_receipts": [
                "framed request", "source bundle", "representative request payload",
                "raw process snapshots", "build stdout/stderr", "nm output",
                "correctness WebP products and corpus bytes"],
        },
        "admission_and_ownership": admission,
        "correctness_and_semantics": {
            **correctness, "source_static_audit": static,
            "phase1_local_prerequisite_raw": file_identity(phase1_local_path),
            "phase1_local_prerequisite_checks": {
                "checks": len(phase1_local["checks"]), "guard_count": 36,
                "boundary_fixtures": 16, "sanitizer_configurations": 2,
                "public_api_abi_equal": True, "default_omission": True,
            },
        },
        "raw_inventory": inventory,
        "recomputed_statistics": statistics_record,
        "gate_verdicts": gates,
        "decision": {
            "selected_consequence": 2,
            "exact_decision": (
                "RETAIN_V16_DEFAULT_OFF_AS_FORENSIC_EVIDENCE_AND_REJECT_"
                "PRODUCTION_PROMOTION"),
            "rationale": (
                "All frozen diagnostic/evidence gates pass, but the measured "
                "candidate is not consistently beneficial: photo DP improves "
                "while graphic DP regresses, and whole-encode paired directions "
                "are inconsistent in three of four case/method cells. The frozen "
                "protocol also expressly forbids promotion from this diagnostic."),
            "production_consequence": "NONE",
            "production_status": (
                "UNCHANGED; V16 remains compile-time default-off, runtime exact-"
                "opt-in diagnostic code and is not promoted."),
            "production_files_modified_in_phase3": [],
            "broader_interval_family_status": (
                "NO_CLOSE_OR_REOPEN_DECISION; frozen consistency support is absent."),
            "next_experiment_proposed": False,
            "next_experiment_executed": False,
        },
        "limitations": [
            "The frozen compact boundary intentionally retains digest/count receipts, "
            "not bytes, for the request, source bundle, process snapshots, build/nm "
            "streams, corpus, and correctness products; their receipt fields cannot "
            "be independently rehashed without violating the frozen evidence boundary.",
            "Remote absence is established by the cleanup-last in-session receipt; "
            "the protocol forbids a follow-up remote inspection and Phase 3 performed none.",
            "Coarse nested timers bound stages but cannot identify PushInterval self "
            "time, call-stack, code-layout, branch-predictor, or cache causality.",
            "Only two 3000x2000 corpus cases, methods 4 and 6, three process repetitions, "
            "and four retained encodes per process are admitted; no pooling or "
            "generalization beyond those cells is authorized.",
            "The frozen statistical rule is descriptive repeatability only; it defines "
            "no confidence interval or significance test.",
        ],
        "blocker": None,
    }
    OUTPUT.write_bytes(pretty(record))
    print(json.dumps({
        "status": "PASS", "output": OUTPUT.relative_to(ROOT).as_posix(),
        "output_bytes": OUTPUT.stat().st_size,
        "output_sha256": digest_file(OUTPUT),
        "selected_consequence": record["decision"]["selected_consequence"],
        "exact_decision": record["decision"]["exact_decision"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
