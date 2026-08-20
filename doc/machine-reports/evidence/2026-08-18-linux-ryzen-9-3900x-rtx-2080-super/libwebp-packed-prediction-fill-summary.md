# Pre-Ampere packed whole-macroblock prediction-fill rejection

Parent: `68c4406994d4a6f126d9882e8e1b7f41ba9c4710`

The native Release build used `-DCMAKE_CUDA_ARCHITECTURES=native`. A fresh
root Nsight Compute profile measured the representative 50-CTA photo launch
at 121.79 us, 3,879,409 instructions, 89.78% `No Eligible`, and 26.04%
achieved occupancy. Source correlation assigned 136,965 instructions and 186
barrier-stall samples to the retained parallel I16/UV prediction-plane fill.

One pre-Ampere candidate generated four adjacent DC, true-motion, vertical,
or horizontal pixels per lane and published them with an aligned `uchar4`
shared store. Ampere+ compiled the original scalar-per-pixel loop. Registers,
stack, and shared memory remained 103 / 352 / 23,392 bytes. Instructions fell
by 42,070 to 3,837,339, but duration stayed flat at 121.86 us and `No
Eligible` worsened to 89.90%. The profiled WebP SHA-256 was exact.

Five order-balanced process pairs per format produced 60 exact timing rows:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 35.470 ms/image | 35.190 ms/image | +0.544 ms/image |
| JPEG | 35.602 ms/image | 36.193 ms/image | -0.080 ms/image |

The candidate passed 7/7 focused tests. CPU/CUDA hashes and bytes matched for
methods 2--6 and qualities 25/75/98 over six tiny/odd fixtures, and for 20
forced-fallback cells across both formats, bands 0/1/3/5/7, and inline versus
pipelined token recording.

PNG missed the 1.5 ms/image gate and JPEG regressed, so the candidate was
removed. Restored source matched the parent blob exactly, retained resources
returned, and the rebuilt focused suite passed 7/7 tests. Architecture
thresholds, Ampere+ behavior, and the frozen corpus/generator are unchanged.
