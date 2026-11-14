# pm-wt-rewrite/01/01c pm core create and show fc-c3514f:fc-2b34c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-c-create-show.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/01c pm core create and show fc-c3514f:fc-2b34c9

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-c-create-show.md`

You are a worker on ticket **fc-2b34c9** (pm core), third of four serial workers on
its branch. Earlier workers built `pm/cli/pm`, `pm/tools/ticket`, `pm/tools/store.py`,
`pm/tools/verbs/init.py` and `pm/tools/gitcommit.py`; their reports are
`reports/01-core-a.md` and `reports/01-core-b.md` under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree. You build the
`create` and `show` verbs. Do only that.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9`, branch
  `fc-2b34c9`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`. If the worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop.
- Code standard: `docs/component-principles.md`. Read it first.

## Read first (selectively: budget is 80k tokens / 40 tool calls)

- The two reports, then `pm/tools/store.py` and `pm/tools/verbs/init.py` (the shape a
  verb file takes here).
- `pm ticket show fc-2b34c9`, body and notes. The overseer moved the duplicate guard
  into this ticket (note of 2026-11-13).
- `pm/docs/spec/v2/SPEC.md` sections 4 (rows, assignee identity, cross-store edge
  syntax) and 8 (`create` contract).
- Old source, read-only, at `/Users/matthias/frontier/runtime-tools/pm/ticket/src/`.
  Do not read whole files. `ticket`: 78-95 (`priority_type`), 146-157 (commit
  subject), 176-210 (`emit`, `fmt_line`, `claim_veto`), 268-381 (`is_remote_ref`,
  `edge_target`, `cmd_create`), 2014-2077 (`cmd_show`), 2830-2854 and 3039-3048
  (their parsers). `ticket_core.py`: 128-150 (title and label checks), 540-560
  (`now`, `make_note`), 562-623 (duplicate guard), 625-790 (session token and
  assignee identity), 2651-2658 (`projection_show`), and in `Store` the `new_id`,
  `is_ready`, `blockers_of`, `children`, `tombstone_row`, `archived_row`,
  `cross_blockers`, `cross_blocks_of` methods (find them with `rg -n`).

## Deliver

1. `pm/tools/verbs/create.py`: port of `cmd_create` with every flag in its parser,
   the same output, refusals and exit codes, including the whole duplicate guard
   (`find_duplicates` and its constants, the exit-2 `possible duplicate` refusal,
   `--json` candidates, `--new` marking `dedupe_overridden`, `--dup-of` sighting note
   of kind `finding`). `--discovered-from` to a row of this store, including a
   compacted or archived id, works; to a row in another store (a prefix this store
   does not own, `is_remote_ref`) it calls `store.unbuilt("cross-store-edge")`.
   Commit subject `pm: create <id>` as the old one builds it.
2. `pm/tools/verbs/show.py`: port of `cmd_show`, text and `--json`, `--notes`,
   `--all-notes` (edit-trail notes hidden behind one count line), archived rows
   (`archived: <path>`), compacted ids, `subtasks:`, the parent's title inline.
   Cross-store parts: a row with an edge whose target is `<prefix>/<id>` calls
   `store.unbuilt("routing")`; the reverse "blocks (other stores)" line calls
   `store.unbuilt("routing")` only when the registry file (`$PM_STORES_FILE`, else
   `~/.config/pm/stores.json`) exists and lists at least one store, else prints
   nothing. An id whose prefix this store does not own calls `store.unbuilt("routing")`.
   New surface: `--field <name>`, repeatable, reads the same object `--json`
   prints and writes one line per requested field in the order given: a string as
   is, a number as digits, a boolean as `true`/`false`, null as an empty line, a list
   of strings comma-joined with no spaces, anything else as compact JSON. An unknown
   field exits 1 with `pm: show: no field <name>` and the list of fields. `--field`
   with `--json` is an argparse error.
3. `pm/tools/store.py`, additive only: helpers that three or more kept verbs will
   call (title and label checks, `make_note`, assignee identity, `is_ready`,
   `blockers_of`, `children`). A helper only `create` or only `show` uses stays in
   that verb file. Change no existing function's signature; if you must, stop and
   report it.

Do not write `test_cli_contract.py`, `routing.py`, any doc, or a README. Do not edit
`pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or anything under `pm/docs/`;
a parity test that looks wrong goes in NOT DONE with its name and why. Never write
under `~/frontier`.

## Gate (run from the worktree root, all must pass)

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_create_show_roundtrip
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k DuplicateGuardTest -k test_archived_id_is_refused_as_archived_not_as_unknown -k test_create
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

The first must end `parity: passed 1, pending 0, failed 0, skipped 0`. The second must
end `failed 0`; paste its last lines including every `pending:` line. The last must exit
0 with `failed 0`; paste its `parity:` line and its `unbuilt verbs still needed:` line.
The full run takes about four minutes; run it once at the end.

## Report

Commit on `fc-2b34c9` with explicit `git add` paths, message `pm core: create and show
verbs (fc-2b34c9)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-c.md`,
commit it on the same branch, and print only that path.
