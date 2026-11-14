# pm-wt-rewrite/02/00-6a wt characterization: review gaps in finish, land, teardown fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-6a-review-finish.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-6a wt characterization: review gaps in finish, land, teardown fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-6a-review-finish.md`

You are a worker on ticket fc-30c060, part 6a. You start with zero context. Your worktree
is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`;
the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway
under the test's temp root. Each new repo in a test gets its own store prefix (the new
pm's `init` registers prefixes and refuses a repeat).

## What exists

`WT/tests/test_wt_cli.py` and `WT/tests/run_wt.py`: a black-box suite of about 95 tests,
green against the old wt. Read the whole test file first and reuse its helpers
(`StartedCase.started`, the `post-rewrite` hook trick for ff-only retries, the `git`
shim via `wt(..., path_first=...)`, `faults()`). Keep its style: docstring quotes the
contract phrase; assert exit codes and the first words of wt's own lines; never pm's
text. Contract: `WT/docs/contract.md`. Old wt, read-only:
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`.

A read-only review compared the suite with the contract:
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-review.md`.
Read it. The overseer accepted its findings; this part closes these (6b does the rest):

1. **land refusals** (contract.md:38-41): `land` refuses a dirty worktree, a rebase
   conflict (auto-park) and ff-only exhaustion like `finish`; and `land` and
   `finish --keep-open` remove the branch too -- assert it in both existing land tests.
2. **gate on land** (58-63): `land` without `--no-gate` runs the gate; a failing gate
   refuses `land`.
3. **cross-repo guard** (39, 310-313): a `--repo`/`--store` call into another repo with
   no declared pair in the private `GIT_PAIRS_FILE` refuses with the `wt: cross-repo`
   line and mutates nothing. Overseer ruling: the behavior is kept; the new wt honors
   `GIT_PAIRS_FILE` with the same shape.
4. **never `branch -D`, `worktree remove --force`, `rm -rf`** (97-98): a logging `git`
   shim (passes everything to `/usr/bin/git`, appends its argv to a file) on a full
   start-finish, a start-park and a failed-remove run; assert no `branch -D` (any
   force spelling: `-D`, `--delete --force`, `-df`) and no `worktree remove` with
   `--force`/`-f`.
5. **fault rows** (99-103, 163-165): a failure that writes a fault row ends its `wt:`
   line with `(reported: <path>)`, the path exists under `$WT_FAULT_REPORT_DIR`, and the
   same failure twice adds no second row for the same root cause (pin how the old wt
   dedups). Pick the failures that write rows from `wt_core.py`.
6. **failed-remove shapes** (119-121): with the `git` shim, the dir-gone shape hands
   over `worktree prune`, and the `.git`-file-missing shape hands over `rm -rf` then
   prune. Pin each line's first words.
7. **STOP line text** (192): the `STOP.` line names the merge and the failed
   `git worktree remove`.
8. **ff-only retry count** (74-76): pin exactly three tries -- the hook counter after
   exhaustion, and that two moves are absorbed.
9. **NOT closed line** (156-162, test line 1099): the `OK: <id> merged` line itself
   carries `ticket NOT closed`, and ends with a command naming the ticket id (do not
   pin the pm command's words; they differ by side).
10. **deferred text** (181-186): the deferred line carries
    `This is infrastructure, not a finding: file no ticket and write no retro.`; the
    finish OK line carries `registration and branch deferred to wt prune, ticket closed`.
11. **fast-forward only** (test line 776-781): assert `git rev-list --merges <before>..main`
    is empty.
12. **happy path branch removal** (test line 771-772): the clean path must assert the
    branch is gone; only the deferred path may keep it, and the deferred path is
    exercised by `DeferredTeardownTest`, so drop the "deferred" escape from the happy test
    if the sandbox here deletes the admin dir (it did in every earlier run); if you keep
    an escape, assert the registration is prunable when it is taken.

A case that cannot run sandboxed goes in a new `WT/docs/uncovered.md` (case, why, exact
operator-terminal command). If the old wt contradicts the contract, pin the old wt and
name the test and the contract line in NOT DONE.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```

The first: `failed 0`, `pending 0`, `skipped 0`. The second (a stand-in wt that answers
every verb as unbuilt): `failed 0`; every wt test pending except the expected skips.
Paste each run's last two lines in EVIDENCE.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-6a-review-finish.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
