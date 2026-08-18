// Copyright 2026
//
// Bit-exact CUDA device port of the VP8 encoder DSP used by the CUDA
// decimate stage: intra predictors, forward/inverse transforms, quantization,
// SSE/texture-distortion metrics, block copies, and flatness helpers.
//
// Every function mirrors the plain C reference implementation (the *_C
// functions in src/dsp/enc.c, plus TransformWHT_C from src/dsp/dec.c and the
// IsFlat helpers from src/dsp/quant.h) with identical integer arithmetic and
// the encoder's BPS-strided working-buffer layout. The only intentional
// deviation is that the CPU's precomputed clip1[] lookup table (which stores
// clip_8b of every index) is replaced by direct CudaClip8b calls, which is
// value-identical by construction. This header contains only __device__
// functions and device-usable constants; the including .cu file provides the
// <stdint.h> types.

#ifndef WEBP_ENC_CUDA_DECIMATE_DSP_CUH_
#define WEBP_ENC_CUDA_DECIMATE_DSP_CUH_

//------------------------------------------------------------------------------
// Layout constants (see src/dsp/dsp.h and src/enc/vp8i_enc.h).

constexpr int kCudaBPS = 32;  // stride of the encoder yuv working buffers

constexpr int kCudaYOffEnc = 0;
constexpr int kCudaUOffEnc = 16;
constexpr int kCudaVOffEnc = 16 + 8;
constexpr int kCudaYuvSizeEnc = kCudaBPS * 16;
constexpr int kCudaPredSizeEnc = 32 * kCudaBPS + 16 * kCudaBPS + 8 * kCudaBPS;

// Prediction-buffer block offsets (yuv_p layout).
constexpr int kCudaI16DC16 = 0 * 16 * kCudaBPS;
constexpr int kCudaI16TM16 = kCudaI16DC16 + 16;
constexpr int kCudaI16VE16 = 1 * 16 * kCudaBPS;
constexpr int kCudaI16HE16 = kCudaI16VE16 + 16;
constexpr int kCudaC8DC8 = 2 * 16 * kCudaBPS;
constexpr int kCudaC8TM8 = kCudaC8DC8 + 1 * 16;
constexpr int kCudaC8VE8 = 2 * 16 * kCudaBPS + 8 * kCudaBPS;
constexpr int kCudaC8HE8 = kCudaC8VE8 + 1 * 16;
constexpr int kCudaI4DC4 = 3 * 16 * kCudaBPS + 0;
constexpr int kCudaI4TM4 = kCudaI4DC4 + 4;
constexpr int kCudaI4VE4 = kCudaI4DC4 + 8;
constexpr int kCudaI4HE4 = kCudaI4DC4 + 12;
constexpr int kCudaI4RD4 = kCudaI4DC4 + 16;
constexpr int kCudaI4VR4 = kCudaI4DC4 + 20;
constexpr int kCudaI4LD4 = kCudaI4DC4 + 24;
constexpr int kCudaI4VL4 = kCudaI4DC4 + 28;
constexpr int kCudaI4HD4 = 3 * 16 * kCudaBPS + 4 * kCudaBPS;
constexpr int kCudaI4HU4 = kCudaI4HD4 + 4;
constexpr int kCudaI4TMP = kCudaI4HD4 + 8;

__device__ __constant__ uint16_t kCudaVP8I16ModeOffsets[4] = {
    kCudaI16DC16, kCudaI16TM16, kCudaI16VE16, kCudaI16HE16};
__device__ __constant__ uint16_t kCudaVP8UVModeOffsets[4] = {
    kCudaC8DC8, kCudaC8TM8, kCudaC8VE8, kCudaC8HE8};
// Indexed by {B_DC_PRED .. B_HU_PRED}.
__device__ __constant__ uint16_t kCudaVP8I4ModeOffsets[10] = {
    kCudaI4DC4, kCudaI4TM4, kCudaI4VE4, kCudaI4HE4, kCudaI4RD4,
    kCudaI4VR4, kCudaI4LD4, kCudaI4VL4, kCudaI4HD4, kCudaI4HU4};

__device__ __constant__ uint16_t kCudaVP8Scan[16] = {
    0 + 0 * kCudaBPS,  4 + 0 * kCudaBPS,  8 + 0 * kCudaBPS,  12 + 0 * kCudaBPS,
    0 + 4 * kCudaBPS,  4 + 4 * kCudaBPS,  8 + 4 * kCudaBPS,  12 + 4 * kCudaBPS,
    0 + 8 * kCudaBPS,  4 + 8 * kCudaBPS,  8 + 8 * kCudaBPS,  12 + 8 * kCudaBPS,
    0 + 12 * kCudaBPS, 4 + 12 * kCudaBPS, 8 + 12 * kCudaBPS,
    12 + 12 * kCudaBPS};

