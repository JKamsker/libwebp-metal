#!/usr/bin/env python3
"""Validate deterministic lossless outputs for a stage-profile dataset."""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def run(command, environment):
    subprocess.run(command, env=environment, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    parser.add_argument("--encoder", type=pathlib.Path, required=True)
    parser.add_argument("--decoder", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--methods", type=int, nargs="+", default=[4, 6])
    parser.add_argument("--quality", type=int, default=75)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    encoder = args.encoder.resolve()
    decoder = args.decoder.resolve()
    output = args.output.resolve()
    entries = []
    with tempfile.TemporaryDirectory(prefix="libwebp-stage-output-check.") as raw:
        temporary = pathlib.Path(raw)
        for case in manifest["cases"]:
            input_path = pathlib.Path(case["path"])
            assert digest(input_path) == case["sha256"]
            for method in args.methods:
                results = {}
                for backend in ("cpu", "metal"):
                    environment = os.environ.copy()
                    if backend == "cpu":
                        environment["WEBP_METAL"] = "0"
                    else:
                        environment.update({
                            "WEBP_METAL": "1",
                            "WEBP_METAL_MIN_PIXELS": "0",
                            "WEBP_METAL_HASH": "1",
                            "WEBP_METAL_HASH_MIN_PIXELS": "0",
                        })
                    hashes = []
                    first_output = temporary / f"{case['case_id']}-m{method}-{backend}.webp"
                    for trial in range(2):
                        encoded = temporary / (
                            f"{case['case_id']}-m{method}-{backend}-{trial}.webp")
                        run([str(encoder), "-quiet", "-lossless", "-exact", "-q",
                             str(args.quality), "-m", str(method), str(input_path),
                             "-o", str(encoded)], environment)
                        hashes.append(digest(encoded))
                        if trial == 0:
                            encoded.rename(first_output)
                    assert hashes[0] == hashes[1]
                    decoded = temporary / f"{case['case_id']}-m{method}-{backend}.pam"
                    run([str(decoder), "-quiet", str(first_output), "-pam", "-o",
                         str(decoded)], os.environ.copy())
                    results[backend] = {
                        "bitstream_sha256": hashes[0],
                        "output_bytes": first_output.stat().st_size,
                        "decoded_sha256": digest(decoded),
                    }
                assert results["cpu"]["decoded_sha256"] == \
                    results["metal"]["decoded_sha256"]
                entries.append({"case_id": case["case_id"], "method": method,
                                "cpu": results["cpu"], "metal": results["metal"]})
    result = {
        "schema": "libwebp-encoder-stage-output-validation-v1",
        "manifest": str(args.manifest.resolve()),
        "encoder": str(encoder),
        "decoder": str(decoder),
        "quality": args.quality,
        "checks": {
            "repeated_cpu_bitstream_hash_equal": True,
            "repeated_metal_bitstream_hash_equal": True,
            "cpu_metal_decoded_pixels_equal": True,
        },
        "entries": entries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
