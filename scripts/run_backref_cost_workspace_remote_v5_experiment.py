#!/usr/bin/env python3
"""Frozen remote-v5 host operator for the backref-cost workspace remote v5 A/B."""

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
import stat
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "backref_cost_workspace_remote_v5_manifest.json"


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
            check: bool = True, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
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
                      inject: bool = False,
                      benchmark_session: bool = False) -> dict[str, str]:
    host = manifest["remote_host"]
    env = {
        "HOME": str(Path.home()),
        "PATH": manifest["toolchain"]["environment"]["PATH"],
        "LANG": manifest["toolchain"]["environment"]["LANG"],
        "LC_ALL": manifest["toolchain"]["environment"]["LC_ALL"],
        "TMPDIR": os.environ["TMPDIR"],
        "USER": os.environ["USER"],
        "LOGNAME": os.environ["LOGNAME"],
        "DEVELOPER_DIR": host["developer_dir"],
        "SDKROOT": host["sdk_path"],
    }
    candidate = manifest["candidate"]
    for name in manifest["forbidden_environment"]:
        env.pop(name, None)
    if benchmark_session:
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


def toolchain_admission(manifest: dict,
                        overrides: dict[str, str] | None = None) -> dict:
    """Admit only the frozen, explicit Apple/make toolchain."""
    frozen = manifest["toolchain"]
    observed_environment = {
        name: os.environ.get(name) for name in frozen["environment"]
    }
    if observed_environment != frozen["environment"]:
        raise RuntimeError("noninteractive toolchain environment mismatch")
    records = {}
    overrides = overrides or {}
    for name, expected in frozen["executables"].items():
        supplied = Path(overrides.get(name, expected["path"]))
        if not supplied.is_absolute() or not os.path.lexists(supplied):
            raise RuntimeError(f"required tool is absent: {name}")
        mode = os.lstat(supplied).st_mode
        path_type = "symlink" if stat.S_ISLNK(mode) else (
            "regular" if stat.S_ISREG(mode) else "other")
        canonical = supplied.resolve(strict=True)
        if (str(supplied) != expected["path"] or
                str(canonical) != expected["canonical_path"] or
                path_type != expected["path_type"] or
                not canonical.is_file() or
                not os.access(canonical, os.X_OK) or
                sha256(canonical) != expected["sha256"]):
            raise RuntimeError(f"wrong executable admitted for {name}")
        version = command(expected["version_argv"], check=False)
        combined = ((version.stdout or "") +
                    (version.stderr or "" if version.stderr else ""))
        lines = combined.strip().splitlines()
        if version.returncode not in expected["version_exit_codes"]:
            raise RuntimeError(f"version probe failed for {name}")
        if "version_lines" in expected and lines != expected["version_lines"]:
            raise RuntimeError(f"version output mismatch for {name}")
        records[name] = {
            "path": str(supplied), "canonical_path": str(canonical),
            "path_type": path_type, "sha256": sha256(canonical),
            "version_argv": expected["version_argv"],
            "version_exit_code": version.returncode, "version_lines": lines,
        }
    xcrun = frozen["executables"]["xcrun"]["path"]
    resolved = {
        name: capture([xcrun, "--find", name])
        for name in ("clang", "clang++", "ar", "ranlib")
    }
    sdk_path = capture([xcrun, "--sdk", "macosx", "--show-sdk-path"])
    sdk_version = capture(
        [xcrun, "--sdk", "macosx", "--show-sdk-version"])
    developer_dir = capture(["/usr/bin/xcode-select", "-p"])
    if (resolved != frozen["xcrun_resolved"] or
            sdk_path != manifest["remote_host"]["sdk_path"] or
            sdk_version != manifest["remote_host"]["sdk_version"] or
            developer_dir != manifest["remote_host"]["developer_dir"]):
        raise RuntimeError("effective compiler, SDK, or developer dir mismatch")
    compiler = frozen["executables"]["clang"]["path"]
    with tempfile.TemporaryDirectory(prefix="remote-v5-toolchain-probe-") as raw:
        object_path = Path(raw) / "probe.o"
        probe = command([
            compiler, "-arch", "arm64", "-isysroot", sdk_path,
            "-x", "c", "-c", "/dev/null", "-o", str(object_path),
        ], check=False)
        if probe.returncode != 0 or not object_path.is_file():
            raise RuntimeError("effective compiler/SDK probe failed")
        probe_hash = sha256(object_path)
    return {
        "schema": manifest["schemas"]["toolchain"],
        "status": "admitted", "environment": observed_environment,
        "executables": records, "xcrun_resolved": resolved,
        "effective_compiler": compiler, "effective_sdk_path": sdk_path,
        "effective_sdk_version": sdk_version,
        "effective_developer_dir": developer_dir,
        "compiler_sdk_probe_sha256": probe_hash,
        "exact_build_commands": manifest["builds"]["exact_commands"],
        "cmake_used": False, "homebrew_used": False,
        "host_or_global_path_changed": False,
    }


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
        "_experiment_runner", "cache_size_serial_sweep_runner",
        "cache_size_single_pass_slab_runner", "benchmark_metal",
        "metal_benchmark", "metal_encode_batch_experiment",
        "metal_import_bench", "nvidia-smi", "nvcc", "cuda-memcheck",
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
    xcrun = manifest["toolchain"]["executables"]["xcrun"]["path"]
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("remote host must be Darwin arm64")
    compiler_path = capture([xcrun, "--find", "clang"])
    compiler_version = capture([compiler_path, "--version"])
    sdk_path = capture([xcrun, "--sdk", "macosx", "--show-sdk-path"])
    sdk_version = capture([xcrun, "--sdk", "macosx", "--show-sdk-version"])
    developer_dir = capture(["/usr/bin/xcode-select", "-p"])
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
        "noninteractive_path": os.environ.get("PATH"),
        "low_power_mode_pmset_off": "lowpowermode         0" in custom,
        "low_power_mode_profiler_off": bool(ac_entries) and all(
            row.get("LowPowerMode") == "No" for row in ac_entries),
        "ac_power_effective": "AC Power" in battery and bool(ac_entries) and all(
            row.get("Current Power Source") == "TRUE" for row in ac_entries),
        "pmset_batt": battery, "pmset_custom": custom,
        "pmset_thermal": thermal, "system_profiler_power": power_json,
        "process_isolation": processes,
    }


