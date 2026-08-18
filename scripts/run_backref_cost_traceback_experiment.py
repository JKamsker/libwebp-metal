#!/usr/bin/env python3
"""Frozen recorder-free operator for the backref cost/traceback A/B."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_traceback_experiment_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run(argv: list[str], *, env: dict[str, str] | None = None,
        timeout: int = 300, stdout=None) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=ROOT, env=env, timeout=timeout,
                            stdout=stdout or subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=stdout is None,
                            check=False)
    if result.returncode != 0:
        output = result.stdout if isinstance(result.stdout, str) else ""
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n{output}")
    return result


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT,
                                   text=True).strip()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for artifact in manifest["frozen_artifacts"]:
        relative, expected = artifact["path"], artifact["sha256"]
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"frozen hash mismatch for {relative}: {actual}")
    if manifest["protocol"]["recorders"] != "none":
        raise RuntimeError("frozen protocol unexpectedly enables a recorder")
    return manifest


def validate_source(manifest: dict) -> str:
    commit = git("rev-parse", "HEAD")
    variable = manifest["required_expected_commit_environment"]
    expected = os.environ.get(variable)
    if not expected:
        raise RuntimeError(f"{variable} is required")
    if commit != expected:
        raise RuntimeError(f"HEAD {commit} does not match handoff {expected}")
    if git("status", "--porcelain"):
        raise RuntimeError("operator requires a completely clean worktree")
    if subprocess.run(["git", "merge-base", "--is-ancestor",
                       manifest["base_commit"], commit], cwd=ROOT,
                      check=False).returncode != 0:
        raise RuntimeError("handoff is not descended from the frozen base")
    return commit


def variant_env(manifest: dict, variant: str,
                *, inject: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    candidate = manifest["candidate"]
    env["WEBP_BENCHMARK_SESSION"] = "exclusive"
    env.pop(candidate["failure_injection_flag"], None)
    if variant == "candidate":
        env[candidate["runtime_flag"]] = candidate["runtime_value"]
        if inject:
            env[candidate["failure_injection_flag"]] = "1"
    else:
        env.pop(candidate["runtime_flag"], None)
    return env


def available_memory_bytes() -> int:
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return pages * page_size
    except (OSError, ValueError):
        pass
    if platform.system() == "Darwin":
        result = run(["vm_stat"])
        page_size = 4096
        pages = 0
        for line in result.stdout.splitlines():
            if "page size of" in line:
                page_size = int(line.split("page size of", 1)[1].split()[0])
            if line.startswith(("Pages free:", "Pages inactive:",
                                "Pages speculative:")):
                pages += int(line.split(":", 1)[1].strip().rstrip("."))
        if pages > 0:
            return pages * page_size
    raise RuntimeError("available-memory prerequisite is unavailable")


def configure_and_build(manifest: dict, temporary: Path, log) -> dict[str, Path]:
    builds: dict[str, Path] = {}
    for variant in ("baseline", "candidate"):
        build = temporary / f"build-{variant}"
        command = ["cmake", "-S", str(ROOT), "-B", str(build),
                   *manifest["builds"]["common"]]
        if variant == "candidate":
            command.append(f"-D{manifest['candidate']['build_flag']}=ON")
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, timeout=600, stdout=log)
        command = ["cmake", "--build", str(build), "--target", "cwebp",
                   "dwebp", "-j4"]
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, timeout=1200, stdout=log)
        runner = build / "backref_cost_traceback_experiment_runner"
        command = [os.environ.get("CC", "cc"), "-O3", "-DNDEBUG",
                   f"-I{ROOT}", str(ROOT / manifest["candidate"]["runner"]),
                   str(build / "libwebp.a"), str(build / "libsharpyuv.a"),
                   "-lm", "-o", str(runner)]
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, stdout=log)
        builds[variant] = build
    return builds


def generate_corpus(manifest: dict, temporary: Path) -> tuple[Path, dict]:
    corpus = temporary / "corpus"
    run([sys.executable, str(ROOT / manifest["corpus"]["generator"]),
         "--output", str(corpus), "--verify"], timeout=1200)
    publication = json.loads((corpus / "manifest.json").read_text())
    cases = {row["case_id"]: row for row in publication["cases"]}
    for case in cases.values():
        if sha256(corpus / case["file"]) != case["sha256"]:
            raise RuntimeError(f"generated corpus mismatch: {case['case_id']}")
    for timed in manifest["corpus"]["timed"]:
        if cases[timed["case_id"]]["sha256"] != timed["sha256"]:
            raise RuntimeError("timed corpus role hash mismatch")
    return corpus, cases


def encode(binary: Path, source: Path, output: Path, method: int, quality: int,
           env: dict[str, str]) -> None:
    run([str(binary), "-quiet", "-lossless", "-exact", "-q", str(quality), "-m",
         str(method), "-o", str(output), str(source)], env=env)


def decode(binary: Path, source: Path, output: Path) -> None:
    run([str(binary), str(source), "-ppm", "-o", str(output)])


def correctness_gate(manifest: dict, builds: dict[str, Path], corpus: Path,
                     cases: dict, output: Path) -> list[dict]:
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="backref-cost-correctness-") as raw:
        check = Path(raw)
        for matrix in manifest["corpus"]["correctness_matrix"]:
            case_id = matrix["case_id"]
            source = corpus / cases[case_id]["file"]
            quality = matrix["quality"]
            for method in matrix["methods"]:
                names = ("baseline", "candidate", "repeat", "fallback",
                         "default_env")
                paths = {name: check / f"{case_id}-q{quality}-m{method}-{name}.webp"
                         for name in names}
                encode(builds["baseline"] / "cwebp", source,
                       paths["baseline"], method, quality,
                       variant_env(manifest, "baseline"))
                encode(builds["candidate"] / "cwebp", source,
                       paths["candidate"], method, quality,
                       variant_env(manifest, "candidate"))
                encode(builds["candidate"] / "cwebp", source,
                       paths["repeat"], method, quality,
                       variant_env(manifest, "candidate"))
                encode(builds["candidate"] / "cwebp", source,
                       paths["fallback"], method, quality,
                       variant_env(manifest, "candidate", inject=True))
                encode(builds["baseline"] / "cwebp", source,
                       paths["default_env"], method, quality,
                       variant_env(manifest, "candidate"))
                hashes = {name: sha256(path) for name, path in paths.items()}
                if len(set(hashes.values())) != 1:
                    raise RuntimeError(
                        f"bitstream mismatch for {case_id} method {method}")
                decoded: dict[str, str] = {}
                for name, path in paths.items():
                    ppm = check / f"{case_id}-q{quality}-m{method}-{name}.ppm"
                    decode(builds["baseline"] / "dwebp", path, ppm)
                    decoded[name] = sha256(ppm)
                if len(set(decoded.values())) != 1 or \
                        decoded["baseline"] != cases[case_id]["sha256"]:
                    raise RuntimeError(
                        f"decoded mismatch for {case_id} method {method}")
                rows.append({
                    "schema": manifest["schemas"]["correctness"],
                    "case_id": case_id, "quality": quality, "method": method,
                    "input_sha256": cases[case_id]["sha256"],
                    "bitstream_sha256": hashes["baseline"],
                    "decoded_sha256": decoded["baseline"],
                    "decoded_source_exact": True,
                    "candidate_deterministic": True,
                    "fallback_exact": True,
                    "default_build_independent": True,
                })
    write_json(output / "correctness.json", rows)
    return rows


def timed_matrix(manifest: dict, builds: dict[str, Path], corpus: Path,
                 cases: dict, output: Path) -> tuple[list[dict], list[dict]]:
    samples: list[dict] = []
    commands: list[dict] = []
    sequence = 0
    with (output / "records.jsonl").open("w", encoding="utf-8") as records, \
            (output / "commands.jsonl").open("w", encoding="utf-8") as command_file:
        for timed in manifest["corpus"]["timed"]:
            role, case_id = timed["role"], timed["case_id"]
            source = corpus / cases[case_id]["file"]
            for method in manifest["protocol"]["methods"]:
                for lifecycle in ("cold", "warm"):
                    life = manifest["protocol"]["lifecycles"][lifecycle]
                    for pair in range(life["process_pairs"]):
                        variants = manifest["protocol"]["pair_order"][pair].split("-")
                        for order, variant in enumerate(variants):
                            runner = builds[variant] / "backref_cost_traceback_experiment_runner"
                            argv = [str(runner), str(source), case_id, lifecycle,
                                    variant, str(method),
                                    str(life["discarded_warmups_per_process"]),
                                    str(life["measured_encodes_per_process"])]
                            started = time.monotonic()
                            result = run(argv, env=variant_env(manifest, variant))
                            wall = time.monotonic() - started
                            if wall > manifest["resources"]["maximum_command_seconds"]:
                                raise RuntimeError("command duration ceiling exceeded")
                            row_count = 0
                            for line in result.stdout.splitlines():
                                sample = json.loads(line)
                                if sample.get("schema") != manifest["schemas"]["sample"]:
                                    raise RuntimeError("sample schema mismatch")
                                sample.update({"role": role, "pair": pair,
                                               "order": order,
                                               "sequence": sequence})
                                sequence += 1
                                row_count += 1
                                samples.append(sample)
                                records.write(json.dumps(sample, sort_keys=True) + "\n")
                            expected = (life["discarded_warmups_per_process"] +
                                        life["measured_encodes_per_process"])
                            if row_count != expected:
                                raise RuntimeError("runner row-count mismatch")
                            command = {
                                "schema": manifest["schemas"]["command"],
                                "role": role, "case_id": case_id,
                                "method": method, "lifecycle": lifecycle,
                                "pair": pair, "order": order,
                                "variant": variant, "argv": argv,
                                "wall_seconds": wall, "sample_rows": row_count,
                            }
                            commands.append(command)
                            command_file.write(json.dumps(command,
                                                          sort_keys=True) + "\n")
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    signatures: dict[tuple[str, int], tuple[int, str]] = {}
    for row in measured:
        key = (row["case_id"], row["method"])
        signature = (row["bitstream_bytes"], row["bitstream_fnv1a64"])
        if key in signatures and signatures[key] != signature:
            raise RuntimeError("timed bitstream signature mismatch")
        signatures[key] = signature
    return samples, commands


def nearest_rank_p95(values: list[int]) -> int:
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def evaluate(manifest: dict, samples: list[dict], commands: list[dict]) -> dict:
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    cells = []
    required_pass = True
    for timed in manifest["corpus"]["timed"]:
        role, case_id = timed["role"], timed["case_id"]
        for method in manifest["protocol"]["methods"]:
            for lifecycle in ("cold", "warm"):
                process: dict[tuple[int, str], list[int]] = {}
                raw = {"baseline": [], "candidate": []}
                for row in measured:
                    if (row["case_id"], row["method"], row["lifecycle"]) != \
                            (case_id, method, lifecycle):
                        continue
                    process.setdefault((row["pair"], row["variant"]), []).append(
                        row["elapsed_ns"])
                    raw[row["variant"]].append(row["elapsed_ns"])
                pair_count = manifest["protocol"]["lifecycles"][lifecycle]["process_pairs"]
                ratios = []
                for pair in range(pair_count):
                    baseline = statistics.median(process[(pair, "baseline")])
                    candidate = statistics.median(process[(pair, "candidate")])
                    ratios.append(candidate / baseline)
                median_ratio = statistics.median(ratios)
                p95_ratio = (nearest_rank_p95(raw["candidate"]) /
                             nearest_rank_p95(raw["baseline"]))
                limits = manifest["protocol"]["acceptance"]
                passed = (median_ratio <= limits["paired_median_ratio_maximum"] and
                          p95_ratio <= limits["p95_ratio_maximum"])
                if role == "holdout":
                    required_pass = required_pass and passed
                cells.append({
                    "role": role, "case_id": case_id, "method": method,
                    "lifecycle": lifecycle, "process_pairs": pair_count,
                    "paired_median_ratio": median_ratio,
                    "p95_ratio": p95_ratio, "passes_performance": passed,
                })
    return {
        "schema": manifest["schemas"]["evaluation"],
        "timing_authority": "end-to-end WebPEncode only",
        "boundary_timing_available": False,
        "command_processes": len(commands), "sample_rows": len(samples),
        "measured_samples": len(measured), "cells": cells,
        "decision": "accept" if required_pass else "reject",
    }


def output_bytes(output: Path) -> int:
    return sum(path.stat().st_size for path in output.rglob("*") if path.is_file())


def write_artifact_hashes(manifest: dict, output: Path) -> None:
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "artifact-hashes.json":
            rows.append({"path": str(path.relative_to(output)),
                         "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_json(output / "artifact-hashes.json", {
        "schema": manifest["schemas"]["artifact_hashes"], "artifacts": rows})


def execute(manifest: dict, output: Path) -> None:
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")
    commit = validate_source(manifest)
    available = available_memory_bytes()
    if available < manifest["resources"]["minimum_available_memory_bytes"]:
        raise RuntimeError("available-memory prerequisite failed")
    if output.exists() or not output.is_absolute():
        raise RuntimeError("output must be an absolute path that does not exist")
    lease_path = Path(manifest["resources"]["lease_path"])
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("exclusive benchmark lease is already held") from error
        output.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix="backref-cost-traceback-build-") as raw:
            temporary = Path(raw)
            with (output / "build.log").open("wb") as log:
                builds = configure_and_build(manifest, temporary, log)
            corpus, cases = generate_corpus(manifest, temporary)
            correctness = correctness_gate(manifest, builds, corpus, cases, output)
            samples, commands = timed_matrix(manifest, builds, corpus, cases, output)
            for case in cases.values():
                if sha256(corpus / case["file"]) != case["sha256"]:
                    raise RuntimeError(
                        f"corpus mutated during execution: {case['case_id']}")
    elapsed = time.monotonic() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rss = max(before, after)
    if platform.system() != "Darwin":
        rss *= 1024
    inventory = manifest["protocol"]["expected_inventory"]
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    warmups = [row for row in samples if row["sample_role"] == "warmup"]
    cold = [row for row in measured if row["lifecycle"] == "cold"]
    warm = [row for row in measured if row["lifecycle"] == "warm"]
    baseline_measured = [row for row in measured
                         if row["variant"] == "baseline"]
    candidate_measured = [row for row in measured
                          if row["variant"] == "candidate"]
    if (len(commands) != inventory["command_processes"] or
            len(cold) != inventory["cold_measured_samples"] or
            len(warm) != inventory["warm_measured_samples"] or
            len(measured) != inventory["total_measured_samples"] or
            len(baseline_measured) != inventory["variant_measured_samples"] or
            len(candidate_measured) != inventory["variant_measured_samples"] or
            len(warmups) != inventory["warmup_samples"] or
            len(correctness) != inventory["correctness_cells"]):
        raise RuntimeError("frozen inventory mismatch")
    evaluation = evaluate(manifest, samples, commands)
    if (len(evaluation["cells"]) != inventory["evaluation_cells"] or
            sum(cell["role"] == "holdout"
                for cell in evaluation["cells"]) !=
            inventory["required_holdout_cells"]):
        raise RuntimeError("frozen evaluation-cell inventory mismatch")
    write_json(output / "evaluation.json", evaluation)
    resources = {
        "schema": manifest["schemas"]["resources"],
        "source_commit": commit, "elapsed_seconds": elapsed,
        "available_memory_bytes_preflight": available,
        "maximum_child_rss_bytes": rss,
        "output_bytes_before_index": output_bytes(output),
        "parallel_benchmark_processes": 1, "lease_released": True,
    }
    if elapsed > manifest["resources"]["maximum_total_seconds"]:
        raise RuntimeError("total duration ceiling exceeded")
    if rss > manifest["resources"]["maximum_child_rss_bytes"]:
        raise RuntimeError("RSS ceiling exceeded")
    if resources["output_bytes_before_index"] > \
            manifest["resources"]["maximum_output_bytes"]:
        raise RuntimeError("output-size ceiling exceeded")
    write_json(output / "resources.json", resources)
    (output / "operator-report.md").write_text(
        "# Backref cost/traceback operator report\n\n"
        f"Source: `{commit}`  \nCorrectness cells: {len(correctness)}  \n"
        f"Timed decision: **{evaluation['decision']}**  \n"
        "Timing authority: external end-to-end `WebPEncode`; no recorder or "
        "boundary timing was compiled or used. Closed-experiment samples and "
        "ratios were not used.\n", encoding="utf-8")
    write_artifact_hashes(manifest, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        if args.command == "validate":
            print(json.dumps({
                "schema": manifest["schema"],
                "manifest_sha256": sha256(MANIFEST_PATH),
                "operator_sha256": sha256(Path(__file__)),
            }, sort_keys=True))
            return 0
        execute(manifest, args.output)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
