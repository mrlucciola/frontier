# pm-wt-rewrite/01/03e1 pm verb validate fc-c3514f:fc-913d02

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e1-validate.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03e1 pm verb validate fc-c3514f:fc-913d02

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e1-validate.md`

Ticket **fc-913d02** (checks and views), first of four serial workers on its branch;
later ones build `archive`, `board` and `overview`, then `lint`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02`.
- Spec: `pm ticket show fc-913d02` (body and notes).

## Deliver

1. `pm/tools/verbs/validate.py`: invariants I-01 to I-19 with the old problem lines,
   numbered operator steps and exit codes (0 clean, 1 problems, 2 no or unparsable
   store), `--json` (one document, also without a store), `--workspace` fan-out over a
   `.code-workspace` file (JSONC with trailing commas), `.pm/history-pending` as a store
   entry and not an I-01 problem, pre-v2 configs reported as I-02. `validate` does its
   own raw load: `Store` refuses pre-v2 stores and does not catch malformed rows, so
   read the files directly where the old code did (`_open_store_for_validate`);
   `Store.rows` has `(lineno, obj)` for a loadable store.
2. Fix hints that named a dropped verb get new text: I-02 on a pre-v2 config and a
   missing required key (old: `run: pm ticket upgrade`), I-10 unsorted labels (old:
   `run: pm ticket fix-labels <id>`). Write a hint that names a command that exists
   (for a pre-v2 store, the old pm's upgrade by its path, as `store.py`'s refusal does).
   Record the three old and new texts in `pm/docs/cut-list.md` under "What the cuts
   change", in the existing bullet about fix hints.

Old source by name: `ticket`: `_relpath`, `_open_store_for_validate`,
`_target_spec_version`, `_validate_one`, `_validate_json`, `_print_json`,
`_print_validate_result`, `_parse_jsonc`, `discover_workspace_repos`, `cmd_validate`,
`_cmd_validate_workspace`, the `validate` `add_parser` block; `ticket_core.py`:
`Problem`, `schema_check` and its helpers, `backfill_missing_keys`, `Store.validate`,
`_validate_config`, `_validate_duplicate_ids`, `_validate_row`,
`_validate_blocks_cycles`, `_validate_archive`, `read_archive_index`. The JSON schemas
are `pm/docs/spec/v2/ticket.schema.json` and `config.schema.json` (read-only; load
them from there). This is a large worker: if the budget runs out, land single-store
`validate` first and report `--workspace` in NOT DONE.

## Gate

The common gate with `-k ValidateTest -k validate`, plus
`/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'`'s
validate-hint case now running, not skipped. The full run's `unbuilt verbs still
needed:` line does not name `validate`.

## Report

Commit message `pm checks: validate (fc-913d02)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e1-validate.md`.
