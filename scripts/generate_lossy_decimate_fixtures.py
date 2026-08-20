#!/usr/bin/env python3
"""Generate CPU-golden, versioned lossy-decimate conformance fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def safe_name(path: Path) -> str:
    result = "".join(c if c.isalnum() or c in "-_" else "-" for c in path.stem)
    return result.strip("-") or "input"


def write_synthetic_ppm(path: Path, width: int, height: int, pattern: str) -> None:
    with path.open("wb") as output:
        output.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        for y in range(height):
            row = bytearray(width * 3)
            for x in range(width):
                if pattern == "tie-flat":
                    red = green = blue = 128
                else:
                    value = 255 if ((x // 2) ^ (y // 2)) & 1 else 0
                    red = value
                    green = 255 - value
                    blue = value
                row[3 * x : 3 * x + 3] = bytes((red, green, blue))
            output.write(row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwebp", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--methods", default="3,4,5,6")
    parser.add_argument("--qualities", default="25,75,98")
    parser.add_argument(
        "--include-synthetic",
        action="store_true",
        help="add deterministic flat tie and coefficient-extreme edge cases",
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    methods = [int(value) for value in args.methods.split(",")]
    qualities = [int(value) for value in args.qualities.split(",")]
    if any(value < 3 or value > 6 for value in methods):
        parser.error("lossy-decimate fixtures require methods in 3..6")
    if any(value < 0 or value > 100 for value in qualities):
        parser.error("qualities must be in 0..100")
    if len(set(methods)) != len(methods) or len(set(qualities)) != len(qualities):
        parser.error("methods and qualities must not contain duplicates")
    cwebp = args.cwebp.resolve(strict=True)
    inputs = [(path.resolve(strict=True), str(path.resolve())) for path in args.inputs]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="libwebp-decimate-fixtures-") as temp:
        temp_dir = Path(temp)
        if args.include_synthetic:
            synthetic = (
                ("tie-flat-33x31.ppm", 33, 31, "tie-flat"),
                ("coefficient-extreme-257x255.ppm", 257, 255, "extreme"),
            )
            for name, width, height, pattern in synthetic:
                path = temp_dir / name
                write_synthetic_ppm(path, width, height, pattern)
                inputs.append((path, f"generated:{name}"))
        input_names = [safe_name(path) for path, _ in inputs]
        if len(set(input_names)) != len(input_names):
            raise SystemExit("input basenames must be unique after sanitization")
        for input_path, input_label in inputs:
            for method in methods:
                for quality in qualities:
                    stem = f"{safe_name(input_path)}-m{method}-q{quality}"
                    fixture = output_dir / f"{stem}.wpd"
                    encoded = temp_dir / f"{stem}.webp"
                    fixture.unlink(missing_ok=True)
                    environment = os.environ.copy()
                    environment.update(
                        {
                            "WEBP_ACCELERATOR": "none",
                            "WEBP_CUDA": "0",
                            "WEBP_DECIMATE_FIXTURE_PATH": str(fixture),
                        }
                    )
                    command = [
                        str(cwebp),
                        "-quiet",
                        "-m",
                        str(method),
                        "-q",
                        str(quality),
                        "-pass",
                        "1",
                        str(input_path),
                        "-o",
                        str(encoded),
                    ]
                    completed = subprocess.run(
                        command,
                        env=environment,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                    )
                    if completed.returncode != 0 or not fixture.is_file():
                        raise SystemExit(
                            f"fixture generation failed for {stem}: "
                            f"{completed.stderr.strip()}"
                        )
                    records.append(
                        {
                            "fixture": fixture.name,
                            "fixture_sha256": digest(fixture),
                            "input": input_label,
                            "input_sha256": digest(input_path),
                            "method": method,
                            "quality": quality,
                            "encoded_bytes": encoded.stat().st_size,
                            "encoded_sha256": digest(encoded),
                        }
                    )
    manifest = {
        "schema": "webp-lossy-decimate-fixture-manifest",
        "version": 1,
        "generator": "generate_lossy_decimate_fixtures.py",
        "fixtures": records,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"fixtures": len(records), "manifest": str(manifest_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
