#!/usr/bin/env python3
"""Fail-closed stage-attribution-v4 payload triple-agreement gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v4_payload as generator
import backref_cost_aligned_null_stage_attribution_v4_transport as transport


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v4_manifest.json"
FIXTURE = (ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v4-design" /
           "representative-payload-fixture.json")
RECEIPT = (ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v4-design" /
           "representative-payload-agreement.json")


def independent_digest(size: int) -> str:
    domain = b"libwebp-backref-cost-aligned-null-stage-attribution-v4-rehearsal\x00"
    output = hashlib.sha256()
    produced = 0
    counter = 0
    while produced < size:
        block = hashlib.sha256(domain + counter.to_bytes(8, "big")).digest()
        count = min(len(block), size - produced)
        output.update(block[:count])
        produced += count
        counter += 1
    return output.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    size = manifest["return_contract"]["representative_rehearsal_payload_bytes"]
    expected = manifest["return_contract"]["representative_rehearsal_payload_sha256"]
    generated = generator.sha256(size)
    independent = independent_digest(size)
    transported = transport.deterministic_payload_sha256(size)
    fixture_digest = fixture["sha256"]
    receipt_values = {
        receipt["manifest_sha256_value"],
        receipt["generator_recomputation_sha256"],
        receipt["independent_fixture_sha256_value"],
    }
    observed = {expected, generated, independent, transported, fixture_digest}
    assert observed == {expected}
    assert receipt_values == {expected}
    assert size == generator.PAYLOAD_BYTES == fixture["payload_bytes"]
    stale_v2 = generator.STALE_V2_SHA256
    stale_v4 = generator.STALE_V4_SHA256
    stale_v4 = generator.STALE_V4_SHA256
    stale_alignment_v1 = generator.STALE_ALIGNMENT_V1_SHA256
    stale_alignment_v2 = generator.STALE_ALIGNMENT_V2_SHA256
    stale_alignment_v4 = generator.STALE_ALIGNMENT_V4_SHA256
    assert stale_v2 == fixture["stale_v2_sha256"]
    assert stale_v4 == fixture["stale_v4_sha256"]
    assert stale_v4 == fixture["stale_v4_sha256"]
    assert stale_alignment_v1 == fixture["stale_alignment_v1_sha256"]
    assert stale_alignment_v2 == fixture["stale_alignment_v2_sha256"]
    assert stale_alignment_v4 == fixture["stale_alignment_v4_sha256"]
    assert stale_v2 not in observed and stale_v4 not in observed and \
        stale_v4 not in observed and stale_alignment_v1 not in observed and \
        stale_alignment_v2 not in observed and stale_alignment_v4 not in observed
    assert receipt["negative_stale_v2_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_v4_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_v4_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v1_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v2_test"] == "PASS_REJECTED"
    assert receipt["negative_stale_alignment_v4_test"] == "PASS_REJECTED"
    assert receipt["status"] == "PASS"
    print(json.dumps({
        "status": "PASS", "payload_bytes": size, "sha256": expected,
        "manifest_generator_fixture_agree": True,
        "transport_generator_agrees": True,
        "stale_v2_sha256": stale_v2, "stale_v4_sha256": stale_v4,
        "stale_v4_sha256": stale_v4,
        "stale_alignment_v1_sha256": stale_alignment_v1,
        "stale_alignment_v2_sha256": stale_alignment_v2,
        "stale_alignment_v4_sha256": stale_alignment_v4,
        "negative_stale_v2_test": "PASS_REJECTED",
        "negative_stale_v4_test": "PASS_REJECTED",
        "negative_stale_v4_test": "PASS_REJECTED",
        "negative_stale_alignment_v1_test": "PASS_REJECTED",
        "negative_stale_alignment_v2_test": "PASS_REJECTED",
        "negative_stale_alignment_v4_test": "PASS_REJECTED",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
