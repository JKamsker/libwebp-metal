#!/usr/bin/env python3
"""Read-only Phase 2 audit for the frozen alignment-v3 handoff.

This auditor deliberately has no SSH, network, lease, benchmark, profiler, or
remote-cleanup path.  It replays only committed Phase 1 evidence and local
validators, then reports the independent authority decision.
"""

from __future__ import annotations

import collections
import hashlib
import io
import json
import re
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import backref_cost_specialization_alignment_v3_admission as admission
import backref_cost_specialization_alignment_v3_archive as archive_protocol
import backref_cost_specialization_alignment_v3_transport as transport
import execute_backref_cost_specialization_alignment_v3 as executor


ROOT = Path(__file__).resolve().parents[1]
BASE = "c208d6ed33b0ee5e84ba02e78696879266658e7e"
PHASE1A = "f6735570eb2a81faa60544b289fb0207b8cde873"
PHASE1B = "3b28d9066d94d9397b2b36a09540547adee9efa5"
EVIDENCE = ROOT / "evidence/backref-cost-specialization-alignment-v3-design"
REHEARSAL = EVIDENCE / "rehearsal"
PROTOCOL = REHEARSAL / "return-protocol"
AUTH = EVIDENCE / "phase1b-authorization.json"
HASH_INDEX = EVIDENCE / "phase1b-rehearsal-hashes.json"
MANIFEST = ROOT / "scripts/backref_cost_specialization_alignment_v3_manifest.json"
SCHEMAS = ROOT / "scripts/backref_cost_specialization_alignment_v3_schemas.json"
TRANSPORT = ROOT / "scripts/backref_cost_specialization_alignment_v3_transport.py"
PROTOCOL_DOC = ROOT / "doc/backref-cost-specialization-alignment-v3-protocol-20260820.md"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    return result.stdout.strip()


def git_bytes(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load(path: Path) -> dict:
    value = transport.strict_json_loads(path.read_bytes())
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def git_blob_sha(commit: str, path: str) -> str:
    return digest_bytes(git_bytes("show", f"{commit}:{path}"))


class SizedValue:
    """Avoid materializing the already-hashed 23 MiB request for ACK replay."""

    def __init__(self, size: int):
        self.size = size

    def __len__(self) -> int:
        return self.size


def verify_hash_index() -> dict:
    index = load(HASH_INDEX)
    rows = index.get("artifacts")
    if index.get("schema") != \
            "libwebp-backref-cost-specialization-alignment-v3-phase1b-hash-index-v1":
        raise RuntimeError("Phase 1B hash-index schema mismatch")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Phase 1B hash-index is empty")
    observed = {}
    prior = ""
    for row in rows:
        relative = row.get("path")
        if not isinstance(relative, str) or relative <= prior or \
                relative.startswith("/") or ".." in Path(relative).parts:
            raise RuntimeError("Phase 1B hash-index is unsafe or unordered")
        path = REHEARSAL / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"missing or symlinked rehearsal artifact: {relative}")
        if path.stat().st_size != row.get("bytes") or digest(path) != row.get("sha256"):
            raise RuntimeError(f"rehearsal artifact digest mismatch: {relative}")
        observed[relative] = row["sha256"]
        prior = relative
    actual = {
        path.relative_to(REHEARSAL).as_posix()
        for path in REHEARSAL.rglob("*") if path.is_file()
    }
    if actual != set(observed):
        raise RuntimeError("Phase 1B hash-index membership mismatch")
    stdout = next(row for row in rows
                  if row["path"] == "return-protocol/channel-stdout.bin")
    response = next(row for row in rows
                    if row["path"] == "return-protocol/framed-response.bin")
    stderr = next(row for row in rows
                  if row["path"] == "return-protocol/transport-stderr.bin")
    return {
        "schema": index["schema"],
        "index_sha256": digest(HASH_INDEX),
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "channel_stdout_bytes": stdout["bytes"],
        "channel_stdout_sha256": stdout["sha256"],
        "framed_response_bytes": response["bytes"],
        "framed_response_sha256": response["sha256"],
        "transport_stderr_bytes": stderr["bytes"],
        "transport_stderr_sha256": stderr["sha256"],
    }


