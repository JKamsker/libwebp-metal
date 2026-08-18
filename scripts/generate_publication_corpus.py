#!/usr/bin/env python3
"""Generate and verify the redistributable publication corpus.

The image bytes depend only on the constants and integer operations in this
file.  They do not depend on Python's random module, host endianness, locale,
clock, filesystem path, or any external image asset.

The generator source digest is calculated after normalizing Git's Windows
line endings so the canonical manifest verifies on every supported platform.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA = "libwebp-publication-corpus-manifest-v1"
CORPUS_VERSION = 1
GENERATOR_VERSION = 1
GENERATOR_SEED = 0x9E3779B9
FORMAT = "binary PPM (P6), opaque 8-bit RGB"
SIZES = (
    ("small", 512, 512),
    ("medium", 1600, 1200),
    ("large", 3000, 2000),
)
CATEGORIES = (
    ("photo", "smooth gradients, bounded coordinate noise, and broad color variation"),
    ("graphic", "six-color blocks with strong horizontal and vertical edges"),
    ("texture", "high-frequency deterministic xorshift32 samples"),
)
ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MANIFEST = ROOT / "benchmarks" / "publication-corpus" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_source(path: Path) -> str:
    """Hash source text independently of the checkout's line-ending policy."""
    source = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(source).hexdigest()


def ppm_row(category: str, width: int, height: int, y: int) -> bytearray:
    row = bytearray(width * 3)
    state = (GENERATOR_SEED ^ (y * 0x85EBCA6B)) & 0xFFFFFFFF
    for x in range(width):
        if category == "photo":
            noise = ((x * 17 + y * 29 + ((x ^ y) * 7)) & 31) - 16
            red = max(0, min(255, (180 * x // max(1, width - 1)) + 35 + noise))
            green = max(
                0,
                min(255, (150 * y // max(1, height - 1)) + 45 + noise // 2),
            )
            blue = max(
                0,
                min(255, (red + green) // 2 + ((x // 64 + y // 64) & 15)),
            )
        elif category == "graphic":
            palette = (
                (238, 238, 232),
                (38, 62, 96),
                (225, 82, 65),
                (247, 190, 66),
                (50, 150, 105),
                (103, 78, 167),
            )
            index = (
                (x // max(8, width // 12))
                + 3 * (y // max(8, height // 9))
            ) % len(palette)
            if (
                abs(x - width // 2) < max(2, width // 150)
                or abs(y - height // 2) < max(2, height // 150)
            ):
                index = 1
            red, green, blue = palette[index]
        elif category == "texture":
            state ^= (state << 13) & 0xFFFFFFFF
            state ^= state >> 17
            state ^= (state << 5) & 0xFFFFFFFF
            red = state & 255
            green = (state >> 8) & 255
            blue = (state >> 16) & 255
        else:
            raise ValueError(f"unknown category: {category}")
        offset = 3 * x
        row[offset : offset + 3] = bytes((red, green, blue))
    return row


def write_case(path: Path, category: str, width: int, height: int) -> None:
    with path.open("wb") as output:
        output.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        for y in range(height):
            output.write(ppm_row(category, width, height, y))


def manifest_for(output: Path) -> dict[str, object]:
    cases = []
    for size_class, width, height in SIZES:
        for category, _ in CATEGORIES:
            case_id = f"{category}-{size_class}"
            path = output / f"{case_id}.ppm"
            cases.append(
                {
                    "bytes": path.stat().st_size,
                    "case_id": case_id,
                    "category": category,
                    "file": path.name,
                    "height": height,
                    "pixels": width * height,
                    "sha256": sha256(path),
                    "size_class": size_class,
                    "width": width,
                }
            )
    return {
        "schema": SCHEMA,
        "corpus_version": CORPUS_VERSION,
        "generator": {
            "algorithm": "integer formulas defined entirely in generator source",
            "seed": GENERATOR_SEED,
            "seed_hex": f"0x{GENERATOR_SEED:08x}",
            "source": "scripts/generate_publication_corpus.py",
            "source_sha256": sha256_source(Path(__file__).resolve()),
            "version": GENERATOR_VERSION,
        },
        "format": FORMAT,
        "categories": [
            {"id": category, "description": description}
            for category, description in CATEGORIES
        ],
        "license": {
            "spdx": "BSD-3-Clause",
            "file": "COPYING",
            "scope": "generator source, manifest, and generated PPM bytes",
            "third_party_media": False,
        },
        "provenance": (
            "Repository-generated synthetic pixels; no external or embedded "
            "image media, model output, network input, or runtime randomness."
        ),
        "total_generated_bytes": sum(case["bytes"] for case in cases),
        "cases": cases,
    }


def generate(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    for size_class, width, height in SIZES:
        for category, _ in CATEGORIES:
            write_case(
                output / f"{category}-{size_class}.ppm",
                category,
                width,
                height,
            )
    manifest = manifest_for(output)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify(manifest: dict[str, object], expected_path: Path) -> None:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    if manifest != expected:
        raise SystemExit(
            f"generated manifest does not match canonical manifest: {expected_path}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--verify",
        nargs="?",
        const=CANONICAL_MANIFEST,
        type=Path,
        help="compare generated schema, metadata, dimensions, sizes, and hashes",
    )
    args = parser.parse_args()
    manifest = generate(args.output)
    if args.verify:
        verify(manifest, args.verify)
        print(f"PASS: publication corpus matches {args.verify}")
    else:
        print(args.output / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