__device__ __constant__ uint16_t kCudaVP8ScanUV[4 + 4] = {
    0 + 0 * kCudaBPS, 4 + 0 * kCudaBPS,  0 + 4 * kCudaBPS, 4 + 4 * kCudaBPS,
    8 + 0 * kCudaBPS, 12 + 0 * kCudaBPS, 8 + 4 * kCudaBPS, 12 + 4 * kCudaBPS};

__device__ __constant__ uint8_t kCudaZigzag[16] = {
    0, 1, 4, 8, 5, 2, 3, 6, 9, 12, 13, 10, 7, 11, 14, 15};

//------------------------------------------------------------------------------
// Quantization matrix (mirror of VP8Matrix in src/enc/vp8i_enc.h).

struct CudaVP8Matrix {
  uint16_t q[16];        // quantizer steps
  uint16_t iq[16];       // reciprocals, fixed point.
  uint32_t bias[16];     // rounding bias
  uint32_t zthresh[16];  // value below which a coefficient is zeroed
  uint16_t sharpen[16];  // frequency boosters for slight sharpening
};

constexpr int kCudaQFix = 17;
constexpr int kCudaMaxLevel = 2047;

__device__ __forceinline__ int CudaQuantDiv(uint32_t n, uint32_t iQ,
                                            uint32_t B) {
  return (int)((n * iQ + B) >> kCudaQFix);
}

//------------------------------------------------------------------------------
// Basic helpers.

__device__ __forceinline__ uint8_t CudaClip8b(int v) {
  return (!(v & ~0xff)) ? (uint8_t)v : (v < 0) ? 0 : 255;
}

__device__ __forceinline__ int CudaAbs(int v) { return v < 0 ? -v : v; }

//------------------------------------------------------------------------------
// Transforms (bit-exact ports of ITransformOne/ITransform_C, FTransform_C,
// FTransform2_C, FTransformWHT_C from src/dsp/enc.c and TransformWHT_C from
// src/dsp/dec.c).

// WEBP_TRANSFORM_AC3_* constants from src/dsp/dsp.h.
constexpr int kCudaTransformAc3C1 = 20091;
constexpr int kCudaTransformAc3C2 = 35468;

__device__ __forceinline__ int CudaTransformAc3Mul1(int a) {
  return ((a * kCudaTransformAc3C1) >> 16) + a;
}

__device__ __forceinline__ int CudaTransformAc3Mul2(int a) {
  return (a * kCudaTransformAc3C2) >> 16;
}

__device__ void CudaITransformOne(const uint8_t* ref, const int16_t* in,
                                  uint8_t* dst) {
  int C[4 * 4];
  int* tmp = C;
  int i;
  for (i = 0; i < 4; ++i) {  // vertical pass
    const int a = in[0] + in[8];
    const int b = in[0] - in[8];
    const int c = CudaTransformAc3Mul2(in[4]) - CudaTransformAc3Mul1(in[12]);
    const int d = CudaTransformAc3Mul1(in[4]) + CudaTransformAc3Mul2(in[12]);
    tmp[0] = a + d;
    tmp[1] = b + c;
    tmp[2] = b - c;
    tmp[3] = a - d;
    tmp += 4;
    in++;
  }

  tmp = C;
  for (i = 0; i < 4; ++i) {  // horizontal pass
    const int dc = tmp[0] + 4;
    const int a = dc + tmp[8];
    const int b = dc - tmp[8];
    const int c = CudaTransformAc3Mul2(tmp[4]) - CudaTransformAc3Mul1(tmp[12]);
    const int d = CudaTransformAc3Mul1(tmp[4]) + CudaTransformAc3Mul2(tmp[12]);
    dst[0 + i * kCudaBPS] = CudaClip8b(ref[0 + i * kCudaBPS] + ((a + d) >> 3));
    dst[1 + i * kCudaBPS] = CudaClip8b(ref[1 + i * kCudaBPS] + ((b + c) >> 3));
    dst[2 + i * kCudaBPS] = CudaClip8b(ref[2 + i * kCudaBPS] + ((b - c) >> 3));
    dst[3 + i * kCudaBPS] = CudaClip8b(ref[3 + i * kCudaBPS] + ((a - d) >> 3));
    tmp++;
  }
}

__device__ void CudaITransform(const uint8_t* ref, const int16_t* in,
                               uint8_t* dst, int do_two) {
  CudaITransformOne(ref, in, dst);
  if (do_two) {
    CudaITransformOne(ref + 4, in + 16, dst + 4);
  }
}

