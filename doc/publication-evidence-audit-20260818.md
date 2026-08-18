# Publication evidence and corpus audit (2026-08-18)

This audit separates the publishable, reproducible research core from retained
historical evidence whose inputs have unresolved provenance. It does not alter
any raw artifact, experiment result, codec behavior, threshold, API, or ABI.

The later predictor-boundary and exact-backref diagnostic attempts produced no
timed observations: both stopped in a Darwin free-memory preflight before lease
acquisition. They support no publication performance claim. Their evidence and
limitations are audited in
[next-boundary-experiment-evaluation-20260818.md](next-boundary-experiment-evaluation-20260818.md).

## Evidence policy

Publication-core claims must have committed raw evidence and inputs that are
either generated deterministically from repository source or available with
documented redistribution rights. A hash proves byte identity, not authorship
or permission. Results involving an unavailable external input remain useful
historical records, but are not publication-core support and cannot be
reproduced by substituting a similarly named file.

| Claim group | Input and raw-evidence audit | Publication treatment |
|---|---|---|
| Experiment 1 stage profile, its warm CPU/Metal ratios, and its 18-cell output validation | Nine formula-generated PPMs; committed manifest, hashes, records, and validation | **Retained.** Exact input bytes are publication corpus v1. |
| Experiment 2 crossover observations and the decision not to change thresholds | Runner-generated inputs with fixed seeds 101/303; committed raw rows and validity record | **Retained.** Synthetic/content-local and one-device limits remain. |
| Experiment 3 import/batch observations and the decision not to promote a batch ABI | C harness generates the 3000x2000 RGB input; committed raw rows and validation | **Retained.** |
| Experiment 4 warmed lossy-import candidates, including the exact 2x2 6/6 result | C harness generates the 6 MP and 12 MP bytes; committed raw rows, checksums, summary, and validation | **Retained.** This is the evidence supporting the promoted 2x2 specialization. |
| Experiment 4 transform/hash candidates and external-image correctness loops | Depends on the three unavailable files below; raw timing artifacts are committed | **Removed from the publication core; retained as a historical appendix.** No optimization conclusion is published from these rows. |
| Experiment 5 standalone predictor timing and external-image correctness | Depends on the three unavailable files below; raw CSV and validation are committed | **Removed from the publication core; retained as historical evidence.** Its existing default-off implementation disposition is unchanged, but the six-stratum result is not a reproducible publication claim. |
| `BENCHMARK_RESULTS.md` complete-lossless/hash tables and file-size/equality statements | Depends on the three unavailable files and lacks raw per-trial samples | **Quarantined as recorded-only history.** Not used by the publication core. |
| Architecture, private API/ABI, build gates, defaults, and source-level fallback contracts | Established by repository source and untimed tests; not corpus-dependent | **Retained**, with device/runtime behavior limited to the executed tests. |

The unresolved external identities are:

| Historical input | Recorded SHA-256 | Rights status |
|---|---|---|
| `mitski.png` | `4dc95f6926a01f4c6ab32ac0559d8a4c3db1722bd26bde96efeff685ca7fdab0` | No source URL, author, license, or redistribution terms identified. |
| `corgi.jpeg` | `7991a0293e31ae253247be6e1fe3b9df1bf106c0ea4ec536bba40b5c7d0fd8d0` | No source URL, author, license, or redistribution terms identified. |
| `siamese.jpg` | `5c449f30fb52754c83c5aca1c10716bb7fbae9bfdac1c057da491d6174713c8e` | No source URL, author, license, or redistribution terms identified. |

Nothing in this audit infers a license for those files. Their names and hashes
are retained solely to identify the historical bytes.

## Publication corpus v1

`benchmarks/publication-corpus/manifest.json` defines nine on-demand opaque P6
PPMs. It crosses `photo`, `graphic`, and `texture` formulas with 512x512,
1600x1200, and 3000x2000 dimensions. Generator version 1 and seed
`0x9e3779b9` are explicit; the portable manifest records every file's dimensions,
byte count, and SHA-256, plus the generator source SHA-256. The generator
embeds no media and uses no network, model, clock, platform random source, or
Python random implementation.

The generator source, canonical manifest, and generated PPM bytes are
distributed under the BSD-3-Clause terms in `COPYING`. These exact bytes match
experiment 1's nine image hashes. They do not retroactively replace any
external-image experiment.

Generate and verify without taking a benchmark lease:

```sh
python3 scripts/generate_publication_corpus.py \
  --output /tmp/libwebp-publication-corpus --verify
python3 scripts/test_publication_corpus.py
```

The first command validates schema metadata, provenance/license fields,
dimensions, byte counts, and hashes. The second generates the corpus twice and
requires byte-for-byte and manifest equality.

## Timing decision

No new timed follow-up is required to publish the bounded core. Experiments
1--3 and experiment 4's lossy-import suite already support the retained claims
with deterministic generated inputs. Removing the external-dependent
experiment 4 transform/hash and experiment 5 results narrows the report rather
than creating a replacement claim.

Accordingly, this work adds no experiment build flag, runtime flag, timing
entry point, or reuse of the item 1--5 gates. Any future attempt to make a new
natural-image performance claim is a new experiment: it must define its corpus
and protocol in advance and receive independent default-off build/runtime gates
and the exclusive benchmark-session refusal required by project policy.

## Historical-artifact boundary

All committed raw JSONL/CSV, manifests, operator reports, summaries,
validations, and `benchmarks/metal/recorded_baseline.tsv` are preserved byte for
byte. Documentation labels them; it does not rewrite, delete, or reinterpret
their recorded input identities.
