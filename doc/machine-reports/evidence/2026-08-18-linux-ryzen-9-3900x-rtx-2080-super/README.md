# RTX 2080 SUPER benchmark evidence

This directory contains the raw artifacts cited by the corresponding machine
report. `SHA256SUMS` covers every evidence file other than itself.

The JSON and JSONL files are direct benchmark outputs. The TSV files contain
the variant/format prefix followed by each benchmark's JSON output. The
`gprof-i4-diagonal-replay.tar.gz` archive contains the original `gprofng`
experiment directory; inspect it with:

```sh
mkdir -p /tmp/libwebp-profile-check
tar -xzf gprof-i4-diagonal-replay.tar.gz -C /tmp/libwebp-profile-check
gprofng display text -functions \
  /tmp/libwebp-profile-check/libwebp-gprof-i4-diagonal-replay.er
```

Verify the copied artifacts from this directory with:

```sh
sha256sum -c SHA256SUMS
```
