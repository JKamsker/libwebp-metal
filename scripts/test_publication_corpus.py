#!/usr/bin/env python3
"""Untimed determinism, hash, schema, provenance, and license checks."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import generate_publication_corpus as corpus


def main() -> int:
    expected = json.loads(corpus.CANONICAL_MANIFEST.read_text(encoding="utf-8"))
    assert expected["schema"] == corpus.SCHEMA
    assert expected["corpus_version"] == corpus.CORPUS_VERSION
    assert expected["generator"]["version"] == corpus.GENERATOR_VERSION
    assert expected["generator"]["seed"] == corpus.GENERATOR_SEED
    assert expected["generator"]["source_sha256"] == corpus.sha256(
        Path(corpus.__file__)
    )
    assert expected["license"] == {
        "file": "COPYING",
        "scope": "generator source, manifest, and generated PPM bytes",
        "spdx": "BSD-3-Clause",
        "third_party_media": False,
    }
    assert (corpus.ROOT / expected["license"]["file"]).is_file()
    assert "no external or embedded image media" in expected["provenance"]
    assert {case["category"] for case in expected["cases"]} == {
        "photo",
        "graphic",
        "texture",
    }
    assert len(expected["cases"]) == 9
    assert len({case["case_id"] for case in expected["cases"]}) == 9
    assert expected["total_generated_bytes"] == sum(
        case["bytes"] for case in expected["cases"]
    )
    assert not any("path" in case for case in expected["cases"])

    historical = json.loads(
        (corpus.ROOT / "profile-data" / "dataset" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    historical_cases = {
        case["case_id"]: (
            case["width"],
            case["height"],
            case["sha256"],
        )
        for case in historical["cases"]
    }
    canonical_cases = {
        case["case_id"]: (
            case["width"],
            case["height"],
            case["sha256"],
        )
        for case in expected["cases"]
    }
    assert canonical_cases == historical_cases

    with tempfile.TemporaryDirectory(prefix="libwebp-publication-corpus-") as tmp:
        root = Path(tmp)
        first = corpus.generate(root / "first")
        second = corpus.generate(root / "second")
        assert first == second == expected
        assert (root / "first" / "manifest.json").read_bytes() == (
            root / "second" / "manifest.json"
        ).read_bytes()
        for case in expected["cases"]:
            first_path = root / "first" / case["file"]
            second_path = root / "second" / case["file"]
            assert first_path.read_bytes() == second_path.read_bytes()
            assert corpus.sha256(first_path) == case["sha256"]
            assert first_path.stat().st_size == case["bytes"]

    print(
        "PASS: publication corpus schema/license/provenance and two-generation "
        "byte determinism"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
