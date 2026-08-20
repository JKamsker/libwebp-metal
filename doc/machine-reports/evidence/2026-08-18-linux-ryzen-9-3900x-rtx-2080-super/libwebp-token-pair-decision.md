# Packed adaptive token/stat pair rejection

Base: `cca895f5a52ebfb6935b5d913592408665b3ef44`

The immediately preceding whole-process gprofng profiles put
`VP8RecordCoeffTokens` at 56.92% of PNG and 57.79% of JPEG exclusive CPU
samples. Its annotated x86-64 instructions showed the packed-token stores and
adjacent adaptive-statistics read/modify/write sites as the largest sampled
clusters. Existing coverage counted 117,400,812 coefficient iterations, with
60.0% nonzero and only 4,596 statistics renormalizations among 362,698,740
recorded events.

The candidate paired the two adaptive decisions every nonzero coefficient
must record (`v != 0` and `v > 1`). When at least two page slots remained it
used one 32-bit token store and one 64-bit adjacent-statistics load/store;
the original scalar helpers handled page boundaries. Generated x86-64 code
contained the intended 32/64-bit operations, but `VP8RecordCoeffTokens` grew
from `0x1370` (4,976) to `0x14e2` (5,346) bytes because of the fallback and
altered zero path.

The native-sm_75 candidate passed `cuda_concurrency_test`,
`cuda_trellis_test`, and `cuda_near_lossless_test`. Two order-reversed process
pairs per format, with one warmup and three retained batch-24 samples, were
exact in all 24 rows:

| Format | Parent | Packed pair | Gain | Hash / bytes |
|---|---:|---:|---:|---|
| PNG lossy | 41.012 ms/image | 43.978 ms/image | -2.966 ms/image | `ace64e860de89b43` / 6,441,688 |
| JPEG lossy | 40.519 ms/image | 41.443 ms/image | -0.924 ms/image | `1cbb84d2ab926db3` / 6,400,792 |

The candidate was restored immediately. The wider code and common-path
branch layout outweighed the paired memory operations. Parent and candidate
benchmark SHA-256 values were respectively
`efd7a286bcc673528854f73d9c3dcb05ed263acde9e4eecc4d101cec07454f14`
and
`537277a18eb5fa7399f462254bca12d32cdbf0b7927a50f195127199d07ac54b`.

The profile archives are the checksum-verifiable `libwebp-token-ipo-profile-*`
files from the immediately preceding experiment. This result is native-sm_75
only and changes no Ampere+ behavior, threshold, or claim.