def replay_channel() -> dict:
    ready = load(PROTOCOL / "ready.json")
    declaration = load(PROTOCOL / "request-declaration.json")
    progress = load(PROTOCOL / "request-progress.json")
    transfer = load(REHEARSAL / "transfer-cleanup.json")
    raw_channel = (PROTOCOL / "channel-stdout.bin").read_bytes()
    raw_response = (PROTOCOL / "framed-response.bin").read_bytes()

    request = SimpleNamespace(
        value=SizedValue(progress["request_payload_bytes"]),
        declaration=declaration,
        declaration_sha256=ready["request_declaration_sha256"],
        chunk_count=declaration["request_chunk_count"],
    )
    observer = transport.OnlineChannelValidator(
        request,
        transaction_nonce=ready["transaction_nonce"],
        bootstrap_sha256=ready["bootstrap_sha256"],
    )
    observer.feed(raw_channel)
    channel = observer.finalize()

    stream = io.BytesIO(raw_channel[len(transport.CHANNEL_MAGIC):])
    frames = []
    while True:
        frame = transport.read_frame(
            stream, payload_cap=max(transport.CHUNK_BYTES,
                                    transport.MAX_CONTROL_PAYLOAD_BYTES))
        if frame is None:
            break
        frames.append(frame)
    kinds = [header["kind"] for header, _ in frames]
    sequences = [header.get("sequence") for header, _ in frames]
    ack_headers = [header for header, _ in frames
                   if header["kind"] == "request-ack"]
    response_payloads = [payload for header, payload in frames
                         if header["kind"] == "response-chunk"]
    if channel["response"] != raw_response:
        raise RuntimeError("online channel response differs from persisted response")
    if sequences != list(range(len(frames))):
        raise RuntimeError("request-channel sequence is not contiguous")
    if kinds[0] != "ready" or kinds[-1] != "response-complete":
        raise RuntimeError("request-channel boundary frames are wrong")
    if len(response_payloads) != 1 or response_payloads[0] != raw_response:
        raise RuntimeError("request-channel response chunk reconstruction failed")
    if transfer["request_payload_bytes"] != progress["request_payload_bytes"] or \
            transfer["request_payload_sha256"] != progress["request_payload_sha256"]:
        raise RuntimeError("transfer/request progress disagreement")
    return {
        "channel_stdout_bytes": len(raw_channel),
        "channel_stdout_sha256": digest_bytes(raw_channel),
        "response_bytes": len(raw_response),
        "response_sha256": digest_bytes(raw_response),
        "frame_count": len(frames),
        "frame_kind_counts": dict(collections.Counter(kinds)),
        "sequence_contiguous": True,
        "request_ack_count": len(ack_headers),
        "request_ack_index_min": min(header["ack_index"] for header in ack_headers),
        "request_ack_index_max": max(header["ack_index"] for header in ack_headers),
        "response_chunk_count": len(response_payloads),
        "response_chunk_bytes": [len(payload) for payload in response_payloads],
        "ready_remote_process_pid": channel["ready"]["remote_process_pid"],
        "request_declaration_accepted": channel["request_declaration_accepted"],
        "request_chunks_acked": channel["request_chunks_acked"],
        "request_bytes_acked": channel["request_bytes_acked"],
        "request_payload_bytes": progress["request_payload_bytes"],
        "request_payload_sha256": progress["request_payload_sha256"],
        "request_declaration_sha256": ready["request_declaration_sha256"],
        "request_chunk_bytes": declaration["request_chunk_bytes"],
        "request_chunk_count": declaration["request_chunk_count"],
        "response_matches_persisted": True,
        "transfer_request_wire_bytes": transfer["request_channel_wire_bytes"],
        "transfer_request_wire_sha256": transfer["request_channel_wire_sha256"],
    }


