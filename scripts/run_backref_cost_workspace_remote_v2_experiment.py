#!/usr/bin/env python3
"""Frozen remote-v2 host operator for the backref-cost workspace remote v2 A/B."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import platform
import re
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_remote_v2_manifest.json"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def command(argv: list[str], *, env: dict[str, str] | None = None,
            timeout: int = 300, stdout=None, stderr=None,
            check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=ROOT, env=env, timeout=timeout,
                            stdout=stdout if stdout is not None else subprocess.PIPE,
                            stderr=stderr if stderr is not None else subprocess.STDOUT,
                            text=stdout is None, check=False)
    if check and result.returncode != 0:
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
        path = ROOT / artifact["path"]
        actual = sha256(path)
        if actual != artifact["sha256"]:
            raise RuntimeError(
                f"frozen hash mismatch for {artifact['path']}: {actual}")
    if manifest["protocol"]["recorders"] != "none":
        raise RuntimeError("recorders must remain disabled")
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
        raise RuntimeError("operator requires a clean worktree")
    if command(["git", "merge-base", "--is-ancestor",
                manifest["base_commit"], commit], check=False).returncode != 0:
        raise RuntimeError("source is not descended from the frozen base")
    return commit


def clean_environment(manifest: dict, variant: str,
                      inject: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    candidate = manifest["candidate"]
    for name in manifest["forbidden_environment"]:
        env.pop(name, None)
    env["WEBP_BENCHMARK_SESSION"] = "exclusive"
    env.pop(candidate["runtime_flag"], None)
    env.pop(candidate["failure_injection_flag"], None)
    if variant == "candidate":
        env[candidate["runtime_flag"]] = "1"
        if inject:
            env[candidate["failure_injection_flag"]] = "1"
    return env


def capture(argv: list[str]) -> str:
    return command(argv).stdout.strip()


def available_memory() -> int:
    vm = capture(["vm_stat"])
    match = re.search(r"page size of ([0-9]+) bytes", vm)
    if match is None:
        raise RuntimeError("vm_stat page size unavailable")
    pages = sum(int(found.group(1)) for found in
                (re.search(rf"^{name}:\s+([0-9]+)\.", vm, re.MULTILINE)
                 for name in ("Pages free", "Pages inactive", "Pages speculative"))
                if found is not None)
    return pages * int(match.group(1))


def disk_snapshot(path: Path) -> tuple[int, str]:
    raw = capture(["df", "-Pk", str(path)])
    rows = raw.splitlines()
    if len(rows) != 2:
        raise RuntimeError("unexpected df output")
    return int(rows[1].split()[3]) * 1024, raw


def process_snapshot(output: Path | None, stage: str) -> dict:
    text = capture(["ps", "-axo", "pid=,ppid=,state=,etime=,command="])
    if output is not None:
        (output / f"processes-{stage}.txt").write_text(text + "\n")
    lines = text.splitlines()
    runner_workers = [line for line in lines if "Runner.Worker" in line]
    forbidden_patterns = (
        "backref_cost_workspace_remote_v2_experiment_runner",
        "benchmark_metal", "metal_benchmark", "nvidia-smi", "nvcc", "cuda-memcheck",
    )
    conflicts = [line for line in lines
                 if any(pattern.lower() in line.lower()
                        for pattern in forbidden_patterns)]
    record = {
        "stage": stage,
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "process_table_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "runner_worker_matches": runner_workers,
        "benchmark_or_cuda_matches": conflicts,
        "github_runner_listener_present": any("Runner.Listener" in line
                                                for line in lines),
    }
    if runner_workers:
        raise RuntimeError("active GitHub Actions Runner.Worker/job detected")
    if conflicts:
        raise RuntimeError("another benchmark or CUDA process is active")
    return record


def host_preflight(manifest: dict, output: Path | None = None,
                   stage: str = "preflight") -> dict:
    host = manifest["remote_host"]
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("remote host must be Darwin arm64")
    compiler_path = capture(["xcrun", "--find", "clang"])
    compiler_version = capture(["xcrun", "clang", "--version"])
    sdk_path = capture(["xcrun", "--sdk", "macosx", "--show-sdk-path"])
    sdk_version = capture(["xcrun", "--sdk", "macosx", "--show-sdk-version"])
    developer_dir = capture(["xcode-select", "-p"])
    model = capture(["sysctl", "-n", "hw.model"])
    cpu = capture(["sysctl", "-n", "machdep.cpu.brand_string"])
    memory = int(capture(["sysctl", "-n", "hw.memsize"]))
    available = available_memory()
    disk, disk_record = disk_snapshot(Path.home())
    battery = capture(["pmset", "-g", "batt"])
    custom = capture(["pmset", "-g", "custom"])
    thermal = capture(["pmset", "-g", "therm"])
    power_json = json.loads(capture(["system_profiler", "SPPowerDataType", "-json"]))
    ac_entries = [row.get("AC Power", {})
                  for row in power_json.get("SPPowerDataType", [])
                  if "AC Power" in row]
    if (compiler_path != host["compiler_path"] or
            compiler_version.splitlines() != host["compiler_version_lines"] or
            sdk_path != host["sdk_path"] or sdk_version != host["sdk_version"] or
            model != host["hardware_model"] or cpu != host["cpu_brand"]):
        raise RuntimeError("compiler, SDK, or Apple hardware identity mismatch")
    if memory != host["physical_memory_bytes"]:
        raise RuntimeError("physical-memory identity mismatch")
    if available < manifest["resources"]["minimum_available_memory_bytes"]:
        raise RuntimeError("available-memory prerequisite failed")
    if disk < manifest["resources"]["minimum_available_disk_bytes"]:
        raise RuntimeError("available-disk prerequisite failed")
    if "AC Power" not in battery or "lowpowermode         0" not in custom:
        raise RuntimeError("AC power with Low Power Mode off is required")
    if not ac_entries or any(row.get("Current Power Source") != "TRUE" or
                             row.get("LowPowerMode") != "No" for row in ac_entries):
        raise RuntimeError("system_profiler power prerequisite failed")
    for required in host["required_thermal_lines"]:
        if required not in thermal:
            raise RuntimeError("thermal/performance state prerequisite failed")
    processes = process_snapshot(output, stage)
    return {
        "schema": manifest["schemas"]["preflight"], "stage": stage,
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uname": capture(["uname", "-a"]), "sw_vers": capture(["sw_vers"]),
        "hardware_model": model, "cpu_brand": cpu,
        "physical_memory_bytes": memory, "available_memory_bytes": available,
        "available_disk_bytes": disk, "disk_record": disk_record,
        "disk_record_path": str(Path.home()), "compiler_path": compiler_path,
        "compiler_version_lines": compiler_version.splitlines(),
        "sdk_path": sdk_path, "sdk_version": sdk_version,
        "effective_developer_dir": developer_dir,
        "effective_developer_dir_environment": os.environ.get("DEVELOPER_DIR"),
        "effective_sdkroot_environment": os.environ.get("SDKROOT"),
        "effective_cc_environment": os.environ.get("CC"),
        "low_power_mode_pmset_off": "lowpowermode         0" in custom,
        "low_power_mode_profiler_off": bool(ac_entries) and all(
            row.get("LowPowerMode") == "No" for row in ac_entries),
        "ac_power_effective": "AC Power" in battery and bool(ac_entries) and all(
            row.get("Current Power Source") == "TRUE" for row in ac_entries),
        "pmset_batt": battery, "pmset_custom": custom,
        "pmset_thermal": thermal, "system_profiler_power": power_json,
        "process_isolation": processes,
    }


def configure_and_build(manifest: dict, temporary: Path, log) -> dict[str, Path]:
    builds = {}
    build_env = clean_environment(manifest, "baseline")
    build_env["CC"] = manifest["remote_host"]["compiler_path"]
    build_env["SDKROOT"] = manifest["remote_host"]["sdk_path"]
    for variant in ("baseline", "candidate"):
        build = temporary / f"build-{variant}"
        argv = ["cmake", "-S", str(ROOT), "-B", str(build),
                *manifest["builds"]["common"]]
        if variant == "candidate":
            argv.append(f"-D{manifest['candidate']['build_flag']}=ON")
        log.write(("COMMAND " + " ".join(argv) + "\n").encode())
        command(argv, env=build_env, timeout=600, stdout=log)
        targets = ["cwebp", "dwebp"]
        if variant == "candidate":
            targets.append(manifest["candidate"]["runner_target"])
        argv = ["cmake", "--build", str(build), "--target", *targets, "-j4"]
        log.write(("COMMAND " + " ".join(argv) + "\n").encode())
        command(argv, env=build_env, timeout=1200, stdout=log)
        if variant == "baseline":
            runner = build / manifest["candidate"]["runner_target"]
            argv = [manifest["remote_host"]["compiler_path"], "-O3", "-DNDEBUG",
                    f"-I{ROOT}", str(ROOT / manifest["candidate"]["runner"]),
                    str(build / "libwebp.a"), str(build / "libsharpyuv.a"),
                    "-lm", "-o", str(runner)]
            log.write(("COMMAND " + " ".join(argv) + "\n").encode())
            command(argv, env=build_env, stdout=log)
        builds[variant] = build
    return builds


def generate_corpus(manifest: dict, temporary: Path) -> tuple[Path, dict]:
    corpus = temporary / "corpus"
    command([sys.executable, str(ROOT / manifest["corpus"]["generator"]),
             "--output", str(corpus), "--verify"], timeout=1200)
    publication = json.loads((corpus / "manifest.json").read_text())
    cases = {row["case_id"]: row for row in publication["cases"]}
    for case in cases.values():
        if sha256(corpus / case["file"]) != case["sha256"]:
            raise RuntimeError("generated corpus hash mismatch")
    for timed in manifest["corpus"]["timed"]:
        if cases[timed["case_id"]]["sha256"] != timed["sha256"]:
            raise RuntimeError("frozen timed corpus hash mismatch")
    return corpus, cases


def encode(binary: Path, source: Path, output: Path, method: int, quality: int,
           env: dict[str, str]) -> None:
    command([str(binary), "-quiet", "-lossless", "-exact", "-q", str(quality),
             "-m", str(method), "-o", str(output), str(source)], env=env)


def correctness_gate(manifest: dict, builds: dict[str, Path], corpus: Path,
                     cases: dict, output: Path) -> list[dict]:
    rows = []
    with tempfile.TemporaryDirectory(prefix="backref-workspace-correctness-") as raw:
        check = Path(raw)
        for matrix in manifest["corpus"]["correctness_matrix"]:
            case_id, quality = matrix["case_id"], matrix["quality"]
            source = corpus / cases[case_id]["file"]
            for method in matrix["methods"]:
                variants = {
                    "baseline": (builds["baseline"] / "cwebp",
                                 clean_environment(manifest, "baseline")),
                    "candidate_off": (builds["candidate"] / "cwebp",
                                      clean_environment(manifest, "baseline")),
                    "candidate": (builds["candidate"] / "cwebp",
                                  clean_environment(manifest, "candidate")),
                    "repeat": (builds["candidate"] / "cwebp",
                               clean_environment(manifest, "candidate")),
                    "fallback": (builds["candidate"] / "cwebp",
                                 clean_environment(manifest, "candidate", True)),
                    "default_env": (builds["baseline"] / "cwebp",
                                    clean_environment(manifest, "candidate")),
                }
                paths = {}
                for name, (binary, env) in variants.items():
                    path = check / f"{case_id}-q{quality}-m{method}-{name}.webp"
                    encode(binary, source, path, method, quality, env)
                    paths[name] = path
                hashes = {name: sha256(path) for name, path in paths.items()}
                if len(set(hashes.values())) != 1:
                    raise RuntimeError("correctness bitstream mismatch")
                decoded = {}
                for name, path in paths.items():
                    ppm = check / f"{case_id}-q{quality}-m{method}-{name}.ppm"
                    command([str(builds["baseline"] / "dwebp"), str(path),
                             "-ppm", "-o", str(ppm)])
                    decoded[name] = sha256(ppm)
                if len(set(decoded.values())) != 1 or \
                        decoded["baseline"] != cases[case_id]["sha256"]:
                    raise RuntimeError("correctness decoded-pixel mismatch")
                rows.append({
                    "schema": manifest["schemas"]["correctness"],
                    "case_id": case_id, "quality": quality, "method": method,
                    "input_sha256": cases[case_id]["sha256"],
                    "bitstream_sha256": hashes["baseline"],
                    "decoded_sha256": decoded["baseline"],
                    "candidate_deterministic": True, "fallback_exact": True,
                    "default_build_independent": True,
                })
    write_json(output / "correctness.json", rows)
    return rows


def timed_matrix(manifest: dict, builds: dict[str, Path], corpus: Path,
                 cases: dict, output: Path) -> tuple[list[dict], list[dict]]:
    samples, commands = [], []
    sequence = 0
    with (output / "records.jsonl").open("w") as records, \
            (output / "commands.jsonl").open("w") as command_rows, \
            (output / "timed-child-stderr.log").open("w") as timed_stderr:
        for timed in manifest["corpus"]["timed"]:
            role, case_id = timed["role"], timed["case_id"]
            source = corpus / cases[case_id]["file"]
            for method in manifest["protocol"]["methods"]:
                for lifecycle in ("cold", "warm"):
                    life = manifest["protocol"]["lifecycles"][lifecycle]
                    for pair in range(life["process_pairs"]):
                        variants = manifest["protocol"]["pair_order"][pair].split("-")
                        for order, variant in enumerate(variants):
                            runner = builds[variant] / manifest["candidate"]["runner_target"]
                            argv = [str(runner), str(source), case_id, lifecycle,
                                    variant, str(method),
                                    str(life["discarded_warmups_per_process"]),
                                    str(life["measured_encodes_per_process"])]
                            timed_stderr.write(
                                f"### sequence={sequence} role={role} case={case_id} "
                                f"method={method} lifecycle={lifecycle} pair={pair} "
                                f"order={order} variant={variant}\n")
                            timed_stderr.flush()
                            started = time.monotonic()
                            result = command(argv,
                                             env=clean_environment(manifest, variant),
                                             stderr=timed_stderr)
                            wall = time.monotonic() - started
                            if wall > manifest["resources"]["maximum_command_seconds"]:
                                raise RuntimeError("timed command duration ceiling exceeded")
                            lines = result.stdout.splitlines()
                            expected = (life["discarded_warmups_per_process"] +
                                        life["measured_encodes_per_process"])
                            if len(lines) != expected:
                                raise RuntimeError("timed runner row-count mismatch")
                            for line in lines:
                                row = json.loads(line)
                                if row.get("schema") != manifest["schemas"]["sample"]:
                                    raise RuntimeError("timed sample schema mismatch")
                                row.update({"role": role, "pair": pair, "order": order,
                                            "sequence": sequence})
                                records.write(json.dumps(row, sort_keys=True) + "\n")
                                samples.append(row)
                                sequence += 1
                            entry = {
                                "schema": manifest["schemas"]["command"],
                                "role": role, "case_id": case_id, "method": method,
                                "lifecycle": lifecycle, "pair": pair, "order": order,
                                "variant": variant, "argv": argv,
                                "wall_seconds": wall, "sample_rows": len(lines),
                                "stderr_log": "timed-child-stderr.log",
                            }
                            command_rows.write(json.dumps(entry, sort_keys=True) + "\n")
                            commands.append(entry)
    signatures = {}
    for row in samples:
        key = (row["case_id"], row["method"])
        value = (row["bitstream_bytes"], row["bitstream_fnv1a64"])
        if key in signatures and signatures[key] != value:
            raise RuntimeError("timed bitstream signature mismatch")
        signatures[key] = value
    return samples, commands


def p95(values: list[int]) -> int:
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def evaluate(manifest: dict, samples: list[dict], commands: list[dict]) -> dict:
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    cells, required_pass = [], True
    for timed in manifest["corpus"]["timed"]:
        role, case_id = timed["role"], timed["case_id"]
        for method in manifest["protocol"]["methods"]:
            for lifecycle in ("cold", "warm"):
                process, raw = {}, {"baseline": [], "candidate": []}
                for row in measured:
                    if (row["case_id"], row["method"], row["lifecycle"]) != \
                            (case_id, method, lifecycle):
                        continue
                    process.setdefault((row["pair"], row["variant"]), []).append(
                        row["elapsed_ns"])
                    raw[row["variant"]].append(row["elapsed_ns"])
                pairs = manifest["protocol"]["lifecycles"][lifecycle]["process_pairs"]
                ratios = [statistics.median(process[(pair, "candidate")]) /
                          statistics.median(process[(pair, "baseline")])
                          for pair in range(pairs)]
                median_ratio = statistics.median(ratios)
                p95_ratio = p95(raw["candidate"]) / p95(raw["baseline"])
                limits = manifest["protocol"]["acceptance"]
                passed = (median_ratio <= limits["paired_median_ratio_maximum"] and
                          p95_ratio <= limits["p95_ratio_maximum"])
                if role == "holdout":
                    required_pass = required_pass and passed
                cells.append({"role": role, "case_id": case_id, "method": method,
                              "lifecycle": lifecycle, "process_pairs": pairs,
                              "paired_median_ratio": median_ratio,
                              "p95_ratio": p95_ratio,
                              "passes_performance": passed})
    return {"schema": manifest["schemas"]["evaluation"],
            "timing_authority": "end-to-end WebPEncode only",
            "command_processes": len(commands), "sample_rows": len(samples),
            "measured_samples": len(measured), "cells": cells,
            "decision": "accept" if required_pass else "reject"}


def output_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def write_hash_index(manifest: dict, output: Path) -> None:
    rows = [{"path": str(path.relative_to(output)), "bytes": path.stat().st_size,
             "sha256": sha256(path)} for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "artifact-hashes.json"]
    write_json(output / "artifact-hashes.json",
               {"schema": manifest["schemas"]["artifact_hashes"],
                "artifacts": rows})


def execute(manifest: dict, output: Path) -> None:
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")
    commit = validate_source(manifest)
    if output.exists() or not output.is_absolute():
        raise RuntimeError("output must be an absolute path that does not exist")
    output.mkdir(parents=True)
    preflight = host_preflight(manifest, output, "preflight")
    write_json(output / "preflight.json", preflight)
    source_rows = [{"path": item["path"], "sha256": sha256(ROOT / item["path"])}
                   for item in manifest["frozen_artifacts"]]
    write_json(output / "source-hashes.json", {
        "schema": manifest["schemas"]["source_hashes"],
        "source_commit": commit, "manifest_sha256": sha256(MANIFEST_PATH),
        "frozen_artifacts": source_rows,
        "candidate_equivalence": manifest["candidate"]["equivalence"]})
    lease_path = Path(os.path.expanduser(manifest["resources"]["lease_path"]))
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rss_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    lease_record = {"schema": manifest["schemas"]["lease"],
                    "path": str(lease_path), "acquired": False,
                    "released": False}
    try:
        with lease_path.open("a+") as lease:
            try:
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError("remote exclusive benchmark lease is held") from error
            lease_record["acquired"] = True
            lease_record["acquired_at_utc"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            write_json(output / "lease-record.json", lease_record)
            try:
                with tempfile.TemporaryDirectory(
                        prefix="backref-cost-workspace-remote-v2-build-") as raw:
                    temporary = Path(raw)
                    with (output / "build.log").open("wb") as log:
                        builds = configure_and_build(manifest, temporary, log)
                    corpus, cases = generate_corpus(manifest, temporary)
                    correctness = correctness_gate(
                        manifest, builds, corpus, cases, output)
                    pre_timing = host_preflight(manifest, output, "pre-timing")
                    write_json(output / "pre-timing.json", pre_timing)
                    samples, commands = timed_matrix(
                        manifest, builds, corpus, cases, output)
                    post = host_preflight(manifest, output, "post-timing")
                    write_json(output / "post-timing.json", post)
                    for case in cases.values():
                        if sha256(corpus / case["file"]) != case["sha256"]:
                            raise RuntimeError("corpus mutated")
            finally:
                fcntl.flock(lease, fcntl.LOCK_UN)
                lease_record["released"] = True
                lease_record["released_at_utc"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    finally:
        write_json(output / "lease-record.json", lease_record)
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rss = max(rss_before, rss)
    inventory = manifest["protocol"]["expected_inventory"]
    measured = [row for row in samples if row["sample_role"] != "warmup"]
    warmups = [row for row in samples if row["sample_role"] == "warmup"]
    cold = [row for row in measured if row["lifecycle"] == "cold"]
    warm = [row for row in measured if row["lifecycle"] == "warm"]
    if (len(commands), len(cold), len(warm), len(warmups), len(measured),
            sum(row["variant"] == "baseline" for row in measured),
            sum(row["variant"] == "candidate" for row in measured),
            len(correctness)) != (
            inventory["command_processes"], inventory["cold_measured_samples"],
            inventory["warm_measured_samples"], inventory["warmup_samples"],
            inventory["total_measured_samples"],
            inventory["variant_measured_samples"],
            inventory["variant_measured_samples"], inventory["correctness_cells"]):
        raise RuntimeError("frozen raw inventory mismatch")
    evaluation = evaluate(manifest, samples, commands)
    if len(evaluation["cells"]) != inventory["evaluation_cells"]:
        raise RuntimeError("frozen evaluation inventory mismatch")
    write_json(output / "evaluation.json", evaluation)
    resources = {"schema": manifest["schemas"]["resources"],
                 "source_commit": commit, "elapsed_seconds": elapsed,
                 "maximum_child_rss_bytes": rss,
                 "output_bytes_before_index": output_bytes(output),
                 "parallel_timed_processes": 1,
                 "command_processes": len(commands),
                 "measured_samples": len(measured),
                 "preflight_available_disk_bytes": preflight["available_disk_bytes"],
                 "pre_timing_available_disk_bytes": pre_timing["available_disk_bytes"],
                 "post_timing_available_disk_bytes": post["available_disk_bytes"],
                 "lease_released": lease_record["released"]}
    if elapsed > manifest["resources"]["maximum_total_seconds"] or \
            rss > manifest["resources"]["maximum_child_rss_bytes"] or \
            resources["output_bytes_before_index"] > \
            manifest["resources"]["maximum_output_bytes"]:
        raise RuntimeError("resource ceiling exceeded")
    write_json(output / "resources.json", resources)
    (output / "operator-report.md").write_text(
        "# Remote backref-cost workspace remote v2 A/B operator report\n\n"
        f"Source: `{commit}`  \nCorrectness cells: {len(correctness)}  \n"
        f"Raw commands: {len(commands)}  \nRaw sample rows: {len(samples)}  \n"
        f"Frozen automated decision: **{evaluation['decision']}**  \n"
        "Only this v2 matrix is eligible. Timing was remote, serial, "
        "recorder-free, and end-to-end only.\n")
    write_hash_index(manifest, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("preflight")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        if args.command == "validate":
            commit = validate_source(manifest)
            print(json.dumps({"schema": manifest["schema"],
                              "source_commit": commit,
                              "manifest_sha256": sha256(MANIFEST_PATH),
                              "operator_sha256": sha256(Path(__file__))},
                             sort_keys=True))
        elif args.command == "preflight":
            validate_source(manifest)
            print(json.dumps(host_preflight(manifest), sort_keys=True))
        else:
            execute(manifest, args.output)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
