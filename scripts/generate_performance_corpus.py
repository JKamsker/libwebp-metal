#!/usr/bin/env python3
"""Generate the deterministic, redistributable performance corpus."""

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA_VERSION = 1
WIDTH = 2560
HEIGHT = 1920


def write_ppm(path: Path, pattern: str) -> None:
    digest = hashlib.sha256()
    with path.open("wb") as output:
        header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
        output.write(header)
        digest.update(header)
        for y in range(HEIGHT):
            row = bytearray(WIDTH * 3)
            for x in range(WIDTH):
                if pattern == "smooth":
                    red = (x * 255) // (WIDTH - 1)
                    green = (y * 255) // (HEIGHT - 1)
                    blue = ((x // 32) * 17 + (y // 24) * 11) & 255
                else:
                    # Coordinate hashing is deterministic across Python and OS
                    # versions, unlike the implementation details of random.
                    value = (x + 0x9E3779B9 * (y + 1)) & 0xFFFFFFFF
                    value ^= value >> 16
                    value = (value * 0x7FEB352D) & 0xFFFFFFFF
                    value ^= value >> 15
                    value = (value * 0x846CA68B) & 0xFFFFFFFF
                    value ^= value >> 16
                    red = value & 255
                    green = (value >> 8) & 255
                    blue = (value >> 16) & 255
                offset = x * 3
                row[offset : offset + 3] = bytes((red, green, blue))
            output.write(row)
            digest.update(row)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    files = []
    for pattern in ("smooth", "texture"):
        path = args.output / f"{pattern}-{WIDTH}x{HEIGHT}.ppm"
        sha256 = write_ppm(path, pattern)
        files.append(
            {
                "name": path.name,
                "pattern": pattern,
                "width": WIDTH,
                "height": HEIGHT,
                "sha256": sha256,
                "bytes": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generator": Path(__file__).name,
        "files": files,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
