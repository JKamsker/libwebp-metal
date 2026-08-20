# Backref-cost specialization factorization v4 Phase 3

## Decision

The diagnostic passes, but H fails the frozen production gate. Retain the
factorization as diagnostic-only and default-off; do not promote it to
production.

The decisive failures are not marginal bookkeeping failures. Photo method 4
whole encode regresses by a mean 1.941% with a wholly positive 95% bootstrap
interval. Every whole-encode cell has at least one paired B-to-H regression
above the frozen +0.50% limit, and graphic method 6 also has an upper confidence
bound above zero. Photo method 4 DP steady additionally has a +2.437% maximum
paired regression.

## Frozen pairwise results

Percentages are paired `100 * (Y - X) / X`; negative is faster. Each entry is
the arithmetic mean and deterministic 100,000-resample paired-bootstrap 95%
percentile interval over the 12 predeclared aligned rows. The complete paired
values, median, sample standard deviation, minimum, maximum, sign counts, seed,
and interval are in
`evidence/backref-cost-specialization-factorization-v4-phase3-evaluation-20260820.json`.
“Production” applies only to B-to-H DP steady and whole encode. A pass requires
a negative mean, nonpositive upper confidence bound, and no paired regression
above +0.50%.

| Cell | Metric | B→L layout/control | L→H hint | B→H total | Frozen classification | Production |
| --- | --- | ---: | ---: | ---: | --- | --- |
| photo-m4 | DP total | +4.027% [+0.834, +7.360] | -4.338% [-7.335, -1.520] | -0.791% [-1.325, -0.094] | interaction-mixed-opposite-sign | — |
| photo-m4 | DP steady | +4.200% [+0.862, +7.707] | -4.506% [-7.601, -1.578] | -0.826% [-1.365, -0.112] | interaction-mixed-opposite-sign | FAIL: paired row > +0.50% |
| photo-m4 | whole encode | +0.391% [+0.042, +0.733] | +1.554% [+0.327, +2.653] | +1.941% [+0.975, +2.794] | hint-dominant | FAIL: mean, CI, paired row |
| photo-m6 | DP total | -0.766% [-1.192, -0.351] | -0.577% [-0.825, -0.287] | -1.339% [-1.841, -0.837] | interaction-mixed | — |
| photo-m6 | DP steady | -0.749% [-1.189, -0.324] | -0.605% [-0.854, -0.322] | -1.349% [-1.858, -0.837] | interaction-mixed | PASS |
| photo-m6 | whole encode | -1.346% [-2.115, -0.565] | +0.077% [-0.129, +0.276] | -1.273% [-1.959, -0.561] | interaction-mixed-opposite-sign | FAIL: paired row > +0.50% |
| graphic-m4 | DP total | +0.400% [+0.180, +0.611] | -0.913% [-1.145, -0.726] | -0.518% [-0.737, -0.308] | interaction-mixed-opposite-sign | — |
| graphic-m4 | DP steady | +0.412% [+0.204, +0.612] | -0.937% [-1.174, -0.755] | -0.529% [-0.746, -0.326] | interaction-mixed-opposite-sign | PASS |
| graphic-m4 | whole encode | +0.333% [-0.298, +0.908] | -0.816% [-1.146, -0.496] | -0.490% [-0.919, -0.093] | interaction-mixed-opposite-sign | FAIL: paired row > +0.50% |
| graphic-m6 | DP total | -0.021% [-0.234, +0.181] | -0.396% [-0.545, -0.182] | -0.418% [-0.583, -0.242] | hint-dominant | — |
| graphic-m6 | DP steady | -0.009% [-0.224, +0.188] | -0.398% [-0.554, -0.179] | -0.408% [-0.572, -0.235] | hint-dominant | PASS |
| graphic-m6 | whole encode | -0.809% [-1.324, -0.374] | +0.322% [-0.012, +0.670] | -0.490% [-1.064, +0.114] | interaction-mixed-opposite-sign | FAIL: CI, paired row |

## Causal interpretation

B-to-L is layout/control, L-to-H is the append hint within matched
always-specialized structure, and B-to-H is their simultaneous total.

