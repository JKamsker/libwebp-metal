# Remote v3 operator handoff

This is a frozen handoff, not authorization to run timing. The protocol commit
reported with this cycle is the only eligible source identity. Earlier cycles,
refusals, host observations, and the untimed admission rehearsal contain zero
performance samples and are provenance only.

## Admission-only rehearsal

Admission-only requires an exact clean commit and an unset benchmark session:

```sh
env -u WEBP_BENCHMARK_SESSION \
WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V3_COMMIT=<EXACT_COMMIT> \
python3 scripts/execute_backref_cost_workspace_remote_v3.py admission-only \
  /new/absolute/admission-evidence-directory
```

It uses the same `admission.admit_source` path as `run`, exercises transfer
hashes, repository-context verification, exact clone identity, malformed
rejection, scoped cleanup, and absence, then stops before lease acquisition or
any timed binary. It never changes runner services/directories or host settings.

## Frozen timed command

Only a separately authorized operator may invoke this exact shape once from
the clean frozen protocol commit:

```sh
WEBP_EXPECTED_BACKREF_COST_WORKSPACE_REMOTE_V3_COMMIT=<FROZEN_PROTOCOL_COMMIT> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/execute_backref_cost_workspace_remote_v3.py run \
  /new/absolute/evidence/backref-cost-workspace-remote-v3
```

Do not retry, substitute a host, alter counts/order/criteria, enable recorders,
change AC/LPM/power state, stop runner services, enter runner directories, or
use CUDA. Any mismatch or active `Runner.Worker` fails closed.

The operator verifies exact Darwin arm64 Apple M4 identity, compiler and
effective SDK, AC, LPM off from both sources, thermal/performance lines,
physical/available memory, disk, process isolation, and sole synchronous
execution. It records preflight, immediately-pre-timing, and post-timing state;
separate child stderr; transfer/source/tree hashes; lease acquisition/release;
evidence return hashes; and exact-child cleanup proof.

Acceptance is automatic and conjunctive: 26 correctness/fallback cells; exact
408-process/1,560-retained-sample inventory; every one of 12 holdout cells with
paired median candidate/baseline ratio at most 0.99 and nearest-rank p95 ratio
at most 1.01; all identity, state, resource, lease, transfer, evidence, and
cleanup gates. Tune cells are descriptive only. Production promotion is a
separate decision and is not part of this cycle.
