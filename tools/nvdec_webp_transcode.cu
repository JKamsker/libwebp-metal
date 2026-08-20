// Copyright 2026
//
// Opt-in NVDEC VP8/WebP -> CUDA lossy WebP transcoder. This private tool keeps
// decoded pixels on the device and transactionally retries the complete image
// through the CPU path whenever eligibility, decode, handoff, or required
// encoder-stage checks fail.

#include <cuda.h>
#include <cuda_runtime.h>
#include <nvcuvid.h>

#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#else
#include <time.h>
#include <unistd.h>
#endif

#include <algorithm>
#include <fstream>
#include <limits>
#include <string>
#include <vector>

#include "src/enc/cuda_enc.h"
#include "src/webp/decode.h"
#include "src/webp/encode.h"
#include "src/webp/mux.h"
#include "tools/cuda_transcode_common.h"

namespace {

struct Options {
  const char* input = nullptr;
  const char* output = nullptr;
  const char* backend = "auto";
  int device = 0;
  int method = 4;
  int quality = 75;
  int warmups = 0;
  int samples = 1;
  bool verify = false;
};

struct Encoded {
  uint8_t* bytes = nullptr;
  size_t size = 0;
};

struct Timing {
  uint64_t parse_ns = 0;
  uint64_t decode_ns = 0;
  uint64_t handoff_ns = 0;
  uint64_t encode_ns = 0;
  uint64_t metadata_ns = 0;
  uint64_t total_ns = 0;
  uint64_t device_to_device_bytes = 0;
};

uint64_t NowNs() {
#if defined(_WIN32)
  static LARGE_INTEGER frequency = {};
  LARGE_INTEGER counter;
  if (frequency.QuadPart == 0) QueryPerformanceFrequency(&frequency);
  QueryPerformanceCounter(&counter);
  return frequency.QuadPart > 0
             ? (uint64_t)((1000000000.0 * counter.QuadPart) /
                          frequency.QuadPart)
             : 0;
#else
  struct timespec value;
  return clock_gettime(CLOCK_MONOTONIC, &value) == 0
             ? (uint64_t)value.tv_sec * UINT64_C(1000000000) + value.tv_nsec
             : 0;
#endif
}

bool ParseInt(const char* text, int minimum, int maximum, int* value) {
  char* end = nullptr;
  long parsed;
  errno = 0;
  parsed = strtol(text, &end, 10);
  if (errno != 0 || text == end || *end != '\0' || parsed < minimum ||
      parsed > maximum) {
    return false;
  }
  *value = (int)parsed;
  return true;
}

void Usage(const char* program) {
  fprintf(stderr,
          "Usage: %s [--backend auto|nvdec|cpu] [--device N] "
          "[--method 0..6] [--quality 0..100] [--warmups N] "
          "[--samples N] [--verify] INPUT OUTPUT\n",
          program);
}

bool ParseOptions(int argc, char** argv, Options* options) {
  std::vector<const char*> positional;
  for (int i = 1; i < argc; ++i) {
    const char* flag = argv[i];
    if (!strcmp(flag, "--verify")) {
      options->verify = true;
    } else if (flag[0] != '-') {
      positional.push_back(flag);
    } else {
      const char* value = ++i < argc ? argv[i] : nullptr;
      if (value == nullptr) return false;
      if (!strcmp(flag, "--backend")) {
        if (strcmp(value, "auto") && strcmp(value, "nvdec") &&
            strcmp(value, "cpu")) {
          return false;
        }
        options->backend = value;
      } else if (!strcmp(flag, "--device")) {
        if (!ParseInt(value, 0, 1024, &options->device)) return false;
      } else if (!strcmp(flag, "--method")) {
        if (!ParseInt(value, 0, 6, &options->method)) return false;
      } else if (!strcmp(flag, "--quality")) {
        if (!ParseInt(value, 0, 100, &options->quality)) return false;
      } else if (!strcmp(flag, "--warmups")) {
        if (!ParseInt(value, 0, 10000, &options->warmups)) return false;
      } else if (!strcmp(flag, "--samples")) {
        if (!ParseInt(value, 1, 10000, &options->samples)) return false;
      } else {
        return false;
      }
    }
  }
  if (positional.size() != 2u) return false;
  options->input = positional[0];
  options->output = positional[1];
  return true;
}

bool ReadFile(const char* path, std::vector<uint8_t>* data) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) return false;
  const std::streamoff size = input.tellg();
  if (size < 0 || (uint64_t)size > std::numeric_limits<size_t>::max()) {
    return false;
  }
  data->resize((size_t)size);
  input.seekg(0);
  return data->empty() ||
         (input.read(reinterpret_cast<char*>(data->data()), size) && input);
}

