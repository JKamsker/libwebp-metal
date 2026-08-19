Times are milliseconds per image. Batch uses a persistent 24-item process; single starts a new `cwebp` process per image. Speedup above `1×` favors CUDA.

| Method | CPU time | CUDA time | Speedup |
|---|---:|---:|---:|
| PNG lossy — batch | 92.8 ms | 40.3 ms | **2.30×** |
| PNG lossy — single | 94.8 ms | 262.1 ms | 0.36× |
| PNG lossless — batch | 142.8 ms | 77.4 ms | **1.84×** |
| PNG lossless — single | 155.2 ms | 304.7 ms | 0.51× |
| PNG near-lossless — batch | 209.8 ms | 77.8 ms | **2.70×** |
| PNG near-lossless — single | 223.2 ms | 308.1 ms | 0.72× |
| JPEG lossy — batch | 92.7 ms | 40.0 ms | **2.32×** |
| JPEG lossy — single | 95.5 ms | 261.4 ms | 0.37× |
| JPEG lossless — batch | 695.4 ms | 127.5 ms | **5.46×** |
| JPEG lossless — single | 699.6 ms | 346.4 ms | **2.02×** |
| JPEG near-lossless — batch | 799.8 ms | 128.3 ms | **6.24×** |
| JPEG near-lossless — single | 809.7 ms | 362.1 ms | **2.24×** |

Bottom line: CUDA helps persistent lossy, lossless, near-lossless batches, and has mixed results when starting a fresh process for each image.
