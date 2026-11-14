# pm-wt-rewrite/04/01d pm log core: render, show and stores fc-2a6562:fc-dac416

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-d-render.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/01d pm log core: render, show and stores fc-2a6562:fc-dac416

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-d-render.md`

Ticket **fc-dac416**, last of four serial workers on its branch. The dispatcher, the
store, identity, the registry, `init` and `new` exist (reports `01-core-a-*` to
`01-core-c-*` in the worktree's `reports/`). You write the output side and the verbs
`show` and `stores`, then prove the whole ticket's gate. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first,
especially "Module contract".

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416`.

## Read first

`pm/docs/design.md` sections "Output" (all of it) and "Verbs"; transcripts
`01-init.t`, `02-new-show.t`, `10-epic.t`, `12-default-id.t`; the store, who and
registry modules as the previous worker left them.

## Deliver

1. `render.line(t, tickets)` and `render.show(t, tickets, all_notes=False)` in
   `pm/tools/render.py`, implementing every line the design's "show and take"
   paragraph lists, in its order, with the note rules and the last-five heading.
   A `blocked by` or `blocks` entry whose target is in another store is a later
   ticket: treat a target not in `tickets` as not done.
2. `pm/tools/verbs/show.py`: `pm show [id] [--notes] [--json]`; `--json` calls
   `store.unbuilt("json")`.
3. `pm/tools/verbs/stores.py`: `pm stores`, one `<prefix>  <path>` line per registry
   line, with `  ro` after a read-only one.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 01-init -k 02-new-show
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The first must exit 0 with `passed 2, pending 0, failed 0`. The second must exit 0
with `failed 0`; paste its full `-v` output. Then read every transcript that is
pending and check whether its first wrong step is really where an unbuilt verb was
called, not a wrong output from `init`, `new`, `show`, `stores` or `help` that the
pending status hides: for each transcript, the steps before its first unbuilt call
must all match. Name any that do not in NOT DONE, with the step.

## Report

Commit message `pm log core: render, show and stores`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/01-core-d-render.md`.
