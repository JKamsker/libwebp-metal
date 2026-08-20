#!/usr/bin/env python3
"""Fail-closed stage-attribution-v2 toolchain agreement gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v2_toolchain as toolchain


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_manifest.json"
FIXTURE = (ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v2-design" /
           "toolchain-identity-fixture.json")
RECEIPT = (ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v2-design" /
           "toolchain-identity-agreement.json")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    actual = toolchain.identity()
    frozen = manifest["toolchain_identity_gate"]["identity"]
    assert frozen == actual == fixture["identity"]
    assert receipt["status"] == "PASS"
    assert receipt["manifest_actual_fixture_agree"] is True
    assert receipt["required_executables"] == list(toolchain.EXECUTABLE_PATHS)
    assert receipt["required_metadata"] == list(toolchain.METADATA_PATHS)
    canonical = json.dumps(actual, sort_keys=True,
                           separators=(",", ":")).encode()
    assert receipt["identity_canonical_sha256"] == \
        hashlib.sha256(canonical).hexdigest()
    serialized = json.dumps(frozen, sort_keys=True)
    assert "/usr/bin/xcrun" not in serialized
    assert "xcrun" not in frozen["required_executable_names"]
    assert frozen["xcrun_required"] is False
    assert frozen["stale_v2_xcrun_sha256"] == toolchain.STALE_V2_XCRUN_SHA256
    assert frozen["stale_v2_xcrun_rejected"] is True
    assert frozen["stale_v3_identity_canonical_sha256"] == \
        toolchain.STALE_V3_IDENTITY_CANONICAL_SHA256
    assert hashlib.sha256(canonical).hexdigest() != \
        toolchain.STALE_V3_IDENTITY_CANONICAL_SHA256
    assert frozen["stale_v4_identity_canonical_sha256"] == \
        toolchain.STALE_V4_IDENTITY_CANONICAL_SHA256
    assert hashlib.sha256(canonical).hexdigest() != \
        toolchain.STALE_V4_IDENTITY_CANONICAL_SHA256
    assert frozen["stale_alignment_v1_identity_canonical_sha256"] == \
        toolchain.STALE_ALIGNMENT_V1_IDENTITY_CANONICAL_SHA256
    assert hashlib.sha256(canonical).hexdigest() != \
        toolchain.STALE_ALIGNMENT_V1_IDENTITY_CANONICAL_SHA256
    assert frozen["stale_alignment_v2_identity_canonical_sha256"] == \
        toolchain.STALE_ALIGNMENT_V2_IDENTITY_CANONICAL_SHA256
    assert hashlib.sha256(canonical).hexdigest() != \
        toolchain.STALE_ALIGNMENT_V2_IDENTITY_CANONICAL_SHA256
    assert frozen["stale_alignment_v3_identity_canonical_sha256"] == \
        toolchain.STALE_ALIGNMENT_V3_IDENTITY_CANONICAL_SHA256
    assert hashlib.sha256(canonical).hexdigest() != \
        toolchain.STALE_ALIGNMENT_V3_IDENTITY_CANONICAL_SHA256
    assert receipt["negative_stale_v3_identity_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_v4_identity_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v1_identity_test"] == \
        "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v2_identity_test"] == \
        "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v3_identity_test"] == \
        "PASS_REJECTED"
    commands = json.dumps(manifest["required_child_commands"], sort_keys=True)
    assert "xcrun" not in commands
    assert toolchain.STALE_V2_XCRUN_SHA256 not in commands
    print(json.dumps({
        "status": "PASS", "manifest_actual_fixture_agree": True,
        "required_executables": len(toolchain.EXECUTABLE_PATHS),
        "required_metadata": len(toolchain.METADATA_PATHS),
        "xcrun_required": False,
        "stale_v2_xcrun_negative_test": "PASS_REJECTED",
        "stale_v3_identity_negative_test": "PASS_REJECTED",
        "stale_v4_identity_negative_test": "PASS_REJECTED",
        "stale_alignment_v1_identity_negative_test": "PASS_REJECTED",
        "stale_alignment_v2_identity_negative_test": "PASS_REJECTED",
        "stale_alignment_v3_identity_negative_test": "PASS_REJECTED",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
