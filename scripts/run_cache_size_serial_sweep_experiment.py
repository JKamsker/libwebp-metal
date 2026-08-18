#!/usr/bin/env python3
"""Frozen recorder-free operator for the cache-size serial-sweep A/B."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "cache_size_serial_sweep_experiment_v1.json"


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
        timeout: int = 240, stdout=None) -> subprocess.CompletedProcess:
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
    checks = (
        (manifest["corpus"]["generator"],
         manifest["corpus"]["generator_sha256"]),
        (manifest["corpus"]["manifest"],
         manifest["corpus"]["manifest_sha256"]),
        (manifest["candidate"]["source"],
         manifest["candidate"]["source_sha256"]),
        (manifest["candidate"]["runner"],
         manifest["candidate"]["runner_sha256"]),
        (manifest["operator"]["path"], manifest["operator"]["sha256"]),
    )
    for relative, expected in checks:
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"frozen hash mismatch for {relative}: {actual}")
    return manifest


def validate_source(manifest: dict) -> str:
    commit = git("rev-parse", "HEAD")
    expected = os.environ.get(manifest["required_expected_commit_environment"])
    if not expected:
        raise RuntimeError(
            f"{manifest['required_expected_commit_environment']} is required")
    if commit != expected:
        raise RuntimeError(f"HEAD {commit} does not match handoff {expected}")
    if git("status", "--porcelain"):
        raise RuntimeError("operator requires a completely clean worktree")
    if subprocess.run(["git", "merge-base", "--is-ancestor",
                       manifest["base_commit"], commit], cwd=ROOT,
                      check=False).returncode != 0:
        raise RuntimeError("handoff is not descended from the frozen base")
    return commit


def candidate_env(manifest: dict, *, inject: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    candidate = manifest["candidate"]
    env["WEBP_BENCHMARK_SESSION"] = "exclusive"
    env[candidate["runtime_flag"]] = candidate["runtime_value"]
    if inject:
        env[candidate["failure_injection_flag"]] = "1"
    else:
        env.pop(candidate["failure_injection_flag"], None)
    return env


def baseline_env(manifest: dict) -> dict[str, str]:
    env = os.environ.copy()
    env["WEBP_BENCHMARK_SESSION"] = "exclusive"
    env.pop(manifest["candidate"]["runtime_flag"], None)
    env.pop(manifest["candidate"]["failure_injection_flag"], None)
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
        available_pages = 0
        for line in result.stdout.splitlines():
            if "page size of" in line:
                page_size = int(line.split("page size of", 1)[1].split()[0])
            if line.startswith(("Pages free:", "Pages inactive:",
                                "Pages speculative:")):
                available_pages += int(line.split(":", 1)[1].strip().rstrip("."))
        if available_pages > 0:
            return available_pages * page_size
    raise RuntimeError("available-memory prerequisite is unavailable")


def configure_and_build(manifest: dict, temporary: Path, log) -> dict[str, Path]:
    common = manifest["builds"]["common"]
    builds: dict[str, Path] = {}
    for variant in ("baseline", "candidate"):
        build = temporary / f"build-{variant}"
        command = ["cmake", "-S", str(ROOT), "-B", str(build), *common]
        if variant == "candidate":
            command.append(
                f"-D{manifest['candidate']['build_flag']}=ON")
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, timeout=600, stdout=log)
        command = ["cmake", "--build", str(build), "--target", "cwebp",
                   "dwebp", "-j4"]
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, timeout=900, stdout=log)
        runner = build / "cache_size_serial_sweep_runner"
        command = [os.environ.get("CC", "cc"), "-O3", "-DNDEBUG",
                   f"-I{ROOT}", str(ROOT / manifest["candidate"]["runner"]),
                   str(build / "libwebp.a"), str(build / "libsharpyuv.a"),
                   "-lm", "-o", str(runner)]
        log.write(("COMMAND " + " ".join(command) + "\n").encode())
        run(command, timeout=240, stdout=log)
        builds[variant] = build
    return builds


def generate_corpus(manifest: dict, temporary: Path) -> tuple[Path, dict]:
    corpus = temporary / "corpus"
    run([sys.executable, str(ROOT / manifest["corpus"]["generator"]),
         "--output", str(corpus), "--verify"], timeout=900)
    publication = json.loads((corpus / "manifest.json").read_text())
    for case in publication["cases"]:
        if sha256(corpus / case["file"]) != case["sha256"]:
            raise RuntimeError(f"generated corpus hash mismatch: {case['case_id']}")
    return corpus, {case["case_id"]: case for case in publication["cases"]}


def encode(cwebp: Path, source: Path, output: Path, method: int,
           env: dict[str, str]) -> None:
    run([str(cwebp), "-quiet", "-lossless", "-exact", "-q", "75", "-m",
         str(method), "-o", str(output), str(source)], env=env)


def decode(dwebp: Path, source: Path, output: Path) -> None:
    run([str(dwebp), str(source), "-ppm", "-o", str(output)])


def correctness_gate(manifest: dict, builds: dict[str, Path], corpus: Path,
                     cases: dict[str, dict], output: Path) -> list[dict]:
    rows = []
    with tempfile.TemporaryDirectory(prefix="cache-sweep-correctness-") as raw:
        check = Path(raw)
        for case_id in manifest["corpus"]["correctness_cases"]:
            source = corpus / cases[case_id]["file"]
            for method in manifest["protocol"]["methods"]:
                paths = {name: check / f"{case_id}-m{method}-{name}.webp"
                         for name in ("baseline", "candidate", "repeat",
                                      "fallback")}
                encode(builds["baseline"] / "cwebp", source,
                       paths["baseline"], method, baseline_env(manifest))
                encode(builds["candidate"] / "cwebp", source,
                       paths["candidate"], method, candidate_env(manifest))
                encode(builds["candidate"] / "cwebp", source,
                       paths["repeat"], method, candidate_env(manifest))
                encode(builds["candidate"] / "cwebp", source,
                       paths["fallback"], method,
                       candidate_env(manifest, inject=True))
                hashes = {name: sha256(path) for name, path in paths.items()}
                if len(set(hashes.values())) != 1:
                    raise RuntimeError(
                        f"bitstream mismatch for {case_id} method {method}")
                decoded = {}
                for name, path in paths.items():
                    decoded_path = check / f"{case_id}-m{method}-{name}.ppm"
                    decode(builds["baseline"] / "dwebp", path, decoded_path)
                    decoded[name] = sha256(decoded_path)
                if len(set(decoded.values())) != 1:
                    raise RuntimeError(
                        f"decoded-pixel mismatch for {case_id} method {method}")
                if decoded["baseline"] != cases[case_id]["sha256"]:
                    raise RuntimeError(
                        f"decoded pixels differ from source for {case_id} method {method}")
                rows.append({
                    "schema": manifest["schemas"]["correctness"],
                    "case_id": case_id,
                    "method": method,
                    "input_sha256": cases[case_id]["sha256"],
                    "bitstream_sha256": hashes["baseline"],
                    "decoded_sha256": decoded["baseline"],
                    "decoded_source_exact": True,
                    "candidate_deterministic": True,
                    "fallback_exact": True,
                })
    write_json(output / "correctness.json", rows)
    return rows


def nearest_rank_p95(values: list[float]) -> float:
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def timed_matrix(manifest: dict, builds: dict[str, Path], corpus: Path,
                 cases: dict[str, dict], output: Path) -> tuple[list[dict], list[dict]]:
    samples: list[dict] = []
    commands: list[dict] = []
    records_path = output / "records.jsonl"
    commands_path = output / "commands.jsonl"
    pair_order = manifest["protocol"]["pair_order"]
    sequence = 0
    with records_path.open("w", encoding="utf-8") as records, \
            commands_path.open("w", encoding="utf-8") as command_file:
        for role in ("tune", "holdout"):
            case_id = manifest["corpus"]["timed"][role]["case_id"]
            source = corpus / cases[case_id]["file"]
            for method in manifest["protocol"]["methods"]:
                for lifecycle in ("cold", "warm"):
                    life = manifest["protocol"]["lifecycles"][lifecycle]
                    for pair in range(life["process_pairs"]):
                        variants = pair_order[pair].split("-")
                        for order, variant in enumerate(variants):
                            runner = builds[variant] / "cache_size_serial_sweep_runner"
                            argv = [str(runner), str(source), case_id, lifecycle,
                                    variant, str(method),
                                    str(life["discarded_warmups_per_process"]),
                                    str(life["measured_encodes_per_process"])]
                            started = time.monotonic()
                            result = run(argv, env=(candidate_env(manifest)
                                                   if variant == "candidate"
                                                   else baseline_env(manifest)))
                            duration = time.monotonic() - started
                            if duration > manifest["resources"]["maximum_command_seconds"]:
                                raise RuntimeError("command duration ceiling exceeded")
                            row_count = 0
                            for line in result.stdout.splitlines():
                                sample = json.loads(line)
                                if sample["schema"] != manifest["schemas"]["sample"]:
                                    raise RuntimeError("sample schema mismatch")
                                sample.update({"role": role, "pair": pair,
                                               "order": order,
                                               "sequence": sequence})
                                sequence += 1
                                samples.append(sample)
                                records.write(json.dumps(sample,
                                                         sort_keys=True) + "\n")
                                row_count += 1
                            expected_rows = (life["discarded_warmups_per_process"] +
                                             life["measured_encodes_per_process"])
                            if row_count != expected_rows:
                                raise RuntimeError("runner row-count mismatch")
                            command = {
                                "schema": manifest["schemas"]["command"],
                                "role": role, "case_id": case_id,
                                "method": method, "lifecycle": lifecycle,
                                "pair": pair, "order": order,
                                "variant": variant, "argv": argv,
                                "wall_seconds": duration, "sample_rows": row_count,
                            }
                            commands.append(command)
                            command_file.write(json.dumps(command,
                                                          sort_keys=True) + "\n")
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    signatures = {(row["case_id"], row["method"]):
                  (row["bitstream_bytes"], row["bitstream_fnv1a64"])
                  for row in measured}
    for row in measured:
        if signatures[(row["case_id"], row["method"])] != (
                row["bitstream_bytes"], row["bitstream_fnv1a64"]):
            raise RuntimeError("timed bitstream signature mismatch")
    return samples, commands


def evaluate(manifest: dict, samples: list[dict], commands: list[dict]) -> dict:
    cells = []
    required_pass = True
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    for role in ("tune", "holdout"):
        case_id = manifest["corpus"]["timed"][role]["case_id"]
        for method in manifest["protocol"]["methods"]:
            for lifecycle in ("cold", "warm"):
                process_values: dict[tuple[int, str], list[int]] = {}
                raw_values = {"baseline": [], "candidate": []}
                for row in measured:
                    if (row["case_id"], row["method"], row["lifecycle"]) != (
                            case_id, method, lifecycle):
                        continue
                    key = (row["pair"], row["variant"])
                    process_values.setdefault(key, []).append(row["elapsed_ns"])
                    raw_values[row["variant"]].append(row["elapsed_ns"])
                pair_ratios = []
                pair_count = manifest["protocol"]["lifecycles"][lifecycle][
                    "process_pairs"]
                for pair in range(pair_count):
                    baseline = statistics.median(process_values[(pair, "baseline")])
                    candidate = statistics.median(process_values[(pair, "candidate")])
                    pair_ratios.append(candidate / baseline)
                median_ratio = statistics.median(pair_ratios)
                p95_ratio = (nearest_rank_p95(raw_values["candidate"]) /
                             nearest_rank_p95(raw_values["baseline"]))
                passed = (median_ratio <= manifest["protocol"]["acceptance"]
                          ["paired_median_ratio_maximum"] and
                          p95_ratio <= manifest["protocol"]["acceptance"]
                          ["p95_ratio_maximum"])
                if role == "holdout":
                    required_pass = required_pass and passed
                cells.append({"role": role, "case_id": case_id,
                              "method": method, "lifecycle": lifecycle,
                              "process_pairs": pair_count,
                              "paired_median_ratio": median_ratio,
                              "p95_ratio": p95_ratio,
                              "passes_performance": passed})
    return {"schema": manifest["schemas"]["evaluation"],
            "timing_authority": "end-to-end WebPEncode only",
            "boundary_timing_available": False,
            "command_processes": len(commands),
            "sample_rows": len(samples),
            "measured_samples": len(measured),
            "cells": cells,
            "decision": "accept" if required_pass else "reject"}


def output_bytes(output: Path) -> int:
    return sum(path.stat().st_size for path in output.rglob("*") if path.is_file())


def write_artifact_hashes(manifest: dict, output: Path) -> None:
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "artifact-hashes.json":
            rows.append({"path": str(path.relative_to(output)),
                         "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_json(output / "artifact-hashes.json",
               {"schema": manifest["schemas"]["artifact_hashes"],
                "artifacts": rows})


def execute(manifest: dict, output: Path) -> None:
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")
    commit = validate_source(manifest)
    available = available_memory_bytes()
    if available < manifest["resources"]["minimum_available_memory_bytes"]:
        raise RuntimeError("available-memory prerequisite failed")
    if output.exists():
        raise RuntimeError("output path must not already exist")
    output.mkdir(parents=True)
    lease_path = Path(manifest["resources"]["lease_path"])
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    with lease_path.open("a+") as lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("exclusive benchmark lease is already held") from error
        with tempfile.TemporaryDirectory(prefix="cache-size-sweep-build-") as raw:
            temporary = Path(raw)
            with (output / "build.log").open("wb") as log:
                builds = configure_and_build(manifest, temporary, log)
            corpus, cases = generate_corpus(manifest, temporary)
            correctness = correctness_gate(manifest, builds, corpus, cases,
                                           output)
            samples, commands = timed_matrix(manifest, builds, corpus, cases,
                                              output)
    elapsed = time.monotonic() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rss = max(before, after)
    if platform.system() != "Darwin":
        rss *= 1024
    evaluation = evaluate(manifest, samples, commands)
    inventory = manifest["protocol"]["expected_inventory"]
    if len(commands) != inventory["command_processes"]:
        raise RuntimeError("command inventory mismatch")
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    warmups = [row for row in samples if row["sample_role"] == "warmup"]
    if (len(measured) != inventory["total_measured_samples"] or
            len(warmups) != inventory["warmup_samples"] or
            len(correctness) != inventory["correctness_cells"]):
        raise RuntimeError("sample or correctness inventory mismatch")
    write_json(output / "evaluation.json", evaluation)
    resources = {"schema": manifest["schemas"]["resources"],
                 "source_commit": commit, "elapsed_seconds": elapsed,
                 "available_memory_bytes_preflight": available,
                 "maximum_child_rss_bytes": rss,
                 "output_bytes_before_index": output_bytes(output),
                 "lease_released": True}
    if elapsed > manifest["resources"]["maximum_total_seconds"]:
        raise RuntimeError("total duration ceiling exceeded")
    if rss > manifest["resources"]["maximum_child_rss_bytes"]:
        raise RuntimeError("RSS ceiling exceeded")
    if resources["output_bytes_before_index"] > manifest["resources"][
            "maximum_output_bytes"]:
        raise RuntimeError("output-size ceiling exceeded")
    write_json(output / "resources.json", resources)
    (output / "operator-report.md").write_text(
        "# Cache-size serial-sweep operator report\n\n"
        f"Source: `{commit}`  \n"
        f"Correctness cells: {len(correctness)}  \n"
        f"Timed decision: **{evaluation['decision']}**  \n"
        "Timing authority: end-to-end `WebPEncode`; no boundary recorder or "
        "boundary timing was used.\n", encoding="utf-8")
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
            print(json.dumps({"schema": manifest["schema"],
                              "manifest_sha256": sha256(MANIFEST_PATH),
                              "operator_sha256": sha256(Path(__file__))},
                             sort_keys=True))
            return 0
        execute(manifest, args.output.resolve())
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
