#!/usr/bin/env python3
"""Untimed, workload-free protocol and freeze tests for specialization alignment v3."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import backref_cost_specialization_alignment_v3_admission as admission
import backref_cost_specialization_alignment_v3_transport as transport
import execute_backref_cost_specialization_alignment_v3 as executor
import run_backref_cost_specialization_alignment_v3_experiment as operator
import backref_cost_specialization_alignment_v3_toolchain as toolchain
import evaluate_backref_cost_specialization_alignment_v3 as evaluator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_specialization_alignment_v3_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected(function, *args, **kwargs) -> None:
    try:
        function(*args, **kwargs)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        return
    raise AssertionError(f"unsafe contract accepted: {function.__name__}")


def extract_body(text: str, name: str) -> str:
    start = text.index(name + "(")
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        depth += (text[index] == "{") - (text[index] == "}")
        if depth == 0:
            return text[brace:index + 1]
    raise AssertionError(f"unterminated function: {name}")


def semantic_identity() -> None:
    current = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    assert "VP8LBackrefCostSpecializationAlignmentV3GetVariant" in current
    boundary = current.split("const WEBP_FACTORIZATION_VARIANT_TYPE variant", 1)[1]
    boundary = boundary.split("#else", 1)[0]
    assert boundary.count("switch (variant)") == 1
    assert boundary.count("BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert boundary.count("BackwardReferencesHashChainDistanceOnlyLayoutClone(") == 1
    assert boundary.count("BackwardReferencesHashChainDistanceOnly(") == 1
    preprocessed = subprocess.check_output(
        [str(toolchain.EXECUTABLE_PATHS["clang"]), "-E", "-P", f"-I{ROOT}",
         "-DWEBP_USE_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT=1",
         "src/enc/backward_references_cost_enc.c"], cwd=ROOT, text=True)
    traceback = extract_body(preprocessed, "VP8LBackwardReferencesTraceBackwards")
    assert traceback.count(
        "VP8LBackrefCostSpecializationAlignmentV3GetVariant()") == 1
    assert traceback.count("BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert traceback.count("BackwardReferencesHashChainDistanceOnlyLayoutClone(") == 1
    assert traceback.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert traceback.count(
        "WebPProfileStageBegin(WEBP_PROFILE_BACKREF_COST_DP_TOTAL)") == 1


def v11_v13_boundary_audit() -> None:
    v11 = (ROOT / "evidence/backref-cost-attribution-v11-design/rehearsal/"
           "return-protocol/framed-stdout.bin")
    v13 = (ROOT / "evidence/backref-cost-attribution-v13-design/rehearsal/"
           "return-protocol/framed-stdout.bin")
    phase3 = json.loads((ROOT / "evidence/backref-cost-attribution-v13-phase3/"
                         "phase3-evaluation.json").read_text())
    new_admission = (ROOT / "scripts/backref_cost_specialization_alignment_v3_admission.py").read_text()
    assert v11.stat().st_size == 1941990
    assert sha256(v11) == \
        "f6cb02af4d445ac355bdf007f8cfc19daf19d98d3e45647e0689f89264f848f4"
    assert v13.stat().st_size == 1942116
    assert sha256(v13) == \
        "edaafe783c94d5cb9dcef376012bb64960730d1f6a92f493f3f60464be41109d"
    partial = phase3["raw_stream"]["partial_frame"]
    assert phase3["raw_stream"]["complete_bulk_chunks"] == 3
    assert partial["declared_payload_bytes"] == 524288
    assert partial["available_payload_bytes"] == 359772
    assert "class TransportDeadlineStateMachine" in new_admission
    assert "response_deadline" not in new_admission


def v15_exact_refusal_audit() -> None:
    stdout = (ROOT / "evidence/backref-cost-attribution-v15-design/rehearsal/"
              "return-protocol/framed-stdout.bin")
    stderr = (ROOT / "evidence/backref-cost-attribution-v15-design/rehearsal/"
              "return-protocol/transport-stderr.bin")
    authorization = json.loads((
        ROOT / "evidence/backref-cost-attribution-v15-design/"
        "phase1b-authorization.json").read_text())
    assert stdout.read_bytes() == b""
    assert sha256(stdout) == \
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert stderr.read_bytes() == (
        b"ssh: connect to host 100.85.234.14 port 22: Operation timed out\r\n")
    assert stderr.stat().st_size == 65
    assert sha256(stderr) == \
        "561ab6a0b87eb9dbd145fcb63a6dddd66c215f13680aa83763b3260d3e904eaa"
    assert authorization["timed_execution_authorized"] is False
    assert authorization["phase_2_authority"] == "NONE"
    assert authorization["rehearsal_attempts"] == 1
    assert authorization["retry_count"] == 0
    assert authorization["remote_connection_established"] is False
    assert authorization["prior_cycle_paths_contacted"] is False


def response_fixture(*, success: bool = True, cleanup: bool = True,
                     include_bulk: bool = True) -> bytes:
    archive = b"representative archive bytes" if include_bulk else b""
    operator_status = {
        "status": "complete" if success else "refused",
        "benchmark_lease_acquisition_attempted": False}
    frames = [
        ("source-admission", transport.canonical_json({
            "schema": transport.SOURCE_RECEIPT_SCHEMA,
            "receipt_version": transport.SOURCE_RECEIPT_VERSION,
            "status": "verified", "source_commit": "1" * 40,
            "source_tree": "2" * 40,
            "source_bundle_sha256": "3" * 64,
            "source_map_entry_count": 1,
            "source_map_sha256": "4" * 64,
            "bundle_verified_in_repository_context": True,
            "verification_repository_removed": True,
            "clean_status": True}), {"sequence": 0}),
        ("operator-status", transport.canonical_json(operator_status),
         {"sequence": 1}),
        ("archive-build", transport.canonical_json({
            "status": "accepted" if include_bulk else "not-attempted",
            "builder_exit_code": 0 if include_bulk else None}), {"sequence": 2}),
        ("lease-state", transport.canonical_json({
            "state": "not-attempted", "acquisition_attempted": False}),
         {"sequence": 3}),
    ]
    sequence = 4
    if include_bulk:
        declaration = {"schema": transport.BULK_DECLARATION_SCHEMA,
                       "status": "accepted",
                       "compression_format": "tar+gzip",
                       "archive_bytes": len(archive),
                       "archive_sha256": transport.sha256_bytes(archive),
                       "chunk_count": 1, "chunk_bytes": transport.CHUNK_BYTES,
                       "inventory": {
                           "schema": "libwebp-backref-cost-specialization-alignment-v3-archive-inventory-v1",
                           "status": "accepted", "member_count": 1,
                           "inventory_sha256": "0" * 64}}
        frames.append(("bulk-declaration", transport.canonical_json(declaration),
                       {"sequence": sequence}))
        sequence += 1
        frames.append(("bulk-chunk", archive,
                       {"sequence": sequence, "chunk_index": 0}))
        sequence += 1
    frames.append(("integrity-footer", transport.canonical_json({
        "status": "complete" if success and include_bulk else "refused",
        "archive_sha256": transport.sha256_bytes(archive)
        if include_bulk else None}), {"sequence": sequence}))
    sequence += 1
    if cleanup:
        frames.append(("cleanup-footer", transport.canonical_json({
            "status": "complete", "removed_exact_validated_child": True,
            "absence_proved": True}), {"sequence": sequence}))
    return transport.encode_stream(frames)


def framing_contracts() -> None:
    complete = response_fixture()
    parsed = transport.parse_response(complete, require_success=True)
    assert parsed["success"] and parsed["archive"] == b"representative archive bytes"
    rejected(transport.parse_response, complete[:-3], require_success=True)
    rejected(transport.parse_response, response_fixture(cleanup=False),
             require_success=True)
    malformed = bytearray(complete)
    malformed[len(transport.MAGIC) + 4] ^= 1
    rejected(transport.parse_response, bytes(malformed), require_success=True)
    corrupted = bytearray(complete)
    marker = b"representative archive bytes"
    corrupted[bytes(corrupted).index(marker)] ^= 1
    rejected(transport.parse_response, bytes(corrupted), require_success=True)
    control_only = response_fixture(success=False, include_bulk=False)
    assert not transport.parse_response(
        control_only, require_success=False)["success"]
    rejected(transport.parse_response, control_only, require_success=True)
    # Timeout authority applies only to this newly spawned retained child.
    rejected(admission.run_owned,
             [sys.executable, "-c", "import time; time.sleep(2)"],
             timeout=0.01)


def plan_contract(manifest: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="specialization-alignment-v3-plan-") as raw:
        temporary = Path(raw)
        corpus = temporary / "corpus"
        output = temporary / "output"
        corpus.mkdir()
        for directory in ("stages", "runner"):
            (output / directory).mkdir(parents=True, exist_ok=True)
        cases = {}
        for row in manifest["corpus"]:
            (corpus / row["file"]).touch()
            cases[row["case_id"]] = row
        plan = operator.frozen_profile_plan(
            manifest, Path("/frozen/runner"), corpus, cases, output)
        assert len(plan) == 36
        assert [row["ordinal"] for row in plan] == list(range(36))
        assert {row["variant"] for row in plan} == {"B", "L", "H"}
        assert all(row["command"][-2:] == ["1", "4"] for row in plan)
        assert not any(token in ("xctrace", "sample")
                       for row in plan for token in row["command"])


def authority_rejections() -> None:
    source, source_tree, freeze, freeze_tree = (
        "1" * 40, "2" * 40, "3" * 40, "4" * 40)
    digest = "a" * 64
    receipt_paths = (
        "transfer-cleanup.json", "rehearsal.json",
        "return-protocol/source-admission.json",
        "return-protocol/cleanup-footer.json")
    envelope = {
        "schema": executor.AUTHORIZATION_SCHEMA,
        "authorization_status": "AUTHORIZED",
        "phase_2_authority": "ALIGNMENT_V3_DIAGNOSTIC_ONLY",
        "source_commit": source, "source_tree": source_tree,
        "manifest_sha256": digest, "protocol_sha256": digest,
        "schema_catalog_sha256": digest, "transport_source_sha256": digest,
        "rehearsal_hash_index_sha256": digest,
        "rehearsal_receipt_hashes": {path: digest for path in receipt_paths},
        "observed_transport_calibration": {
            "representative_payload_bytes": 2 * 1024 * 1024,
            "archive_bytes": 600 * 1024, "chunk_count": 3,
            "transaction_elapsed_ns": 1, "finite_margin_ratio": 4.0},
        "cleanup_footer_verified": True,
        "remote_cleanup_absence_proved": True,
        "integrity_footer_verified": True,
        "source_admission_verified": True,
        "archive_integrity_verified": True,
        "process_isolation_verified": True,
        "channel_ready_verified": True,
        "request_stream_acknowledged": True,
        "response_channel_verified": True,
        "framed_response_cap_verified": True,
        "archive_cap_verified": True,
        "benchmark_lease_acquisition_attempted": False,
        "post_run_remote_cleanup_operations": 0,
        "timed_execution_authorized": True}
    diff = [
        ("A", "evidence/backref-cost-specialization-alignment-v3-design/rehearsal/raw.bin"),
        ("A", "evidence/backref-cost-specialization-alignment-v3-design/phase1b-rehearsal-hashes.json"),
        ("A", "evidence/backref-cost-specialization-alignment-v3-design/phase1b-authorization.json")]
    kwargs = {
        "envelope": envelope, "head_commit": freeze, "head_tree": freeze_tree,
        "parents": [source], "source_tree": source_tree, "diff_entries": diff,
        "source_hashes": {key: digest for key in (
            "manifest", "protocol", "schemas", "transport")},
        "hash_index_sha256": digest,
        "receipt_identities": {path: (source, source_tree)
                               for path in receipt_paths}}
    assert executor.validate_authority_values(**kwargs) == source
    fixtures = [
        {**kwargs, "parents": ["9" * 40]},
        {**kwargs, "diff_entries": diff + [("M", "scripts/frozen.py")]},
        {**kwargs, "hash_index_sha256": "6" * 64},
        {**kwargs, "envelope": None},
    ]
    for field in ("channel_ready_verified", "request_stream_acknowledged",
                  "response_channel_verified"):
        changed = copy.deepcopy(kwargs)
        changed["envelope"][field] = False
        fixtures.append(changed)
    stale = copy.deepcopy(kwargs)
    stale["receipt_identities"]["rehearsal.json"] = ("8" * 40, source_tree)
    fixtures.append(stale)
    for fixture in fixtures:
        rejected(executor.validate_authority_values, **fixture)


def strict_hash_index_order_contract() -> None:
    paths = [
        "rehearsal.json",
        "return-protocol/channel-stdout.bin",
        "return-protocol/cleanup-footer.json",
        "return-protocol/framed-response.bin",
        "transfer-cleanup.json",
    ]
    rows = [{"path": path} for path in paths]
    assert executor.validate_rehearsal_hash_row_order(rows) == paths
    rejected(executor.validate_rehearsal_hash_row_order,
             [rows[0], rows[3], rows[1], rows[2]])
    rejected(executor.validate_rehearsal_hash_row_order,
             [rows[0], rows[0]])


def compact_inventory_contract() -> None:
    inspected = {"schema": "inventory", "member_count": 3,
                 "members": [{"name": "a"}], "status": "accepted"}
    compact = {
        "member_count": 3,
        "inventory_sha256": transport.sha256_bytes(
            transport.canonical_json(inspected)),
    }
    executor.validate_compact_inventory(compact, inspected)
    rejected(executor.validate_compact_inventory,
             {**compact, "inventory_sha256": "0" * 64}, inspected)


def compact_source_control_freeze_contract(manifest: dict) -> None:
    freeze_path = ROOT / manifest["source_admission_control_freeze"]["path"]
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    paths = manifest["admission_identity_paths"]
    source_hashes = {path: sha256(ROOT / path) for path in sorted(paths)}
    count, digest = transport.source_map_commitment(source_hashes)
    compact = freeze["compact_receipt"]
    transport.validate_compact_source_receipt_shape(compact)
    payload = transport.canonical_json(compact)
    encoded = transport._encoded_json("source-admission", compact, 0)
    assert freeze["status"] == "PASS"
    assert freeze["identity_paths"] == sorted(paths)
    assert freeze["identity_path_count"] == count
    assert freeze["exact_sorted_source_map_sha256"] == digest
    assert compact["source_map_entry_count"] == count
    assert compact["source_map_sha256"] == digest
    assert freeze["compact_control_payload_bytes"] == len(payload)
    assert freeze["compact_encoded_frame_bytes"] == len(encoded)
    assert freeze["compact_control_payload_margin_bytes"] == \
        transport.MAX_CONTROL_PAYLOAD_BYTES - len(payload)
    assert len(payload) < transport.MAX_CONTROL_PAYLOAD_BYTES
    assert freeze["alignment_v1_full_map_control_payload_bytes"] > \
        transport.MAX_CONTROL_PAYLOAD_BYTES
    assert freeze["negative_alignment_v1_full_map_exceeds_cap"] is True
    assert freeze["positive_alignment_v3_compact_fits_cap"] is True
    assert "source_hashes" not in json.dumps(compact)


def v4_audit_and_null_contract(manifest: dict) -> None:
    audit = json.loads((
        ROOT / "evidence/backref-cost-specialization-alignment-v3-design/phase1-prior-evidence-audit.json"
    ).read_text())
    assert audit["status"] == "PASS_WITH_V4_RAW_MAP_RECONSTRUCTED"
    assert audit["performance_samples_generated"] == 0
    assert audit["remote_contacts"] == 0
    assert audit["v4_raw_indexes"]["artifact-hashes.json"]["rows"] == 123
    assert audit["v4_raw_indexes"]["returned-evidence-hashes.json"]["rows"] == 133
    assert all(not row["mismatches"]
               for row in audit["v4_raw_indexes"].values())
    assert audit["v4_codegen_crosscheck"][
        "local_remote_common_facts_equal"] is True
    assert len(audit["v4_linker_map_rows"]) == 6
    bounds = manifest["acceptance"]["mandatory_b_to_l_null_control"]
    passing = {"mean_percent": 0.1,
               "bootstrap_mean_ci95_percent": [-0.2, 0.3],
               "paired_percentages": [-0.4, 0.2] * 6}
    assert evaluator.null_control(passing, bounds)["passes"]
    fixtures = [
        {**passing, "mean_percent": 0.751},
        {**passing, "bootstrap_mean_ci95_percent": [0.01, 0.3]},
        {**passing, "bootstrap_mean_ci95_percent": [-1.501, 0.3]},
        {**passing, "paired_percentages": [-0.4] * 11 + [3.001]},
    ]
    assert all(not evaluator.null_control(row, bounds)["passes"]
               for row in fixtures)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["base_commit"] == \
        "c208d6ed33b0ee5e84ba02e78696879266658e7e"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_SPECIALIZATION_ALIGNMENT_V3_VARIANT"
    assert manifest["protocol_version"] == transport.PROTOCOL_VERSION == 10
    assert manifest["protocol"]["profile_processes"] == 36
    assert manifest["protocol"]["warmups_per_profile"] == 1
    assert manifest["protocol"]["retained_encodes_per_profile"] == 4
    assert manifest["protocol"]["retained_stage_records"] == 144
    assert manifest["protocol"]["runner_output_records"] == 180
    assert manifest["protocol"]["stage_records"] == 180
    assert "24 total" in manifest["protocol"]["correctness"]
    assert "exactly 12 untimed work rows" in manifest["protocol"][
        "selected_dp_structure"]
    assert "100000-resample" in manifest["protocol"]["statistics"]
    assert "0x424c4801" in manifest["protocol"]["statistics"]
    assert manifest["protocol"]["alignment_boundary_bytes"] == 16384
    assert manifest["protocol"]["entry_order"] == [
        "PushInterval", "PushIntervalLayoutClone", "PushIntervalSpecialized",
        "BackwardReferencesHashChainDistanceOnly",
        "BackwardReferencesHashChainDistanceOnlyLayoutClone",
        "BackwardReferencesHashChainDistanceOnlySpecialized"]
    assert "B->L" in manifest["protocol"]["pairing"]
    assert "H may be proposed only" in manifest["acceptance"][
        "production_promotion"]
    null = manifest["acceptance"]["mandatory_b_to_l_null_control"]
    assert null["per_cell_absolute_mean_percent_max"] == 0.75
    assert null["per_cell_bootstrap_95_ci_endpoint_absolute_percent_max"] == 1.50
    assert null["per_paired_row_absolute_percent_max"] == 3.00
    assert manifest["diagnostic"]["external_profiler_invocations"] == 0
    assert "range <0.10" in manifest["acceptance"]["repeatability"]
    evaluator_source = (ROOT / "scripts" /
        "evaluate_backref_cost_specialization_alignment_v3.py").read_text()
    assert "if any(value >= 0.10" in evaluator_source
    null_gate = evaluator_source.index("if null_passes:")
    assert evaluator_source.index("classify_effect(", null_gate) > null_gate
    assert manifest["return_contract"]["single_remote_session"] is True
    assert manifest["return_contract"]["remote_interactions_per_transaction"] == 1
    assert manifest["process_isolation"][
        "positive_ancestor_identity_sets"] is None
    assert manifest["return_contract"][
        "representative_rehearsal_payload_bytes"] >= manifest[
            "return_contract"]["maximum_expected_run_archive_bytes"]
    assert transport.MAX_ARCHIVE_BYTES == 768 * 1024
    assert transport.MAX_RESPONSE_BYTES == 1024 * 1024
    assert transport.MAX_CONTROL_PAYLOAD_BYTES == 8 * 1024
    assert transport.CHUNK_BYTES == 256 * 1024
    assert transport.MAX_BOOTSTRAP_SOURCE_BYTES == 24 * 1024
    assert transport.MAX_REQUEST_DECLARATION_BYTES == 8 * 1024
    assert transport.MAX_REQUEST_BYTES == 32 * 1024 * 1024
    assert transport.MAX_SOURCE_BUNDLE_BYTES == 28 * 1024 * 1024
    assert transport.REQUEST_CHUNK_BYTES == 64 * 1024
    assert manifest["return_contract"]["maximum_expected_run_archive_bytes"] == \
        512 * 1024
    assert manifest["return_contract"]["representative_rehearsal_payload_bytes"] == \
        2 * 1024 * 1024
    assert manifest["return_contract"]["timeouts"] == {
        "ssh_connect_seconds": 30,
        "ssh_connect_justification": "overlay first-session admission only",
        "server_alive_interval_seconds": 15,
        "server_alive_count_max": 3, "absolute_transaction_seconds": 1800,
        "silent_operator_seconds": 900,
        "connect_channel_ready_seconds": 45,
        "request_progress_seconds": 15,
        "response_progress_seconds": 15}
    expected = ('env WEBP_BENCHMARK_SESSION=exclusive '
                'EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" '
                'python3 scripts/execute_backref_cost_specialization_alignment_v3.py run '
                '"$PWD/evidence/backref-cost-specialization-alignment-v3-execution-20260820"')
    assert manifest["frozen_phase_2_command"] == expected
    for row in manifest["frozen_artifacts"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    admission_set = set(admission.IDENTITY_PATHS) | set(
        manifest["admission_identity_paths"])
    frozen_set = {manifest["frozen_artifact_set"]["self_manifest"]} | {
        row["path"] for row in manifest["frozen_artifacts"]}
    assert admission_set == frozen_set
    assert set(manifest["frozen_artifact_set"][
        "payload_identity_required_members"]).issubset(frozen_set)
    assert set(manifest["frozen_artifact_set"][
        "toolchain_identity_required_members"]).issubset(frozen_set)
    assert manifest["toolchain_identity_gate"]["identity"] == toolchain.identity()
    assert set(("ld", "otool")).issubset(
        manifest["toolchain_identity_gate"]["identity"][
            "required_executable_names"])
    assert "xcrun" not in json.dumps(manifest["required_child_commands"])
    semantic_identity()
    v4_audit_and_null_contract(manifest)
    framing_contracts()
    plan_contract(manifest)
    authority_rejections()
    strict_hash_index_order_contract()
    compact_inventory_contract()
    compact_source_control_freeze_contract(manifest)
    print("PASS: specialization alignment v3 frozen semantics, strict single-session frames, "
          "all refusal fixtures, authority separation, and 36-command plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