__device__ void CudaFTransform(const uint8_t* src, const uint8_t* ref,
                               int16_t* out) {
  int i;
  int tmp[16];
  for (i = 0; i < 4; ++i, src += kCudaBPS, ref += kCudaBPS) {
    const int d0 = src[0] - ref[0];  // 9bit dynamic range ([-255,255])
    const int d1 = src[1] - ref[1];
    const int d2 = src[2] - ref[2];
    const int d3 = src[3] - ref[3];
    const int a0 = (d0 + d3);  // 10b [-510,510]
    const int a1 = (d1 + d2);
    const int a2 = (d1 - d2);
    const int a3 = (d0 - d3);
    tmp[0 + i * 4] = (a0 + a1) * 8;                        // 14b [-8160,8160]
    tmp[1 + i * 4] = (a2 * 2217 + a3 * 5352 + 1812) >> 9;  // [-7536,7542]
    tmp[2 + i * 4] = (a0 - a1) * 8;
    tmp[3 + i * 4] = (a3 * 2217 - a2 * 5352 + 937) >> 9;
  }
  for (i = 0; i < 4; ++i) {
    const int a0 = (tmp[0 + i] + tmp[12 + i]);  // 15b
    const int a1 = (tmp[4 + i] + tmp[8 + i]);
    const int a2 = (tmp[4 + i] - tmp[8 + i]);
    const int a3 = (tmp[0 + i] - tmp[12 + i]);
    out[0 + i] = (int16_t)((a0 + a1 + 7) >> 4);  // 12b
    out[4 + i] =
        (int16_t)(((a2 * 2217 + a3 * 5352 + 12000) >> 16) + (a3 != 0));
    out[8 + i] = (int16_t)((a0 - a1 + 7) >> 4);
    out[12 + i] = (int16_t)((a3 * 2217 - a2 * 5352 + 51000) >> 16);
  }
}

__device__ void CudaFTransform2(const uint8_t* src, const uint8_t* ref,
                                int16_t* out) {
  CudaFTransform(src, ref, out);
  CudaFTransform(src + 4, ref + 4, out + 16);
}

// Input are the 16 DC coefficients of an int16_t tmp[16][16] block array
// (stride 16 between consecutive blocks, hence in += 64 walks one column of
// the 4x4 DC grid), exactly like FTransformWHT_C.
__device__ void CudaFTransformWHT(const int16_t* in, int16_t* out) {
  // input is 12b signed
  int32_t tmp[16];
  int i;
  for (i = 0; i < 4; ++i, in += 64) {
    const int a0 = (in[0 * 16] + in[2 * 16]);  // 13b
    const int a1 = (in[1 * 16] + in[3 * 16]);
    const int a2 = (in[1 * 16] - in[3 * 16]);
    const int a3 = (in[0 * 16] - in[2 * 16]);
    tmp[0 + i * 4] = a0 + a1;  // 14b
    tmp[1 + i * 4] = a3 + a2;
    tmp[2 + i * 4] = a3 - a2;
    tmp[3 + i * 4] = a0 - a1;
  }
  for (i = 0; i < 4; ++i) {
    const int a0 = (tmp[0 + i] + tmp[8 + i]);  // 15b
    const int a1 = (tmp[4 + i] + tmp[12 + i]);
    const int a2 = (tmp[4 + i] - tmp[12 + i]);
    const int a3 = (tmp[0 + i] - tmp[8 + i]);
    const int b0 = a0 + a1;  // 16b
    const int b1 = a3 + a2;
    const int b2 = a3 - a2;
    const int b3 = a0 - a1;
    out[0 + i] = (int16_t)(b0 >> 1);  // 15b
    out[4 + i] = (int16_t)(b1 >> 1);
    out[8 + i] = (int16_t)(b2 >> 1);
    out[12 + i] = (int16_t)(b3 >> 1);
  }
}

// Inverse WHT (TransformWHT_C from src/dsp/dec.c): reads the 16 transformed
// DC values and scatters them back as the DC of each block in an
// int16_t[16][16] array (out[0], out[16], ..., out += 64 per row of four).
__device__ void CudaTransformWHT(const int16_t* in, int16_t* out) {
  int tmp[16];
  int i;
  for (i = 0; i < 4; ++i) {
    const int a0 = in[0 + i] + in[12 + i];
    const int a1 = in[4 + i] + in[8 + i];
    const int a2 = in[4 + i] - in[8 + i];
    const int a3 = in[0 + i] - in[12 + i];
    tmp[0 + i] = a0 + a1;
    tmp[8 + i] = a0 - a1;
    tmp[4 + i] = a3 + a2;
    tmp[12 + i] = a3 - a2;
  }
  for (i = 0; i < 4; ++i) {
    const int dc = tmp[0 + i * 4] + 3;  // w/ rounder
    const int a0 = dc + tmp[3 + i * 4];
    const int a1 = tmp[1 + i * 4] + tmp[2 + i * 4];
    const int a2 = tmp[1 + i * 4] - tmp[2 + i * 4];
    const int a3 = dc - tmp[3 + i * 4];
    out[0] = (int16_t)((a0 + a1) >> 3);
    out[16] = (int16_t)((a3 + a2) >> 3);
    out[32] = (int16_t)((a0 - a1) >> 3);
    out[48] = (int16_t)((a3 - a2) >> 3);
    out += 64;
  }
}

