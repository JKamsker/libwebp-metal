#!/usr/bin/env python3
"""Untimed B/L correctness, ledger, recorder separation, ABI and boundaries."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import backref_cost_aligned_null_stage_attribution_v3_toolchain as toolchain
import backref_cost_aligned_null_stage_attribution_v3_identity as identity


ROOT = Path(__file__).resolve().parents[1]
BASE = "92c3b59b2d178c5a03ec20b897252b358f07de81"
BUILD = "WEBP_BUILD_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT"
RECORDER = "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RECORDER"
MACRO = "WEBP_USE_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_VARIANT"
RUNNER = "backref_cost_aligned_null_stage_attribution_v3_experiment_runner"


def run(argv: list[str], *, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    clean = os.environ.copy()
    for name in ("WEBP_BENCHMARK_SESSION", "CUDA_VISIBLE_DEVICES",
                 "MallocNanoZone", RUNTIME):
        clean.pop(name, None)
    if env:
        clean.update(env)
    result = subprocess.run(argv, cwd=ROOT, env=clean, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {argv}\n{result.stdout}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(build: Path, *, experiment: bool, recorder: bool = False,
              sanitizer: str | None = None) -> None:
    argv = [
        "cmake", "-S", ".", "-B", str(build), "-DWEBP_ENABLE_METAL=OFF",
        f"-DCMAKE_C_COMPILER={toolchain.EXECUTABLE_PATHS['clang']}",
        f"-DCMAKE_OBJCXX_COMPILER={toolchain.EXECUTABLE_PATHS['clang++']}",
        f"-DCMAKE_OSX_SYSROOT={toolchain.SDK_PATH}",
        "-DBUILD_SHARED_LIBS=OFF", "-DWEBP_BUILD_EXTRAS=OFF",
        "-DWEBP_BUILD_CWEBP=OFF", "-DWEBP_BUILD_DWEBP=OFF",
        "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]
    if experiment:
        argv += [f"-D{BUILD}=ON", f"-D{RECORDER}={'ON' if recorder else 'OFF'}",
                 "-DCMAKE_C_FLAGS_RELWITHDEBINFO=-O3 -g -DNDEBUG -fno-omit-frame-pointer",
                 f"-DCMAKE_EXE_LINKER_FLAGS=-Wl,-no_deduplicate,-map,{build / 'linker.map'}"]
    if sanitizer:
        sanitize = ("undefined,integer" if sanitizer == "undefined" else
                    "array-bounds,pointer-overflow")
        flags = (f"-O1 -g -fno-omit-frame-pointer -fsanitize={sanitize} "
                 "-fno-sanitize-recover=all")
        if sanitizer == "undefined":
            # The lossless decoder deliberately uses an overflowing unsigned
            # shift while reconstructing a 64-bit accumulator. Keep all other
            # undefined/integer checks enabled for the encoder boundary.
            flags += " -fno-sanitize=unsigned-shift-base"
        argv += [f"-DCMAKE_C_FLAGS={flags}",
                 f"-DCMAKE_EXE_LINKER_FLAGS=-fsanitize={sanitize} "
                 f"-Wl,-no_deduplicate,-map,{build / 'linker.map'}"]
    run(argv)


def build(directory: Path, *targets: str) -> None:
    run(["cmake", "--build", str(directory), "--target", *targets,
         "--parallel", "2"])


def write_ppm(path: Path, width: int, height: int, seed: int) -> None:
    pixels = bytearray()
    state = seed & 0xffffffff
    for index in range(width * height):
        state ^= (state << 13) & 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        if seed & 1:
            x, y = index % width, index // width
            palette = ((238, 238, 232), (38, 62, 96), (225, 82, 65),
                       (247, 190, 66), (50, 150, 105), (103, 78, 167))
            pixels.extend(palette[((x // 16) + 3 * (y // 12)) % 6])
        else:
            pixels.extend((state & 255, (state >> 8) & 255,
                           (state >> 16) & 255))
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + pixels)


def correctness(runner: Path, source: Path, method: int, variant: str,
                output: Path, extra: dict[str, str] | None = None) -> None:
    environment = {RUNTIME: variant, **(extra or {})}
    run([str(runner), "correctness", str(source), str(method), variant,
         str(output)], env=environment)


def public_symbols(library: Path) -> list[str]:
    output = run([str(toolchain.EXECUTABLE_PATHS["nm"]), str(library)]).stdout
    return sorted(line.split()[-1] for line in output.splitlines()
                  if line.split() and line.split()[-1].startswith("WebP"))


def symbol_rows(binary: Path, symbol: str) -> list[tuple[str, str, str]]:
    output = run([str(toolchain.EXECUTABLE_PATHS["llvm-objdump"]),
                  f"--disassemble-symbols=_{symbol}", str(binary)]).stdout
    rows = []
    for line in output.splitlines():
        match = re.match(
            r"^\s*[0-9a-f]+:\s+([0-9a-f]+)\s+(\S+)(?:\s+(.*))?$", line)
        if match:
            rows.append((match.group(1), match.group(2), match.group(3) or ""))
    # Mach-O symbol extents include the deliberate page-fill NOPs. No selected
    # hot body contains a semantic trailing NOP, so remove only the contiguous
    # linker-visible tail and freeze its byte count separately.
    while rows and rows[-1][1] == "nop":
        rows.pop()
    return rows


def canonical_instructions(binary: Path, symbol: str) -> list[str]:
    rows = symbol_rows(binary, symbol)
    aliases = identity.normalization_aliases()
    canonical = []
    for _, mnemonic, operands in rows:
        for old, new in aliases.items():
            operands = operands.replace(old, new)
        # PC-relative encodings necessarily differ when equal bodies occupy
        # different pages. Preserve the referenced symbol/addend while removing
        # only the printed absolute address.
        operands = re.sub(r"0x[0-9a-f]+ (?=<_[^>]+>)", "", operands)
        canonical.append(f"{mnemonic}\t{operands}".rstrip())
    return canonical


def symbol_facts(binary: Path, symbol: str) -> dict[str, object]:
    rows = symbol_rows(binary, symbol)
    mnemonics = [row[1] for row in rows]
    is_branch = lambda mnemonic: (
        mnemonic == "b" or mnemonic.startswith("b.") or
        mnemonic in ("bl", "blr", "br", "ret") or
        mnemonic.startswith(("cb", "tb")))
    return {
        "size_bytes": 4 * len(mnemonics),
        "instruction_count": len(mnemonics),
        "branch_count": sum(is_branch(mnemonic) for mnemonic in mnemonics),
        "load_count": sum(mnemonic.startswith(("ld", "ldr"))
                          for mnemonic in mnemonics),
        "store_count": sum(mnemonic.startswith(("st", "str"))
                           for mnemonic in mnemonics),
        "mnemonics_sha256": hashlib.sha256(
            "\n".join(mnemonics).encode()).hexdigest(),
        "instruction_words_sha256": hashlib.sha256(
            "\n".join(row[0] for row in rows).encode()).hexdigest(),
        "canonical_instructions_sha256": hashlib.sha256(
            "\n".join(canonical_instructions(binary, symbol)).encode()
        ).hexdigest(),
    }


def main() -> int:
    source = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    assert all(entry.symbol in source for entry in identity.HOT_ENTRIES)
    assert "VP8LBackrefCostAlignedNullStageAttributionV3GetVariant" in source
    assert "switch (variant)" in source
    assert not run(["git", "diff", "--name-only", BASE, "--", "src/webp",
                    "sharpyuv"]).stdout.strip()

    with tempfile.TemporaryDirectory(
            prefix="backref-aligned-null-stage-v2-test-") as raw:
        temporary = Path(raw)
        ordinary = temporary / "ordinary"
        timed = temporary / "timed"
        recorded = temporary / "recorded"
        configure(ordinary, experiment=False)
        configure(timed, experiment=True)
        configure(recorded, experiment=True, recorder=True)
        build(ordinary, "webp")
        build(timed, "webp", RUNNER)
        build(recorded, RUNNER)
        ordinary_commands = (ordinary / "compile_commands.json").read_text()
        timed_commands = (timed / "compile_commands.json").read_text()
        recorded_commands = (recorded / "compile_commands.json").read_text()
        assert MACRO not in ordinary_commands and RUNNER not in ordinary_commands
        ordinary_archive = (ordinary / "libwebp.a").read_bytes()
        assert b"SPECIALIZATION_ALIGNED_NULL_STAGE_ATTRIBUTION_V3" not in ordinary_archive
        assert b"specialization_alignment_v4" not in ordinary_archive
        assert RUNTIME.encode() not in ordinary_archive
        assert f"-D{MACRO}=1" in timed_commands and RECORDER not in timed_commands
        assert f"-D{RECORDER}=1" in recorded_commands
        absent = run(["cmake", "--build", str(ordinary), "--target", RUNNER],
                     check=False)
        assert absent.returncode != 0
        assert public_symbols(ordinary / "libwebp.a") == \
            public_symbols(timed / "libwebp.a")

        timed_runner = timed / RUNNER
        recorder_runner = recorded / RUNNER
        timed_runner_sha256 = digest(timed_runner)
        recorder_runner_sha256 = digest(recorder_runner)
        timed_nm = run([str(toolchain.EXECUTABLE_PATHS["nm"]),
                        "-nm", str(timed_runner)]).stdout
        recorder_nm = run([str(toolchain.EXECUTABLE_PATHS["nm"]),
                           "-nm", str(recorder_runner)]).stdout
        candidate_symbols = identity.names()
        for symbol in candidate_symbols:
            assert symbol in timed_nm
        private_addresses = {}
        for line in timed_nm.splitlines():
            match = re.match(r"^([0-9a-f]+).* _([^ ]+)$", line)
            if match and match.group(2) in candidate_symbols:
                private_addresses[match.group(2)] = match.group(1)
        assert len(private_addresses) == identity.count()
        assert len(set(private_addresses.values())) == identity.count()
        assert "AlignedNullStageAttributionV3RecordPush" not in timed_nm
        assert "AlignedNullStageAttributionV3RecordPush" in recorder_nm
        assert digest(timed_runner) != digest(recorder_runner)
        for baseline, layout in identity.equivalence_pairs():
            assert canonical_instructions(timed_runner, baseline) == \
                canonical_instructions(timed_runner, layout)
        observed_codegen = {
            symbol: symbol_facts(timed_runner, symbol)
            for symbol in candidate_symbols
        }
        address_values = {name: int(value, 16)
                          for name, value in private_addresses.items()}
        expected_order = identity.names()
        assert sorted(address_values, key=address_values.get) == expected_order
        assert all(value % identity.BOUNDARY_BYTES == 0
                   for value in address_values.values())
        assert all(address_values[expected_order[i + 1]] -
                   address_values[expected_order[i]] == identity.BOUNDARY_BYTES
                   for i in range(identity.count() - 1))
        for push, dp in identity.displacement_pairs():
            assert address_values[dp] - address_values[push] == \
                2 * identity.BOUNDARY_BYTES
        otool = run([str(toolchain.EXECUTABLE_PATHS["otool"]), "-l",
                     str(timed_runner)]).stdout
        section = re.search(
            r"sectname __br_null_v3\n\s+segname __TEXT\n"
            r"\s+addr (0x[0-9a-f]+)\n\s+size (0x[0-9a-f]+)\n"
            r"\s+offset ([0-9]+)\n\s+align 2\^14 \(16384\)", otool)
        assert section is not None
        section_block = otool[section.start():]
        assert re.search(r"\n\s+flags 0x80000400", section_block)
        assert int(section.group(1), 16) == address_values[expected_order[0]]
        linker_map = timed / "linker.map"
        map_text = linker_map.read_text(encoding="utf-8")
        map_rows = [line for line in map_text.splitlines()
                    if line.split() and
                    line.rsplit(None, 1)[-1].removeprefix("_") in expected_order]
        assert len(map_rows) == identity.count()
        assert [row.rsplit(None, 1)[-1].removeprefix("_")
                for row in map_rows] == expected_order
        body_bytes = sum(fact["size_bytes"] for fact in observed_codegen.values())
        padding_bytes = int(section.group(2), 16) - body_bytes
        section_map_rows = [line for line in map_text.splitlines()
                            if "__TEXT\t__br_null_v3" in line]
        assert len(section_map_rows) == 1
        linker_map_extract = "\n".join(section_map_rows + map_rows) + "\n"
        frozen_codegen = json.loads((
            ROOT / "evidence/backref-cost-aligned-null-stage-attribution-v3-design" /
            "phase1-local-codegen.json").read_text(encoding="utf-8"))
        assert private_addresses == frozen_codegen["symbol_addresses"]
        assert frozen_codegen["section_size_bytes"] == int(section.group(2), 16)
        assert frozen_codegen["inter_entry_padding_bytes"] == padding_bytes
        assert frozen_codegen["linker_map_extract_sha256"] == hashlib.sha256(
            linker_map_extract.encode()).hexdigest()
        for symbol, expected in frozen_codegen["facts"].items():
            assert observed_codegen[symbol] == expected, (
                symbol, observed_codegen[symbol], expected)

        truth = {}
        for value in (None, "", "0", "B", "L", "H", "b", "HL"):
            environment = {} if value is None else {RUNTIME: value}
            truth["absent" if value is None else value] = json.loads(
                run([str(timed_runner), "guard"], env=environment).stdout)[
                    "variant"]
        assert truth == {"absent": 0, "": -1, "0": -1, "B": 0, "L": 1,
                         "H": -1, "b": -1, "HL": -1}
        timer = json.loads(run([str(timed_runner), "timer-check"]).stdout)
        assert timer["monotonic"] and timer["positive_deltas"] > 0
        assert all(name in timer for name in
                   ("p50_read_delta_ns", "p95_read_delta_ns",
                    "p99_read_delta_ns", "maximum_delta_ns"))

        fixtures = ((1, 1), (9, 1), (10, 1), (11, 1), (33, 17), (129, 65))
        local = temporary / "local.ppm"
        write_ppm(local, 257, 97, 7)
        timer_accounting = []
        for variant in ("B", "L"):
            stage = temporary / f"timer-validation-{variant}.jsonl"
            environment = {
                RUNTIME: variant, "WEBP_BENCHMARK_SESSION": "exclusive",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_TIMERS": "1",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_STAGE_OUTPUT":
                    str(stage),
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RUN_ID":
                    f"local-timer-{variant}",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CASE_ID":
                    "local",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_SAMPLE_SET":
                    "timer-validation",
            }
            emitted = [json.loads(line) for line in run(
                [str(recorder_runner), "timer-accounting-check", str(local),
                 "local", "4", variant], env=environment).stdout.splitlines()
                       if line.strip()]
            stages = [json.loads(line) for line in stage.read_text().splitlines()
                      if line.strip()]
            assert len(emitted) == 2 and len(stages) == 1
            assert emitted[1]["schema"].endswith(
                "timer-accounting-output-v1")
            assert emitted[1]["per_pixel_clock_calls"] == 0
            assert stages[0]["schema"].endswith("stage-ledger-v1")
            assert stages[0]["sample_role"] == "timer-validation"
            assert stages[0]["ledger_valid"]
            assert stages[0]["ledger_sum_ns"] == stages[0]["total_ns"]
            assert stages[0]["reconciliation_delta_ns"] == 0
            assert stages[0]["clock_reads"] == \
                stages[0]["expected_clock_reads"]
            nested = stages[0]["stages"]
            assert nested["backref_cost_dp_total"]["calls"] == \
                nested["backref_cost_dp_setup"]["calls"] == \
                nested["backref_cost_dp_steady"]["calls"] > 0
            assert nested["backref_cost_dp_setup"]["ns"] + \
                nested["backref_cost_dp_steady"]["ns"] <= \
                nested["backref_cost_dp_total"]["ns"]
            timer_accounting.append({"output": emitted[1],
                                     "stage": stages[0]})
        ledger_fixtures = []
        for fixture_name, expected_calls in (
                ("early-return", {}),
                ("allocation-failure", {"lossless_prepare": 1}),
                ("empty-input", {"lossless_container_setup": 1}),
                ("tiny-skip", {"lossless_prepare": 1,
                               "lossless_stream_finalize": 1}),
                ("repeated-stage", {"lossless_prepare": 2})):
            stage = temporary / f"fixture-{fixture_name}.jsonl"
            fixture_environment = {
                RUNTIME: "B", "WEBP_BENCHMARK_SESSION": "exclusive",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_TIMERS": "1",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_STAGE_OUTPUT":
                    str(stage),
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_RUN_ID":
                    f"fixture-{fixture_name}",
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_CASE_ID":
                    fixture_name,
                "WEBP_BACKREF_COST_ALIGNED_NULL_STAGE_ATTRIBUTION_V3_SAMPLE_SET":
                    "timer-validation",
            }
            run([str(recorder_runner), "ledger-fixture", fixture_name],
                env=fixture_environment)
            fixture_row = json.loads(stage.read_text())
            assert fixture_row["ledger_valid"]
            assert fixture_row["ledger_sum_ns"] == fixture_row["total_ns"]
            assert fixture_row["reconciliation_delta_ns"] == 0
            assert fixture_row["clock_reads"] == \
                fixture_row["expected_clock_reads"]
            assert {name: value["calls"]
                    for name, value in fixture_row["stages"].items()} == \
                expected_calls
            ledger_fixtures.append({"fixture": fixture_name,
                                    "clock_reads": fixture_row["clock_reads"],
                                    "stage_calls": expected_calls})
        products = []
        work = {}
        for variant in ("B", "L"):
            output = temporary / f"local-{variant}.webp"
            correctness(timed_runner, local, 4, variant, output)
            products.append(digest(output))
            work[variant] = json.loads(run(
                [str(recorder_runner), "work", str(local), "local", "4",
                 variant], env={RUNTIME: variant}).stdout)
        assert len(set(products)) == 1
        common = ("push_calls", "short_push_calls", "cache_segments",
                  "overlap_scans", "insert_calls", "interval_pops",
                  "max_live_intervals", "bitstream_fnv1a64")
        assert all(work["B"][field] == work["L"][field]
                   for field in common)
        assert work["B"]["position_forward_steps"] == \
            work["L"]["position_forward_steps"]
        assert all(work[variant][field] == 0 for variant in ("B", "L")
                   for field in ("append_hint_fast_paths",
                                 "append_hint_branch_checks",
                                 "append_hint_loads", "append_hint_updates",
                                 "pop_tail_branch_checks", "pop_tail_updates"))
        section_size_bytes = int(section.group(2), 16)
        linker_map_sha256 = digest(linker_map)
        linker_map_extract_sha256 = hashlib.sha256(
            linker_map_extract.encode()).hexdigest()
        timed_runner_bytes = timed_runner.stat().st_size

        boundary_encodes = 0
        for sanitizer in ("undefined", "bounds"):
            directory = temporary / sanitizer
            configure(directory, experiment=True, sanitizer=sanitizer)
            build(directory, RUNNER)
            runner = directory / RUNNER
            for index, (width, height) in enumerate(fixtures):
                fixture = temporary / f"{sanitizer}-{index}.ppm"
                write_ppm(fixture, width, height, index + 1)
                hashes = []
                for variant in ("B", "L"):
                    output = temporary / f"{sanitizer}-{index}-{variant}.webp"
                    fixture_method = 4 if index % 2 == 0 else 6
                    correctness(runner, fixture, fixture_method, variant, output,
                                {"UBSAN_OPTIONS":
                                 "halt_on_error=1:silence_unsigned_overflow=1"})
                    hashes.append(digest(output))
                    boundary_encodes += 1
                assert len(set(hashes)) == 1

    print(json.dumps({
        "status": "PASS", "base_commit": BASE,
        "local_correctness_encodes": 2,
        "boundary_correctness_encodes": boundary_encodes,
        "sanitizer_configurations": 2, "truth_table": truth,
        "timer_validation": timer, "public_api_abi_equal": True,
        "timer_accounting_validation_rows": timer_accounting,
        "ledger_fixture_rows": ledger_fixtures,
        "default_omission": True, "timed_recorder_free": True,
        "matched_layout_codegen": True,
        "timed_runner_sha256": timed_runner_sha256,
        "recorder_runner_sha256": recorder_runner_sha256,
        "codegen_facts": observed_codegen,
        "symbol_addresses": private_addresses,
        "alignment_boundary_bytes": 16384,
        "section_size_bytes": section_size_bytes,
        "section_flags": "0x80000400",
        "inter_entry_padding_bytes": padding_bytes,
        "linker_map_sha256": linker_map_sha256,
        "linker_map_extract_sha256": linker_map_extract_sha256,
        "timed_runner_bytes": timed_runner_bytes,
        "local_bitstream_sha256": products[0], "local_work": work,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
