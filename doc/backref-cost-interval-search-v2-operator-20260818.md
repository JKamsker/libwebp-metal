# Interval-search v2 operator handoff

## Terminal handoff: timing is not authorized

The frozen phase-1 decision is `REJECT_TIMING` because the untimed independent
return rehearsal did not produce a complete schema-valid transfer report.
Do not invoke the command below from this handoff. The driver also enforces the
manifest's `timed_execution_authorized: false` gate before source admission.

The originally designed command, retained only so the frozen protocol can be
audited, was:

```sh
WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V2_COMMIT=<phase-1-commit> \
WEBP_BENCHMARK_SESSION=exclusive \
python3 scripts/execute_backref_cost_interval_search_v2.py run \
  /absolute/new/local/evidence/backref-cost-interval-search-v2-execution-20260818
```

Do not rerun, edit, tune, substitute local timing, overlap work, start CUDA, or
alter the host, global PATH, packages, toolchain, power/LPM, runner service, or
runner directories. A refusal is the cycle result. Retain the returned indexed
refusal archive, independently hash-verified lease record, and independent
post-deletion exact-child cleanup receipt. Never manually extract quarantine.
