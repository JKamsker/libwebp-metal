// Copyright 2026
//
// Private CUDA adapter for the backend-neutral encoder accelerator interface.

#ifndef WEBP_ENC_CUDA_ENC_H_
#define WEBP_ENC_CUDA_ENC_H_

#include "src/enc/accelerator_enc.h"

#ifdef __cplusplus
extern "C" {
#endif

const WebPEncoderAccelerator* WebPGetCUDAEncoderAccelerator(void);

// Internal benchmark instrumentation. Stage bits are set only after a CUDA
// callback returns SUCCESS. Reset also clears the resident-handoff counter.
void WebPCUDAResetSuccessfulStages(void);
uint32_t WebPCUDAGetSuccessfulStages(void);
uint64_t WebPCUDAGetResidentLosslessHandoffCount(void);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_CUDA_ENC_H_
