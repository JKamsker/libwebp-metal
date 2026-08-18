# Publication corpus v1

This directory contains only the canonical manifest. The 70.2 MiB of image
bytes are generated on demand and are intentionally not committed:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-publication-corpus --verify
```

The nine opaque P6 PPM inputs cross three formula-defined categories (`photo`,
`graphic`, and `texture`) with dimensions 512x512, 1600x1200, and 3000x2000.
Generator version 1 uses the explicit seed `0x9e3779b9`; every output byte is
derived by integer operations in `scripts/generate_publication_corpus.py`.
`manifest.json` pins the generator-source SHA-256 and records dimensions, byte
counts, and SHA-256 for each file. It is byte-identical at every output
location.

## Provenance and redistribution

The generator contains no embedded or external image media, downloaded input,
model output, or runtime randomness. The generator source, manifest, and the
PPM bytes produced by generator version 1 are distributed under the repository
BSD-3-Clause terms in `COPYING`. There are no identified third-party media
rights to resolve for this corpus.

The category labels describe formulas, not natural-image populations. This
corpus is suitable for deterministic codec correctness and controlled
performance protocols, but it cannot support claims about broad photographic
content generalization by itself.

Run the untimed two-generation verification with:

```sh
python3 scripts/test_publication_corpus.py
```

This corpus reproduces the exact nine generated inputs used by experiment 1.
It does not replace, rename, or retroactively reproduce historical evidence
collected from `mitski.png`, `corgi.jpeg`, or `siamese.jpg`.
