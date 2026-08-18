#!/usr/bin/env python3
"""Untimed v2 candidate identity, correctness, fallback, and omission checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CYCLE_BASE = "d12036f790cce1dd4bef9fe3c963b0ef294d4c4a"
BUILD = "WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT"
MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT"
FAULT = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT_INJECT_FAILURE"
PRIOR_MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT"
PRIOR_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT"
RUNNER = "backref_cost_workspace_remote_v2_experiment_runner"
SOURCE = "backref_cost_workspace_remote_v2_experiment_enc.c"

CORRECTNESS_MATRIX = (
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
    for name in (RUNTIME, FAULT, PRIOR_RUNTIME, "WEBP_BENCHMARK_SESSION",
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
    args = ["cmake", "-S", ".", "-B", str(build),
            "-DWEBP_ENABLE_METAL=OFF", "-DBUILD_SHARED_LIBS=OFF",
            "-DWEBP_BUILD_EXTRAS=OFF", "-DWEBP_BUILD_CWEBP=ON",
            "-DWEBP_BUILD_DWEBP=ON", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    if candidate:
        args.append(f"-D{BUILD}=ON")
    if sanitizer == "undefined":
        flags = ("-O1 -g -fno-omit-frame-pointer "
                 "-fsanitize=undefined,integer -fno-sanitize-recover=all")
        args += [f"-DCMAKE_C_FLAGS={flags}",
                 "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=undefined,integer"]
    elif sanitizer == "bounds":
        flags = ("-O1 -g -fno-omit-frame-pointer "
                 "-fsanitize=array-bounds,pointer-overflow "
                 "-fno-sanitize-recover=all")
        args += [f"-DCMAKE_C_FLAGS={flags}",
                 "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=array-bounds,pointer-overflow"]
    run(args)


def build(directory: Path, *targets: str) -> None:
    run(["cmake", "--build", str(directory), "--target", *targets, "-j4"])


def encode(binary: Path, source: Path, output: Path, method: int, quality: int,
           env: dict[str, str] | None = None) -> None:
    run([str(binary), "-quiet", "-lossless", "-exact", "-q", str(quality),
         "-m", str(method), "-o", str(output), str(source)], env=env)


def candidate_projection_hashes() -> dict[str, str]:
    boundary = "src/enc/backward_references_cost_enc.c"
    validated = run(["git", "show", f"{CYCLE_BASE}:{boundary}"]).stdout
    current = (ROOT / boundary).read_text(encoding="utf-8")
    compiler = os.environ.get("CC", "cc")

    def preprocess(source: str, macro: str) -> str:
        return run([compiler, "-E", "-P", f"-I{ROOT}", f"-D{macro}=1",
                    "-x", "c", "-"], input_text=source).stdout

    expected = preprocess(validated, PRIOR_MACRO)
    actual = preprocess(current, MACRO)
    actual = actual.replace("VP8LBackrefCostWorkspaceRemoteV2ExperimentEnabled",
                            "VP8LBackrefCostWorkspaceABExperimentEnabled")
    actual = actual.replace("VP8LBackrefCostWorkspaceRemoteV2ExperimentMalloc",
                            "VP8LBackrefCostWorkspaceABExperimentMalloc")
    expected = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', expected)
    actual = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', actual)
    if actual != expected:
        raise AssertionError("v2 projection differs from the validated workspace candidate")

    prior_path = "src/enc/backref_cost_workspace_ab_experiment_enc.c"
    prior = run(["git", "show", f"{CYCLE_BASE}:{prior_path}"]).stdout
    helper = (ROOT / "src/enc/backref_cost_workspace_remote_v2_experiment_enc.c").read_text()
    prior = prior[prior.index("static int EnvironmentIsOne"):]
    helper = helper[helper.index("static int EnvironmentIsOne"):]
    helper = helper.replace("VP8LBackrefCostWorkspaceRemoteV2Experiment",
                            "VP8LBackrefCostWorkspaceABExperiment")
    helper = helper.replace("WEBP_BACKREF_COST_WORKSPACE_REMOTE_V2_EXPERIMENT",
                            "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT")
    if helper != prior:
        raise AssertionError("v2 helper behavior differs from the validated helper")
    return {
        "boundary_projection_sha256": hashlib.sha256(expected.encode()).hexdigest(),
        "normalized_helper_body_sha256": hashlib.sha256(prior.encode()).hexdigest(),
    }


def main() -> int:
    assert run(["git", "merge-base", "--is-ancestor", CYCLE_BASE, "HEAD"]).returncode == 0
    projections = candidate_projection_hashes()
    runner_source = (ROOT / "tools" /
                     "backref_cost_workspace_remote_v2_experiment_runner.c").read_text()
    session_check = runner_source.index("session == NULL")
    input_read = runner_source.index("ReadPPM(input_path")
    assert session_check < input_read
    assert "WEBP_BENCHMARK_SESSION=exclusive" in runner_source

    with tempfile.TemporaryDirectory(prefix="backref-workspace-remote-v2-test-") as raw:
        temp = Path(raw)
        baseline, candidate = temp / "baseline", temp / "candidate"
        undefined, bounds = temp / "undefined", temp / "bounds"
        corpus = temp / "corpus"
        configure(baseline, candidate=False)
        configure(candidate, candidate=True)
        build(baseline, "cwebp", "dwebp")
        build(candidate, "cwebp", "dwebp", RUNNER)

        baseline_commands = (baseline / "compile_commands.json").read_text()
        candidate_commands = (candidate / "compile_commands.json").read_text()
        assert MACRO not in baseline_commands and SOURCE not in baseline_commands
        assert f"-D{MACRO}=1" in candidate_commands and SOURCE in candidate_commands
        assert f"-D{PRIOR_MACRO}=1" not in candidate_commands
        absent = run(["cmake", "--build", str(baseline), "--target", RUNNER],
                     check=False)
        assert absent.returncode != 0
        symbols = run(["nm", str(baseline / "libwebp.a")]).stdout
        strings = run(["strings", str(baseline / "libwebp.a")]).stdout
        cwebp_strings = run(["strings", str(baseline / "cwebp")]).stdout
        assert "BackrefCostWorkspaceRemoteV2" not in symbols
        for forbidden in (RUNTIME, FAULT, RUNNER, SOURCE):
            assert forbidden not in strings and forbidden not in cwebp_strings

        run([sys.executable, "scripts/generate_publication_corpus.py",
             "--output", str(corpus), "--verify"])
        publication = json.loads((corpus / "manifest.json").read_text())
        cases = {row["case_id"]: row for row in publication["cases"]}
        active = {RUNTIME: "1"}
        injected = {RUNTIME: "1", FAULT: "1"}
        prior_only = {PRIOR_RUNTIME: "1"}
        for case_id, quality in CORRECTNESS_MATRIX:
            source = corpus / cases[case_id]["file"]
            assert digest(source) == cases[case_id]["sha256"]
            for method in (4, 6):
                variants = {
                    "baseline": (baseline / "cwebp", None),
                    "off": (candidate / "cwebp", None),
                    "candidate": (candidate / "cwebp", active),
                    "repeat": (candidate / "cwebp", active),
                    "fallback": (candidate / "cwebp", injected),
                    "prior_gate": (candidate / "cwebp", prior_only),
                    "default_env": (baseline / "cwebp", active),
                }
                outputs = {}
                for name, (binary, environment) in variants.items():
                    output = temp / f"{case_id}-q{quality}-m{method}-{name}.webp"
                    encode(binary, source, output, method, quality, environment)
                    outputs[name] = digest(output)
                assert len(set(outputs.values())) == 1, outputs
                decoded = temp / f"{case_id}-q{quality}-m{method}.ppm"
                run([str(baseline / "dwebp"),
                     str(temp / f"{case_id}-q{quality}-m{method}-candidate.webp"),
                     "-ppm", "-o", str(decoded)])
                assert digest(decoded) == cases[case_id]["sha256"]

        for sanitizer in ("undefined", "bounds"):
            directory = undefined if sanitizer == "undefined" else bounds
            configure(directory, candidate=True, sanitizer=sanitizer)
            build(directory, "cwebp")
            source = corpus / cases["texture-small"]["file"]
            candidate_output = temp / f"{sanitizer}-candidate.webp"
            fallback_output = temp / f"{sanitizer}-fallback.webp"
            encode(directory / "cwebp", source, candidate_output, 6, 75,
                   active | {"UBSAN_OPTIONS": "halt_on_error=1"})
            encode(directory / "cwebp", source, fallback_output, 6, 75,
                   injected | {"UBSAN_OPTIONS": "halt_on_error=1"})
            assert digest(candidate_output) == digest(fallback_output)

    print(json.dumps({"status": "PASS", "cycle_base": CYCLE_BASE,
                      "correctness_cells": 26, **projections}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
