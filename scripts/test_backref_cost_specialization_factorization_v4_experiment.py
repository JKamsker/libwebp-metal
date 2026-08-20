#!/usr/bin/env python3
"""Untimed B/L/H correctness, recorder separation, ABI and boundary gates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import backref_cost_specialization_factorization_v4_toolchain as toolchain


ROOT = Path(__file__).resolve().parents[1]
BASE = "f289499b37875d8166792ed104f2b26e23cf4ffd"
BUILD = "WEBP_BUILD_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT"
RECORDER = "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_RECORDER"
MACRO = "WEBP_USE_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_EXPERIMENT"
RUNTIME = "WEBP_BACKREF_COST_SPECIALIZATION_FACTORIZATION_V4_VARIANT"
RUNNER = "backref_cost_specialization_factorization_v4_experiment_runner"


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
                 "-DCMAKE_EXE_LINKER_FLAGS=-Wl,-no_deduplicate"]
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
                 "-Wl,-no_deduplicate"]
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


def symbol_mnemonics(binary: Path, symbol: str) -> list[str]:
    output = run([str(toolchain.EXECUTABLE_PATHS["llvm-objdump"]),
                  f"--disassemble-symbols=_{symbol}", str(binary)]).stdout
    return [match.group(1) for line in output.splitlines()
            if (match := re.match(r"^\s*[0-9a-f]+:\s+[0-9a-f]+\s+(\S+)",
                                  line))]


def symbol_facts(binary: Path, symbol: str) -> dict[str, object]:
    mnemonics = symbol_mnemonics(binary, symbol)
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
    }


def main() -> int:
    source = (ROOT / "src/enc/backward_references_cost_enc.c").read_text()
    assert "PushIntervalLayoutClone" in source
    assert "VP8LBackrefCostSpecializationFactorizationV4GetVariant" in source
    assert "switch (variant)" in source
    assert not run(["git", "diff", "--name-only", BASE, "--", "src/webp",
                    "sharpyuv"]).stdout.strip()

    with tempfile.TemporaryDirectory(
            prefix="backref-specialization-factorization-v4-test-") as raw:
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
        for symbol in ("PushInterval", "PushIntervalLayoutClone",
                       "PushIntervalSpecialized",
                       "BackwardReferencesHashChainDistanceOnly",
                       "BackwardReferencesHashChainDistanceOnlyLayoutClone",
                       "BackwardReferencesHashChainDistanceOnlySpecialized"):
            assert symbol in timed_nm
        private_addresses = {}
        for line in timed_nm.splitlines():
            match = re.match(r"^([0-9a-f]+).* _([^ ]+)$", line)
            if match and match.group(2) in (
                    "PushInterval", "PushIntervalLayoutClone",
                    "PushIntervalSpecialized",
                    "BackwardReferencesHashChainDistanceOnly",
                    "BackwardReferencesHashChainDistanceOnlyLayoutClone",
                    "BackwardReferencesHashChainDistanceOnlySpecialized"):
                private_addresses[match.group(2)] = match.group(1)
        assert len(private_addresses) == 6
        assert len(set(private_addresses.values())) == 6
        assert "FactorizationV4RecordPush" not in timed_nm
        assert "FactorizationV4RecordPush" in recorder_nm
        assert digest(timed_runner) != digest(recorder_runner)
        assert symbol_mnemonics(timed_runner, "PushInterval") == \
            symbol_mnemonics(timed_runner, "PushIntervalLayoutClone")
        assert symbol_mnemonics(
            timed_runner, "BackwardReferencesHashChainDistanceOnly") == \
            symbol_mnemonics(
                timed_runner, "BackwardReferencesHashChainDistanceOnlyLayoutClone")
        assert symbol_mnemonics(timed_runner, "PushIntervalSpecialized") != \
            symbol_mnemonics(timed_runner, "PushIntervalLayoutClone")
        observed_codegen = {
            symbol: symbol_facts(timed_runner, symbol)
            for symbol in (
                "BackwardReferencesHashChainDistanceOnly",
                "BackwardReferencesHashChainDistanceOnlyLayoutClone",
                "BackwardReferencesHashChainDistanceOnlySpecialized",
                "PushInterval", "PushIntervalLayoutClone",
                "PushIntervalSpecialized")
        }
        frozen_codegen = json.loads((
            ROOT / "evidence/backref-cost-specialization-factorization-v4-design" /
            "phase1-local-codegen.json").read_text(encoding="utf-8"))
        assert private_addresses == frozen_codegen["symbol_addresses"]
        for symbol, expected in frozen_codegen["facts"].items():
            assert observed_codegen[symbol] == expected

        truth = {}
        for value in (None, "", "0", "B", "L", "H", "b", "HL"):
            environment = {} if value is None else {RUNTIME: value}
            truth["absent" if value is None else value] = json.loads(
                run([str(timed_runner), "guard"], env=environment).stdout)[
                    "variant"]
        assert truth == {"absent": 0, "": -1, "0": -1, "B": 0, "L": 1,
                         "H": 2, "b": -1, "HL": -1}
        timer = json.loads(run([str(timed_runner), "timer-check"]).stdout)
        assert timer["monotonic"] and timer["positive_deltas"] > 0

        fixtures = ((1, 1), (9, 1), (10, 1), (11, 1), (33, 17), (129, 65))
        local = temporary / "local.ppm"
        write_ppm(local, 257, 97, 7)
        products = []
        work = {}
        for variant in ("B", "L", "H"):
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
        assert all(work["B"][field] == work["L"][field] == work["H"][field]
                   for field in common)
        assert work["B"]["position_forward_steps"] == \
            work["L"]["position_forward_steps"]
        assert work["H"]["position_forward_steps"] == 0
        assert work["H"]["append_hint_fast_paths"] > 0

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
                for variant in ("B", "L", "H"):
                    output = temporary / f"{sanitizer}-{index}-{variant}.webp"
                    correctness(runner, fixture, 4, variant, output,
                                {"UBSAN_OPTIONS":
                                 "halt_on_error=1:silence_unsigned_overflow=1"})
                    hashes.append(digest(output))
                    boundary_encodes += 1
                assert len(set(hashes)) == 1

    print(json.dumps({
        "status": "PASS", "base_commit": BASE,
        "local_correctness_encodes": 3,
        "boundary_correctness_encodes": boundary_encodes,
        "sanitizer_configurations": 2, "truth_table": truth,
        "timer_validation": timer, "public_api_abi_equal": True,
        "default_omission": True, "timed_recorder_free": True,
        "matched_layout_codegen": True,
        "timed_runner_sha256": timed_runner_sha256,
        "recorder_runner_sha256": recorder_runner_sha256,
        "codegen_facts": observed_codegen,
        "symbol_addresses": private_addresses,
        "local_bitstream_sha256": products[0], "local_work": work,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
