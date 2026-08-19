#!/usr/bin/env python3
"""Frozen attribution-v12 indexed archive builder and extractor."""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import json
import os
import posixpath
import shutil
import stat
import tarfile
from pathlib import Path, PurePosixPath


ARCHIVE_SCHEMA = "libwebp-backref-cost-attribution-v12-archive-v1"
INVENTORY_SCHEMA = "libwebp-backref-cost-attribution-v12-archive-inventory-v1"
ARTIFACT_SCHEMA = "libwebp-backref-cost-attribution-v12-artifact-hashes-v1"
RETURNED_SCHEMA = (
    "libwebp-backref-cost-attribution-v12-returned-evidence-hashes-v1")
CHUNK = 1024 * 1024


class ArchiveRefusal(RuntimeError):
    def __init__(self, member: str, reason: str):
        super().__init__(f"{member}: {reason}")
        self.member = member
        self.reason = reason


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _safe_relative(raw: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\0" in raw:
        raise ArchiveRefusal(str(raw), "name is empty or not normalized POSIX")
    name = PurePosixPath(raw)
    if name.is_absolute() or raw.startswith("/"):
        raise ArchiveRefusal(raw, "absolute path")
    if any(part in ("", ".", "..") for part in name.parts):
        raise ArchiveRefusal(raw, "traversal or non-normalized component")
    if any(part == "__MACOSX" or part.startswith("._") for part in name.parts):
        raise ArchiveRefusal(raw, "AppleDouble metadata member")
    normalized = posixpath.normpath(raw)
    if normalized != raw or str(name) != raw:
        raise ArchiveRefusal(raw, "non-normalized member name")
    return name


def _contained(root: Path, relative: PurePosixPath) -> Path:
    target = root.joinpath(*relative.parts)
    canonical = Path(os.path.realpath(target))
    if os.path.commonpath((str(root), str(canonical))) != str(root):
        raise ArchiveRefusal(str(relative), "canonical containment escape")
    return target


def _regular(path: Path, name: str) -> os.stat_result:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        raise ArchiveRefusal(name, "symlink")
    if not stat.S_ISREG(info.st_mode):
        kind = "directory" if stat.S_ISDIR(info.st_mode) else "nonregular file"
        raise ArchiveRefusal(name, kind)
    if info.st_nlink != 1:
        raise ArchiveRefusal(name, "hardlinked regular file")
    if hasattr(os, "listxattr") and os.listxattr(path, follow_symlinks=False):
        raise ArchiveRefusal(name, "extended attributes")
    return info


def load_artifact_index(root: Path, index: Path) -> list[dict]:
    supplied_root = root
    root = Path(os.path.realpath(root))
    root_info = os.lstat(supplied_root)
    if (not supplied_root.is_absolute() or supplied_root != root or
            stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode)):
        raise ArchiveRefusal(str(supplied_root),
                             "evidence root is not an absolute canonical directory")
    if Path(os.path.realpath(index.parent)) != root:
        raise ArchiveRefusal(str(index), "artifact index is not directly in root")
    _regular(index, index.name)
    value = json.loads(index.read_text(encoding="utf-8"))
    if value.get("schema") != ARTIFACT_SCHEMA:
        raise ArchiveRefusal(index.name, "artifact index schema mismatch")
    rows = value.get("artifacts")
    if not isinstance(rows, list):
        raise ArchiveRefusal(index.name, "artifact list is absent")
    prior = ""
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ArchiveRefusal(index.name, "artifact row is not an object")
        name = row.get("path")
        relative = _safe_relative(name)
        if name == index.name or name in seen or name <= prior:
            raise ArchiveRefusal(name, "artifact list is duplicate or unordered")
        path = _contained(root, relative)
        info = _regular(path, name)
        if info.st_size != row.get("bytes") or sha256(path) != row.get("sha256"):
            raise ArchiveRefusal(name, "artifact size or SHA-256 mismatch")
        prior = name
        seen.add(name)
    actual: set[str] = set()
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for child in sorted(directories + files):
            path = current_path / child
            relative = path.relative_to(root).as_posix()
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                raise ArchiveRefusal(relative, "symlink in evidence tree")
            if stat.S_ISDIR(info.st_mode):
                if hasattr(os, "listxattr") and os.listxattr(
                        path, follow_symlinks=False):
                    raise ArchiveRefusal(relative, "directory extended attributes")
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ArchiveRefusal(relative, "nonregular file in evidence tree")
            if info.st_nlink != 1:
                raise ArchiveRefusal(relative, "hardlinked file in evidence tree")
            actual.add(relative)
    expected = seen | {index.name}
    if actual != expected:
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        name = (extra or missing or [index.name])[0]
        raise ArchiveRefusal(name, "artifact index/tree membership mismatch")
    return rows