//------------------------------------------------------------------------------
// Intra predictions (ports of Fill/VerticalPred/HorizontalPred/TrueMotion/
// DCMode and IntraChromaPreds_C/Intra16Preds_C/Intra4Preds_C).
// NULL left/top pointers encode unavailable borders exactly like the CPU.

__device__ __forceinline__ void CudaFill(uint8_t* dst, int value, int size) {
  int j, x;
  for (j = 0; j < size; ++j) {
    for (x = 0; x < size; ++x) dst[j * kCudaBPS + x] = (uint8_t)value;
  }
}

__device__ __forceinline__ void CudaVerticalPred(uint8_t* dst,
                                                 const uint8_t* top,
                                                 int size) {
  int j, x;
  if (top != nullptr) {
    for (j = 0; j < size; ++j) {
      for (x = 0; x < size; ++x) dst[j * kCudaBPS + x] = top[x];
    }
  } else {
    CudaFill(dst, 127, size);
  }
}

__device__ __forceinline__ void CudaHorizontalPred(uint8_t* dst,
                                                   const uint8_t* left,
                                                   int size) {
  if (left != nullptr) {
    int j, x;
    for (j = 0; j < size; ++j) {
      for (x = 0; x < size; ++x) dst[j * kCudaBPS + x] = left[j];
    }
  } else {
    CudaFill(dst, 129, size);
  }
}

__device__ void CudaTrueMotion(uint8_t* dst, const uint8_t* left,
                               const uint8_t* top, int size) {
  int y;
  if (left != nullptr) {
    if (top != nullptr) {
      // Equivalent to the CPU's clip1[255 + top[x] + left[y] - left[-1]]
      // table lookups: clip1 stores clip_8b of every index.
      const int top_left = left[-1];
      for (y = 0; y < size; ++y) {
        int x;
        for (x = 0; x < size; ++x) {
          dst[x] = CudaClip8b(top[x] + left[y] - top_left);
        }
        dst += kCudaBPS;
      }
    } else {
      CudaHorizontalPred(dst, left, size);
    }
  } else {
    // true motion without left samples (hence: with default 129 value)
    // is equivalent to VE prediction where you just copy the top samples.
    // Note that if top samples are not available, the default value is
    // then 129, and not 127 as in the VerticalPred case.
    if (top != nullptr) {
      CudaVerticalPred(dst, top, size);
    } else {
      CudaFill(dst, 129, size);
    }
  }
}

__device__ void CudaDCMode(uint8_t* dst, const uint8_t* left,
                           const uint8_t* top, int size, int round,
                           int shift) {
  int DC = 0;
  int j;
  if (top != nullptr) {
    for (j = 0; j < size; ++j) DC += top[j];
    if (left != nullptr) {  // top and left present
      for (j = 0; j < size; ++j) DC += left[j];
    } else {  // top, but no left
      DC += DC;
    }
    DC = (DC + round) >> shift;
  } else if (left != nullptr) {  // left but no top
    for (j = 0; j < size; ++j) DC += left[j];
    DC += DC;
    DC = (DC + round) >> shift;
  } else {  // no top, no left, nothing.
    DC = 0x80;
  }
  CudaFill(dst, DC, size);
}

// Chroma 8x8 prediction. 'left' holds 16 samples (U then V), 'top' 8+8.
__device__ void CudaIntraChromaPreds(uint8_t* dst, const uint8_t* left,
                                     const uint8_t* top) {
  // U block
  CudaDCMode(kCudaC8DC8 + dst, left, top, 8, 8, 4);
  CudaVerticalPred(kCudaC8VE8 + dst, top, 8);
  CudaHorizontalPred(kCudaC8HE8 + dst, left, 8);
  CudaTrueMotion(kCudaC8TM8 + dst, left, top, 8);
  // V block
  dst += 8;
  if (top != nullptr) top += 8;
  if (left != nullptr) left += 16;
  CudaDCMode(kCudaC8DC8 + dst, left, top, 8, 8, 4);
  CudaVerticalPred(kCudaC8VE8 + dst, top, 8);
  CudaHorizontalPred(kCudaC8HE8 + dst, left, 8);
  CudaTrueMotion(kCudaC8TM8 + dst, left, top, 8);
}

__device__ void CudaIntra16Preds(uint8_t* dst, const uint8_t* left,
                                 const uint8_t* top) {
  CudaDCMode(kCudaI16DC16 + dst, left, top, 16, 16, 5);
  CudaVerticalPred(kCudaI16VE16 + dst, top, 16);
  CudaHorizontalPred(kCudaI16HE16 + dst, left, 16);
  CudaTrueMotion(kCudaI16TM16 + dst, left, top, 16);
}

