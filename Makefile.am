ACLOCAL_AMFLAGS = -I m4
SUBDIRS = sharpyuv src imageio man
EXTRA_DIST = COPYING autogen.sh CUDA_BENCHMARK_RESULTS.md \
  CUDA_ACCELERATION_EXPERIMENTS.md \
  scripts/test_cuda.sh scripts/test_cuda_variants.sh \
  scripts/test_cuda_acceleration_experiments.sh \
  tests/cuda_concurrency_test.c tools/cuda_benchmark.c \
  tools/cuda_acceleration_experiments.cu

if BUILD_EXTRAS
  SUBDIRS += extras
endif

SUBDIRS += examples
