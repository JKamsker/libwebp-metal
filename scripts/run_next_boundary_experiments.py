#!/usr/bin/env python3
"""Frozen operator for the predictor-boundary and backref-exact experiments."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "next_boundary_experiments_v1.json"
LEASE_PATH = Path("/tmp/libwebp-metal-next-boundary.lock")


def parse_vm_stat_available_bytes(output: str) -> int:
    """Returns conservative reclaimable bytes from Darwin's vm_stat output."""
    header = re.search(r"page size of ([0-9]+) bytes", output)
    if header is None:
        raise ValueError("vm_stat page size is missing")
    page_size = int(header.group(1))
    pages = {}
    for line in output.splitlines():
        match = re.fullmatch(r"([^:]+):\s*([0-9]+)\.?", line.strip())
        if match is not None:
            pages[match.group(1)] = int(match.group(2))
    fields = ("Pages free", "Pages inactive", "Pages speculative")
    missing = [field for field in fields if field not in pages]
    if page_size <= 0 or missing:
        detail = ", ".join(missing) if missing else "invalid page size"
        raise ValueError(f"vm_stat available-page data is incomplete: {detail}")
    # Purgeable pages can overlap inactive pages, so do not count them again.
    return page_size * sum(pages[field] for field in fields)


def available_memory_bytes() -> int:
    """Returns available memory, failing closed if the host cannot report it."""
    try:
        page_count = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if page_count < 0 or page_size <= 0:
            raise ValueError("sysconf returned an invalid page count or size")
        return page_count * page_size
    except (OSError, ValueError) as error:
        if platform.system() != "Darwin":
            raise SystemExit(
                f"free-memory prerequisite unavailable: {error}") from error
    result = subprocess.run(
        ["vm_stat"], cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"free-memory prerequisite unavailable: vm_stat exited "
            f"{result.returncode}")
    try:
        return parse_vm_stat_available_bytes(result.stdout)
    except ValueError as error:
        raise SystemExit(
            f"free-memory prerequisite unavailable: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    corpus = manifest["corpus"]
    for key, expected in (("generator", corpus["generator_sha256"]),
                          ("manifest", corpus["manifest_sha256"])):
        actual = sha256(ROOT / corpus[key])
        if actual != expected:
            raise SystemExit(f"frozen corpus {key} hash mismatch: {actual}")
    return manifest


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_source(manifest: dict, require_expected: bool) -> str:
    commit = git("rev-parse", "HEAD")
    expected = os.environ.get(manifest["required_expected_commit_environment"])
    if require_expected and not expected:
        raise SystemExit("WEBP_EXPECTED_DESIGNER_COMMIT is required")
    if expected and commit != expected:
        raise SystemExit(f"HEAD {commit} does not match frozen handoff {expected}")
    if git("status", "--porcelain"):
        raise SystemExit("operator requires a completely clean worktree")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", manifest["base_commit"], commit],
        cwd=ROOT, check=False)
    if ancestry.returncode != 0:
        raise SystemExit("designer commit is not descended from the frozen base")
    return commit


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def write_artifact_hashes(output: Path) -> None:
    artifacts = {str(path.relative_to(output)): sha256(path)
                 for path in sorted(output.rglob("*")) if path.is_file()
                 and path.name != "artifact-hashes.json"}
    write_json(output / "artifact-hashes.json", artifacts)


def diagnostic(argv: list[str]) -> str:
    return subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False).stdout.strip()


def sanitize_hardware(value: object) -> object:
    if isinstance(value, dict):
        return {key: sanitize_hardware(item) for key, item in value.items()
                if not any(token in key.lower() for token in ("serial", "uuid", "udid"))}
    if isinstance(value, list):
        return [sanitize_hardware(item) for item in value]
    return value


def run_checked(argv: list[str], *, env: dict[str, str] | None = None,
                timeout: int = 240, stdout=None, stderr=None) -> None:
    result = subprocess.run(argv, cwd=ROOT, env=env, timeout=timeout,
                            stdout=stdout, stderr=stderr, check=False)
    if result.returncode != 0:
        raise SystemExit(f"prerequisite failed ({result.returncode}): {' '.join(argv)}")


