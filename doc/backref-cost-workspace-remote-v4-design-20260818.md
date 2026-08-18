# Backref-cost workspace remote v4 design

Remote v3 correctly refused an AppleDouble member created by generic macOS
`tar`, but that refusal also hid the lease record and cleanup proof inside the
rejected channel. V4 changes only evidence return. The CostManager candidate is
the exact recorder-free v3 candidate modulo wholly private v4 names; integer
costs, strict ties, update order, the ten inline plus 490 allocated nodes,
traceback, reference/cache ordering, and transactional allocation-failure
fallback are unchanged.

V4 is independently gated by
`WEBP_BUILD_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT`,
`WEBP_USE_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT`, and runtime value
`WEBP_BACKREF_COST_WORKSPACE_REMOTE_V4_EXPERIMENT=1`. All are default off and
absent from ordinary objects and binaries. V3's canonical path guard and
repository-context bundle verification are retained under new v4 identities.

The frozen Python builder accepts only the sorted, verified remote
`artifact-hashes.json` list plus that index. It checks canonical containment,
exact tree membership, normalized relative POSIX names, regular files with one
link, and real parent directories. It explicitly writes GNU-format tar members
with fixed metadata and never recursively adds a directory. Symlinks,
hardlinks, devices, FIFOs, absolute paths, traversal, unknown files, and
containment escapes fail closed, preventing AppleDouble/xattr sidecars.

The extractor inventories every member before writing anything. A rejected
archive is kept under `return-protocol/quarantine/` with remote/local archive
digests, the complete name/type/size inventory, and the first offending member
and reason. No rejected member is extracted. A successful extraction rechecks
the remote artifact index, then creates and immediately verifies the local
`returned-evidence-hashes.json`.

`lease-record.json` is initialized before host preflight and fetched as an
independent regular file. Its remote SHA-256 must match locally before archive
inspection or extraction. Exact-child cleanup runs even if the pipeline,
builder, transfer, or extractor fails; its receipt is returned independently
after deletion and must prove absence. Thus archive refusal cannot suppress
lease-release state or cleanup evidence.

Design validation is untimed, never sets `WEBP_BENCHMARK_SESSION`, never takes
the benchmark lease, and does not invoke the runner. The live roundtrip record
is frozen under `evidence/backref-cost-workspace-remote-v4-design/`.
