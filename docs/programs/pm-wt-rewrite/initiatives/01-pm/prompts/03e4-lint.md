# pm-wt-rewrite/01/03e4 pm verb lint fc-c3514f:fc-913d02

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e4-lint.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03e4 pm verb lint fc-c3514f:fc-913d02

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e4-lint.md`

Ticket **fc-913d02** (checks and views), last of four serial workers on its branch.
Earlier workers built `validate`, `archive`, `board`, `overview`; their reports are
under `docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/` in the worktree. Read and
obey `docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02`.
- Spec: `pm ticket show fc-913d02` (body and notes: `lint <id>` and the pilot contract
  were added upstream after the body was written).

## Deliver

`pm/tools/verbs/lint.py`: `validate`'s output and exit code first, then one
`WARN stale-path <id> <path>` per missing path cited in an open ticket body and one
`WARN local-path <id> <path>` per path under the repo's `.local/` dump; warnings never
change the exit code and go to stderr under `--json`; none under `--workspace` or for an
unopenable store. The pilot contract: P-01 for an open ticket labelled `pilot` whose
body `review_by:` line is missing, unparsable or past, P-02 for a closed one lacking a
`measured:` or `ruling:` note; these are lint problems (exit 1), not validate's.
`lint <id>`: the dispatch-heading check whose rule `pm/docs/cut-list.md` quotes
(`missing: <heading>` lines and exit 1, or `dispatchable` and exit 0; unknown id exit 1).

Old source by name: `ticket`: `cmd_lint`, its `add_parser` block; `ticket_core.py`:
`_BODY_PATH_RE`, `_ABS_PATH_RE`, `_PLANNED_RE`, `_TRANSIENT_SEGMENTS`,
`LOCAL_DUMP_DIR`, `_body_path_tokens`, `body_path_warnings`, `stale_body_paths`,
`DISPATCH_HEADINGS`, `missing_dispatch_headings`, `_pilot_review_by`, `_pilot_tickets`,
`pilot_problems`. The pilot helpers are used by `summary` too, on another branch; by
component principle 2 (two verbs) lint keeps its own copy in `lint.py`. Reuse
`validate.py`'s functions by importing them from `verbs.validate` only if the old code
shares them the same way; otherwise move what both need into `store.py`.

## Gate

The common gate with `-k lint`. The full run's `unbuilt verbs still needed:` line names
none of `validate`, `archive`, `board`, `overview`, `lint`.

## Report

Commit message `pm checks: lint (fc-913d02)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e4-lint.md`.
