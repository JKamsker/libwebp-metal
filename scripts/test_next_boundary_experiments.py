#!/usr/bin/env python3
"""Untimed correctness, determinism, fallback, and refusal checks."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROWS = (
    ("WEBP_BUILD_PREDICTOR_BOUNDARY_EXPERIMENT",
     "WEBP_PREDICTOR_BOUNDARY_EXPERIMENT",
     "WEBP_PREDICTOR_BOUNDARY_CONTROL",
     "WEBP_PREDICTOR_BOUNDARY_INJECT_RECORD_FAILURE",
     "WEBP_PREDICTOR_BOUNDARY_OUTPUT",
     "-predictor_boundary_repetitions", "libwebp-predictor-boundary-v1"),
    ("WEBP_BUILD_BACKREF_EXACT_EXPERIMENT",
     "WEBP_BACKREF_EXACT_EXPERIMENT",
     "WEBP_BACKREF_EXACT_CONTROL",
     "WEBP_BACKREF_EXACT_INJECT_RECORD_FAILURE",
     "WEBP_BACKREF_EXACT_OUTPUT",
     "-backref_exact_repetitions", "libwebp-backref-exact-v1"),
)


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
    with tempfile.TemporaryDirectory(prefix="webp-boundary-check-") as temporary:
        temp = Path(temporary)
        corpus = temp / "corpus"
        run([sys.executable, "scripts/generate_publication_corpus.py",
             "--output", str(corpus), "--verify"])
        input_path = corpus / "photo-small.ppm"
        for build_flag, runtime, control, failure, output_flag, option, schema in ROWS:
            run(["make", "-f", "makefile.unix", "clean"])
            run(["make", "-f", "makefile.unix", "-j4", "WEBP_ENABLE_METAL=1",
                 f"{build_flag}=1", "examples/cwebp", "examples/dwebp"])
            base_env = os.environ.copy()
            base_env.update({runtime: "1", "WEBP_BENCHMARK_SESSION": "exclusive",
                             "WEBP_ACCELERATOR": "metal", "WEBP_METAL": "1",
                             "WEBP_BOUNDARY_CASE_ID": "photo-small",
                             "WEBP_BOUNDARY_LIFECYCLE": "correctness"})
            outputs = []
            for label, extra in (("record-a", {}), ("record-b", {}),
                                 ("control", {control: "1"}),
                                 ("fallback", {failure: "1"})):
                encoded = temp / f"{runtime}-{label}.webp"
                records = temp / f"{runtime}-{label}.jsonl"
                env = base_env | extra | {output_flag: str(records)}
                run(["examples/cwebp", "-quiet", "-lossless", "-exact", "-q",
                     "75", "-m", "4", "-o", str(encoded), str(input_path)], env)
                outputs.append(digest(encoded))
                if label != "fallback":
                    rows = [json.loads(line) for line in records.read_text().splitlines()]
                    assert len(rows) == 1 and rows[0]["schema"] == schema
                else:
                    assert not records.exists()
            assert len(set(outputs)) == 1, (runtime, outputs)
            decoded = temp / f"{runtime}-decoded.ppm"
            run(["examples/dwebp", "-quiet", "-ppm", "-o", str(decoded),
                 str(temp / f"{runtime}-record-a.webp")])
            assert digest(decoded) == digest(input_path)
            refused = base_env.copy()
            refused.pop("WEBP_BENCHMARK_SESSION")
            result = run(["examples/cwebp", "-quiet", "-lossless", option, "2",
                          str(input_path)], refused, ok=False)
            assert "WEBP_BENCHMARK_SESSION=exclusive" in result.stdout
            missing = base_env.copy()
            missing.pop(runtime)
            result = run(["examples/cwebp", "-quiet", "-lossless", option, "2",
                          str(input_path)], missing, ok=False)
            assert f"{runtime}=1" in result.stdout
            invalid_runtime = base_env | {runtime: "true"}
            result = run(["examples/cwebp", "-quiet", "-lossless", option, "2",
                          str(input_path)], invalid_runtime, ok=False)
            assert f"{runtime}=1" in result.stdout
            invalid_session = base_env | {"WEBP_BENCHMARK_SESSION": "shared"}
            result = run(["examples/cwebp", "-quiet", "-lossless", option, "2",
                          str(input_path)], invalid_session, ok=False)
            assert "WEBP_BENCHMARK_SESSION=exclusive" in result.stdout
    print("PASS: boundary experiments correctness, determinism, fallback, and refusals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
