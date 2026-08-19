#!/usr/bin/env python3
"""Exact specialization-factorization-v4 run-directory generator, validator, and cleanup guard."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys


SAFE_ROOT_BASENAME = ".libwebp-metal-backref-cost-specialization-factorization-v4"
RUN_TOKEN = re.compile(r"run\.[A-Za-z0-9]{6}")


class UnsafePath(ValueError):
    pass


def canonical_remote_home() -> str:
    raw = os.environ.get("HOME", "")
    if not raw or not os.path.isabs(raw):
        raise UnsafePath("remote HOME must be absolute")
    canonical = os.path.realpath(raw)
    if canonical != raw.rstrip("/") or canonical == "/":
        raise UnsafePath("remote HOME must already be canonical and non-root")
    info = os.lstat(canonical)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafePath("remote HOME must be a real directory")
    return canonical


def expected_safe_root(home: str) -> str:
    return os.path.join(home, SAFE_ROOT_BASENAME)


def validate_shape(home: str, safe_root: str, candidate: str) -> str:
    if not all(os.path.isabs(value) for value in (home, safe_root, candidate)):
        raise UnsafePath("HOME, safe root, and run path must be absolute")
    expected_root = expected_safe_root(home)
    if safe_root != expected_root:
        raise UnsafePath("safe root is not the exact child of canonical HOME")
    token = os.path.basename(candidate)
    if RUN_TOKEN.fullmatch(token) is None:
        raise UnsafePath("run basename is not a strict run.XXXXXX token")
    expected_candidate = os.path.join(safe_root, token)
    if candidate != expected_candidate or os.path.dirname(candidate) != safe_root:
        raise UnsafePath("run path is not the exact safe-root child")
    if os.path.commonpath((safe_root, candidate)) != safe_root:
        raise UnsafePath("run path escapes the safe root")
    return token


def ensure_safe_root(home: str) -> str:
    actual_home = canonical_remote_home()
    if home != actual_home:
        raise UnsafePath("supplied HOME does not match execution-time HOME")
    safe_root = expected_safe_root(home)
    try:
        os.mkdir(safe_root, 0o700)
    except FileExistsError:
        pass
    info = os.lstat(safe_root)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafePath("safe root must be a real directory")
    if os.path.realpath(safe_root) != safe_root:
        raise UnsafePath("safe root is not canonical")
    if os.path.dirname(safe_root) != home:
        raise UnsafePath("safe root is not directly beneath HOME")
    return safe_root


def validate_existing(home: str, safe_root: str, candidate: str) -> dict:
    token = validate_shape(home, safe_root, candidate)
    actual_root = ensure_safe_root(home)
    if safe_root != actual_root:
        raise UnsafePath("safe-root identity changed")
    info = os.lstat(candidate)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafePath("run path must be a real directory, not a symlink")
    canonical = os.path.realpath(candidate)
    if canonical != candidate or os.path.dirname(canonical) != safe_root:
        raise UnsafePath("canonical run path is not the exact safe-root child")
    return {"home": home, "safe_root": safe_root, "run_directory": candidate,
            "token": token, "validated": True}


def generate() -> dict:
    home = canonical_remote_home()
    safe_root = ensure_safe_root(home)
    result = subprocess.run(
        ["mktemp", "-d", os.path.join(safe_root, "run.XXXXXX")],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise UnsafePath(f"mktemp -d failed: {result.stderr.strip()}")
    candidate = result.stdout.strip()
    record = validate_existing(home, safe_root, candidate)
    record["generator"] = "mktemp -d"
    return record


def cleanup(home: str, safe_root: str, candidate: str) -> dict:
    record = validate_existing(home, safe_root, candidate)
    shutil.rmtree(candidate)
    absent = not os.path.lexists(candidate)
    if not absent:
        raise UnsafePath("validated run directory remains after cleanup")
    return {**record, "removed_exact_validated_child": True,
            "absence_proved": True}


def expect_rejected(home: str, safe_root: str, candidate: str) -> str:
    try:
        validate_existing(home, safe_root, candidate)
    except (OSError, UnsafePath) as error:
        return str(error)
    raise UnsafePath(f"unsafe fixture was accepted: {candidate}")


def round_trip() -> dict:
    generated = generate()
    home = generated["home"]
    safe_root = generated["safe_root"]
    candidate = generated["run_directory"]
    token = generated["token"]
    nested_symlink = os.path.join(candidate, "run.SYM123")
    os.symlink(candidate, nested_symlink)
    rejected = {
        "malformed": expect_rejected(home, safe_root,
                                     os.path.join(safe_root, "run.bad")),
        "sibling": expect_rejected(
            home, safe_root,
            os.path.join(home, SAFE_ROOT_BASENAME + "-sibling", token)),
        "symlink": expect_rejected(home, safe_root, nested_symlink),
        "traversal": expect_rejected(
            home, safe_root, os.path.join(candidate, "..", token)),
    }
    accepted = validate_existing(home, safe_root, candidate)
    cleaned = cleanup(home, safe_root, candidate)
    return {"schema": "libwebp-backref-cost-specialization-factorization-v4-path-round-trip-v1",
            "accepted": accepted, "rejected": rejected, "cleanup": cleaned}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    sub.add_parser("round-trip")
    for name in ("validate", "cleanup"):
        child = sub.add_parser(name)
        child.add_argument("home")
        child.add_argument("safe_root")
        child.add_argument("run_directory")
    args = parser.parse_args()
    try:
        if args.command == "generate":
            value = generate()
        elif args.command == "round-trip":
            value = round_trip()
        elif args.command == "validate":
            value = validate_existing(args.home, args.safe_root,
                                      args.run_directory)
        else:
            value = cleanup(args.home, args.safe_root, args.run_directory)
        print(json.dumps(value, sort_keys=True))
        return 0
    except (OSError, UnsafePath, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
