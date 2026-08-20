// Copyright 2026
// Experimental dependency-free FPGA accelerator skeleton.

#ifndef WEBP_ENC_FPGA_ENC_H_
#define WEBP_ENC_FPGA_ENC_H_

#include "src/enc/accelerator_enc.h"
#include "src/webp/types.h"

#ifdef __cplusplus
extern "C" {
#endif

WEBP_EXTERN const WebPEncoderAccelerator* WebPGetFPGAEncoderAccelerator(void);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_FPGA_ENC_H_
