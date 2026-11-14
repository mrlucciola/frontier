# pm-wt-rewrite/02/02a wt verb: start fc-262fa8:fc-8ecb48

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02a-start.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/02a wt verb: start fc-262fa8:fc-8ecb48

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02a-start.md`

You are a worker on ticket fc-8ecb48. You start with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48` on branch `fc-8ecb48`; the
overseer created it.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
it binds you (rules, the core, the rulings, the gate, the report).

## Deliver

`wt/tools/verbs/start.zsh` only. Read `pm ticket show fc-8ecb48` (the spec), the
contract's `start` lines (`wt/docs/contract.md`), the suite's `StartTest` and every other
test that calls `wt start` (all of them do: your verb is every test's first step), and
the old `cmd_start` and `_own_claim_assignees` in
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only).

What start does, in the order the old `cmd_start` does it: parse `<id> [--as NAME]
[--session ID] [--store PATH] [--repo PATH] [--force]` (`--as` defaults to `$WT_ACTOR`;
`--session` defaults to `$PM_SESSION_ID`, then `$CODEX_THREAD_ID`); resolve store and
target repo; run the cross-repo guard; quiet prune; refuse a branch whose tip is a
mass-deleting `WIP: park` commit; adopt the ticket when it is already held with the same
actor and token (one `adopting existing claim on <id>` line), else take it with
`pm take` (passing `--force` and printing the park-not-finish reminder when forced),
refusing with `wt: ticket <id> is not claimable` and pm's reason when pm refuses; add or
resume the worktree at `<repo>/.worktrees/<id>` on branch `<id>` (resume rebases onto
the default branch; a conflict re-parks, as the old wt does, see fc-f0cc16); append the
restart hint when `git worktree add` fails with `.git/worktrees` and `Operation not
permitted`; `pm emit <id> wt.start branch=<id> path=<worktree>`; print
`OK: <id> -> <worktree>`. Undo the take when the worktree cannot be added, as the old
wt does.

## Gate

Per `02-common.md`. Classes that must have no pending or failed test: `StartTest`.
Every other pending test must name a verb other than `start` as its first unbuilt step.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02a-start.md`