bool WriteFileAtomically(const char* path, const uint8_t* data, size_t size) {
  const std::string temporary = std::string(path) + ".tmp";
  FILE* output = fopen(temporary.c_str(), "wb");
  bool ok = output != nullptr;
  if (ok && size != 0) ok = fwrite(data, 1, size, output) == size;
  if (output != nullptr && fclose(output) != 0) ok = false;
  if (!ok) {
    (void)remove(temporary.c_str());
    return false;
  }
#if defined(_WIN32)
  if (!MoveFileExA(temporary.c_str(), path,
                   MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
    (void)remove(temporary.c_str());
    return false;
  }
#else
  if (rename(temporary.c_str(), path) != 0) {
    (void)remove(temporary.c_str());
    return false;
  }
#endif
  return true;
}

bool SetEnvironment(const char* name, const char* value) {
#if defined(_WIN32)
  return _putenv_s(name, value) == 0;
#else
  return setenv(name, value, 1) == 0;
#endif
}

bool ConfigureBackend(bool cuda, int device) {
  char device_text[32];
  snprintf(device_text, sizeof(device_text), "%d", device);
  return SetEnvironment("WEBP_ACCELERATOR", cuda ? "cuda" : "none") &&
         SetEnvironment("WEBP_CUDA", cuda ? "1" : "0") &&
         SetEnvironment("WEBP_CUDA_DEVICE", device_text) &&
         SetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS", "1") &&
         SetEnvironment("WEBP_CUDA_LOSSY_ANALYSIS_MIN_MACROBLOCKS", "0") &&
         SetEnvironment("WEBP_CUDA_LOSSY_DECIMATE", "1") &&
         SetEnvironment("WEBP_CUDA_LOSSY_DECIMATE_MIN_MBS", "0");
}

bool InitConfig(const Options& options, WebPConfig* config) {
  if (!WebPConfigInit(config)) return false;
  config->lossless = 0;
  config->method = options.method;
  config->quality = (float)options.quality;
  config->exact = 1;
  return WebPValidateConfig(config) != 0;
}

bool TakeWriter(WebPMemoryWriter* writer, Encoded* encoded) {
  encoded->bytes = writer->mem;
  encoded->size = writer->size;
  writer->mem = nullptr;
  writer->size = 0;
  writer->max_size = 0;
  return true;
}

bool EncodePicture(const Options& options, WebPPicture* picture,
                   Encoded* encoded) {
  WebPConfig config;
  WebPMemoryWriter writer;
  if (!InitConfig(options, &config)) return false;
  WebPMemoryWriterInit(&writer);
  picture->writer = WebPMemoryWrite;
  picture->custom_ptr = &writer;
  if (!WebPEncode(&config, picture)) {
    WebPMemoryWriterClear(&writer);
    return false;
  }
  return TakeWriter(&writer, encoded);
}

bool EncodeCPU(const Options& options, const uint8_t* data, size_t size,
               Encoded* encoded, Timing* timing) {
  WebPBitstreamFeatures features;
  WebPPicture picture;
  const uint64_t decode_begin = NowNs();
  uint64_t encode_begin;
  bool ok = false;
  if (WebPGetFeatures(data, size, &features) != VP8_STATUS_OK ||
      !WebPPictureInit(&picture)) {
    return false;
  }
  // "CPU" names the input decoder. The normal encoder policy remains CUDA
  // capable and independently falls back stage-by-stage, matching the
  // existing CPU-decode/CUDA-encode transcoding baseline.
  if (!ConfigureBackend(true, options.device)) goto end;
  picture.width = features.width;
  picture.height = features.height;
  if (features.has_alpha) {
    int width = 0, height = 0;
    uint8_t* rgba = WebPDecodeRGBA(data, size, &width, &height);
    picture.use_argb = 1;
    if (rgba == nullptr || width != picture.width || height != picture.height ||
        !WebPPictureImportRGBA(&picture, rgba, width * 4)) {
      WebPFree(rgba);
      goto end;
    }
    WebPFree(rgba);
  } else {
    int width = 0, height = 0, y_stride = 0, uv_stride = 0;
    uint8_t *u = nullptr, *v = nullptr;
    uint8_t* y =
        WebPDecodeYUV(data, size, &width, &height, &u, &v, &y_stride,
                      &uv_stride);
    const int uv_height = (picture.height + 1) / 2;
    picture.use_argb = 0;
    picture.colorspace = WEBP_YUV420;
    if (y == nullptr || width != picture.width || height != picture.height ||
        !WebPPictureAlloc(&picture)) {
      WebPFree(y);
      goto end;
    }
    for (int row = 0; row < picture.height; ++row) {
      memcpy(picture.y + (size_t)row * picture.y_stride,
             y + (size_t)row * y_stride, (size_t)picture.width);
    }
    for (int row = 0; row < uv_height; ++row) {
      const size_t width_uv = ((size_t)picture.width + 1u) / 2u;
      memcpy(picture.u + (size_t)row * picture.uv_stride,
             u + (size_t)row * uv_stride, width_uv);
      memcpy(picture.v + (size_t)row * picture.uv_stride,
             v + (size_t)row * uv_stride, width_uv);
    }
    WebPFree(y);
  }
  if (timing != nullptr) timing->decode_ns = NowNs() - decode_begin;
  encode_begin = NowNs();
  ok = EncodePicture(options, &picture, encoded);
  if (timing != nullptr) timing->encode_ns = NowNs() - encode_begin;
end:
  WebPPictureFree(&picture);
  return ok;
}

bool AddMetadataChunk(WebPMux* mux, const char fourcc[4],
                      const WebPTranscodeChunk& chunk) {
  if (chunk.bytes == nullptr) return true;
  WebPData data;
  data.bytes = chunk.bytes;
  data.size = chunk.size;
  return WebPMuxSetChunk(mux, fourcc, &data, 1) == WEBP_MUX_OK;
}

bool PreserveMetadata(const WebPTranscodeInput& input, Encoded* encoded) {
  WebPData bitstream;
  WebPData assembled;
  WebPMux* mux;
  if (input.iccp.bytes == nullptr && input.exif.bytes == nullptr &&
      input.xmp.bytes == nullptr) {
    return true;
  }
  bitstream.bytes = encoded->bytes;
  bitstream.size = encoded->size;
  WebPDataInit(&assembled);
  mux = WebPMuxCreate(&bitstream, 1);
  if (mux == nullptr || !AddMetadataChunk(mux, "ICCP", input.iccp) ||
      !AddMetadataChunk(mux, "EXIF", input.exif) ||
      !AddMetadataChunk(mux, "XMP ", input.xmp) ||
      WebPMuxAssemble(mux, &assembled) != WEBP_MUX_OK) {
    WebPMuxDelete(mux);
    WebPDataClear(&assembled);
    return false;
  }
  WebPMuxDelete(mux);
  WebPFree(encoded->bytes);
  encoded->bytes = const_cast<uint8_t*>(assembled.bytes);
  encoded->size = assembled.size;
  return true;
}

__global__ void SplitNV12(const uint8_t* uv, size_t pitch, uint8_t* u,
                          uint8_t* v, size_t uv_width, size_t uv_height) {
  const size_t index = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
  if (index < uv_width * uv_height) {
    const size_t row = index / uv_width;
    const size_t column = index - row * uv_width;
    u[index] = uv[row * pitch + 2u * column];
    v[index] = uv[row * pitch + 2u * column + 1u];
  }
}

struct NVDECSession {
  WebPPicture* picture = nullptr;
  int expected_width = 0;
  int expected_height = 0;
  CUvideoparser parser = nullptr;
  CUvideodecoder decoder = nullptr;
  unsigned long surface_height = 0;
  int display_count = 0;
  bool failed = false;
  int decode_status = (int)cuvidDecodeStatus_Invalid;
  int decode_status_result = -1;
  bool decode_concealed = false;
  const char* reason = "nvdec-error";
  uint64_t device_to_device_bytes = 0;
  uint64_t handoff_ns = 0;
  uint64_t timestamp = 0;
};

bool Injected(const char* stage) {
  const char* value = getenv("WEBP_NVDEC_INJECT");
  return value != nullptr && !strcmp(value, stage);
}

int CUDAAPI HandleSequence(void* opaque, CUVIDEOFORMAT* format) {
  NVDECSession* session = static_cast<NVDECSession*>(opaque);
  CUVIDDECODECAPS caps = {};
  CUVIDDECODECREATEINFO create = {};
  const int width = format->display_area.right - format->display_area.left;
  const int height = format->display_area.bottom - format->display_area.top;
  if (getenv("WEBP_NVDEC_VERBOSE") != nullptr) {
    fprintf(stderr,
            "WebP-NVDEC: sequence codec=%d chroma=%d depth=%u coded=%ux%u "
            "display=[%d,%d,%d,%d] expected=%dx%d\n",
            (int)format->codec, (int)format->chroma_format,
            format->bit_depth_luma_minus8 + 8u, format->coded_width,
            format->coded_height, format->display_area.left,
            format->display_area.top, format->display_area.right,
            format->display_area.bottom, session->expected_width,
            session->expected_height);
  }
  if (Injected("decoder")) {
    session->reason = "injected-decoder-error";
    session->failed = true;
    return 0;
  }
  if (session->decoder != nullptr || format->codec != cudaVideoCodec_VP8 ||
      format->chroma_format != cudaVideoChromaFormat_420 ||
      format->bit_depth_luma_minus8 != 0 || format->display_area.left != 0 ||
      format->display_area.top != 0 || width != session->expected_width ||
      height != session->expected_height) {
    session->reason = "unsupported-nvdec-sequence";
    session->failed = true;
    return 0;
  }
  caps.eCodecType = cudaVideoCodec_VP8;
  caps.eChromaFormat = format->chroma_format;
  caps.nBitDepthMinus8 = format->bit_depth_luma_minus8;
  if (cuvidGetDecoderCaps(&caps) != CUDA_SUCCESS || !caps.bIsSupported ||
      format->coded_width < (unsigned)caps.nMinWidth ||
      format->coded_height < (unsigned)caps.nMinHeight ||
      format->coded_width > caps.nMaxWidth ||
      format->coded_height > caps.nMaxHeight ||
      ((uint64_t)format->coded_width * format->coded_height) / 256u >
          caps.nMaxMBCount) {
    session->reason = "nvdec-vp8-unsupported";
    session->failed = true;
    return 0;
  }
  create.ulWidth = format->coded_width;
  create.ulHeight = format->coded_height;
  // A still VP8 frame needs no reference-frame queue beyond the parser's
  // current surface, but keep two surfaces for SDK/driver compatibility.
  create.ulNumDecodeSurfaces = 2;
  create.CodecType = cudaVideoCodec_VP8;
  create.ChromaFormat = cudaVideoChromaFormat_420;
  create.ulCreationFlags = cudaVideoCreate_PreferCUVID;
  create.bitDepthMinus8 = 0;
  create.ulMaxWidth = format->coded_width;
  create.ulMaxHeight = format->coded_height;
  create.display_area.left = format->display_area.left;
  create.display_area.top = format->display_area.top;
  create.display_area.right = format->display_area.right;
  create.display_area.bottom = format->display_area.bottom;
  create.OutputFormat = cudaVideoSurfaceFormat_NV12;
  create.DeinterlaceMode = cudaVideoDeinterlaceMode_Weave;
  create.ulTargetWidth = format->coded_width;
  create.ulTargetHeight = format->coded_height;
  create.ulNumOutputSurfaces = 1;
  session->surface_height = create.ulTargetHeight;
  if (cuvidCreateDecoder(&session->decoder, &create) != CUDA_SUCCESS) {
    session->reason = "nvdec-decoder-allocation";
    session->failed = true;
    return 0;
  }
  return (int)create.ulNumDecodeSurfaces;
}

int CUDAAPI HandleDecode(void* opaque, CUVIDPICPARAMS* picture) {
  NVDECSession* session = static_cast<NVDECSession*>(opaque);
  if (session->decoder == nullptr ||
      cuvidDecodePicture(session->decoder, picture) != CUDA_SUCCESS) {
    session->reason = "nvdec-decode-error";
    session->failed = true;
    return 0;
  }
  return 1;
}

int CUDAAPI HandleDisplay(void* opaque, CUVIDPARSERDISPINFO* display) {
  NVDECSession* session = static_cast<NVDECSession*>(opaque);
  CUVIDPROCPARAMS processing = {};
  CUdeviceptr mapped = 0;
  unsigned int pitch = 0;
  uint8_t* u = nullptr;
  uint8_t* v = nullptr;
  const size_t uv_width = ((size_t)session->expected_width + 1u) / 2u;
  const size_t uv_height = ((size_t)session->expected_height + 1u) / 2u;
  const size_t uv_bytes = uv_width * uv_height;
  WebPAcceleratorResult handoff = WEBP_ACCELERATOR_ERROR;
  uint64_t begin;
  if (session->display_count != 0 || Injected("map")) {
    session->reason = "nvdec-map-error";
    session->failed = true;
    return 0;
  }
  processing.progressive_frame = display->progressive_frame;
  processing.second_field = display->repeat_first_field + 1;
  processing.top_field_first = display->top_field_first;
  processing.unpaired_field = display->repeat_first_field < 0;
  if (cuvidMapVideoFrame(session->decoder, display->picture_index, &mapped,
                         &pitch, &processing) != CUDA_SUCCESS ||
      mapped == 0 || pitch < (unsigned)session->expected_width ||
      Injected("allocation") || cudaMalloc(&u, uv_bytes) != cudaSuccess ||
      cudaMalloc(&v, uv_bytes) != cudaSuccess) {
    session->reason = "nvdec-map-or-allocation-error";
    session->failed = true;
    if (u != nullptr) cudaFree(u);
    if (v != nullptr) cudaFree(v);
    if (mapped != 0) cuvidUnmapVideoFrame(session->decoder, mapped);
    return 0;
  }
  {
    CUVIDGETDECODESTATUS status = {};
    const CUresult status_result =
        cuvidGetDecodeStatus(session->decoder, display->picture_index, &status);
    session->decode_status_result = (int)status_result;
    session->decode_status =
        status_result == CUDA_SUCCESS ? (int)status.decodeStatus
                                      : (int)cuvidDecodeStatus_Invalid;
    session->decode_concealed =
        status_result == CUDA_SUCCESS &&
        status.decodeStatus == cuvidDecodeStatus_Error_Concealed;
    if (getenv("WEBP_NVDEC_VERBOSE") != nullptr) {
      fprintf(stderr,
              "WebP-NVDEC: picture=%d decode_status=%d status_result=%d\n",
              display->picture_index, session->decode_status,
              (int)status_result);
    }
    // NVIDIA's SDK sample treats this API as diagnostic only when supported;
    // the Turing VP8 decoder returns CUDA_ERROR_NOT_SUPPORTED. A reported
    // hard, unconcealed error is not safe for transcoding. Error_Concealed is
    // retained and surfaced in telemetry; strict RIFF/VP8 geometry checks
    // have already rejected truncated input.
    if (status_result == CUDA_SUCCESS &&
        status.decodeStatus == cuvidDecodeStatus_Error) {
      session->reason = "nvdec-corrupt-frame";
      session->failed = true;
      (void)cudaFree(u);
      (void)cudaFree(v);
      (void)cuvidUnmapVideoFrame(session->decoder, mapped);
      return 0;
    }
  }
  begin = NowNs();
  {
    const uint8_t* const uv = reinterpret_cast<const uint8_t*>(
        (uintptr_t)(mapped + (CUdeviceptr)((size_t)pitch *
                                          session->surface_height)));
    const unsigned int threads = 256;
    const unsigned int blocks =
        (unsigned int)((uv_bytes + threads - 1u) / threads);
    SplitNV12<<<blocks, threads>>>(uv, pitch, u, v, uv_width, uv_height);
    if (cudaGetLastError() == cudaSuccess &&
        cudaDeviceSynchronize() == cudaSuccess && !Injected("handoff")) {
      handoff = WebPCUDARegisterExternalYUV420(
          reinterpret_cast<const void*>((uintptr_t)mapped), pitch, u, uv_width,
          v, uv_width, session->picture->y, session->picture->y_stride,
          session->picture->u, session->picture->v,
          session->picture->uv_stride, session->expected_width,
          session->expected_height, &session->device_to_device_bytes);
    }
  }
  session->handoff_ns = NowNs() - begin;
  (void)cudaFree(u);
  (void)cudaFree(v);
  if (cuvidUnmapVideoFrame(session->decoder, mapped) != CUDA_SUCCESS ||
      handoff != WEBP_ACCELERATOR_SUCCESS) {
    WebPCUDAClearExternalYUV420();
    session->reason = "device-yuv-handoff-error";
    session->failed = true;
    return 0;
  }
  ++session->display_count;
  return 1;
}

void DestroyNVDECSession(NVDECSession* session) {
  if (session->parser != nullptr) {
    (void)cuvidDestroyVideoParser(session->parser);
  }
  if (session->decoder != nullptr) {
    (void)cuvidDestroyDecoder(session->decoder);
  }
  session->parser = nullptr;
  session->decoder = nullptr;
}

bool DecodeNVDEC(const Options& options, const WebPTranscodeInput& input,
                 WebPPicture* picture, NVDECSession* session, Timing* timing,
                 const char** reason) {
  CUVIDPARSERPARAMS parser_params = {};
  CUVIDSOURCEDATAPACKET packet = {};
  CUcontext context = nullptr;
  uint64_t begin = NowNs();
  bool ok = false;
  if (Injected("parser") || cudaSetDevice(options.device) != cudaSuccess ||
      cudaFree(nullptr) != cudaSuccess || cuCtxGetCurrent(&context) != CUDA_SUCCESS ||
      context == nullptr) {
    *reason = Injected("parser") ? "injected-parser-error"
                                  : "cuda-device-unavailable";
    timing->decode_ns = NowNs() - begin;
    return false;
  }
  session->picture = picture;
  session->display_count = 0;
  session->failed = false;
  session->decode_status = (int)cuvidDecodeStatus_Invalid;
  session->decode_status_result = -1;
  session->decode_concealed = false;
  session->reason = "nvdec-error";
  session->device_to_device_bytes = 0;
  session->handoff_ns = 0;
  if (session->parser == nullptr) {
    session->expected_width = input.width;
    session->expected_height = input.height;
    parser_params.CodecType = cudaVideoCodec_VP8;
    parser_params.ulMaxNumDecodeSurfaces = 2;
    parser_params.ulMaxDisplayDelay = 0;
    parser_params.pUserData = session;
    parser_params.pfnSequenceCallback = HandleSequence;
    parser_params.pfnDecodePicture = HandleDecode;
    parser_params.pfnDisplayPicture = HandleDisplay;
    if (cuvidCreateVideoParser(&session->parser, &parser_params) !=
        CUDA_SUCCESS) {
      *reason = "nvdec-parser-create-error";
      timing->decode_ns = NowNs() - begin;
      return false;
    }
  } else if (session->expected_width != input.width ||
             session->expected_height != input.height) {
    *reason = "nvdec-session-dimension-change";
    timing->decode_ns = NowNs() - begin;
    return false;
  }
  packet.payload = input.vp8.bytes;
  packet.payload_size = input.vp8.size;
  packet.flags = CUVID_PKT_TIMESTAMP;
  packet.timestamp = (CUvideotimestamp)session->timestamp++;
  if (cuvidParseVideoData(session->parser, &packet) == CUDA_SUCCESS &&
      !session->failed && session->display_count == 1) {
    ok = true;
  }
  timing->decode_ns = NowNs() - begin;
  timing->handoff_ns = session->handoff_ns;
  timing->device_to_device_bytes = session->device_to_device_bytes;
  *reason = ok ? "none" : session->reason;
  if (!ok) {
    WebPCUDAClearExternalYUV420();
    DestroyNVDECSession(session);
  }
  return ok;
}

bool EncodeNVDEC(const Options& options, const WebPTranscodeInput& input,
                 Encoded* encoded, NVDECSession* session, Timing* timing,
                 const char** reason) {
  WebPPicture picture;
  uint32_t stages;
  uint64_t begin;
  bool ok = false;
  if (!WebPPictureInit(&picture)) {
    *reason = "cuda-configuration-error";
    return false;
  }
  if (!ConfigureBackend(true, options.device)) {
    *reason = "cuda-configuration-error";
    goto end;
  }
  picture.use_argb = 0;
  picture.colorspace = WEBP_YUV420;
  picture.width = input.width;
  picture.height = input.height;
  if (!WebPPictureAlloc(&picture)) {
    *reason = "host-placeholder-allocation";
    goto end;
  }
  WebPCUDAResetSuccessfulStages();
  if (!DecodeNVDEC(options, input, &picture, session, timing, reason)) goto end;
  begin = NowNs();
  if (!EncodePicture(options, &picture, encoded)) {
    *reason = "cuda-encode-error";
    goto end;
  }
  timing->encode_ns = NowNs() - begin;
  stages = WebPCUDAGetSuccessfulStages();
  if ((stages & (WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS |
                 WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE)) !=
      (WEBP_ACCELERATOR_STAGE_LOSSY_ANALYSIS |
       WEBP_ACCELERATOR_STAGE_LOSSY_DECIMATE)) {
    WebPFree(encoded->bytes);
    *encoded = Encoded();
    *reason = "required-cuda-stage-declined";
    goto end;
  }
  ok = true;
end:
  WebPPictureFree(&picture);
  WebPCUDAClearExternalYUV420();
  return ok;
}

double DecodePSNR(const Encoded& a, const Encoded& b, int* dimensions_match) {
  int aw = 0, ah = 0, bw = 0, bh = 0;
  uint8_t* ap = WebPDecodeRGBA(a.bytes, a.size, &aw, &ah);
  uint8_t* bp = WebPDecodeRGBA(b.bytes, b.size, &bw, &bh);
  double error = 0.0;
  *dimensions_match = ap != nullptr && bp != nullptr && aw == bw && ah == bh;
  if (*dimensions_match) {
    const size_t count = (size_t)aw * ah * 4u;
    for (size_t i = 0; i < count; ++i) {
      const double delta = (double)ap[i] - bp[i];
      error += delta * delta;
    }
    error /= count;
  }
  WebPFree(ap);
  WebPFree(bp);
  if (!*dimensions_match) return 0.0;
  return error == 0.0 ? 99.0 : 10.0 * log10(255.0 * 255.0 / error);
}

bool RunOne(const Options& options, const std::vector<uint8_t>& data,
            Encoded* encoded, NVDECSession* session, Timing* timing,
            const char** selected_backend, const char** decline_reason,
            const char** decoded_format) {
  WebPTranscodeInput input;
  uint64_t begin = NowNs();
  uint64_t stage_begin = begin;
  bool accelerated = false;
  if (!WebPTranscodeParseInput(data.data(), data.size(), &input)) {
    input.status = WEBP_TRANSCODE_INPUT_MALFORMED;
    input.reason = WebPTranscodeInputStatusName(input.status);
  }
  timing->parse_ns = NowNs() - stage_begin;
  *decline_reason = input.reason;
  if (strcmp(options.backend, "cpu") &&
      input.status == WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE) {
    accelerated =
        EncodeNVDEC(options, input, encoded, session, timing, decline_reason);
  }
  if (!accelerated) {
    if (!EncodeCPU(options, data.data(), data.size(), encoded, timing)) {
      return false;
    }
    timing->device_to_device_bytes = 0;
    *selected_backend = "cpu";
    *decoded_format = input.status == WEBP_TRANSCODE_INPUT_ALPHA
                          ? "cpu-rgba"
                          : "cpu-yuv420";
    if (!strcmp(options.backend, "cpu") &&
        input.status == WEBP_TRANSCODE_INPUT_NVDEC_ELIGIBLE) {
      *decline_reason = "forced-cpu";
    }
  } else {
    *selected_backend = "nvdec";
    *decline_reason = "none";
    *decoded_format = "nvdec-nv12";
  }
  stage_begin = NowNs();
  if (!PreserveMetadata(input, encoded)) return false;
  timing->metadata_ns = NowNs() - stage_begin;
  timing->total_ns = NowNs() - begin;
  return true;
}

}  // namespace

