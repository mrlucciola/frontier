# pm-wt-rewrite/01/03c2 pm verbs reparent edit note fc-c3514f:fc-c10bcf

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c2-reparent-edit-note.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03c2 pm verbs reparent edit note fc-c3514f:fc-c10bcf

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c2-reparent-edit-note.md`

Ticket **fc-c10bcf** (structure verbs), second of two serial workers on its branch. The
first built `dep`, `unlink` and cross-store edges; its report is
`reports/03c1-dep-unlink-edges.md` under `docs/programs/pm-wt-rewrite/initiatives/01-pm/`
in the worktree. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf`.
- Spec: `pm ticket show fc-c10bcf` (body and notes).

## Deliver

`pm/tools/verbs/reparent.py`, `edit.py`, `note.py`: reparent between epics and
`--none`, refusing a non-epic parent, self and cycles; edit's atomic `--title`,
`--priority` (also `P<n>`), `--body`, `--append-body` (no doubled or leading blank
line; empty refused; with `--body` refused) with every previous value kept as a note of
kind `edit-trail`, nothing written on any refusal; note `<id> <text>`, `--text`,
`--kind` before or after the text, an unknown kind an argparse error (exit 2).

Old source by name: `ticket`: `cmd_reparent`, `cmd_edit`, `cmd_note`, their
`add_parser` blocks; `ticket_core.py`: `Store.would_parent_cycle`, `NOTE_KINDS`,
`make_note`. `store.py` already has `make_note`, `title_problem`, `label_problem`.

## Gate

The common gate with `-k reparent -k edit -k note`. The full run's `unbuilt verbs still
needed:` line names none of `dep`, `unlink`, `reparent`, `edit`, `note`.

## Report

Commit message `pm structure: reparent, edit, note (fc-c10bcf)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03c2-reparent-edit-note.md`.
