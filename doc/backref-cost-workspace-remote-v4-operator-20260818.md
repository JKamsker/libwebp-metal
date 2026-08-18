# Remote v4 operator handoff

Use the clean designer commit only. Run the repository untimed v4 tests first,
then perform exactly one command with both required environment values:

```sh
WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V4_COMMIT=<designer-commit> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/execute_backref_cost_workspace_remote_v4.py run \
  /absolute/new/local/evidence/backref-cost-workspace-remote-v4-execution-20260818
```

Do not rerun, edit, tune, substitute a local run, start CUDA, overlap a timed
process, or alter the host, power state, runner service, or runner directory.
Admission or resource refusal is the result for this cycle.

The driver must return `return-protocol/lease-record.json` with a matching
`lease-transfer.json` before extraction. It must return the remote builder
digest and complete inventory, verify the archive hash, inspect before extract,
verify `artifact-hashes.json`, and create/verify
`returned-evidence-hashes.json`. `return-protocol/cleanup-receipt.json` must be
produced only after exact-child deletion and prove absence. On extractor
refusal, retain `return-protocol/quarantine/evidence.tar.gz`, both digests, the
complete member inventory, and exact offending member/reason. Never manually
extract a refused archive.
