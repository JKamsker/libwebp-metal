# Retained bottleneck refresh and I4 flatness-handoff feasibility

- Parent: `50ed9f7dfc9feb13568fba2daa26bdb8b0624105`
- Native benchmark binary SHA-256: `a824960c90fff1cb8fc2105540258cd5485da96b511e50e0d82d5958be0cf6a7`
- Retained CUDA source blobs: `cuda_decimate_enc.cu` `7809e965a02b2eaec04a0e659239e66c6056c025`; `cuda_decimate_dsp.cuh` `c954dbf427a3ac9337b45a3119121dfcd61014f4`
- Generator SHA-256: `6a4271dd036ff96be03188109680554e3d1676862c23553b5dd15474b2aeb007`
- Corpus manifest SHA-256: `4711e88382816a1d1546bde24f044e37c3c6c6f9d5a47b2b3b625f40be8d973b`

The native-sm_75 retained stage build was run over one warmup and three
batch-24 samples of the six small/medium PNG and JPEG inputs. Excluding the
single profiler warmup record, the 95 records per format averaged:

| Format | Total | Decimate | Emit tokens | Write | Import |
|---|---:|---:|---:|---:|---:|
| PNG | 28.786 ms | 19.177 ms | 4.038 ms | 2.230 ms | 1.377 ms |
| JPEG | 28.084 ms | 19.028 ms | 3.836 ms | 1.836 ms | 1.402 ms |

All-thread `perf` captures over six measured batch-24 samples put
`VP8PutTokenPage` first at 24.16% PNG and 25.09% JPEG. They did not expose a
new scheduling target; the direct token-worker lifecycle probe already bounds
setup/synchronization/teardown at 0.747/0.764 ms per image. The raw `strace`
control records 197 `clone3` calls in each batch-24 process and is retained as
corroborating lifecycle evidence, not as an additive wall-time estimate.

The current source correlation still exposes the separate I4 flatness walk.
A possible handoff could count non-DC nonzeros in the existing four-lane
quantizer and remove the later scalar scan. It cannot improve the current
metric critical path on photo or texture: their residual-warp totals are
306/270 million cycles versus 209/145 million for SSE plus flatness. On
graphic-medium, SSE plus flatness is only 1.70% longer than residual
(85.632 versus 84.178 million cycles). Even charging the entire 37.5% I4
phase to that metric interval gives an intentionally impossible bound of
`27.115 ms * 0.375 * 0.01699 = 0.173 ms` for graphic-medium. Charging the
same bound to both graphic inputs yields only 0.058 ms/image over the
six-input corpus.

This is far below the required 1.5 ms/image in both formats before accounting
for the quantizer's additional count/reduction work. No source candidate was
opened. Turing/Ampere+ branches, 784/12,544 versus 64/4,000 defaults, and the
frozen generator/corpus are unchanged.
