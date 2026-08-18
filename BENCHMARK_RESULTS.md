# Modern Metal migration benchmark results

These are historical migration-baseline measurements. The later five-item
experiment series is interpreted in
[doc/experiment-series-analysis-20260817.md](doc/experiment-series-analysis-20260817.md);
it changes the selected lossy kernel without rewriting these recorded numbers.

**Publication quarantine:** the complete-lossless and hash tables, their
file-size/equality statements, and their three named inputs are not part of the
publishable reproducible core. Raw per-trial samples were not retained, and no
source, author, license, or redistribution terms have been identified for
`mitski.png`, `corgi.jpeg`, or `siamese.jpg`. These numbers remain immutable
historical records only. See
[the evidence audit](doc/publication-evidence-audit-20260818.md). The generated
publication corpus must not be substituted into these rows or presented as a
reproduction of them.

Measured on 2026-08-17 on a 14-core Apple M4 Pro MacBook Pro with 24 GB of
memory. macOS reported no thermal or power warnings. The migrated encoder was
built at `-O3` from `v1.6.0-221-g4fe551df` plus the local Metal changes.

The legacy published measurements were taken on an Apple M4 Max, so a direct
old-versus-new M4 Pro comparison is included where the hardware difference is
material.

## Complete lossless encoding

Seven alternating one-shot CLI trials were averaged for each cell. Every Metal
trial used a new process, so lazy shader compilation is included just as it is
in the legacy cumulative table. CPU used `WEBP_METAL=0`; Metal forced the
cross-color path and used the normal hash threshold. `-lossless -exact` was
used throughout.

| Input | Method | Modern CPU | Modern Metal | Modern speedup | Legacy speedup |
|---|---:|---:|---:|---:|---:|
| `mitski.png` | 4 | 0.9571 s | 0.4100 s | **2.334x** | 2.379x |
| `corgi.jpeg` | 4 | 1.6614 s | 0.7943 s | **2.092x** | 2.096x |
| `siamese.jpg` | 4 | 3.1343 s | 1.3629 s | **2.300x** | 2.375x |
| `mitski.png` | 6 | 1.1186 s | 0.4314 s | **2.593x** | 2.163x |
| `corgi.jpeg` | 6 | 2.0300 s | 0.9214 s | **2.203x** | 2.064x |
| `siamese.jpg` | 6 | 3.5357 s | 1.4200 s | **2.490x** | 2.348x |

The complete speedups are in the same range as the legacy implementation.
Method 4 is within roughly 0-3% of the old speedup; method 6 is 6-20% better.
Both modern CPU and Metal absolute times are generally lower than the old M4
Max records, reflecting current libwebp changes as well as run-to-run and
machine differences.

Decoded CPU and Metal benchmark outputs were compared and were pixel-identical.
Metal file-size changes ranged from +0.020% to +0.468%, within the legacy
documented 0.3-0.5% tradeoff.

## Hash-chain candidate search

Five alternating one-shot trials were averaged. Both sides used the Metal
cross-color transform; only `WEBP_METAL_HASH` changed. CPU and Metal hash files
were byte-identical in every case.

| Input | Method | CPU hash | Metal hash | Modern speedup | Legacy speedup |
|---|---:|---:|---:|---:|---:|
| `mitski.png` | 4 | 0.5780 s | 0.4160 s | **1.389x** | 1.412x |
| `corgi.jpeg` | 4 | 1.3000 s | 0.8000 s | **1.625x** | 1.610x |
| `siamese.jpg` | 4 | 2.4120 s | 1.3720 s | **1.758x** | 1.756x |
| `mitski.png` | 6 | 0.6000 s | 0.4360 s | **1.376x** | 1.295x |
| `corgi.jpeg` | 6 | 1.4260 s | 0.9300 s | **1.533x** | 1.454x |
| `siamese.jpg` | 6 | 2.4480 s | 1.4160 s | **1.729x** | 1.624x |

The method-4 results effectively reproduce the old values. Method 6 is
consistently slightly better in the modern tree.

## Warmed RGB-to-YUV import

Each process performed one unmeasured warm-up before 50 imports at 6 MP or 30
imports at 12 MP. The table uses the median of three processes.

| Input | Modern CPU | Modern Metal | Modern speedup | Legacy M4 Max record |
|---|---:|---:|---:|---:|
| 3000x2000 (6 MP) | 5.258 ms | 1.874 ms | **2.806x** | 4.55x |
| 4000x3000 (12 MP) | 10.569 ms | 3.750 ms | **2.818x** | 4.95x |

The M4 Pro does not reproduce the M4 Max's 4.5-5x warmed-import headline.
However, rebuilding the legacy WebP-Metal tree and running it on this same M4
Pro produced 2.740x at 6 MP and 2.854x at 12 MP. The migrated implementation is
therefore equivalent to the old implementation on identical hardware; the gap
to the published record is a machine difference rather than a migration
regression.

## Conclusion

The modern port preserves the accelerator's performance profile. Complete
lossless and hash-chain gains are in the same ballpark as, and often slightly
better than, the legacy records. Warmed lossy import is also unchanged in a
same-machine comparison, although the M4 Pro's measured speedup is lower than
the published M4 Max result.
