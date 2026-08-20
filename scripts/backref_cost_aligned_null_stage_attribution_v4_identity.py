#!/usr/bin/env python3
"""Canonical four-body identity domain for aligned-null attribution V4.

This module is the only authored symbol inventory.  Every consumer imports it;
JSON receipts may contain generated copies, but no consumer owns another list
or count.
"""

from __future__ import annotations

import hashlib
import json
import copy
from dataclasses import asdict, dataclass
from typing import Iterable


DOMAIN_SCHEMA = (
    "libwebp-backref-cost-aligned-null-stage-attribution-v4-four-body-domain-v1"
)
EXPECTED_RECEIPT_SCHEMA = (
    "libwebp-backref-cost-aligned-null-stage-attribution-v4-four-body-expected-receipt-v1"
)
ACTUAL_RECEIPT_SCHEMA = (
    "libwebp-backref-cost-aligned-null-stage-attribution-v4-four-body-actual-receipt-v1"
)
BOUNDARY_BYTES = 16384
SECTION_SEGMENT = "__TEXT"
SECTION_NAME = "__br_null_v4"
SECTION_FLAGS = "0x80000400"
SECTION_ALIGNMENT_POWER = 14
NO_DEDUPLICATE_FLAG = "-Wl,-no_deduplicate"


@dataclass(frozen=True)
class HotEntry:
    symbol: str
    variant: str
    role: str
    ordinal: int
    pair_ordinal: int


# The sole authored expected-symbol list, in required address order.
HOT_ENTRIES = (
    HotEntry("PushInterval", "B", "push_interval", 0, 0),
    HotEntry("PushIntervalLayoutClone", "L", "push_interval", 1, 0),
    HotEntry("BackwardReferencesHashChainDistanceOnly", "B", "dp", 2, 1),
    HotEntry(
        "BackwardReferencesHashChainDistanceOnlyLayoutClone", "L", "dp", 3, 1
    ),
)


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def domain() -> dict:
    value = {
        "schema": DOMAIN_SCHEMA,
        "entries": [asdict(entry) for entry in HOT_ENTRIES],
        "boundary_bytes": BOUNDARY_BYTES,
        "entry_modulo_required": 0,
        "inter_entry_spacing_bytes": BOUNDARY_BYTES,
        "dp_to_corresponding_push_displacement_bytes": 2 * BOUNDARY_BYTES,
        "section": {
            "segment": SECTION_SEGMENT,
            "name": SECTION_NAME,
            "flags": SECTION_FLAGS,
            "alignment_power": SECTION_ALIGNMENT_POWER,
            "executable_pure_instructions": True,
        },
        "no_deduplicate_flag": NO_DEDUPLICATE_FLAG,
        "deduplication_forbidden": True,
    }
    value["domain_sha256"] = hashlib.sha256(canonical_json(value)).hexdigest()
    return value


def names() -> list[str]:
    return [entry.symbol for entry in HOT_ENTRIES]


def count() -> int:
    return len(HOT_ENTRIES)


def equivalence_pairs() -> list[tuple[str, str]]:
    result = []
    for role in ("push_interval", "dp"):
        entries = [entry for entry in HOT_ENTRIES if entry.role == role]
        result.append((entries[0].symbol, entries[1].symbol))
    return result


def normalization_aliases() -> dict[str, str]:
    """Return generated L-to-B symbol aliases for normalized disassembly."""
    return {layout: baseline for baseline, layout in equivalence_pairs()}


def displacement_pairs() -> list[tuple[str, str]]:
    result = []
    for variant in ("B", "L"):
        push = next(entry.symbol for entry in HOT_ENTRIES
                    if entry.variant == variant and entry.role == "push_interval")
        dp = next(entry.symbol for entry in HOT_ENTRIES
                  if entry.variant == variant and entry.role == "dp")
        result.append((push, dp))
    return result


def expected_addresses(section_address: int) -> dict[str, str]:
    return {
        entry.symbol: f"{section_address + entry.ordinal * BOUNDARY_BYTES:016x}"
        for entry in HOT_ENTRIES
    }


