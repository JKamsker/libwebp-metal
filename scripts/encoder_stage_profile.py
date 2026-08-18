#!/usr/bin/env python3
"""Prepare, run, and summarize reproducible libwebp encoder stage profiles."""

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import platform
import statistics
import subprocess
import sys

import generate_publication_corpus as publication_corpus


SCHEMA = "libwebp-encoder-stage-v1"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_dataset(dataset_dir):
    canonical = publication_corpus.generate(dataset_dir)
    publication_corpus.verify(canonical, publication_corpus.CANONICAL_MANIFEST)
    cases = [
        {
            "case_id": case["case_id"],
            "content_class": case["category"],
            "size_class": case["size_class"],
            "width": case["width"],
            "height": case["height"],
            "pixels": case["pixels"],
            "path": str((dataset_dir / case["file"]).resolve()),
            "sha256": case["sha256"],
        }
        for case in canonical["cases"]
    ]
    manifest = {
        "schema": "libwebp-stage-profile-dataset-v1",
        "generator": str((pathlib.Path(__file__).parent /
                          "generate_publication_corpus.py").resolve()),
        "format": "binary PPM (P6), opaque RGB",
        "publication_corpus_schema": canonical["schema"],
        "publication_corpus_version": canonical["corpus_version"],
        "seed_policy": canonical["generator"],
        "cases": cases,
    }
    write_json(dataset_dir / "manifest.json", manifest)
    return manifest


def command_output(command):
    try:
        return subprocess.run(command, check=False, text=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).stdout.strip()
    except OSError as error:
        return f"unavailable: {error}"


