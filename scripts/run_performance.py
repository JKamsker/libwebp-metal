#!/usr/bin/env python3
"""Collect raw, alternating CPU/Metal end-to-end timing samples."""

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


SCHEMA_VERSION = 1


def command_output(command):
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return result.stdout.strip()
    except OSError as error:
        return "unavailable: %s" % error


def collect_environment(corpus_manifest):
    sysctl = {}
    sysctl_keys = (
        "hw.model",
        "hw.machine",
        "hw.memsize",
        "machdep.cpu.brand_string",
    )
    for key in sysctl_keys:
        sysctl[key] = command_output(["sysctl", "-n", key])
    return {
        "schema_version": SCHEMA_VERSION,
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": command_output(["git", "rev-parse", "HEAD"]),
        "runner": {
            key: os.environ.get(key, "")
            for key in ("RUNNER_NAME", "RUNNER_OS", "RUNNER_ARCH")
        },
        "platform": platform.platform(),
        "uname": command_output(["uname", "-a"]),
        "sw_vers": command_output(["sw_vers"]),
        "sysctl": sysctl,
        "clang": command_output(["clang", "--version"]),
        "cmake": command_output(["cmake", "--version"]),
        "xcode": command_output(["xcodebuild", "-version"]),
        "power": command_output(["pmset", "-g", "batt"]),
        "thermal": command_output(["pmset", "-g", "therm"]),
        "corpus_manifest_sha256": hashlib.sha256(
            corpus_manifest.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
    }


def cases(corpus):
    smooth = corpus / f"smooth-2560x1920.ppm"
    texture = corpus / f"texture-2560x1920.ppm"
    result = []
    for image in (smooth, texture):
        for method in (4, 6):
            result.append(
                (
                    f"lossless_e2e_m{method}/{image.stem}",
                    image,
                    ["-lossless", "-exact", "-m", str(method)],
                    {"WEBP_ACCELERATOR": "none", "WEBP_METAL": "0"},
                    {
                        "WEBP_ACCELERATOR": "metal",
                        "WEBP_METAL": "1",
                        "WEBP_METAL_MIN_PIXELS": "0",
                        "WEBP_METAL_VERBOSE": "1",
                    },
                )
            )
    for method in (4, 6):
        result.append(
            (
                f"hash_candidate_m{method}/{smooth.stem}",
                smooth,
                ["-lossless", "-exact", "-m", str(method)],
                {
                    "WEBP_ACCELERATOR": "metal",
                    "WEBP_METAL": "1",
                    "WEBP_METAL_MIN_PIXELS": "0",
                    "WEBP_METAL_HASH": "0",
                },
                {
                    "WEBP_ACCELERATOR": "metal",
                    "WEBP_METAL": "1",
                    "WEBP_METAL_MIN_PIXELS": "0",
                    "WEBP_METAL_HASH": "1",
                    "WEBP_METAL_HASH_MIN_PIXELS": "0",
                    "WEBP_METAL_VERBOSE": "1",
                },
            )
        )
    result.append(
        (
            f"lossy_e2e_m4/{smooth.stem}",
            smooth,
            ["-q", "75", "-m", "4"],
            {
                "WEBP_ACCELERATOR": "none",
                "WEBP_METAL": "0",
                "WEBP_METAL_LOSSY": "0",
            },
            {
                "WEBP_ACCELERATOR": "metal",
                "WEBP_METAL": "0",
                "WEBP_METAL_LOSSY": "1",
                "WEBP_METAL_LOSSY_MIN_PIXELS": "0",
                "WEBP_METAL_VERBOSE": "1",
            },
        )
    )
    return result


def run_one(encoder, output_dir, case_name, image, arguments, variant, knobs,
            iteration, measured):
    output_path = output_dir / "last-output.webp"
    command = [
        str(encoder), "-quiet", *arguments, str(image), "-o", str(output_path)
    ]
    environment = os.environ.copy()
    environment.update(knobs)
    started = time.perf_counter_ns()
    completed = subprocess.run(
        command,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = (time.perf_counter_ns() - started) / 1_000_000_000
    if completed.returncode != 0:
        raise RuntimeError("benchmark failed (%s, %s): %s" %
                           (case_name, variant, completed.stderr))
    expected_log = None
    if variant == "accelerated":
        if case_name.startswith("hash_candidate"):
            expected_log = "WebP-Metal: hash candidates"
        elif case_name.startswith("lossy"):
            expected_log = "WebP-Metal: lossy RGB->YUV"
        else:
            expected_log = "WebP-Metal: transformed"
    if expected_log and expected_log not in completed.stderr:
        raise RuntimeError(
            "accelerated path was not observed (%s): %s" %
            (case_name, completed.stderr)
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "case": case_name,
        "variant": variant,
        "iteration": iteration,
        "measured": measured,
        "seconds": elapsed,
        "command": command,
        "environment": knobs,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "output_bytes": output_path.stat().st_size,
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--warmups", type=int, default=1)
    args = parser.parse_args()
    if args.samples < 5:
        parser.error("--samples must be at least 5")
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        parser.error(
            "timed collection requires WEBP_BENCHMARK_SESSION=exclusive"
        )
    encoder = (args.bin_dir / "cwebp").resolve()
    if not encoder.is_file():
        parser.error(f"encoder not found: {encoder}")
    manifest = args.corpus / "manifest.json"
    if not manifest.is_file():
        parser.error(f"corpus manifest not found: {manifest}")
    args.output.mkdir(parents=True, exist_ok=True)
    environment = collect_environment(manifest)
    (args.output / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n")

    sample_path = args.output / "samples.jsonl"
    with sample_path.open("w", encoding="utf-8") as output:
        benchmark_cases = cases(args.corpus)
        for case_name, image, arguments, baseline_env, accelerated_env in (
                benchmark_cases):
            total = args.warmups + args.samples
            for iteration in range(total):
                order = (("baseline", baseline_env),
                         ("accelerated", accelerated_env))
                if iteration % 2:
                    order = tuple(reversed(order))
                for variant, knobs in order:
                    record = run_one(
                        encoder,
                        args.output,
                        case_name,
                        image,
                        arguments,
                        variant,
                        knobs,
                        iteration,
                        iteration >= args.warmups,
                    )
                    output.write(json.dumps(record, sort_keys=True) + "\n")
                    output.flush()
    (args.output / "last-output.webp").unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