def build_and_generate(experiment: dict, output: Path, manifest: dict) -> Path:
    run_checked(["make", "-f", "makefile.unix", "clean"], timeout=240)
    run_checked([
        "make", "-f", "makefile.unix", "-j4", "WEBP_ENABLE_METAL=1",
        f"{experiment['build_flag']}=1", "examples/cwebp", "examples/dwebp",
    ], timeout=600)
    corpus_dir = output / "corpus"
    run_checked([sys.executable, manifest["corpus"]["generator"],
                 "--output", str(corpus_dir), "--verify"], timeout=600)
    return corpus_dir


def experiment_env(experiment: dict, output: Path, case_id: str,
                   lifecycle: str, control: bool, inject_failure: bool) -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT", "WEBP_BACKREF_EXACT_EXPERIMENT",
        "WEBP_PREDICTOR_BOUNDARY_CONTROL", "WEBP_BACKREF_EXACT_CONTROL",
        "WEBP_PREDICTOR_BOUNDARY_INJECT_RECORD_FAILURE",
        "WEBP_BACKREF_EXACT_INJECT_RECORD_FAILURE",
    ):
        env.pop(name, None)
    env.update({
        "WEBP_BENCHMARK_SESSION": "exclusive",
        "WEBP_ACCELERATOR": "metal", "WEBP_METAL": "1",
        "WEBP_METAL_MIN_PIXELS": "0", "WEBP_METAL_HASH": "1",
        "WEBP_METAL_HASH_MIN_PIXELS": "0",
        experiment["runtime_flag"]: "1",
        experiment["output_flag"]: str(
            output / ("correctness-records.jsonl"
                      if lifecycle == "correctness" else "records.jsonl")),
        "WEBP_BOUNDARY_RUN_ID": output.name,
        "WEBP_BOUNDARY_CASE_ID": case_id,
        "WEBP_BOUNDARY_LIFECYCLE": lifecycle,
    })
    if control:
        env[experiment["control_flag"]] = "1"
    if inject_failure:
        env[experiment["failure_injection_flag"]] = "1"
    return env


def encode_command(experiment: dict, input_path: Path, method: int,
                   repetitions: int, output_path: Path | None = None) -> list[str]:
    command = [str(ROOT / "examples" / "cwebp"), "-quiet", "-lossless", "-exact",
               "-q", "75", "-m", str(method)]
    if repetitions != 1:
        command += [experiment["repetition_option"], str(repetitions)]
    if output_path is not None:
        command += ["-o", str(output_path)]
    command.append(str(input_path))
    return command


