#!/usr/bin/env python3
"""Untimed attribution-v13 path, admission, frame, and mode tests."""

from __future__ import annotations

import hashlib
import io
import os
import subprocess
import tempfile
from pathlib import Path

import backref_cost_attribution_v13_admission as admission
import backref_cost_attribution_v13_transport as transport
import execute_backref_cost_attribution_v13 as executor
from backref_cost_attribution_v13_paths import (
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
    assert SAFE_ROOT_BASENAME.endswith("attribution-v13")
    assert validate_shape(home, root, run) == "run.A21KcK"
    rejected(validate_shape, home, root, f"{root}/run.bad")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v8/run.A21KcK")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v9/run.A21KcK")
    rejected(validate_shape, home, root,
             f"{home}/.libwebp-metal-backref-cost-attribution-v10/run.A21KcK")
    with tempfile.TemporaryDirectory(prefix="attribution-v13-path-home-") as raw:
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
    with tempfile.TemporaryDirectory(prefix="attribution-v13-admit-") as raw:
        root = Path(raw)
        repository = root / "repository"
        child = root / "run.12345678"
        repository.mkdir()
        child.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name",
                        "v13 admission test"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email",
                        "v13@example.invalid"], check=True)
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
        receipt = transport._admit_source(child, bundle, metadata)
        assert receipt["status"] == "verified"
        assert receipt["source_commit"] == commit and receipt["source_tree"] == tree
        assert receipt["admission"]["verification_repository_removed"]


def frame_and_receipt_contracts() -> None:
    payload = transport.deterministic_payload(4096)
    metadata = {"protocol_version": 1, "mode": "rehearse"}
    request = transport.request_bytes(metadata, b"bundle", payload)
    decoded, bundle, observed = transport.parse_request(io.BytesIO(request))
    assert decoded == metadata and bundle == b"bundle" and observed == payload
    rejected(transport.parse_request, io.BytesIO(request[:-1]))
    malformed = bytearray(request)
    malformed[-1] ^= 1
    rejected(transport.parse_request, io.BytesIO(bytes(malformed)))

    digest = "1" * 64
    valid = {"schema": admission.SOURCE_RECEIPT_SCHEMA,
             "receipt_version": admission.SOURCE_RECEIPT_VERSION,
             "source_bundle_sha256": digest,
             "admission": {"bundle_sha256": digest}}
    executor.validate_admission_receipt(valid, digest)
    invalid = dict(valid)
    invalid["source_bundle_sha256"] = "2" * 64
    rejected(executor.validate_admission_receipt, invalid, digest)


def remote_refusal_cleanup_contract() -> None:
    """A real local remote-end fixture refuses and cleans in one process."""
    with tempfile.TemporaryDirectory(prefix="attribution-v13-remote-home-") as raw:
        home = Path(raw).resolve()
        bundle = b"not a git bundle\n"
        metadata = {
            "protocol_version": transport.PROTOCOL_VERSION, "mode": "run",
            "source_commit": "1" * 40, "source_tree": "2" * 40,
            "source_hashes": {},
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


def main() -> int:
    path_tests()
    repository_context_admission()
    frame_and_receipt_contracts()
    remote_refusal_cleanup_contract()
    mode_truth_table()
    print("PASS: attribution v13 canonical-only paths, repository-context source "
          "admission, strict request frames, receipt hashes, and disjoint modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