def assert_exact_domain(rows: Iterable[dict]) -> None:
    observed = list(rows)
    expected = [asdict(entry) for entry in HOT_ENTRIES]
    if observed != expected:
        raise RuntimeError("four-body identity domain mismatch")
    if len({row["symbol"] for row in observed}) != count():
        raise RuntimeError("four-body identity contains duplicate symbols")
    if [row["ordinal"] for row in observed] != list(range(count())):
        raise RuntimeError("four-body identity order/count mismatch")


def assert_address_geometry(addresses: dict[str, str]) -> None:
    if list(addresses) != names():
        raise RuntimeError("four-body symbol order mismatch")
    values = [int(addresses[name], 16) for name in names()]
    if len(set(values)) != count():
        raise RuntimeError("four-body symbols were deduplicated")
    if any(value % BOUNDARY_BYTES for value in values):
        raise RuntimeError("four-body entry modulo mismatch")
    if any(right - left != BOUNDARY_BYTES for left, right in zip(values, values[1:])):
        raise RuntimeError("four-body entry spacing mismatch")
    for push, dp in displacement_pairs():
        if int(addresses[dp], 16) - int(addresses[push], 16) != 2 * BOUNDARY_BYTES:
            raise RuntimeError("four-body B/L role displacement mismatch")


def generator_binding() -> dict:
    value = domain()
    return {
        "schema": DOMAIN_SCHEMA,
        "domain_sha256": value["domain_sha256"],
        "entries": value["entries"],
        "entry_count": count(),
    }


def validate_machine_receipt(receipt: dict,
                             expected_bindings: dict | None = None) -> None:
    if receipt.get("schema") != EXPECTED_RECEIPT_SCHEMA:
        raise RuntimeError("four-body receipt schema mismatch")
    if receipt.get("generator") != generator_binding():
        raise RuntimeError("receipt was not derived from canonical generator")
    bindings = receipt.get("bindings")
    required_bindings = {
        "source_base_commit", "source_base_tree", "build_identity_sha256",
        "manifest_identity_sha256", "generator_file_sha256"}
    if not isinstance(bindings, dict) or set(bindings) != required_bindings or \
            len(bindings["source_base_commit"]) != 40 or \
            len(bindings["source_base_tree"]) != 40 or \
            any(len(bindings[name]) != 64 for name in required_bindings
                if name not in ("source_base_commit", "source_base_tree")):
        raise RuntimeError("four-body receipt binding schema mismatch")
    if expected_bindings is not None and bindings != expected_bindings:
        raise RuntimeError("four-body source/tree/build/manifest binding mismatch")
    addresses = receipt.get("symbol_addresses")
    facts = receipt.get("facts")
    if not isinstance(addresses, dict) or set(addresses) != set(names()) or \
            not isinstance(facts, dict) or set(facts) != set(names()):
        raise RuntimeError("four-body receipt symbol inventory mismatch")
    ordered_addresses = {name: addresses[name] for name in names()}
    assert_address_geometry(ordered_addresses)
    for left, right in equivalence_pairs():
        lhs, rhs = facts[left], facts[right]
        for field in ("size_bytes", "instruction_count", "branch_count",
                      "load_count", "store_count", "mnemonics_sha256",
                      "canonical_instructions_sha256"):
            if lhs.get(field) != rhs.get(field):
                raise RuntimeError(f"B/L code identity mismatch: {field}")
    section = receipt.get("section", {})
    if section.get("segment") != SECTION_SEGMENT or \
            section.get("name") != SECTION_NAME or \
            section.get("flags") != SECTION_FLAGS or \
            section.get("alignment_power") != SECTION_ALIGNMENT_POWER or \
            section.get("executable_pure_instructions") is not True or \
            int(section.get("address", "-1"), 16) != int(
                ordered_addresses[names()[0]], 16):
        raise RuntimeError("four-body section identity mismatch")
    body = sum(facts[name]["size_bytes"] for name in names())
    if receipt.get("body_bytes") != body or \
            receipt.get("padding_bytes") != section.get("size_bytes") - body or \
            receipt.get("no_deduplicate_flag") != NO_DEDUPLICATE_FLAG:
        raise RuntimeError("four-body body/padding/no-deduplicate mismatch")
    for field in ("binary_bytes", "binary_sha256", "linker_map_bytes",
                  "linker_map_sha256", "linker_map_extract_sha256"):
        if field not in receipt:
            raise RuntimeError(f"four-body receipt missing {field}")
