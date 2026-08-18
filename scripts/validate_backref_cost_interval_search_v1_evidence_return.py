#!/usr/bin/env python3
"""Untimed live pandocs-agent validation of the exact v5 return protocol."""

from __future__ import annotations

import argparse
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import backref_cost_interval_search_v1_admission as admission
import backref_cost_interval_search_v1_archive as protocol
import execute_backref_cost_interval_search_v1 as driver


SETUP = r'''import hashlib,json,os,sys,tarfile,io
from pathlib import Path
root=Path(sys.argv[1]); evidence=root/'evidence'
(evidence/'nested'/'deeper').mkdir(parents=True)
(evidence/'root.txt').write_text('representative root evidence\n')
(evidence/'nested'/'deeper'/'record.json').write_text('{"nested":true,"status":"PASS"}\n')
(evidence/'lease-record.json').write_text('{"schema":"libwebp-backref-cost-interval-search-v1-lease-v1","path":"validation-only","acquired":false,"released":false,"acquisition_attempted":false}\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
rows=[{"path":p.relative_to(evidence).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(evidence.rglob('*')) if p.is_file()]
(evidence/'artifact-hashes.json').write_text(json.dumps({"schema":"libwebp-backref-cost-interval-search-v1-artifact-hashes-v1","artifacts":rows},indent=2,sort_keys=True)+'\n')
fixtures=root/'fixtures'; fixtures.mkdir()
specs=[('traversal','evidence/../escape',tarfile.REGTYPE),('absolute','/evidence/escape',tarfile.REGTYPE),('symlink','evidence/link',tarfile.SYMTYPE),('hardlink','evidence/hard',tarfile.LNKTYPE),('fifo','evidence/fifo',tarfile.FIFOTYPE)]
for label,name,kind in specs:
  with tarfile.open(fixtures/(label+'.tar.gz'),'w:gz') as opened:
    safe=tarfile.TarInfo('evidence/safe.txt'); safe.size=4; opened.addfile(safe,io.BytesIO(b'safe'))
    bad=tarfile.TarInfo(name); bad.type=kind
    if kind in (tarfile.SYMTYPE,tarfile.LNKTYPE): bad.linkname='../../outside'
    opened.addfile(bad)
    tail=tarfile.TarInfo('evidence/tail.txt'); tail.size=4; opened.addfile(tail,io.BytesIO(b'tail'))
for label in ('symlink','hardlink','fifo'):
  bad=root/('builder-'+label); bad.mkdir(); regular=bad/'record'; regular.write_text('x')
  if label=='symlink': (bad/'bad').symlink_to(regular)
  elif label=='hardlink': os.link(regular,bad/'bad')
  else: os.mkfifo(bad/'bad')
  candidates=[p for p in sorted(bad.iterdir()) if p.is_file()]
  rows=[{"path":p.name,"bytes":p.stat().st_size,"sha256":sha(p)} for p in candidates]
  (bad/'artifact-hashes.json').write_text(json.dumps({"schema":"libwebp-backref-cost-interval-search-v1-artifact-hashes-v1","artifacts":rows},indent=2,sort_keys=True)+'\n')
'''


