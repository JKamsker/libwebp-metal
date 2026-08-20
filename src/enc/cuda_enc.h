// Copyright 2026
//
// Private CUDA adapter for the backend-neutral encoder accelerator interface.

#ifndef WEBP_ENC_CUDA_ENC_H_
#define WEBP_ENC_CUDA_ENC_H_

#include "src/enc/accelerator_enc.h"
#include "src/webp/types.h"

#ifdef __cplusplus
extern "C" {
#endif

WEBP_EXTERN const WebPEncoderAccelerator* WebPGetCUDAEncoderAccelerator(void);

// Private tool-only handoff for decoded/preprocessed YUV420 that already
// lives on the selected CUDA device. The device planes are copied
// device-to-device into backend-owned tight planes before this function
// returns, so decoder-owned mappings may then be released. host_y/u/v and
// their strides identify the otherwise-unused WebPPicture planes supplied to
// WebPEncode(). The encode is valid only when both lossy analysis and
// decimation subsequently report SUCCESS; callers must discard and CPU-retry
// the whole image otherwise.
WEBP_EXTERN WebPAcceleratorResult WebPCUDARegisterExternalYUV420(
    const void* device_y, size_t device_y_stride, const void* device_u,
    size_t device_u_stride, const void* device_v, size_t device_v_stride,
    const uint8_t* host_y, int host_y_stride, const uint8_t* host_u,
    const uint8_t* host_v, int host_uv_stride, int width, int height,
    uint64_t* device_to_device_bytes);
WEBP_EXTERN void WebPCUDAClearExternalYUV420(void);

#if defined(WEBP_CUDA_ENABLE_LOSSY_DECIMATE)
// Whole-pass lossy macroblock decimation, implemented in
// cuda_decimate_enc.cu with its own device resources.
WebPAcceleratorResult WebPCUDALossyDecimate(
    void* context, const WebPAcceleratorDecimateRequest* request);
// Warms the decimate unit's stream and static tables; called from the
// process-start prewarm thread.
void WebPCUDALossyDecimatePrewarm(void);
WebPAcceleratorResult WebPCUDALossyDecimateFlush(void);
void WebPCUDALossyDecimateEndEncode(void);
void WebPCUDALossyDecimateTrim(void);
WebPAcceleratorResult WebPCUDARegisterDecimateExternalYUV420(
    const uint8_t* device_y, size_t device_y_stride,
    const uint8_t* device_u, const uint8_t* device_v,
    size_t device_uv_stride, const uint8_t* host_y, int host_y_stride,
    const uint8_t* host_u, const uint8_t* host_v, int host_uv_stride,
    int width, int height);
void WebPCUDAClearDecimateExternalYUV420(void);
// Last timing-enabled pass, split at CUDA events around the kernel wavefront
// and result downloads. Returns zero when timing is disabled or unavailable.
WEBP_EXTERN uint64_t WebPCUDAGetLastDecimateExecutionNanoseconds(void);
WEBP_EXTERN uint64_t WebPCUDAGetLastDecimateResultTransferNanoseconds(void);
#endif

// Internal benchmark instrumentation. Stage bits are set only after a CUDA
// callback returns SUCCESS. Reset also clears the resident-handoff counter.
void WebPCUDAResetSuccessfulStages(void);
uint32_t WebPCUDAGetSuccessfulStages(void);
uint64_t WebPCUDAGetResidentLosslessHandoffCount(void);
// True when the selected CUDA device predates Ampere. Tool-only scheduling
// policy uses this query without creating backend streams.
int WebPCUDAIsPreAmpereDevice(void);
// True when the current encode may use the CPU worker-parallel lossless color
// cache search. The default is limited to pre-Ampere CUDA devices with an
// already-successful lossless stage; the environment override is intended for
// matched cross-hardware A/B measurement.
int WebPCUDAParallelCacheSearchEnabled(void);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_CUDA_ENC_H_
