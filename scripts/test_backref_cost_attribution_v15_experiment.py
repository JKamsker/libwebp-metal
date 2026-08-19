#!/usr/bin/env python3
"""Untimed V15 correctness, single-DP, sanitizer, ABI, and omission checks."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "e085ff0cd7e0e9f4e9bdeaa939346725ae3d4d22"
BUILD = "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT"
MACRO = "WEBP_USE_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_ATTRIBUTION_V15_EXPERIMENT"
RUNNER = "backref_cost_attribution_v15_experiment_runner"
SOURCE = "backref_cost_attribution_v15_experiment_enc.c"


def run(argv: list[str], *, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    clean = os.environ.copy()
    for name in (
        "WEBP_BENCHMARK_SESSION", "CUDA_VISIBLE_DEVICES", "MallocNanoZone",
        "WEBP_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V2_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V3_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V4_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V5_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V6_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V7_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V8_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V9_EXPERIMENT", RUNTIME,
        "WEBP_BACKREF_COST_ATTRIBUTION_V10_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V11_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V12_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V13_EXPERIMENT",
        "WEBP_BACKREF_COST_ATTRIBUTION_V14_EXPERIMENT",
    ):
        clean.pop(name, None)
    if env:
        clean.update(env)
    result = subprocess.run(argv, cwd=ROOT, env=clean, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {argv}\n{result.stdout}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(build: Path, *, candidate: bool,
              sanitizer: str | None = None) -> None:
    argv = [
        "cmake", "-S", ".", "-B", str(build), "-DWEBP_ENABLE_METAL=OFF",
        "-DBUILD_SHARED_LIBS=OFF", "-DWEBP_BUILD_EXTRAS=OFF",
        "-DWEBP_BUILD_CWEBP=OFF", "-DWEBP_BUILD_DWEBP=OFF",
        "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]
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
                 "-DCMAKE_EXE_LINKER_FLAGS="
                 "-fsanitize=array-bounds,pointer-overflow"]
    run(argv)


def build(directory: Path, *targets: str) -> None:
    run(["cmake", "--build", str(directory), "--target", *targets,
         "--parallel", "2"])


def runner_correctness(runner: Path, source: Path, method: int, variant: str,
                       output: Path, extra: dict[str, str] | None = None) -> None:
    environment = {} if extra is None else dict(extra)
    if variant == "candidate":
        environment[RUNTIME] = "1"
    run([str(runner), "correctness", str(source), str(method), variant,
         str(output)], env=environment)


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


def public_symbols(library: Path) -> list[str]:
    output = run(["nm", str(library)]).stdout
    return sorted(line.split()[-1] for line in output.splitlines()
                  if line.split() and line.split()[-1].startswith("WebP"))


def main() -> int:
    assert run(["git", "rev-parse", "HEAD"]).returncode == 0
    assert not run(["git", "diff", "--name-only", BASE, "--", "src/webp",
                    "sharpyuv"]).stdout.strip()
    source_text = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    assert "V15 preserves the frozen selector-once and one-selected-DP boundary" in \
        source_text
    assert "BACKREF_DP_RECORD_CALL();" in (
        ROOT / "src/enc/backward_references_cost_distance_only_enc.inc"
    ).read_text()

    with tempfile.TemporaryDirectory(prefix="backref-attribution-v15-test-") as raw:
        temporary = Path(raw)
        baseline = temporary / "baseline"
        candidate = temporary / "candidate"
        corpus = temporary / "corpus"
        configure(baseline, candidate=False)
        configure(candidate, candidate=True)
        build(baseline, "webp")
        build(candidate, "webp", RUNNER)
        baseline_commands = (baseline / "compile_commands.json").read_text()
        candidate_commands = (candidate / "compile_commands.json").read_text()
        assert MACRO not in baseline_commands and SOURCE not in baseline_commands
        assert f"-D{MACRO}=1" in candidate_commands and \
            SOURCE in candidate_commands
        absent = run(["cmake", "--build", str(baseline), "--target", RUNNER],
                     check=False)
        assert absent.returncode != 0
        baseline_strings = run(["strings", str(baseline / "libwebp.a")]).stdout
        for forbidden in (RUNTIME, RUNNER, SOURCE,
                          "BackrefCostAttributionV15"):
            assert forbidden not in baseline_strings
        assert public_symbols(baseline / "libwebp.a") == \
            public_symbols(candidate / "libwebp.a")

        runner = candidate / RUNNER
        truth_table = {}
        for value in (None, "", "0", "01", "1", "true"):
            environment = {} if value is None else {RUNTIME: value}
            row = json.loads(run([str(runner), "guard"],
                                 env=environment).stdout)
            truth_table["absent" if value is None else value] = row["enabled"]
        assert truth_table == {
            "absent": False, "": False, "0": False, "01": False,
            "1": True, "true": False,
        }
        timer = json.loads(run([str(runner), "timer-check"]).stdout)
        assert timer["monotonic"] and timer["positive_deltas"] > 0
        for variant in ("baseline", "candidate"):
            stage_output = temporary / f"timer-accounting-{variant}.jsonl"
            environment = {
                "WEBP_BENCHMARK_SESSION": "exclusive",
                "WEBP_BACKREF_COST_ATTRIBUTION_V15_TIMERS": "1",
                "WEBP_BACKREF_COST_ATTRIBUTION_V15_STAGE_OUTPUT":
                    str(stage_output),
                "WEBP_BACKREF_COST_ATTRIBUTION_V15_RUN_ID": "local-smoke",
                "WEBP_BACKREF_COST_ATTRIBUTION_V15_CASE_ID":
                    "synthetic-no-encoder",
                "WEBP_BACKREF_COST_ATTRIBUTION_V15_SAMPLE_SET": "cold",
            }
            if variant == "candidate":
                environment[RUNTIME] = "1"
            run([str(runner), "timer-accounting-check", variant],
                env=environment)
            accounting = json.loads(stage_output.read_text())
            stages = accounting["stages"]
            assert accounting["selected_dp_calls"] == 1
            assert accounting["selector_evaluations"] == 1
            assert [stages[name]["calls"] for name in (
                "backref_cost_dp_total", "backref_cost_dp_setup",
                "backref_cost_dp_steady")] == [1, 1, 1]
            assert stages["backref_cost_dp_setup"]["ns"] + \
                stages["backref_cost_dp_steady"]["ns"] <= \
                stages["backref_cost_dp_total"]["ns"]

        run(["python3", "scripts/generate_publication_corpus.py", "--output",
             str(corpus), "--verify"])
        publication = json.loads((corpus / "manifest.json").read_text())
        cases = {row["case_id"]: row for row in publication["cases"]}
        correctness_encodes = 0
        for case_id in ("photo-large", "graphic-large"):
            source = corpus / cases[case_id]["file"]
            source_hash = digest(source)
            for method in (4, 6):
                products = []
                for variant in ("baseline", "candidate"):
                    for repeat in range(2):
                        output = temporary / (
                            f"{case_id}-m{method}-{variant}-{repeat}.webp")
                        runner_correctness(runner, source, method, variant,
                                           output)
                        products.append(digest(output))
                        correctness_encodes += 1
                assert len(set(products)) == 1
                assert digest(source) == source_hash == cases[case_id]["sha256"]
                counters = {}
                for variant in ("baseline", "candidate"):
                    environment = {RUNTIME: "1"} if variant == "candidate" \
                        else None
                    counters[variant] = json.loads(run(
                        [str(runner), "counter-check", str(source),
                         str(method), variant], env=environment).stdout)
                assert counters["baseline"]["candidate_dp_calls"] == 0
                assert counters["candidate"]["baseline_dp_calls"] == 0
                assert counters["baseline"]["bitstream_fnv1a64"] == \
                    counters["candidate"]["bitstream_fnv1a64"]
                assert counters["baseline"]["bitstream_bytes"] == \
                    counters["candidate"]["bitstream_bytes"]
                assert all(row["post_reset_zero"] for row in counters.values())
                invalid = json.loads(run(
                    [str(runner), "counter-check", str(source), str(method),
                     "baseline"], env={RUNTIME: "01"}).stdout)
                assert invalid["baseline_dp_calls"] == \
                    invalid["selector_evaluations"]
                assert invalid["candidate_dp_calls"] == 0
                assert invalid["bitstream_fnv1a64"] == \
                    counters["baseline"]["bitstream_fnv1a64"]
        assert correctness_encodes == 16

        for sanitizer in ("undefined", "bounds"):
            directory = temporary / sanitizer
            configure(directory, candidate=True, sanitizer=sanitizer)
            build(directory, RUNNER)
            sanitized_runner = directory / RUNNER
            options = {"UBSAN_OPTIONS": "halt_on_error=1"}
            for index, (width, height) in enumerate(
                    ((1, 1), (2, 1), (9, 1), (10, 1), (11, 1),
                     (257, 1), (33, 17), (129, 65))):
                fixture = temporary / f"boundary-{sanitizer}-{index}.ppm"
                write_boundary_ppm(fixture, width, height, index + 1)
                baseline_output = temporary / f"{sanitizer}-{index}-base.webp"
                candidate_output = temporary / f"{sanitizer}-{index}-cand.webp"
                runner_correctness(sanitized_runner, fixture, 4, "baseline",
                                   baseline_output, options)
                runner_correctness(sanitized_runner, fixture, 4, "candidate",
                                   candidate_output, options)
                assert digest(baseline_output) == digest(candidate_output)

    print(json.dumps({
        "status": "PASS", "base_commit": BASE,
        "correctness_encodes": 16, "counter_cells": 4,
        "sanitizer_configurations": 2, "boundary_fixtures": 16,
        "exact_runtime_truth_table": truth_table,
        "timer_validation": timer,
        "public_api_abi_equal": True, "default_omission": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