//------------------------------------------------------------------------------
// Luma 4x4 predictions. Left samples are top[-5..-2], top_left is top[-1],
// top samples are top[0..3], top right is top[4..7], as in Intra4Preds_C.

__device__ __forceinline__ uint8_t CudaAvg3(int a, int b, int c) {
  return (uint8_t)((a + 2 * b + c + 2) >> 2);
}

__device__ __forceinline__ uint8_t CudaAvg2(int a, int b) {
  return (uint8_t)((a + b + 1) >> 1);
}

#define CUDA_I4_DST(x, y) dst[(x) + (y) * kCudaBPS]

__device__ void CudaVE4(uint8_t* dst, const uint8_t* top) {  // vertical
  const uint8_t vals[4] = {
      CudaAvg3(top[-1], top[0], top[1]),
      CudaAvg3(top[0], top[1], top[2]),
      CudaAvg3(top[1], top[2], top[3]),
      CudaAvg3(top[2], top[3], top[4]),
  };
  int i, x;
  for (i = 0; i < 4; ++i) {
    for (x = 0; x < 4; ++x) dst[i * kCudaBPS + x] = vals[x];
  }
}

__device__ void CudaHE4(uint8_t* dst, const uint8_t* top) {  // horizontal
  const int X = top[-1];
  const int I = top[-2];
  const int J = top[-3];
  const int K = top[-4];
  const int L = top[-5];
  int x;
  const uint8_t r0 = CudaAvg3(X, I, J);
  const uint8_t r1 = CudaAvg3(I, J, K);
  const uint8_t r2 = CudaAvg3(J, K, L);
  const uint8_t r3 = CudaAvg3(K, L, L);
  for (x = 0; x < 4; ++x) {
    dst[0 * kCudaBPS + x] = r0;
    dst[1 * kCudaBPS + x] = r1;
    dst[2 * kCudaBPS + x] = r2;
    dst[3 * kCudaBPS + x] = r3;
  }
}

__device__ void CudaDC4(uint8_t* dst, const uint8_t* top) {
  uint32_t dc = 4;
  int i;
  for (i = 0; i < 4; ++i) dc += top[i] + top[-5 + i];
  CudaFill(dst, dc >> 3, 4);
}

__device__ void CudaRD4(uint8_t* dst, const uint8_t* top) {
  const int X = top[-1];
  const int I = top[-2];
  const int J = top[-3];
  const int K = top[-4];
  const int L = top[-5];
  const int A = top[0];
  const int B = top[1];
  const int C = top[2];
  const int D = top[3];
  CUDA_I4_DST(0, 3) = CudaAvg3(J, K, L);
  CUDA_I4_DST(0, 2) = CUDA_I4_DST(1, 3) = CudaAvg3(I, J, K);
  CUDA_I4_DST(0, 1) = CUDA_I4_DST(1, 2) = CUDA_I4_DST(2, 3) =
      CudaAvg3(X, I, J);
  CUDA_I4_DST(0, 0) = CUDA_I4_DST(1, 1) = CUDA_I4_DST(2, 2) =
      CUDA_I4_DST(3, 3) = CudaAvg3(A, X, I);
  CUDA_I4_DST(1, 0) = CUDA_I4_DST(2, 1) = CUDA_I4_DST(3, 2) =
      CudaAvg3(B, A, X);
  CUDA_I4_DST(2, 0) = CUDA_I4_DST(3, 1) = CudaAvg3(C, B, A);
  CUDA_I4_DST(3, 0) = CudaAvg3(D, C, B);
}

__device__ void CudaLD4(uint8_t* dst, const uint8_t* top) {
  const int A = top[0];
  const int B = top[1];
  const int C = top[2];
  const int D = top[3];
  const int E = top[4];
  const int F = top[5];
  const int G = top[6];
  const int H = top[7];
  CUDA_I4_DST(0, 0) = CudaAvg3(A, B, C);
  CUDA_I4_DST(1, 0) = CUDA_I4_DST(0, 1) = CudaAvg3(B, C, D);
  CUDA_I4_DST(2, 0) = CUDA_I4_DST(1, 1) = CUDA_I4_DST(0, 2) =
      CudaAvg3(C, D, E);
  CUDA_I4_DST(3, 0) = CUDA_I4_DST(2, 1) = CUDA_I4_DST(1, 2) =
      CUDA_I4_DST(0, 3) = CudaAvg3(D, E, F);
  CUDA_I4_DST(3, 1) = CUDA_I4_DST(2, 2) = CUDA_I4_DST(1, 3) =
      CudaAvg3(E, F, G);
  CUDA_I4_DST(3, 2) = CUDA_I4_DST(2, 3) = CudaAvg3(F, G, H);
  CUDA_I4_DST(3, 3) = CudaAvg3(G, H, H);
}

