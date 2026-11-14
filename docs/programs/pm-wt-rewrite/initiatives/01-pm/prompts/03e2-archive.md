# pm-wt-rewrite/01/03e2 pm verb archive fc-c3514f:fc-913d02

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e2-archive.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03e2 pm verb archive fc-c3514f:fc-913d02

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e2-archive.md`

Ticket **fc-913d02** (checks and views), second of four serial workers on its branch.
The first built `validate`; its report is `reports/03e1-validate.md` under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02`.
- Spec: `pm ticket show fc-913d02` (body and notes).

## Deliver

`pm/tools/verbs/archive.py`: archive by ids and by `--closed-before <date>`, both
together as a filter, `--dry-run` writing nothing, the refusals (open row naming
`close`, unknown id, parent of a live child, a row after the cutoff, no ids and no date,
`<id>: already archived`), parent and child together, bulk skipping a parent of a live
child, the `tickets-<year>.jsonl` year file and `archive/archive-index.jsonl` (spec v2
section 6), and the index committed in the same commit as the ticket file through
`Store.extra_commit_paths`. A no-op archive (`--closed-before 2000-01-01` on a store
with no closed rows) writes and commits nothing.

Old source by name: `ticket`: `_archive_hint`, `_archive_select`,
`_archive_parent_reason`, `_archive_run`, `cmd_archive`, its `add_parser` block;
`ticket_core.py`: `archive_year_prefix`, `archive_year_filename`,
`archive_live_children`, `archive_fixed_point`, `archive_rows`, `commit_archive_index`,
`closed_before`, `ARCHIVE_INDEX_ROW_KEYS`. Leave the sweep (`sweep_closed`,
`_sweep_compact`) alone: it is deferred.

## Gate

The common gate with `-k archive -k test_no_op_mutation_does_not_commit`. The full run's
`unbuilt verbs still needed:` line names neither `validate` nor `archive`.

## Report

Commit message `pm checks: archive (fc-913d02)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e2-archive.md`.
