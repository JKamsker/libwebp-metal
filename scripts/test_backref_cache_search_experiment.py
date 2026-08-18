#!/usr/bin/env python3
"""Untimed isolation, refusal, correctness, and recorder-safety checks."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_FLAG = "WEBP_BUILD_BACKREF_CACHE_SEARCH_EXPERIMENT"
RUNTIME_FLAG = "WEBP_BACKREF_CACHE_SEARCH_EXPERIMENT"
CONTROL_FLAG = "WEBP_BACKREF_CACHE_SEARCH_CONTROL"
FAILURE_FLAG = "WEBP_BACKREF_CACHE_SEARCH_INJECT_RECORD_FAILURE"
OUTPUT_FLAG = "WEBP_BACKREF_CACHE_SEARCH_OUTPUT"
OPTION = "-backref_cache_search_repetitions"
SCHEMA = "libwebp-backref-cache-search-v1"


def run(argv: list[str], env: dict[str, str] | None = None,
        ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            check=False)
    if ok and result.returncode != 0:
        raise AssertionError((argv, result.stdout))
    if not ok and result.returncode == 0:
        raise AssertionError(f"unexpected success: {argv}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    run([sys.executable, "scripts/run_backref_cache_search_experiment.py",
         "validate"])
    with tempfile.TemporaryDirectory(
            prefix="webp-cache-search-check-") as temporary:
        temp = Path(temporary)
        corpus = temp / "corpus"
        run([sys.executable, "scripts/generate_publication_corpus.py",
             "--output", str(corpus), "--verify"])
        input_path = corpus / "texture-small.ppm"

        run(["make", "-f", "makefile.unix", "clean"])
        run(["make", "-f", "makefile.unix", "-j4", "WEBP_ENABLE_METAL=0",
             "examples/cwebp", "examples/dwebp"])
        symbols = run(["nm", "src/libwebp.a"]).stdout
        strings = run(["strings", "examples/cwebp"]).stdout
        assert "WebPBackrefCacheSearch" not in symbols
        assert RUNTIME_FLAG not in strings
        assert OPTION not in strings

        run(["make", "-f", "makefile.unix", "clean"])
        run(["make", "-f", "makefile.unix", "-j4", "WEBP_ENABLE_METAL=1",
             f"{BUILD_FLAG}=1", "examples/cwebp", "examples/dwebp"])
        base_env = os.environ.copy()
        base_env.update({
            RUNTIME_FLAG: "1",
            "WEBP_BENCHMARK_SESSION": "exclusive",
            "WEBP_ACCELERATOR": "metal",
            "WEBP_METAL": "1",
            "WEBP_BACKREF_CACHE_SEARCH_CASE_ID": "texture-small",
            "WEBP_BACKREF_CACHE_SEARCH_LIFECYCLE": "correctness",
            "WEBP_BACKREF_CACHE_SEARCH_RUN_ID": "untimed-validation",
        })
        outputs = []
        variants = (
            ("record-a", {}, temp / "record-a.jsonl"),
            ("record-b", {}, temp / "record-b.jsonl"),
            ("control", {CONTROL_FLAG: "1"}, temp / "control.jsonl"),
            ("injected", {FAILURE_FLAG: "1"}, temp / "injected.jsonl"),
            ("open-failure", {}, temp / "missing" / "record.jsonl"),
        )
        for label, extra, records in variants:
            encoded = temp / f"{label}.webp"
            env = base_env | extra | {OUTPUT_FLAG: str(records)}
            run(["examples/cwebp", "-quiet", "-lossless", "-exact",
                 "-q", "75", "-m", "4", "-o", str(encoded),
                 str(input_path)], env)
            outputs.append(digest(encoded))
            if label in ("record-a", "record-b", "control"):
                rows = [json.loads(line)
                        for line in records.read_text().splitlines()]
                assert len(rows) == 1 and rows[0]["schema"] == SCHEMA
                if label.startswith("record"):
                    assert rows[0]["stages"]["backref_total"]["calls"] == 1
                    assert rows[0]["stages"]["cache_search"]["calls"] == 2
                else:
                    assert rows[0]["stages"]["backref_total"]["calls"] == 0
                    assert rows[0]["stages"]["cache_search"]["calls"] == 0
            else:
                assert not records.exists()
        assert len(set(outputs)) == 1, outputs
        decoded = temp / "decoded.ppm"
        run(["examples/dwebp", "-quiet", "-ppm", "-o", str(decoded),
             str(temp / "record-a.webp")])
        assert digest(decoded) == digest(input_path)

        absent_env = base_env.copy()
        absent_env.pop(RUNTIME_FLAG)
        absent_records = temp / "independence.jsonl"
        absent_env[OUTPUT_FLAG] = str(absent_records)
        absent_env["WEBP_BACKREF_EXACT_EXPERIMENT"] = "1"
        run(["examples/cwebp", "-quiet", "-lossless", "-exact", "-m", "4",
             "-o", str(temp / "independence.webp"), str(input_path)],
            absent_env)
        assert not absent_records.exists()

        for env, expected in (
            (absent_env, f"{RUNTIME_FLAG}=1"),
            (base_env | {RUNTIME_FLAG: "true"}, f"{RUNTIME_FLAG}=1"),
            ({key: value for key, value in base_env.items()
              if key != "WEBP_BENCHMARK_SESSION"},
             "WEBP_BENCHMARK_SESSION=exclusive"),
            (base_env | {"WEBP_BENCHMARK_SESSION": "shared"},
             "WEBP_BENCHMARK_SESSION=exclusive"),
        ):
            result = run(["examples/cwebp", "-quiet", "-lossless", OPTION,
                          "2", str(input_path)], env, ok=False)
            assert expected in result.stdout, result.stdout

        operator = [sys.executable,
                    "scripts/run_backref_cache_search_experiment.py", "run",
                    "backref_cache_search", str(temp / "evidence")]
        clean_env = os.environ.copy()
        clean_env.pop(RUNTIME_FLAG, None)
        clean_env.pop("WEBP_BENCHMARK_SESSION", None)
        result = run(operator, clean_env, ok=False)
        assert f"{RUNTIME_FLAG}=1" in result.stdout
        result = run(operator, clean_env | {RUNTIME_FLAG: "1"}, ok=False)
        assert "WEBP_BENCHMARK_SESSION=exclusive" in result.stdout

    print("PASS: focused cache-search experiment untimed guards and correctness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