int main(int argc, char** argv) {
  Options options;
  std::vector<uint8_t> input;
  Encoded final_output;
  NVDECSession nvdec_session;
  if (!ParseOptions(argc, argv, &options)) {
    Usage(argv[0]);
    return 2;
  }
  if (!ReadFile(options.input, &input)) {
    fprintf(stderr, "failed to read input: %s\n", options.input);
    return 2;
  }
  for (int sequence = -options.warmups; sequence < options.samples;
       ++sequence) {
    Encoded output;
    Timing timing;
    const char* backend = "cpu";
    const char* reason = "none";
    const char* decoded_format = "unknown";
    double verification_psnr = -1.0;
    int width = 0, height = 0;
    if (!RunOne(options, input, &output, &nvdec_session, &timing, &backend,
                &reason, &decoded_format) ||
        !WebPGetInfo(output.bytes, output.size, &width, &height)) {
      WebPFree(output.bytes);
      fprintf(stderr, "transcode failed at sequence %d\n", sequence);
      DestroyNVDECSession(&nvdec_session);
      return 1;
    }
    if (sequence < 0) {
      WebPFree(output.bytes);
      continue;
    }
    if (options.verify && !strcmp(backend, "nvdec")) {
      Encoded reference;
      int dimensions_match = 0;
      if (!EncodeCPU(options, input.data(), input.size(), &reference,
                     nullptr)) {
        WebPFree(output.bytes);
        DestroyNVDECSession(&nvdec_session);
        return 1;
      }
      verification_psnr =
          DecodePSNR(output, reference, &dimensions_match);
      WebPFree(reference.bytes);
      if (!dimensions_match || verification_psnr < 40.0) {
        fprintf(stderr,
                "NVDEC/CPU verification failed: dimensions=%d PSNR=%.3f "
                "(required >=40 dB)\n",
                dimensions_match, verification_psnr);
        WebPFree(output.bytes);
        DestroyNVDECSession(&nvdec_session);
        return 1;
      }
    }
    printf("{\"operation\":\"webp_transcode\",\"sequence\":%d,"
           "\"backend\":\"%s\",\"decline_reason\":\"%s\","
           "\"decoded_format\":\"%s\",\"nvdec_decode_status\":%d,"
           "\"nvdec_decode_status_result\":%d,"
           "\"nvdec_error_concealed\":%s,"
           "\"width\":%d,\"height\":%d,\"method\":%d,"
           "\"quality\":%d,\"parse_ns\":%llu,\"decode_ns\":%llu,"
           "\"device_handoff_ns\":%llu,\"webp_encode_ns\":%llu,"
           "\"metadata_ns\":%llu,\"total_ns\":%llu,"
           "\"images_per_second\":%.6f,"
           "\"decoded_host_to_device_bytes\":0,"
           "\"decoded_device_to_host_bytes\":0,"
           "\"decoded_device_to_device_bytes\":%llu,"
           "\"verification_psnr_db\":%.6f,"
           "\"output_bytes\":%zu}\n",
           sequence, backend, reason, decoded_format,
           nvdec_session.decode_status,
           nvdec_session.decode_status_result,
           nvdec_session.decode_concealed ? "true" : "false", width, height,
           options.method,
           options.quality, (unsigned long long)timing.parse_ns,
           (unsigned long long)timing.decode_ns,
           (unsigned long long)timing.handoff_ns,
           (unsigned long long)timing.encode_ns,
           (unsigned long long)timing.metadata_ns,
           (unsigned long long)timing.total_ns,
           timing.total_ns != 0 ? 1e9 / timing.total_ns : 0.0,
           (unsigned long long)timing.device_to_device_bytes,
           verification_psnr, output.size);
    WebPFree(final_output.bytes);
    final_output = output;
  }
  if (!WriteFileAtomically(options.output, final_output.bytes,
                           final_output.size)) {
    fprintf(stderr, "failed to write output: %s\n", options.output);
    WebPFree(final_output.bytes);
    DestroyNVDECSession(&nvdec_session);
    return 1;
  }
  WebPFree(final_output.bytes);
  DestroyNVDECSession(&nvdec_session);
  return 0;
}
