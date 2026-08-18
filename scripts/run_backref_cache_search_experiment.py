#!/usr/bin/env python3
"""Frozen operator for the focused back-reference cache-search experiment."""

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
MANIFEST_PATH = ROOT / "scripts" / "backref_cache_search_experiment_v1.json"
LEASE_PATH = Path("/tmp/libwebp-metal-next-boundary.lock")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["common"]["lease_path"] != str(LEASE_PATH):
        raise SystemExit("frozen lease path does not match operator")
    corpus = manifest["corpus"]
    for key, expected in (("generator", corpus["generator_sha256"]),
                          ("manifest", corpus["manifest_sha256"])):
        actual = sha256(ROOT / corpus[key])
        if actual != expected:
            raise SystemExit(f"frozen corpus {key} hash mismatch: {actual}")
    publication = json.loads(
        (ROOT / corpus["manifest"]).read_text(encoding="utf-8"))
    actual_hashes = {row["case_id"]: row["sha256"]
                     for row in publication["cases"]}
    if actual_hashes != corpus["correctness_input_hashes"]:
        raise SystemExit("frozen publication case hashes do not match manifest")
    return manifest


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_source(manifest: dict) -> str:
    commit = git("rev-parse", "HEAD")
    variable = manifest["required_expected_commit_environment"]
    expected = os.environ.get(variable)
    if not expected:
        raise SystemExit(f"{variable} is required")
    if commit != expected:
        raise SystemExit(f"HEAD {commit} does not match frozen handoff {expected}")
    if git("status", "--porcelain"):
        raise SystemExit("operator requires a completely clean worktree")
    if subprocess.run(["git", "merge-base", "--is-ancestor",
                       manifest["base_commit"], commit], cwd=ROOT,
                      check=False).returncode != 0:
        raise SystemExit("designer commit is not descended from the frozen base")
    return commit


def parse_vm_stat_available_bytes(output: str) -> int:
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
    return page_size * sum(pages[field] for field in fields)


def available_memory_bytes() -> int:
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
    result = subprocess.run(["vm_stat"], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        raise SystemExit("free-memory prerequisite unavailable: vm_stat failed")
    try:
        return parse_vm_stat_available_bytes(result.stdout)
    except ValueError as error:
        raise SystemExit(
            f"free-memory prerequisite unavailable: {error}") from error


def diagnostic(argv: list[str]) -> str:
    return subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False).stdout.strip()


def sanitize_hardware(value: object) -> object:
    if isinstance(value, dict):
        return {key: sanitize_hardware(item) for key, item in value.items()
                if not any(token in key.lower()
                           for token in ("serial", "uuid", "udid"))}
    if isinstance(value, list):
        return [sanitize_hardware(item) for item in value]
    return value


def run_checked(argv: list[str], *, env: dict[str, str] | None = None,
                timeout: int = 240, stdout=None, stderr=None) -> None:
    result = subprocess.run(argv, cwd=ROOT, env=env, timeout=timeout,
                            stdout=stdout, stderr=stderr, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"prerequisite failed ({result.returncode}): {' '.join(argv)}")


def experiment_env(manifest: dict, output: Path, case_id: str,
                   lifecycle: str, control: bool,
                   inject_failure: bool) -> dict[str, str]:
    experiment = manifest["experiment"]
    env = os.environ.copy()
    names = [experiment[key] for key in (
        "runtime_flag", "control_flag", "output_flag",
        "failure_injection_flag", "run_id_flag", "case_id_flag",
        "lifecycle_flag")]
    for name in names:
        env.pop(name, None)
    env.update({
        "WEBP_BENCHMARK_SESSION": "exclusive",
        "WEBP_ACCELERATOR": "metal",
        "WEBP_METAL": "1",
        "WEBP_METAL_MIN_PIXELS": "0",
        "WEBP_METAL_HASH": "1",
        "WEBP_METAL_HASH_MIN_PIXELS": "0",
        experiment["runtime_flag"]: "1",
        experiment["output_flag"]: str(
            output / ("correctness-records.jsonl"
                      if lifecycle == "correctness" else "records.jsonl")),
        experiment["run_id_flag"]: output.name,
        experiment["case_id_flag"]: case_id,
        experiment["lifecycle_flag"]: lifecycle,
    })
    if control:
        env[experiment["control_flag"]] = "1"
    if inject_failure:
        env[experiment["failure_injection_flag"]] = "1"
    return env


