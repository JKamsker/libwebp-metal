#!/usr/bin/env python3
"""Record the sole stage-attribution-v3 rehearsal as Phase 1B evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v3_identity as identity


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v3-design"
REHEARSAL = DESIGN / "rehearsal"
INDEX = DESIGN / "phase1b-rehearsal-hashes.json"
AUTHORIZATION = DESIGN / "phase1b-authorization.json"
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_manifest.json"
PROTOCOL = ROOT / "doc/backref-cost-aligned-null-stage-attribution-v3-protocol-20260820.md"
SCHEMAS = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_schemas.json"
TRANSPORT = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v3_transport.py"
EXPECTED_RECEIPT = DESIGN / "four-body-expected-receipt.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["/usr/bin/git", *args], cwd=ROOT, text=True).strip()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def artifact_rows() -> list[dict]:
    if not REHEARSAL.is_dir():
        raise RuntimeError("the sole rehearsal directory is absent")
    paths = sorted(path for path in REHEARSAL.rglob("*") if path.is_file())
    if not paths:
        raise RuntimeError("the sole rehearsal produced no persistent receipt")
    return [{"path": path.relative_to(REHEARSAL).as_posix(),
             "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in paths]


def success_gate(source_commit: str, source_tree: str,
                 rows: list[dict]) -> tuple[bool, list[str], dict]:
    required = {
        "artifact-hashes.json", "build-identity.json", "codegen.json",
        "diagnostic-admission.json", "operator-status.json",
        "profile-plan.json", "rehearsal.json",
        "remote-admission-process-isolation.json",
        "resource-admission-admission.json",
        "source-admission-details.json",
        "return-protocol/archive-build.json",
        "return-protocol/bulk-declaration.json",
        "return-protocol/channel-stdout.bin",
        "return-protocol/cleanup-footer.json",
        "return-protocol/framed-response.bin",
        "return-protocol/integrity-footer.json",
        "return-protocol/lease-state.json",
        "return-protocol/operator-status.json",
        "return-protocol/ready.json",
        "return-protocol/request-declaration.json",
        "return-protocol/request-progress.json",
        "return-protocol/request-progress-chain.json",
        "return-protocol/response-channel-complete.json",
        "return-protocol/response-channel-declaration.json",
        "return-protocol/source-admission.json",
        "return-protocol/transport-stderr.bin",
        "returned-evidence-hashes.json",
        "transfer-cleanup.json",
    }
    names = {row["path"] for row in rows}
    reasons = [f"missing rehearsal receipt: {name}"
               for name in sorted(required - names)]
    if reasons:
        return False, reasons, {}
    rehearsal = load(REHEARSAL / "rehearsal.json")
    transfer = load(REHEARSAL / "transfer-cleanup.json")
    cleanup = load(REHEARSAL / "return-protocol/cleanup-footer.json")
    integrity = load(REHEARSAL / "return-protocol/integrity-footer.json")
    source = load(REHEARSAL / "return-protocol/source-admission.json")
    ready = load(REHEARSAL / "return-protocol/ready.json")
    request_progress = load(
        REHEARSAL / "return-protocol/request-progress.json")
    request_chain = load(
        REHEARSAL / "return-protocol/request-progress-chain.json")
    response_declaration = load(
        REHEARSAL / "return-protocol/response-channel-declaration.json")
    response_complete = load(
        REHEARSAL / "return-protocol/response-channel-complete.json")
    source_details = load(REHEARSAL / "source-admission-details.json")
    remote_process = load(
        REHEARSAL / "remote-admission-process-isolation.json")
    operator = load(REHEARSAL / "return-protocol/operator-status.json")
    archive = load(REHEARSAL / "return-protocol/archive-build.json")
    lease = load(REHEARSAL / "return-protocol/lease-state.json")
    resources = load(REHEARSAL / "resource-admission-admission.json")
    build = load(REHEARSAL / "build-identity.json")
    codegen = load(REHEARSAL / "codegen.json")
    manifest = load(MANIFEST)
    expected = load(EXPECTED_RECEIPT)
    identity.validate_machine_receipt(
        expected, manifest.get("four_body_receipt_bindings"))
    addresses_map = codegen.get("symbol_addresses", {})
    addresses = [int(addresses_map.get(name, "-1"), 16)
                 for name in identity.names()]
    receipt_match = (
        expected.get("schema") == identity.EXPECTED_RECEIPT_SCHEMA and
        expected.get("generator") == identity.generator_binding() ==
            manifest.get("four_body_identity") == codegen.get("four_body_identity") and
        expected.get("bindings") == manifest.get("four_body_receipt_bindings") and
        addresses_map == expected.get("symbol_addresses") and
        codegen.get("facts") == expected.get("facts") and
        codegen.get("section") == expected.get("section") and
        codegen.get("inter_entry_padding_bytes") == expected.get("padding_bytes") and
        codegen.get("linker_map_sha256") == expected.get("linker_map_sha256") and
        codegen.get("linker_map_extract_sha256") ==
            expected.get("linker_map_extract_sha256") and
        codegen.get("linker_map_bytes") == expected.get("linker_map_bytes") and
        build.get("timed_runner_sha256") == expected.get("binary_sha256") and
        build.get("timed_runner_bytes") == expected.get("binary_bytes") and
        build.get("alignment_section_size_bytes") ==
            expected.get("section", {}).get("size_bytes") and
        build.get("alignment_body_bytes") == expected.get("body_bytes") and
        build.get("alignment_padding_bytes") == expected.get("padding_bytes")
    )
    identities = (rehearsal, transfer, cleanup, source, operator)
    source_rows = source_details.get("source_map")
    source_rows_digest = hashlib.sha256(json.dumps(
        source_rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest() \
        if isinstance(source_rows, list) else None
    checks = {
        "all source receipts identify Phase 1A": all(
            item.get("source_commit") == source_commit and
            item.get("source_tree") == source_tree for item in identities),
        "zero workloads and samples": rehearsal.get("encoder_workloads") == 0 and
            rehearsal.get("performance_samples") == 0 and
            rehearsal.get("profiler_workloads") == 0 and
            rehearsal.get("correctness_encodes") == 0 and
            rehearsal.get("runner_children") == 0 and
            rehearsal.get("direct_child_receipts") == 0 and
            rehearsal.get("timer_validation") ==
                "not-run-in-zero-workload-rehearsal" and
            transfer.get("encoder_workloads") == 0 and
            transfer.get("profile_encoder_workloads") == 0 and
            transfer.get("untimed_correctness_workloads") == 0 and
            transfer.get("untimed_counter_workloads") == 0 and
            transfer.get("timed_binary_invoked") is False,
        "lease was not attempted":
            transfer.get("benchmark_lease_acquisition_attempted") is False and
            lease.get("state") == "not-attempted" and
            lease.get("acquisition_attempted") is False,
        "source admission verified":
            source.get("status") == "verified" and
            source_details.get("status") == "verified" and
            isinstance(source_rows, list) and
            len(source_rows) == len(manifest["admission_identity_paths"]) and
            source.get("source_map_entry_count") == len(source_rows) ==
                source_details.get("source_map_entry_count") and
            source.get("source_map_sha256") == source_rows_digest ==
                source_details.get("source_map_sha256") and
            all(isinstance(row, dict) and set(row) == {"path", "sha256"}
                for row in source_rows) and
            [row["path"] for row in source_rows] == sorted(
                row["path"] for row in source_rows) and
            len({row["path"] for row in source_rows}) == len(source_rows) and
            source_details.get("source_commit") == source_commit and
            source_details.get("source_tree") == source_tree and
            source_details.get("source_bundle_sha256") ==
                source.get("source_bundle_sha256"),
        "operator completed": operator.get("status") == "complete" and
            operator.get("operator_exit_code") == 0,
        "archive accepted": archive.get("status") == "accepted",
        "integrity completed": integrity.get("status") == "complete",
        "cleanup and absence proved": cleanup.get("status") == "complete" and
            cleanup.get("absence_proved") is True and
            cleanup.get("removed_exact_validated_child") is True and
            transfer.get("cleanup_footer_verified") is True and
            transfer.get("remote_cleanup_absence_proved") is True,
        "observe-only process isolation":
            resources.get("process_isolation", {}).get("discovered_pid_signals") == 0 and
            not resources.get("process_isolation", {}).get("exact_identity_conflicts") and
            remote_process.get("status") == "verified" and
            remote_process.get("process_isolation", {}).get(
                "discovered_pid_signals") == 0 and
            not remote_process.get("process_isolation", {}).get(
                "exact_identity_conflicts"),
        "transport complete and capped": transfer.get("status") == "complete" and
            transfer.get("transport_exit_code") == 0 and
            transfer.get("framed_response_cap_verified") is True and
            transfer.get("transport_online_persistence_hash_count_verified") is True,
        "READY authenticated remote channel":
            transfer.get("ssh_process_created") is True and
            transfer.get("channel_ready_reached") is True and
            transfer.get("remote_connection_established") is True and
            ready.get("request_payload_read_before_ready") is False and
            ready.get("remote_files_created_before_ready") == 0 and
            transfer.get("ready_remote_identity_receipt") == ready,
        "request declaration chunks and ACKs complete":
            transfer.get("request_declaration_accepted") is True and
            transfer.get("request_complete_ack_verified") is True and
            request_progress.get("status") == "complete" and
            request_progress.get("declaration_accepted") is True and
            request_progress.get("request_chunks_written") ==
                request_progress.get("request_chunks_acknowledged") and
            request_progress.get("request_bytes_acknowledged") ==
                request_progress.get("request_payload_bytes") and
            transfer.get("request_chunks_written") ==
                transfer.get("request_chunks_acknowledged") and
            transfer.get("request_bytes_acknowledged") ==
                transfer.get("request_payload_bytes"),
        "request progress chain complete":
            request_chain.get("status") == "complete" and
            request_chain.get("row_cap") == 512 and
            request_chain.get("rows_recorded") ==
                request_progress.get("request_chunks_acknowledged") and
            request_chain.get("chunks_planned") ==
                request_progress.get("request_chunks_acknowledged") and
            request_chain.get("last_fully_acknowledged_chunk") ==
                request_chain.get("chunks_planned") and
            len(request_chain.get("rows", [])) ==
                request_chain.get("rows_recorded") and
            all(row.get("chunk_ordinal") == index + 1 and
                row.get("cumulative_bytes") == row.get("byte_end_exclusive") and
                row.get("write_start_monotonic_ns") <=
                    row.get("write_complete_monotonic_ns") <=
                    row.get("ack_received_monotonic_ns") and
                row.get("ack_latency_ns") ==
                    row.get("ack_received_monotonic_ns") -
                    row.get("write_complete_monotonic_ns")
                for index, row in enumerate(request_chain.get("rows", []))),
        "response channel complete":
            response_declaration.get("status") == "started" and
            response_complete.get("status") == "complete" and
            response_declaration.get("response_bytes") ==
                response_complete.get("response_bytes") ==
                transfer.get("framed_response_bytes") and
            response_declaration.get("response_sha256") ==
                response_complete.get("response_sha256") ==
                transfer.get("framed_response_sha256"),
        "alignment build frozen":
            build.get("timed_recorder_free") is True and
            build.get("all_four_private_addresses_distinct") is True and
            len(addresses) == identity.count() and
            len(set(addresses)) == identity.count() and
            all(value % identity.BOUNDARY_BYTES == 0
                                        for value in addresses) and
            codegen.get("baseline_layout_canonical_instructions_equal") is True and
            codegen.get("section", {}).get("flags") == identity.SECTION_FLAGS and
            codegen.get("section", {}).get(
                "executable_pure_instructions") is True and
            receipt_match,
    }
    reasons.extend(name for name, passed in checks.items() if not passed)
    return not reasons, reasons, {
        "transfer": transfer, "build": build, "codegen": codegen,
        "frozen_four_body_receipt": expected,
        "four_body_receipt_exact_match": receipt_match,
        "resources": resources, "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-exit-code", type=int, required=True)
    args = parser.parse_args()
    if INDEX.exists() or AUTHORIZATION.exists():
        raise RuntimeError("Phase 1B index/envelope already exists")
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    rows = artifact_rows()
    index = {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v3-phase1b-hash-index-v1",
        "source_commit": source_commit, "source_tree": source_tree,
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "artifacts": rows,
    }
    write(INDEX, index)
    passed, reasons, facts = success_gate(source_commit, source_tree, rows)
    passed = passed and args.attempt_exit_code == 0
    if args.attempt_exit_code != 0:
        reasons.append(f"sole rehearsal command exited {args.attempt_exit_code}")
    transfer = facts.get("transfer", {})
    calibration = transfer.get("transport_calibration")
    hashes = {row["path"]: row["sha256"] for row in rows}
    observed_transfer = load(REHEARSAL / "transfer-cleanup.json") \
        if (REHEARSAL / "transfer-cleanup.json").is_file() else {}
    connection_established = (
        observed_transfer.get("channel_ready_reached") is True and
        observed_transfer.get("remote_connection_established") is True)
    authorization = {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v3-authorization-v1",
        "authorization_status": "AUTHORIZED" if passed else "REFUSED",
        "status": "AUTHORIZED" if passed else "REFUSED",
        "phase_2_authority": (
            "ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CONDITIONAL_DIAGNOSTIC_AUTHORITY"
            if passed else "NONE"),
        "pipeline_invocation_authorized": passed,
        "performance_sampling_authorized_before_dynamic_admission": False,
        "timed_execution_authorized": False,
        "authorization_scope": (
            "Phase 2 may make exactly one frozen stage-attribution-v3 diagnostic transaction. No performance sample is admitted until dynamic correctness, timer-accounting, and online direct-child gates pass inside that invocation; no production promotion, retry, or other workload is authorized."
            if passed else "Phase 2 is unauthorized."),
        "base_commit": "92c3b59b2d178c5a03ec20b897252b358f07de81",
        "branch": "codex/backref-cost-aligned-null-stage-attribution-v3",
        "source_commit": source_commit, "source_tree": source_tree,
        "phase_1b_parent_rule":
            "the commit containing this envelope has exactly one parent equal to source_commit",
        "phase_1b_identity_rule":
            "HEAD is additions-only Phase 1B; no Phase 1A artifact is modified",
        "manifest_sha256": sha256(MANIFEST),
        "protocol_sha256": sha256(PROTOCOL),
        "schema_catalog_sha256": sha256(SCHEMAS),
        "transport_source_sha256": sha256(TRANSPORT),
        "rehearsal_hash_index_sha256": sha256(INDEX),
        "rehearsal_receipt_hashes": hashes,
        "raw_rehearsal_artifact_counts": {
            "file_count": len(rows), "total_bytes": index["total_bytes"],
            "channel_stdout_bytes": next((row["bytes"] for row in rows if
                row["path"] == "return-protocol/channel-stdout.bin"), 0),
            "framed_response_bytes": next((row["bytes"] for row in rows if
                row["path"] == "return-protocol/framed-response.bin"), 0),
            "transport_stderr_bytes": next((row["bytes"] for row in rows if
                row["path"] == "return-protocol/transport-stderr.bin"), 0),
        },
        "observed_transport_calibration": calibration,
        "rehearsal_attempts": 1, "connection_attempts": 1,
        "retry_count": 0, "rerun_count": 0,
        "remote_connection_established": connection_established,
        "remote_contacts_established": 1 if connection_established else 0,
        "prior_cycle_paths_contacted": False,
        "benchmark_lease_acquisition_attempted": False,
        "post_run_remote_cleanup_operations": 0,
        "timed_binary_invoked": False, "encoder_workloads": 0,
        "profiler_workloads": 0, "timed_workloads": 0,
        "performance_samples": 0,
        "correctness_encodes": 0,
        "timer_validation_children": 0,
        "direct_runner_children": 0,
        "dynamic_gates_deferred_to_single_phase2_pipeline": True,
        "zero_workload_rehearsal_does_not_historically_prove_future_children": True,
        "source_admission_verified": passed,
        "process_isolation_verified": passed,
        "channel_ready_verified": passed,
        "request_stream_acknowledged": passed,
        "response_channel_verified": passed,
        "archive_integrity_verified": passed,
        "archive_cap_verified": passed,
        "framed_response_cap_verified": passed,
        "integrity_footer_verified": passed,
        "cleanup_footer_verified": passed,
        "remote_cleanup_absence_proved": passed,
        "gate_outcomes": facts.get("checks", {}),
        "refusal_reasons": reasons,
        "production_promotion_authorized": False,
    }
    if passed:
        authorization["remote_build_identity"] = facts["build"]
        authorization["remote_codegen"] = facts["codegen"]
        authorization["remote_resources"] = facts["resources"]
    write(AUTHORIZATION, authorization)
    print(json.dumps({"status": authorization["authorization_status"],
                      "source_commit": source_commit,
                      "rehearsal_files": len(rows),
                      "phase_2_authority": authorization["phase_2_authority"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