__device__ void CudaVR4(uint8_t* dst, const uint8_t* top) {
  const int X = top[-1];
  const int I = top[-2];
  const int J = top[-3];
  const int K = top[-4];
  const int A = top[0];
  const int B = top[1];
  const int C = top[2];
  const int D = top[3];
  CUDA_I4_DST(0, 0) = CUDA_I4_DST(1, 2) = CudaAvg2(X, A);
  CUDA_I4_DST(1, 0) = CUDA_I4_DST(2, 2) = CudaAvg2(A, B);
  CUDA_I4_DST(2, 0) = CUDA_I4_DST(3, 2) = CudaAvg2(B, C);
  CUDA_I4_DST(3, 0) = CudaAvg2(C, D);

  CUDA_I4_DST(0, 3) = CudaAvg3(K, J, I);
  CUDA_I4_DST(0, 2) = CudaAvg3(J, I, X);
  CUDA_I4_DST(0, 1) = CUDA_I4_DST(1, 3) = CudaAvg3(I, X, A);
  CUDA_I4_DST(1, 1) = CUDA_I4_DST(2, 3) = CudaAvg3(X, A, B);
  CUDA_I4_DST(2, 1) = CUDA_I4_DST(3, 3) = CudaAvg3(A, B, C);
  CUDA_I4_DST(3, 1) = CudaAvg3(B, C, D);
}

__device__ void CudaVL4(uint8_t* dst, const uint8_t* top) {
  const int A = top[0];
  const int B = top[1];
  const int C = top[2];
  const int D = top[3];
  const int E = top[4];
  const int F = top[5];
  const int G = top[6];
  const int H = top[7];
  CUDA_I4_DST(0, 0) = CudaAvg2(A, B);
  CUDA_I4_DST(1, 0) = CUDA_I4_DST(0, 2) = CudaAvg2(B, C);
  CUDA_I4_DST(2, 0) = CUDA_I4_DST(1, 2) = CudaAvg2(C, D);
  CUDA_I4_DST(3, 0) = CUDA_I4_DST(2, 2) = CudaAvg2(D, E);

  CUDA_I4_DST(0, 1) = CudaAvg3(A, B, C);
  CUDA_I4_DST(1, 1) = CUDA_I4_DST(0, 3) = CudaAvg3(B, C, D);
  CUDA_I4_DST(2, 1) = CUDA_I4_DST(1, 3) = CudaAvg3(C, D, E);
  CUDA_I4_DST(3, 1) = CUDA_I4_DST(2, 3) = CudaAvg3(D, E, F);
  CUDA_I4_DST(3, 2) = CudaAvg3(E, F, G);
  CUDA_I4_DST(3, 3) = CudaAvg3(F, G, H);
}

__device__ void CudaHU4(uint8_t* dst, const uint8_t* top) {
  const int I = top[-2];
  const int J = top[-3];
  const int K = top[-4];
  const int L = top[-5];
  CUDA_I4_DST(0, 0) = CudaAvg2(I, J);
  CUDA_I4_DST(2, 0) = CUDA_I4_DST(0, 1) = CudaAvg2(J, K);
  CUDA_I4_DST(2, 1) = CUDA_I4_DST(0, 2) = CudaAvg2(K, L);
  CUDA_I4_DST(1, 0) = CudaAvg3(I, J, K);
  CUDA_I4_DST(3, 0) = CUDA_I4_DST(1, 1) = CudaAvg3(J, K, L);
  CUDA_I4_DST(3, 1) = CUDA_I4_DST(1, 2) = CudaAvg3(K, L, L);
  CUDA_I4_DST(3, 2) = CUDA_I4_DST(2, 2) = CUDA_I4_DST(0, 3) =
      CUDA_I4_DST(1, 3) = CUDA_I4_DST(2, 3) = CUDA_I4_DST(3, 3) = (uint8_t)L;
}

__device__ void CudaHD4(uint8_t* dst, const uint8_t* top) {
  const int X = top[-1];
  const int I = top[-2];
  const int J = top[-3];
  const int K = top[-4];
  const int L = top[-5];
  const int A = top[0];
  const int B = top[1];
  const int C = top[2];

  CUDA_I4_DST(0, 0) = CUDA_I4_DST(2, 1) = CudaAvg2(I, X);
  CUDA_I4_DST(0, 1) = CUDA_I4_DST(2, 2) = CudaAvg2(J, I);
  CUDA_I4_DST(0, 2) = CUDA_I4_DST(2, 3) = CudaAvg2(K, J);
  CUDA_I4_DST(0, 3) = CudaAvg2(L, K);

  CUDA_I4_DST(3, 0) = CudaAvg3(A, B, C);
  CUDA_I4_DST(2, 0) = CudaAvg3(X, A, B);
  CUDA_I4_DST(1, 0) = CUDA_I4_DST(3, 1) = CudaAvg3(I, X, A);
  CUDA_I4_DST(1, 1) = CUDA_I4_DST(3, 2) = CudaAvg3(J, I, X);
  CUDA_I4_DST(1, 2) = CUDA_I4_DST(3, 3) = CudaAvg3(K, J, I);
  CUDA_I4_DST(1, 3) = CudaAvg3(L, K, J);
}

