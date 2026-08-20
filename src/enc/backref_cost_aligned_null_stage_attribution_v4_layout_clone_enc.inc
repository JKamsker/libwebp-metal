// Intentionally no include guard. This is the baseline algorithm cloned into
// its own noinline symbol so B->L measures duplication/placement/control layout
// without changing interval work. Keep this body semantically locked to
// PushInterval; the codegen gate compares their normalized disassemblies.
static WEBP_BACKREF_ALIGNED_NULL_STAGE_ATTRIBUTION_V4_ENTRY void PushIntervalLayoutClone(
    CostManager* const manager, int64_t distance_cost, int position, int len) {
  size_t i;
  CostInterval* interval = manager->head;
  CostInterval* interval_next;
  const CostCacheInterval* const cost_cache_intervals = manager->cache_intervals;
  const int kSkipDistance = 10;

  INTERVAL_SPECIALIZATION_RECORD(
      VP8LBackrefCostIntervalSpecializationV1RecordPush(len < kSkipDistance));
  if (len < kSkipDistance) {
    int j;
    for (j = position; j < position + len; ++j) {
      const int k = j - position;
      int64_t cost_tmp;
      assert(k >= 0 && k < MAX_LENGTH);
      cost_tmp = distance_cost + manager->cost_cache[k];
      if (manager->costs[j] > cost_tmp) {
        manager->costs[j] = cost_tmp;
        manager->dist_array[j] = k + 1;
      }
    }
    return;
  }

  for (i = 0;
       i < manager->cache_intervals_size && cost_cache_intervals[i].start < len;
       ++i) {
    int start = position + cost_cache_intervals[i].start;
    const int end = position +
                    (cost_cache_intervals[i].end > len
                         ? len
                         : cost_cache_intervals[i].end);
    const int64_t cost = distance_cost + cost_cache_intervals[i].cost;

    INTERVAL_SPECIALIZATION_RECORD(
        VP8LBackrefCostIntervalSpecializationV1RecordCacheSegment());
    for (; interval != NULL && interval->start < end;
         interval = interval_next) {
      interval_next = interval->next;
      INTERVAL_SPECIALIZATION_RECORD(
          VP8LBackrefCostIntervalSpecializationV1RecordOverlapScan(
              start >= interval->end));
      if (start >= interval->end) continue;

      if (cost >= interval->cost) {
        const int start_new = interval->end;
        InsertInterval(manager, interval, cost, position, start,
                       interval->start
#if defined(WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER)
                       ,
                       /*had_null_hint=*/0
#endif
        );
        start = start_new;
        if (start >= end) break;
        continue;
      }

      if (start <= interval->start) {
        if (interval->end <= end) {
          PopInterval(manager, interval);
        } else {
          interval->start = end;
          break;
        }
      } else {
        if (end < interval->end) {
          const int end_original = interval->end;
          interval->end = start;
          InsertInterval(manager, interval, interval->cost, interval->index,
                         end, end_original
#if defined(WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER)
                         ,
                         /*had_null_hint=*/0
#endif
          );
          interval = interval->next;
          break;
        } else {
          interval->end = start;
        }
      }
    }
    InsertInterval(manager, interval, cost, position, start, end
#if defined(WEBP_BACKREF_COST_INTERVAL_SPECIALIZATION_V1_RECORDER)
                   ,
                   interval == NULL
#endif
    );
  }
}
