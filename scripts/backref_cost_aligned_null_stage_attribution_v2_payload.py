#!/usr/bin/env python3
"""Canonical deterministic stage-attribution-v2 payload generator."""

from __future__ import annotations

import argparse
import hashlib
import json


DOMAIN = b"libwebp-backref-cost-aligned-null-stage-attribution-v2-rehearsal\x00"
DOMAIN_TEXT = "libwebp-backref-cost-aligned-null-stage-attribution-v2-rehearsal\\0"
PAYLOAD_BYTES = 2 * 1024 * 1024
IO_CHUNK_BYTES = 64 * 1024
STALE_V2_SHA256 = \
    "68358e6f43afbbd3d983f89185dd0da7694a65e5cbc8f31bdc8ef2102b1dc6d0"
STALE_V3_SHA256 = \
    "8fb97e16b8be09e7dc0c20b0b26387a0f8301d0aa738fa7ade4a6a97d15afeb8"
STALE_V4_SHA256 = \
    "d34b944ec0b8eead809367d456785cf37d325459bca34506bec74af5efba4db0"
STALE_ALIGNMENT_V1_SHA256 = \
    "6d464de5123e056c63990cbcfda55cd6c68d5a70434fd340704fb5fa054f2eb3"
STALE_ALIGNMENT_V2_SHA256 = \
    "2e2ea6d7479bc385057e7a55154e220e67d28e7861c8b54fae5ea8549bbca607"
STALE_ALIGNMENT_V3_SHA256 = \
    "25309a36ead04a05c8169e7cdc40a5ac8f47d406819c322461f6006cc1cd6845"


def chunks(size: int = PAYLOAD_BYTES, chunk_bytes: int = IO_CHUNK_BYTES):
    if size < 0 or chunk_bytes < 1:
        raise ValueError("deterministic payload bounds are invalid")
    counter = 0
    remaining = size
    pending = bytearray()
    while remaining:
        while len(pending) < min(chunk_bytes, remaining):
            pending.extend(hashlib.sha256(
                DOMAIN + counter.to_bytes(8, "big")).digest())
            counter += 1
        length = min(chunk_bytes, remaining)
        yield bytes(pending[:length])
        del pending[:length]
        remaining -= length


def sha256(size: int = PAYLOAD_BYTES) -> str:
    digest = hashlib.sha256()
    for chunk in chunks(size):
        digest.update(chunk)
    return digest.hexdigest()


def identity() -> dict[str, object]:
    digest = sha256()
    return {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-payload-identity-v1",
        "algorithm": "sha256(domain || uint64_be(counter)) concatenation truncated to payload bytes",
        "domain": DOMAIN_TEXT,
        "payload_bytes": PAYLOAD_BYTES,
        "sha256": digest,
        "stale_v2_sha256": STALE_V2_SHA256,
        "stale_v3_sha256": STALE_V3_SHA256,
        "stale_v4_sha256": STALE_V4_SHA256,
        "stale_alignment_v1_sha256": STALE_ALIGNMENT_V1_SHA256,
        "stale_alignment_v2_sha256": STALE_ALIGNMENT_V2_SHA256,
        "stale_alignment_v3_sha256": STALE_ALIGNMENT_V3_SHA256,
        "stale_v2_rejected": digest != STALE_V2_SHA256,
        "stale_v3_rejected": digest != STALE_V3_SHA256,
        "stale_v4_rejected": digest != STALE_V4_SHA256,
        "stale_alignment_v1_rejected": digest != STALE_ALIGNMENT_V1_SHA256,
        "stale_alignment_v2_rejected": digest != STALE_ALIGNMENT_V2_SHA256,
        "stale_alignment_v3_rejected": digest != STALE_ALIGNMENT_V3_SHA256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", action="store_true")
    args = parser.parse_args()
    if args.identity:
        print(json.dumps(identity(), sort_keys=True))
    else:
        for chunk in chunks():
            print(chunk.hex(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
