Times are milliseconds per image. Batch uses a persistent 24-item process; single starts a new `cwebp` process per image. Speedup above `1×` favors CUDA.

| Method | CPU time | CUDA time | Speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 91.6 ms | 28.3 ms | **3.24×** |
| PNG lossy — single | 93.3 ms | 256.4 ms | 0.36× |
| PNG lossless — batch | 140.6 ms | 76.7 ms | **1.83×** |
| PNG lossless — single | 150.3 ms | 296.2 ms | 0.51× |
| PNG near-lossless — batch | 202.7 ms | 76.9 ms | **2.64×** |
| PNG near-lossless — single | 215.2 ms | 305.2 ms | 0.71× |
| JPEG lossy — batch | 89.3 ms | 29.4 ms | **3.04×** |
| JPEG lossy — single | 93.6 ms | 260.6 ms | 0.36× |
| JPEG lossless — batch | 675.0 ms | 124.8 ms | **5.41×** |
| JPEG lossless — single | 674.6 ms | 339.7 ms | **1.99×** |
| JPEG near-lossless — batch | 785.8 ms | 125.3 ms | **6.27×** |
| JPEG near-lossless — single | 790.9 ms | 352.1 ms | **2.25×** |

Bottom line: CUDA helps persistent lossy, lossless, near-lossless batches, and has mixed results when starting a fresh process for each image.
