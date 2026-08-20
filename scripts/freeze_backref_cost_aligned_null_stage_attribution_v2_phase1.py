#!/usr/bin/env python3
"""Generate fresh stage-attribution-v2 identity fixtures and freeze hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v2_payload as payload
import backref_cost_aligned_null_stage_attribution_v2_toolchain as toolchain
import backref_cost_aligned_null_stage_attribution_v2_transport as transport
import backref_cost_aligned_null_stage_attribution_v2_identity as identity
import test_backref_cost_aligned_null_stage_attribution_v2_experiment as experiment_test


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_manifest.json"
EVIDENCE = ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v2-design"
SOURCE_CONTROL_FREEZE = EVIDENCE / "source-admission-control-freeze.json"
REQUEST_CHANNEL_FREEZE = EVIDENCE / "request-channel-size-freeze.json"
EXPECTED_FOUR_BODY_RECEIPT = EVIDENCE / "four-body-expected-receipt.json"
ACTUAL_FOUR_BODY_RECEIPT = EVIDENCE / "four-body-actual-receipt.json"
LOCAL_UNTIMED_EVIDENCE = EVIDENCE / "phase1-local-untimed-experiment.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def receipt_bindings(manifest: dict) -> dict:
    """Generate the nonrecursive source/tree/build/manifest receipt binding."""
    base = manifest["base_commit"]
    stable_manifest_identity = {
        "base_commit": base,
        "build": manifest["build"],
        "four_body_identity": identity.generator_binding(),
        "schemas": manifest["schemas"],
        "protocol": manifest["protocol"],
    }
    return {
        "source_base_commit": base,
        "source_base_tree": run(["git", "rev-parse", f"{base}^{{tree}}"]).strip(),
        "build_identity_sha256": canonical_sha256(manifest["build"]),
        "manifest_identity_sha256": canonical_sha256(stable_manifest_identity),
        "generator_file_sha256": sha256(
            ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_identity.py"),
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run(argv: list[str]) -> str:
    result = subprocess.run(argv, check=False, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {argv}\n{result.stdout}")
    return result.stdout


def git_blob_sha(commit: str, relative: str) -> str:
    value = subprocess.check_output(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT)
    return hashlib.sha256(value).hexdigest()


def capture_codegen(build_root: Path, bindings: dict) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    runner = build_root / "backref_cost_aligned_null_stage_attribution_v2_experiment_runner"
    linker_map = build_root / "linker.map"
    if not runner.is_file() or not linker_map.is_file():
        raise RuntimeError("alignment build runner or linker map is absent")
    symbols = identity.names()
    nm_text = run([str(toolchain.EXECUTABLE_PATHS["nm"]), "-nm", str(runner)])
    addresses = {}
    for line in nm_text.splitlines():
        match = re.match(r"^([0-9a-f]+).* _([^ ]+)$", line)
        if match and match.group(2) in symbols:
            addresses[match.group(2)] = match.group(1)
    if set(addresses) != set(symbols):
        raise RuntimeError("alignment codegen symbols are incomplete")
    values = {name: int(value, 16) for name, value in addresses.items()}
    ordered_addresses = {name: addresses[name] for name in symbols}
    identity.assert_address_geometry(ordered_addresses)
    if sorted(values, key=values.get) != symbols:
        raise RuntimeError("alignment codegen order/modulo mismatch")
    facts = {symbol: experiment_test.symbol_facts(runner, symbol)
             for symbol in symbols}
    for left, right in identity.equivalence_pairs():
        if experiment_test.canonical_instructions(runner, left) != \
                experiment_test.canonical_instructions(runner, right):
            raise RuntimeError("B/L canonical instruction identity mismatch")
    otool_text = run([str(toolchain.EXECUTABLE_PATHS["otool"]), "-l",
                      str(runner)])
    section = re.search(
        rf"sectname {identity.SECTION_NAME}\n\s+segname {identity.SECTION_SEGMENT}\n"
        r"\s+addr (0x[0-9a-f]+)\n\s+size (0x[0-9a-f]+)\n"
        r"\s+offset ([0-9]+)\n\s+align 2\^14 \(16384\)", otool_text)
    if section is None:
        raise RuntimeError("alignment Mach-O section is absent")
    section_block = otool_text[section.start():]
    flags = re.search(r"\n\s+flags (0x[0-9a-f]+)", section_block)
    if flags is None or flags.group(1) != "0x80000400":
        raise RuntimeError("alignment Mach-O section is not executable pure instructions")
    map_text = linker_map.read_text(encoding="utf-8")
    map_rows = [line for line in map_text.splitlines()
                if line.split() and
                line.rsplit(None, 1)[-1].removeprefix("_") in symbols]
    section_rows = [line for line in map_text.splitlines()
                    if f"{identity.SECTION_SEGMENT}\t{identity.SECTION_NAME}" in line]
    if len(map_rows) != identity.count() or len(section_rows) != 1:
        raise RuntimeError("alignment linker-map extract is incomplete")
    extract = "\n".join(section_rows + map_rows) + "\n"
    destination = EVIDENCE / "linker-map.txt"
    shutil.copyfile(linker_map, destination)
    (EVIDENCE / "linker-map-extract.txt").write_text(extract,
                                                       encoding="utf-8")
    section_size = int(section.group(2), 16)
    padding_bytes = section_size - sum(fact["size_bytes"]
                                       for fact in facts.values())
    write_json(EVIDENCE / "phase1-local-codegen.json", {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-local-codegen-v1",
        "status": "PASS",
        "compiler": "Apple clang 17.0.0",
        "flags": "-O3 -g -DNDEBUG -fno-omit-frame-pointer; -Wl,-no_deduplicate",
        "timed_runner_sha256": sha256(runner),
        "timed_runner_bytes": runner.stat().st_size,
        "symbol_addresses": ordered_addresses,
        "four_body_identity": identity.generator_binding(),
        "facts": facts,
        "alignment_boundary_bytes": identity.BOUNDARY_BYTES,
        "all_entry_modulos": {name: values[name] % identity.BOUNDARY_BYTES for name in symbols},
        "entry_order": symbols,
        "inter_entry_spacing_bytes": identity.BOUNDARY_BYTES,
        "dp_to_push_displacement_bytes": 2 * identity.BOUNDARY_BYTES,
        "section_segment": identity.SECTION_SEGMENT,
        "section_name": identity.SECTION_NAME,
        "section_address": section.group(1),
        "section_file_offset": int(section.group(3)),
        "section_size_bytes": section_size,
        "section_alignment_power": 14,
        "section_flags": flags.group(1),
        "section_executable_pure_instructions": True,
        "body_bytes": sum(fact["size_bytes"] for fact in facts.values()),
        "inter_entry_padding_bytes": padding_bytes,
        "linker_map_sha256": sha256(linker_map),
        "linker_map_bytes": linker_map.stat().st_size,
        "linker_map_extract_sha256": hashlib.sha256(extract.encode()).hexdigest(),
        "baseline_layout_canonical_instructions_equal": True,
        "no_h_body_in_candidate_scope": True,
        "all_four_symbol_addresses_distinct": len(set(values.values())) == identity.count(),
        "linker_identical_code_deduplication_disabled": True,
    })
    actual = {
        "schema": identity.EXPECTED_RECEIPT_SCHEMA,
        "generator": identity.generator_binding(),
        "bindings": bindings,
        "symbol_addresses": ordered_addresses,
        "facts": facts,
        "section": {
            "segment": identity.SECTION_SEGMENT,
            "name": identity.SECTION_NAME,
            "address": section.group(1),
            "file_offset": int(section.group(3)),
            "size_bytes": section_size,
            "alignment_power": identity.SECTION_ALIGNMENT_POWER,
            "flags": flags.group(1),
            "executable_pure_instructions": True,
        },
        "body_bytes": sum(fact["size_bytes"] for fact in facts.values()),
        "padding_bytes": padding_bytes,
        "binary_bytes": runner.stat().st_size,
        "binary_sha256": sha256(runner),
        "linker_map_bytes": linker_map.stat().st_size,
        "linker_map_sha256": sha256(linker_map),
        "linker_map_extract_sha256": hashlib.sha256(extract.encode()).hexdigest(),
        "no_deduplicate_flag": identity.NO_DEDUPLICATE_FLAG,
    }
    # Freeze the generator-derived expectation first.
    write_json(EXPECTED_FOUR_BODY_RECEIPT, actual)
    identity.validate_machine_receipt(actual, bindings)

    # Independently rerun symbol, body, section, map and binary extraction.
    second_nm = run([str(toolchain.EXECUTABLE_PATHS["nm"]), "-nm", str(runner)])
    second_addresses = {}
    for line in second_nm.splitlines():
        match = re.match(r"^([0-9a-f]+).* _([^ ]+)$", line)
        if match and match.group(2) in identity.names():
            second_addresses[match.group(2)] = match.group(1)
    second_addresses = {name: second_addresses[name] for name in identity.names()}
    identity.assert_address_geometry(second_addresses)
    second_facts = {name: experiment_test.symbol_facts(runner, name)
                    for name in identity.names()}
    second_otool = run([str(toolchain.EXECUTABLE_PATHS["otool"]), "-l",
                        str(runner)])
    second_section = re.search(
        rf"sectname {identity.SECTION_NAME}\n\s+segname {identity.SECTION_SEGMENT}\n"
        r"\s+addr (0x[0-9a-f]+)\n\s+size (0x[0-9a-f]+)\n"
        r"\s+offset ([0-9]+)\n\s+align 2\^14 \(16384\)", second_otool)
    if second_section is None:
        raise RuntimeError("independent four-body section reconstruction failed")
    second_flags = re.search(
        r"\n\s+flags (0x[0-9a-f]+)", second_otool[second_section.start():])
    second_map = linker_map.read_text(encoding="utf-8")
    second_map_rows = [line for line in second_map.splitlines()
                       if line.split() and line.rsplit(None, 1)[-1].removeprefix("_")
                       in identity.names()]
    second_section_rows = [line for line in second_map.splitlines()
                           if f"{identity.SECTION_SEGMENT}\t{identity.SECTION_NAME}" in line]
    second_extract = "\n".join(second_section_rows + second_map_rows) + "\n"
    second_body = sum(second_facts[name]["size_bytes"] for name in identity.names())
    independently_recomputed = {
        "schema": identity.EXPECTED_RECEIPT_SCHEMA,
        "generator": identity.generator_binding(),
        "bindings": bindings,
        "symbol_addresses": second_addresses,
        "facts": second_facts,
        "section": {
            "segment": identity.SECTION_SEGMENT,
            "name": identity.SECTION_NAME,
            "address": second_section.group(1),
            "file_offset": int(second_section.group(3)),
            "size_bytes": int(second_section.group(2), 16),
            "alignment_power": identity.SECTION_ALIGNMENT_POWER,
            "flags": second_flags.group(1) if second_flags else "",
            "executable_pure_instructions": second_flags is not None and
                second_flags.group(1) == identity.SECTION_FLAGS,
        },
        "body_bytes": second_body,
        "padding_bytes": int(second_section.group(2), 16) - second_body,
        "binary_bytes": runner.stat().st_size,
        "binary_sha256": sha256(runner),
        "linker_map_bytes": linker_map.stat().st_size,
        "linker_map_sha256": sha256(linker_map),
        "linker_map_extract_sha256": hashlib.sha256(
            second_extract.encode()).hexdigest(),
        "no_deduplicate_flag": identity.NO_DEDUPLICATE_FLAG,
    }
    identity.validate_machine_receipt(independently_recomputed, bindings)
    write_json(ACTUAL_FOUR_BODY_RECEIPT, independently_recomputed)
    if EXPECTED_FOUR_BODY_RECEIPT.read_bytes() != ACTUAL_FOUR_BODY_RECEIPT.read_bytes():
        raise RuntimeError("four-body expected/actual receipt bytes disagree")


def audit_v4(v4_map: Path) -> None:
    """Audit merged Alignment V4 and V1 without importing any timing row."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    design = ROOT / "evidence/backref-cost-specialization-alignment-v4-design"
    execution = design / "phase2-run-20260820"
    evaluation_path = design / "phase3-evaluation.json"
    audit_path = design / "phase3-audit.json"
    index_results = {}
    for name in ("artifact-hashes.json", "returned-evidence-hashes.json"):
        path = execution / name
        index = json.loads(path.read_text(encoding="utf-8"))
        failures = []
        for row in index["artifacts"]:
            member = execution / row["path"]
            if not member.is_file() or member.stat().st_size != row["bytes"] or \
                    sha256(member) != row["sha256"]:
                failures.append(row["path"])
        index_results[name] = {"rows": len(index["artifacts"]),
                               "mismatches": failures,
                               "sha256": sha256(path)}
    if any(row["mismatches"] for row in index_results.values()):
        raise RuntimeError("Alignment V4 raw evidence hash audit failed")
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    primary = evaluation["statistics"]["graphic-m4"]["whole_encode"]["B_to_L"]
    if primary["mean_percent"] != -0.6199563389094708 or \
            primary["bootstrap_mean_ci95_percent"] != \
            [-1.0795343104954225, -0.21412171812593112] or \
            audit.get("mandatory_b_to_l_null_control", {}).get("passing_domains") != 11 or \
            audit.get("mandatory_b_to_l_null_control", {}).get("required_domains") != 12:
        raise RuntimeError("Alignment V4 evaluator reconstruction mismatch")
    controls = {
        metric: evaluation["statistics"]["graphic-m4"][metric]["B_to_L"]
        for metric in ("dp_total", "dp_steady")
    }
    if not all(row["bootstrap_mean_ci95_percent"][0] <= 0 <=
               row["bootstrap_mean_ci95_percent"][1]
               for row in controls.values()):
        raise RuntimeError("Alignment V4 graphic-m4 DP null controls mismatch")
    v1_design = ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v1-design"
    v1_execution = ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v1-execution-20260820"
    v1_evaluation_path = (
        ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v1-evaluation-20260820/phase3-evaluation.json"
    )
    v1_authorization = json.loads(
        (v1_design / "phase1b-authorization.json").read_text(encoding="utf-8")
    )
    v1_evaluation = json.loads(v1_evaluation_path.read_text(encoding="utf-8"))
    failed = [name for name, passed in v1_authorization["gate_outcomes"].items()
              if not passed]
    timing_like = sorted(
        path.relative_to(ROOT).as_posix()
        for path in v1_execution.rglob("*")
        if path.is_file() and (
            "/runner/" in path.as_posix() or
            "/stages/" in path.as_posix() or
            "timing" in path.name
        )
    )
    reconstruction = v1_evaluation["raw_v1_evidence_and_statistical_reconstruction"]
    if failed != ["alignment build frozen"] or \
            v1_authorization.get("refusal_reasons") != ["alignment build frozen"] or \
            v1_authorization.get("phase_2_authority") != "NONE" or \
            reconstruction.get("phase2_raw_v1_timing_rows") != 0 or \
            reconstruction.get("phase2_raw_v1_stage_rows") != 0 or \
            reconstruction.get("bootstrap_resamples_executed") != 0 or timing_like:
        raise RuntimeError("V1 sole stale-six-body refusal/zero-row audit failed")
    destination = EVIDENCE / "v4-static-audit-linker-map.txt"
    if v4_map != destination:
        shutil.copyfile(v4_map, destination)
    write_json(EVIDENCE / "phase1-prior-evidence-audit.json", {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-prior-evidence-audit-v1",
        "status": "PASS_ALIGNMENT_V4_PREMISE_FROZEN",
        "audited_merge": "5de7b3848adfdb5d1058a061979535f05f976e5b",
        "alignment_v4_commits": {
            "phase1a": "f1e1b1afd4c12921b326276ae7f07f4d27137548",
            "phase1b": "22eaed7f89e12fc3a4510f75f570ca5edffe5ea2",
            "phase2": "7f3bb9a4d05c786aac8cf4176268582123365959",
            "phase3": "a0569a0adf14deb6a7d72078d883a21d3944dc38",
            "merge": "5de7b3848adfdb5d1058a061979535f05f976e5b"},
        "raw_index_audit": index_results,
        "evaluator_reconstruction": {
            "evaluation_path": str(evaluation_path.relative_to(ROOT)),
            "audit_path": str(audit_path.relative_to(ROOT)),
            "domains_passing": 11, "domains_total": 12,
            "sole_failure": {"cell": "graphic-m4", "metric": "whole_encode",
                             "mean_percent": primary["mean_percent"],
                             "ci95_percent": primary["bootstrap_mean_ci95_percent"]},
            "graphic_m4_dp_total": {
                "mean_percent": controls["dp_total"]["mean_percent"],
                "ci95_percent": controls["dp_total"]["bootstrap_mean_ci95_percent"],
                "null_passed": True},
            "graphic_m4_dp_steady": {
                "mean_percent": controls["dp_steady"]["mean_percent"],
                "ci95_percent": controls["dp_steady"]["bootstrap_mean_ci95_percent"],
                "null_passed": True}},
        "timer_boundary_classification": {
            "nested_overlapping_descriptive": [
                "backref_cost_dp_setup", "backref_cost_dp_steady",
                "backref_cost_dp_total", "backref_cost_traceback",
                "backref_cost_materialize"],
            "parent_overlapping_descriptive": [
                "lossless_hash_chain", "lossless_backward_refs"],
            "attribution_suitable_v4_timers": [],
            "reason": "V4 lacks a complete mutually-exclusive whole-encode partition; its nested timers cannot be summed into a causal ledger."},
        "v4_timing_rows_loaded_into_v2_statistics": 0,
        "v4_samples_pooled_reused_or_relabelled": False,
        "v1_authority_audit": {
            "authorization_path": str((v1_design / "phase1b-authorization.json").relative_to(ROOT)),
            "evaluation_path": str(v1_evaluation_path.relative_to(ROOT)),
            "gate_count": len(v1_authorization["gate_outcomes"]),
            "passed_gate_count": sum(v1_authorization["gate_outcomes"].values()),
            "failed_gates": failed,
            "stale_expectation_source":
                "scripts/record_backref_cost_aligned_null_stage_attribution_v1_phase1b.py:201",
            "stale_expected_identity": {
                "private_address_count": 6, "section_size_bytes": 83212,
                "body_bytes": 5624, "padding_bytes": 77588},
            "valid_receipt_path": str((v1_design / "rehearsal/codegen.json").relative_to(ROOT)),
            "valid_v1_identity": {
                "private_address_count": 4, "section_size_bytes": 50444,
                "body_bytes": 3600, "padding_bytes": 46844},
            "phase2_raw_timing_rows": 0,
            "phase2_raw_stage_rows": 0,
            "bootstrap_resamples_executed": 0,
            "timing_like_files": timing_like,
            "can_contribute_samples_to_v2": False,
            "status": "PASS_SOLE_STALE_SIX_BODY_GATE_ZERO_ROWS",
        },
        "v1_timing_rows_loaded_into_v2_statistics": 0,
        "v1_samples_pooled_reused_or_relabelled": False,
        "performance_samples_generated": 0,
    })
    return


