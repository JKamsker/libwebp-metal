#!/usr/bin/env python3
"""Untimed tests for the frozen interval-attribution v8 indexed evidence archive protocol."""

from __future__ import annotations

import io
import json
import os
import tarfile
import tempfile
from pathlib import Path

import backref_cost_attribution_v8_archive as protocol


def make_index(root: Path) -> Path:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "artifact-hashes.json":
            rows.append({"path": path.relative_to(root).as_posix(),
                         "bytes": path.stat().st_size,
                         "sha256": protocol.sha256(path)})
    index = root / "artifact-hashes.json"
    protocol.write_json(index, {"schema": protocol.ARTIFACT_SCHEMA,
                                "artifacts": rows})
    return index


def malicious(path: Path, name: str, kind: bytes) -> None:
    with tarfile.open(path, "w:gz") as opened:
        safe = tarfile.TarInfo("evidence/safe.txt")
        safe.size = 4
        opened.addfile(safe, io.BytesIO(b"safe"))
        member = tarfile.TarInfo(name)
        member.type = kind
        if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            member.linkname = "../../outside"
        opened.addfile(member)
        tail = tarfile.TarInfo("evidence/tail.txt")
        tail.size = 4
        opened.addfile(tail, io.BytesIO(b"tail"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="attribution-v8-archive-test-") as raw:
        temporary = Path(os.path.realpath(raw))
        evidence = temporary / "evidence"
        (evidence / "nested" / "deeper").mkdir(parents=True)
        (evidence / "root.txt").write_text("root\n")
        (evidence / "nested" / "deeper" / "record.json").write_text(
            '{"status":"ok"}\n')
        index = make_index(evidence)
        archive = temporary / "evidence.tar.gz"
        inventory = temporary / "inventory.json"
        digest = temporary / "digest.json"
        record = protocol.build_archive(evidence, index, archive, inventory, digest)
        assert record["status"] == "accepted"
        assert record["compression_format"] == "tar+gzip"
        assert record["archive_bytes"] == archive.stat().st_size
        assert record["archive_sha256"] == protocol.sha256(archive)
        inspected = protocol.inspect_archive(archive)
        assert inspected == json.loads(inventory.read_text())
        assert [row["name"] for row in inspected["members"]] == [
            "evidence/nested", "evidence/nested/deeper",
            "evidence/artifact-hashes.json", "evidence/nested/deeper/record.json",
            "evidence/root.txt",
        ]
        extracted = temporary / "returned"
        protocol.extract_archive(archive, extracted)
        assert (extracted / "nested" / "deeper" / "record.json").read_text() == \
            '{"status":"ok"}\n'
        returned = protocol.write_returned_index(extracted, ["later.json"])
        assert returned["excluded_after_index"] == ["later.json"]
        protocol.verify_returned_index(
            extracted / "returned-evidence-hashes.json", extracted)

        archive_bytes = archive.read_bytes()
        for label, value in (
                ("truncated", archive_bytes[:len(archive_bytes) // 2]),
                ("corrupt", bytes([archive_bytes[0] ^ 1]) + archive_bytes[1:])):
            broken = temporary / f"{label}.tar.gz"
            broken.write_bytes(value)
            assert protocol.inspect_archive(broken)["status"] == "rejected"
            destination = temporary / f"broken-{label}"
            try:
                protocol.extract_archive(broken, destination)
                raise AssertionError(f"{label} archive was accepted")
            except protocol.ArchiveRefusal:
                pass
            assert not destination.exists()

        fixtures = (
            ("traversal", "evidence/../escape", tarfile.REGTYPE, "traversal"),
            ("absolute", "/evidence/escape", tarfile.REGTYPE, "absolute"),
            ("symlink", "evidence/link", tarfile.SYMTYPE, "symlink"),
            ("hardlink", "evidence/hard", tarfile.LNKTYPE, "hardlink"),
            ("fifo", "evidence/fifo", tarfile.FIFOTYPE, "nonregular"),
            ("appledouble", "evidence/._record", tarfile.REGTYPE, "AppleDouble"),
        )
        for label, name, kind, reason in fixtures:
            fixture = temporary / f"{label}.tar.gz"
            malicious(fixture, name, kind)
            observed = protocol.inspect_archive(fixture)
            assert observed["status"] == "rejected"
            assert observed["member_count"] == 3
            assert observed["offending"]["member"] == name
            assert reason in observed["offending"]["reason"]
            refused = temporary / f"refused-{label}"
            try:
                protocol.extract_archive(fixture, refused)
                raise AssertionError(f"{label} archive was accepted")
            except protocol.ArchiveRefusal:
                pass
            assert not refused.exists()

        pax = temporary / "pax-xattr.tar.gz"
        with tarfile.open(pax, "w:gz", format=tarfile.PAX_FORMAT) as opened:
            member = tarfile.TarInfo("evidence/record")
            member.size = 1
            member.pax_headers = {"SCHILY.xattr.user.test": "value"}
            opened.addfile(member, io.BytesIO(b"x"))
        observed = protocol.inspect_archive(pax)
        assert observed["status"] == "rejected"
        assert "PAX" in observed["offending"]["reason"]

        for label in ("symlink", "hardlink", "fifo"):
            bad = temporary / f"builder-{label}"
            bad.mkdir()
            regular = bad / "record"
            regular.write_text("x")
            if label == "symlink":
                (bad / "bad").symlink_to(regular)
            elif label == "hardlink":
                os.link(regular, bad / "bad")
            else:
                os.mkfifo(bad / "bad")
            try:
                make_index(bad)
                protocol.load_artifact_index(bad, bad / "artifact-hashes.json")
                raise AssertionError(f"builder accepted {label}")
            except (protocol.ArchiveRefusal, OSError):
                pass

    print("PASS: indexed builder/extractor, normalized ordering, full inventory, "
          "hash verification, no-partial extraction, and malicious rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
