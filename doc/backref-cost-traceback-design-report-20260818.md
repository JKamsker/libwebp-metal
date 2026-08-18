# Backref cost/traceback workspace design report (untimed)

## Audited boundary and decision

The verified base is `3142ff3fe31cd1666c5615c5c4ee7dec2ef891f8`.
`VP8LGetBackwardReferences` reaches
`VP8LBackwardReferencesTraceBackwards` only on the non-low-effort path, after
the standard/RLE/box candidate selection, when the selected type is standard
or box and quality is at least 25. The publication protocol therefore uses
methods 4 and 6 at quality 75 and separately verifies invocation on every timed
input without taking a timed sample.

The untimed freeze check set a debugger breakpoint on the exact function and
observed entry for all 12 medium/large publication case-method combinations.
The debugger stopped at entry and no elapsed value or performance datum was
captured.

The audited implementation has three sequential parts: build integer symbol
costs from the selected references; run the interval-backed dynamic program
into `costs` and `dist_array`; then pack the chosen lengths backwards and
rebuild references while reproducing color-cache decisions. `CostModelBuild`
allocates a temporary histogram. `CostManagerInit` independently allocates the
cost array and cached-length intervals. The manager embeds ten interval nodes,
then allocates and recycles individual nodes up to the fixed 500-node live cap.
The hot update rules use strict `>` comparisons, and interval replacement uses
the existing `>=` relation. Those relations, traversal order, and linked-list
ordering determine exact ties.

The selected recorder-free candidate changes ownership only. After the cached
length costs establish the exact cached-interval count, one allocation contains
the pixel cost array, that exact interval array, and 490 additional interval
nodes. The existing ten inline nodes remain first. The DP loop, cost model,
cached values, interval insertion/removal order, live-node cap, strict cost
updates, `dist_array`, traceback packing, chosen-path traversal, cache lookup
and insertion order, reference append order, and final acceptance comparison
are unchanged. No clock, stage recorder, counter, CUDA code, Metal code, or
public API is added.

This is a credible implementation candidate without another observational
recorder because it removes two array allocations and all possible per-node
allocations from the exact target boundary while adding no new scan and no
calculation to the DP loop. Its performance is not assumed. A candidate
workspace allocation or injected workspace fault occurs before any DP update;
the wrapper clears that attempt and reruns the unchanged baseline path. Any
other allocation or reference-storage failure keeps the original error path.

## Closed evidence audit

The committed raw records, commands, correctness, resource records, artifact
indexes, operator reports, and evaluations for `backref_cache_search`,
`cache_size_serial_sweep`, and `cache_size_single_pass_slab` were inspected only
to confirm their recorded provenance and terminal dispositions. The first is
an observational recorder; the latter two are recorder-free exact
implementations rejected by their own frozen all-cell performance rules. None
is rerun, renamed, pooled, promoted, reproduced as a new sample, or used in a
ratio. This design makes no performance interpretation from those files.

## Safety and compatibility

The three independent gates are
`WEBP_BUILD_BACKREF_COST_TRACEBACK_EXPERIMENT`,
`WEBP_USE_BACKREF_COST_TRACEBACK_EXPERIMENT`, and exact runtime value
`WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT=1`. The private fault value is
`WEBP_BACKREF_COST_TRACEBACK_EXPERIMENT_INJECT_FAILURE=1`. Default CMake and
`makefile.unix` builds omit the helper translation unit, private symbols,
runtime strings, test and runner targets. The public headers, ABI, bitstream
syntax, normal allocation behavior, fallback contract, and production defaults
are unchanged.

Untimed tests compare every reconstructed `PixOrCopy` field (including cache
indexes), deterministic repeats, fault fallback, invalid runtime values, and
immutable pixels/hash chains over no-copy, periodic, run-length and constant
patterns at 1, 2, 3, 11, 257, 4,097 and 65,537 pixels and cache bits 0, 1, 5
and 10. The frozen operator adds bitstream and decoded-pixel equality, quality
24/25/26/75/100 edges, methods 4/6, all publication cases, default-build
independence, corpus immutability, refusal gates, and sanitizer execution.

No timed workload or performance sample was run by the designer.
