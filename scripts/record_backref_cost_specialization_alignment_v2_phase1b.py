#!/usr/bin/env python3
"""Record the sole alignment-v2 rehearsal as additions-only Phase 1B evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "evidence/backref-cost-specialization-alignment-v2-design"
REHEARSAL = DESIGN / "rehearsal"
INDEX = DESIGN / "phase1b-rehearsal-hashes.json"
AUTHORIZATION = DESIGN / "phase1b-authorization.json"
MANIFEST = ROOT / "scripts/backref_cost_specialization_alignment_v2_manifest.json"
PROTOCOL = ROOT / "doc/backref-cost-specialization-alignment-v2-protocol-20260820.md"
SCHEMAS = ROOT / "scripts/backref_cost_specialization_alignment_v2_schemas.json"
TRANSPORT = ROOT / "scripts/backref_cost_specialization_alignment_v2_transport.py"


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
        "return-protocol/cleanup-footer.json",
        "return-protocol/framed-stdout.bin",
        "return-protocol/integrity-footer.json",
        "return-protocol/lease-state.json",
        "return-protocol/operator-status.json",
        "return-protocol/source-admission.json",
        "return-protocol/transport-stderr.bin",
        "returned-evidence-hashes.json", "timer-validation.json",
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
    source_details = load(REHEARSAL / "source-admission-details.json")
    remote_process = load(
        REHEARSAL / "remote-admission-process-isolation.json")
    operator = load(REHEARSAL / "return-protocol/operator-status.json")
    archive = load(REHEARSAL / "return-protocol/archive-build.json")
    lease = load(REHEARSAL / "return-protocol/lease-state.json")
    resources = load(REHEARSAL / "resource-admission-admission.json")
    build = load(REHEARSAL / "build-identity.json")
    codegen = load(REHEARSAL / "codegen.json")
    addresses = [int(value, 16)
                 for value in codegen.get("symbol_addresses", {}).values()]
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
            isinstance(source_rows, list) and len(source_rows) > 0 and
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
        "alignment build frozen":
            build.get("timed_recorder_free") is True and
            build.get("all_six_private_addresses_distinct") is True and
            len(addresses) == 6 and all(value % 16384 == 0
                                        for value in addresses) and
            codegen.get("baseline_layout_canonical_instructions_equal") is True and
            codegen.get("section", {}).get("size_bytes") == 83212 and
            codegen.get("section", {}).get("flags") == "0x80000400" and
            codegen.get("section", {}).get(
                "executable_pure_instructions") is True and
            codegen.get("inter_entry_padding_bytes") == 77588 and
            build.get("alignment_section_size_bytes") == 83212 and
            build.get("alignment_body_bytes") == 5624 and
            build.get("alignment_padding_bytes") == 77588,
    }
    reasons.extend(name for name, passed in checks.items() if not passed)
    return not reasons, reasons, {
        "transfer": transfer, "build": build, "codegen": codegen,
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
        "schema": "libwebp-backref-cost-specialization-alignment-v2-phase1b-hash-index-v1",
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
    connection_established = (
        REHEARSAL / "return-protocol/source-admission.json").is_file()
    authorization = {
        "schema": "libwebp-backref-cost-specialization-alignment-v2-authorization-v1",
        "authorization_status": "AUTHORIZED" if passed else "REFUSED",
        "status": "AUTHORIZED" if passed else "REFUSED",
        "phase_2_authority": "ALIGNMENT_V2_DIAGNOSTIC_ONLY" if passed else "NONE",
        "timed_execution_authorized": passed,
        "authorization_scope": (
            "Phase 2 may make exactly one frozen alignment-v2 diagnostic transaction; no production promotion, Phase 3, retry, or other workload is authorized."
            if passed else "Phase 2 is unauthorized."),
        "base_commit": "b96909b28b3d64f000d0f98ffa76137305010808",
        "branch": "codex/backref-cost-specialization-alignment-v2",
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
            "framed_stdout_bytes": next((row["bytes"] for row in rows if
                row["path"] == "return-protocol/framed-stdout.bin"), 0),
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
        "source_admission_verified": passed,
        "process_isolation_verified": passed,
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
