# pm-wt-rewrite/02/02d wt verbs: status and prune fc-262fa8:fc-983ff4

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02d-status-prune.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/02d wt verbs: status and prune fc-262fa8:fc-983ff4

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02d-status-prune.md`

You are a worker on ticket fc-983ff4. You start with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4` on branch `fc-983ff4`; the
overseer created it after `start` merged, so `wt start` works in the suite.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
it binds you (rules, the core, the rulings, the gate, the report).

## Deliver

`wt/tools/verbs/status.zsh` and `wt/tools/verbs/prune.zsh` only. Read
`pm ticket show fc-983ff4` (the spec), the contract's `status` and `prune` lines and its
"Deferred teardown and prune" section (`wt/docs/contract.md`), the suite's
`StatusPruneTest`, the status and prune cases of `ResolutionTest` and
`DeferredTeardownTest.test_prune_clears_the_debt`, and the old `cmd_status`,
`cmd_prune` and `_prune_debt` in
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only).

- `status [--store S] [--repo R]`: the worktree list joined against tickets, one line per
  worktree as the old wt prints it, ticket status read with `wt_pm_get` (pm's words
  `open taken parked done`), bare entries skipped (`WT_WORKTREE_BARE`), a prunable
  registration labelled `deferred-teardown`, a worktree with no ticket shown as such.
- `prune [--store S] [--repo R]`: the lib's `wt_prune_debt` (not quiet), with its
  remaining-registrations operator line.
- `wt pending` is dropped; nothing to write for it.

## Gate

Per `02-common.md`. Classes that must have no pending or failed test: the status and
prune tests in `StatusPruneTest` (every test there except those whose first unbuilt
step is `park`, `finish` or `selftest`), `test_status_takes_store_and_repo_flags`,
`test_prune_takes_a_repo_flag`. Every other pending test must name a verb other than
`status` or `prune` as its first unbuilt step.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02d-status-prune.md`
