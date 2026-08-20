#!/usr/bin/env python3
"""Canonical pinned-Xcode toolchain identity for Factorization V4."""

from __future__ import annotations

import hashlib
import json
import plistlib
import re
import subprocess
from pathlib import Path


DEVELOPER_DIR = Path("/Applications/Xcode-26.3.0.app/Contents/Developer")
TOOLCHAIN_BIN = DEVELOPER_DIR / "Toolchains/XcodeDefault.xctoolchain/usr/bin"
SDK_PATH = (DEVELOPER_DIR /
            "Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk")
STALE_V2_XCRUN_SHA256 = \
    "b3f741e4a6af192170bbb662221163e730870944b8ad29bfac455241789b8152"
CURRENT_UNREQUIRED_XCRUN_SHA256 = \
    "a439970aea2b4e435eac6518ff62c97fd1c57d8c731974027ad211b515c7a7b8"
STALE_V3_IDENTITY_CANONICAL_SHA256 = \
    "735eb9be26c9b7118819b502bf0e24b6d87e8da945d81858c22bebdf889ce077"

EXECUTABLE_PATHS = {
    "clang": TOOLCHAIN_BIN / "clang",
    "clang++": TOOLCHAIN_BIN / "clang++",
    "nm": TOOLCHAIN_BIN / "nm",
    "ar": TOOLCHAIN_BIN / "ar",
    "ranlib": TOOLCHAIN_BIN / "ranlib",
    "llvm-objdump": TOOLCHAIN_BIN / "llvm-objdump",
}
METADATA_PATHS = {
    "xcode-version-plist": DEVELOPER_DIR.parent / "version.plist",
    "toolchain-info-plist": (DEVELOPER_DIR /
                              "Toolchains/XcodeDefault.xctoolchain/ToolchainInfo.plist"),
    "sdk-settings-json": SDK_PATH / "SDKSettings.json",
    "sdk-settings-plist": SDK_PATH / "SDKSettings.plist",
}
VERSION_COMMANDS = {
    "clang": ("--version",),
    "clang++": ("--version",),
    "nm": ("--version",),
    "ranlib": ("-V",),
    "llvm-objdump": ("--version",),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_version(path: Path, arguments: tuple[str, ...]) -> dict[str, object]:
    result = subprocess.run(
        [str(path), *arguments], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    output = result.stdout + result.stderr
    return {
        "arguments": list(arguments),
        "returncode": result.returncode,
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "output_lines": output.decode("utf-8", errors="strict").splitlines(),
    }


def identity() -> dict[str, object]:
    for path in (*EXECUTABLE_PATHS.values(), *METADATA_PATHS.values()):
        if not path.is_file():
            raise RuntimeError(f"required pinned toolchain file is absent: {path}")
    with METADATA_PATHS["xcode-version-plist"].open("rb") as source:
        xcode = plistlib.load(source)
    with METADATA_PATHS["toolchain-info-plist"].open("rb") as source:
        toolchain = plistlib.load(source)
    with METADATA_PATHS["sdk-settings-plist"].open("rb") as source:
        sdk = plistlib.load(source)
    sdk_json = json.loads(
        METADATA_PATHS["sdk-settings-json"].read_text(encoding="utf-8"))
    if sdk_json.get("Version") != sdk.get("Version"):
        raise RuntimeError("SDK plist/json version disagreement")

    executables: dict[str, object] = {}
    for name, path in EXECUTABLE_PATHS.items():
        version = _run_version(path, VERSION_COMMANDS[name]) \
            if name in VERSION_COMMANDS else {
                "arguments": [], "returncode": None, "output_sha256": None,
                "output_lines": [],
                "version_source": "Xcode bundle metadata; ar has no standalone version query",
            }
        if name in ("clang", "clang++"):
            stable_lines = [line for line in version["output_lines"]
                            if not line.startswith("Target:")]
            version["output_lines"] = stable_lines
            version["output_sha256"] = hashlib.sha256(
                ("\n".join(stable_lines) + "\n").encode()).hexdigest()
        if name == "ranlib":
            matched = [line for line in version["output_lines"]
                       if re.fullmatch(r"Apple Inc\. version cctools-[0-9.]+", line)]
            if len(matched) != 1:
                raise RuntimeError("ranlib cctools version identity is unavailable")
        executables[name] = {
            "path": str(path),
            "canonical_path": str(path.resolve()),
            "sha256": sha256(path.resolve()),
            "version": version,
        }

    metadata = {
        name: {"path": str(path), "canonical_path": str(path.resolve()),
               "bytes": path.stat().st_size, "sha256": sha256(path.resolve())}
        for name, path in METADATA_PATHS.items()
    }
    return {
        "schema": "libwebp-backref-cost-specialization-factorization-v4-toolchain-identity-v1",
        "developer_dir": str(DEVELOPER_DIR),
        "xcode": {
            "short_version": xcode["CFBundleShortVersionString"],
            "bundle_version": xcode["CFBundleVersion"],
            "product_build_version": xcode["ProductBuildVersion"],
            "toolchain_identifier": toolchain["Identifier"],
        },
        "sdk": {
            "path": str(SDK_PATH),
            "canonical_path": str(SDK_PATH.resolve()),
            "version": sdk["Version"],
            "canonical_name": sdk["CanonicalName"],
            "display_name": sdk["DisplayName"],
        },
        "executables": executables,
        "metadata": metadata,
        "required_executable_names": list(EXECUTABLE_PATHS),
        "required_metadata_names": list(METADATA_PATHS),
        "xcrun_required": False,
        "stale_v2_xcrun_sha256": STALE_V2_XCRUN_SHA256,
        "stale_v2_xcrun_rejected": all(
            item["sha256"] != STALE_V2_XCRUN_SHA256
            for item in executables.values()),
        "stale_v3_identity_canonical_sha256":
            STALE_V3_IDENTITY_CANONICAL_SHA256,
    }


def main() -> int:
    print(json.dumps(identity(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