def remote_protocol(arguments: list[str], *, check: bool = True):
    argv = " ".join(shlex.quote(value) for value in arguments)
    return admission.ssh(f"python3 - {argv}",
                         input_bytes=Path(protocol.__file__).read_bytes(),
                         check=check)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    if os.environ.get("WEBP_BENCHMARK_SESSION") is not None:
        raise RuntimeError("live evidence validation requires benchmark session unset")
    if not output.is_absolute() or output.exists():
        raise RuntimeError("output must be a new absolute path")
    process = admission.remote_process_guard()
    generated = admission.remote_path_guard("generate")
    record = {"home": generated["home"], "safe_root": generated["safe_root"],
              "run_directory": generated["run_directory"]}
    remote = record["run_directory"]
    cleanup = None
    with tempfile.TemporaryDirectory(prefix="interval-search-v1-live-return-") as raw:
        temporary = Path(raw)
        transfers = {}
        builder_rejections = {}
        malicious_rejections = {}
        try:
            admission.ssh(f"python3 - {shlex.quote(remote)}",
                          input_bytes=SETUP.encode())
            built = remote_protocol([
                "build", f"{remote}/evidence",
                f"{remote}/evidence/artifact-hashes.json",
                f"{remote}/evidence.tar.gz", f"{remote}/archive-inventory.json",
                f"{remote}/archive-digest.json",
            ])
            for name in ("evidence.tar.gz", "archive-inventory.json",
                         "archive-digest.json"):
                local = temporary / name
                transfers[name] = driver.fetch_regular(record, name, local)
            digest = json.loads((temporary / "archive-digest.json").read_text())
            inventory = json.loads((temporary / "archive-inventory.json").read_text())
            if digest["archive_sha256"] != transfers["evidence.tar.gz"][
                    "local_sha256"]:
                raise RuntimeError("live archive digest mismatch")
            if digest["inventory_sha256"] != protocol.sha256(
                    temporary / "archive-inventory.json"):
                raise RuntimeError("live inventory digest mismatch")
            if protocol.inspect_archive(temporary / "evidence.tar.gz") != inventory:
                raise RuntimeError("live full member inventory mismatch")
            output.mkdir(parents=True)
            protocol.extract_archive(temporary / "evidence.tar.gz",
                                     output / "returned")
            for label in ("traversal", "absolute", "symlink", "hardlink", "fifo"):
                local = output / "fixtures" / f"{label}.tar.gz"
                local.parent.mkdir(exist_ok=True)
                transfers[f"fixture-{label}"] = driver.fetch_regular(
                    record, f"fixtures/{label}.tar.gz", local)
                observed = protocol.inspect_archive(local)
                target = output / f"must-not-extract-{label}"
                try:
                    protocol.extract_archive(local, target)
                    raise RuntimeError(f"live malicious {label} fixture was accepted")
                except protocol.ArchiveRefusal as error:
                    malicious_rejections[label] = {
                        "offending_member": error.member, "reason": error.reason,
                        "complete_member_inventory": observed,
                        "no_content_extracted": not target.exists(),
                    }
            for label in ("symlink", "hardlink", "fifo"):
                bad = f"{remote}/builder-{label}"
                result = remote_protocol([
                    "build", bad, f"{bad}/artifact-hashes.json",
                    f"{remote}/bad-{label}.tar.gz",
                    f"{remote}/bad-{label}-inventory.json",
                    f"{remote}/bad-{label}-digest.json",
                ], check=False)
                if result.returncode == 0:
                    raise RuntimeError(f"live builder accepted {label}")
                builder_rejections[label] = {
                    "exit_code": result.returncode,
                    "stdout": result.stdout.decode(errors="replace"),
                    "stderr": result.stderr.decode(errors="replace"),
                }
        finally:
            cleanup = admission.cleanup_remote(record["home"], record["safe_root"],
                                               record["run_directory"])
        report = {
            "schema": "libwebp-backref-cost-interval-search-v1-live-return-validation-v1",
            "status": "PASS", "remote_host_alias": admission.HOST,
            "benchmark_lease_acquisition_attempted": False,
            "timed_binary_invoked": False, "host_settings_changed": False,
            "runner_directories_or_services_touched": False,
            "process_isolation": process, "path_generation": generated,
            "builder_stdout": built.stdout.decode(errors="replace"),
            "builder_stderr": built.stderr.decode(errors="replace"),
            "transfers": transfers, "archive_digest": digest,
            "full_member_inventory": inventory,
            "artifact_index_verified_after_extraction": True,
            "builder_rejections": builder_rejections,
            "malicious_rejections": malicious_rejections,
            "cleanup_receipt": cleanup,
            "local_returned_index_created_and_verified": True,
        }
        protocol.write_json(output / "live-validation.json", report)
        protocol.write_returned_index(output, [])
        protocol.verify_returned_index(output / "returned-evidence-hashes.json",
                                       output)
    print(json.dumps({"status": "PASS", "output": str(output),
                      "member_count": inventory["member_count"],
                      "malicious_rejections": len(malicious_rejections),
                      "builder_rejections": len(builder_rejections)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError,
            protocol.ArchiveRefusal, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