__device__ void CudaTM4(uint8_t* dst, const uint8_t* top) {
  int x, y;
  // Equivalent to the CPU's clip1[255 + top[x] + top[-2 - y] - top[-1]].
  const int top_left = top[-1];
  for (y = 0; y < 4; ++y) {
    const int left_y = top[-2 - y];
    for (x = 0; x < 4; ++x) {
      dst[x] = CudaClip8b(top[x] + left_y - top_left);
    }
    dst += kCudaBPS;
  }
}

#undef CUDA_I4_DST

// Left samples are top[-5..-2], top_left is top[-1], top are located at
// top[0..3], and top right is top[4..7].
__device__ void CudaIntra4Preds(uint8_t* dst, const uint8_t* top) {
  CudaDC4(kCudaI4DC4 + dst, top);
  CudaTM4(kCudaI4TM4 + dst, top);
  CudaVE4(kCudaI4VE4 + dst, top);
  CudaHE4(kCudaI4HE4 + dst, top);
  CudaRD4(kCudaI4RD4 + dst, top);
  CudaVR4(kCudaI4VR4 + dst, top);
  CudaLD4(kCudaI4LD4 + dst, top);
  CudaVL4(kCudaI4VL4 + dst, top);
  CudaHD4(kCudaI4HD4 + dst, top);
  CudaHU4(kCudaI4HU4 + dst, top);
}

// Single-mode variant so one lane per mode can build its own prediction.
// The mode index matches kCudaVP8I4ModeOffsets / the B_*_PRED order.
__device__ void CudaIntra4PredMode(uint8_t* dst, const uint8_t* top,
                                   int mode) {
  switch (mode) {
    case 0: CudaDC4(kCudaI4DC4 + dst, top); break;
    case 1: CudaTM4(kCudaI4TM4 + dst, top); break;
    case 2: CudaVE4(kCudaI4VE4 + dst, top); break;
    case 3: CudaHE4(kCudaI4HE4 + dst, top); break;
    case 4: CudaRD4(kCudaI4RD4 + dst, top); break;
    case 5: CudaVR4(kCudaI4VR4 + dst, top); break;
    case 6: CudaLD4(kCudaI4LD4 + dst, top); break;
    case 7: CudaVL4(kCudaI4VL4 + dst, top); break;
    case 8: CudaHD4(kCudaI4HD4 + dst, top); break;
    case 9: CudaHU4(kCudaI4HU4 + dst, top); break;
    default: break;
  }
}

//------------------------------------------------------------------------------
// Metrics (SSE*_C and Disto*_C ports).

__device__ __forceinline__ int CudaGetSSE(const uint8_t* a, const uint8_t* b,
                                          int w, int h) {
  int count = 0;
  int y, x;
  for (y = 0; y < h; ++y) {
    for (x = 0; x < w; ++x) {
      const int diff = (int)a[x] - b[x];
      count += diff * diff;
    }
    a += kCudaBPS;
    b += kCudaBPS;
  }
  return count;
}

__device__ int CudaSSE16x16(const uint8_t* a, const uint8_t* b) {
  return CudaGetSSE(a, b, 16, 16);
}
__device__ int CudaSSE16x8(const uint8_t* a, const uint8_t* b) {
  return CudaGetSSE(a, b, 16, 8);
}
__device__ int CudaSSE8x8(const uint8_t* a, const uint8_t* b) {
  return CudaGetSSE(a, b, 8, 8);
}
__device__ int CudaSSE4x4(const uint8_t* a, const uint8_t* b) {
  return CudaGetSSE(a, b, 4, 4);
}

// Hadamard transform: returns the weighted sum of the absolute value of
// transformed coefficients. w[] contains a row-major 4 by 4 symmetric matrix.
__device__ int CudaTTransform(const uint8_t* in, const uint16_t* w) {
  int sum = 0;
  int tmp[16];
  int i;
  // horizontal pass
  for (i = 0; i < 4; ++i, in += kCudaBPS) {
    const int a0 = in[0] + in[2];
    const int a1 = in[1] + in[3];
    const int a2 = in[1] - in[3];
    const int a3 = in[0] - in[2];
    tmp[0 + i * 4] = a0 + a1;
    tmp[1 + i * 4] = a3 + a2;
    tmp[2 + i * 4] = a3 - a2;
    tmp[3 + i * 4] = a0 - a1;
  }
  // vertical pass
  for (i = 0; i < 4; ++i, ++w) {
    const int a0 = tmp[0 + i] + tmp[8 + i];
    const int a1 = tmp[4 + i] + tmp[12 + i];
    const int a2 = tmp[4 + i] - tmp[12 + i];
    const int a3 = tmp[0 + i] - tmp[8 + i];
    const int b0 = a0 + a1;
    const int b1 = a3 + a2;
    const int b2 = a3 - a2;
    const int b3 = a0 - a1;

    sum += w[0] * CudaAbs(b0);
    sum += w[4] * CudaAbs(b1);
    sum += w[8] * CudaAbs(b2);
    sum += w[12] * CudaAbs(b3);
  }
  return sum;
}