def _tar_info(name: str, *, directory: bool, size: int = 0) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name + ("/" if directory else ""))
    info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
    info.size = 0 if directory else size
    info.mode = 0o755 if directory else 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info


def build_archive(root: Path, index: Path, archive: Path,
                  inventory_path: Path, digest_path: Path) -> dict:
    rows = load_artifact_index(root, index)
    root = Path(os.path.realpath(root))
    files = [index.name, *(row["path"] for row in rows)]
    directories = sorted({
        PurePosixPath(*PurePosixPath(name).parts[:depth]).as_posix()
        for name in files for depth in range(1, len(PurePosixPath(name).parts))
    })
    members: list[dict] = []
    with contextlib.ExitStack() as stack:
        raw_archive = stack.enter_context(archive.open("xb"))
        compressed = stack.enter_context(gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_archive, mtime=0))
        opened = stack.enter_context(tarfile.open(
            fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT))
        for name in directories:
            path = _contained(root, _safe_relative(name))
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise ArchiveRefusal(name, "indexed parent is not a real directory")
            if hasattr(os, "listxattr") and os.listxattr(
                    path, follow_symlinks=False):
                raise ArchiveRefusal(name, "directory extended attributes")
            opened.addfile(_tar_info(f"evidence/{name}", directory=True))
            members.append({"name": f"evidence/{name}", "type": "directory",
                            "size": 0})
        for name in files:
            path = _contained(root, _safe_relative(name))
            before = _regular(path, name)
            with path.open("rb") as source:
                opened.addfile(_tar_info(f"evidence/{name}", directory=False,
                                         size=before.st_size), source)
            after = os.lstat(path)
            if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
                raise ArchiveRefusal(name, "artifact changed while archived")
            members.append({"name": f"evidence/{name}", "type": "regular",
                            "size": before.st_size})
    digest = sha256(archive)
    inventory = {"schema": INVENTORY_SCHEMA, "status": "accepted",
                 "member_count": len(members), "members": members,
                 "offending": None}
    write_json(inventory_path, inventory)
    record = {"schema": ARCHIVE_SCHEMA, "status": "accepted",
              "compression_format": "tar+gzip",
              "archive_sha256": digest, "archive_bytes": archive.stat().st_size,
              "member_count": len(members),
              "inventory_sha256": sha256(inventory_path)}
    write_json(digest_path, record)
    return record


def inspect_archive(archive: Path) -> dict:
    members: list[dict] = []
    seen: set[str] = set()
    offending: dict | None = None
    try:
        with tarfile.open(archive, "r:gz") as opened:
            for member in opened.getmembers():
                kind = "directory" if member.isdir() else (
                    "regular" if member.isfile() else
                    "symlink" if member.issym() else
                    "hardlink" if member.islnk() else "nonregular")
                row = {"name": member.name, "type": kind, "size": member.size}
                members.append(row)
                try:
                    relative = _safe_relative(member.name)
                    if not relative.parts or relative.parts[0] != "evidence":
                        raise ArchiveRefusal(member.name, "member is outside evidence root")
                    if member.name in seen:
                        raise ArchiveRefusal(member.name, "duplicate member")
                    seen.add(member.name)
                    if not (member.isdir() or member.isfile()):
                        raise ArchiveRefusal(member.name, f"forbidden {kind} member")
                    if member.pax_headers:
                        raise ArchiveRefusal(member.name, "PAX or xattr metadata")
                    if member.isfile() and member.size < 0:
                        raise ArchiveRefusal(member.name, "negative regular-file size")
                except ArchiveRefusal as error:
                    if offending is None:
                        offending = {"member": error.member, "reason": error.reason}
    except (tarfile.TarError, OSError, EOFError) as error:
        if offending is None:
            offending = {"member": "<archive>", "reason": str(error)}
    return {"schema": INVENTORY_SCHEMA,
            "status": "rejected" if offending else "accepted",
            "member_count": len(members), "members": members,
            "offending": offending}


