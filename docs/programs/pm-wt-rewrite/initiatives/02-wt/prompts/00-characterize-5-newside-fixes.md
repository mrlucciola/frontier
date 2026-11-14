# pm-wt-rewrite/02/00-5 wt characterization: new-side setup fixes fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-5-newside-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-5 wt characterization: new-side setup fixes fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-5-newside-fixes.md`

You are a worker on ticket fc-30c060, part 5, a small fix round. You start with zero
context. Your worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060`
on branch `fc-30c060`; the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 40k tokens or 20 tool calls. Read-only: everything under
`~/frontier`, `~/.local`, `~/.config/pm`, provider config dirs, and this repo's `pm/`.

## The problem

The suite (`WT/tests/test_wt_cli.py`, runner `WT/tests/run_wt.py`) is green against the
old wt. The overseer ran it on the new-pm side against a stand-in wt that answers every
verb as unbuilt (exit 70, verb appended to `$WT_UNBUILT_LOG`):

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```

It printed `wt suite: passed 9, pending 83, skipped 1, failed 8`. Every test must be
pending or passed there (the one skip, `test_pending_lists_done_unmerged_with_cleared_blockers`,
is expected). The 8 failures are two bugs in the suite, not in wt:

1. **`FinishTest.test_every_refusal_names_a_next_step`** runs its cases as `subTest`s.
   (a) Each case's `make_repo` uses prefix `tk`; the new pm's `pm init` registers the
   prefix in the private `$PM_STORES` and refuses a second store with the same prefix
   (`pm: prefix tk belongs to .../repos/r1. Choose another.`). Give each case its own
   prefix. Check every other test that builds more than one repo for the same issue.
   (b) A `Pending` raised inside a `subTest` is reported as an ERROR, not as pending.
   Make the runner count it as pending (the test is pending if any subtest is pending
   and none failed before its unbuilt call), or restructure so it cannot happen. Keep
   the rule of `PLAN.md` "The pending rule": a failure before any unbuilt call is a
   failure.
2. **`ResolutionTest.test_two_owners_stop_with_a_wt_line`**: the new pm has no "two
   owners" error. A prefix may sit on several registry lines and pm routes the id itself
   (`/Users/matthias/projects/frontier-clean/pm/docs/design.md`, "Ids and the
   registry"). Overseer ruling: this case is old-side only. On the new side it skips
   itself with the reason `the new pm routes a shared prefix itself (design.md, Ids and
   the registry)`. Its docstring says so.

Change nothing else. Do not change what any test asserts against the old wt.

## Gate

Both must hold; paste each run's last two lines in EVIDENCE:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```

The first: `failed 0`, `pending 0`, `skipped 0`. The second: `failed 0`, `skipped 2`
(pending and two owners), every other wt test pending.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-5-newside-fixes.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
