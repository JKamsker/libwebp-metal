#!/usr/bin/env python3
"""Untimed unit tests for v5 paths, repository-context admission, and sharing."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import backref_cost_workspace_remote_v5_admission as admission
import execute_backref_cost_workspace_remote_v5 as executor
from backref_cost_workspace_remote_v5_paths import (
    SAFE_ROOT_BASENAME, UnsafePath, cleanup, ensure_safe_root,
    validate_existing, validate_shape,
)


def rejected(function, *args) -> None:
    try:
        function(*args)
    except (OSError, RuntimeError, UnsafePath):
        return
    raise AssertionError(f"unsafe input accepted: {args}")


def path_tests() -> None:
    home = "/Users/pandocs-agent-001"
    root = f"{home}/{SAFE_ROOT_BASENAME}"
    run = f"{root}/run.A21KcK"
    assert validate_shape(home, root, run) == "run.A21KcK"
    rejected(validate_shape, home, root, f"{root}/run.bad")
    rejected(validate_shape, home, root,
             f"{home}/{SAFE_ROOT_BASENAME}-sibling/run.A21KcK")
    rejected(validate_shape, home, root, f"{root}/nested/run.A21KcK")
    rejected(validate_shape, home, root, f"{run}/../run.A21KcK")
    with tempfile.TemporaryDirectory(prefix="remote-v5-path-home-") as raw:
        actual_home = os.path.realpath(raw)
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = actual_home
        try:
            actual_root = ensure_safe_root(actual_home)
            actual_run = os.path.join(actual_root, "run.ABC123")
            os.mkdir(actual_run)
            assert validate_existing(actual_home, actual_root,
                                     actual_run)["validated"]
            symlink = os.path.join(actual_root, "run.SYM123")
            os.symlink(actual_run, symlink)
            rejected(validate_existing, actual_home, actual_root, symlink)
            os.unlink(symlink)
            proof = cleanup(actual_home, actual_root, actual_run)
            assert proof["absence_proved"] and not os.path.lexists(actual_run)
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


def repository_context_admission_tests() -> None:
    with tempfile.TemporaryDirectory(prefix="remote-v5-admit-test-") as raw:
        temporary = Path(os.path.realpath(raw))
        repository = temporary / "repository"
        repository.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name",
                        "v5 admission test"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email",
                        "v5-admission@example.invalid"], check=True)
        source = repository / "source.txt"
        source.write_text("exact source\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "add", "source.txt"],
                       check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-q", "-m",
                        "fixture"], check=True)
        commit = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "HEAD^{tree}"],
            text=True).strip()
        run_directory = temporary / "run.ABC123"
        run_directory.mkdir()
        bundle = run_directory / "source.bundle"
        subprocess.run(["git", "-C", str(repository), "bundle", "create",
                        str(bundle), "HEAD"], check=True)
        bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        result = admission.remote_admit(
            str(run_directory), "source.bundle", bundle_sha, commit, tree,
            {"source.txt": source_sha})
        assert result["bundle_verified_in_repository_context"]
        assert result["verification_repository_removed"]
        assert result["clean_status"] and result["source_tree"] == tree
        assert not (run_directory / "verify.git").exists()

        malformed = run_directory / "malformed.bundle"
        malformed.write_bytes(b"not a bundle\n")
        malformed_sha = hashlib.sha256(malformed.read_bytes()).hexdigest()
        rejected(admission.remote_admit, str(run_directory), "malformed.bundle",
                 malformed_sha, commit, tree, {"source.txt": source_sha})
        assert not (run_directory / "malformed-verify.git").exists()
        assert not (run_directory / "malformed-source").exists()


def shared_path_test() -> None:
    sentinel = {"shared": True}
    with mock.patch.object(executor.admission, "admit_source",
                           return_value=sentinel) as shared:
        assert executor.prepare_remote("admission-only") is sentinel
        assert executor.prepare_remote("run") is sentinel
    assert shared.call_args_list == [
        mock.call(exercise_malformed=True),
        mock.call(exercise_malformed=False),
    ]


def main() -> int:
    path_tests()
    repository_context_admission_tests()
    shared_path_test()
    print("PASS: v5 canonical paths, repository-context bundle verification, "
          "malformed rejection, cleanup, and shared admission implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
