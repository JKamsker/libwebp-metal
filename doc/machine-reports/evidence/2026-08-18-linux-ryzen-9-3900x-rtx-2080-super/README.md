# RTX 2080 SUPER benchmark evidence

This directory contains the raw artifacts cited by the corresponding machine
report. `SHA256SUMS` covers every evidence file other than itself.

The JSON and JSONL files are direct benchmark outputs. The TSV files contain
the variant/format prefix followed by each benchmark's JSON output. The
`gprof-i4-diagonal-replay.tar.gz` archive contains the original `gprofng`
experiment directory. `gprof-current-token-profile.tar.gz` contains the later
retained-head texture-batch profile that attributed 60.10% of samples to
`VP8PutTokenPage` and 36.26% to `VP8RecordCoeffTokens`. Inspect them with:

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
