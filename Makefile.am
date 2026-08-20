ACLOCAL_AMFLAGS = -I m4
SUBDIRS = sharpyuv src imageio man
EXTRA_DIST = COPYING autogen.sh CUDA_BENCHMARK_RESULTS.md \
  CUDA_ACCELERATION_EXPERIMENTS.md \
  CUDA_EXPERIMENT_SUMMARY.md \
  CUDA_NEAR_LOSSLESS_RESULTS_RAW.md \
  doc/lossy-decimate-conformance.md \
  doc/nvdec-webp-transcoding.md \
  scripts/generate_lossy_decimate_fixtures.py \
  scripts/test_cuda.sh scripts/test_cuda_variants.sh \
  scripts/test_cuda_acceleration_experiments.sh \
  tests/bit_writer_utils_test.c \
  tests/cuda_concurrency_test.c tests/cuda_histogram_test.c \
  tests/cuda_near_lossless_test.c tests/cuda_trellis_test.c \
  tools/benchmark_platform.h tools/cuda_batch_benchmark.c \
  tools/cuda_transcode_common.c tools/cuda_transcode_common.h \
  tools/nvdec_webp_transcode.cu tests/cuda_external_yuv_test.cu \
  tests/cuda_transcode_policy_test.c \
  tools/cuda_benchmark.c \
  tools/lossy_decimate_conformance.c \
  tools/cuda_acceleration_experiments.cu

if BUILD_EXTRAS
  SUBDIRS += extras
endif

SUBDIRS += examples
