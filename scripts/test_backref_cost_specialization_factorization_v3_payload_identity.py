#!/usr/bin/env python3
"""Fail-closed V3 representative-payload triple-agreement gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import backref_cost_specialization_factorization_v3_payload as generator
import backref_cost_specialization_factorization_v3_transport as transport


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_specialization_factorization_v3_manifest.json"
FIXTURE = (ROOT / "evidence/backref-cost-specialization-factorization-v3-design" /
           "representative-payload-fixture.json")
RECEIPT = (ROOT / "evidence/backref-cost-specialization-factorization-v3-design" /
           "representative-payload-agreement.json")


def independent_digest(size: int) -> str:
    domain = b"libwebp-backref-cost-specialization-factorization-v3-rehearsal\x00"
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
    stale = generator.STALE_PREDECESSOR_SHA256
    assert stale == fixture["stale_predecessor_sha256"]
    assert stale not in observed
    assert receipt["negative_stale_predecessor_test"] == "PASS_REJECTED"
    assert receipt["status"] == "PASS"
    print(json.dumps({
        "status": "PASS", "payload_bytes": size, "sha256": expected,
        "manifest_generator_fixture_agree": True,
        "transport_generator_agrees": True,
        "stale_predecessor_sha256": stale,
        "negative_stale_predecessor_test": "PASS_REJECTED",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
