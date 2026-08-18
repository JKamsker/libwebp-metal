#!/usr/bin/env python3
"""Untimed, read-only audit of the frozen cache-search evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "297b9e5257ed1098503f7630f3223c1fddbef261"
DESIGNER_COMMIT = "90ceb5a3d81a761678c0e89d44f7c09e5ce18836"
EXECUTOR_COMMIT = "5ab9cfc0cf435e821ce7cd8d7c8c2112ef170ec8"
MANIFEST_PATH = ROOT / "scripts" / "backref_cache_search_experiment_v1.json"
OPERATOR_PATH = ROOT / "scripts" / "run_backref_cache_search_experiment.py"
EVIDENCE_INDEX_PATH = (
    ROOT / "profile-data" / "runs" /
    "20260818-next-backref-cache-search-executor" / "evidence-index.json")
EXPECTED_MANIFEST_SHA256 = (
    "ed0c68b0e72fb013da5fe244d20453e3c86d1199cc7877725c2c4b4fb8041fe1")
EXPECTED_OPERATOR_SHA256 = (
    "1a66c966dc1d5735e5bba6ef8b281f4b8093b542c399b451c72594d8084a1848")
EXPECTED_ARTIFACT_INDEX_SHA256 = (
    "55acf72755516c68fa9b6884589553ae8b9d1ba18679de85d7a97f29491e547d")
BOOTSTRAP_SEED = 20260818
BOOTSTRAP_RESAMPLES = 10000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"audit failed: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT,
                                   text=True).strip()


def is_ancestor(older: str, newer: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", older,
                           newer], cwd=ROOT, check=False,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


def audit_source_guards() -> None:
    scientific_paths = (
        "CMakeLists.txt", "makefile.unix", "examples/cwebp.c",
        "src/enc/backref_cache_search_experiment_enc.c",
        "src/enc/backref_cache_search_experiment_enc.h",
        "src/enc/backward_references_enc.c", "src/enc/webp_enc.c",
        "scripts/backref_cache_search_experiment_v1.json",
        "scripts/run_backref_cache_search_experiment.py",
        "scripts/test_backref_cache_search_experiment.py",
        "scripts/test_experiment_guards.py")
    for relative in scientific_paths:
        frozen = subprocess.check_output(
            ["git", "show", f"{DESIGNER_COMMIT}:{relative}"], cwd=ROOT)
        require((ROOT / relative).read_bytes() == frozen,
                f"scientific source changed after designer: {relative}")
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    makefile = (ROOT / "makefile.unix").read_text(encoding="utf-8")
    cli = (ROOT / "examples" / "cwebp.c").read_text(encoding="utf-8")
    recorder = (ROOT / "src" / "enc" /
                "backref_cache_search_experiment_enc.c").read_text(
                    encoding="utf-8")
    callsite = (ROOT / "src" / "enc" /
                "backward_references_enc.c").read_text(encoding="utf-8")
    build_flag = "WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT"
    macro = "WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT"
    runtime = "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT"
    option = "-backref_cache_search_repetitions"
    require(f"option({build_flag}" in cmake and
            "experiment.\" OFF)" in cmake and
            f"{build_flag} ?= 0" in makefile,
            "default-off build declarations")
    require(f"ifeq ($({build_flag}),1)" in makefile and
            f"-D{macro}=1" in makefile and
            "backref_cache_search_experiment_enc.o" in makefile,
            "Unix make source/macro gate")
    require(f"if({build_flag})" in cmake and macro in cmake and
            "backref_cache_search_experiment_enc.c" in cmake,
            "CMake source/macro gate")
    require(f"defined({macro})" in cli and option in cli and
            runtime in cli, "private CLI guard")
    require(runtime in recorder and
            "WEBP_BENCHMARK_SESSION" in recorder and
            "WEBP_BACKREF_CACHE_SEARCH_CONTROL" in recorder and
            "WEBP_BACKREF_CACHE_SEARCH_INJECT_RECORD_FAILURE" in recorder,
            "runtime/refusal/transactional recorder guards")
    require(callsite.count("WebPBackrefCacheSearchStageBegin()") == 1 and
            callsite.count("WebPBackrefCacheSearchStageEnd(") == 1 and
            callsite.count("WebPBackrefCacheSearchTotalBegin()") == 1,
            "focused source probe placement")
    require(not git("diff", "--name-only", DESIGNER_COMMIT, EXECUTOR_COMMIT,
                    "--", *scientific_paths),
            "executor changed scientific source")


def median_mad(values: list[float]) -> tuple[float, float]:
    center = statistics.median(values)
    return center, statistics.median(abs(value - center) for value in values)


def bootstrap_median_ci(values: list[float],
                        generator: random.Random) -> tuple[float, float]:
    bootstraps = sorted(
        statistics.median(generator.choice(values) for _ in values)
        for _ in range(BOOTSTRAP_RESAMPLES))
    low = bootstraps[int(0.025 * BOOTSTRAP_RESAMPLES)]
    high = bootstraps[math.ceil(0.975 * BOOTSTRAP_RESAMPLES) - 1]
    return low, high


def nearest_rank(values: list[int], quantile: float) -> int:
    require(values, "nearest-rank input is empty")
    return sorted(values)[math.ceil(quantile * len(values)) - 1]


def audit_artifacts(evidence: Path) -> tuple[dict, int]:
    index_path = evidence / "artifact-hashes.json"
    require(sha256(index_path) == EXPECTED_ARTIFACT_INDEX_SHA256,
            "artifact hash index digest")
    artifact_hashes = read_json(index_path)
    actual_files = {
        str(path.relative_to(evidence))
        for path in evidence.rglob("*")
        if path.is_file() and path.name != "artifact-hashes.json"
    }
    require(set(artifact_hashes) == actual_files,
            "artifact index does not exactly cover evidence files")
    require(len(artifact_hashes) == 89, "artifact count")
    for relative, expected in artifact_hashes.items():
        require(sha256(evidence / relative) == expected,
                f"artifact digest: {relative}")
    return artifact_hashes, sum(
        path.stat().st_size for path in evidence.rglob("*") if path.is_file())


def expected_commands(manifest: dict) -> list[tuple]:
    experiment = manifest["experiment"]
    common = manifest["common"]
    expected = []
    cases = [(case, "tune") for case in experiment["tune_cases"]]
    cases += [(case, "holdout") for case in experiment["holdout_cases"]]
    for case_id, role in cases:
        for method in common["methods"]:
            for lifecycle in ("cold", "warm"):
                spec = common["lifecycles"][lifecycle]
                for pair in range(spec["process_pairs"]):
                    for variant in common["pair_order"][pair].split("-"):
                        expected.append((case_id, role, method, lifecycle,
                                         pair, variant,
                                         spec["encodes_per_process"]))
    return expected


def audit_commands_and_records(manifest: dict, evidence: Path
                               ) -> tuple[list[tuple[dict, list[dict]]], dict]:
    experiment = manifest["experiment"]
    inventory = manifest["common"]["expected_inventory"]
    commands = read_jsonl(evidence / "commands.jsonl")
    records = read_jsonl(evidence / "records.jsonl")
    require(len(commands) == inventory["command_rows"], "command count")
    require(len(records) == inventory["raw_timing_records"],
            "timing-record count")
    require([row.get("sequence") for row in commands] ==
            list(range(1, len(commands) + 1)), "command sequence")
    actual_order = [
        (row.get("case_id"), row.get("tune_holdout"), row.get("method"),
         row.get("lifecycle"), row.get("pair"), row.get("variant"),
         row.get("repetitions")) for row in commands]
    require(actual_order == expected_commands(manifest), "command order")

    process_rows = []
    position = 0
    pids = []
    max_command_seconds = 0.0
    for command in commands:
        require(command.get("schema") == experiment["command_schema"],
                "command schema")
        require(command.get("experiment") == manifest["experiment_id"],
                "command experiment")
        environment = command.get("experiment_environment", {})
        require(environment == {
            "WEBP_ACCELERATOR": "metal",
            "WEBP_BACKREF_CACHE_SEARCH_CONTROL":
                "1" if command["variant"] == "control" else "0",
            "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT": "1",
            "WEBP_BENCHMARK_SESSION": "exclusive",
        }, "command environment")
        argv = command.get("argv", [])
        expected_middle = ["-quiet", "-lossless", "-exact", "-q", "75",
                           "-m", str(command["method"])]
        if command["repetitions"] != 1:
            expected_middle += [experiment["repetition_option"],
                                str(command["repetitions"])]
        require(Path(argv[0]).name == "cwebp" and
                argv[1:-1] == expected_middle and
                Path(argv[-1]).name == f"{command['case_id']}.ppm",
                "frozen encoder command")
        stderr_path = evidence / command["stderr"]
        require(sha256(stderr_path) == command["stderr_sha256"],
                "command stderr digest")
        require(stderr_path.stat().st_size == 0, "nonempty command stderr")
        require(command["elapsed_ns"] > 0, "nonpositive command duration")
        max_command_seconds = max(max_command_seconds,
                                  command["elapsed_ns"] / 1e9)

        count = command["repetitions"]
        rows = records[position:position + count]
        position += count
        require(len(rows) == count, "record slice")
        require(len({row.get("pid") for row in rows}) == 1,
                "one PID per command")
        pids.append(rows[0]["pid"])
        require([row.get("encode_index") for row in rows] ==
                list(range(count)), "encode indexes")
        expected_roles = (["cold"] if command["lifecycle"] == "cold" else
                          ["warmup"] + ["warm"] * (count - 1))
        require([row.get("sample_role") for row in rows] == expected_roles,
                "sample roles")
        dimensions = {"texture-medium": (1600, 1200),
                      "texture-large": (3000, 2000)}
        width, height = dimensions[command["case_id"]]
        for row in rows:
            require(row.get("schema") == experiment["schema"],
                    "timing-record schema")
            require(row.get("run_id") == "backref-cache-search" and
                    row.get("case_id") == command["case_id"] and
                    row.get("method") == command["method"] and
                    row.get("variant") == command["variant"],
                    "record identity")
            require(row.get("width") == width and row.get("height") == height
                    and row.get("pixels") == width * height,
                    "record dimensions")
            require(row.get("ok") is True and row.get("error_code") == 0 and
                    row.get("total_ns", 0) > 0, "record success")
            backref = row["stages"]["backref_total"]
            cache = row["stages"]["cache_search"]
            if command["variant"] == "record":
                require(backref["calls"] == 1 and cache["calls"] == 2,
                        "record call counts")
                require(0 < cache["elapsed_ns"] <= backref["elapsed_ns"] <=
                        row["total_ns"], "nested elapsed times")
            else:
                require(backref == {"elapsed_ns": 0, "calls": 0} and
                        cache == {"elapsed_ns": 0, "calls": 0},
                        "control clocks")
        process_rows.append((command, [
            row for row in rows if row["sample_role"] != "warmup"]))
    require(position == len(records), "unassigned timing records")
    require(len(set(pids)) == len(commands), "one process per command")

    roles = {role: sum(row["sample_role"] == role for row in records)
             for role in ("cold", "warmup", "warm")}
    require(roles == {"cold": inventory["cold_records"],
                      "warmup": inventory["discarded_warmups"],
                      "warm": inventory["measured_warm_records"]},
            "sample-role inventory")
    measured = [row for row in records if row["sample_role"] != "warmup"]
    variants = {variant: sum(row["variant"] == variant for row in measured)
                for variant in ("record", "control")}
    require(variants == {
        "record": inventory["measured_record_variant"],
        "control": inventory["measured_control_variant"]},
        "measured variant inventory")
    return process_rows, {
        "command_rows": len(commands),
        "raw_timing_records": len(records),
        "cold_records": roles["cold"],
        "discarded_warmups": roles["warmup"],
        "measured_warm_records": roles["warm"],
        "measured_record_variant": variants["record"],
        "measured_control_variant": variants["control"],
        "unique_processes": len(set(pids)),
        "maximum_command_seconds": max_command_seconds,
    }


def audit_correctness(manifest: dict, evidence: Path) -> dict:
    experiment = manifest["experiment"]
    inventory = manifest["common"]["expected_inventory"]
    raw = read_jsonl(evidence / "correctness-records.jsonl")
    summary = read_json(evidence / "correctness.json")
    require(len(raw) == inventory["raw_correctness_records"],
            "raw correctness count")
    require(summary.get("schema") == experiment["correctness_schema"] and
            summary.get("ok") is True, "correctness summary schema/status")
    require(len(summary.get("rows", [])) ==
            inventory["correctness_summary_rows"],
            "correctness summary count")
    position = 0
    summary_position = 0
    flags = (
        "repeated_record_deterministic", "decoded_input_equal",
        "control_equal", "injected_record_failure_transactional",
        "recorder_open_failure_transactional")
    for case_id in experiment["correctness_cases"]:
        for method in manifest["common"]["methods"]:
            rows = raw[position:position + 3]
            position += 3
            require(len(rows) == 3 and
                    [row.get("variant") for row in rows] ==
                    ["record", "record", "control"],
                    "correctness record variants")
            require(all(row.get("schema") == experiment["schema"] and
                        row.get("case_id") == case_id and
                        row.get("method") == method and row.get("ok") is True
                        and row.get("error_code") == 0 for row in rows),
                    "correctness record identity/status")
            first, second, control = rows
            require(first["stages"]["backref_total"]["calls"] ==
                    second["stages"]["backref_total"]["calls"] and
                    first["stages"]["cache_search"]["calls"] ==
                    second["stages"]["cache_search"]["calls"],
                    "repeated recorder call counts")
            require(first["stages"]["backref_total"]["calls"] > 0 and
                    0 < first["stages"]["cache_search"]["calls"] <=
                    2 * first["stages"]["backref_total"]["calls"],
                    "correctness recorder call relationship")
            require(control["stages"] == {
                "backref_total": {"elapsed_ns": 0, "calls": 0},
                "cache_search": {"elapsed_ns": 0, "calls": 0}},
                "correctness control clocks")
            row = summary["rows"][summary_position]
            summary_position += 1
            require(row.get("case_id") == case_id and
                    row.get("method") == method and
                    all(row.get(flag) is True for flag in flags) and
                    len(row.get("bitstream_sha256", "")) == 64,
                    "correctness summary row")
    require(position == len(raw), "unassigned correctness records")
    return {
        "raw_correctness_records": len(raw),
        "correctness_summary_rows": len(summary["rows"]),
        "determinism": True,
        "decoded_pixel_identity": True,
        "control_identity": True,
        "injected_record_failure_transactional": True,
        "recorder_open_failure_transactional": True,
    }


def evaluate_cells(manifest: dict,
                   processes: list[tuple[dict, list[dict]]]) -> list[dict]:
    acceptance = manifest["common"]["acceptance"]
    generator = random.Random(BOOTSTRAP_SEED)
    cells = []
    cases = [(case, "tune") for case in manifest["experiment"]["tune_cases"]]
    cases += [(case, "holdout")
              for case in manifest["experiment"]["holdout_cases"]]
    for case_id, role in cases:
        for method in manifest["common"]["methods"]:
            for lifecycle in ("cold", "warm"):
                selected = [item for item in processes
                            if item[0]["case_id"] == case_id and
                            item[0]["method"] == method and
                            item[0]["lifecycle"] == lifecycle]
                by_pair: dict[int, dict[str, list[dict]]] = {}
                for command, rows in selected:
                    by_pair.setdefault(command["pair"], {})[
                        command["variant"]] = rows
                pair_ratios = []
                process_shares = []
                record_raw = []
                control_raw = []
                for pair in sorted(by_pair):
                    variants = by_pair[pair]
                    require(set(variants) == {"record", "control"},
                            "pair variants")
                    record = variants["record"]
                    control = variants["control"]
                    pair_ratios.append(
                        statistics.median(row["total_ns"] for row in record) /
                        statistics.median(row["total_ns"] for row in control))
                    process_shares.append(statistics.median(
                        row["stages"]["cache_search"]["elapsed_ns"] /
                        row["stages"]["backref_total"]["elapsed_ns"]
                        for row in record))
                    record_raw += [row["total_ns"] for row in record]
                    control_raw += [row["total_ns"] for row in control]
                share, share_mad = median_mad(process_shares)
                share_ci = bootstrap_median_ci(process_shares, generator)
                ratio, ratio_mad = median_mad(pair_ratios)
                ratio_ci = bootstrap_median_ci(pair_ratios, generator)
                p95_ratio = (nearest_rank(record_raw, 0.95) /
                             nearest_rank(control_raw, 0.95))
                share_pass = share >= acceptance[
                    "holdout_cache_search_share_of_backref_total_minimum"]
                median_pass = ratio <= acceptance[
                    "record_control_median_ratio_maximum"]
                p95_pass = p95_ratio <= acceptance[
                    "record_control_p95_ratio_maximum"]
                cells.append({
                    "role": role,
                    "case_id": case_id,
                    "method": method,
                    "lifecycle": lifecycle,
                    "raw_records_per_variant": len(record_raw),
                    "process_pairs": len(pair_ratios),
                    "cache_search_share": share,
                    "cache_search_share_mad": share_mad,
                    "cache_search_share_bootstrap_95": list(share_ci),
                    "record_control_median_ratio": ratio,
                    "record_control_median_ratio_mad": ratio_mad,
                    "record_control_median_ratio_bootstrap_95": list(ratio_ci),
                    "record_control_p95_ratio": p95_ratio,
                    "pair_median_ratios": pair_ratios,
                    "criteria": {
                        "share": share_pass,
                        "median_overhead": median_pass,
                        "p95_overhead": p95_pass,
                        "all": share_pass and median_pass and p95_pass,
                    },
                })
    return cells


def audit_source_and_resources(manifest: dict, evidence: Path,
                               artifact_bytes: int,
                               command_inventory: dict) -> dict:
    preflight = read_json(evidence / "preflight.json")
    machine = read_json(evidence / "machine.json")
    resources = read_json(evidence / "resource-notes.json")
    ceilings = manifest["common"]["resource_ceilings"]
    require(preflight.get("commit") == DESIGNER_COMMIT and
            preflight.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256 and
            preflight.get("session") == "exclusive" and
            preflight.get("lease") == manifest["common"]["lease_path"],
            "preflight source/session/lease")
    require(machine.get("physical_metal_device_count") ==
            ceilings["single_physical_metal_device"], "device count")
    require(machine.get("gpu_performance_claim") is False and
            machine.get("dispatch_evidence_required") is False,
            "GPU claim boundary")
    require(machine.get("free_memory_bytes", 0) >=
            ceilings["minimum_free_memory_bytes"], "free-memory gate")
    require(resources.get("completed") is True and
            resources.get("failure") is None and
            resources.get("lease_released") is True,
            "completion/lease release")
    require(resources.get("elapsed_seconds", math.inf) <=
            ceilings["maximum_total_duration_seconds"], "duration ceiling")
    require(resources.get("maximum_observed_rss_bytes", math.inf) <=
            ceilings["maximum_observed_rss_bytes"], "RSS ceiling")
    require(artifact_bytes <= ceilings["maximum_output_bytes"],
            "output ceiling")
    require(command_inventory["maximum_command_seconds"] <=
            ceilings["command_timeout_seconds"], "command timeout ceiling")
    build = (evidence / "build.log").read_text(encoding="utf-8",
                                               errors="replace")
    require("-DWEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT=1" in build and
            "-DWEBP_USE_METAL=1" in build and
            "backref_cache_search_experiment_enc.o" in build,
            "experiment/Metal build evidence")
    searchable = "\n".join(
        (evidence / name).read_text(encoding="utf-8", errors="replace")
        for name in ("build.log", "commands.jsonl", "operator-report.md"))
    require(not any(token in searchable.lower()
                    for token in ("cuda", "nvcc", "nvidia")),
            "CUDA marker in execution evidence")
    return {
        "source_commit": preflight["commit"],
        "physical_metal_device_count": machine["physical_metal_device_count"],
        "free_memory_bytes": machine["free_memory_bytes"],
        "elapsed_seconds": resources["elapsed_seconds"],
        "maximum_observed_rss_bytes":
            resources["maximum_observed_rss_bytes"],
        "evidence_bytes_including_hash_index": artifact_bytes,
        "maximum_command_seconds": command_inventory["maximum_command_seconds"],
        "lease_release_evidenced": True,
        "thermal_warning_recorded": False,
        "gpu_performance_claim": False,
        "dispatch_evidence_required": False,
        "cuda_marker_found": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path)
    args = parser.parse_args()
    manifest = read_json(MANIFEST_PATH)
    evidence_index = read_json(EVIDENCE_INDEX_PATH)
    evidence = (args.evidence_root or Path(
        evidence_index["experiment"]["evidence_path"])).resolve()

    require(is_ancestor(BASE_COMMIT, DESIGNER_COMMIT),
            "baseline is not designer ancestor")
    require(is_ancestor(DESIGNER_COMMIT, EXECUTOR_COMMIT),
            "designer is not executor ancestor")
    require(is_ancestor(EXECUTOR_COMMIT, git("rev-parse", "HEAD")),
            "HEAD is not descended from executor evidence")
    require(sha256(MANIFEST_PATH) == EXPECTED_MANIFEST_SHA256,
            "manifest digest")
    require(sha256(OPERATOR_PATH) == EXPECTED_OPERATOR_SHA256,
            "operator digest")
    require(evidence_index.get("base_commit") == BASE_COMMIT and
            evidence_index.get("designer_commit") == DESIGNER_COMMIT and
            evidence_index.get("source_commit") == DESIGNER_COMMIT and
            evidence_index["experiment"].get("artifact_hashes_sha256") ==
            EXPECTED_ARTIFACT_INDEX_SHA256,
            "executor evidence index authority")
    require(manifest.get("base_commit") == BASE_COMMIT and
            manifest.get("experiment_id") == "backref_cache_search" and
            manifest["experiment"].get("direct_production_promotion_allowed")
            is False and manifest["experiment"].get("gpu_performance_claim")
            is False, "manifest authority/claim boundary")
    require(not git("diff", "--name-only", BASE_COMMIT, DESIGNER_COMMIT,
                    "--", "src/webp"), "installed header changed")
    audit_source_guards()

    artifacts, artifact_bytes = audit_artifacts(evidence)
    processes, command_inventory = audit_commands_and_records(
        manifest, evidence)
    correctness = audit_correctness(manifest, evidence)
    cells = evaluate_cells(manifest, processes)
    resources = audit_source_and_resources(
        manifest, evidence, artifact_bytes, command_inventory)
    holdout = [cell for cell in cells if cell["role"] == "holdout"]
    accepted = all(cell["criteria"]["all"] for cell in holdout)
    require(not accepted, "frozen evidence unexpectedly accepted")
    failed = [
        {"method": cell["method"], "lifecycle": cell["lifecycle"],
         "failed_criteria": [name for name, passed in cell["criteria"].items()
                             if name != "all" and not passed]}
        for cell in holdout if not cell["criteria"]["all"]]
    require(failed == [{"method": 6, "lifecycle": "cold",
                        "failed_criteria": ["median_overhead"]}],
            "unexpected holdout failure set")

    result = {
        "schema": "libwebp-backref-cache-search-evaluation-v1",
        "ancestry": {
            "base_commit": BASE_COMMIT,
            "designer_commit": DESIGNER_COMMIT,
            "executor_evidence_commit": EXECUTOR_COMMIT,
            "evaluation_commit": "the separate descendant commit containing this artifact",
        },
        "authority": {
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "operator_sha256": EXPECTED_OPERATOR_SHA256,
            "artifact_hashes_sha256": EXPECTED_ARTIFACT_INDEX_SHA256,
            "artifact_count_excluding_hash_index": len(artifacts),
            "all_nested_artifact_hashes_verified": True,
        },
        "inventory": command_inventory | correctness,
        "statistics": {
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_stream":
                "one deterministic stream in frozen case/method/lifecycle order; share then overhead",
            "warm_reduction":
                "median of five measured encodes within each process",
            "pairing": "record-process median / control-process median",
            "mad": "median absolute deviation over process-pair values",
            "p95": "nearest-rank within each raw variant stratum",
            "pooling": False,
        },
        "cells": cells,
        "gates": {
            "source_manifest_operator": True,
            "independent_default_off_source_and_runtime_guards": True,
            "artifact_hash_inventory_schema_order": True,
            "correctness_determinism_decoded_pixels_fallback": True,
            "exact_timing_call_counts": True,
            "lease_release": True,
            "single_physical_metal_device": True,
            "resource_ceilings": True,
            "cuda_used": False,
            "gpu_or_end_to_end_claim": False,
        },
        "resources": resources,
        "decision": {
            "accepted": False,
            "failed_holdout_cells": failed,
            "disposition":
                "reject_not_accept_as_future_implementation_research_boundary; retain_default_off_diagnostic",
            "production_change_supported": False,
            "threshold_policy_default_public_abi_api_or_cache_semantics_change": False,
            "independent_ratios_multiplied": False,
        },
        "limitations": {
            "hardware_replication_count": 1,
            "execution_days": 1,
            "inputs": "deterministic synthetic texture-medium and texture-large",
            "warm_samples_within_process_correlated": True,
            "dispatch_specific_claim": False,
            "end_to_end_speedup_claim": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
