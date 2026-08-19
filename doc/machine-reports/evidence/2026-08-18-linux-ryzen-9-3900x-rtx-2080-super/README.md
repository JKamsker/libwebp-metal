# RTX 2080 SUPER benchmark evidence

This directory contains the raw artifacts cited by the corresponding machine
report. `SHA256SUMS` covers every evidence file other than itself.

The JSON and JSONL files are direct benchmark outputs. The TSV files contain
the variant/format prefix followed by each benchmark's JSON output. The
`gprof-i4-diagonal-replay.tar.gz` archive contains the original `gprofng`
experiment directory. `gprof-current-token-profile.tar.gz` contains the later
retained-head texture-batch profile that attributed 60.10% of samples to
`VP8PutTokenPage` and 36.26% to `VP8RecordCoeffTokens`.

`chroma-i16-overlap-ab.jsonl` contains all 60 native-sm_75 A/B timing records
for the rejected scheduling candidate. The six
`retained-lossy-stage-*.jsonl` files contain the raw guarded wall-stage records
and batch-harness output: 24 warmup plus 72 measured encodes for each of
graphic, photo, and texture.

`i4-i16-chroma-overlap-ab.jsonl` contains the 60-record full composition
screen. `i4-chroma-overlap-ab.jsonl` contains both five-process blocks for the
lean composition (120 records total), including the borderline repeat used
for its decision.

`i4-chroma-token-fallthrough-screen.jsonl` contains the 24-record screen that
showed the CPU probability layout did not compose with the lean GPU candidate.

`i4-balanced-chroma-overlap-ab-block1.jsonl` and
`i4-balanced-chroma-overlap-ab-block2.jsonl` contain the two independent
60-record timing blocks for the rejected balanced-four-warp I4/chroma
composition. `i4-balanced-chroma-overlap-parity.jsonl` contains the 105
per-case CPU/CUDA and band-3 fallback SHA-256 comparisons; every row is exact.

`i4-team-barrier-chroma-screen.jsonl` contains the 24 exact timing rows for
the rejected team-local I4 barrier plus chroma-overlap composition.

`i4-boundary-static-commit-screen.jsonl` contains the 24 exact timing rows for
the rejected boundary-gather, static-dispatch, and parallel-commit composition.

`i4-warp-argmin-static-screen.jsonl` contains the 24 exact timing rows for the
rejected warp-argmin/static-dispatch/parallel-commit composition.
`retained-phase-refresh.txt` is the raw native-sm_75 phase trace used to select
that experiment.

`partition0-token-overlap-screen.jsonl` contains the 24 exact timing rows for
the rejected host-side schedule that generated VP8 partition 0 while all eight
token partitions emitted on worker threads. The `parent` rows set
`WEBP_PARTITION0_PIPELINE=0`; candidate and parent rows came from the same
native-sm_75 binary.

Inspect the sampling archives with:

```sh
mkdir -p /tmp/libwebp-profile-check
tar -xzf gprof-i4-diagonal-replay.tar.gz -C /tmp/libwebp-profile-check
gprofng display text -functions \
  /tmp/libwebp-profile-check/libwebp-gprof-i4-diagonal-replay.er
tar -xzf gprof-current-token-profile.tar.gz -C /tmp/libwebp-profile-check
gprofng display text -functions \
  /tmp/libwebp-profile-check/current.er
```

Verify the copied artifacts from this directory with:

```sh
sha256sum -c SHA256SUMS
```
