# pm-wt-rewrite/01/03b1 pm verbs list ready fc-c3514f:fc-739601

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b1-list-ready.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03b1 pm verbs list ready fc-c3514f:fc-739601

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03b1-list-ready.md`

Ticket **fc-739601** (read verbs), first of two serial workers on its branch; the second
builds `tree` and `summary`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-739601`.
- Spec: `pm ticket show fc-739601` (body and notes).

## Deliver

`pm/tools/verbs/list.py` and `ready.py`: `list --status` (repeatable), `--label`,
`--all-stores` (rows gain `store` under `--json`; a frozen or unreadable registered store
is named on stderr as `skipped <path>: frozen` and left out), `ready --scope` (epic
subtree or label; neither is an error) and `--limit`, readiness across cross-store
blocked-by edges failing closed on an unresolved target, the frozen one-liner on a
frozen store, and every `--json` shape exactly as the old projections.

Old source by name: `ticket`: `cmd_ready`, `_list_all_stores`, `cmd_list`, their
`add_parser` blocks; `ticket_core.py`: `scope_filter`, `projection_ready`,
`projection_list`, `frozen_notice`. `store.py` has `fmt_line` and `is_ready`;
`routing.py` has the registry and frozen notice; reuse them.

## Gate

The common gate with `-k list -k ready`. The full run's `unbuilt verbs still needed:`
line names neither `list` nor `ready`.

## Report

Commit message `pm reads: list, ready (fc-739601)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03b1-list-ready.md`.
