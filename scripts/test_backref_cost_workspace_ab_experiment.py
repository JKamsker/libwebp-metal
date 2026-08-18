#!/usr/bin/env python3
"""Untimed equivalence, isolation, fallback, and refusal checks."""

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
BASE = "e7c1be7d4070103a9b41b8c30fbbc95cd18e5a5c"
BUILD = "WEBP_BUILD_BACKREF_COST_WORKSPACE_AB_EXPERIMENT"
MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_AB_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT"
FAULT = "WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT_INJECT_FAILURE"
OLD_BUILD = "WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT"
OLD_MACRO = "WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT"
OLD_RUNTIME = "WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT"


def run(argv: list[str], *, env: dict[str, str] | None = None,
        input_text: str | None = None, check: bool = True,
        timeout: int = 1200) -> subprocess.CompletedProcess[str]:
    clean = os.environ.copy()
    for name in (RUNTIME, FAULT, OLD_RUNTIME, "WEBP_BENCHMARK_SESSION",
                 "MallocNanoZone"):
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
    path = "src/enc/backward_references_cost_enc.c"
    merged = run(["git", "show", f"{BASE}:{path}"]).stdout
    current = (ROOT / path).read_text(encoding="utf-8")
    compiler = os.environ.get("CC", "cc")

    def preprocess(source: str, macro: str) -> str:
        result = run([compiler, "-E", "-P", f"-I{ROOT}", f"-D{macro}=1",
                      "-x", "c", "-"], input_text=source)
        return result.stdout

    old = preprocess(merged, OLD_MACRO)
    new = preprocess(current, MACRO)
    new = new.replace("VP8LBackrefCostWorkspaceABExperimentEnabled",
                      "VP8LBackrefCostTracebackExperimentEnabled")
    new = new.replace("VP8LBackrefCostWorkspaceABExperimentMalloc",
                      "VP8LBackrefCostTracebackExperimentMalloc")
    old = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', old)
    new = re.sub(r'"<stdin>", [0-9]+,', '"<source>", 0,', new)
    if new != old:
        raise AssertionError("new candidate projection differs from merged research candidate")
    helper_path = "src/enc/backref_cost_traceback_experiment_enc.c"
    old_helper = run(["git", "show", f"{BASE}:{helper_path}"]).stdout
    new_helper = (ROOT / "src/enc/backref_cost_workspace_ab_experiment_enc.c").read_text()
    old_helper = old_helper[old_helper.index("static int EnvironmentIsOne"):]
    new_helper = new_helper[new_helper.index("static int EnvironmentIsOne"):]
    new_helper = new_helper.replace("VP8LBackrefCostWorkspaceABExperiment",
                                    "VP8LBackrefCostTracebackExperiment")
    new_helper = new_helper.replace("WEBP_BACKREF_COST_WORKSPACE_AB_EXPERIMENT",
                                    "WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT")
    if new_helper != old_helper:
        raise AssertionError("new helper body differs from merged research helper")
    return {
        "boundary_projection_sha256": hashlib.sha256(old.encode()).hexdigest(),
        "helper_body_sha256": hashlib.sha256(old_helper.encode()).hexdigest(),
    }


def main() -> int:
    assert run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0
    projections = candidate_projection_hashes()
    with tempfile.TemporaryDirectory(prefix="backref-workspace-ab-test-") as raw:
        temp = Path(raw)
        baseline, candidate = temp / "baseline", temp / "candidate"
        undefined, bounds = temp / "undefined", temp / "bounds"
        corpus = temp / "corpus"
        configure(baseline, candidate=False)
        configure(candidate, candidate=True)
        build(baseline, "cwebp", "dwebp")
        build(candidate, "cwebp", "dwebp",
              "backref_cost_workspace_ab_experiment_runner")

        baseline_commands = (baseline / "compile_commands.json").read_text()
        candidate_commands = (candidate / "compile_commands.json").read_text()
        source_name = "backref_cost_workspace_ab_experiment_enc.c"
        assert MACRO not in baseline_commands and source_name not in baseline_commands
        assert f"-D{MACRO}=1" in candidate_commands
        assert source_name in candidate_commands
        assert f"-D{OLD_MACRO}=1" not in candidate_commands
        assert OLD_BUILD not in candidate_commands
        absent = run(["cmake", "--build", str(baseline), "--target",
                      "backref_cost_workspace_ab_experiment_runner"], check=False)
        assert absent.returncode != 0
        symbols = run(["nm", str(baseline / "libwebp.a")]).stdout
        strings = run(["strings", str(baseline / "libwebp.a")]).stdout
        assert "BackrefCostWorkspaceAB" not in symbols
        assert RUNTIME not in strings and FAULT not in strings

        runner = candidate / "backref_cost_workspace_ab_experiment_runner"
        refusal = run([str(runner), "missing.ppm", "guard", "cold",
                       "candidate", "4", "0", "1"],
                      env={RUNTIME: "1"}, check=False)
        assert refusal.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in refusal.stdout

        run([sys.executable, "scripts/generate_publication_corpus.py",
             "--output", str(corpus), "--verify"])
        publication = json.loads((corpus / "manifest.json").read_text())
        cases = {row["case_id"]: row for row in publication["cases"]}
        manifest = json.loads((ROOT / "scripts" /
                               "backref_cost_traceback_experiment_v1.json").read_text())
        active = {RUNTIME: "1"}
        injected = {RUNTIME: "1", FAULT: "1"}
        old_only = {OLD_RUNTIME: "1"}
        for matrix in manifest["corpus"]["correctness_matrix"]:
            case_id, quality = matrix["case_id"], matrix["quality"]
            source = corpus / cases[case_id]["file"]
            assert digest(source) == cases[case_id]["sha256"]
            for method in matrix["methods"]:
                variants = {
                    "baseline": (baseline / "cwebp", None),
                    "off": (candidate / "cwebp", None),
                    "candidate": (candidate / "cwebp", active),
                    "repeat": (candidate / "cwebp", active),
                    "fallback": (candidate / "cwebp", injected),
                    "old_gate": (candidate / "cwebp", old_only),
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

    print(json.dumps({"status": "PASS", "base_commit": BASE,
                      **projections}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
