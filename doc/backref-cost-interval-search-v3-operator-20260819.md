# Backref-cost interval-search v3 operator handoff

From the exact clean Phase-1 commit, local validation is:

```sh
env -u WEBP_BENCHMARK_SESSION WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V3_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_interval_search_v3.py validate
```

Phase 1 used the same expected-commit form with `rehearse` and a new absolute
output, once for the exact untimed workload and once with
`--refusal-fixture missing`. Neither command may carry a benchmark session.

Phase 2 may run exactly once, only if the manifest authorizes it:

```sh
env WEBP_BENCHMARK_SESSION=exclusive WEBP_EXPECTED_BACKREF_COST_INTERVAL_SEARCH_V3_COMMIT="$(git rev-parse HEAD)" python3 scripts/execute_backref_cost_interval_search_v3.py run /Users/jonaskamsker/.codex/worktrees/f379/libwebp-metal/evidence/backref-cost-interval-search-v3-execution-20260819
```

Do not substitute rehearsal mode, retry, edit the source/manifest/protocol,
reuse prior samples, install tools, change host/power/runner state, or run a
local timed fallback. Preserve the returned raw evidence without evaluation;
Phase 3 independently recomputes every statistic.