def verify_archive_and_admission(source_hashes: dict[str, str],
                                 source_tree: str) -> dict:
    compact = load(PROTOCOL / "source-admission.json")
    details = load(REHEARSAL / "source-admission-details.json")
    executor.validate_source_admission_details(details, source_hashes, compact)
    if compact["source_commit"] != PHASE1A or compact["source_tree"] != source_tree:
        raise RuntimeError("compact source admission identity is stale")

    with tempfile.TemporaryDirectory(prefix="alignment-v3-phase2-audit-") as raw:
        temporary = Path(raw)
        parsed = transport.parse_response_file(
            PROTOCOL / "framed-response.bin",
            temporary / "evidence.tar.gz",
            require_success=True,
        )
        inspected = archive_protocol.inspect_archive(parsed["archive_path"])
        extracted = temporary / "extracted-evidence"
        extracted_inventory = archive_protocol.extract_archive(
            parsed["archive_path"], extracted)
        executor.validate_archived_source_admission(
            extracted, source_hashes, compact)
        index = load(extracted / "artifact-hashes.json")
        details_in_archive = load(extracted / "source-admission-details.json")
        if details_in_archive != details:
            raise RuntimeError("archived full source-admission detail differs")
    return {
        "response_frame_count": parsed["frame_count"],
        "response_bulk_chunk_count": parsed["chunk_count"],
        "archive_bytes": parsed["archive_bytes"],
        "archive_sha256": parsed["archive_sha256"],
        "archive_inspect_status": inspected["status"],
        "archive_member_count": inspected["member_count"],
        "archive_extract_status": extracted_inventory["status"],
        "archived_artifact_index_rows": len(index["artifacts"]),
        "source_map_entry_count": compact["source_map_entry_count"],
        "source_map_sha256": compact["source_map_sha256"],
        "compact_full_source_admission_equal": True,
        "source_commit": compact["source_commit"],
        "source_tree": compact["source_tree"],
        "source_bundle_sha256": compact["source_bundle_sha256"],
    }


