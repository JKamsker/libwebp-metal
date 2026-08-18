# Backref-cost workspace remote v3 design

Status: implementation design, default off, untimed. Baseline:
`805e5ac4341ccf0d1ef960adb9107275652c973f`.

The v3 cycle preserves the exact correctness-validated CostManager workspace
candidate. It does not tune the algorithm. Integer costs, strict tie handling,
update and reference order, ten inline nodes plus 490 exact-sized workspace
nodes, traceback, cache selection, and transactional allocation-failure
fallback are unchanged. Earlier cycles and zero-sample infrastructure
observations are provenance only and cannot enter v3 performance evidence.

## Independent gates and omission

V3 uses only these new identities:

- build: `WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT`;
- private compile macro: `WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT`;
- runtime: `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT=1`;
- fault injection: `WEBP_BACKREF_COST_WORKSPACE_REMOTE_V3_EXPERIMENT_INJECT_FAILURE=1`;
- runner: `backref_cost_workspace_remote_v3_experiment_runner`.

All workspace experiment compile gates are mutually exclusive. Ordinary CMake
and `makefile.unix` builds omit the v3 source, symbols, runner target, runtime
behavior, runtime/fault strings, and protocol scripts from binaries. The runner
checks exact `WEBP_BENCHMARK_SESSION=exclusive` before input loading or timing.

## Structurally safe admission

`backref_cost_workspace_remote_v3_paths.py` retains the v2 canonical-home,
real-directory, strict `run.XXXXXX`, direct-child, symlink, traversal, scoped
cleanup, and absence checks under a new v3 safe root. The shared admission
implementation then:

1. refuses any active `Runner.Worker` job and competing benchmark/CUDA process
   without touching services;
2. creates a bundle for the exact clean expected commit and records its commit,
   tree, and critical source SHA-256 values;
3. transfers into the validated run child and requires matching local/remote
   SHA-256;
4. creates an empty bare repository at the fixed scoped `verify.git` child;
5. runs `git -C ABSOLUTE_VERIFY_REPOSITORY bundle verify ABSOLUTE_BUNDLE`;
6. removes that verification repository, clones the verified bundle, checks out
   the exact expected commit detached, and proves exact tree, clean status, and
   source SHA-256 values;
7. on any failure removes only fixed scoped verification/clone state, while the
   canonical path guard alone authorizes whole-run cleanup.

Bundle verification is never invoked outside repository context. SHA or path
checks are never advisory. A malformed bundle rehearsal must be rejected and
must leave neither its scoped verification repository nor clone. Final cleanup
removes only the exact validated run child and proves absence.

`execute_backref_cost_workspace_remote_v3.py admission-only` and `run` both
call `admission.admit_source`; a unit test executes both dispatches against the
same mocked function. Admission-only additionally tests malformed rejection,
then stops before benchmark lease acquisition and before any timed binary. It
requires `WEBP_BENCHMARK_SESSION` to be unset. Timed `run` requires its exact
value to be `exclusive` before remote admission.

No design, test, or rehearsal command changes host power/LPM settings, runner
directories/services, or production state. No CUDA path is permitted.
