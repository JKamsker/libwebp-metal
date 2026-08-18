# Cache-size single-pass slab design report (untimed)

## Audit result

`CalculateBestCacheSize` consumes an immutable ARGB stream and immutable linked
backward references. For quality above 25 it allocates candidate histograms for
bits 0 through the caller's maximum and color arrays for bits 1 through that
maximum. It walks the references once, maintaining every cache state in lockstep.
Literal cache keys are derived once at the maximum width and shifted for smaller
caches. Copy lengths contribute the same prefix to every histogram; changed copy
colors update every cache. Entropy is evaluated in ascending cache-bit order and
uses strict improvement, so exact ties retain the first (lowest) value.

At the 10-bit edge the baseline performs 11 histogram allocations and 10 cache
allocations. Histogram allocation initializes metadata, the caller clears each
full histogram, and cache allocation clears each color array. Cleanup walks all
21 ownership edges. The selected cache bits later drive an in-place reference
rewrite; cost evaluation, LZ77 winner selection, and traceback are downstream
and do not need to change.

The closed serial sweep reduced live state but replayed the immutable stream for
every candidate. This candidate deliberately retains simultaneous states and one
reference traversal. A single zero-filled allocation owns metadata, histogram
objects, variable literal arrays, and cache colors. Thirty-two-byte alignment is
applied to each object/array boundary, all pointers are wired before traversal,
and one free releases the transaction. The only dynamic allocation site is
`WebPSafeCalloc`; no baseline histogram or color-cache allocator is called.

The candidate is credible because it removes allocator fan-out and redundant
independent clear operations without adding reference traversal, changing loop
order, copying state, or broadening the implementation boundary. Its effect is
not assumed: the frozen A/B requires an end-to-end holdout median improvement
and bounded p95 in every method/lifecycle cell. Failure to clear all independent
gates rejects the candidate.

## Safety and compatibility

The result pointer changes only after all entropy values are evaluated. A slab
allocation or injected allocation fault returns failure to the private dispatch,
which reruns the unchanged baseline with the original maximum. Quality 25 and
below takes the unchanged zero-cache fast path. The private build flag defaults
off, and default artifacts contain no candidate source, symbol, target, runtime
string, or fault knob. No installed header, public function, struct, ABI, syntax,
fallback contract, Metal path, or CUDA path changes.

Untimed unit and end-to-end tests cover explicit ties, all cache-bit and quality
edges, exhaustive and targeted streams, immutable inputs, deterministic repeats,
fault fallback, complete publication-corpus stream/decode equivalence, build
omission, runtime/lease refusal, and executable array-bounds, pointer-overflow,
undefined-behavior, and integer sanitizers.

No timed workload, benchmark, performance sampling, closed-experiment rerun, or
prior experiment sample was used to produce this design or report. Historical
closed values were read only to respect their recorded disposition and to avoid
reproducing the rejected topology.

On this Apple toolchain an AddressSanitizer-instrumented allocation-only test
process did not complete, so this design makes no AddressSanitizer pass claim.
The frozen executable sanitizer coverage is array-bounds, pointer-overflow,
undefined behavior, and integer checks; the ordinary exhaustive and complete
end-to-end matrices remain separate. This host sanitizer limitation is not an
implementation or executor blocker, but it must accompany the handoff.
