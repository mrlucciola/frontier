# pm-wt-rewrite/04/03c pm import and the import check fc-2a6562:fc-4a8593

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03c-import.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/03c pm import and the import check fc-2a6562:fc-4a8593

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03c-import.md`

Ticket **fc-4a8593**, one of three step-3 workers running in parallel. Every verb but
`hook` and `import` is built and merged. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first. Run
`pm ticket show fc-4a8593` (the old pm, read-only) for the ticket body. Your write
set is `pm/tools/verbs/import.py` and `pm/tests/import_check.py`; other workers edit
`pm/cli/pm`, `store.change` and `orient.py` in parallel.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-4a8593`.

## Read first

`pm/docs/design.md` "Import" and "Store"; transcript `19-import.t`; the fixture
`pm/tests/fixtures/v2/`; `pm/v2/docs/spec/v2/SPEC.md` (the row format, edges,
archive files); `pm/tools/store.py`.

## Deliver

1. `pm/tools/verbs/import.py` by the design's mapping table, including an epic's
   `subtasks` entries and the rows of `archive/tickets-*.jsonl`. It writes all events
   in one append through the store's lock, with each event's own `ts` and `by`
   (`import`, or the assignee as `<name>#<token>`, or `closed_by`), registers the
   prefix, and leaves the old files in place. It refuses a store with events, as
   transcript 19 shows. Note kinds of the old store are kept as they are.
2. `pm/tests/import_check.py` as the ticket body says: for each store in
   `~/frontier/runtime-tools/pm/stores.json`, copy its `.pm` directory into a
   temporary directory under this worktree's `.tmp/`, run this component's
   `pm import` there with `PM_STORES` pointing at a scratch file, and compare with the
   installed `pm` run on the same copy (`pm ticket list --json` with every status,
   `PM_TELEMETRY_DIR=-`, `PM_STORES_FILE` pointing at an empty registry). It never
   writes to a real store, `~/.config/pm` or `~/frontier`. Print each difference;
   exit 0 only when every store matches.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 19-import -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
/usr/bin/python3 -B pm/tests/import_check.py
```

The first exits 0 with `passed 1`. The second exits 0 with `failed 0` and no
`import` in its unbuilt line. The third exits 0; if a store cannot be read inside
the sandbox, list it in NOT DONE with the exact error and the operator command. An
import that would lose a ticket or a non-edit-trail note is a stop condition: report
it, do not paper over it.

## Report

Commit message `pm import: spec v2 to the log, and the import check`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-4a8593/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/03c-import.md`.
