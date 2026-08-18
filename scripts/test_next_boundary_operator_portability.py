#!/usr/bin/env python3
"""Untimed unit checks for next-boundary free-memory preflight portability."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
OPERATOR_PATH = ROOT / "scripts" / "run_next_boundary_experiments.py"
SPEC = importlib.util.spec_from_file_location("next_boundary_operator", OPERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
OPERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OPERATOR)


VM_STAT = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               100.
Pages active:                             999.
Pages inactive:                           200.
Pages speculative:                          3.
Pages purgeable:                           50.
"""


def main() -> int:
    assert OPERATOR.parse_vm_stat_available_bytes(VM_STAT) == 303 * 16384
    for malformed in ("", "Pages free: 1.",
                      "Mach Virtual Memory Statistics: (page size of 0 bytes)\n"):
        try:
            OPERATOR.parse_vm_stat_available_bytes(malformed)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed vm_stat output was accepted")

    with mock.patch.object(OPERATOR.os, "sysconf", side_effect=(123, 4096)):
        assert OPERATOR.available_memory_bytes() == 123 * 4096

    completed = subprocess.CompletedProcess(["vm_stat"], 0, VM_STAT, "")
    with mock.patch.object(OPERATOR.os, "sysconf",
                           side_effect=ValueError("unsupported")), \
         mock.patch.object(OPERATOR.platform, "system", return_value="Darwin"), \
         mock.patch.object(OPERATOR.subprocess, "run", return_value=completed):
        assert OPERATOR.available_memory_bytes() == 303 * 16384

    failed = subprocess.CompletedProcess(["vm_stat"], 1, "failure", "")
    with mock.patch.object(OPERATOR.os, "sysconf",
                           side_effect=ValueError("unsupported")), \
         mock.patch.object(OPERATOR.platform, "system", return_value="Darwin"), \
         mock.patch.object(OPERATOR.subprocess, "run", return_value=failed):
        try:
            OPERATOR.available_memory_bytes()
        except SystemExit as error:
            assert "free-memory prerequisite unavailable" in str(error)
        else:
            raise AssertionError("failed vm_stat did not fail closed")

    with mock.patch.object(OPERATOR.os, "sysconf",
                           side_effect=ValueError("unsupported")), \
         mock.patch.object(OPERATOR.platform, "system", return_value="Linux"):
        try:
            OPERATOR.available_memory_bytes()
        except SystemExit as error:
            assert "free-memory prerequisite unavailable" in str(error)
        else:
            raise AssertionError("unsupported non-Darwin sysconf did not fail closed")

    print("PASS: next-boundary free-memory preflight portability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
