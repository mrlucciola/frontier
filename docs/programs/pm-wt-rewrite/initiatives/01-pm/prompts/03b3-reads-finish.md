# pm-wt-rewrite/01/03b3 pm read verbs finish: summary catch-up, now-runnable tests fc-c3514f:fc-739601

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b3-reads-finish.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03b3 pm read verbs finish: summary catch-up, now-runnable tests fc-c3514f:fc-739601

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b3-reads-finish.md`

Ticket **fc-739601** (read verbs), third worker on its branch. Earlier workers built
`list`, `ready`, `tree`, `summary` (reports `03b1-list-ready.md` and
`03b2-tree-summary.md` under `docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/`
in the worktree). The overseer has since rebased the branch onto main, which now has
`claim hold release close reopen` and `history`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-739601`.

## Deliver

1. `summary`'s history catch-up: today an owed snapshot (the `history-pending` marker
   on a `history_ref` store) calls `store.unbuilt("history")`. Build it as the old
   `cmd_summary` and `_store_dirty_line` do, using `gitcommit.commit_store` (merged
   from fc-c5e673); `summary` still writes nothing else. Parity test:
   `HistoryCliTest.test_summary_catches_up_a_pending_snapshot`.
2. Tests of `list`, `ready`, `tree`, `summary` that were pending on `claim`/`close` now
   run. Make every one of them that fails pass, in the four verb files or additively in
   `store.py`/`routing.py`. A failure caused by a verb outside this ticket (still
   unbuilt `dep`, `validate`, `lint`, ...) stays pending; one caused by a merged verb
   outside your write set goes in NOT DONE with the test name and the cause.

## Gate

The common gate with `-k list -k ready -k tree -k summary -k test_summary_catches_up`.
Paste every `pending:` line of the narrow run. The full run's `unbuilt verbs still
needed:` line names none of `list`, `ready`, `tree`, `summary`, `history`.

## Report

Commit message `pm reads: summary history catch-up; now-runnable read tests (fc-739601)`.
Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03b3-reads-finish.md`.
