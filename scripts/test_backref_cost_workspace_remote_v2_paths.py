#!/usr/bin/env python3
"""Deterministic untimed tests for the exact remote v2 path guard."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from backref_cost_workspace_remote_v2_paths import (
    SAFE_ROOT_BASENAME,
    UnsafePath,
    cleanup,
    ensure_safe_root,
    validate_existing,
    validate_shape,
)


def rejected(function, *args) -> None:
    try:
        function(*args)
    except (OSError, UnsafePath):
        return
    raise AssertionError(f"unsafe path accepted: {args}")


def real_users_style_shape_tests() -> None:
    home = "/Users/pandocs-agent-001"
    root = f"{home}/{SAFE_ROOT_BASENAME}"
    run = f"{root}/run.A21KcK"
    assert validate_shape(home, root, run) == "run.A21KcK"
    rejected(validate_shape, home, root, f"{root}/run.bad")
    rejected(validate_shape, home, root, f"{home}/{SAFE_ROOT_BASENAME}-x/run.A21KcK")
    rejected(validate_shape, home, root, f"{root}/nested/run.A21KcK")
    rejected(validate_shape, home, root, f"{run}/../run.A21KcK")
    rejected(validate_shape, home, root, f"{root}//run.A21KcK")


def filesystem_tests() -> None:
    with tempfile.TemporaryDirectory(prefix="remote-v2-path-home-") as raw:
        home = os.path.realpath(raw)
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = home
        try:
            root = ensure_safe_root(home)
            run = os.path.join(root, "run.ABC123")
            os.mkdir(run)
            assert validate_existing(home, root, run)["validated"]
            symlink = os.path.join(root, "run.SYM123")
            os.symlink(run, symlink)
            rejected(validate_existing, home, root, symlink)
            os.unlink(symlink)
            result = cleanup(home, root, run)
            assert result["absence_proved"] and not os.path.lexists(run)
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


def main() -> int:
    real_users_style_shape_tests()
    filesystem_tests()
    print("PASS: real /Users-style shape, canonical root, symlink, traversal, "
          "exact-child cleanup, and absence checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
