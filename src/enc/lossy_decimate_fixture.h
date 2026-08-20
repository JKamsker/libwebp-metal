// Copyright 2026
//
// Private portable fixture support for the lossy-decimate accelerator stage.

#ifndef WEBP_ENC_LOSSY_DECIMATE_FIXTURE_H_
#define WEBP_ENC_LOSSY_DECIMATE_FIXTURE_H_

#include <stddef.h>
#include <stdint.h>

#include "src/enc/accelerator_enc.h"
#include "src/webp/types.h"

#ifdef __cplusplus
extern "C" {
#endif

#define WEBP_DECIMATE_FIXTURE_SCHEMA_VERSION 1u

typedef struct {
  WebPAcceleratorDecimateRequest request;
  WebPAcceleratorDecimateResult* golden_results;
  uint8_t* golden_recon_y;
  uint8_t* golden_recon_u;
  uint8_t* golden_recon_v;
} WebPDecimateFixture;

// Loads or writes the endian-stable WPDCRD fixture format. The fixture owns
// every pointer reachable from request after a successful load/copy.
WEBP_EXTERN int WebPDecimateFixtureLoad(const char* path,
                                        WebPDecimateFixture* fixture,
                                        char* error, size_t error_size);
WEBP_EXTERN int WebPDecimateFixtureWrite(
    const char* path, const WebPDecimateFixture* fixture, char* error,
    size_t error_size);
WEBP_EXTERN void WebPDecimateFixtureClear(WebPDecimateFixture* fixture);

// CPU-golden capture hooks used by frame_enc.c. Conformance builds enable
// them; ordinary library builds compile the inline no-ops below away.
#if defined(WEBP_DECIMATE_FIXTURE_CAPTURE)
void WebPDecimateFixtureCaptureBegin(
    const WebPAcceleratorDecimateRequest* request);
void WebPDecimateFixtureCaptureResetDecision(void);
void WebPDecimateFixtureCaptureNoteMaxDelta(int max_delta);
int WebPDecimateFixtureCaptureTakeMaxDelta(uint16_t* max_delta);
void WebPDecimateFixtureCaptureRecord(
    int mb_index, const WebPAcceleratorDecimateResult* result,
    const uint8_t* recon_y, const uint8_t* recon_u, const uint8_t* recon_v,
    int recon_stride);
void WebPDecimateFixtureCaptureFinish(int success);
#else
static inline void WebPDecimateFixtureCaptureBegin(
    const WebPAcceleratorDecimateRequest* request) {
  (void)request;
}
static inline void WebPDecimateFixtureCaptureResetDecision(void) {}
static inline void WebPDecimateFixtureCaptureNoteMaxDelta(int max_delta) {
  (void)max_delta;
}
static inline int WebPDecimateFixtureCaptureTakeMaxDelta(
    uint16_t* max_delta) {
  (void)max_delta;
  return 0;
}
static inline void WebPDecimateFixtureCaptureRecord(
    int mb_index, const WebPAcceleratorDecimateResult* result,
    const uint8_t* recon_y, const uint8_t* recon_u, const uint8_t* recon_v,
    int recon_stride) {
  (void)mb_index;
  (void)result;
  (void)recon_y;
  (void)recon_u;
  (void)recon_v;
  (void)recon_stride;
}
static inline void WebPDecimateFixtureCaptureFinish(int success) {
  (void)success;
}
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_LOSSY_DECIMATE_FIXTURE_H_
