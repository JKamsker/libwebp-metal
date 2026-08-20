#!/usr/bin/env python3
"""Negative matrix for the sole generated V2 four-body identity domain."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v2_identity as identity


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v2-design/four-body-expected-receipt.json"
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_manifest.json"


def rejected(callable_) -> None:
    try:
        callable_()
    except (RuntimeError, ValueError, TypeError):
        return
    raise AssertionError("negative four-body fixture was accepted")


def main() -> int:
    domain = identity.domain()
    identity.assert_exact_domain(domain["entries"])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["four_body_identity"] == identity.generator_binding()
    assert manifest["acceptance"]["codegen_symbols"] == identity.names()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    expected_bindings = manifest["four_body_receipt_bindings"]
    identity.validate_machine_receipt(receipt, expected_bindings)

    domain_fixtures = []
    stale_six = copy.deepcopy(domain["entries"])
    stale_six.extend([
        {"symbol": "PushIntervalSpecialized", "variant": "H",
         "role": "push_interval", "ordinal": 4, "pair_ordinal": 0},
        {"symbol": "BackwardReferencesHashChainDistanceOnlySpecialized",
         "variant": "H", "role": "dp", "ordinal": 5, "pair_ordinal": 1},
    ])
    domain_fixtures.append(stale_six)
    for mutation in ("missing", "extra", "duplicate", "reordered", "wrong-role"):
        rows = copy.deepcopy(domain["entries"])
        if mutation == "missing": rows.pop()
        elif mutation == "extra": rows.append(copy.deepcopy(rows[-1]) | {"symbol": "extra"})
        elif mutation == "duplicate": rows[-1]["symbol"] = rows[0]["symbol"]
        elif mutation == "reordered": rows[0], rows[1] = rows[1], rows[0]
        else: rows[0]["role"] = "dp"
        domain_fixtures.append(rows)
    for rows in domain_fixtures:
        rejected(lambda rows=rows: identity.assert_exact_domain(rows))

    receipt_fixtures = []
    for mutation in ("wrong-count", "wrong-address", "wrong-spacing",
                     "wrong-modulus", "wrong-generator", "wrong-facts",
                     "wrong-section", "wrong-padding", "missing-binary",
                     "wrong-source-binding", "wrong-tree-binding",
                     "wrong-build-binding", "wrong-manifest-binding"):
        row = copy.deepcopy(receipt)
        if mutation == "wrong-count": row["symbol_addresses"].pop(identity.names()[-1])
        elif mutation == "wrong-address": row["symbol_addresses"][identity.names()[1]] = row["symbol_addresses"][identity.names()[0]]
        elif mutation == "wrong-spacing": row["symbol_addresses"][identity.names()[1]] = f"{int(row['symbol_addresses'][identity.names()[1]], 16) + identity.BOUNDARY_BYTES:016x}"
        elif mutation == "wrong-modulus": row["symbol_addresses"][identity.names()[0]] = f"{int(row['symbol_addresses'][identity.names()[0]], 16) + 4:016x}"
        elif mutation == "wrong-generator": row["generator"]["domain_sha256"] = "0" * 64
        elif mutation == "wrong-facts": row["facts"][identity.names()[1]]["instruction_count"] += 1
        elif mutation == "wrong-section": row["section"]["flags"] = "0x0"
        elif mutation == "wrong-padding": row["padding_bytes"] += 1
        elif mutation == "missing-binary": row.pop("binary_sha256")
        elif mutation == "wrong-source-binding":
            row["bindings"]["source_base_commit"] = "0" * 40
        elif mutation == "wrong-tree-binding":
            row["bindings"]["source_base_tree"] = "0" * 40
        elif mutation == "wrong-build-binding":
            row["bindings"]["build_identity_sha256"] = "0" * 64
        else: row["bindings"]["manifest_identity_sha256"] = "0" * 64
        receipt_fixtures.append(row)
    for row in receipt_fixtures:
        rejected(lambda row=row: identity.validate_machine_receipt(
            row, expected_bindings))

    # Source/tree/build binding negatives are enforced by the Phase-1B gate;
    # ensure its authority implementation has no stale handwritten six-body facts.
    authority = (ROOT / "scripts/record_backref_cost_aligned_null_stage_attribution_v2_phase1b.py").read_text()
    for stale in ("all_six_private_addresses_distinct", "len(addresses) == 6",
                  "83212", "5624", "77588"):
        assert stale not in authority
    for binding in ("source_commit", "source_tree", "manifest.get(\"four_body_identity\")",
                    "timed_runner_sha256", "linker_map_sha256"):
        assert binding in authority

    print(json.dumps({
        "status": "PASS", "canonical_entries": identity.count(),
        "stale_v1_six_body_rejected": True,
        "domain_negative_fixtures": len(domain_fixtures),
        "receipt_negative_fixtures": len(receipt_fixtures),
        "expected_receipt_bytes": RECEIPT.stat().st_size,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