def environment_metadata(encoder, argv):
    return {
        "schema": "libwebp-stage-profile-environment-v1",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": argv,
        "cwd": str(pathlib.Path.cwd()),
        "git_commit": command_output(["git", "rev-parse", "HEAD"]),
        "git_status": command_output(["git", "status", "--short"]),
        "encoder": str(encoder.resolve()),
        "encoder_sha256": sha256(encoder),
        "encoder_version": command_output([str(encoder), "-version"]),
        "compiler": command_output(["clang", "--version"]),
        "xcode": command_output(["xcodebuild", "-version"]),
        "build_command": os.environ.get("WEBP_STAGE_PROFILE_BUILD_COMMAND",
                                         "not provided"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "uname": command_output(["uname", "-a"]),
        "hardware": command_output(["system_profiler", "SPHardwareDataType"]),
        "gpu": command_output(["system_profiler", "SPDisplaysDataType"]),
        "power": command_output(["pmset", "-g", "batt"]),
        "thermal": command_output(["pmset", "-g", "therm"]),
    }


def run_profiles(args):
    if os.environ.get("WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT") != "1":
        raise SystemExit(
            "run requires WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT=1")
    if os.environ.get("WEBP_BENCHMARK_SESSION") != "exclusive":
        raise SystemExit("run requires WEBP_BENCHMARK_SESSION=exclusive")
    encoder = args.encoder.resolve()
    if not os.access(encoder, os.X_OK):
        raise SystemExit(f"encoder is not executable: {encoder}")
    help_result = subprocess.run(
        [str(encoder), "-longhelp"], check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if "-profile_repetitions" not in help_result.stdout:
        raise SystemExit(
            "encoder lacks the profiling hook; rebuild with "
            "WEBP_BUILD_ENCODER_STAGE_PROFILE_EXPERIMENT=1")
    manifest = prepare_dataset(args.dataset_dir.resolve())
    run_id = args.run_id or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir.resolve() / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    records_path = output_dir / "records.jsonl"
    commands_path = output_dir / "commands.jsonl"
    write_json(output_dir / "dataset_manifest.json", manifest)
    write_json(output_dir / "environment.json",
               environment_metadata(encoder, sys.argv))
    selected = set(args.cases.split(",")) if args.cases else None
    commands = []
    for case in manifest["cases"]:
        if selected is not None and case["case_id"] not in selected:
            continue
        for method in args.methods:
            for backend in args.backends:
                base_command = [str(encoder), "-quiet", "-lossless", "-exact",
                                "-q", str(args.quality), "-m", str(method)]
                common_env = os.environ.copy()
                common_env.update({
                    "WEBP_ENCODER_STAGE_PROFILE_EXPERIMENT": "1",
                    "WEBP_STAGE_PROFILE_OUTPUT": str(records_path),
                    "WEBP_STAGE_PROFILE_RUN_ID": run_id,
                    "WEBP_STAGE_PROFILE_CASE_ID": case["case_id"],
                    "WEBP_STAGE_PROFILE_BACKEND": backend,
                })
                if backend == "cpu":
                    common_env["WEBP_METAL"] = "0"
                else:
                    common_env.update({
                        "WEBP_METAL": "1",
                        "WEBP_METAL_MIN_PIXELS": "0",
                        "WEBP_METAL_HASH": "1",
                        "WEBP_METAL_HASH_MIN_PIXELS": "0",
                    })
                for trial in range(args.cold_repetitions):
                    command = base_command + ["-profile_repetitions", "1",
                                              case["path"]]
                    env = common_env.copy()
                    env["WEBP_STAGE_PROFILE_SAMPLE_SET"] = "cold"
                    commands.append({"case_id": case["case_id"],
                                     "method": method, "backend": backend,
                                     "sample_set": "cold", "trial": trial,
                                     "argv": command})
                    subprocess.run(command, env=env, check=True)
                if args.warm_repetitions > 0:
                    command = base_command + [
                        "-profile_repetitions", str(args.warm_repetitions + 1),
                        case["path"]]
                    env = common_env.copy()
                    env["WEBP_STAGE_PROFILE_SAMPLE_SET"] = "warm"
                    commands.append({"case_id": case["case_id"],
                                     "method": method, "backend": backend,
                                     "sample_set": "warm",
                                     "measured_repetitions": args.warm_repetitions,
                                     "argv": command})
                    subprocess.run(command, env=env, check=True)
    with commands_path.open("w") as output:
        for command in commands:
            output.write(json.dumps(command, sort_keys=True) + "\n")
    summarize(records_path, output_dir / "baseline.json", manifest)
    print(output_dir)


def distribution(values):
    median = statistics.median(values)
    deviations = [abs(value - median) for value in values]
    return {"n": len(values), "min": min(values), "median": median,
            "max": max(values), "mad": statistics.median(deviations)}


def summarize(records_path, output_path, manifest=None):
    records = []
    with records_path.open() as source:
        for line in source:
            if line.strip():
                record = json.loads(line)
                if record.get("schema") != SCHEMA:
                    raise ValueError(f"unexpected schema in {records_path}")
                if record["sample_role"] != "warmup":
                    records.append(record)
    groups = {}
    for record in records:
        key = (record["case_id"], record["method"], record["backend"],
               record["sample_role"])
        groups.setdefault(key, []).append(record)
    summaries = []
    for key, values in sorted(groups.items()):
        case_id, method, backend, sample_role = key
        first_value = values[0]
        stage_names = sorted({name for value in values
                              for name in value["stages"]})
        stage_summary = {}
        median_total = statistics.median([value["total_ns"] for value in values])
        for name in stage_names:
            samples = [value["stages"].get(name, {}).get("ns", 0)
                       for value in values]
            item = distribution(samples)
            item["median_share_total"] = item["median"] / median_total
            item["median_calls"] = statistics.median([
                value["stages"].get(name, {}).get("calls", 0)
                for value in values])
            stage_summary[name] = item
        summaries.append({
            "case_id": case_id, "method": method, "backend": backend,
            "sample_role": sample_role,
            "quality": first_value["quality"],
            "exact": first_value["exact"],
            "thread_level": first_value["thread_level"],
            "width": first_value["width"],
            "height": first_value["height"],
            "pixels": first_value["pixels"],
            "total_ns": distribution([value["total_ns"] for value in values]),
            "output_bytes": distribution([value["output_bytes"] for value in values]),
            "metal_cross_color_rate": sum(value["metal_cross_color"]
                                           for value in values) / len(values),
            "metal_hash_rate": sum(value["metal_hash"]
                                    for value in values) / len(values),
            "stages": stage_summary,
        })
    baseline = {
        "schema": "libwebp-encoder-stage-baseline-v1",
        "source": str(records_path.resolve()),
        "dataset_schema": manifest.get("schema") if manifest else None,
        "aggregation": "median; MAD is median absolute deviation; warmups excluded",
        "groups": summaries,
    }
    write_json(output_path, baseline)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="generate deterministic PPM inputs")
    prepare.add_argument("--dataset-dir", type=pathlib.Path,
                         default=pathlib.Path("profile-data/dataset"))
    run = subparsers.add_parser("run", help="execute serialized profile trials")
    run.add_argument("--encoder", type=pathlib.Path,
                     default=pathlib.Path("examples/cwebp"))
    run.add_argument("--dataset-dir", type=pathlib.Path,
                     default=pathlib.Path("profile-data/dataset"))
    run.add_argument("--output-dir", type=pathlib.Path,
                     default=pathlib.Path("profile-data/runs"))
    run.add_argument("--run-id")
    run.add_argument("--methods", type=int, nargs="+", default=[4, 6])
    run.add_argument("--backends", nargs="+", choices=("cpu", "metal"),
                     default=["cpu", "metal"])
    run.add_argument("--quality", type=int, default=75)
    run.add_argument("--cold-repetitions", type=int, default=3)
    run.add_argument("--warm-repetitions", type=int, default=3)
    run.add_argument("--cases", help="comma-separated case IDs (smoke/debug only)")
    summary = subparsers.add_parser("summarize", help="aggregate existing JSONL")
    summary.add_argument("records", type=pathlib.Path)
    summary.add_argument("--output", type=pathlib.Path,
                         default=pathlib.Path("baseline.json"))
    args = parser.parse_args()
    if args.command == "prepare":
        manifest = prepare_dataset(args.dataset_dir.resolve())
        print(args.dataset_dir.resolve() / "manifest.json")
        assert len(manifest["cases"]) == (
            len(publication_corpus.SIZES) * len(publication_corpus.CATEGORIES)
        )
    elif args.command == "run":
        run_profiles(args)
    else:
        summarize(args.records.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
