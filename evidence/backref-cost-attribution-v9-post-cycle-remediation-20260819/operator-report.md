# Backref cost attribution V9 — post-cycle CI remediation

PR #31's `Research experiment guards` job exposed a mismatch between the
frozen V9 implementation and its local ownership fixture. The fixture expected
an optional `/usr/bin/python3` path record to classify successfully, but the
frozen implementation can reject that record as noncanonical with
`FrameRefusal: resolved executable path is not
absolute/canonical/provenanced`.

This remediation changes only the fixture and adds this provenance record. The
fixture now deterministically asserts the frozen fail-closed rejection. V9's
implementation and interpretation are unchanged: the recorded process-identity
defect remains blocked, and its semantic correction belongs to a future V10
under fresh gates.

The fixture is a manifest-frozen artifact. Changing it intentionally
supersedes and invalidates V9's frozen artifact-hash set; the manifest and the
REFUSED Phase-1B envelope are not re-frozen. Consequently this post-cycle
change cannot create V9 execution authority. Timed execution remains false,
Phase-2 authority remains `NONE`, the interval family remains unassessed, and
there is no production consequence.

All pre-existing Phase-1, Phase-2, and Phase-3 evidence is preserved
byte-for-byte. This local remediation performed no remote contact, lease
operation, process inspection or signal, cleanup, encoder/profiler/benchmark/
sanitizer/timed workload, or host/runner/service/power/auth/toolchain change.
V1–V8 guards, default-off and isolation coverage, and discovered-PID signal
exclusion remain intact.