The factors do not have stable effects across content and method. At method 4,
layout regresses DP while the hint improves DP for both photo and graphic, so
the total is a smaller net gain. Photo method 4 then reverses at whole encode:
both components regress, producing the only positive B-to-H whole-encode mean.
At method 6, photo DP gains are mixed/additive, while graphic DP is
hint-dominant because its layout component is near zero. Whole encode is again
different: layout supplies the gain while the hint is near-zero/slower for
both content classes. Thus the append hint has a measurable DP-local effect,
but it is context-sensitive and does not translate into a reliable whole-
encode production benefit.

## Independent verification

The exact first-parent chain is main `f289499b` → Phase 1A `1f60c324` →
Phase 1B `c271d129` → Phase 2 `b06596fb`. Phase 1B adds only 23 rehearsal and
authorization files; Phase 2 adds only its 135-file execution tree plus its
audit. Every manifest-frozen artifact remains byte-identical.

Payload identity is a four-way manifest/generator/fixture/rehearsal agreement
at SHA-256 `d34b944e…ba4db0`; stale V2 and V3 identities are rejected. The
toolchain envelope agrees across manifest, independent fixture, and remote
admission: Xcode 26.3 build 17C529, `macosx26.2`, with absolute pinned clang,
clang++, nm, ar, ranlib, and llvm-objdump identities and no xcrun in required
lists.

Committed source/evidence establishes ordinary-build omission, selector-once
before mutation, one closed selected body, absent=B and invalid-value refusal,
guard isolation, unchanged public ABI, sanitizer/integer/fallback/tie/update-
order/traceback semantics, exact bitstream/pixel/RGB/repeat/input behavior,
and recorder-free timing. With `-Wl,-no_deduplicate`, all six private addresses
are distinct. B/L DP and PushInterval sizes, instruction/branch/load/store
counts and mnemonic digests are equal; H differs only at the intended larger
PushInterval hint boundary.

Both raw hash layers recompute: 123 archive artifacts at index SHA-256
`a979120c…b59459a`, and 133 returned artifacts at `6ef2b10b…9ee9`. The
44,012-byte safe 126-member archive and 55,858-byte framed stream are below
their 786,432-byte and exclusive 1,048,576-byte caps. Exact frames are source,
operator, archive, lease, declaration, one chunk, integrity, then cleanup-last.
One exclusive lease was acquired/released; discovered PID signals, profiler
workloads, retries, reruns, and post-run remote cleanup contacts are zero, and
exact-child absence is proved. The sole Phase 1 rehearsal remained one
zero-workload/zero-lease transaction and was not rerun; Phase 2 used exactly
one host session.

Raw inventory is exactly 36 profile processes, 180 runner rows, 180 stage rows,
36 excluded warmups, 144 retained rows, and 12 work rows in frozen
photo/graphic × method 4/6 × repetition/variant order. The correctness gate
performed 24 executions (two per B/L/H case/method) and retained four aggregate
case/method records. Work, timed, and correctness bitstream sizes reconcile;
work and timed FNV-1a digests reconcile. B/L work is exact after selected-body
identity, all common B/L/H work is equal, and only H has hint/pop-tail activity
and zero forward-positioning steps. All repeatability gates pass (maximum
median ratio 1.0344; maximum required stage-share range 0.00638).

All 36 statistical blocks were independently recomputed from the committed
rows, including exact retained pairing, seeds, 100,000 bootstrap resamples,
percentile interpolation, descriptive statistics, classifications, and
production checks. They exactly match the machine-readable evaluation.

## Evaluator input-contract note

A direct invocation of the frozen evaluator on the Phase 2 root stops before
reading samples because it requires `artifact-hashes.json` to cover the whole
argument directory. The committed root correctly also contains outer
transport/extraction receipts, `returned-evidence-hashes.json`, and
`transfer-cleanup.json`, which are outside the archive index. The frozen
evaluator was left unchanged and run on a temporary byte-identical view of its
123 indexed artifacts plus the archive index. The result was then independently
recomputed against the full committed root. No raw or frozen artifact was
modified.
