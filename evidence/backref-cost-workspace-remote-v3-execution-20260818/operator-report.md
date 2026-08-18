# Remote backref-cost workspace remote v3 execution refusal

Status: **REFUSED ON EVIDENCE-RETURN INTEGRITY**

Frozen protocol commit: `9617a720a882bef739caca019a76e45d8a9b17e6`

Remote host: `pandocs-agent`

Invocation: exactly once with `WEBP_BENCHMARK_SESSION=exclusive`

The frozen driver reached evidence retrieval, verified the returned archive
hash before extraction, and then stopped because its immutable safe extractor
reported `unsafe returned archive member`. The frozen output directory was not
created; this refusal directory was created only afterward. No alternate
extraction or rerun was attempted, and no raw A/B record, correctness record,
host-state record, lease record, or evaluation was treated as available.

Committed evidence counts are zero: 0 command processes, 0 raw sample rows,
0 retained samples, 0 warmups, 0 correctness cells, and 0 evaluation cells.
The actual remote matrix counts are not asserted because the remote evidence
was not returned intact. The operator lease record and exact-child cleanup
receipt were not returned; the frozen driver cleanup path ran after the
extractor failure, and a read-only check found no child in the canonical v3
safe root. Runner services/directories and host settings were not touched. No
performance decision or production consequence is recorded.