def correctness_gate(experiment: dict, corpus: Path, output: Path,
                     methods: list[int]) -> None:
    rows = []
    with tempfile.TemporaryDirectory(prefix="webp-boundary-correctness-") as temporary:
        check_dir = Path(temporary)
        for case_id in experiment["correctness_cases"]:
            input_path = corpus / f"{case_id}.ppm"
            for method in methods:
                hashes = []
                for label, control, inject in (("record", False, False),
                                               ("control", True, False),
                                               ("fallback", False, True)):
                    encoded = check_dir / f"{case_id}-m{method}-{label}.webp"
                    env = experiment_env(experiment, output, case_id, "correctness",
                                         control, inject)
                    run_checked(encode_command(experiment, input_path, method, 1, encoded),
                                env=env, timeout=240, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                    hashes.append(sha256(encoded))
                if len(set(hashes)) != 1:
                    raise SystemExit(f"correctness/fallback mismatch: {case_id} m{method}")
                decoded = check_dir / f"{case_id}-m{method}-decoded.ppm"
                run_checked([str(ROOT / "examples" / "dwebp"), "-quiet", "-ppm",
                             "-o", str(decoded),
                             str(check_dir / f"{case_id}-m{method}-record.webp")],
                            timeout=240, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
                if sha256(decoded) != sha256(input_path):
                    raise SystemExit(f"decoded-pixel mismatch: {case_id} m{method}")
                rows.append({"case_id": case_id, "method": method,
                             "bitstream_sha256": hashes[0], "deterministic": True,
                             "decoded_input_equal": True,
                             "transactional_fallback": True})
    write_json(output / "correctness.json", {"schema": "libwebp-boundary-correctness-v1",
                                               "rows": rows, "ok": True})


def timed_matrix(experiment_name: str, experiment: dict, corpus: Path,
                 output: Path, manifest: dict) -> None:
    matrix_started = time.monotonic()
    commands_path = output / "commands.jsonl"
    stderr_dir = output / "stderr"
    stderr_dir.mkdir()
    sequence = 0
    cases = [(case, "tune") for case in experiment["tune_cases"]]
    cases += [(case, "holdout") for case in experiment["holdout_cases"]]
    for case_id, role in cases:
        for method in manifest["common"]["methods"]:
            for lifecycle in ("cold", "warm"):
                spec = manifest["common"]["lifecycles"][lifecycle]
                repetitions = spec["encodes_per_process"]
                for pair in range(spec["process_pairs"]):
                    order = manifest["common"]["pair_order"][pair].split("-")
                    for variant in order:
                        control = variant == "control"
                        sequence += 1
                        stderr_path = stderr_dir / f"{sequence:04d}.log"
                        command = encode_command(experiment, corpus / f"{case_id}.ppm",
                                                 method, repetitions)
                        env = experiment_env(experiment, output, case_id, lifecycle,
                                             control, False)
                        before = time.monotonic_ns()
                        with stderr_path.open("wb") as err:
                            run_checked(command, env=env,
                                        timeout=manifest["common"]["resource_ceilings"]["command_timeout_seconds"],
                                        stdout=subprocess.DEVNULL, stderr=err)
                        elapsed = time.monotonic_ns() - before
                        row = {"schema": "libwebp-boundary-command-v1",
                               "sequence": sequence, "experiment": experiment_name,
                               "case_id": case_id, "tune_holdout": role,
                               "method": method, "lifecycle": lifecycle,
                               "pair": pair, "variant": variant,
                               "repetitions": repetitions, "argv": command,
                               "elapsed_ns": elapsed,
                               "stderr": str(stderr_path.relative_to(output)),
                               "stderr_sha256": sha256(stderr_path)}
                        with commands_path.open("a", encoding="utf-8") as sink:
                            sink.write(json.dumps(row, sort_keys=True) + "\n")
                        rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
                        if platform.system() != "Darwin":
                            rss *= 1024
                        if rss > manifest["common"]["resource_ceilings"]["maximum_observed_rss_bytes"]:
                            raise SystemExit("observed RSS ceiling exceeded")
                        if time.monotonic() - matrix_started > \
                                manifest["common"]["resource_ceilings"]["maximum_total_duration_seconds_per_experiment"]:
                            raise SystemExit("experiment duration ceiling exceeded")
                        if sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) > \
                                manifest["common"]["resource_ceilings"]["maximum_output_bytes"]:
                            raise SystemExit("evidence output ceiling exceeded")


def operator_run(name: str, output: Path, manifest: dict) -> None:
    experiment = manifest["experiments"][name]
    if os.environ.get(experiment["runtime_flag"]) != "1":
        raise SystemExit(f"refusing timed run: {experiment['runtime_flag']}=1 is required")
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise SystemExit("refusing timed run: WEBP_BENCHMARK_SESSION=exclusive is required")
    commit = validate_source(manifest, require_expected=True)
    if output.exists():
        raise SystemExit("refusing to overwrite evidence output")
    ceilings = manifest["common"]["resource_ceilings"]
    free_memory = available_memory_bytes()
    if free_memory < ceilings["minimum_free_memory_bytes"]:
        raise SystemExit("free-memory prerequisite failed")
    if shutil.disk_usage(output.parent).free < ceilings["maximum_output_bytes"] * 2:
        raise SystemExit("free-disk prerequisite failed")
    lease = LEASE_PATH.open("w")
    try:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lease.close()
        raise SystemExit("exclusive benchmark lease is already held")
    started = time.time()
    completed = False
    failure = None
    try:
        output.mkdir(parents=True)
        write_json(output / "preflight.json", {
            "schema": "libwebp-boundary-preflight-v1", "commit": commit,
            "manifest_sha256": sha256(MANIFEST_PATH), "experiment": name,
            "lease": str(LEASE_PATH), "session": "exclusive",
            "started_unix": started,
        })
        profiler = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        if profiler.returncode != 0 or "metal" not in profiler.stdout.lower():
            raise SystemExit("physical Metal device prerequisite failed")
        display_profile = json.loads(profiler.stdout)
        devices = display_profile.get("SPDisplaysDataType", [])
        if len(devices) != 1:
            raise SystemExit(
                f"expected one physical Metal device, found {len(devices)}")
        compiler = diagnostic(["cc", "--version"])
        sdk = diagnostic(["xcrun", "--show-sdk-version"])
        write_json(output / "machine.json", {
            "platform": platform.platform(), "machine": platform.machine(),
            "python": platform.python_version(),
            "processor": platform.processor(), "sdk": sdk,
            "compiler": compiler,
            "display_profile": sanitize_hardware(display_profile),
            "free_memory_bytes": free_memory,
            "load_average": os.getloadavg(),
            "power": diagnostic(["pmset", "-g", "batt"]),
            "thermal": diagnostic(["pmset", "-g", "therm"]),
        })
        with tempfile.TemporaryDirectory(prefix="webp-boundary-corpus-") as temporary:
            corpus = build_and_generate(experiment, Path(temporary), manifest)
            correctness_gate(experiment, corpus, output, manifest["common"]["methods"])
            timed_matrix(name, experiment, corpus, output, manifest)
        completed = True
    except BaseException as error:
        failure = f"{type(error).__name__}: {error}"
        if output.exists():
            write_json(output / "failure.json", {
                "schema": "libwebp-boundary-failure-v1",
                "experiment": name, "commit": commit, "failure": failure,
            })
            (output / "operator-report.md").write_text(
                f"# Frozen operator handoff\n\nExperiment: `{name}`  \n"
                f"Commit: `{commit}`  \nStatus: failed; no parameters were changed.  \n"
                f"Failure: `{failure}`\n", encoding="utf-8")
        raise
    finally:
        fcntl.flock(lease, fcntl.LOCK_UN)
        lease.close()
        if output.exists():
            rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            if platform.system() != "Darwin":
                rss *= 1024
            write_json(output / "resource-notes.json", {
                "elapsed_seconds": time.time() - started,
                "maximum_observed_rss_bytes": rss,
                "ending_load_average": os.getloadavg(),
                "ending_power": diagnostic(["pmset", "-g", "batt"]),
                "ending_thermal": diagnostic(["pmset", "-g", "therm"]),
                "lease_released": True, "completed": completed,
                "failure": failure,
            })
            if not completed:
                write_artifact_hashes(output)
    (output / "operator-report.md").write_text(
        f"# Frozen operator handoff\n\nExperiment: `{name}`  \nCommit: `{commit}`  \n"
        f"Manifest: `{sha256(MANIFEST_PATH)}`  \nProtocol completed without interpretation.\n",
        encoding="utf-8")
    write_artifact_hashes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    run = sub.add_parser("run")
    run.add_argument("experiment", choices=("predictor_boundary", "backref_exact"))
    run.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = load_manifest()
    if args.command == "validate":
        if os.environ.get("WEBP_BENCHMARK_SESSION") == "exclusive":
            raise SystemExit("validate refuses an exclusive benchmark session")
        print(json.dumps({"schema": manifest["schema"],
                          "manifest_sha256": sha256(MANIFEST_PATH),
                          "experiments": sorted(manifest["experiments"])}, sort_keys=True))
        return 0
    operator_run(args.experiment, args.output.resolve(), manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
