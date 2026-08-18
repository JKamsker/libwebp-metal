# Backref-cost interval-search v1 design (untimed)

## Audited boundary

The verified base is `568d2476afef3465294bec6a4e099d1b598135f7`.
This cycle does not rerun, rename, pool, or reuse the rejected exact-sized
CostManager workspace result. Its remote make/toolchain admission, indexed
return, independent lease return, and exact-child cleanup structure are reused
only as operational protocol concepts under wholly new v1 identities.

`VP8LBackwardReferencesTraceBackwards` builds integer symbol costs, runs
`BackwardReferencesHashChainDistanceOnly`, packs the chosen path, and rebuilds
references in exact cache order. `CostManager` stores non-overlapping
`CostInterval` nodes ordered by `start`; `UpdateCostAtIndex(i, 1)` expires nodes
after their final useful index, and `PushInterval` consumes cached length-cost
segments in increasing start/end order. Its local `interval` pointer is already
monotonic across segments in one call.

The remaining repeated search is in `PositionOrphanInterval`. An insertion
whose hint is null restarts at `head` and advances to the insertion point. The
new interval is often strictly after every live interval, so this scans the
whole list even though `ConnectIntervals` can maintain the last node at no
algorithmic ambiguity.

## Committed work evidence and selection

An experiment-only recorder measured calls and directly relevant list work on
all nine publication cases at methods 4 and 6. It recorded no clock or elapsed
field. Raw records and the aggregate are in
`evidence/backref-cost-interval-search-v1-design-work/`.

| case | method | pushes | inserts | null hints | baseline forward steps | candidate tail fast paths | max live |
|---|---:|---:|---:|---:|---:|---:|---:|
| photo-small | 4/6 each | 34,712 | 27,043 | 25,335 | 113,189 | 23,909 | 21 |
| graphic-small | 4/6 each | 272 | 1,942 | 1,819 | 19,478 | 1,680 | 35 |
| photo-medium | 4 | 129,297 | 106,250 | 101,485 | 432,544 | 95,259 | 26 |
| photo-medium | 6 | 129,285 | 107,194 | 102,251 | 435,772 | 96,002 | 28 |
| graphic-medium | 4/6 each | 678 | 8,300 | 8,140 | 146,115 | 7,994 | 38 |
| photo-large | 4 | 296,362 | 422,392 | 401,781 | 1,647,141 | 379,197 | 36 |
| photo-large | 6 | 297,708 | 423,906 | 402,661 | 1,657,468 | 380,116 | 36 |
| graphic-large | 4/6 each | 1,652 | 22,484 | 22,411 | 427,598 | 22,260 | 30 |
| texture small/medium/large | 4/6 each | 0 | 0 | 0 | 0 | 0 | 0 |

Across 18 case-method pairs, 12 were active. Baseline positioning performed
5,585,685 forward and 53,769 backward steps. The candidate retained the exact
53,769 backward steps and removed every forward step, taking 1,062,260 strict
tail fast paths. All bitstream hashes and every non-search counter matched.
This supports exactly one implementation boundary: a maintained tail index for
strictly-after-tail null-hint insertion. Texture is correctness-only because
this corpus produces no `PushInterval` work there.

## Candidate and semantic contract

The candidate adds `tail` and `use_interval_search_v1` only to the gated
private `CostManager`. `ConnectIntervals` maintains `tail`. When and only when
the insertion hint is null, the list is nonempty, and
`current->start > tail->start`, positioning starts at `tail`; every other case
runs the unchanged baseline search. The strict relation deliberately excludes
equal starts. The existing strict cost update, `>=` replacement decision,
interval splitting/removal, insertion order, live-node cap, allocation and
serialization behavior, traceback, color-cache lookup/insertion, reference
append order, and input arrays are unchanged.

There is no candidate allocation or operation that can fail after DP mutation.
The private failure injection causes an exact baseline execution before the DP
starts, providing transactional fallback coverage without inventing a
mid-computation recovery path.

The independent gates are exactly:

- `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`
- `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT`
- `WEBP_BACKREF_COST_INTERVAL_SEARCH_V1_EXPERIMENT=1`

The optional private recorder macro is accepted only with the build gate and is
used solely by untimed validation. Frozen timed baseline/candidate builds omit
it, its calls, and its counters. Ordinary CMake, Unix make, and Autotools builds
omit the helper object, runner, macro, symbols, and runtime strings. The v1
compile gate is mutually exclusive with every overlapping backref-cost
workspace experiment.

## Frozen execution design

The remote path is the admitted noninteractive Unix-make/Xcode path validated
by remote v5; CMake, Homebrew/MacPorts discovery, installs, downloads, runner
directories/services, global PATH changes, power changes, and CUDA are
forbidden. Three independent clean builds are made: default baseline,
recorder-free candidate, and untimed recorder candidate. The recorder build
runs before correctness and timing and must satisfy the frozen work criterion.
It is never used for timing.

Tune cases are photo-medium and graphic-medium. Holdouts are photo-large and
graphic-large. Both methods 4/6 and cold/warm lifecycles are independent. Every
holdout cell must have paired median candidate/baseline at most 0.995 and raw
nearest-rank p95 ratio at most 1.005. Tune cells are descriptive only. All
correctness, work, source/toolchain, host-state, lease, resource, archive,
transfer, extraction, and cleanup gates are conjunctive and cannot be changed
after freeze.

No timed benchmark was run in phase 1.
