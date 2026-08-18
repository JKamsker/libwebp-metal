# Next-boundary experiment evaluation (2026-08-18)

## Outcome

Neither `predictor_boundary` nor `backref_exact` produced a measurement. Both
exact frozen commands stopped in the free-memory preflight before the host
lease, device check, build, corpus generation, correctness gate, or timed
matrix. No speedup, slowdown, stage share, uncertainty interval, p95 result,
correctness result, or production performance conclusion can be inferred.

The research diagnostics remain default-off and are retained without a
performance disposition. No encoder implementation, threshold, policy,
accelerator ABI, public API, or runtime default is promoted or rejected by this
cycle.

## Evidence and integrity audit

The audited ancestry is:

1. default-branch anchor `cdf2539b29bb767b1557e5069cfee9c111f07358`;
2. designer commit `cdf64a57790d3e7d52fe2685afe0976e41cbe633`;
3. executor evidence commit `78eb0f2e8a47433e699bdd0efa3aee9b78f03408`.

The executor commit adds only
`profile-data/runs/20260818-next-boundary-executor/evidence-index.json`; a diff
against the designer commit contains no source, script, protocol, threshold,
or design change. The frozen manifest SHA-256 independently verifies as
`476c54607a463908ed44cf8e8d1b955af35f3def6f15d11da423a1bd90d6e969`.

The external evidence directories are:

- `/Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818/predictor-boundary`;
- `/Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818/backref-exact`.

Their `artifact-hashes.json` files verify as
`9524bbc6af1300154416261ed25ff8d3f10e275502454de2eb5c396122ee2aa9`
and
`13ef949dc1acf86270638b2d9e3edd216479226e83c1a6e5d0ce004e4f5200a4`,
respectively. Every file named by both hash manifests also verifies. The raw
stderr files contain the same traceback at line 255 of the designer operator:

```text
ValueError: unrecognized configuration name
```

The failed operation is
`os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")`. On the recorded
Darwin/Python 3.9.6 host, the first configuration name is unavailable.

Each `commands.jsonl` contains one attempt row with the designer commit, frozen
manifest hash, exact experiment/runtime flag, exact expected commit, and exact
`WEBP_BENCHMARK_SESSION=exclusive` request. No `preflight.json`,
`correctness.json`, `records.jsonl`, timed command row, dispatch stderr, or
encoded output exists. The operator source confirms that the failing memory
query precedes lease creation. `/tmp/libwebp-metal-next-boundary.lock` was
absent after execution and during evaluation.

The evidence index declares predictor first and backref second, and the
executor reports strict serial execution. The supplemental rows share one
capture timestamp and contain no distinct attempt start times, so attempt order
cannot be reconstructed independently from timestamps. This does not create a
timed-overlap ambiguity: both commands failed before acquiring the lease or
starting any workload.

No CUDA command or artifact appears. The machine supplement reports one Apple
M4 Pro Metal device, but that is a post-failure read-only diagnostic; the
frozen device gate was not reached. Its SDK diagnostic also failed, but that is
not the observed operator blocker because the operator never reached SDK
capture.

## Criteria and decisions

| Experiment | Frozen criteria | Observed evidence | Decision |
|---|---|---|---|
| `predictor_boundary` | Photo-large methods 4/6, cold/warm selector+apply and selector shares; predictor-map deferral rule; record/control median and p95 overhead; correctness, determinism, fallback, resource ceilings | No records or correctness gate. All shares, ratios, MAD/bootstrap intervals, p95s, strata, dispatches, and ceilings are unobserved/not assessable. Designer-phase untimed validation is code validation, not an executor result. | Do not promote or performance-reject. Retain the default-off diagnostic and the prior rejection of residual-only dispatch. A future broader resident/fused boundary remains contingent on the unchanged frozen criteria. |
| `backref_exact` | Texture-large methods 4/6, cold/warm standard-LZ77 and accounted shares; record/control median and p95 overhead; correctness, determinism, fallback, resource ceilings | No records or correctness gate. All shares, ratios, MAD/bootstrap intervals, p95s, strata, dispatches, and ceilings are unobserved/not assessable. Designer-phase untimed validation is code validation, not an executor result. | Do not promote or performance-reject. Retain the default-off diagnostic. Exact candidate evaluation remains a future opportunity while CPU serial choice and cache semantics remain authoritative. |

There is no uncertainty estimate to report because there are no observations.
The absence of observations is not a zero effect and is not evidence that any
criterion passed or failed. Independent ratios are not combined.

## Evidence-supported consequence

The observed blocker justifies one research-operator portability correction.
The 8 GiB minimum, corpus, matrix, methods, lifecycle, order, hypotheses,
metrics, acceptance criteria, and experiment gates remain unchanged. The
operator now uses `SC_AVPHYS_PAGES` where available and, on Darwin only, falls
back to `vm_stat`. It counts free, inactive, and speculative pages, excluding
purgeable pages to avoid double-counting inactive memory. Missing fields,
malformed output, command failure, invalid values, and unsupported non-Darwin
`sysconf` all fail closed before lease acquisition.

`scripts/test_next_boundary_operator_portability.py` is a pure untimed unit
guard for the sysconf path, representative 16 KiB Darwin output, malformed
output, failed `vm_stat`, and unsupported non-Darwin behavior.
`scripts/test_experiment_guards.py` invokes it without granting an exclusive
benchmark session. The portable correctness workflow runs that static guard as
a separate Linux job; it does not enter either experiment pipeline.

This tooling correction does not reinterpret either failed attempt and does
not authorize a rerun in this cycle. Any later timing must be separately
released from its exact source commit, preserve the frozen manifest and
criteria, use new evidence directories, and repeat the normal designer/
executor/evaluator separation. No new experiment is designed here because no
new scientific question arose; the existing two questions remain unanswered.

## Publication boundary and remaining opportunities

This cycle supports only a process claim: both diagnostics failed safely before
timing and their evidence was preserved. It supports no production performance
claim.

The remaining optimization opportunities are unchanged:

- a broader fused or resident predictor selector+apply boundary, potentially
  including predictor-map encoding if its measured share requires it, never a
  resurrection of standalone residual dispatch;
- exact texture backward-reference candidate evaluation while retaining CPU
  order-sensitive selection, traceback, and cache semantics.

Natural-content, different-day, multi-device, energy, memory-pressure,
concurrency, and long-run thermal generalization also remain unmeasured.
