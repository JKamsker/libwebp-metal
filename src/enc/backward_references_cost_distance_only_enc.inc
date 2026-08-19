// Intentionally no include guard: the specialization experiment instantiates
// this private DP body once for the production baseline and once for the
// always-specialized candidate. The two names below must be macros.
static int BACKREF_DISTANCE_ONLY_NAME(
    int xsize, int ysize, const uint32_t* const argb, int cache_bits,
    const VP8LHashChain* const hash_chain, const VP8LBackwardRefs* const refs,
    uint16_t* const dist_array) {
  int i;
  int ok = 0;
  int cc_init = 0;
  const int pix_count = xsize * ysize;
  const int use_color_cache = (cache_bits > 0);
  const size_t literal_array_size =
      sizeof(*((CostModel*)NULL)->literal) * VP8LHistogramNumCodes(cache_bits);
  const size_t cost_model_size = sizeof(CostModel) + literal_array_size;
  CostModel* const cost_model =
      (CostModel*)WebPSafeCalloc(1ULL, cost_model_size);
  VP8LColorCache hashers;
  CostManager* cost_manager =
      (CostManager*)WebPSafeCalloc(1ULL, sizeof(*cost_manager));
  int offset_prev = -1, len_prev = -1;
  int64_t offset_cost = -1;
  int first_offset_is_constant = -1;
  int reach = 0;

  if (cost_model == NULL || cost_manager == NULL) goto Error;
  cost_model->literal = (uint32_t*)(cost_model + 1);
  if (use_color_cache) {
    cc_init = VP8LColorCacheInit(&hashers, cache_bits);
    if (!cc_init) goto Error;
  }
  if (!CostModelBuild(cost_model, xsize, cache_bits, refs)) goto Error;
  if (!CostManagerInit(cost_manager, dist_array, pix_count, cost_model)) {
    goto Error;
  }

  dist_array[0] = 0;
  AddSingleLiteralWithCostModel(argb, &hashers, cost_model, /*idx=*/0,
                                use_color_cache, /*prev_cost=*/0,
                                cost_manager->costs, dist_array);
  for (i = 1; i < pix_count; ++i) {
    const int64_t prev_cost = cost_manager->costs[i - 1];
    int offset, len;
    VP8LHashChainFindCopy(hash_chain, i, &offset, &len);
    AddSingleLiteralWithCostModel(argb, &hashers, cost_model, i,
                                  use_color_cache, prev_cost,
                                  cost_manager->costs, dist_array);
    if (len >= 2) {
      if (offset != offset_prev) {
        const int code = VP8LDistanceToPlaneCode(xsize, offset);
        offset_cost = GetDistanceCost(cost_model, code);
        first_offset_is_constant = 1;
        BACKREF_PUSH_INTERVAL_NAME(cost_manager, prev_cost + offset_cost, i,
                                   len);
      } else {
        assert(offset_cost >= 0);
        assert(len_prev >= 0);
        assert(first_offset_is_constant == 0 || first_offset_is_constant == 1);
        if (first_offset_is_constant) {
          reach = i - 1 + len_prev - 1;
          first_offset_is_constant = 0;
        }
        if (i + len - 1 > reach) {
          int offset_j, len_j = 0;
          int j;
          assert(len == MAX_LENGTH || len == pix_count - i);
          for (j = i; j <= reach; ++j) {
            VP8LHashChainFindCopy(hash_chain, j + 1, &offset_j, &len_j);
            if (offset_j != offset) {
              VP8LHashChainFindCopy(hash_chain, j, &offset_j, &len_j);
              break;
            }
          }
          UpdateCostAtIndex(cost_manager, j - 1, 0);
          UpdateCostAtIndex(cost_manager, j, 0);
          BACKREF_PUSH_INTERVAL_NAME(
              cost_manager, cost_manager->costs[j - 1] + offset_cost, j,
              len_j);
          reach = j + len_j - 1;
        }
      }
    }
    UpdateCostAtIndex(cost_manager, i, 1);
    offset_prev = offset;
    len_prev = len;
  }

  ok = !refs->error;
Error:
  if (cc_init) VP8LColorCacheClear(&hashers);
  CostManagerClear(cost_manager);
  WebPSafeFree(cost_model);
  WebPSafeFree(cost_manager);
  return ok;
}
