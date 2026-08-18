# Backref-cost interval-search v2 design (untimed)

## Audited boundary and v1 consequence

The verified base is `22456df935cb3e9e834c0d06a3240db708ace2d7`.
Interval-search v1 remains a valid default-off negative result. It is not rerun,
pooled, relabeled, or promoted. Its committed raw work and timing records show
that positioning steps fell from 5,370,566 to 50,215 (99.065%), all four
graphic-large holdout cells passed, and all four photo-large medians failed;
only four of eight required holdout cells passed both frozen gates.

Source and optimized arm64 codegen identify v1's persistent cost. Its gated
`CostManager` adds `tail` and `use_interval_search_v1`, grows from 33,224 to
33,232 bytes, and shifts every following field. Every `ConnectIntervals` site
contains tail maintenance; every null-hint insertion reads the activation
field and tail and tests a strict start relation. On the required tune/holdout
rows this maps to 3,363,926 `ConnectIntervals` calls and 1,069,280 null-hint
checks. The exact per-cell source events, reconstructed tail-changing events,
layout, assembly hashes, opcode inventory, and limitations are recorded in
`evidence/backref-cost-interval-search-v2-design-codegen/audit.json`.

## Selected v2 candidate

V2 uses only state already traversed by one `PushInterval` call. Its overlap
scan is monotonic and necessarily visits the final live node before `interval`
becomes null. V2 remembers that visited node in a function-local append hint.
Successful tail insertion updates the local; an in-call pop of the visited tail
moves it to the predecessor. The local dies when `PushInterval` returns, so
expiration in `UpdateCostAtIndex` cannot make it stale.

For the final insertion of a cache-cost segment, and only when the original
hint is null, the local is nonnull, and `start` is strictly greater than the
local's start, v2 supplies the local as the ordinary positioning hint. Equal
starts take the baseline path. If no valid local exists, the unchanged search
starts at `head`. There is no persistent field, no `CostManager` layout change,
no `ConnectIntervals` bookkeeping, and no state carried across pushes.

The recorder ran no clock and recorded no elapsed field. Across all nine
publication cases and methods 4/6, the 12 active pairs retained exactly the v1
causal result: baseline had 5,585,685 forward and 53,769 backward positioning
steps; v2 had zero forward and the same 53,769 backward steps, with 1,062,260
local append fast paths. Bitstreams and every non-search counter match. V2's
fallback tail-update checks total 117,020 and its in-call pop-tail checks total
37,438, versus v1's persistent connect/null decision-site total derived from
the same rows. Texture remains correctness-only because it has no interval
work.

Optimized v2 restores the baseline 33,224-byte layout and removes v1's added
manager-field reads. Complete translation-unit assembly has 261 scalar `ldr`
instructions versus v1's 266, though v2 has larger static text and additional
control-flow sites. That mixed codegen result is why no performance claim is
made here: the frozen end-to-end median and p95 matrix remains decisive.

## Semantic, failure, and gate contract

V2 changes no integer cost, strict cost comparison, `>=` replacement choice,
interval start/end relation, equal-start order, update order, live-node cap,
allocation or recycling choice, traceback, color-cache lookup/insertion,
reference append order, or input array. The returned insertion pointer is only
a view of the node the baseline already allocated and linked. No new
allocation or fallible operation exists. Fault injection chooses an exact
baseline run before DP mutation, so fallback is transactional; existing node
allocation failure still serializes the interval exactly as baseline.

The wholly independent controls are:

- `WEBP_BUILD_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT`;
- `WEBP_USE_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT`;
- exact runtime `WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_EXPERIMENT=1`.

The recorder additionally requires
`WEBP_BACKREF_COST_INTERVAL_SEARCH_V2_RECORDER` and is forbidden in timed
binaries. V2 is mutually exclusive with v1 and every overlapping backref-cost
experiment. Ordinary CMake and Unix-make builds omit its helper object, target,
macro, symbols, runtime/fault strings, and runner.

## Frozen execution design

The sole authorized phase-2 action is the exact v2 pipeline in the manifest.
It uses the admitted noninteractive Unix-make Apple toolchain and explicit SDK;
CMake, installs, downloads, package discovery, global PATH changes, host/power
changes, runner directories/services, and CUDA are forbidden. Baseline and
candidate timed binaries are separate clean recorder-free builds; v1 is never
a timed variant. A third candidate recorder build runs only untimed work gates
and refuses samples.

Tune remains photo-medium and graphic-medium. Holdout remains photo-large and
graphic-large. Methods 4/6 and cold/warm lifecycles are independent. Cold has
11 alternating process pairs with one retained encode and no warmup. Warm has
six alternating pairs, two discarded warmups, and nine retained encodes.
There are 272 command processes and 1,040 retained samples. Tune is descriptive.
Every one of eight holdout cells must have paired process-median ratio at most
0.995 and nearest-rank raw p95 ratio at most 1.005. Correctness, work,
activation, source/toolchain, process, power, resources, lease, archive/index,
transfer/extraction, and exact cleanup gates are conjunctive.

## Terminal phase-1 decision

No timed benchmark was run in phase 1. The v2 mechanism remains a credible
algorithmic candidate, and the remote untimed operator completed its exact
Unix-make builds, 26 correctness cells, and 16 causal-work rows. The enclosing
independent evidence-return rehearsal nevertheless terminated with
`KeyError: 'bundle_sha256'`: it addressed the `admit_source()` result as though
that field were top-level, while the implemented contract exposes
`source_bundle_sha256` at the top level and `admission.bundle_sha256` for the
remote verification result.

This is an operational gate failure. It occurred after returnable rehearsal
artifacts had been created, but before a complete schema-valid top-level
transfer report could be emitted. Phase 1 did not retry. A read-only post-fail
query found zero children under the experiment safe root, proved the exact
`run.mvmKuE` child absent, and found zero `Runner.Worker` processes. Those facts
do not reconstruct the missing independent return record.

The frozen decision is therefore `REJECT_TIMING`; the executor has a hard
manifest gate and must not admit or start a timed pipeline from this handoff.
The next credible diagnostic, in a new phase-1 cycle with fresh evidence
identities, is to contract-test the admission-result field path and run one
untimed indexed refusal-return rehearsal. The corpus, command counts, work
gate, and 0.995 median / 1.005 p95 ceilings above remain unchanged.
