// Copyright 2026
//
// Private hooks for the focused backward-reference cache-search experiment.

#ifndef WEBP_ENC_BACKREF_CACHE_SEARCH_EXPERIMENT_ENC_H_
#define WEBP_ENC_BACKREF_CACHE_SEARCH_EXPERIMENT_ENC_H_

#include <stdint.h>

#include "src/webp/encode.h"

#ifdef __cplusplus
extern "C" {
#endif

#if defined(WEBP_USE_BACKREF_CACHE_SEARCH_EXPERIMENT)
void WebPBackrefCacheSearchBegin(const WebPConfig* config,
                                 const WebPPicture* picture);
void WebPBackrefCacheSearchEnd(int ok, int error_code);
uint64_t WebPBackrefCacheSearchTotalBegin(void);
void WebPBackrefCacheSearchTotalEnd(uint64_t start_ns);
uint64_t WebPBackrefCacheSearchStageBegin(void);
void WebPBackrefCacheSearchStageEnd(uint64_t start_ns);
#else
#define WebPBackrefCacheSearchBegin(config, picture) \
  ((void)(config), (void)(picture))
#define WebPBackrefCacheSearchEnd(ok, error_code) \
  ((void)(ok), (void)(error_code))
#define WebPBackrefCacheSearchTotalBegin() ((uint64_t)0)
#define WebPBackrefCacheSearchTotalEnd(start_ns) ((void)(start_ns))
#define WebPBackrefCacheSearchStageBegin() ((uint64_t)0)
#define WebPBackrefCacheSearchStageEnd(start_ns) ((void)(start_ns))
#endif

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // WEBP_ENC_BACKREF_CACHE_SEARCH_EXPERIMENT_ENC_H_
