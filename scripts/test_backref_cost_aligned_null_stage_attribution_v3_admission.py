#!/usr/bin/env python3
"""Untimed stage-attribution-v3 path, admission, frame, and mode tests."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v3_admission as admission
import backref_cost_aligned_null_stage_attribution_v3_transport as transport
import execute_backref_cost_aligned_null_stage_attribution_v3 as executor
import backref_cost_aligned_null_stage_attribution_v3_archive as archive_protocol
from backref_cost_aligned_null_stage_attribution_v3_paths import (
    SAFE_ROOT_BASENAME, UnsafePath, cleanup, ensure_safe_root,
    validate_existing, validate_shape)


def rejected(function, *args, **kwargs) -> None:
    try:
        function(*args, **kwargs)
    except (OSError, RuntimeError, UnsafePath, transport.FrameRefusal):
        return
    raise AssertionError(f"unsafe input accepted: {function.__name__}")


def path_tests() -> None:
    home = "/Users/pandocs-agent-001"
    root = f"{home}/{SAFE_ROOT_BASENAME}"
    run = f"{root}/run.A21KcK"
    assert SAFE_ROOT_BASENAME.endswith(
        "backref-cost-aligned-null-stage-attribution-v3")
    assert validate_shape(home, root, run) == "run.A21KcK"
    rejected(validate_shape, home, root, f"{root}/run.bad")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v8/run.A21KcK")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v9/run.A21KcK")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v10/run.A21KcK")
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-path-home-") as raw:
        actual_home = os.path.realpath(raw)
        previous = os.environ.get("HOME")
        os.environ["HOME"] = actual_home
        try:
            actual_root = ensure_safe_root(actual_home)
            actual_run = os.path.join(actual_root, "run.ABC123")
            os.mkdir(actual_run)
            assert validate_existing(actual_home, actual_root, actual_run)["validated"]
            proof = cleanup(actual_home, actual_root, actual_run)
            assert proof["absence_proved"] and not os.path.lexists(actual_run)
        finally:
            if previous is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = previous


def repository_context_admission() -> None:
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-admit-") as raw:
        root = Path(raw)
        repository = root / "repository"
        child = root / "run.12345678"
        repository.mkdir()
        child.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name",
                        "stage-attribution-v3 admission test"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email",
                        "stage-attribution-v3@example.invalid"], check=True)
        source_file = repository / "source.txt"
        source_file.write_text("exact source\n")
        subprocess.run(["git", "-C", str(repository), "add", "source.txt"],
                       check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-q", "-m",
                        "fixture"], check=True)
        commit = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD^{tree}"],
            text=True).strip()
        bundle = child / "source.bundle"
        subprocess.run(["git", "-C", str(repository), "bundle", "create",
                        str(bundle), "HEAD"], check=True)
        bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
        metadata = {"source_bundle_sha256": bundle_sha,
                    "source_commit": commit, "source_tree": tree,
                    "source_hashes": {"source.txt": hashlib.sha256(
                        source_file.read_bytes()).hexdigest()}}
        receipt, details = transport._admit_source(child, bundle, metadata)
        assert receipt["status"] == "verified"
        assert receipt["source_commit"] == commit and receipt["source_tree"] == tree
        assert receipt["verification_repository_removed"]
        assert "source_hashes" not in json.dumps(receipt)
        assert details["source_map"] == [{
            "path": "source.txt", "sha256": metadata["source_hashes"]["source.txt"]}]


def frame_and_receipt_contracts() -> None:
    payload = transport.deterministic_payload(4096)
    metadata = {"protocol_version": 1, "mode": "rehearse",
                "source_hashes": {"source.txt": "0" * 64}}
    request = transport.request_bytes(metadata, b"bundle", payload)
    decoded, bundle, observed = transport.parse_request(io.BytesIO(request))
    assert decoded == metadata and bundle == b"bundle" and observed == payload
    rejected(transport.parse_request, io.BytesIO(request[:-1]))
    malformed = bytearray(request)
    malformed[-1] ^= 1
    rejected(transport.parse_request, io.BytesIO(bytes(malformed)))
    rejected(transport.source_map_rows,
             {"z": "0" * 64, "a": "1" * 64})
    rejected(transport.strict_json_loads,
             b'{"source_hashes":{"a":"' + b"0" * 64 +
             b'","a":"' + b"1" * 64 + b'"}}')

    digest = "1" * 64
    requested = {"a-source.txt": digest, "z-source.txt": "2" * 64}
    count, source_digest = transport.source_map_commitment(requested)
    valid = {
        "schema": admission.SOURCE_RECEIPT_SCHEMA,
        "receipt_version": admission.SOURCE_RECEIPT_VERSION,
        "status": "verified", "source_commit": "1" * 40,
        "source_tree": "2" * 40, "source_bundle_sha256": digest,
        "source_map_entry_count": count,
        "source_map_sha256": source_digest,
        "bundle_verified_in_repository_context": True,
        "verification_repository_removed": True, "clean_status": True}
    executor.validate_admission_receipt(valid, digest, requested)
    invalid = dict(valid)
    invalid["source_bundle_sha256"] = "2" * 64
    rejected(executor.validate_admission_receipt, invalid, digest, requested)
    for key, value in (("source_map_entry_count", count + 1),
                       ("source_map_entry_count", True),
                       ("source_map_sha256", "0" * 64),
                       ("schema", "stale")):
        malformed = dict(valid)
        malformed[key] = value
        rejected(executor.validate_admission_receipt, malformed, digest,
                 requested)

    rows = transport.source_map_rows(requested)
    details = {
        "schema": transport.SOURCE_DETAILS_SCHEMA, "status": "verified",
        "source_commit": valid["source_commit"],
        "source_tree": valid["source_tree"],
        "source_bundle_sha256": digest,
        "source_map_entry_count": count,
        "source_map_sha256": source_digest, "source_map": rows}
    executor.validate_source_admission_details(details, requested, valid)
    for changed in (
            {**details, "source_map": list(reversed(rows))},
            {**details, "source_map": rows + rows},
            {**details, "source_map_entry_count": count + 1},
            {**details, "source_map_sha256": "0" * 64},
            {**details, "source_commit": "3" * 40}):
        rejected(executor.validate_source_admission_details, changed,
                 requested, valid)
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-details-") as raw:
        extracted = Path(raw)
        rejected(executor.validate_archived_source_admission,
                 extracted, requested, valid)
        (extracted / "source-admission-details.json").write_text(
            json.dumps({**details, "source_map_sha256": "0" * 64}))
        rejected(executor.validate_archived_source_admission,
                 extracted, requested, valid)


def remote_refusal_cleanup_contract() -> None:
    """A real local remote-end fixture refuses and cleans in one process."""
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-remote-home-") as raw:
        home = Path(raw).resolve()
        bundle = b"not a git bundle\n"
        metadata = {
            "protocol_version": transport.PROTOCOL_VERSION, "mode": "run",
            "source_commit": "1" * 40, "source_tree": "2" * 40,
            "source_hashes": {"source.txt": "3" * 64},
            "source_bundle_bytes": len(bundle),
            "source_bundle_sha256": hashlib.sha256(bundle).hexdigest(),
            "representative_payload_bytes": 0,
            "representative_payload_sha256": hashlib.sha256(b"").hexdigest(),
            "maximum_expected_run_archive_bytes": 4 * 1024 * 1024}
        request = transport.request_bytes(metadata, bundle, b"")
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        result = admission.run_owned(
            [os.environ.get("PYTHON", "python3"), str(Path(transport.__file__))],
            input_data=request, timeout=10, env=environment)
        assert result.returncode != 0
        parsed = transport.parse_response(result.stdout, require_success=False)
        assert not parsed["success"] and parsed["cleanup"]["absence_proved"]
        safe_root = home / transport.SAFE_ROOT_BASENAME
        assert safe_root.is_dir() and not any(safe_root.iterdir())


def mode_truth_table() -> None:
    for mode in ("validate", "rehearse", "run"):
        for value in (None, "", "exclusive", "shared"):
            environment = {} if value is None else {"WEBP_BENCHMARK_SESSION": value}
            accepted = ((mode in ("validate", "rehearse") and value is None) or
                        (mode == "run" and value == "exclusive"))
            if accepted:
                executor.validate_mode_environment(mode, environment)
            else:
                rejected(executor.validate_mode_environment, mode, environment)


def indexed_detail_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="stage-attribution-v3-indexed-detail-") as raw:
        evidence = Path(raw).resolve()
        original = evidence / "operator-status.json"
        original.write_text("{}\n")
        index = evidence / "artifact-hashes.json"
        index.write_text(json.dumps({
            "schema": archive_protocol.ARTIFACT_SCHEMA,
            "artifacts": [{
                "path": original.name, "bytes": original.stat().st_size,
                "sha256": hashlib.sha256(original.read_bytes()).hexdigest()}]
        }, indent=2, sort_keys=True) + "\n")
        detail = {"schema": transport.SOURCE_DETAILS_SCHEMA,
                  "status": "verified"}
        transport._add_indexed_detail(
            evidence, "source-admission-details.json", detail)
        value = json.loads(index.read_text())
        assert [row["path"] for row in value["artifacts"]] == [
            "operator-status.json", "source-admission-details.json"]
        archive_protocol.load_artifact_index(evidence, index)
        rejected(transport._add_indexed_detail,
                 evidence, "source-admission-details.json", detail)


def main() -> int:
    path_tests()
    repository_context_admission()
    frame_and_receipt_contracts()
    remote_refusal_cleanup_contract()
    mode_truth_table()
    indexed_detail_contract()
    print("PASS: specialization aligned null stage attribution v3 canonical-only paths, repository-context source "
          "admission, strict request frames, receipt hashes, and disjoint modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
