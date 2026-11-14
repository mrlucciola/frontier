# pm-wt-rewrite/01/03e3 pm verbs board overview fc-c3514f:fc-913d02

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e3-board-overview.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03e3 pm verbs board overview fc-c3514f:fc-913d02

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03e3-board-overview.md`

Ticket **fc-913d02** (checks and views), third of four serial workers on its branch.
Earlier workers built `validate` and `archive`; their reports are under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/` in the worktree. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02`.
- Spec: `pm ticket show fc-913d02` (body and notes).

## Deliver

1. `pm/tools/verbs/board.py` and `overview.py`: ports of the old renderers, reached as
   `pm ticket board|overview` and `pm view board|overview`, with the same flags and
   output. Both render the old `project()` projection; it has no other user, so build
   it in the verb that needs it, or in `store.py` if both do (they do: put `project`
   there, under that name, with its frozen shape).
2. `pm/tests/test_views.py`: the old view tests ported to drive the CLI as a subprocess
   (component principle 5), not to import the renderers.

Old source by name: `/Users/matthias/frontier/runtime-tools/pm/view/src/board.py` (198
lines) and `overview.py` (165 lines), read whole; their tests
`/Users/matthias/frontier/runtime-tools/pm/view/tests/test_board.py` and
`test_overview.py`; `ticket`: `cmd_board`, `cmd_overview`, their `add_parser` blocks;
`ticket_core.py`: `project`, `PROJECTION_VERSION`.

## Gate

The common gate with `-k board -k overview`, plus
`/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_views.py'`. The full
run's `unbuilt verbs still needed:` line names none of `validate`, `archive`, `board`,
`overview`.

## Report

Commit message `pm views: board, overview (fc-913d02)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e3-board-overview.md`.
