#!/usr/bin/env python3
"""Untimed interval-search v3 correctness, fallback, and omission checks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "c472599ce8d3aee1e4f5bcf70b56b9c354351660"
BUILD = "WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
MACRO = "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT"
FAULT = "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_EXPERIMENT_INJECT_FAILURE"
V2_MACRO = "WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT"
V2_RUNTIME = "WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT"
V3_MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT"
V3_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT"
V4_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT"
V5_RUNTIME = "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT"
V5_MACRO = "WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V5_EXPERIMENT"
RUNNER = "backref_cost_interval_search_v3_experiment_runner"
SOURCE = "backref_cost_interval_search_v3_experiment_enc.c"
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
    for name in (RUNTIME, FAULT, V2_RUNTIME, V3_RUNTIME, V4_RUNTIME, V5_RUNTIME,
                 "WEBP_BENCHMARK_SESSION",
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


def write_boundary_ppm(path: Path, width: int, height: int, seed: int) -> None:
    pixels = bytearray()
    state = seed & 0xffffffff
    for index in range(width * height):
        state ^= (state << 13) & 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        if seed & 1:
            value = ((index // 3) & 3) * 61
            pixels.extend((value, value ^ 0x55, value))
        else:
            pixels.extend((state & 255, (state >> 8) & 255,
                           (state >> 16) & 255))
    path.write_bytes(
        f"P6\n{width} {height}\n255\n".encode("ascii") + pixels)


def equivalence() -> dict[str, str]:
    boundary = ROOT / "src/enc/backward_references_cost_enc.c"
    current = boundary.read_text(encoding="utf-8")
    compiler = os.environ.get("CC", "cc")

    def preprocess(macro: str) -> str:
        return run([compiler, "-E", "-P", f"-I{ROOT}", f"-D{macro}=1",
                    "-x", "c", "-"], input_text=current).stdout

    baseline = preprocess("WEBP_INTERVAL_SEARCH_V3_UNUSED_BASELINE_MACRO")
    v2 = preprocess(V2_MACRO)
    actual = preprocess(MACRO)
    normalize = lambda value: re.sub(
        r"(IntervalSearch|INTERVAL_SEARCH_)[Vv]?[23]", r"\1VERSION", value)
    assert normalize(v2) == normalize(actual)
    assert "use_interval_search_v3" not in baseline
    assert "CostInterval* append_hint = NULL" in current
    assert "start > append_hint->start" in current
    assert "if (use_append_hint) append_hint = interval" in current
    assert "if (interval_next == NULL)" in current
    assert "CostInterval* append_hint;" not in actual
    assert "use_interval_search_v3;" not in actual
    assert "current->start < previous->start" in current
    assert "previous->next->start < current->start" in current
    assert current.index("start > append_hint->start") < \
        current.index("position_hint = append_hint")
    helper = (ROOT / "src/enc/backref_cost_interval_search_v3_experiment_enc.c").read_text()
    v2_helper = (ROOT / "src/enc/backref_cost_interval_search_v2_experiment_enc.c").read_text()
    normalize_identity = lambda value: re.sub(
        r"([Vv]|_v)[23]", r"\1VERSION", value)
    assert normalize_identity(v2_helper) == normalize_identity(helper)
    layout_probe = current.replace(
        "} CostManager;", "} CostManager;\n"
        "typedef char CostManagerSizeMustRemain33224["
        "sizeof(CostManager) == 33224 ? 1 : -1];", 1)
    for macro in (V2_MACRO, MACRO):
        run([compiler, "-fsyntax-only", f"-I{ROOT}", f"-D{macro}=1",
             "-x", "c", "-"], input_text=layout_probe)
    return {
        "baseline_preprocessed_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
        "candidate_preprocessed_sha256": hashlib.sha256(actual.encode()).hexdigest(),
        "normalized_v2_v3_candidate_sha256": hashlib.sha256(
            normalize(actual).encode()).hexdigest(),
        "cost_manager_size_bytes": 33224,
        "helper_sha256": hashlib.sha256(helper.encode()).hexdigest(),
    }


def main() -> int:
    assert run(["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"]).returncode == 0
    projections = equivalence()
    compiler = os.environ.get("CC", "cc")
    overlap = run([compiler, f"-I{ROOT}", f"-D{MACRO}=1", f"-D{V5_MACRO}=1",
                   "-fsyntax-only", "src/enc/backward_references_cost_enc.c"],
                  check=False)
    assert overlap.returncode != 0
    assert "mutually exclusive" in overlap.stdout
    v2_overlap = run([compiler, f"-I{ROOT}", f"-D{MACRO}=1",
                      f"-D{V2_MACRO}=1", "-fsyntax-only",
                      "src/enc/backward_references_cost_enc.c"], check=False)
    assert v2_overlap.returncode != 0
    assert "mutually exclusive" in v2_overlap.stdout
    runner_source = (ROOT / "tools" /
                     "backref_cost_interval_search_v3_experiment_runner.c").read_text()
    assert "session == NULL" in runner_source
    assert "recorder build refuses timed samples" in runner_source
    with tempfile.TemporaryDirectory(prefix="interval-search-v3-candidate-test-") as raw:
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
        assert "BackrefCostIntervalSearchV3" not in symbols
        for forbidden in (RUNTIME, FAULT, RUNNER, SOURCE, "interval-search v3"):
            assert forbidden not in strings and forbidden not in binary_strings
        candidate_symbols = run(["nm", str(candidate / "libwebp.a")]).stdout
        candidate_strings = run(["strings", str(candidate / "libwebp.a")]).stdout
        assert "BackrefCostIntervalSearchV3Record" not in candidate_symbols
        assert "WEBP_BACKREF_COST_INTERVAL_SEARCH_V3_RECORDER" not in \
            candidate_strings
        baseline_exports = sorted(line.split()[-1] for line in symbols.splitlines()
                                  if line.split() and line.split()[-1].startswith("WebP"))
        candidate_exports = sorted(
            line.split()[-1] for line in candidate_symbols.splitlines()
            if line.split() and line.split()[-1].startswith("WebP"))
        assert baseline_exports == candidate_exports
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
                    "invalid_runtime": (candidate / "cwebp", {RUNTIME: "01"}),
                    "repeat": (candidate / "cwebp", active),
                    "fallback": (candidate / "cwebp", injected),
                    "v2_gate": (candidate / "cwebp", {V2_RUNTIME: "1"}),
                    "workspace_v3_gate": (candidate / "cwebp", {V3_RUNTIME: "1"}),
                    "v4_gate": (candidate / "cwebp", {V4_RUNTIME: "1"}),
                    "v5_gate": (candidate / "cwebp", {V5_RUNTIME: "1"}),
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
            source = corpus / cases["photo-small"]["file"]
            candidate_output = temporary / f"{sanitizer}-candidate.webp"
            fallback_output = temporary / f"{sanitizer}-fallback.webp"
            options = {"UBSAN_OPTIONS": "halt_on_error=1"}
            encode(directory / "cwebp", source, candidate_output, 6, 75,
                   active | options)
            encode(directory / "cwebp", source, fallback_output, 6, 75,
                   injected | options)
            assert digest(candidate_output) == digest(fallback_output)
            for index, (width, height) in enumerate(
                    ((1, 1), (2, 1), (9, 1), (10, 1), (11, 1),
                     (257, 1), (33, 17), (129, 65))):
                fuzzed = temporary / f"boundary-{sanitizer}-{index}.ppm"
                write_boundary_ppm(fuzzed, width, height, index + 1)
                baseline_output = temporary / f"boundary-{sanitizer}-{index}-base.webp"
                candidate_output = temporary / f"boundary-{sanitizer}-{index}-cand.webp"
                encode(directory / "cwebp", fuzzed, baseline_output, 4, 75,
                       options)
                encode(directory / "cwebp", fuzzed, candidate_output, 4, 75,
                       active | options)
                assert digest(baseline_output) == digest(candidate_output)
    print(json.dumps({"status": "PASS", "baseline": BASELINE,
                      "correctness_cells": 26, **projections}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
