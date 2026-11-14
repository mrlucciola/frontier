# pm-wt-rewrite/01/03b2 pm verbs tree summary fc-c3514f:fc-739601

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b2-tree-summary.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03b2 pm verbs tree summary fc-c3514f:fc-739601

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b2-tree-summary.md`

Ticket **fc-739601** (read verbs), second of two serial workers on its branch. The first
built `list` and `ready`; its report is `reports/03b1-list-ready.md` under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-739601`.
- Spec: `pm ticket show fc-739601` (body and notes).

## Deliver

`pm/tools/verbs/tree.py` and `summary.py`: tree's impacts, blocked-by chain (remote
blockers as leaves) and epic subtree, refusing an archived id with the old text;
summary's sections (semaphores, in flight, unmerged/parks, stale holds only when the
session is gone, waiting on other stores in text only, the frozen one-liner, the dirty
store line and the history-behind note, `pilots overdue: <ids>` only when there are
some) and `--limit`, and every `--json` shape. Summary must not write: a history
catch-up it owes is `store.unbuilt("history")` until fc-c5e673 merges, unless
`gitcommit.py` already offers it.

Old source by name: `ticket`: `cmd_tree`, `_store_dirty_line`, `cmd_summary`, their
`add_parser` blocks; `ticket_core.py`: `projection_tree`, `projection_summary`,
`Store.is_semaphore`, `Store.walk`, `overdue_pilots`, `_pilot_tickets` and
`_pilot_review_by`. Only `summary` and `lint` use the pilot helpers, two verbs, so
by component principle 2 they live in `summary.py`; the lint worker keeps its own.

## Gate

The common gate with `-k tree -k summary -k HelpTextTest -k test_lint_and_summary_enforce_the_pilot_contract`.
The full run's `unbuilt verbs still needed:` line names none of `list`, `ready`, `tree`,
`summary`.

## Report

Commit message `pm reads: tree, summary (fc-739601)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03b2-tree-summary.md`.
