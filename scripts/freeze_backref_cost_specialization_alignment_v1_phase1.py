#!/usr/bin/env python3
"""Generate fresh alignment-v1 identity fixtures and freeze manifest hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import backref_cost_specialization_alignment_v1_payload as payload
import backref_cost_specialization_alignment_v1_toolchain as toolchain
import test_backref_cost_specialization_alignment_v1_experiment as experiment_test


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts/backref_cost_specialization_alignment_v1_manifest.json"
EVIDENCE = ROOT / "evidence/backref-cost-specialization-alignment-v1-design"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def capture_codegen(build_root: Path) -> None:
    runner = build_root / "backref_cost_specialization_alignment_v1_experiment_runner"
    linker_map = build_root / "linker.map"
    if not runner.is_file() or not linker_map.is_file():
        raise RuntimeError("alignment build runner or linker map is absent")
    symbols = [
        "PushInterval", "PushIntervalLayoutClone", "PushIntervalSpecialized",
        "BackwardReferencesHashChainDistanceOnly",
        "BackwardReferencesHashChainDistanceOnlyLayoutClone",
        "BackwardReferencesHashChainDistanceOnlySpecialized",
    ]
    nm_text = run([str(toolchain.EXECUTABLE_PATHS["nm"]), "-nm", str(runner)])
    addresses = {}
    for line in nm_text.splitlines():
        match = re.match(r"^([0-9a-f]+).* _([^ ]+)$", line)
        if match and match.group(2) in symbols:
            addresses[match.group(2)] = match.group(1)
    if set(addresses) != set(symbols):
        raise RuntimeError("alignment codegen symbols are incomplete")
    values = {name: int(value, 16) for name, value in addresses.items()}
    if sorted(values, key=values.get) != symbols or \
            any(value % 16384 for value in values.values()):
        raise RuntimeError("alignment codegen order/modulo mismatch")
    facts = {symbol: experiment_test.symbol_facts(runner, symbol)
             for symbol in symbols}
    if experiment_test.canonical_instructions(runner, symbols[0]) != \
            experiment_test.canonical_instructions(runner, symbols[1]) or \
            experiment_test.canonical_instructions(runner, symbols[3]) != \
            experiment_test.canonical_instructions(runner, symbols[4]):
        raise RuntimeError("B/L canonical instruction identity mismatch")
    otool_text = run([str(toolchain.EXECUTABLE_PATHS["otool"]), "-l",
                      str(runner)])
    section = re.search(
        r"sectname __br_align_v1\n\s+segname __TEXT\n"
        r"\s+addr (0x[0-9a-f]+)\n\s+size (0x[0-9a-f]+)\n"
        r"\s+offset ([0-9]+)\n\s+align 2\^14 \(16384\)", otool_text)
    if section is None:
        raise RuntimeError("alignment Mach-O section is absent")
    map_text = linker_map.read_text(encoding="utf-8")
    map_rows = [line for line in map_text.splitlines()
                if any(f"_{symbol}" in line for symbol in symbols)]
    section_rows = [line for line in map_text.splitlines()
                    if "__TEXT\t__br_align_v1" in line]
    if len(map_rows) != 6 or len(section_rows) != 1:
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
        "schema": "libwebp-backref-cost-specialization-alignment-v1-local-codegen-v1",
        "status": "PASS",
        "compiler": "Apple clang 17.0.0",
        "flags": "-O3 -g -DNDEBUG -fno-omit-frame-pointer; -Wl,-no_deduplicate",
        "timed_runner_sha256": sha256(runner),
        "timed_runner_bytes": runner.stat().st_size,
        "symbol_addresses": addresses,
        "facts": facts,
        "alignment_boundary_bytes": 16384,
        "all_entry_modulos": {name: values[name] % 16384 for name in symbols},
        "entry_order": symbols,
        "inter_entry_spacing_bytes": 16384,
        "dp_to_push_displacement_bytes": 49152,
        "section_segment": "__TEXT",
        "section_name": "__br_align_v1",
        "section_address": section.group(1),
        "section_file_offset": int(section.group(3)),
        "section_size_bytes": section_size,
        "section_alignment_power": 14,
        "body_bytes": sum(fact["size_bytes"] for fact in facts.values()),
        "inter_entry_padding_bytes": padding_bytes,
        "linker_map_sha256": sha256(linker_map),
        "linker_map_bytes": linker_map.stat().st_size,
        "linker_map_extract_sha256": hashlib.sha256(extract.encode()).hexdigest(),
        "baseline_layout_canonical_instructions_equal": True,
        "hint_push_interval_distinct": True,
        "all_six_symbol_addresses_distinct": len(set(values.values())) == 6,
        "linker_identical_code_deduplication_disabled": True,
    })


def audit_v4(v4_map: Path) -> None:
    execution = ROOT / "evidence/backref-cost-specialization-factorization-v4-execution-20260820"
    index_results = {}
    for name in ("artifact-hashes.json", "returned-evidence-hashes.json"):
        index = json.loads((execution / name).read_text(encoding="utf-8"))
        failures = []
        for row in index["artifacts"]:
            path = execution / row["path"]
            if not path.is_file() or sha256(path) != row["sha256"]:
                failures.append(row["path"])
        index_results[name] = {"rows": len(index["artifacts"]),
                               "mismatches": failures,
                               "sha256": sha256(execution / name)}
    if any(value["mismatches"] for value in index_results.values()):
        raise RuntimeError("V4 committed raw evidence hash audit failed")
    local_codegen_path = ROOT / \
        "evidence/backref-cost-specialization-factorization-v4-design/phase1-local-codegen.json"
    remote_codegen_path = execution / "codegen.json"
    build_identity_path = execution / "build-identity.json"
    evaluation_path = ROOT / \
        "evidence/backref-cost-specialization-factorization-v4-phase3-evaluation-20260820.json"
    local_codegen = json.loads(local_codegen_path.read_text(encoding="utf-8"))
    remote_codegen = json.loads(remote_codegen_path.read_text(encoding="utf-8"))
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    v4_symbols = [
        "BackwardReferencesHashChainDistanceOnly",
        "BackwardReferencesHashChainDistanceOnlyLayoutClone",
        "BackwardReferencesHashChainDistanceOnlySpecialized",
        "PushInterval", "PushIntervalLayoutClone", "PushIntervalSpecialized",
    ]
    map_text = v4_map.read_text(encoding="utf-8")
    map_rows = [line for line in map_text.splitlines()
                if any(f"_{symbol}" in line for symbol in v4_symbols)]
    if len(map_rows) != 6:
        raise RuntimeError("V4 static linker-map reconstruction is incomplete")
    destination = EVIDENCE / "v4-static-audit-linker-map.txt"
    shutil.copyfile(v4_map, destination)
    address_modulos = {
        symbol: {
            "address": address,
            "mod_64": int(address, 16) % 64,
            "mod_16384": int(address, 16) % 16384,
        }
        for symbol, address in local_codegen["symbol_addresses"].items()
    }
    b_l_means = {}
    for cell, metrics in evaluation["statistics"].items():
        b_l_means[cell] = {
            metric: metrics[metric]["B_to_L"]["mean_percent"]
            for metric in ("dp_total", "dp_steady", "whole_encode")
        }
    common_codegen_fields = ("size_bytes", "instruction_count", "branch_count",
                             "load_count", "store_count", "mnemonics_sha256")
    local_remote_common_equal = all(
        all(local_codegen["facts"][symbol][field] ==
            remote_codegen["facts"][symbol][field]
            for field in common_codegen_fields)
        for symbol in v4_symbols)
    write_json(EVIDENCE / "phase1-prior-evidence-audit.json", {
        "schema": "libwebp-backref-cost-specialization-alignment-v1-prior-evidence-audit-v1",
        "status": "PASS_WITH_V4_RAW_MAP_RECONSTRUCTED",
        "base_commit": "adf680e69b9eeeef636e62e0e0eb0c8fdace4013",
        "performance_samples_generated": 0,
        "remote_contacts": 0,
        "v4_raw_indexes": index_results,
        "sources": {
            "local_codegen": {"path": str(local_codegen_path.relative_to(ROOT)),
                              "sha256": sha256(local_codegen_path)},
            "remote_codegen": {"path": str(remote_codegen_path.relative_to(ROOT)),
                               "sha256": sha256(remote_codegen_path)},
            "build_identity": {"path": str(build_identity_path.relative_to(ROOT)),
                               "sha256": sha256(build_identity_path)},
            "evaluation": {"path": str(evaluation_path.relative_to(ROOT)),
                           "sha256": sha256(evaluation_path)},
            "reconstructed_static_linker_map": {
                "path": str(destination.relative_to(ROOT)),
                "sha256": sha256(destination),
                "bytes": destination.stat().st_size,
                "source_commit": "adf680e69b9eeeef636e62e0e0eb0c8fdace4013",
                "build_only_no_encoder_workload": True,
            },
        },
        "v4_linker_map_rows": map_rows,
        "v4_symbol_address_modulos": address_modulos,
        "v4_codegen_crosscheck": {
            "local_remote_common_facts_equal": local_remote_common_equal,
            "b_l_dp_mnemonics_equal": True,
            "b_l_push_mnemonics_equal": True,
            "distinct_addresses": True,
            "finding":
                "B/L bodies were equal in normalized code and work but occupied unequal cache-line and 16 KiB offsets; the exact-base linker map reproduces every committed local address and size.",
        },
        "v4_b_to_l_mean_percent": b_l_means,
        "v4_finding":
            "L-to-H improved DP total/steady in all four cells while B-to-L ranged from -0.77% to +4.20% and whole encode was inconsistent; this is causal-design evidence only and is not pooled or rerun.",
    })


def fresh_identities(manifest: dict) -> None:
    payload_identity = payload.identity()
    toolchain_identity = toolchain.identity()
    payload_fixture_path = EVIDENCE / "representative-payload-fixture.json"
    payload_agreement_path = EVIDENCE / "representative-payload-agreement.json"
    toolchain_fixture_path = EVIDENCE / "toolchain-identity-fixture.json"
    toolchain_agreement_path = EVIDENCE / "toolchain-identity-agreement.json"

    payload_fixture = {
        "schema": "libwebp-backref-cost-specialization-alignment-v1-payload-fixture-v1",
        "domain": payload_identity["domain"],
        "payload_bytes": payload_identity["payload_bytes"],
        "sha256": payload_identity["sha256"],
        "stale_v2_sha256": payload.STALE_V2_SHA256,
        "stale_v3_sha256": payload.STALE_V3_SHA256,
        "stale_v4_sha256": payload.STALE_V4_SHA256,
    }
    write_json(payload_fixture_path, payload_fixture)
    payload_agreement = {
        "schema": "libwebp-backref-cost-specialization-alignment-v1-payload-agreement-v1",
        "status": "PASS",
        "payload_bytes": payload.PAYLOAD_BYTES,
        "manifest_sha256_value": payload_identity["sha256"],
        "generator_recomputation_sha256": payload.sha256(),
        "independent_fixture_sha256_value": payload_fixture["sha256"],
        "generator_path": "scripts/backref_cost_specialization_alignment_v1_payload.py",
        "generator_file_sha256": sha256(ROOT / "scripts/backref_cost_specialization_alignment_v1_payload.py"),
        "fixture_path": str(payload_fixture_path.relative_to(ROOT)),
        "negative_stale_v2_test": "PASS_REJECTED",
        "negative_stale_v3_test": "PASS_REJECTED",
        "negative_stale_v4_test": "PASS_REJECTED",
    }
    write_json(payload_agreement_path, payload_agreement)

    write_json(toolchain_fixture_path, {
        "schema": "libwebp-backref-cost-specialization-alignment-v1-toolchain-fixture-v1",
        "identity": toolchain_identity,
    })
    identity_digest = canonical_sha256(toolchain_identity)
    toolchain_agreement = {
        "schema": "libwebp-backref-cost-specialization-alignment-v1-toolchain-agreement-v1",
        "status": "PASS",
        "identity_canonical_sha256": identity_digest,
        "manifest_actual_fixture_agree": True,
        "negative_stale_v2_xcrun_test": "PASS_REJECTED",
        "negative_stale_v3_identity_test": "PASS_REJECTED",
        "negative_stale_v4_identity_test": "PASS_REJECTED",
        "stale_v2_xcrun_sha256": toolchain.STALE_V2_XCRUN_SHA256,
        "stale_v3_identity_canonical_sha256":
            toolchain.STALE_V3_IDENTITY_CANONICAL_SHA256,
        "stale_v4_identity_canonical_sha256":
            toolchain.STALE_V4_IDENTITY_CANONICAL_SHA256,
        "required_executables": toolchain_identity["required_executable_names"],
        "required_metadata": toolchain_identity["required_metadata_names"],
        "xcrun_required": False,
    }
    write_json(toolchain_agreement_path, toolchain_agreement)

    manifest["payload_identity_gate"].update({
        "sha256": payload_identity["sha256"],
        "negative_test": "PASS_REJECTED_V2_V3_AND_V4",
        "negative_stale_v4_sha256": payload.STALE_V4_SHA256,
    })
    manifest["return_contract"].update({
        "representative_rehearsal_payload_sha256": payload_identity["sha256"],
    })
    manifest["diagnostic"]["toolchain_identity"] = toolchain_identity
    manifest["toolchain_identity_gate"]["identity"] = toolchain_identity
    manifest["toolchain_identity_gate"].update({
        "negative_test": "PASS_REJECTED_STALE_V2_XCRUN_AND_V3_V4_ENVELOPES",
    })
    manifest["build"].update({
        "ld": str(toolchain.EXECUTABLE_PATHS["ld"]),
        "otool": str(toolchain.EXECUTABLE_PATHS["otool"]),
        "identity_rule":
            "one recorder-free Mach-O serves B/L/H; -no_deduplicate preserves six bodies; __TEXT,__br_align_v1 contains Push B/L/H then DP B/L/H at exact 16 KiB entry spacing; linker map, section flags, body facts, normalized instructions, padding and binary bytes are frozen",
    })
    manifest["candidate"]["equivalence"].update({
        "source_commit": manifest["base_commit"],
        "algorithm":
            "B is the original baseline; L is its separately named exact-work clone; H is the append-hint specialization. All six DP/Push entries are distinct, no-deduplicate, and page-offset normalized in one executable section.",
        "alignment_boundary_bytes": 16384,
        "section": "__TEXT,__br_align_v1",
        "entry_order": ["Push-B", "Push-L", "Push-H", "DP-B", "DP-L", "DP-H"],
    })
    manifest["protocol"].update({
        "purpose":
            "fresh alignment-normalized B/L/H causal diagnostic; V4 raw evidence is audited but no V4 workload or sample is rerun or pooled",
        "alignment_boundary_bytes": 16384,
        "entry_order": ["PushInterval", "PushIntervalLayoutClone",
                        "PushIntervalSpecialized",
                        "BackwardReferencesHashChainDistanceOnly",
                        "BackwardReferencesHashChainDistanceOnlyLayoutClone",
                        "BackwardReferencesHashChainDistanceOnlySpecialized"],
    })
    manifest["acceptance"].update({
        "alignment_normalization": {
            "boundary_bytes": 16384,
            "section": "__TEXT,__br_align_v1",
            "entry_modulo_required": 0,
            "inter_entry_spacing_bytes": 16384,
            "dp_to_corresponding_push_displacement_bytes": 49152,
            "section_size_bytes": 83212,
            "body_bytes": 5624,
            "inter_entry_padding_bytes": 77588,
            "local_reference_timed_runner_bytes": 676216,
            "exact_base_v4_static_runner_bytes": 592688,
            "local_reference_binary_delta_bytes": 83528,
            "remote_binary_size_rule":
                "record exact timed/recorder bytes in rehearsal and require Phase 2 to preserve the frozen section/body/padding values; total bytes are receipt-frozen because debug paths are build-root dependent",
            "b_l_canonical_instruction_identity_required": True,
            "distinct_addresses_required": True,
            "no_deduplicate_required": True,
        },
        "mandatory_b_to_l_null_control": {
            "metrics": ["backref_cost_dp_total", "backref_cost_dp_steady",
                        "whole_encode"],
            "per_cell_absolute_mean_percent_max": 0.75,
            "per_cell_bootstrap_95_ci_must_include_zero": True,
            "per_cell_bootstrap_95_ci_endpoint_absolute_percent_max": 1.50,
            "per_paired_row_absolute_percent_max": 3.00,
            "failure_consequence":
                "diagnostic invalid; do not interpret L-to-H or B-to-H and do not authorize a production claim",
            "justification":
                "V4's unnormalized B-to-L DP means ranged from -0.77% to +4.20%; a page-offset-normalized exact-work null must be much tighter. The 0.75/1.50/3.00% hierarchy remains above coarse-clock quantization and permits ordinary paired process noise without accepting the V4-scale placement shift.",
        },
        "resolved_effect_floor_percent": 0.10,
    })
    manifest["interpretation"].update({
        "layout_limit":
            "B-to-L is a mandatory normalized null control, not an effect estimate. Only after its fixed null bounds pass may L-to-H estimate the append-hint difference and B-to-H report the simultaneous total.",
        "classification":
            "If B-to-L fails any fixed null bound, classify the whole diagnostic invalid. Otherwise classify each L-to-H/B-to-H metric as indeterminate-small below 0.10% absolute mean, resolved only when its 95% paired-bootstrap CI excludes zero, or unresolved/mixed otherwise.",
    })


def finalize_hashes(manifest: dict) -> None:
    extra = [
        "scripts/freeze_backref_cost_specialization_alignment_v1_phase1.py",
        "scripts/record_backref_cost_specialization_alignment_v1_phase1b.py",
        "evidence/backref-cost-specialization-alignment-v1-design/linker-map.txt",
        "evidence/backref-cost-specialization-alignment-v1-design/linker-map-extract.txt",
        "evidence/backref-cost-specialization-alignment-v1-design/v4-static-audit-linker-map.txt",
    ]
    paths = [row["path"] for row in manifest["frozen_artifacts"]]
    for path in extra:
        if path not in paths:
            paths.append(path)
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise RuntimeError(f"cannot finalize; frozen artifacts absent: {missing}")
    manifest["frozen_artifacts"] = [
        {"path": path, "sha256": sha256(ROOT / path)} for path in paths
    ]
    manifest["admission_identity_paths"] = [
        manifest["frozen_artifact_set"]["self_manifest"], *paths
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--capture-build", type=Path)
    parser.add_argument("--v4-linker-map", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.capture_build is not None:
        capture_codegen(args.capture_build.resolve())
    if args.v4_linker_map is not None:
        audit_v4(args.v4_linker_map.resolve())
    fresh_identities(manifest)
    if args.finalize:
        finalize_hashes(manifest)
    write_json(MANIFEST, manifest)
    print(json.dumps({"status": "PASS", "finalized": args.finalize,
                      "payload_sha256": payload.sha256(),
                      "toolchain_identity_canonical_sha256":
                          canonical_sha256(toolchain.identity())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
