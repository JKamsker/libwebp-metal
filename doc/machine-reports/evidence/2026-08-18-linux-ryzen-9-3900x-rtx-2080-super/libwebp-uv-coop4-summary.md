# Pre-Ampere cooperative UV transform rejection

Parent: `8ac27efcf21b3ec208e8fea78cbcf2f78b43a05d`

The retained native profile assigned 5.1% of representative photo block
cycles and 252 completion-barrier samples to UV numerical work. One
Turing-only candidate mapped four lanes to each of the 32 UV mode/block
transforms, quantizers, and inverse transforms. Ampere+ retained the scalar
path.

The first build reused `i16_tmp` as `int` scratch without proving alignment.
The field begins at byte offset 5,250 in `MBWork`, so its 32-bit shared
accesses were two-byte misaligned. The kernel failed, Nsight reported
`LaunchFailed`, and transactional CPU fallback preserved exact output. This
diagnostic version is retained as `libwebp-uv-coop4-candidate-*` evidence and
was not treated as candidate performance.

The sole candidate was corrected by declaring `i16_tmp` four-byte aligned.
It then executed successfully and produced the exact profiled WebP SHA-256.
Resources moved from 103 to 102 registers while the 352-byte stack and
23,392-byte shared allocation stayed fixed. The representative launch
improved from 121.79 to 119.26 us, executed instructions rose from 3,879,409
to 3,895,408, `No Eligible` improved from 89.78% to 89.51%, and occupancy
stayed 26.04%. Device timing reduced UV numerical block-cycle share from
5.1% to 3.4%, but photo GPU wall moved only from 26.27 to 26.01 ms.

Five order-balanced process pairs per format produced 60 exact timing rows:

| Format | Control pooled median | Candidate pooled median | Paired-median gain |
|---|---:|---:|---:|
| PNG | 35.271 ms/image | 35.608 ms/image | -0.337 ms/image |
| JPEG | 35.485 ms/image | 35.785 ms/image | -0.200 ms/image |

The aligned candidate and restored builds passed 7/7 focused tests. CPU/CUDA
hashes and byte counts matched for methods 2--6 and qualities 25/75/98 over
six graphic/photo/texture 17x13 and 257x255 fixtures. Twenty injected-fallback
cells also matched across both formats, bands 0/1/3/5/7, and
inline/pipelined token recording.

Both formats regressed, so the candidate was removed. Restored source exactly
matches blob `7809e965a02b2eaec04a0e659239e66c6056c025`; resources returned
to 103 / 352 / 23,392 and 7/7 tests passed. Architecture
thresholds/defaults, Ampere+ behavior, and the frozen corpus/generator are
unchanged.