__device__ int CudaDisto4x4(const uint8_t* const a, const uint8_t* const b,
                            const uint16_t* const w) {
  const int sum1 = CudaTTransform(a, w);
  const int sum2 = CudaTTransform(b, w);
  return CudaAbs(sum2 - sum1) >> 5;
}

__device__ int CudaDisto16x16(const uint8_t* const a, const uint8_t* const b,
                              const uint16_t* const w) {
  int D = 0;
  int x, y;
  for (y = 0; y < 16 * kCudaBPS; y += 4 * kCudaBPS) {
    for (x = 0; x < 16; x += 4) {
      D += CudaDisto4x4(a + x + y, b + x + y, w);
    }
  }
  return D;
}

//------------------------------------------------------------------------------
// Quantization (QuantizeBlock_C / Quantize2Blocks_C ports). The CPU assigns
// VP8EncQuantizeBlockWHT to the very same QuantizeBlock_C, so the WHT variant
// is an alias here as well.

__device__ int CudaQuantizeBlock(int16_t in[16], int16_t out[16],
                                 const CudaVP8Matrix* const mtx) {
  int last = -1;
  int n;
  for (n = 0; n < 16; ++n) {
    const int j = kCudaZigzag[n];
    const int sign = (in[j] < 0);
    const uint32_t coeff = (sign ? -in[j] : in[j]) + mtx->sharpen[j];
    if (coeff > mtx->zthresh[j]) {
      const uint32_t Q = mtx->q[j];
      const uint32_t iQ = mtx->iq[j];
      const uint32_t B = mtx->bias[j];
      int level = CudaQuantDiv(coeff, iQ, B);
      if (level > kCudaMaxLevel) level = kCudaMaxLevel;
      if (sign) level = -level;
      in[j] = (int16_t)(level * (int)Q);
      out[n] = (int16_t)level;
      if (level) last = n;
    } else {
      out[n] = 0;
      in[j] = 0;
    }
  }
  return (last >= 0);
}

__device__ int CudaQuantize2Blocks(int16_t in[32], int16_t out[32],
                                   const CudaVP8Matrix* const mtx) {
  int nz;
  nz = CudaQuantizeBlock(in + 0 * 16, out + 0 * 16, mtx) << 0;
  nz |= CudaQuantizeBlock(in + 1 * 16, out + 1 * 16, mtx) << 1;
  return nz;
}

__device__ __forceinline__ int CudaQuantizeBlockWHT(
    int16_t in[16], int16_t out[16], const CudaVP8Matrix* const mtx) {
  return CudaQuantizeBlock(in, out, mtx);
}

//------------------------------------------------------------------------------
// Block copies (Copy4x4_C / Copy16x8_C ports).

__device__ __forceinline__ void CudaCopy(const uint8_t* src, uint8_t* dst,
                                         int w, int h) {
  int y, x;
  for (y = 0; y < h; ++y) {
    for (x = 0; x < w; ++x) dst[x] = src[x];
    src += kCudaBPS;
    dst += kCudaBPS;
  }
}

__device__ void CudaCopy4x4(const uint8_t* src, uint8_t* dst) {
  CudaCopy(src, dst, 4, 4);
}

__device__ void CudaCopy16x8(const uint8_t* src, uint8_t* dst) {
  CudaCopy(src, dst, 16, 8);
}

//------------------------------------------------------------------------------
// Flatness helpers (plain C variants from src/dsp/quant.h).

__device__ int CudaIsFlat(const int16_t* levels, int num_blocks, int thresh) {
  int score = 0;
  while (num_blocks-- > 0) {
    int i;
    for (i = 1; i < 16; ++i) {  // omit DC, we're only interested in AC
      score += (levels[i] != 0);
      if (score > thresh) return 0;
    }
    levels += 16;
  }
  return 1;
}

__device__ int CudaIsFlatSource16(const uint8_t* src) {
  const uint8_t value = src[0];
  int i, x;
  for (i = 0; i < 16; ++i) {
    for (x = 0; x < 16; ++x) {
      if (src[x] != value) return 0;
    }
    src += kCudaBPS;
  }
  return 1;
}

#endif  // WEBP_ENC_CUDA_DECIMATE_DSP_CUH_
