# Backref-cost workspace remote v5 design

V5 resolves v4's missing-CMake admission blocker without changing the
recorder-free CostManager candidate. Integer costs, strict ties, update order,
ten inline plus 490 allocated nodes, traceback, reference/cache order, and
transactional allocation-failure fallback are unchanged. V5 uses wholly new
build, compile, and exact runtime gates and remains absent from ordinary builds.

The runner's noninteractive PATH is frozen as `/usr/bin:/bin:/usr/sbin:/sbin`.
The build admits explicit Xcode 26.3 clang/clang++, ar/ranlib, macOS SDK 26.2,
GNU make 3.81, xcrun, git, Python, and shasum by exact path, canonical target,
executable type, SHA-256, version output where meaningful, and an effective
compiler/SDK object probe. Missing-make and wrong-make fixtures must refuse.
No CMake or Homebrew executable is used. Two clean local clones are built
serially with `makefile.unix`; compile and link commands carry explicit arm64
and SDK flags. V5's deterministic make mode suppresses Homebrew, MacPorts, SDL,
and Metal discovery for these two builds only.

The operator creates `evidence/lease-record.json` before admission and writes
`refusal.json`, `operator-status.json`, and the complete sorted
`artifact-hashes.json` on every controlled exit. Thus a toolchain, build,
preflight, correctness, timing, or resource refusal remains a valid indexed
archive. Lease return, archive return, and exact-child cleanup remain three
independent hash-verified channels.

The v4 archive policy is retained and made explicit for Apple metadata: only
canonical-contained real directories and single-link regular files are
accepted. Symlinks, hardlinks, devices, FIFOs, absolute/traversing/non-normal
names, AppleDouble/`__MACOSX`, PAX/xattr metadata, filesystem xattrs, unknown
files, and containment escapes refuse. Inventory is complete before any write;
extraction stages all content and removes the stage on refusal. Rejected
archives are quarantined with digests, inventory, member, and reason.

Untimed design validation never sets `WEBP_BENCHMARK_SESSION`, acquires the
benchmark lease, or invokes the timed runner. It may create only a validated
temporary child under the v5 safe root and must return an exact-child absence
proof. Any `Runner.Worker` or benchmark/CUDA conflict refuses immediately.

The frozen live rehearsal admitted and built both variants with seven exact
commands, passed all 26 remote correctness cells, and returned a seven-member
indexed archive. Missing-make and wrong-make fixtures both refused. A separate
missing-make controlled exit returned four indexed members, including the
minimal lease, refusal, and operator-status records. Both run children were
removed with independent absence proofs. The general security rehearsal
returned six members, rejected three unsafe builder trees and five malicious
archives with no partial extraction, and proved exact cleanup. The read-only
inspection found Homebrew CMake 4.4.2 at `/opt/homebrew/bin/cmake`, but v5 does
not admit or invoke it; the repository makefile path is sufficient.
The rehearsal source commit `ed18da115e234c13ef383ea08291e1eaecb235b7`
exists only in a disposable repository copy and is ineligible for performance;
it differs from the final handoff only in subsequently frozen design evidence,
schema links, documentation, and tests, not candidate or build behavior.
