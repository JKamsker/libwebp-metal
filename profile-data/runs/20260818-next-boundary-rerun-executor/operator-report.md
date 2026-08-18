# Next-boundary continuation executor handoff

This is the separate continuation evidence index for the frozen boundary experiments. The raw evidence remains at the external paths recorded in `evidence-index.json`; the prior blocked evidence under `20260818/predictor-boundary` and `20260818/backref-exact` was not overwritten.

## Frozen authority

- Base: `cdf2539b29bb767b1557e5069cfee9c111f07358`
- Designer: `cdf64a57790d3e7d52fe2685afe0976e41cbe633`
- Runnable source: `a964bb6aac67a64f71fa105db5fc8b04649ab9f0`
- Manifest SHA-256: `476c54607a463908ed44cf8e8d1b955af35f3def6f15d11da423a1bd90d6e969`
- Operator SHA-256: `a790796c2d715b3b6405b801de88401e379e710bbf09297d55038a98e993d054`

The operator’s exact-source preflight requires its expected-commit environment value to equal the runnable `HEAD`. Therefore the continuation commands used `a964bb6…` for that environment value while separately recording the immutable designer handoff `cdf64a5…`.

## Execution and lease protocol

The fixed Darwin `vm_stat` fallback and all frozen untimed gates passed before timing. The machine had one physical Apple M4 Pro Metal 4 device. The frozen operator acquired `/tmp/libwebp-metal-next-boundary.lock` for each experiment, ran one matrix at a time, released it in its `finally` path, and the lock was absent before the second experiment and after final handoff. No CUDA or parallel benchmark process was used.

The exact commands and complete stdout/stderr transcript paths are recorded in `evidence-index.json`. Output directories were fresh continuation paths:

- `/Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818-cycle2/predictor-boundary`
- `/Users/jonaskamsker/.codex/worktrees/7919/libwebp-metal-evidence/20260818-cycle2/backref-exact`

## Raw matrix inventory

Both experiments completed timing with the frozen matrix: 80 command rows, 200 raw encoder records, 18 correctness rows, and 80 per-command stderr files.

`predictor_boundary` used `photo-medium` as tune and `photo-large` as holdout. `backref_exact` used `texture-medium` as tune and `texture-large` as holdout. Each used methods 4 and 6, seven cold record/control pairs, and three warm record/control pairs per case/method. Raw record roles were 56 cold, 24 warmup, and 120 warm records per experiment. All correctness rows report deterministic bitstreams, decoded-pixel equality, and transactional fallback.

The operator reports no failure. Predictor duration was 118.6174635887146 seconds with maximum observed RSS 354729984 bytes. Backref duration was 80.33265995979309 seconds with maximum observed RSS 356139008 bytes. Both are below the frozen resource ceilings. Power was AC with the internal battery charged; the captured thermal diagnostics reported no thermal or performance warning.

## Untimed validation

Passed before execution: Darwin free-memory portability, frozen manifest validation, independent build/runtime/default-off/refusal/no-lease guards, full boundary correctness/determinism/fallback checks, publication corpus verification, round-trip, accelerator interface, Python/JSON validation, and `git diff --check`.

This executor handoff contains no performance interpretation, ratio calculation, acceptance decision, production change, hypothesis change, parameter change, or new experiment.
