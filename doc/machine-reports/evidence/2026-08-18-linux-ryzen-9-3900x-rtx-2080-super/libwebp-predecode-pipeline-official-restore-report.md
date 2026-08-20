Times are milliseconds per image. Batch uses a persistent 24-item process; single starts a new `cwebp` process per image. Speedup above `1×` favors CUDA.

| Method | CPU time | CUDA time | Speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 90.2 ms | 39.6 ms | **2.28×** |
| PNG lossy — single | 92.7 ms | 259.8 ms | 0.36× |
| PNG lossless — batch | 139.6 ms | 76.6 ms | **1.82×** |
| PNG lossless — single | 151.8 ms | 297.2 ms | 0.51× |
| PNG near-lossless — batch | 204.9 ms | 77.3 ms | **2.65×** |
| PNG near-lossless — single | 215.1 ms | 306.3 ms | 0.70× |
| JPEG lossy — batch | 92.2 ms | 39.6 ms | **2.33×** |
| JPEG lossy — single | 93.6 ms | 264.8 ms | 0.35× |
| JPEG lossless — batch | 672.1 ms | 124.6 ms | **5.39×** |
| JPEG lossless — single | 684.5 ms | 342.4 ms | **2.00×** |
| JPEG near-lossless — batch | 792.2 ms | 124.9 ms | **6.34×** |
| JPEG near-lossless — single | 790.4 ms | 354.9 ms | **2.23×** |

Bottom line: CUDA helps persistent lossy, lossless, near-lossless batches, and has mixed results when starting a fresh process for each image.