def main() -> int:
    current = git("rev-parse", "HEAD")
    main_ref = git("rev-parse", "main")
    phase1a_parent = git("rev-list", "--parents", "-n", "1", PHASE1A).split()[1:]
    phase1b_parent = git("rev-list", "--parents", "-n", "1", PHASE1B).split()[1:]
    current_parent = git("rev-list", "--parents", "-n", "1", current).split()[1:]
    ancestry = {
        "main_ref": main_ref,
        "main_matches_exact_base": main_ref == BASE,
        "phase1a_parent": phase1a_parent,
        "phase1a_parent_is_exact_base": phase1a_parent == [BASE],
        "phase1b_parent": phase1b_parent,
        "phase1b_parent_is_exact_phase1a": phase1b_parent == [PHASE1A],
        "base_is_ancestor_of_phase1b":
            subprocess.run(["git", "merge-base", "--is-ancestor", BASE, PHASE1B],
                           cwd=ROOT).returncode == 0,
        "current_head_is_phase1b_or_phase2_child":
            current == PHASE1B or current_parent == [PHASE1B],
    }
    if not all(value for key, value in ancestry.items()
               if key.startswith(("main_matches", "phase1a_parent_is",
                                  "phase1b_parent_is", "base_is", "current_head"))):
        raise RuntimeError("Phase 1 ancestry is not exact")

    diff_lines = git("diff", "--name-status", PHASE1A, PHASE1B).splitlines()
    diff_entries = [line.split("\t", 1) for line in diff_lines if "\t" in line]
    allowed_prefix = "evidence/backref-cost-specialization-alignment-v3-design/rehearsal/"
    allowed = {
        "evidence/backref-cost-specialization-alignment-v3-design/phase1b-authorization.json",
        "evidence/backref-cost-specialization-alignment-v3-design/phase1b-rehearsal-hashes.json",
    }
    additions_only = all(status == "A" and
                         (path.startswith(allowed_prefix) or path in allowed)
                         for status, path in diff_entries)
    if not additions_only or len(diff_entries) != 30:
        raise RuntimeError("Phase 1B is not the exact additions-only handoff")

    auth = load(AUTH)
    hash_index = verify_hash_index()
    frozen_paths = {
        "manifest": "scripts/backref_cost_specialization_alignment_v3_manifest.json",
        "protocol": "doc/backref-cost-specialization-alignment-v3-protocol-20260820.md",
        "schemas": "scripts/backref_cost_specialization_alignment_v3_schemas.json",
        "transport": "scripts/backref_cost_specialization_alignment_v3_transport.py",
    }
    frozen_hashes = {
        name: {
            "working_tree_sha256": digest(ROOT / path),
            "phase1a_blob_sha256": git_blob_sha(PHASE1A, path),
            "authorization_sha256": auth[f"{name if name != 'schemas' else 'schema_catalog'}_sha256"
                                     if name != "transport" else "transport_source_sha256"],
        }
        for name, path in frozen_paths.items()
    }
    # The authorization calls the schema hash schema_catalog_sha256.
    frozen_hashes["schemas"]["authorization_sha256"] = auth["schema_catalog_sha256"]
    if any(row["working_tree_sha256"] != row["phase1a_blob_sha256"] or
           row["working_tree_sha256"] != row["authorization_sha256"]
           for row in frozen_hashes.values()):
        raise RuntimeError("frozen source hash mismatch")
    if auth.get("rehearsal_hash_index_sha256") != hash_index["index_sha256"]:
        raise RuntimeError("authorization/hash-index digest mismatch")

    source_commit = PHASE1A
    source_tree = git("rev-parse", f"{PHASE1A}^{{tree}}")
    manifest = load(MANIFEST)
    identity_paths = list(admission.IDENTITY_PATHS)
    identity_paths.extend(manifest["admission_identity_paths"])
    source_hashes = {
        relative: git_blob_sha(PHASE1A, relative)
        for relative in dict.fromkeys(identity_paths)
    }
    archive = verify_archive_and_admission(source_hashes, source_tree)
    channel = replay_channel()
    build = load(REHEARSAL / "build-identity.json")
    codegen = load(REHEARSAL / "codegen.json")
    addresses = {name: int(value, 16)
                 for name, value in codegen["symbol_addresses"].items()}
    alignment = {
        "all_six_private_addresses_distinct": len(set(addresses.values())) == 6,
        "all_entry_mod_16384_zero": all(value % 16384 == 0
                                          for value in addresses.values()),
        "entry_spacing_16384": sorted(addresses.values()) == [
            min(addresses.values()) + 16384 * i for i in range(6)],
        "dp_to_push_displacement_49152": codegen["dp_to_push_displacement_bytes"] == 49152,
        "section_executable_pure_instructions":
            codegen["section"]["executable_pure_instructions"] is True and
            codegen["section"]["flags"] == "0x80000400",
        "section_size_bytes": codegen["section"]["size_bytes"],
        "body_bytes": build["alignment_body_bytes"],
        "padding_bytes": build["alignment_padding_bytes"],
        "baseline_layout_canonical_instructions_equal":
            codegen["baseline_layout_canonical_instructions_equal"],
        "hint_body_distinct": codegen["hint_body_distinct"],
        "timed_recorder_free": build["timed_recorder_free"],
        "timed_runner_sha256": build["timed_runner_sha256"],
        "timed_runner_bytes": build["timed_runner_bytes"],
    }
    if not all(value is True for key, value in alignment.items()
               if isinstance(value, bool)):
        raise RuntimeError("frozen alignment facts failed")

    payload_agreement = load(EVIDENCE / "representative-payload-agreement.json")
    payload = {
        "bytes": payload_agreement["payload_bytes"],
        "sha256": payload_agreement["independent_fixture_sha256_value"],
        "generator_fixture_manifest_agree":
            payload_agreement["independent_fixture_sha256_value"] ==
            payload_agreement["generator_recomputation_sha256"] ==
            payload_agreement["manifest_sha256_value"],
        "stale_identity_negatives": all(
            payload_agreement[key] == "PASS_REJECTED"
            for key in ("negative_stale_alignment_v1_test",
                        "negative_stale_v2_test", "negative_stale_v3_test",
                        "negative_stale_v4_test")),
    }
    toolchain = load(EVIDENCE / "toolchain-identity-agreement.json")
    toolchain_facts = {
        "manifest_actual_fixture_agree": toolchain["manifest_actual_fixture_agree"],
        "required_executable_count": len(toolchain["required_executables"]),
        "required_metadata_count": len(toolchain["required_metadata"]),
        "xcrun_required": toolchain["xcrun_required"],
        "stale_identity_negatives": all(
            toolchain[key].startswith("PASS_REJECTED")
            for key in ("negative_stale_alignment_v1_identity_test",
                        "negative_stale_alignment_v2_identity_test",
                        "negative_stale_v2_xcrun_test",
                        "negative_stale_v3_identity_test",
                        "negative_stale_v4_identity_test")),
    }
    if not payload["generator_fixture_manifest_agree"] or \
            not payload["stale_identity_negatives"] or \
            not toolchain_facts["manifest_actual_fixture_agree"] or \
            not toolchain_facts["stale_identity_negatives"] or \
            toolchain_facts["xcrun_required"]:
        raise RuntimeError("payload/toolchain identity gate failed")

    rehearsal = load(REHEARSAL / "rehearsal.json")
    transfer = load(REHEARSAL / "transfer-cleanup.json")
    lease = load(PROTOCOL / "lease-state.json")
    resources = load(REHEARSAL / "resource-admission-admission.json")
    remote_process = load(REHEARSAL / "remote-admission-process-isolation.json")
    safety = {
        "phase1_rehearsal_remote_contacts": auth["remote_contacts_established"],
        "phase1_rehearsal_attempts": auth["rehearsal_attempts"],
        "phase1_rehearsal_retry_count": auth["retry_count"],
        "phase1_rehearsal_rerun_count": auth["rerun_count"],
        "prior_cycle_paths_contacted": auth["prior_cycle_paths_contacted"],
        "post_run_remote_cleanup_operations":
            transfer["post_run_remote_cleanup_operations"],
        "discovered_pid_signals": resources["process_isolation"]["discovered_pid_signals"],
        "remote_discovered_pid_signals":
            remote_process["process_isolation"]["discovered_pid_signals"],
        "local_exact_identity_conflicts": resources["process_isolation"][
            "exact_identity_conflicts"],
        "remote_exact_identity_conflicts": remote_process["process_isolation"][
            "exact_identity_conflicts"],
        "settings_changed": resources["settings_changed"],
        "lease_state": lease["state"],
        "timed_binary_invoked": transfer["timed_binary_invoked"],
    }

    # This is deliberately stricter than the broad Phase 1B diagnostic envelope:
    # the untimed rehearsal explicitly records these timing prerequisites as absent.
    timed_prerequisites = {
        "correctness_before_first_profile": False,
        "coarse_timer_record_accounting": False,
        "all_timed_children_serial_and_directly_owned": False,
    }
    authority = {
        "phase1b_envelope_authorization_status": auth["authorization_status"],
        "phase1b_envelope_phase2_authority": auth["phase_2_authority"],
        "phase1b_envelope_timed_execution_authorized": auth[
            "timed_execution_authorized"],
        "independent_timed_prerequisites": timed_prerequisites,
        "authority": "NONE",
        "timed_execution_authorized": False,
        "refusal_reasons": [
            "rehearsal did not run the mandatory 24 correctness encodes before timing",
            "rehearsal records timer_accounting_validation=not-run-in-rehearsal",
            "rehearsal had no timed children, so serial/direct ownership was not proven",
        ],
    }

    result = {
        "schema": "libwebp-backref-cost-specialization-alignment-v3-phase2-audit-v1",
        "phase": "2",
        "status": "REFUSED",
        "result": "FAIL_CLOSED_REFUSAL_NO_HOST_CONTACT",
        "base_commit": BASE,
        "phase1a_commit": PHASE1A,
        "phase1b_commit": PHASE1B,
        "audited_head": PHASE1B,
        "audit_head": current,
        "ancestry": ancestry,
        "phase1b_additions_only": {
            "diff_entry_count": len(diff_entries),
            "all_entries_added_and_allowlisted": additions_only,
            "frozen_phase1a_artifacts_modified": False,
        },
        "frozen_hashes": frozen_hashes,
        "hash_index": hash_index,
        "raw_channel_replay": channel,
        "archive_and_source_admission": archive,
        "alignment": alignment,
        "payload": payload,
        "toolchain": toolchain_facts,
        "safety": safety,
        "authority": authority,
        "host_contact": {
            "remote_host": "pandocs-agent",
            "phase2_contact_attempted": False,
            "phase2_ssh_process_created": False,
            "phase2_lease_attempted": False,
            "phase2_timed_command_invoked": False,
            "phase2_retry_count": 0,
            "phase2_rerun_count": 0,
            "reason": "independent authority is NONE; no host contact is permitted",
        },
        "raw_counts": {
            "timed_phase2_processes": 0,
            "timed_phase2_samples": 0,
            "timed_phase2_correctness_encodes": 0,
            "timed_phase2_work_rows": 0,
            "timed_phase2_stage_rows": 0,
            "phase1_rehearsal_encoder_workloads": rehearsal["encoder_workloads"],
            "phase1_rehearsal_performance_samples": rehearsal["performance_samples"],
            "phase1_rehearsal_profile_commands_constructed":
                rehearsal["profile_commands_constructed"],
            "phase1_rehearsal_request_bytes": transfer["request_payload_bytes"],
            "phase1_rehearsal_request_chunks_written": transfer[
                "request_chunks_written"],
            "phase1_rehearsal_request_chunks_acknowledged": transfer[
                "request_chunks_acknowledged"],
            "phase1_rehearsal_channel_stdout_bytes": transfer["channel_stdout_bytes"],
            "phase1_rehearsal_response_bytes": transfer["framed_response_bytes"],
            "phase1_rehearsal_archive_bytes": archive["archive_bytes"],
            "phase1_rehearsal_source_paths": archive["source_map_entry_count"],
            "phase1_rehearsal_evidence_files": hash_index["file_count"],
            "phase1_rehearsal_evidence_bytes": hash_index["total_bytes"],
        },
        "evidence_paths": {
            "phase1b_authorization": str(AUTH.relative_to(ROOT)),
            "phase1b_hash_index": str(HASH_INDEX.relative_to(ROOT)),
            "rehearsal_root": str(REHEARSAL.relative_to(ROOT)),
            "ready": str((PROTOCOL / "ready.json").relative_to(ROOT)),
            "request_declaration": str((PROTOCOL / "request-declaration.json").relative_to(ROOT)),
            "request_progress": str((PROTOCOL / "request-progress.json").relative_to(ROOT)),
            "source_admission": str((PROTOCOL / "source-admission.json").relative_to(ROOT)),
            "source_admission_details": str((REHEARSAL / "source-admission-details.json").relative_to(ROOT)),
            "framed_response": str((PROTOCOL / "framed-response.bin").relative_to(ROOT)),
            "channel_stdout": str((PROTOCOL / "channel-stdout.bin").relative_to(ROOT)),
            "cleanup_footer": str((PROTOCOL / "cleanup-footer.json").relative_to(ROOT)),
            "build_identity": str((REHEARSAL / "build-identity.json").relative_to(ROOT)),
            "codegen": str((REHEARSAL / "codegen.json").relative_to(ROOT)),
            "request_size_freeze": str((EVIDENCE / "request-channel-size-freeze.json").relative_to(ROOT)),
            "source_control_freeze": str((EVIDENCE / "source-admission-control-freeze.json").relative_to(ROOT)),
            "payload_agreement": str((EVIDENCE / "representative-payload-agreement.json").relative_to(ROOT)),
            "toolchain_agreement": str((EVIDENCE / "toolchain-identity-agreement.json").relative_to(ROOT)),
        },
        "next_credible_lead": "A new independently frozen Phase 2 handoff must first prove correctness-before-timing, timer accounting, and serial directly-owned timed children; only then may the exact one-session timed command be reconsidered.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