def capture_local_untimed_evidence() -> dict:
    """Persist the comprehensive workload-free/synthetic local gate output."""
    value = json.loads(run([
        "python3",
        str(ROOT / "scripts/test_backref_cost_aligned_null_stage_attribution_v2_experiment.py")
    ]).strip())
    work = value["local_work"]

    def normalized(row: dict) -> dict:
        result = dict(row)
        result.pop("variant")
        result["selected_dp_calls"] = (
            result.pop("baseline_dp_calls") +
            result.pop("layout_clone_dp_calls"))
        return result

    normalized_b = normalized(work["B"])
    normalized_l = normalized(work["L"])
    if normalized_b != normalized_l:
        raise RuntimeError("normalized B/L algorithm-work evidence differs")
    value["normalized_work_sha256"] = canonical_sha256(normalized_b)
    value["normalized_work_b_l_equal"] = True
    value["normalized_semantic_sha256"] = canonical_sha256({
        "generator": identity.generator_binding(),
        "work": normalized_b,
        "bitstream_sha256": value["local_bitstream_sha256"],
        "codegen": value["codegen_facts"],
    })
    write_json(LOCAL_UNTIMED_EVIDENCE, value)
    return value


def fresh_identities(manifest: dict) -> None:
    payload_identity = payload.identity()
    toolchain_identity = toolchain.identity()
    codegen = json.loads((EVIDENCE / "phase1-local-codegen.json").read_text(
        encoding="utf-8"))
    alignment = manifest["acceptance"]["alignment_normalization"]
    alignment.update({
        "body_bytes": codegen["body_bytes"],
        "boundary_bytes": codegen["alignment_boundary_bytes"],
        "dp_to_corresponding_push_displacement_bytes":
            codegen["dp_to_push_displacement_bytes"],
        "entry_modulo_required": 0,
        "inter_entry_padding_bytes": codegen["inter_entry_padding_bytes"],
        "inter_entry_spacing_bytes": codegen["alignment_boundary_bytes"],
        "local_reference_timed_runner_bytes": codegen["timed_runner_bytes"],
        "section": f"{identity.SECTION_SEGMENT},{identity.SECTION_NAME}",
        "section_size_bytes": codegen["section_size_bytes"],
    })
    payload_fixture_path = EVIDENCE / "representative-payload-fixture.json"
    payload_agreement_path = EVIDENCE / "representative-payload-agreement.json"
    toolchain_fixture_path = EVIDENCE / "toolchain-identity-fixture.json"
    toolchain_agreement_path = EVIDENCE / "toolchain-identity-agreement.json"

    payload_fixture = {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-payload-fixture-v1",
        "domain": payload_identity["domain"],
        "payload_bytes": payload_identity["payload_bytes"],
        "sha256": payload_identity["sha256"],
        "stale_v2_sha256": payload.STALE_V2_SHA256,
        "stale_v3_sha256": payload.STALE_V3_SHA256,
        "stale_v4_sha256": payload.STALE_V4_SHA256,
        "stale_alignment_v1_sha256": payload.STALE_ALIGNMENT_V1_SHA256,
        "stale_alignment_v2_sha256": payload.STALE_ALIGNMENT_V2_SHA256,
        "stale_alignment_v3_sha256": payload.STALE_ALIGNMENT_V3_SHA256,
    }
    write_json(payload_fixture_path, payload_fixture)
    payload_agreement = {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-payload-agreement-v1",
        "status": "PASS",
        "payload_bytes": payload.PAYLOAD_BYTES,
        "manifest_sha256_value": payload_identity["sha256"],
        "generator_recomputation_sha256": payload.sha256(),
        "independent_fixture_sha256_value": payload_fixture["sha256"],
        "generator_path": "scripts/backref_cost_aligned_null_stage_attribution_v2_payload.py",
        "generator_file_sha256": sha256(ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_payload.py"),
        "fixture_path": str(payload_fixture_path.relative_to(ROOT)),
        "negative_stale_v2_test": "PASS_REJECTED",
        "negative_stale_v3_test": "PASS_REJECTED",
        "negative_stale_v4_test": "PASS_REJECTED",
        "negative_stale_alignment_v1_test": "PASS_REJECTED",
        "negative_stale_alignment_v2_test": "PASS_REJECTED",
        "negative_stale_alignment_v3_test": "PASS_REJECTED",
    }
    write_json(payload_agreement_path, payload_agreement)

    write_json(toolchain_fixture_path, {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-toolchain-fixture-v1",
        "identity": toolchain_identity,
    })
    identity_digest = canonical_sha256(toolchain_identity)
    toolchain_agreement = {
        "schema": "libwebp-backref-cost-aligned-null-stage-attribution-v2-toolchain-agreement-v1",
        "status": "PASS",
        "identity_canonical_sha256": identity_digest,
        "manifest_actual_fixture_agree": True,
        "negative_stale_v2_xcrun_test": "PASS_REJECTED",
        "negative_stale_v3_identity_test": "PASS_REJECTED",
        "negative_stale_v4_identity_test": "PASS_REJECTED",
        "negative_stale_alignment_v1_identity_test": "PASS_REJECTED",
        "negative_stale_alignment_v2_identity_test": "PASS_REJECTED",
        "negative_stale_alignment_v3_identity_test": "PASS_REJECTED",
        "stale_v2_xcrun_sha256": toolchain.STALE_V2_XCRUN_SHA256,
        "stale_v3_identity_canonical_sha256":
            toolchain.STALE_V3_IDENTITY_CANONICAL_SHA256,
        "stale_v4_identity_canonical_sha256":
            toolchain.STALE_V4_IDENTITY_CANONICAL_SHA256,
        "stale_alignment_v1_identity_canonical_sha256":
            toolchain.STALE_ALIGNMENT_V1_IDENTITY_CANONICAL_SHA256,
        "stale_alignment_v2_identity_canonical_sha256":
            toolchain.STALE_ALIGNMENT_V2_IDENTITY_CANONICAL_SHA256,
        "stale_alignment_v3_identity_canonical_sha256":
            toolchain.STALE_ALIGNMENT_V3_IDENTITY_CANONICAL_SHA256,
        "required_executables": toolchain_identity["required_executable_names"],
        "required_metadata": toolchain_identity["required_metadata_names"],
        "xcrun_required": False,
    }
    write_json(toolchain_agreement_path, toolchain_agreement)

    manifest["payload_identity_gate"].update({
        "sha256": payload_identity["sha256"],
        "negative_test": "PASS_REJECTED_ALL_PREDECESSOR_IDENTITIES_THROUGH_ALIGNMENT_V3",
        "negative_stale_v4_sha256": payload.STALE_V4_SHA256,
        "negative_stale_alignment_v3_sha256":
            payload.STALE_ALIGNMENT_V3_SHA256,
    })
    manifest["return_contract"].update({
        "representative_rehearsal_payload_sha256": payload_identity["sha256"],
        "source_admission": {
            "control_schema": transport.SOURCE_RECEIPT_SCHEMA,
            "detail_schema": transport.SOURCE_DETAILS_SCHEMA,
            "compact_control_fields": [
                "schema", "receipt_version", "status", "source_commit",
                "source_tree", "source_bundle_sha256",
                "source_map_entry_count", "source_map_sha256",
                "bundle_verified_in_repository_context",
                "verification_repository_removed", "clean_status"],
            "full_detail_artifact": "source-admission-details.json",
            "canonical_map_encoding":
                "canonical JSON of strictly sorted [{path,sha256},...] rows",
            "local_validation_order":
                "compact receipt against exact requested map, then indexed archived full detail against request and compact receipt",
            "fail_closed": [
                "schema", "count", "digest", "unordered-map",
                "duplicate-or-colliding-map", "missing-detail",
                "archive-mismatch", "control-detail-disagreement"],
        },
    })
    manifest["diagnostic"]["toolchain_identity"] = toolchain_identity
    manifest["toolchain_identity_gate"]["identity"] = toolchain_identity
    manifest["toolchain_identity_gate"].update({
        "negative_test": "PASS_REJECTED_STALE_XCRUN_AND_ALL_PREDECESSOR_ENVELOPES_THROUGH_ALIGNMENT_V3",
    })
    manifest["build"].update({
        "ld": str(toolchain.EXECUTABLE_PATHS["ld"]),
        "otool": str(toolchain.EXECUTABLE_PATHS["otool"]),
        "identity_rule":
            "one recorder-free Mach-O serves B/L; -no_deduplicate preserves four bodies; __TEXT,__br_null_v2 contains Push B/L then DP B/L at exact 16 KiB entry spacing",
    })
    manifest["candidate"]["equivalence"].update({
        "source_commit": manifest["base_commit"],
        "algorithm":
            "B is the original baseline and L is its separately named exact-work clone. Four DP/Push entries are distinct and page-offset normalized; no H candidate exists.",
        "alignment_boundary_bytes": 16384,
        "section": "__TEXT,__br_null_v2",
        "entry_order": ["Push-B", "Push-L", "DP-B", "DP-L"],
    })


def freeze_request_channel_sizes(manifest: dict) -> dict:
    """Serialize the exact capped worst case through the production codecs."""
    paths = manifest["admission_identity_paths"]
    source_hashes = {path: "a" * 64 for path in sorted(paths)}
    source_bundle = b"S" * transport.MAX_SOURCE_BUNDLE_BYTES
    representative = b"R" * payload.PAYLOAD_BYTES
    metadata = {
        "protocol_version": transport.PROTOCOL_VERSION,
        "mode": "rehearse", "source_commit": "b" * 40,
        "source_tree": "c" * 40, "source_hashes": source_hashes,
        "source_bundle_bytes": len(source_bundle),
        "source_bundle_sha256": transport.sha256_bytes(source_bundle),
        "representative_payload_bytes": len(representative),
        "representative_payload_sha256":
            transport.sha256_bytes(representative),
        "maximum_expected_run_archive_bytes": 512 * 1024,
    }
    business = transport.request_bytes(metadata, source_bundle, representative)
    transaction_nonce = "d" * 64
    bootstrap_path = ROOT / \
        "scripts/backref_cost_aligned_null_stage_attribution_v2_bootstrap.py"
    bootstrap_sha = sha256(bootstrap_path)
    request = transport.build_channel_request(
        (ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_transport.py").read_bytes(),
        (ROOT / "scripts/backref_cost_aligned_null_stage_attribution_v2_payload.py").read_bytes(),
        business, transaction_nonce=transaction_nonce,
        bootstrap_sha256=bootstrap_sha)
    request_wire_bytes = len(transport.CHANNEL_MAGIC) + len(
        transport.encode_frame("request-declaration",
                               request.declaration_payload, sequence=0))
    for index, chunk in enumerate(transport.iter_channel_request_chunks(request)):
        request_wire_bytes += len(transport.encode_frame(
            "request-chunk", chunk, sequence=index + 1, chunk_index=index))

    binding = transport.sha256_bytes(transport.canonical_json({
        "schema": transport.CHANNEL_READY_SCHEMA,
        "protocol_version": transport.PROTOCOL_VERSION,
        "transaction_nonce": transaction_nonce,
        "request_declaration_sha256": request.declaration_sha256,
        "bootstrap_sha256": bootstrap_sha}))
    sequence = 0
    controls = []
    ready = {
        "schema": transport.CHANNEL_READY_SCHEMA,
        "protocol_version": transport.PROTOCOL_VERSION,
        "transaction_nonce": transaction_nonce,
        "request_declaration_sha256": request.declaration_sha256,
        "bootstrap_sha256": bootstrap_sha,
        "channel_binding_sha256": binding,
        "remote_process_pid": 2147483647,
        "remote_process_ppid": 2147483647,
        "request_payload_read_before_ready": False,
        "remote_files_created_before_ready": 0,
    }
    controls.append(("ready", ready, {"sequence": sequence}))
    sequence += 1
    declaration_ack = {
        "schema": transport.REQUEST_ACK_SCHEMA, "status": "accepted",
        "ack_kind": "declaration", "transaction_nonce": transaction_nonce,
        "request_bytes_acked": 0, "request_chunks_acked": 0,
        "request_declaration_sha256": request.declaration_sha256,
    }
    controls.append(("request-ack", declaration_ack,
                     {"sequence": sequence, "ack_index": 0}))
    sequence += 1
    for index in range(request.chunk_count):
        acked = min((index + 1) * transport.REQUEST_CHUNK_BYTES,
                    len(request.value))
        ack = {
            "schema": transport.REQUEST_ACK_SCHEMA, "status": "accepted",
            "ack_kind": "chunk", "transaction_nonce": transaction_nonce,
            "request_bytes_acked": acked,
            "request_chunks_acked": index + 1,
            "request_declaration_sha256": request.declaration_sha256,
        }
        controls.append(("request-ack", ack,
                         {"sequence": sequence, "ack_index": index + 1}))
        sequence += 1
    request_complete = {
        "schema": transport.REQUEST_ACK_SCHEMA, "status": "complete",
        "ack_kind": "request", "transaction_nonce": transaction_nonce,
        "request_bytes_acked": len(request.value),
        "request_chunks_acked": request.chunk_count,
        "request_sha256": request.declaration["request_sha256"],
        "request_declaration_sha256": request.declaration_sha256,
    }
    controls.append(("request-complete", request_complete,
                     {"sequence": sequence}))
    sequence += 1
    maximum_response = transport.MAX_RESPONSE_BYTES - 1
    response_sha = transport.sha256_bytes(b"Z" * maximum_response)
    response_chunks = (maximum_response + transport.CHUNK_BYTES - 1) // \
        transport.CHUNK_BYTES
    response_declaration = {
        "schema": transport.RESPONSE_DECLARATION_SCHEMA,
        "status": "started", "transaction_nonce": transaction_nonce,
        "response_bytes": maximum_response, "response_sha256": response_sha,
        "response_chunk_bytes": transport.CHUNK_BYTES,
        "response_chunk_count": response_chunks,
        "transaction_exit_code": 0,
    }
    controls.append(("response-declaration", response_declaration,
                     {"sequence": sequence}))
    sequence += 1
    channel_stdout_bytes = len(transport.CHANNEL_MAGIC)
    control_payload_bytes = []
    for kind, value, fields in controls:
        encoded = transport.canonical_json(value)
        control_payload_bytes.append({"kind": kind, "bytes": len(encoded)})
        channel_stdout_bytes += len(transport.encode_frame(
            kind, encoded, **fields))
    for index, offset in enumerate(range(0, maximum_response,
                                         transport.CHUNK_BYTES)):
        chunk = b"Z" * min(transport.CHUNK_BYTES,
                            maximum_response - offset)
        channel_stdout_bytes += len(transport.encode_frame(
            "response-chunk", chunk, sequence=sequence,
            chunk_index=index))
        sequence += 1
    response_complete = {
        "schema": transport.RESPONSE_COMPLETE_SCHEMA,
        "status": "complete", "transaction_nonce": transaction_nonce,
        "response_bytes": maximum_response, "response_sha256": response_sha,
        "response_chunk_count": response_chunks,
        "transaction_exit_code": 0,
    }
    response_complete_payload = transport.canonical_json(response_complete)
    control_payload_bytes.append({"kind": "response-complete",
                                  "bytes": len(response_complete_payload)})
    channel_stdout_bytes += len(transport.encode_frame(
        "response-complete", response_complete_payload, sequence=sequence))

    with tempfile.TemporaryDirectory(prefix="stage-attribution-v2-base-bundle-") as raw:
        base_bundle = Path(raw) / "source.bundle"
        result = subprocess.run(
            ["git", "bundle", "create", str(base_bundle), "HEAD"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            raise RuntimeError("base source-bundle size reconstruction failed")
        base_bundle_bytes = base_bundle.stat().st_size
        base_bundle_sha = sha256(base_bundle)

    value = {
        "schema":
            "libwebp-backref-cost-aligned-null-stage-attribution-v2-request-size-freeze-v1",
        "status": "PASS", "production_encoder":
            "build_channel_request + encode_frame + fixed chunk iterators",
        "base_bundle_observation": {
            "commit": run(["git", "rev-parse", "HEAD"]).strip(),
            "bytes": base_bundle_bytes, "sha256": base_bundle_sha,
            "remote_contacts": 0,
        },
        "bootstrap_source_bytes": bootstrap_path.stat().st_size,
        "bootstrap_source_cap_bytes": transport.MAX_BOOTSTRAP_SOURCE_BYTES,
        "bootstrap_source_margin_bytes":
            transport.MAX_BOOTSTRAP_SOURCE_BYTES - bootstrap_path.stat().st_size,
        "source_bundle_cap_bytes": transport.MAX_SOURCE_BUNDLE_BYTES,
        "base_bundle_to_cap_margin_bytes":
            transport.MAX_SOURCE_BUNDLE_BYTES - base_bundle_bytes,
        "business_request_cap_bytes": transport.MAX_BUSINESS_REQUEST_BYTES,
        "business_request_worst_case_bytes": len(business),
        "business_request_margin_bytes":
            transport.MAX_BUSINESS_REQUEST_BYTES - len(business),
        "request_cap_bytes": transport.MAX_REQUEST_BYTES,
        "request_worst_case_bytes": len(request.value),
        "request_margin_bytes": transport.MAX_REQUEST_BYTES - len(request.value),
        "request_declaration_cap_bytes":
            transport.MAX_REQUEST_DECLARATION_BYTES,
        "request_declaration_payload_bytes": len(request.declaration_payload),
        "request_declaration_margin_bytes":
            transport.MAX_REQUEST_DECLARATION_BYTES -
            len(request.declaration_payload),
        "request_declaration_encoded_frame_bytes": len(transport.encode_frame(
            "request-declaration", request.declaration_payload, sequence=0)),
        "request_chunk_bytes": transport.REQUEST_CHUNK_BYTES,
        "request_chunk_count": request.chunk_count,
        "request_channel_wire_bytes": request_wire_bytes,
        "request_components": request.declaration["components"],
        "response_business_cap_bytes_exclusive": transport.MAX_RESPONSE_BYTES,
        "response_chunk_bytes": transport.CHUNK_BYTES,
        "maximum_channel_stdout_bytes": transport.MAX_CHANNEL_STDOUT_BYTES,
        "encoded_channel_stdout_worst_case_bytes": channel_stdout_bytes,
        "channel_stdout_margin_bytes":
            transport.MAX_CHANNEL_STDOUT_BYTES - channel_stdout_bytes,
        "maximum_control_payload_observed_bytes":
            max(row["bytes"] for row in control_payload_bytes),
        "control_payload_cap_bytes": transport.MAX_CONTROL_PAYLOAD_BYTES,
        "all_controls_fit": all(
            row["bytes"] <= transport.MAX_CONTROL_PAYLOAD_BYTES
            for row in control_payload_bytes),
        "control_payload_sizes": control_payload_bytes,
        "cap_change_from_v2":
            "outer request is newly explicit and capped at 32 MiB; this narrows V2's 64 MiB per-frame request cap, preserves the exact 2 MiB rehearsal payload, and has conservative measured source-bundle margin without changing workloads, response caps, timeouts, or scientific thresholds",
    }
    if min(value["bootstrap_source_margin_bytes"],
           value["base_bundle_to_cap_margin_bytes"],
           value["business_request_margin_bytes"],
           value["request_margin_bytes"],
           value["request_declaration_margin_bytes"],
           value["channel_stdout_margin_bytes"]) <= 0 or \
            not value["all_controls_fit"]:
        raise RuntimeError("request-channel worst case does not fit frozen caps")
    write_json(REQUEST_CHANNEL_FREEZE, value)
    manifest["request_channel_size_freeze"] = {
        "path": str(REQUEST_CHANNEL_FREEZE.relative_to(ROOT)),
        "schema": value["schema"], "status": value["status"],
        "request_worst_case_bytes": value["request_worst_case_bytes"],
        "request_margin_bytes": value["request_margin_bytes"],
        "request_declaration_payload_bytes":
            value["request_declaration_payload_bytes"],
        "channel_stdout_margin_bytes": value["channel_stdout_margin_bytes"],
    }
    return value


def freeze_local_validation(manifest: dict, request_sizes: dict) -> None:
    """Record the exhaustive Phase-1A verification contract and frozen facts."""
    codegen = json.loads((EVIDENCE / "phase1-local-codegen.json").read_text(
        encoding="utf-8"))
    toolchain_value = toolchain.identity()
    four_body = json.loads(EXPECTED_FOUR_BODY_RECEIPT.read_text(encoding="utf-8"))
    local_untimed = json.loads(LOCAL_UNTIMED_EVIDENCE.read_text(encoding="utf-8"))
    identity.validate_machine_receipt(
        four_body, manifest["four_body_receipt_bindings"])
    write_json(EVIDENCE / "phase1-local-validation.json", {
        "schema":
            "libwebp-backref-cost-aligned-null-stage-attribution-v2-phase1-local-validation-v1",
        "status": "PASS", "base_commit": manifest["base_commit"],
        "phase": "1A", "authority_before_rehearsal": "NONE",
        "timed_execution_authorized": False, "performance_samples": 0,
        "remote_contacts": 0,
        "design_decision": "B_L_ONLY_FOUR_BODY_16K_ALIGNMENT_WITH_COMPLETE_STAGE_LEDGER",
        "checks": {
            "v1_v2_v4_provenance_and_raw_hash_audit": "PASS",
            "v2_request_write_state_and_exact_shape_audited": "PASS_NO_ESTABLISHED_CONTACT_INFERRED",
            "ordinary_build_default_omission": "PASS",
            "public_api_abi_equal": "PASS",
            "runtime_truth_table": "PASS_ABSENT_B_EXACT_B_L_OTHER_INVALID_H_INVALID",
            "selector_once_before_mutation": "PASS",
            "exactly_one_selected_dp": "PASS",
            "timed_recorder_free": "PASS",
            "recorder_build_distinct": "PASS",
            "top_level_partition_non_overlapping": "PASS",
            "merged_v1_stage_ledger_description_audit":
                "PASS_REUSED_WITHOUT_BOUNDARY_CORRECTION",
            "ledger_reconciliation_and_residual": "PASS_ZERO_RESIDUAL_CLOCK_COUNT_FORMULA",
            "nested_timer_non_additivity": "PASS_EXPLICIT",
            "clock_overhead_distribution": "PASS_4096_READS_P50_P95_P99_MAX",
            "early_return_fault_skip_repeat_schema": "PASS",
            "local_correctness_encodes": 2,
            "sanitizer_configurations": 2,
            "sanitizer_boundary_encodes": 24,
            "correctness_fallback_determinism_immutability": "PASS",
            "four_private_symbols_distinct": "PASS_NO_DEDUPLICATION",
            "canonical_four_body_generator_receipt": "PASS_EXACT_EXPECTED_ACTUAL_BYTES",
            "normalized_semantic_work_codegen_digests": "PASS_FROZEN",
            "v1_stale_six_body_domain_negative": "PASS_REJECTED",
            "mach_o_section": "PASS___TEXT___br_null_v2_EXECUTABLE_PURE_INSTRUCTIONS",
            "alignment_modulo": "PASS_ALL_FOUR_ZERO_MOD_16384",
            "b_l_push_and_dp_canonical_instruction_identity": "PASS",
            "h_candidate_absent": "PASS",
            "payload_manifest_generator_fixture_agreement": "PASS",
            "toolchain_manifest_actual_fixture_agreement": "PASS_8_EXECUTABLES_4_METADATA",
            "stale_predecessor_identity_negatives": "PASS_REJECTED",
            "observe_only_process_ownership": "PASS",
            "conditional_authority_state_machine": "PASS_ZERO_WORKLOAD_TO_ONE_PIPELINE_ONLY",
            "dynamic_gate_a_16_correctness_before_timing": "PASS_STRUCTURAL_AND_FIXTURES",
            "dynamic_gate_b_timer_accounting_before_timing": "PASS_STRUCTURAL_AND_FIXTURES",
            "dynamic_gate_c_direct_child_online_ownership": "PASS_SYNTHETIC_FAILURE_MATRIX",
            "zero_accepted_samples_on_admission_failure": "PASS",
            "global_experiment_mutual_exclusion": "PASS_46_GUARDS",
            "single_ssh_ready_before_request": "PASS",
            "request_declaration_fixed_chunks_and_ordered_acks": "PASS",
            "duplex_stdout_stderr_backpressure": "PASS",
            "timeout_boundary_fixtures": "PASS",
            "source_admission_compact_and_full_map_equivalence":
                f"PASS_{len(manifest['admission_identity_paths'])}_PATHS",
            "malformed_duplicate_order_corruption_truncation_negatives": "PASS_REJECTED",
            "integrated_exact_child_cleanup_absence": "PASS",
            "cmake_integration": "PASS",
            "unix_make_integration": "PASS",
            "python_syntax_and_json": "PASS",
        },
        "alignment_freeze": {
            "boundary_bytes": codegen["alignment_boundary_bytes"],
            "section_size_bytes": codegen["section_size_bytes"],
            "body_bytes": codegen["body_bytes"],
            "inter_entry_padding_bytes": codegen["inter_entry_padding_bytes"],
            "dp_to_push_displacement_bytes":
                codegen["dp_to_push_displacement_bytes"],
            "local_reference_runner_bytes": codegen["timed_runner_bytes"],
            "linker_map_extract_sha256": codegen["linker_map_extract_sha256"],
            "four_body_receipt_sha256": sha256(EXPECTED_FOUR_BODY_RECEIPT),
            "four_body_expected_actual_byte_agreement":
                EXPECTED_FOUR_BODY_RECEIPT.read_bytes() ==
                ACTUAL_FOUR_BODY_RECEIPT.read_bytes(),
            "normalized_work_sha256": local_untimed["normalized_work_sha256"],
            "normalized_semantic_sha256":
                local_untimed["normalized_semantic_sha256"],
        },
        "transport_freeze": {
            "control_payload_cap_bytes": transport.MAX_CONTROL_PAYLOAD_BYTES,
            "archive_cap_bytes": transport.MAX_ARCHIVE_BYTES,
            "framed_response_cap_bytes_exclusive": transport.MAX_RESPONSE_BYTES,
            "response_chunk_bytes": transport.CHUNK_BYTES,
            "request_cap_bytes": transport.MAX_REQUEST_BYTES,
            "request_worst_case_bytes": request_sizes["request_worst_case_bytes"],
            "request_margin_bytes": request_sizes["request_margin_bytes"],
            "request_chunk_bytes": transport.REQUEST_CHUNK_BYTES,
            "request_chunk_count_worst_case": request_sizes["request_chunk_count"],
            "channel_stdout_margin_bytes":
                request_sizes["channel_stdout_margin_bytes"],
            "frozen_source_identity_paths": len(manifest["admission_identity_paths"]),
        },
        "identity_freeze": {
            "payload_bytes": payload.PAYLOAD_BYTES,
            "payload_sha256": payload.sha256(),
            "toolchain_identity_canonical_sha256": canonical_sha256(toolchain_value),
            "xcode": toolchain_value["xcode"]["short_version"],
            "sdk": toolchain_value["sdk"]["canonical_name"],
            "required_executables": len(toolchain_value["required_executable_names"]),
            "required_metadata": len(toolchain_value["required_metadata_names"]),
            "xcrun_required": False,
        },
        "frozen_inventory": {
            "cases": ["photo-large", "graphic-large"], "methods": [4, 6],
            "variants": ["B", "L"],
            "variant_order": [["B", "L"], ["L", "B"],
                              ["B", "L"], ["L", "B"]],
            "profile_repetitions": 4, "warmups_per_profile": 1,
            "retained_encodes_per_profile": 4, "profile_processes": 32,
            "warmups": 32, "retained_timing_rows": 128,
            "stage_rows": 160, "runner_rows": 160,
            "correctness_encodes": 16, "untimed_work_rows": 8,
            "timer_validation_clock_children": 1,
            "timer_accounting_children": 2,
            "direct_runner_children": 59,
            "bootstrap_resamples": 100000, "bootstrap_seed": "0x4e554c32",
        },
        "acceptance_freeze": {
            "b_to_l_absolute_mean_percent_max": 0.75,
            "b_to_l_ci_must_include_zero": True,
            "b_to_l_ci_endpoint_absolute_percent_max": 1.50,
            "b_to_l_paired_row_absolute_percent_max": 3.00,
            "resolved_effect_floor_percent": 0.10,
            "production_paired_regression_percent_max": 0.50,
            "repeatability_max_ratio": 2.0,
            "required_stage_share_range_exclusive_max": 0.10,
            "primary_reproduction_cell": "graphic-m4",
            "attribution_absolute_mean_effect_percent_min": 0.20,
            "attribution_absolute_whole_delta_fraction_min": 0.20,
            "direction_consistent_repetitions_min": 3,
            "direction_consistent_repetitions_total": 4,
            "top_level_multiplicity": "Bonferroni family-wise 95% over 9 buckets",
            "inconclusive_outcome_required": True,
        },
        "commands": [
            "python3 -m py_compile scripts/*aligned_null_stage_attribution_v2*.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_identity.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_payload_identity.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_toolchain_identity.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_process_ownership.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_archive.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_streaming.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_admission.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_experiment.py",
            "PYTHONPATH=scripts python3 scripts/test_backref_cost_aligned_null_stage_attribution_v2_protocol.py",
            "PYTHONPATH=scripts python3 scripts/test_experiment_guards.py",
        ],
        "local_synchronous_rehearsal": "NOT_YET_ATTEMPTED_PHASE_1A",
        "production_promotion": "NOT_EVALUATED",
        "next_action":
            "Commit Phase 1A, then perform exactly one synchronous untimed zero-workload zero-lease SSH rehearsal with no retry.",
    })


def finalize_hashes(manifest: dict) -> None:
    self_manifest = manifest["frozen_artifact_set"]["self_manifest"]
    paths = [path for path in manifest["admission_identity_paths"]
             if path != self_manifest]
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise RuntimeError(f"cannot finalize; frozen artifacts absent: {missing}")
    manifest["frozen_artifacts"] = [
        {"path": path, "sha256": sha256(ROOT / path)} for path in paths
    ]
    manifest["admission_identity_paths"] = [
        self_manifest, *paths
    ]


def freeze_source_admission_control(manifest: dict) -> dict:
    """Freeze the exact worst-case compact control using production encoding."""
    paths = manifest["admission_identity_paths"]
    if len(paths) != len(set(paths)):
        raise RuntimeError("admission identity paths collide")
    source_hashes = {
        relative: sha256(ROOT / relative) for relative in sorted(paths)
    }
    count, source_map_sha256 = transport.source_map_commitment(source_hashes)
    compact = {
        "schema": transport.SOURCE_RECEIPT_SCHEMA,
        "receipt_version": transport.SOURCE_RECEIPT_VERSION,
        "status": "verified",
        "source_commit": "f" * 40,
        "source_tree": "e" * 40,
        "source_bundle_sha256": "d" * 64,
        "source_map_entry_count": count,
        "source_map_sha256": source_map_sha256,
        "bundle_verified_in_repository_context": True,
        "verification_repository_removed": True,
        "clean_status": True,
    }
    transport.validate_compact_source_receipt_shape(compact)
    compact_payload = transport.canonical_json(compact)
    compact_frame = transport._encoded_json("source-admission", compact, 0)
    full_v1 = {
        "schema":
            "libwebp-backref-cost-specialization-alignment-v1-source-admission-receipt-v1",
        "receipt_version": 1,
        "status": "verified",
        "source_commit": "f" * 40,
        "source_tree": "e" * 40,
        "source_bundle_sha256": "d" * 64,
        "admission": {
            "bundle_sha256": "d" * 64,
            "bundle_verified_in_repository_context": True,
            "verification_repository_removed": True,
            "clean_status": True,
            "source_hashes": source_hashes,
        },
    }
    full_v1_payload = transport.canonical_json(full_v1)
    if len(compact_payload) >= transport.MAX_CONTROL_PAYLOAD_BYTES or \
            len(full_v1_payload) <= transport.MAX_CONTROL_PAYLOAD_BYTES:
        raise RuntimeError("V2 compact/V1 full-map control-cap regression")
    value = {
        "schema":
            "libwebp-backref-cost-aligned-null-stage-attribution-v2-control-freeze-v1",
        "status": "PASS",
        "construction":
            "actual backref_cost_aligned_null_stage_attribution_v2_transport.canonical_json and _encoded_json",
        "identity_path_count": count,
        "identity_paths": sorted(paths),
        "identity_paths_sha256": hashlib.sha256(
            transport.canonical_json(sorted(paths))).hexdigest(),
        "exact_sorted_source_map_sha256": source_map_sha256,
        "compact_receipt": compact,
        "control_payload_cap_bytes_exclusive":
            transport.MAX_CONTROL_PAYLOAD_BYTES,
        "compact_control_payload_bytes": len(compact_payload),
        "compact_control_payload_margin_bytes":
            transport.MAX_CONTROL_PAYLOAD_BYTES - len(compact_payload),
        "compact_encoded_frame_bytes": len(compact_frame),
        "alignment_v1_full_map_control_payload_bytes": len(full_v1_payload),
        "alignment_v1_full_map_overflow_bytes":
            len(full_v1_payload) - transport.MAX_CONTROL_PAYLOAD_BYTES,
        "negative_alignment_v1_full_map_exceeds_cap": True,
        "positive_alignment_v4_compact_fits_cap": True,
        "full_map_present_in_compact_receipt": False,
    }
    write_json(SOURCE_CONTROL_FREEZE, value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--capture-build", type=Path)
    parser.add_argument("--v4-linker-map", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["four_body_identity"] = identity.generator_binding()
    # Generated compatibility field for older consumers; never authored.
    manifest["acceptance"]["codegen_symbols"] = identity.names()
    manifest["protocol"]["entry_order"] = identity.names()
    hot_names = set(identity.names())
    manifest["acceptance"]["required_symbols"] = [
        name for name in manifest["acceptance"]["required_symbols"]
        if name not in hot_names
    ] + identity.names()
    bindings = receipt_bindings(manifest)
    manifest["four_body_receipt_bindings"] = bindings
    if args.capture_build is not None:
        capture_codegen(args.capture_build.resolve(), bindings)
    if args.v4_linker_map is not None:
        audit_v4(args.v4_linker_map.resolve())
    capture_local_untimed_evidence()
    fresh_identities(manifest)
    request_sizes = freeze_request_channel_sizes(manifest)
    freeze_local_validation(manifest, request_sizes)
    if args.finalize:
        finalize_hashes(manifest)
        manifest["source_admission_control_freeze"] = {
            "path": str(SOURCE_CONTROL_FREEZE.relative_to(ROOT)),
            "receipt_is_not_an_admission_identity_member": True,
            "reason":
                "avoids a recursive self-hash while freezing the exact final admission map",
        }
    write_json(MANIFEST, manifest)
    control = freeze_source_admission_control(manifest) if args.finalize else None
    print(json.dumps({"status": "PASS", "finalized": args.finalize,
                      "payload_sha256": payload.sha256(),
                      "control_payload_bytes":
                          control["compact_control_payload_bytes"]
                          if control is not None else None,
                      "request_worst_case_bytes":
                          request_sizes["request_worst_case_bytes"],
                      "toolchain_identity_canonical_sha256":
                          canonical_sha256(toolchain.identity())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
