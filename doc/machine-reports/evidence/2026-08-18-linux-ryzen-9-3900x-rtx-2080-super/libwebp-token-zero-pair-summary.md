# Coefficient-token zero-pair feasibility rejection

Parent: `792e2592cdbda92f19a22ad3f2c6a4cfd50619bc`

The fresh native stage profile used one warmup and three measured batch-24
method-4/quality-75 file-I/O samples. Full-corpus medians were 34.485 ms/image
PNG and 35.322 JPEG, with exact aggregate hashes/byte counts
`455f70a1e139f043` / 6,441,688 and `0c4b078d5c4d3173` / 6,400,792.
Texture-medium remained the critical host case:

| Format | Total | Decimate/collect/replay | Token emit | Write |
|---|---:|---:|---:|---:|
| PNG | 79.262 ms | 47.572 ms | 15.746 ms | 8.563 ms |
| JPEG | 82.280 ms | 47.192 ms | 18.388 ms | 9.477 ms |

Whole-thread `gprofng` sampling of 72 texture-medium encodes attributed
2.652/5.694 CPU seconds PNG and 2.602/5.964 JPEG to
`VP8RecordCoeffTokens`. A restored-source full-corpus control attributed
0.520 seconds PNG and 0.460 JPEG to that function over 72 encodes, or
7.222 and 6.389 ms/image.

A counter-only probe measured disjoint consecutive-zero packing coverage:

| Workload | Coefficient iterations | Zero iterations | Pair coefficients | Pair share | Maximum store reduction |
|---|---:|---:|---:|---:|---:|
| Full PNG corpus | 38,703,920 | 15,483,240 | 11,365,872 | 29.366% | 14.683% |
| Full JPEG corpus | 39,563,288 | 15,820,760 | 11,392,000 | 28.794% | 14.397% |
| Texture-medium PNG | 135,462,480 | 28,071,120 | 11,211,840 | 8.277% | 4.138% |
| Texture-medium JPEG | 135,479,616 | 28,043,712 | 11,174,592 | 8.248% | 4.124% |

Each pair can remove at most one token store, so the final column is already
an upper bound relative to coefficient iterations; nonzero coefficients emit
multiple tokens, making the fraction of actual token stores smaller. Even the
impossible assumption that pairing deletes the same fraction of the entire
`VP8RecordCoeffTokens` function yields only 1.060 ms/image PNG and 0.920 JPEG
on the full corpus. Real code must retain both statistics updates and add pair
detection plus page-boundary handling.

No representation candidate was implemented. The probe was removed and the
restored native build passed all seven registered focused tests. This is RTX
2080 SUPER-only feasibility evidence; the architecture split, pre-Ampere and
Ampere+ thresholds/defaults, and frozen publication corpus/generator are
unchanged.
