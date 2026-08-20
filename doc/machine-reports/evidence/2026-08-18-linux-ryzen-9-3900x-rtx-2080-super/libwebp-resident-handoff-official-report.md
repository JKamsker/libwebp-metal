Times are milliseconds per image. Batch uses a persistent 24-item process; single starts a new `cwebp` process per image. Speedup above `1×` favors CUDA.

| Method | CPU time | CUDA time | Speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 92.7 ms | 40.5 ms | **2.29×** |
| PNG lossy — single | 95.5 ms | 260.3 ms | 0.37× |
| PNG lossless — batch | 145.0 ms | 78.3 ms | **1.85×** |
| PNG lossless — single | 155.5 ms | 299.4 ms | 0.52× |
| PNG near-lossless — batch | 211.6 ms | 79.5 ms | **2.66×** |
| PNG near-lossless — single | 221.4 ms | 308.5 ms | 0.72× |
| JPEG lossy — batch | 92.9 ms | 40.5 ms | **2.29×** |
| JPEG lossy — single | 95.6 ms | 257.7 ms | 0.37× |
| JPEG lossless — batch | 725.1 ms | 133.5 ms | **5.43×** |
| JPEG lossless — single | 722.5 ms | 348.8 ms | **2.07×** |
| JPEG near-lossless — batch | 853.6 ms | 133.9 ms | **6.38×** |
| JPEG near-lossless — single | 833.3 ms | 364.6 ms | **2.29×** |

Bottom line: CUDA helps persistent lossy, lossless, near-lossless batches, and has mixed results when starting a fresh process for each image.
