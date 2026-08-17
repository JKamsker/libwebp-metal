# Upstream libwebp rebase procedure

The fork maintainer owns the monthly upstream check and the rebase. A second
maintainer reviews the range-diff and validation evidence. Run it during the
first week of each month, before every fork release, and immediately when
upstream publishes a relevant security fix. If there is no upstream delta,
record the checked upstream commit in the maintenance issue and stop.

The canonical remotes are:

```text
origin    https://github.com/JKamsker/libwebp-metal.git
upstream  https://github.com/webmproject/libwebp.git
```

Do not rebase with a dirty tree, delete release tags, or force-update `main`
without a reviewed backup reference. Downstream users must treat fork release
tags as stable and `main` as a rebased development branch.

## Prepare and rebase

1. Open a maintenance issue named `Upstream rebase YYYY-MM` and assign the fork
   maintainer plus reviewer. Link the upstream compare/log and note any
   security advisories.
2. Confirm remotes and a clean tree:

   ```sh
   git remote get-url origin
   git remote get-url upstream
   git status --short
   git fetch --prune origin
   git fetch --prune upstream
   ```

3. From current `origin/main`, create both a recoverable backup and the work
   branch. Never move an existing release tag:

   ```sh
   git switch --detach origin/main
   git branch backup/pre-rebase-YYYYMMDD
   git push origin backup/pre-rebase-YYYYMMDD
   git switch -c codex/rebase-upstream-YYYYMMDD
   old_base=$(git merge-base HEAD upstream/main)
   git log --oneline --reverse "$old_base"..HEAD
   git rebase --onto upstream/main "$old_base"
   ```

4. Resolve conflicts semantically against current upstream contracts; do not
   restore old upstream code just to make the Metal patch apply. For each
   resolution, inspect `git diff --check` and continue with
   `git rebase --continue`. Abort with `git rebase --abort` if the upstream API
   or encoder behavior needs a design decision.
5. Compare the old and new patch stacks and save the output with the issue/PR:

   ```sh
   old_base=$(git merge-base backup/pre-rebase-YYYYMMDD upstream/main)
   new_base=$(git merge-base HEAD upstream/main)
   git range-diff "$old_base"..backup/pre-rebase-YYYYMMDD \
     "$new_base"..HEAD
   git diff --check
   git diff --stat upstream/main...HEAD
   ```

The highest conflict-risk areas are `CMakeLists.txt` and `makefile.unix` source
lists/link language; private encoder contracts in `src/enc/predictor_enc.c`,
`src/enc/backward_references_enc.c`, and `src/enc/picture_csp_enc.c`; progress,
allocation, and fallback behavior around those calls; shared declarations in
`src/enc/metal_enc.h`; and upstream DSP/RTCD changes near
`src/dsp/lossless_enc_metal.mm`. Also inspect `.github`, `scripts`, and these
documents for upstream file renames even when Git reports no conflict.

Item 6 may move calls behind a backend-neutral interface. After that lands, use
its dispatcher, lifecycle, and capability tests as the conflict authority; do
not reintroduce direct Metal calls during a rebase. Item 1 may revise the
performance case set and must finish before declaring a new performance
baseline representative, but it does not block correctness validation.

## Validation gates

Run gates in this order and attach links or logs to the maintenance issue:

1. Review all upstream release notes/security changes between old and new base.
2. Run `git diff --check`, portable `Correctness`, and both Metal-disabled and
   Metal-enabled CMake builds.
3. Run `Metal correctness` on the physical runner. It must observe transform,
   hash-candidate, and lossy-import GPU log markers; CPU fallback alone is not
   a pass.
4. Check public ABI/symbol and installed-package output if upstream touched
   headers, visibility, CMake exports, or library composition.
5. Only after correctness is green, run `Metal performance signal` on the idle
   characterized runner. Compare against the last accepted pre-rebase baseline.
   Apply the warning/critical triage policy in `ci-performance.md`; do not hide
   a signal by accepting a new baseline.
6. Reviewer signs off the range-diff, conflict resolutions, raw environment
   metadata, and validation matrix.

## Publish and recover

Push the work branch normally and review it before updating `main`. Because the
fork keeps a short patch stack directly above upstream, the final update is an
intentional history rewrite:

```sh
git push -u origin codex/rebase-upstream-YYYYMMDD
expected_old_main=$(git rev-parse backup/pre-rebase-YYYYMMDD)
git push --force-with-lease=main:"$expected_old_main" origin HEAD:main
```

Confirm that `expected_old_main` is the exact reviewed old `origin/main` SHA;
never omit the lease. Temporarily allowing that one reviewed update may require
a branch protection administrator. Immediately restore protection, fetch
`origin/main`, verify it equals the reviewed SHA, and create a fork release tag
only through the normal release process. If post-publish validation fails,
restore the backup SHA with another reviewed `--force-with-lease` update and
reopen the maintenance issue; the backup branch is not a release artifact and
may be deleted only after the next successful rebase.

Final checklist:

- [ ] issue, owner, reviewer, old base, new base, and upstream range recorded
- [ ] conflicts and range-diff reviewed, with no old CPU implementation revived
- [ ] portable and physical-Metal correctness gates green
- [ ] ABI/package checks completed when applicable
- [ ] performance result triaged and raw artifacts linked
- [ ] exact lease SHA used; branch protection restored
- [ ] downstream-visible rebase note published
- [ ] next monthly check assigned