def configure_and_build(manifest: dict, temporary: Path, log,
                        output: Path, commit: str) -> dict[str, Path]:
    builds, executed = {}, []
    build_env = clean_environment(manifest, "baseline")
    tools = manifest["toolchain"]["executables"]
    host = manifest["remote_host"]
    build_env.update({
        "CC": tools["clang"]["path"], "CXX": tools["clang++"]["path"],
        "AR": tools["ar"]["path"], "RANLIB": tools["ranlib"]["path"],
    })

    def run_logged(argv: list[str], cwd: Path = ROOT,
                   timeout: int = 1200) -> None:
        executed.append({"cwd": str(cwd), "argv": argv})
        log.write(("CWD " + str(cwd) + "\nCOMMAND " +
                   " ".join(argv) + "\n").encode())
        log.flush()
        command(argv, env=build_env, timeout=timeout, stdout=log, cwd=cwd)

    for variant in ("baseline", "candidate"):
        build = temporary / f"build-{variant}"
        run_logged([tools["git"]["path"], "clone", "--no-hardlinks",
                    "--no-checkout", str(ROOT), str(build)])
        run_logged([tools["git"]["path"], "checkout", "--detach",
                    commit], cwd=build)
        make = [
            tools["make"]["path"], "-f", "makefile.unix", "-j4",
            f"CC={tools['clang']['path']}", f"CXX={tools['clang++']['path']}",
            f"AR={tools['ar']['path']}", f"RANLIB={tools['ranlib']['path']}",
            f"CFLAGS=-O3 -DNDEBUG -arch arm64 -isysroot {host['sdk_path']}",
            f"LDFLAGS=-arch arm64 -isysroot {host['sdk_path']}",
            "EXTRA_FLAGS=", "DWEBP_LIBS=", "CWEBP_LIBS=", "GIF_LIBS=",
            "WEBP_ENABLE_METAL=0",
            "WEBP_BACKREF_COST_WORKSPACE_REMOTE_V5_DETERMINISTIC_BUILD=1",
            f"{manifest['candidate']['build_flag']}=" +
            ("1" if variant == "candidate" else "0"),
            "examples/cwebp", "examples/dwebp",
        ]
        if variant == "candidate":
            make.append("tools/" + manifest["candidate"]["runner_target"])
        run_logged(make, cwd=build)
        runner = build / "tools" / manifest["candidate"]["runner_target"]
        if variant == "baseline":
            argv = [
                tools["clang"]["path"], "-O3", "-DNDEBUG", "-arch", "arm64",
                "-isysroot", host["sdk_path"], f"-I{build}",
                str(build / manifest["candidate"]["runner"]),
                str(build / "src/libwebp.a"),
                str(build / "sharpyuv/libsharpyuv.a"), "-o", str(runner),
            ]
            run_logged(argv, cwd=build)
        required = [build / "examples/cwebp", build / "examples/dwebp", runner,
                    build / "src/libwebp.a", build / "sharpyuv/libsharpyuv.a"]
        if not all(path.is_file() for path in required):
            raise RuntimeError("deterministic make build omitted required output")
        builds[variant] = build
    write_json(output / "build-commands.json", {
        "schema": manifest["schemas"]["build"], "commands": executed,
        "outputs": {
            variant: {
                str(path.relative_to(build)): sha256(path)
                for path in (build / "examples/cwebp", build / "examples/dwebp",
                             build / "tools" /
                             manifest["candidate"]["runner_target"],
                             build / "src/libwebp.a",
                             build / "sharpyuv/libsharpyuv.a")
            } for variant, build in builds.items()
        },
    })
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
                    "baseline": (builds["baseline"] / "examples/cwebp",
                                 clean_environment(manifest, "baseline")),
                    "candidate_off": (builds["candidate"] / "examples/cwebp",
                                      clean_environment(manifest, "baseline")),
                    "candidate": (builds["candidate"] / "examples/cwebp",
                                  clean_environment(manifest, "candidate")),
                    "repeat": (builds["candidate"] / "examples/cwebp",
                               clean_environment(manifest, "candidate")),
                    "fallback": (builds["candidate"] / "examples/cwebp",
                                 clean_environment(manifest, "candidate", True)),
                    "default_env": (builds["baseline"] / "examples/cwebp",
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
                    command([str(builds["baseline"] / "examples/dwebp"), str(path),
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
                            runner = (builds[variant] / "tools" /
                                      manifest["candidate"]["runner_target"])
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
                                             env=clean_environment(
                                                 manifest, variant,
                                                 benchmark_session=True),
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


def record_stage(output: Path, stage: str) -> None:
    write_json(output / "operator-stage.json", {
        "schema": "libwebp-backref-cost-workspace-remote-v5-stage-v1",
        "stage": stage,
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def execute(manifest: dict, output: Path) -> None:
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")
    record_stage(output, "source-validation")
    commit = validate_source(manifest)
    if not output.is_absolute() or not output.is_dir():
        raise RuntimeError("controlled output directory is invalid")
    lease_path = Path(os.path.expanduser(manifest["resources"]["lease_path"]))
    lease_record = {"schema": manifest["schemas"]["lease"],
                    "path": str(lease_path), "acquired": False,
                    "released": False, "acquisition_attempted": False}
    write_json(output / "lease-record.json", lease_record)
    record_stage(output, "toolchain-admission")
    admitted_tools = toolchain_admission(manifest)
    write_json(output / "toolchain.json", admitted_tools)
    record_stage(output, "host-preflight")
    preflight = host_preflight(manifest, output, "preflight")
    write_json(output / "preflight.json", preflight)
    source_rows = [{"path": item["path"], "sha256": sha256(ROOT / item["path"])}
                   for item in manifest["frozen_artifacts"]]
    write_json(output / "source-hashes.json", {
        "schema": manifest["schemas"]["source_hashes"],
        "source_commit": commit, "manifest_sha256": sha256(MANIFEST_PATH),
        "frozen_artifacts": source_rows,
        "candidate_equivalence": manifest["candidate"]["equivalence"]})
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rss_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    try:
        with lease_path.open("a+") as lease:
            lease_record["acquisition_attempted"] = True
            write_json(output / "lease-record.json", lease_record)
            try:
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError("remote exclusive benchmark lease is held") from error
            lease_record["acquired"] = True
            lease_record["acquired_at_utc"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            write_json(output / "lease-record.json", lease_record)
            try:
                record_stage(output, "build")
                with tempfile.TemporaryDirectory(
                        prefix="backref-cost-workspace-remote-v5-build-") as raw:
                    temporary = Path(raw)
                    with (output / "build.log").open("wb") as log:
                        builds = configure_and_build(
                            manifest, temporary, log, output, commit)
                    record_stage(output, "corpus")
                    corpus, cases = generate_corpus(manifest, temporary)
                    record_stage(output, "correctness")
                    correctness = correctness_gate(
                        manifest, builds, corpus, cases, output)
                    record_stage(output, "pre-timing")
                    pre_timing = host_preflight(manifest, output, "pre-timing")
                    write_json(output / "pre-timing.json", pre_timing)
                    record_stage(output, "timing")
                    samples, commands = timed_matrix(
                        manifest, builds, corpus, cases, output)
                    record_stage(output, "post-timing")
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
    record_stage(output, "complete")
    (output / "operator-report.md").write_text(
        "# Remote backref-cost workspace remote v5 A/B operator report\n\n"
        f"Source: `{commit}`  \nCorrectness cells: {len(correctness)}  \n"
        f"Raw commands: {len(commands)}  \nRaw sample rows: {len(samples)}  \n"
        f"Frozen automated decision: **{evaluation['decision']}**  \n"
        "Only this v5 matrix is eligible. Timing was remote, serial, "
        "recorder-free, and end-to-end only.\n")


def controlled_run(output: Path) -> None:
    """Make every refusal after output admission archiveable and indexed."""
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute path")
    output.mkdir(parents=True)
    bootstrap_lease = {
        "schema": "libwebp-backref-cost-workspace-remote-v5-lease-v1",
        "path": None, "acquired": False, "released": False,
        "acquisition_attempted": False,
    }
    write_json(output / "lease-record.json", bootstrap_lease)
    manifest = None
    failure = None
    try:
        manifest = load_manifest()
        execute(manifest, output)
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, ValueError) as error:
        failure = error
        stage = None
        if (output / "operator-stage.json").is_file():
            try:
                stage = json.loads((output / "operator-stage.json").read_text())["stage"]
            except (OSError, KeyError, json.JSONDecodeError):
                stage = "stage-record-unreadable"
        write_json(output / "refusal.json", {
            "schema": "libwebp-backref-cost-workspace-remote-v5-refusal-v1",
            "status": "refused", "error_type": type(error).__name__,
            "reason": str(error), "stage": stage or "manifest-admission",
            "lease_record_present": (output / "lease-record.json").is_file(),
            "timing_samples_present": (output / "records.jsonl").is_file(),
            "controlled_exit": True,
        })
    status = "complete" if failure is None else "refused"
    write_json(output / "operator-status.json", {
        "schema": "libwebp-backref-cost-workspace-remote-v5-operator-status-v1",
        "status": status, "artifact_index_written": True,
        "controlled_exit": True,
    })
    artifact_schema = (manifest["schemas"]["artifact_hashes"] if manifest
                       else "libwebp-backref-cost-workspace-remote-v5-artifact-hashes-v1")
    rows = [{"path": str(path.relative_to(output)),
             "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "artifact-hashes.json"]
    write_json(output / "artifact-hashes.json",
               {"schema": artifact_schema, "artifacts": rows})
    if failure is not None:
        raise RuntimeError(
            "controlled remote-v5 refusal; indexed evidence is returnable") from failure


def rehearsal(manifest: dict, output: Path) -> None:
    """Untimed exact admission/build/correctness rehearsal; never leases/runs timing."""
    if os.environ.get("WEBP_BENCHMARK_SESSION") is not None:
        raise RuntimeError("rehearsal requires WEBP_BENCHMARK_SESSION unset")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("rehearsal output must be a new absolute path")
    output.mkdir(parents=True)
    commit = validate_source(manifest)
    process_record = process_snapshot(output, "rehearsal")
    admitted = toolchain_admission(manifest)
    fixture_results = {}
    fixtures = {
        "missing_make": {"make": "/nonexistent/remote-v5-fixture/make"},
        "wrong_make": {"make": manifest["toolchain"]["executables"]["git"]["path"]},
    }
    for name, override in fixtures.items():
        try:
            toolchain_admission(manifest, override)
        except RuntimeError as error:
            fixture_results[name] = {"refused": True, "reason": str(error)}
        else:
            raise RuntimeError(f"toolchain fixture was accepted: {name}")
    with tempfile.TemporaryDirectory(
            prefix="backref-cost-workspace-remote-v5-rehearsal-") as raw:
        temporary = Path(raw)
        with (output / "build.log").open("wb") as log:
            builds = configure_and_build(
                manifest, temporary, log, output, commit)
        corpus, cases = generate_corpus(manifest, temporary)
        correctness = correctness_gate(manifest, builds, corpus, cases, output)
    write_json(output / "lease-record.json", {
        "schema": manifest["schemas"]["lease"], "path": None,
        "acquisition_attempted": False, "acquired": False, "released": False,
    })
    write_json(output / "rehearsal.json", {
        "schema": manifest["schemas"]["rehearsal"], "status": "PASS",
        "source_commit": commit, "toolchain": admitted,
        "toolchain_refusal_fixtures": fixture_results,
        "process_isolation": process_record,
        "correctness_cells": len(correctness),
        "benchmark_session_present": False, "benchmark_lease_attempted": False,
        "timed_runner_invoked": False, "timed_samples": 0,
        "runner_directories_or_services_touched": False,
        "host_settings_changed": False, "global_path_changed": False,
    })
    write_hash_index(manifest, output)


def refusal_fixture(manifest: dict, output: Path, fixture: str) -> None:
    """Produce the exact minimal indexed evidence shape for an early refusal."""
    if os.environ.get("WEBP_BENCHMARK_SESSION") is not None:
        raise RuntimeError("refusal fixture requires benchmark session unset")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("refusal fixture output must be a new absolute path")
    output.mkdir(parents=True)
    validate_source(manifest)
    write_json(output / "lease-record.json", {
        "schema": manifest["schemas"]["lease"], "path": None,
        "acquisition_attempted": False, "acquired": False, "released": False,
    })
    overrides = {
        "missing": {"make": "/nonexistent/remote-v5-fixture/make"},
        "wrong": {"make": manifest["toolchain"]["executables"]["git"]["path"]},
    }
    if fixture not in overrides:
        raise RuntimeError("unknown refusal fixture")
    try:
        toolchain_admission(manifest, overrides[fixture])
    except RuntimeError as error:
        write_json(output / "refusal.json", {
            "schema": manifest["schemas"]["refusal"], "status": "refused",
            "error_type": type(error).__name__, "reason": str(error),
            "stage": "toolchain-admission", "lease_record_present": True,
            "timing_samples_present": False, "controlled_exit": True,
        })
    else:
        raise RuntimeError("toolchain refusal fixture was accepted")
    write_json(output / "operator-status.json", {
        "schema": manifest["schemas"]["operator_status"], "status": "refused",
        "artifact_index_written": True, "controlled_exit": True,
    })
    write_hash_index(manifest, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("preflight")
    rehearsal_parser = sub.add_parser("rehearse")
    rehearsal_parser.add_argument("output", type=Path)
    fixture_parser = sub.add_parser("refusal-fixture")
    fixture_parser.add_argument("output", type=Path)
    fixture_parser.add_argument("fixture", choices=("missing", "wrong"))
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            controlled_run(args.output)
        else:
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
        elif args.command == "rehearse":
            rehearsal(manifest, args.output)
        elif args.command == "refusal-fixture":
            refusal_fixture(manifest, args.output, args.fixture)
        elif args.command == "run":
            pass
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
