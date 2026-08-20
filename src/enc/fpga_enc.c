// Copyright 2026
//
// This is deliberately a transport-free skeleton. It proves that an FPGA
// implementation can advertise the coarse lossy-decimate stage and decline
// transactionally without introducing vendor headers or runtime libraries.

#include "src/enc/fpga_enc.h"

static WebPAcceleratorResult FPGALossyDecimate(
    void* context, const WebPAcceleratorDecimateRequest* request) {
  (void)context;
  (void)request;
  return WEBP_ACCELERATOR_NOT_RUN;
}

static const WebPEncoderAccelerator kFPGAEncoderAccelerator = {
    WEBP_ENCODER_ACCELERATOR_ABI_VERSION,
    sizeof(WebPEncoderAccelerator),
    "fpga",
    WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE,
    WEBP_ACCELERATOR_PROPERTY_SYNCHRONOUS |
        WEBP_ACCELERATOR_PROPERTY_TRANSACTIONAL_OUTPUT |
        WEBP_ACCELERATOR_PROPERTY_DETERMINISTIC,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    FPGALossyDecimate,
    NULL,
    NULL,
    NULL};

const WebPEncoderAccelerator* WebPGetFPGAEncoderAccelerator(void) {
  return &kFPGAEncoderAccelerator;
}