def encode_command(manifest: dict, input_path: Path, method: int,
                   repetitions: int,
                   output_path: Path | None = None) -> list[str]:
    experiment = manifest["experiment"]
    command = [str(ROOT / "examples" / "cwebp"), "-quiet", "-lossless",
               "-exact", "-q", "75", "-m", str(method)]
    if repetitions != 1:
        command += [experiment["repetition_option"], str(repetitions)]
    if output_path is not None:
        command += ["-o", str(output_path)]
    command.append(str(input_path))
    return command


def build_and_generate(manifest: dict, temporary: Path,
                       output: Path) -> Path:
    experiment = manifest["experiment"]
    with (output / "build.log").open("wb") as log:
        run_checked(["make", "-f", "makefile.unix", "clean"],
                    timeout=240, stdout=log, stderr=subprocess.STDOUT)
        run_checked(["make", "-f", "makefile.unix", "-j4",
                     "WEBP_ENABLE_METAL=1",
                     f"{experiment['build_flag']}=1", "examples/cwebp",
                     "examples/dwebp"], timeout=600, stdout=log,
                    stderr=subprocess.STDOUT)
    corpus = temporary / "corpus"
    run_checked([sys.executable, manifest["corpus"]["generator"],
                 "--output", str(corpus), "--verify"], timeout=600)
    for case_id, expected in manifest["corpus"][
            "correctness_input_hashes"].items():
        actual = sha256(corpus / f"{case_id}.ppm")
        if actual != expected:
            raise SystemExit(f"generated input hash mismatch: {case_id}")
    return corpus


