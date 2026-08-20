# Repeated-workload output-write bound

The retained native-sm_75 batch executable profiled 24-image forced-CUDA
lossy batches at method 4 / quality 75 with one warmup and three retained
samples over the frozen six-image PNG and JPEG sets.

PNG accumulated 1.271 seconds of sampled CPU time and JPEG 1.251 seconds.
`VP8EncWrite` was only 0.010 seconds inclusive in each profile (0.79% and
0.80%); `WebPMemoryWrite` had no exclusive samples. The cold single-image
`cwebp` write-stage values therefore do not identify a gate-sized repeated
batch bottleneck, and no output-allocation or partition-copy candidate was
created.