def extract_archive(archive: Path, destination: Path) -> dict:
    inventory = inspect_archive(archive)
    if inventory["status"] != "accepted":
        offending = inventory["offending"]
        raise ArchiveRefusal(offending["member"], offending["reason"])
    if os.path.lexists(destination):
        raise ArchiveRefusal(str(destination), "extraction destination exists")
    staging = destination.with_name(destination.name + ".extracting")
    if os.path.lexists(staging):
        raise ArchiveRefusal(str(staging), "extraction staging path exists")
    staging.mkdir(parents=True)
    staging = Path(os.path.realpath(staging))
    try:
        with tarfile.open(archive, "r:gz") as opened:
            for member in opened.getmembers():
                relative = _safe_relative(member.name)
                target = _contained(staging, relative)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = opened.extractfile(member)
                    if source is None:
                        raise ArchiveRefusal(member.name, "regular member unreadable")
                    with source, target.open("xb") as output:
                        shutil.copyfileobj(source, output, CHUNK)
        evidence = staging / "evidence"
        load_artifact_index(evidence, evidence / "artifact-hashes.json")
        evidence.rename(destination)
        staging.rmdir()
    except Exception:
        shutil.rmtree(staging)
        raise
    return inventory


def write_returned_index(output: Path, exclusions: list[str]) -> dict:
    rows = []
    excluded = set(exclusions) | {"returned-evidence-hashes.json"}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            relative = path.relative_to(output).as_posix()
            if relative not in excluded:
                _regular(path, relative)
                rows.append({"path": relative, "bytes": path.stat().st_size,
                             "sha256": sha256(path)})
    value = {"schema": RETURNED_SCHEMA, "artifacts": rows,
             "excluded_after_index": sorted(exclusions)}
    write_json(output / "returned-evidence-hashes.json", value)
    verify_returned_index(output / "returned-evidence-hashes.json", output)
    return value


def verify_returned_index(index: Path, output: Path) -> None:
    value = json.loads(index.read_text(encoding="utf-8"))
    if value.get("schema") != RETURNED_SCHEMA:
        raise ArchiveRefusal(index.name, "returned index schema mismatch")
    prior = ""
    listed: set[str] = set()
    for row in value.get("artifacts", []):
        name = row["path"]
        if name <= prior or name in listed:
            raise ArchiveRefusal(name, "returned index is unordered")
        path = _contained(Path(os.path.realpath(output)), _safe_relative(name))
        info = _regular(path, name)
        if info.st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise ArchiveRefusal(name, "returned artifact verification failed")
        prior = name
        listed.add(name)
    excluded = set(value.get("excluded_after_index", []))
    actual = {path.relative_to(output).as_posix()
              for path in output.rglob("*") if path.is_file()}
    expected = listed | {index.relative_to(output).as_posix()}
    observed = actual - excluded
    if observed != expected:
        name = sorted((observed - expected) | (expected - observed))[0]
        raise ArchiveRefusal(name, "returned index/tree membership mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    for name in ("root", "index", "archive", "inventory", "digest"):
        build.add_argument(name, type=Path)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("archive", type=Path)
    extract = sub.add_parser("extract")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)
    returned = sub.add_parser("returned-index")
    returned.add_argument("output", type=Path)
    returned.add_argument("--exclude", action="append", default=[])
    verify = sub.add_parser("verify-returned-index")
    verify.add_argument("index", type=Path)
    verify.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            value = build_archive(args.root, args.index, args.archive,
                                  args.inventory, args.digest)
        elif args.command == "inspect":
            value = inspect_archive(args.archive)
        elif args.command == "extract":
            value = extract_archive(args.archive, args.destination)
        elif args.command == "returned-index":
            value = write_returned_index(args.output, args.exclude)
        else:
            verify_returned_index(args.index, args.output)
            value = {"status": "accepted"}
        print(json.dumps(value, sort_keys=True))
        return 0
    except (ArchiveRefusal, OSError, ValueError, json.JSONDecodeError,
            tarfile.TarError, EOFError) as error:
        if isinstance(error, ArchiveRefusal):
            value = {"status": "rejected", "offending_member": error.member,
                     "reason": error.reason}
        else:
            value = {"status": "rejected", "offending_member": "<archive>",
                     "reason": str(error)}
        print(json.dumps(value, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
