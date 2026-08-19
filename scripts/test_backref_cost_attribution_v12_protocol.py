#!/usr/bin/env python3
"""Untimed, workload-free protocol and freeze tests for attribution v12."""

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

import backref_cost_attribution_v12_admission as admission
import backref_cost_attribution_v12_transport as transport
import execute_backref_cost_attribution_v12 as executor
import run_backref_cost_attribution_v12_experiment as operator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_attribution_v12_manifest.json"


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
    frozen = subprocess.check_output(
        ["git", "show", "673bc3fa:src/enc/backward_references_cost_enc.c"],
        cwd=ROOT, text=True)
    current = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    normalize = lambda value: re.sub(r"\s+", "", value)
    assert normalize(extract_body(frozen, "PushIntervalSpecialized")) == \
        normalize(extract_body(current, "PushIntervalSpecialized"))
    boundary = current.split(
        "// V12 preserves V11's frozen control flow and timer ownership exactly.",
        1)[1].split("#else", 1)[0]
    assert boundary.count("VP8LBackrefCostAttributionV12ExperimentEnabled()") == 1
    assert boundary.count("BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert boundary.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert "VP8LBackrefCostAttributionV12RecordSelector();" in boundary
    preprocessed = subprocess.check_output(
        [os.environ.get("CC", "cc"), "-E", "-P", f"-I{ROOT}",
         "-DWEBP_USE_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT=1",
         "src/enc/backward_references_cost_enc.c"], cwd=ROOT, text=True)
    traceback = extract_body(preprocessed, "VP8LBackwardReferencesTraceBackwards")
    assert traceback.count("BackwardReferencesHashChainDistanceOnlySpecialized(") == 1
    assert traceback.count("BackwardReferencesHashChainDistanceOnly(") == 1
    assert traceback.count(
        "WebPProfileStageBegin(WEBP_PROFILE_BACKREF_COST_DP_TOTAL)") == 1


def response_fixture(*, success: bool = True, cleanup: bool = True,
                     include_bulk: bool = True) -> bytes:
    archive = b"representative archive bytes" if include_bulk else b""
    operator_status = {
        "status": "complete" if success else "refused",
        "benchmark_lease_acquisition_attempted": False}
    frames = [
        ("source-admission", transport.canonical_json({
            "status": "verified", "source_commit": "1" * 40,
            "source_tree": "2" * 40}), {"sequence": 0}),
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
        declaration = {"archive_bytes": len(archive),
                       "archive_sha256": transport.sha256_bytes(archive),
                       "chunk_count": 1, "chunk_bytes": transport.CHUNK_BYTES,
                       "inventory": {"status": "accepted"}}
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
    with tempfile.TemporaryDirectory(prefix="attribution-v12-plan-") as raw:
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
        assert len(plan) == 24
        assert [row["ordinal"] for row in plan] == list(range(24))
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
        "source_commit": source, "source_tree": source_tree,
        "manifest_sha256": digest, "protocol_sha256": digest,
        "schema_catalog_sha256": digest, "transport_source_sha256": digest,
        "rehearsal_hash_index_sha256": digest,
        "rehearsal_receipt_hashes": {path: digest for path in receipt_paths},
        "observed_transport_calibration": {
            "representative_payload_bytes": 16 * 1024 * 1024,
            "archive_bytes": 16 * 1024 * 1024, "chunk_count": 32,
            "transaction_elapsed_ns": 1, "finite_margin_ratio": 2.0},
        "cleanup_footer_verified": True,
        "post_run_remote_cleanup_operations": 0,
        "timed_execution_authorized": True}
    diff = [
        ("A", "evidence/backref-cost-attribution-v12-design/rehearsal/raw.bin"),
        ("A", "evidence/backref-cost-attribution-v12-design/phase1b-rehearsal-hashes.json"),
        ("A", "evidence/backref-cost-attribution-v12-design/phase1b-authorization.json")]
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
    stale = copy.deepcopy(kwargs)
    stale["receipt_identities"]["rehearsal.json"] = ("8" * 40, source_tree)
    fixtures.append(stale)
    for fixture in fixtures:
        rejected(executor.validate_authority_values, **fixture)


def strict_hash_index_order_contract() -> None:
    paths = [
        "rehearsal.json",
        "return-protocol/cleanup-footer.json",
        "return-protocol/framed-stdout.bin",
        "transfer-cleanup.json",
    ]
    rows = [{"path": path} for path in paths]
    assert executor.validate_rehearsal_hash_row_order(rows) == paths
    rejected(executor.validate_rehearsal_hash_row_order,
             [rows[0], rows[3], rows[1], rows[2]])
    rejected(executor.validate_rehearsal_hash_row_order,
             [rows[0], rows[0]])


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["base_commit"] == \
        "6e6fa6905b67c65a10b3a0e80111fd93d9a82552"
    assert manifest["candidate"]["build_flag"] == \
        "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT"
    assert manifest["candidate"]["runtime_flag"] == \
        "WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT"
    assert manifest["protocol"]["profile_processes"] == 24
    assert manifest["protocol"]["retained_stage_records"] == 96
    assert manifest["acceptance"]["production_promotion_forbidden"]
    assert manifest["diagnostic"]["external_profiler_invocations"] == 0
    assert manifest["return_contract"]["single_remote_session"] is True
    assert manifest["process_isolation"][
        "positive_ancestor_identity_sets"] is None
    assert manifest["return_contract"][
        "representative_rehearsal_payload_bytes"] >= manifest[
            "return_contract"]["maximum_expected_run_archive_bytes"]
    assert transport.MAX_ARCHIVE_BYTES == 32 * 1024 * 1024
    assert manifest["return_contract"]["maximum_expected_run_archive_bytes"] == \
        8 * 1024 * 1024
    assert manifest["return_contract"]["representative_rehearsal_payload_bytes"] == \
        16 * 1024 * 1024
    assert manifest["return_contract"]["timeouts"] == {
        "ssh_connect_seconds": 10, "server_alive_interval_seconds": 15,
        "server_alive_count_max": 3, "absolute_transaction_seconds": 1800,
        "silent_operator_seconds": 900,
        "request_and_bulk_progress_seconds": 15}
    expected = ('env WEBP_BENCHMARK_SESSION=exclusive '
                'EXPECTED_FREEZE_COMMIT="$(git rev-parse HEAD)" '
                'python3 scripts/execute_backref_cost_attribution_v12.py run '
                '"$PWD/evidence/backref-cost-attribution-v12-execution-20260819"')
    assert manifest["frozen_phase_2_command"] == expected
    for row in manifest["frozen_artifacts"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    semantic_identity()
    framing_contracts()
    plan_contract(manifest)
    authority_rejections()
    strict_hash_index_order_contract()
    print("PASS: attribution v12 frozen semantics, strict single-session frames, "
          "all refusal fixtures, authority separation, and 24-command plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
