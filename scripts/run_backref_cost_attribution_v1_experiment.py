#!/usr/bin/env python3
"""Frozen remote operator for diagnostic-only backref-cost attribution v1."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from backref_cost_attribution_v1_admission import (
    OBSERVE_ONLY_EXTERNAL_PROCESS_CLASSES, run_owned)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts/backref_cost_attribution_v1_manifest.json"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run(argv: list[str], *, cwd: Path = ROOT,
        env: dict[str, str] | None = None, timeout: int = 1200,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    result = run_owned(argv, cwd=cwd, env=env, timeout=timeout, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def git(*args: str) -> str:
    result = run_owned(["git", *args], cwd=ROOT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout.strip()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["phase_1_decision"]["status"] != "AUTHORIZE_DIAGNOSTIC":
        raise RuntimeError("phase 1 is frozen fail-closed; run is not authorized")
    for row in manifest["frozen_artifacts"]:
        if sha256(ROOT / row["path"]) != row["sha256"]:
            raise RuntimeError(f"frozen source hash mismatch: {row['path']}")
    return manifest


def validate_source(manifest: dict) -> str:
    commit = git("rev-parse", "HEAD")
    expected = os.environ.get(manifest["required_expected_commit_environment"])
    if not expected or expected != commit:
        raise RuntimeError("exact handoff commit environment mismatch")
    if git("status", "--porcelain"):
        raise RuntimeError("operator requires a clean source checkout")
    if run(["git", "merge-base", "--is-ancestor", manifest["base_commit"],
            commit], check=False).returncode != 0:
        raise RuntimeError("handoff is not descended from frozen main")
    return commit


def clean_environment(manifest: dict, variant: str,
                      stage_output: Path | None = None,
                      run_id: str | None = None,
                      case_id: str | None = None) -> dict[str, str]:
    host = manifest["remote_host"]
    env = {
        "HOME": str(Path.home()), "USER": os.environ["USER"],
        "LOGNAME": os.environ["LOGNAME"], "TMPDIR": os.environ["TMPDIR"],
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8", "DEVELOPER_DIR": host["developer_dir"],
        "SDKROOT": host["sdk_path"],
    }
    for name in manifest["forbidden_environment"]:
        env.pop(name, None)
    if variant == "candidate":
        env[manifest["candidate"]["runtime_flag"]] = "1"
    elif variant != "baseline":
        raise RuntimeError("unknown variant")
    if stage_output is not None:
        env.update({
            "WEBP_BENCHMARK_SESSION": "exclusive",
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_TIMERS": "1",
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_STAGE_OUTPUT": str(stage_output),
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_RUN_ID": run_id or "",
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_CASE_ID": case_id or "",
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_SAMPLE_SET": "warm-dominant",
        })
    return env


def process_guard(output: Path, label: str) -> dict:
    result = run(["ps", "-axo", "pid=,ppid=,state=,etime=,command="])
    text = result.stdout
    (output / f"processes-{label}.txt").write_text(text, encoding="utf-8")
    workers = [line for line in text.splitlines() if "Runner.Worker" in line]
    patterns = ("_experiment_runner", "xctrace record", "sample ",
                "benchmark_metal", "nvidia-smi", "nvcc", "cuda")
    conflicts = [line for line in text.splitlines()
                 if any(value.lower() in line.lower() for value in patterns)]
    # Ignore this operator's own argv and the ps command.
    conflicts = [line for line in conflicts
                 if "run_backref_cost_attribution_v1_experiment.py" not in line
                 and "ps -axo" not in line]
    if workers or conflicts:
        raise RuntimeError("Runner.Worker, competing profile, benchmark, or CUDA detected")
    return {"runner_worker_matches": workers, "conflicts": conflicts,
            "runner_listener_present": "Runner.Listener" in text,
            "external_process_classes": list(
                OBSERVE_ONLY_EXTERNAL_PROCESS_CLASSES),
            "external_process_policy":
                "observe-only; conflicts fail closed; never signal",
            "sha256": hashlib.sha256(result.stdout.encode()).hexdigest()}


def available_memory() -> tuple[int, str]:
    raw = run(["/usr/bin/vm_stat"]).stdout
    match = re.search(r"page size of ([0-9]+) bytes", raw)
    if match is None:
        raise RuntimeError("vm_stat page size unavailable")
    pages = 0
    for name in ("Pages free", "Pages inactive", "Pages speculative"):
        found = re.search(rf"^{name}:\s+([0-9]+)\.", raw, re.MULTILINE)
        if found is None:
            raise RuntimeError(f"vm_stat field unavailable: {name}")
        pages += int(found.group(1))
    return pages * int(match.group(1)), raw


def resource_admission(manifest: dict, output: Path, label: str) -> dict:
    """Capture immutable/read-only host state and fail closed on drift."""
    host = manifest["remote_host"]
    model = run(["/usr/sbin/sysctl", "-n", "hw.model"]).stdout.strip()
    cpu = run(["/usr/sbin/sysctl", "-n",
               "machdep.cpu.brand_string"]).stdout.strip()
    physical = int(run(["/usr/sbin/sysctl", "-n",
                        "hw.memsize"]).stdout.strip())
    available, vm_raw = available_memory()
    disk = shutil.disk_usage(output).free
    battery = run(["/usr/bin/pmset", "-g", "batt"]).stdout
    custom = run(["/usr/bin/pmset", "-g", "custom"]).stdout
    thermal = run(["/usr/bin/pmset", "-g", "therm"]).stdout
    power = json.loads(run(["/usr/sbin/system_profiler", "SPPowerDataType",
                            "-json"]).stdout)
    ac_entries = [row.get("AC Power", {})
                  for row in power.get("SPPowerDataType", [])
                  if "AC Power" in row]
    if model != host["hardware_model"] or cpu != host["cpu_brand"] or \
            physical != host["physical_memory_bytes"]:
        raise RuntimeError("Apple hardware identity mismatch")
    if available < manifest["resources"]["minimum_available_memory_bytes"]:
        raise RuntimeError("available-memory prerequisite failed")
    if disk < manifest["resources"]["minimum_available_disk_bytes"]:
        raise RuntimeError("available-disk prerequisite failed")
    if "AC Power" not in battery or "lowpowermode         0" not in custom:
        raise RuntimeError("AC power with Low Power Mode off is required")
    if not ac_entries or any(row.get("Current Power Source") != "TRUE" or
                             row.get("LowPowerMode") != "No"
                             for row in ac_entries):
        raise RuntimeError("system_profiler power prerequisite failed")
    if any(required not in thermal
           for required in host["required_thermal_lines"]):
        raise RuntimeError("thermal/performance state prerequisite failed")
    record = {
        "label": label, "hardware_model": model, "cpu_brand": cpu,
        "physical_memory_bytes": physical,
        "available_memory_bytes": available,
        "available_disk_bytes": disk, "vm_stat": vm_raw,
        "pmset_batt": battery, "pmset_custom": custom,
        "pmset_thermal": thermal, "system_profiler_power": power,
        "process_isolation": process_guard(output, f"resources-{label}"),
        "settings_changed": False,
    }
    write_json(output / f"resource-admission-{label}.json", record)
    return record


def profiler_admission(manifest: dict) -> dict:
    host = manifest["remote_host"]
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("profiler host must be Darwin arm64")
    observed = {}
    for name, expected in manifest["profiler"]["executables"].items():
        path = Path(expected["path"])
        if not path.is_file() or sha256(path.resolve()) != expected["sha256"]:
            raise RuntimeError(f"profiler executable identity mismatch: {name}")
        observed[name] = {"path": str(path), "canonical": str(path.resolve()),
                          "sha256": sha256(path.resolve())}
    xcrun = manifest["profiler"]["executables"]["xcrun"]["path"]
    compiler = run([host["compiler_path"], "--version"]).stdout.splitlines()
    sdk_path = run([xcrun, "--sdk", "macosx", "--show-sdk-path"]).stdout.strip()
    sdk_version = run([xcrun, "--sdk", "macosx",
                       "--show-sdk-version"]).stdout.strip()
    developer_dir = run(["/usr/bin/xcode-select", "-p"]).stdout.strip()
    if compiler != host["compiler_version_lines"] or \
            sdk_path != host["sdk_path"] or sdk_version != host["sdk_version"] or \
            developer_dir != host["developer_dir"]:
        raise RuntimeError("compiler, SDK, or Xcode identity mismatch")
    version = run([xcrun, "xctrace", "version"]).stdout.strip()
    if version != manifest["profiler"]["xctrace_version"]:
        raise RuntimeError("xctrace version mismatch")
    templates = run([xcrun, "xctrace", "list", "templates"]).stdout
    if "Time Profiler" not in templates:
        raise RuntimeError("Time Profiler template unavailable")
    record_help = run([xcrun, "xctrace", "help", "record"]).stdout
    for token in ("--launch", "--no-prompt", "--output", "--template"):
        if token not in record_help:
            raise RuntimeError(f"xctrace record capability missing: {token}")
    if host["developer_dir"] not in observed["xctrace"]["path"]:
        raise RuntimeError("xctrace is not from frozen Xcode")
    return {"executables": observed, "xctrace_version": version,
            "compiler_version_lines": compiler, "sdk_path": sdk_path,
            "sdk_version": sdk_version, "developer_dir": developer_dir,
            "time_profiler_template": True, "record_schema_verified": True,
            "attach_permission": "not assumed; --launch --no-prompt only",
            "symbolization_prerequisite": "dSYM UUID and required symbols must pass"}


def generate_corpus(manifest: dict, temporary: Path) -> tuple[Path, dict]:
    corpus = temporary / "corpus"
    run([sys.executable, "scripts/generate_publication_corpus.py", "--output",
         str(corpus), "--verify"], timeout=1200)
    catalog = json.loads((corpus / "manifest.json").read_text())
    cases = {row["case_id"]: row for row in catalog["cases"]}
    for frozen in manifest["corpus"]:
        row = cases[frozen["case_id"]]
        if row["sha256"] != frozen["sha256"] or \
                sha256(corpus / row["file"]) != frozen["sha256"]:
            raise RuntimeError("frozen corpus mismatch")
    return corpus, cases


def build(manifest: dict, temporary: Path, output: Path) -> dict:
    host = manifest["remote_host"]
    build_root = temporary / "source-build"
    run(["git", "clone", "--no-checkout", str(ROOT), str(build_root)])
    run(["git", "checkout", "--detach", git("rev-parse", "HEAD")], cwd=build_root)
    env = clean_environment(manifest, "baseline")
    env.update({"CC": host["compiler_path"], "AR": manifest["build"]["ar"],
                "RANLIB": manifest["build"]["ranlib"]})
    flags = manifest["build"]["cflags"]
    argv = ["/usr/bin/make", "-f", "makefile.unix", "WEBP_ENABLE_METAL=0",
            "WEBP_BUILD_BACKREF_COST_ATTRIBUTION_V1_EXPERIMENT=1",
            "WEBP_BACKREF_COST_ATTRIBUTION_V1_DETERMINISTIC_BUILD=1",
            f"CFLAGS={flags}",
            "tools/backref_cost_attribution_v1_experiment_runner"]
    result = run(argv, cwd=build_root, env=env, timeout=1800)
    (output / "build.log").write_text(result.stdout + result.stderr,
                                       encoding="utf-8")
    runner = build_root / "tools/backref_cost_attribution_v1_experiment_runner"
    if not runner.is_file():
        raise RuntimeError("attribution runner missing after build")
    dsym = runner.with_suffix(".dSYM")
    run([manifest["profiler"]["executables"]["dsymutil"]["path"], str(runner),
         "-o", str(dsym)], cwd=build_root)
    nm = run([manifest["profiler"]["executables"]["nm"]["path"], "-nm",
              str(runner)], cwd=build_root).stdout
    (output / "symbols.txt").write_text(nm, encoding="utf-8")
    missing = [symbol for symbol in manifest["acceptance"]["required_symbols"]
               if symbol not in nm]
    if missing:
        raise RuntimeError(f"required stable symbols absent: {missing}")
    binary_uuid = run([manifest["profiler"]["executables"]["dwarfdump"]["path"],
                       "--uuid", str(runner)]).stdout.strip()
    dsym_uuid = run([manifest["profiler"]["executables"]["dwarfdump"]["path"],
                     "--uuid", str(dsym)]).stdout.strip()
    if not binary_uuid or binary_uuid.split()[1] not in dsym_uuid:
        raise RuntimeError("runner and dSYM UUID mismatch")
    record = {"command": argv, "runner": str(runner),
              "runner_sha256": sha256(runner), "dsym": str(dsym),
              "binary_uuid": binary_uuid, "dsym_uuid": dsym_uuid,
              "cflags": flags, "same_binary_for_both_variants": True,
              "required_symbols": manifest["acceptance"]["required_symbols"]}
    write_json(output / "build-identity.json", record)
    return {"root": build_root, "runner": runner, "dsym": dsym,
            "identity": record}


def frozen_profile_plan(manifest: dict, runner: Path, corpus: Path,
                        cases: dict, output: Path) -> list[dict]:
    rows = []
    ordinal = 0
    xcrun = manifest["profiler"]["executables"]["xcrun"]["path"]
    for case in manifest["corpus"]:
        case_id = case["case_id"]
        source = corpus / cases[case_id]["file"]
        for method in manifest["protocol"]["methods"]:
            for repetition, variants in enumerate(
                    manifest["protocol"]["variant_order"]):
                for variant in variants:
                    profile_id = f"p{ordinal:02d}-{case_id}-m{method}-{variant}-r{repetition}"
                    trace = output / "profiles" / f"{profile_id}.trace"
                    stages = output / "stages" / f"{profile_id}.jsonl"
                    runner_stdout = output / "runner" / f"{profile_id}.jsonl"
                    env = clean_environment(manifest, variant, stages,
                                            profile_id, case_id)
                    launched = ["/usr/bin/env"] + [
                        f"{name}={value}" for name, value in sorted(env.items())]
                    launched += [str(runner), "profile", str(source), case_id,
                                 str(method), variant, "1", "4"]
                    command = [xcrun, "xctrace", "record", "--no-prompt",
                               "--template", "Time Profiler", "--output",
                               str(trace), "--target-stdout", str(runner_stdout),
                               "--target-stderr", str(output / "runner" /
                                                       f"{profile_id}.stderr"),
                               "--launch", "--", *launched]
                    rows.append({"ordinal": ordinal, "profile_id": profile_id,
                                 "case_id": case_id, "method": method,
                                 "variant": variant, "repetition": repetition,
                                 "trace": str(trace), "stages": str(stages),
                                 "runner_stdout": str(runner_stdout),
                                 "command": command})
                    ordinal += 1
    if len(rows) != manifest["protocol"]["profile_processes"]:
        raise RuntimeError("profile plan inventory mismatch")
    write_json(output / "profile-plan.json", rows)
    return rows


def correctness_gate(manifest: dict, runner: Path, corpus: Path, cases: dict,
                     output: Path) -> list[dict]:
    rows = []
    root = output / "correctness-files"
    root.mkdir()
    for case in manifest["corpus"]:
        case_id = case["case_id"]
        source = corpus / cases[case_id]["file"]
        for method in manifest["protocol"]["methods"]:
            products = {}
            for variant in ("baseline", "candidate"):
                for repeat in range(2):
                    destination = root / f"{case_id}-m{method}-{variant}-{repeat}.webp"
                    argv = [str(runner), "correctness", str(source), str(method),
                            variant, str(destination)]
                    run(argv, env=clean_environment(manifest, variant), timeout=300)
                    products[(variant, repeat)] = sha256(destination)
            hashes = set(products.values())
            if len(hashes) != 1:
                raise RuntimeError("bitstream correctness/determinism mismatch")
            rows.append({"case_id": case_id, "method": method,
                         "bitstream_sha256": hashes.pop(),
                         "baseline_candidate_equal": True,
                         "repeat_deterministic": True})
    write_json(output / "correctness.json", rows)
    return rows


def inspect_trace(manifest: dict, row: dict, output: Path) -> dict:
    xcrun = manifest["profiler"]["executables"]["xcrun"]["path"]
    trace = Path(row["trace"])
    toc = output / "exports" / f"{row['profile_id']}-toc.xml"
    run([xcrun, "xctrace", "export", "--input", str(trace), "--toc",
         "--output", str(toc)])
    try:
        tree = ET.parse(toc)
    except ET.ParseError as error:
        raise RuntimeError("xctrace TOC XML is malformed") from error
    schemas = sorted({element.attrib["schema"] for element in tree.iter()
                      if "schema" in element.attrib})
    sample_schemas = [value for value in schemas
                      if "sample" in value.lower() or "profile" in value.lower()]
    if not sample_schemas:
        raise RuntimeError("Time Profiler TOC has no sample/profile table")
    exports = []
    combined = ""
    for index, schema in enumerate(sample_schemas):
        exported = output / "exports" / f"{row['profile_id']}-{index}.xml"
        xpath = f"/trace-toc/run/data/table[@schema='{schema}']"
        run([xcrun, "xctrace", "export", "--input", str(trace), "--xpath",
             xpath, "--output", str(exported)])
        combined += exported.read_text(encoding="utf-8", errors="replace")
        exports.append({"schema": schema, "path": str(exported),
                        "sha256": sha256(exported)})
    symbol_hits = {name: combined.count(name)
                   for name in manifest["acceptance"]["required_profile_symbols"]}
    if any(value == 0 for value in symbol_hits.values()):
        raise RuntimeError("required profile symbol absent after export")
    # XML shape varies by Xcode; count explicit sample rows first, then weights.
    sample_count = combined.count("<row")
    if sample_count < manifest["acceptance"]["minimum_export_rows_per_profile"]:
        raise RuntimeError("insufficient exported profile rows")
    return {"profile_id": row["profile_id"], "toc": str(toc),
            "toc_sha256": sha256(toc), "schemas": schemas,
            "sample_schemas": sample_schemas, "exports": exports,
            "export_rows": sample_count, "symbol_hits": symbol_hits}


def execute_profiles(manifest: dict, plan: list[dict], output: Path) -> list[dict]:
    results = []
    for row in plan:
        before = process_guard(output, f"before-{row['profile_id']}")
        result = run(row["command"], timeout=manifest["resources"]["profile_timeout_seconds"])
        with (output / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({**row, "exit_code": result.returncode,
                                  "stdout": result.stdout,
                                  "stderr": result.stderr},
                                 sort_keys=True) + "\n")
        inspected = inspect_trace(manifest, row, output)
        stages = [json.loads(line) for line in Path(row["stages"]).read_text().splitlines()
                  if line.strip()]
        retained = [item for item in stages if item.get("sample_role") == "warm"]
        if len(stages) != 5 or len(retained) != 4:
            raise RuntimeError("stage record inventory mismatch")
        for item in stages:
            if any(name not in item["stages"]
                   for name in manifest["acceptance"]["required_timer_stages"]):
                raise RuntimeError("required timer stage missing")
            nested = item["stages"]
            if nested["backref_cost_dp_setup"]["ns"] + \
                    nested["backref_cost_dp_steady"]["ns"] > \
                    nested["backref_cost_dp_total"]["ns"]:
                raise RuntimeError("DP timer nesting/accounting invalid")
            if nested["backref_cost_dp_total"]["ns"] + \
                    nested["backref_cost_traceback"]["ns"] + \
                    nested["backref_cost_materialize"]["ns"] > \
                    nested["lossless_backward_refs"]["ns"]:
                raise RuntimeError("backward-reference timer accounting invalid")
        after = process_guard(output, f"after-{row['profile_id']}")
        results.append({**inspected, "stage_records": len(stages),
                        "retained_stage_records": len(retained),
                        "process_before": before, "process_after": after})
    write_json(output / "profile-completeness.json", results)
    return results


def write_index(manifest: dict, output: Path) -> None:
    rows = [{"path": path.relative_to(output).as_posix(),
             "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "artifact-hashes.json"]
    write_json(output / "artifact-hashes.json", {
        "schema": manifest["schemas"]["artifact_hashes"], "artifacts": rows})


def operator(mode: str, output: Path) -> None:
    if mode == "run" and os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise RuntimeError("run requires WEBP_BENCHMARK_SESSION=exclusive")
    if mode == "rehearse" and "WEBP_BENCHMARK_SESSION" in os.environ:
        raise RuntimeError("rehearse requires WEBP_BENCHMARK_SESSION unset")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute path")
    output.mkdir(parents=True)
    for directory in ("profiles", "stages", "runner", "exports"):
        (output / directory).mkdir()
    manifest = load_manifest()
    commit = validate_source(manifest)
    lease_path = Path(os.path.expanduser(manifest["resources"]["lease_path"]))
    lease_record = {"schema": manifest["schemas"]["lease"],
                    "acquisition_attempted": False, "acquired": False,
                    "released": False, "path": str(lease_path)}
    write_json(output / "lease-record.json", lease_record)
    admitted = profiler_admission(manifest)
    write_json(output / "profiler-admission.json", admitted)
    resource_admission(manifest, output, "admission")
    with tempfile.TemporaryDirectory(prefix="backref-attribution-v1-") as raw:
        temporary = Path(raw)
        corpus, cases = generate_corpus(manifest, temporary)
        built = build(manifest, temporary, output)
        plan = frozen_profile_plan(manifest, built["runner"], corpus, cases,
                                   output)
        if mode == "rehearse":
            # Deliberately no encoder correctness/profile workload in rehearsal.
            write_json(output / "rehearsal.json", {
                "schema": manifest["schemas"]["rehearsal"], "status": "PASS",
                "source_commit": commit, "profile_commands_constructed": len(plan),
                "profiler_invocations": 0, "encoder_workloads": 0,
                "performance_samples": 0, "benchmark_lease_attempted": False,
                "phase_2_fail_closed_prerequisites": [
                    "bitstream/pixel correctness before first profile",
                    "xctrace --launch --no-prompt succeeds without authentication",
                    "trace export contains required symbols and minimum rows"],
            })
        else:
            lease_path.parent.mkdir(parents=True, exist_ok=True)
            with lease_path.open("a+") as lease:
                lease_record["acquisition_attempted"] = True
                write_json(output / "lease-record.json", lease_record)
                try:
                    fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise RuntimeError("exclusive benchmark lease held") from error
                lease_record["acquired"] = True
                write_json(output / "lease-record.json", lease_record)
                try:
                    correctness = correctness_gate(
                        manifest, built["runner"], corpus, cases, output)
                    if len(correctness) != 4:
                        raise RuntimeError("correctness inventory mismatch")
                    process_guard(output, "pre-profiles")
                    resource_admission(manifest, output, "pre-profiles")
                    profiles = execute_profiles(manifest, plan, output)
                    if len(profiles) != 24:
                        raise RuntimeError("profile completeness inventory mismatch")
                    process_guard(output, "post-profiles")
                    resource_admission(manifest, output, "post-profiles")
                    if sum(path.stat().st_size for path in output.rglob("*")
                           if path.is_file()) > \
                            manifest["resources"]["maximum_output_bytes"]:
                        raise RuntimeError("maximum evidence size exceeded")
                finally:
                    fcntl.flock(lease, fcntl.LOCK_UN)
                    lease_record["released"] = True
                    write_json(output / "lease-record.json", lease_record)
    write_json(output / "operator-status.json", {
        "schema": manifest["schemas"]["operator_status"], "status": "complete",
        "mode": mode, "source_commit": commit,
        "production_promotion_authorized": False})
    write_index(manifest, output)


def controlled(mode: str, output: Path) -> None:
    try:
        operator(mode, output)
    except Exception as error:
        manifest = json.loads(MANIFEST_PATH.read_text())
        output.mkdir(parents=True, exist_ok=True)
        lease = output / "lease-record.json"
        if not lease.exists():
            write_json(lease, {"schema": manifest["schemas"]["lease"],
                               "acquisition_attempted": False,
                               "acquired": False, "released": False})
        write_json(output / "refusal.json", {
            "schema": manifest["schemas"]["refusal"], "status": "refused",
            "error_type": type(error).__name__, "reason": str(error),
            "controlled_exit": True})
        write_json(output / "operator-status.json", {
            "schema": manifest["schemas"]["operator_status"],
            "status": "refused", "mode": mode, "controlled_exit": True})
        write_index(manifest, output)
        raise RuntimeError("controlled attribution refusal; indexed evidence retained") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    for name in ("rehearse", "run"):
        child = sub.add_parser(name)
        child.add_argument("output", type=Path)
    fixture = sub.add_parser("refusal-fixture")
    fixture.add_argument("output", type=Path)
    fixture.add_argument("fixture", choices=("missing", "wrong"))
    args = parser.parse_args()
    try:
        if args.command == "validate":
            manifest = load_manifest()
            commit = validate_source(manifest)
            print(json.dumps({"status": "PASS", "source_commit": commit,
                              "manifest_sha256": sha256(MANIFEST_PATH)}))
        elif args.command in ("rehearse", "run"):
            controlled(args.command, args.output)
        else:
            # The executor's archive/refusal path needs a deterministic early refusal.
            if "WEBP_BENCHMARK_SESSION" in os.environ:
                raise RuntimeError("refusal fixture requires session unset")
            manifest = load_manifest()
            args.output.mkdir(parents=True)
            write_json(args.output / "lease-record.json", {
                "schema": manifest["schemas"]["lease"],
                "acquisition_attempted": False, "acquired": False,
                "released": False})
            write_json(args.output / "refusal.json", {
                "schema": manifest["schemas"]["refusal"], "status": "refused",
                "reason": f"frozen {args.fixture} profiler fixture",
                "controlled_exit": True})
            write_json(args.output / "operator-status.json", {
                "schema": manifest["schemas"]["operator_status"],
                "status": "refused", "controlled_exit": True})
            write_index(manifest, args.output)
        return 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