def correctness_gate(manifest: dict, corpus: Path, output: Path) -> None:
    experiment = manifest["experiment"]
    rows = []
    with tempfile.TemporaryDirectory(
            prefix="webp-cache-search-correctness-") as temporary:
        check_dir = Path(temporary)
        for case_id in experiment["correctness_cases"]:
            input_path = corpus / f"{case_id}.ppm"
            for method in manifest["common"]["methods"]:
                hashes = []
                variants = (
                    ("record-a", False, False, None),
                    ("record-b", False, False, None),
                    ("control", True, False, None),
                    ("injected-failure", False, True, None),
                    ("open-failure", False, False,
                     check_dir / "missing" / "record.jsonl"),
                )
                for label, control, inject, bad_output in variants:
                    encoded = check_dir / f"{case_id}-m{method}-{label}.webp"
                    env = experiment_env(manifest, output, case_id,
                                         "correctness", control, inject)
                    if bad_output is not None:
                        env[experiment["output_flag"]] = str(bad_output)
                    run_checked(encode_command(manifest, input_path, method, 1,
                                               encoded), env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                    hashes.append(sha256(encoded))
                if len(set(hashes)) != 1:
                    raise SystemExit(
                        f"correctness/fallback mismatch: {case_id} m{method}")
                decoded = check_dir / f"{case_id}-m{method}-decoded.ppm"
                run_checked([str(ROOT / "examples" / "dwebp"), "-quiet",
                             "-ppm", "-o", str(decoded),
                             str(check_dir /
                                 f"{case_id}-m{method}-record-a.webp")],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
                if sha256(decoded) != sha256(input_path):
                    raise SystemExit(f"decoded-pixel mismatch: {case_id} m{method}")
                rows.append({
                    "case_id": case_id,
                    "method": method,
                    "bitstream_sha256": hashes[0],
                    "repeated_record_deterministic": True,
                    "decoded_input_equal": True,
                    "control_equal": True,
                    "injected_record_failure_transactional": True,
                    "recorder_open_failure_transactional": True,
                })
    write_json(output / "correctness.json", {
        "schema": experiment["correctness_schema"],
        "rows": rows,
        "ok": True,
    })


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as sink:
        sink.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line]


def validate_inventory(manifest: dict, output: Path) -> None:
    experiment = manifest["experiment"]
    expected = manifest["common"]["expected_inventory"]
    commands = read_jsonl(output / "commands.jsonl")
    records = read_jsonl(output / "records.jsonl")
    correctness_records = read_jsonl(output / "correctness-records.jsonl")
    correctness = json.loads(
        (output / "correctness.json").read_text(encoding="utf-8"))
    if len(commands) != expected["command_rows"]:
        raise SystemExit("command inventory mismatch")
    if len(records) != expected["raw_timing_records"]:
        raise SystemExit("raw timing inventory mismatch")
    if len(correctness_records) != expected["raw_correctness_records"]:
        raise SystemExit("raw correctness inventory mismatch")
    if len(correctness["rows"]) != expected["correctness_summary_rows"]:
        raise SystemExit("correctness summary inventory mismatch")
    if not correctness.get("ok"):
        raise SystemExit("correctness summary is not successful")
    if [row.get("sequence") for row in commands] != list(
            range(1, expected["command_rows"] + 1)):
        raise SystemExit("command sequence mismatch")
    expected_order = []
    cases = [(case, "tune") for case in experiment["tune_cases"]]
    cases += [(case, "holdout") for case in experiment["holdout_cases"]]
    for case_id, role in cases:
        for method in manifest["common"]["methods"]:
            for lifecycle in ("cold", "warm"):
                spec = manifest["common"]["lifecycles"][lifecycle]
                for pair in range(spec["process_pairs"]):
                    for variant in manifest["common"]["pair_order"][
                            pair].split("-"):
                        expected_order.append((
                            case_id, role, method, lifecycle, pair, variant,
                            spec["encodes_per_process"]))
    actual_order = [(
        row.get("case_id"), row.get("tune_holdout"), row.get("method"),
        row.get("lifecycle"), row.get("pair"), row.get("variant"),
        row.get("repetitions")) for row in commands]
    if actual_order != expected_order:
        raise SystemExit("frozen command order mismatch")
    if any(row.get("schema") != experiment["command_schema"]
           for row in commands):
        raise SystemExit("command schema mismatch")
    if any(row.get("schema") != experiment["schema"] or not row.get("ok")
           for row in records + correctness_records):
        raise SystemExit("raw record schema or status mismatch")
    if correctness.get("schema") != experiment["correctness_schema"]:
        raise SystemExit("correctness schema mismatch")
    roles = {role: sum(row["sample_role"] == role for row in records)
             for role in ("cold", "warmup", "warm")}
    if roles != {
            "cold": expected["cold_records"],
            "warmup": expected["discarded_warmups"],
            "warm": expected["measured_warm_records"]}:
        raise SystemExit("raw sample-role inventory mismatch")
    measured = [row for row in records if row["sample_role"] != "warmup"]
    variants = {
        variant: sum(row["variant"] == variant for row in measured)
        for variant in ("record", "control")
    }
    if variants != {
            "record": expected["measured_record_variant"],
            "control": expected["measured_control_variant"]}:
        raise SystemExit("measured variant inventory mismatch")


def timed_matrix(manifest: dict, corpus: Path, output: Path) -> None:
    experiment = manifest["experiment"]
    common = manifest["common"]
    matrix_started = time.monotonic()
    commands_path = output / "commands.jsonl"
    stderr_dir = output / "stderr"
    stderr_dir.mkdir()
    sequence = 0
    cases = [(case, "tune") for case in experiment["tune_cases"]]
    cases += [(case, "holdout") for case in experiment["holdout_cases"]]
    for case_id, role in cases:
        for method in common["methods"]:
            for lifecycle in ("cold", "warm"):
                spec = common["lifecycles"][lifecycle]
                repetitions = spec["encodes_per_process"]
                for pair in range(spec["process_pairs"]):
                    order = common["pair_order"][pair].split("-")
                    for variant in order:
                        control = variant == "control"
                        sequence += 1
                        stderr_path = stderr_dir / f"{sequence:04d}.log"
                        command = encode_command(
                            manifest, corpus / f"{case_id}.ppm", method,
                            repetitions)
                        env = experiment_env(manifest, output, case_id,
                                             lifecycle, control, False)
                        before = time.monotonic_ns()
                        with stderr_path.open("wb") as err:
                            run_checked(
                                command, env=env,
                                timeout=common["resource_ceilings"][
                                    "command_timeout_seconds"],
                                stdout=subprocess.DEVNULL, stderr=err)
                        elapsed = time.monotonic_ns() - before
                        append_jsonl(commands_path, {
                            "schema": experiment["command_schema"],
                            "sequence": sequence,
                            "experiment": manifest["experiment_id"],
                            "case_id": case_id,
                            "tune_holdout": role,
                            "method": method,
                            "lifecycle": lifecycle,
                            "pair": pair,
                            "variant": variant,
                            "repetitions": repetitions,
                            "argv": command,
                            "experiment_environment": {
                                experiment["runtime_flag"]: "1",
                                experiment["control_flag"]:
                                    "1" if control else "0",
                                "WEBP_BENCHMARK_SESSION": "exclusive",
                                "WEBP_ACCELERATOR": "metal",
                            },
                            "elapsed_ns": elapsed,
                            "stderr": str(stderr_path.relative_to(output)),
                            "stderr_sha256": sha256(stderr_path),
                        })
                        rss = resource.getrusage(
                            resource.RUSAGE_CHILDREN).ru_maxrss
                        if platform.system() != "Darwin":
                            rss *= 1024
                        ceilings = common["resource_ceilings"]
                        if rss > ceilings["maximum_observed_rss_bytes"]:
                            raise SystemExit("observed RSS ceiling exceeded")
                        if time.monotonic() - matrix_started > ceilings[
                                "maximum_total_duration_seconds"]:
                            raise SystemExit("experiment duration ceiling exceeded")
                        size = sum(path.stat().st_size
                                   for path in output.rglob("*")
                                   if path.is_file())
                        if size > ceilings["maximum_output_bytes"]:
                            raise SystemExit("evidence output ceiling exceeded")


def write_artifact_hashes(output: Path) -> None:
    artifacts = {
        str(path.relative_to(output)): sha256(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "artifact-hashes.json"
    }
    write_json(output / "artifact-hashes.json", artifacts)


def operator_run(name: str, output: Path, manifest: dict) -> None:
    experiment = manifest["experiment"]
    if name != manifest["experiment_id"]:
        raise SystemExit("unknown experiment")
    if os.environ.get(experiment["runtime_flag"]) != "1":
        raise SystemExit(
            f"refusing timed run: {experiment['runtime_flag']}=1 is required")
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise SystemExit(
            "refusing timed run: WEBP_BENCHMARK_SESSION=exclusive is required")
    commit = validate_source(manifest)
    frozen_output = Path(manifest["common"]["evidence_output_path"])
    if output != frozen_output:
        raise SystemExit(f"evidence output must be exactly {frozen_output}")
    if output.exists():
        raise SystemExit("refusing to overwrite evidence output")
    output.parent.mkdir(parents=True, exist_ok=True)
    ceilings = manifest["common"]["resource_ceilings"]
    free_memory = available_memory_bytes()
    if free_memory < ceilings["minimum_free_memory_bytes"]:
        raise SystemExit("free-memory prerequisite failed")
    if shutil.disk_usage(output.parent).free < ceilings[
            "maximum_output_bytes"] * 2:
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
        output.mkdir()
        profiler = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        if profiler.returncode != 0 or "metal" not in profiler.stdout.lower():
            raise SystemExit("physical Metal device prerequisite failed")
        display_profile = json.loads(profiler.stdout)
        devices = display_profile.get("SPDisplaysDataType", [])
        if len(devices) != ceilings["single_physical_metal_device"]:
            raise SystemExit(
                f"expected one physical Metal device, found {len(devices)}")
        write_json(output / "preflight.json", {
            "schema": "libwebp-backref-cache-search-preflight-v1",
            "commit": commit,
            "manifest_sha256": sha256(MANIFEST_PATH),
            "experiment": name,
            "lease": str(LEASE_PATH),
            "session": "exclusive",
            "started_unix": started,
            "corpus_generator_sha256":
                manifest["corpus"]["generator_sha256"],
            "corpus_manifest_sha256":
                manifest["corpus"]["manifest_sha256"],
        })
        write_json(output / "machine.json", {
            "schema": "libwebp-backref-cache-search-machine-v1",
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "os": diagnostic(["sw_vers"]),
            "sdk": diagnostic(["xcrun", "--show-sdk-version"]),
            "compiler": diagnostic(["cc", "--version"]),
            "display_profile": sanitize_hardware(display_profile),
            "physical_metal_device_count": len(devices),
            "free_memory_bytes": free_memory,
            "load_average": os.getloadavg(),
            "power": diagnostic(["pmset", "-g", "batt"]),
            "thermal": diagnostic(["pmset", "-g", "therm"]),
            "gpu_performance_claim": False,
            "dispatch_evidence_required": False,
        })
        with tempfile.TemporaryDirectory(
                prefix="webp-cache-search-corpus-") as temporary:
            corpus = build_and_generate(manifest, Path(temporary), output)
            correctness_gate(manifest, corpus, output)
            timed_matrix(manifest, corpus, output)
            validate_inventory(manifest, output)
        completed = True
    except BaseException as error:
        failure = f"{type(error).__name__}: {error}"
        if output.exists():
            write_json(output / "failure.json", {
                "schema": "libwebp-backref-cache-search-failure-v1",
                "experiment": name,
                "commit": commit,
                "failure": failure,
            })
            (output / "operator-report.md").write_text(
                f"# Frozen operator handoff\n\nExperiment: `{name}`  \n"
                f"Commit: `{commit}`  \nStatus: failed; no parameters changed.  \n"
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
                "schema": "libwebp-backref-cache-search-resources-v1",
                "elapsed_seconds": time.time() - started,
                "maximum_observed_rss_bytes": rss,
                "ending_load_average": os.getloadavg(),
                "ending_power": diagnostic(["pmset", "-g", "batt"]),
                "ending_thermal": diagnostic(["pmset", "-g", "therm"]),
                "lease_released": True,
                "completed": completed,
                "failure": failure,
            })
            if not completed:
                write_artifact_hashes(output)
    (output / "operator-report.md").write_text(
        f"# Frozen operator handoff\n\nExperiment: `{name}`  \n"
        f"Commit: `{commit}`  \nManifest: `{sha256(MANIFEST_PATH)}`  \n"
        "Protocol completed without interpretation. No GPU performance claim "
        "is part of this CPU-boundary diagnostic.\n", encoding="utf-8")
    write_artifact_hashes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    run = sub.add_parser("run")
    run.add_argument("experiment", choices=("backref_cache_search",))
    run.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = load_manifest()
    if args.command == "validate":
        if os.environ.get("WEBP_BENCHMARK_SESSION") == "exclusive":
            raise SystemExit("validate refuses an exclusive benchmark session")
        print(json.dumps({
            "schema": manifest["schema"],
            "manifest_sha256": sha256(MANIFEST_PATH),
            "experiment": manifest["experiment_id"],
        }, sort_keys=True))
        return 0
    operator_run(args.experiment, args.output.resolve(), manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
