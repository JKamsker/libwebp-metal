#!/usr/bin/env python3
"""Untimed guards and equivalence tests for the single-pass slab candidate."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_FLAG = "WEBP_BUILD_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT"
MACRO = "WEBP_USE_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT"
RUNTIME = "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_EXPERIMENT"
FAULT = "WEBP_CACHE_SIZE_SINGLE_PASS_SLAB_INJECT_FAILURE"
OLD_GATES = (
    "WEBP_USE_PREDICTOR_BOUNDARY_EXPERIMENT",
    "WEBP_USE_BACKREF_EXACT_EXPERIMENT",
    "WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT",
    "WEBP_USE_CACHE_SIZE_SERIAL_SWEEP_EXPERIMENT",
)


def execute(argv: list[str], *, env: dict[str, str] | None = None,
            timeout: int = 1200,
            check: bool = True) -> subprocess.CompletedProcess[str]:
    clean = os.environ.copy()
    for name in (RUNTIME, FAULT, "WEBP_BENCHMARK_SESSION", "MallocNanoZone"):
        clean.pop(name, None)
    if env:
        clean.update(env)
    result = subprocess.run(argv, cwd=ROOT, env=clean, timeout=timeout,
                            text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {argv}\n{result.stdout}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(build: Path, candidate: bool,
              sanitizer: str | None = None) -> None:
    argv = ["cmake", "-S", ".", "-B", str(build),
            "-DWEBP_ENABLE_METAL=OFF", "-DBUILD_SHARED_LIBS=OFF",
            "-DWEBP_BUILD_EXTRAS=OFF", "-DWEBP_BUILD_CWEBP=ON",
            "-DWEBP_BUILD_DWEBP=ON", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    if candidate:
        argv.append(f"-D{BUILD_FLAG}=ON")
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
    execute(argv)


def build(build_dir: Path, *targets: str) -> None:
    execute(["cmake", "--build", str(build_dir), "--target", *targets, "-j4"])


def encode(binary: Path, source: Path, output: Path, method: int,
           env: dict[str, str] | None = None,
           check: bool = True) -> subprocess.CompletedProcess[str]:
    return execute([str(binary), "-quiet", "-lossless", "-exact", "-q", "75",
                    "-m", str(method), "-o", str(output), str(source)],
                   env=env, check=check)


def main() -> int:
    manifest_path = ROOT / "scripts" / "cache_size_single_pass_slab_experiment_v1.json"
    manifest = json.loads(manifest_path.read_text())
    source_text = (ROOT / manifest["candidate"]["source"]).read_text()
    assert source_text.count("WebPSafeCalloc(") == 1
    assert "VP8LAllocateHistogram(" not in source_text
    assert "VP8LColorCacheInit(" not in source_text
    assert source_text.count("VP8LRefsCursorInit(") == 1
    assert "cache_size_serial_sweep" not in source_text.lower()

    with tempfile.TemporaryDirectory(prefix="cache-size-slab-test-") as raw:
        temp = Path(raw)
        baseline = temp / "baseline"
        candidate = temp / "candidate"
        sanitizer = temp / "sanitizer"
        bounds_sanitizer = temp / "bounds-sanitizer"
        corpus = temp / "corpus"
        configure(baseline, False)
        configure(candidate, True)
        build(baseline, "cwebp", "dwebp")
        build(candidate, "cwebp", "dwebp",
              "cache_size_single_pass_slab_test")

        baseline_commands = (baseline / "compile_commands.json").read_text()
        candidate_commands = (candidate / "compile_commands.json").read_text()
        assert MACRO not in baseline_commands
        assert "cache_size_single_pass_slab_enc.c" not in baseline_commands
        assert f"-D{MACRO}=1" in candidate_commands
        assert "cache_size_single_pass_slab_enc.c" in candidate_commands
        assert not any(gate in candidate_commands for gate in OLD_GATES)
        absent_target = execute([
            "cmake", "--build", str(baseline), "--target",
            "cache_size_single_pass_slab_test"], check=False)
        assert absent_target.returncode != 0
        baseline_symbols = execute(["nm", str(baseline / "libwebp.a")]).stdout
        assert "SinglePassSlab" not in baseline_symbols
        baseline_strings = execute([
            "strings", str(baseline / "libwebp.a")]).stdout
        assert RUNTIME not in baseline_strings and FAULT not in baseline_strings

        execute([str(candidate / "cache_size_single_pass_slab_test")])
        configure(sanitizer, True, sanitizer="undefined")
        build(sanitizer, "cache_size_single_pass_slab_test", "cwebp")
        execute([str(sanitizer / "cache_size_single_pass_slab_test"),
                 "--sanitizer-smoke"],
                env={"UBSAN_OPTIONS": "halt_on_error=1"})
        configure(bounds_sanitizer, True, sanitizer="bounds")
        build(bounds_sanitizer, "cache_size_single_pass_slab_test")
        execute([str(bounds_sanitizer / "cache_size_single_pass_slab_test"),
                 "--bounds-sanitizer-smoke"],
                env={"UBSAN_OPTIONS": "halt_on_error=1"})

        execute([sys.executable, "scripts/generate_publication_corpus.py",
                 "--output", str(corpus), "--verify"])
        publication = json.loads((corpus / "manifest.json").read_text())
        cases = {row["case_id"]: row for row in publication["cases"]}
        active = {RUNTIME: "1", "WEBP_BENCHMARK_SESSION": "exclusive"}
        injected = active | {FAULT: "1"}

        source = corpus / "photo-small.ppm"
        refused = encode(candidate / "cwebp", source, temp / "refused.webp", 4,
                         {RUNTIME: "1"}, False)
        assert refused.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in refused.stdout
        invalid = encode(candidate / "cwebp", source, temp / "invalid.webp", 4,
                         {RUNTIME: "yes",
                          "WEBP_BENCHMARK_SESSION": "exclusive"}, False)
        assert invalid.returncode != 0 and "expected exact value 1" in invalid.stdout

        for case_id in manifest["corpus"]["correctness_cases"]:
            source = corpus / cases[case_id]["file"]
            assert digest(source) == cases[case_id]["sha256"]
            for method in manifest["protocol"]["methods"]:
                names = ("default", "off", "candidate", "repeat", "fallback",
                         "default_env")
                outputs = {name: temp / f"{case_id}-m{method}-{name}.webp"
                           for name in names}
                encode(baseline / "cwebp", source, outputs["default"], method)
                encode(candidate / "cwebp", source, outputs["off"], method)
                encode(candidate / "cwebp", source, outputs["candidate"], method,
                       active)
                encode(candidate / "cwebp", source, outputs["repeat"], method,
                       active)
                encode(candidate / "cwebp", source, outputs["fallback"], method,
                       injected)
                encode(baseline / "cwebp", source, outputs["default_env"], method,
                       active)
                hashes = {name: digest(path) for name, path in outputs.items()}
                assert len(set(hashes.values())) == 1, (case_id, method, hashes)
                decoded = {}
                for name, path in outputs.items():
                    ppm = temp / f"{case_id}-m{method}-{name}.ppm"
                    execute([str(baseline / "dwebp"), str(path), "-ppm", "-o",
                             str(ppm)])
                    decoded[name] = digest(ppm)
                assert len(set(decoded.values())) == 1
                assert decoded["candidate"] == cases[case_id]["sha256"]

        # Sanitized end-to-end activation and allocation-fallback smoke.
        source = corpus / "texture-small.ppm"
        san_candidate = temp / "san-candidate.webp"
        san_fallback = temp / "san-fallback.webp"
        encode(sanitizer / "cwebp", source, san_candidate, 6, active)
        encode(sanitizer / "cwebp", source, san_fallback, 6, injected)
        assert digest(san_candidate) == digest(san_fallback)

    validation = execute([
        sys.executable,
        "scripts/run_cache_size_single_pass_slab_experiment.py", "validate"])
    assert manifest["schema"] in validation.stdout
    with tempfile.TemporaryDirectory(prefix="slab-operator-refusal-") as raw:
        refused_output = Path(raw) / "must-not-exist"
        refusal = execute([
            sys.executable,
            "scripts/run_cache_size_single_pass_slab_experiment.py", "run",
            str(refused_output)], check=False)
        assert refusal.returncode != 0
        assert "WEBP_BENCHMARK_SESSION=exclusive" in refusal.stdout
        assert not refused_output.exists()

    print("PASS: single-pass slab untimed equivalence, guards, fallback, "
          "determinism, decoded pixels, build independence, lease, and sanitizers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
