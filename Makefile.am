ACLOCAL_AMFLAGS = -I m4
SUBDIRS = sharpyuv src imageio man
EXTRA_DIST = COPYING autogen.sh CUDA_BENCHMARK_RESULTS.md \
  scripts/test_cuda.sh scripts/test_cuda_variants.sh \
  tests/cuda_concurrency_test.c tools/cuda_benchmark.c

if BUILD_EXTRAS
  SUBDIRS += extras
endif

SUBDIRS += examples
