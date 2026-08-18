#!/usr/bin/env python3
"""Untimed v5 candidate identity, correctness, fallback, and omission checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "978e1b3e12e710c25f465fe1c8a68c359a38004e"
BUILD = "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT"
MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT"
FAULT = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT_INJECT_FAILURE"
V3_MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT"
V3_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT"
V4_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT"
RUNNER = "backref_cost_workspace_remote_v5_experiment_runner"
SOURCE = "backref_cost_workspace_remote_v5_experiment_enc.c"
MATRIX = (
    ("photo-small", 75), ("graphic-small", 75), ("texture-small", 75),
    ("photo-medium", 75), ("graphic-medium", 75), ("texture-medium", 75),
    ("photo-large", 75), ("graphic-large", 75), ("texture-large", 75),
    ("graphic-small", 24), ("graphic-small", 25),
    ("graphic-small", 26), ("graphic-small", 100),
)


def run(argv: list[str], *, env: dict[str, str] | None = None,
        input_text: str | None = None, check: bool = True,
        timeout: int = 1200) -> subprocess.CompletedProcess[str]:
    clean = os.environ.copy()
    for name in (RUNTIME, FAULT, V3_RUNTIME, V4_RUNTIME, "WEBP_BENCHMARK_SESSION",
                 "MallocNanoZone", "CUDA_VISIBLE_DEVICES"):
        clean.pop(name, None)
    if env:
        clean.update(env)
    result = subprocess.run(argv, cwd=ROOT, env=clean, input=input_text,
                            timeout=timeout, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {argv}\n{result.stdout}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(build: Path, *, candidate: bool,
              sanitizer: str | None = None) -> None:
    argv = ["cmake", "-S", ".", "-B", str(build),
            "-DWEBP_ENABLE_METAL=OFF", "-DBUILD_SHARED_LIBS=OFF",
            "-DWEBP_BUILD_EXTRAS=OFF", "-DWEBP_BUILD_CWEBP=ON",
            "-DWEBP_BUILD_DWEBP=ON", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    if candidate:
        argv.append(f"-D{BUILD}=ON")
    if sanitizer == "undefined":
        flags = ("-O1 -g -fno-omit-frame-pointer "
                 "-fsanitize=undefined,integer -fno-sanitize-recover=all")
        argv += [f"-DCMAKE_C_FLAGS={flags}",
                 "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=undefined,integer"]
    elif sanitizer == "bounds":
        flags = ("-O1 -g -fno-omit-frame-pointer "
                 "-fsanitize=array-bounds,pointer-overflow "
                 "-fno-sanitize-recover=all")
        argv += [f"-DCMAKE_C_FLAGS={flags}",
                 "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=array-bounds,pointer-overflow"]
    run(argv)


def build(directory: Path, *targets: str) -> None:
    run(["cmake", "--build", str(directory), "--target", *targets, "-j4"])


def encode(binary: Path, source: Path, output: Path, method: int, quality: int,
           env: dict[str, str] | None = None) -> None:
    run([str(binary), "-quiet", "-lossless", "-exact", "-q", str(quality),
         "-m", str(method), "-o", str(output), str(source)], env=env)


def equivalence() -> dict[str, str]:
    boundary = ROOT / "src/enc/backward_references_cost_enc.c"
    current = boundary.read_text(encoding="utf-8")
    compiler = os.environ.get("CC", "cc")

    def preprocess(macro: str) -> str:
        return run([compiler, "-E", "-P", f"-I{ROOT}", f"-D{macro}=1",
                    "-x", "c", "-"], input_text=current).stdout

    expected = preprocess(V3_MACRO)
    actual = preprocess(MACRO)
    actual = actual.replace("VP8LBackrefCostWorkspaceRemoteV5Experiment",
                            "VP8LBackrefCostWorkspaceRemoteV3Experiment")
    expected = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', expected)
    actual = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', actual)
    if actual != expected:
        raise AssertionError("v5 boundary differs from the frozen v3 candidate")
    v3 = (ROOT / "src/enc/backref_cost_workspace_remote_v3_experiment_enc.c").read_text()
    v5 = (ROOT / "src/enc/backref_cost_workspace_remote_v5_experiment_enc.c").read_text()
    v3 = v3[v3.index("static int EnvironmentIsOne"):]
    v5 = v5[v5.index("static int EnvironmentIsOne"):]
    v5 = v5.replace("RemoteV5", "RemoteV3").replace("REMOTE_V5", "REMOTE_V3")
    if v5 != v3:
        raise AssertionError("v5 helper behavior differs from frozen v3")
    return {
        "boundary_projection_sha256": hashlib.sha256(expected.encode()).hexdigest(),
        "normalized_helper_body_sha256": hashlib.sha256(v3.encode()).hexdigest(),
    }


def main() -> int:
    assert run(["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"]).returncode == 0
    projections = equivalence()
    runner_source = (ROOT / "tools" /
                     "backref_cost_workspace_remote_v5_experiment_runner.c").read_text()
    assert runner_source.index("session == NULL") < runner_source.index(
        "ReadPPM(input_path")
    assert "WEBP_BENCHMARK_SESSION=exclusive" in runner_source
    with tempfile.TemporaryDirectory(prefix="remote-v5-candidate-test-") as raw:
        temporary = Path(raw)
        baseline = temporary / "baseline"
        candidate = temporary / "candidate"
        corpus = temporary / "corpus"
        configure(baseline, candidate=False)
        configure(candidate, candidate=True)
        build(baseline, "cwebp", "dwebp")
        build(candidate, "cwebp", "dwebp", RUNNER)
        baseline_commands = (baseline / "compile_commands.json").read_text()
        candidate_commands = (candidate / "compile_commands.json").read_text()
        assert MACRO not in baseline_commands and SOURCE not in baseline_commands
        assert f"-D{MACRO}=1" in candidate_commands and SOURCE in candidate_commands
        absent = run(["cmake", "--build", str(baseline), "--target", RUNNER],
                     check=False)
        assert absent.returncode != 0
        symbols = run(["nm", str(baseline / "libwebp.a")]).stdout
        strings = run(["strings", str(baseline / "libwebp.a")]).stdout
        binary_strings = run(["strings", str(baseline / "cwebp")]).stdout
        assert "BackrefCostWorkspaceRemoteV5" not in symbols
        for forbidden in (RUNTIME, FAULT, RUNNER, SOURCE, "remote v5"):
            assert forbidden not in strings and forbidden not in binary_strings
        run(["python3", "scripts/generate_publication_corpus.py",
             "--output", str(corpus), "--verify"])
        publication = json.loads((corpus / "manifest.json").read_text())
        cases = {row["case_id"]: row for row in publication["cases"]}
        active = {RUNTIME: "1"}
        injected = {RUNTIME: "1", FAULT: "1"}
        for case_id, quality in MATRIX:
            source = corpus / cases[case_id]["file"]
            assert digest(source) == cases[case_id]["sha256"]
            for method in (4, 6):
                variants = {
                    "baseline": (baseline / "cwebp", None),
                    "off": (candidate / "cwebp", None),
                    "candidate": (candidate / "cwebp", active),
                    "repeat": (candidate / "cwebp", active),
                    "fallback": (candidate / "cwebp", injected),
                    "v3_gate": (candidate / "cwebp", {V3_RUNTIME: "1"}),
                    "v4_gate": (candidate / "cwebp", {V4_RUNTIME: "1"}),
                    "default_env": (baseline / "cwebp", active),
                }
                hashes = {}
                for name, (binary, environment) in variants.items():
                    output = temporary / f"{case_id}-{quality}-{method}-{name}.webp"
                    encode(binary, source, output, method, quality, environment)
                    hashes[name] = digest(output)
                assert len(set(hashes.values())) == 1, hashes
                decoded = temporary / f"{case_id}-{quality}-{method}.ppm"
                run([str(baseline / "dwebp"),
                     str(temporary / f"{case_id}-{quality}-{method}-candidate.webp"),
                     "-ppm", "-o", str(decoded)])
                assert digest(decoded) == cases[case_id]["sha256"]
        for sanitizer in ("undefined", "bounds"):
            directory = temporary / sanitizer
            configure(directory, candidate=True, sanitizer=sanitizer)
            build(directory, "cwebp")
            source = corpus / cases["texture-small"]["file"]
            candidate_output = temporary / f"{sanitizer}-candidate.webp"
            fallback_output = temporary / f"{sanitizer}-fallback.webp"
            options = {"UBSAN_OPTIONS": "halt_on_error=1"}
            encode(directory / "cwebp", source, candidate_output, 6, 75,
                   active | options)
            encode(directory / "cwebp", source, fallback_output, 6, 75,
                   injected | options)
            assert digest(candidate_output) == digest(fallback_output)
    print(json.dumps({"status": "PASS", "baseline": BASELINE,
                      "correctness_cells": 26, **projections}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
