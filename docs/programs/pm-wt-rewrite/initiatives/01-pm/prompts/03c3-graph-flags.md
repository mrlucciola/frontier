# pm-wt-rewrite/01/03c3 pm create --blocks/--blocked-by, dep several targets and --note fc-c3514f:fc-c10bcf

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c3-graph-flags.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03c3 pm create --blocks/--blocked-by, dep several targets and --note fc-c3514f:fc-c10bcf

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c3-graph-flags.md`

Ticket **fc-c10bcf** (structure verbs), third worker on its branch. Earlier workers
built `dep`, `unlink`, cross-store edges, `reparent`, `edit`, `note` (reports `03c1-*`
and `03c2-*` under `docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/` in the
worktree). The overseer has since rebased the branch onto main, which now has
`claim hold release close reopen`, `history`, and three parity tests ported from
upstream frontier `944f3cda`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf`.
- Spec: `pm ticket show fc-c10bcf`, the newest note (fr-d7890d).

## Deliver

1. Upstream `944f3cda`: `create --blocks <id>` (repeatable) and `--blocked-by <id>`
   write the edges in the same call; `dep SRC blocks|related DST [DST...]` takes
   several targets; `dep --note TEXT` lands a note on the target. All of it is
   all-or-nothing: an unknown id or a cycle writes nothing. Read the old `cmd_create`,
   `cmd_dep` and their parsers at that commit with
   `git --no-pager -C /Users/matthias/frontier show 944f3cda -- runtime-tools/pm/ticket/src/ticket`.
   Parity tests: `test_dep_blocks_several_targets_all_or_none`,
   `test_dep_related_note_lands_on_target`,
   `test_create_writes_blocks_and_blocked_by_edges`.
2. `edit.py` imports `priority_type` from `verbs/create.py`; a verb file never imports
   another verb file. Move `priority_type` to `store.py` and have both call it there.
3. Tests of `dep`, `unlink`, `reparent`, `edit`, `note` and `CrossStoreEdgeTest`,
   `DuplicateGuardTest` that were pending on `claim`/`close` now run. Make every one of
   them that fails pass, in your verb files, `create.py`, or additively in `store.py`/
   `routing.py`. A failure caused by a verb still unbuilt stays pending; one caused by a
   merged verb outside your write set goes in NOT DONE with the test name and cause.

## Gate

The common gate with `-k dep -k unlink -k reparent -k edit -k note -k CrossStoreEdgeTest -k DuplicateGuardTest -k test_create`.
Paste every `pending:` line of the narrow run. The full run's `unbuilt verbs still
needed:` line names none of `dep`, `unlink`, `reparent`, `edit`, `note`,
`cross-store-edge`.

## Report

Commit message `pm structure: create --blocks/--blocked-by, dep several targets and --note (fc-c10bcf)`.
Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03c3-graph-flags.md`.
