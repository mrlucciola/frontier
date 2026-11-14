# pm-wt-rewrite/04/04a pm integration: remove the unbuilt mechanism fc-2a6562:fc-d6c61c

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-a-unbuilt.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/04a pm integration: remove the unbuilt mechanism fc-2a6562:fc-d6c61c

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-a-unbuilt.md`

Ticket **fc-d6c61c**, first of five serial workers on its branch. Every verb is built
and every transcript passes. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first. Run
`pm ticket show fc-d6c61c` (the old pm, read-only) for the ticket body.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c`.

## Deliver

1. Remove `store.unbuilt` from `pm/tools/store.py` and every call to it under
   `pm/cli/` and `pm/tools/` (`rg -n 'unbuilt|PM_UNBUILT_LOG' pm/cli pm/tools` prints
   nothing afterwards). A verb in the dispatcher's table always has a file now; if
   one is missing, that is an internal error, not a pending verb.
2. Remove the pending-rule paragraph from `pm/AGENTS.md`, and make its gate command
   `/usr/bin/python3 -B pm/tests/run_transcripts.py` without `--allow-pending`. Run
   `python3 -B docs/check_structure.py`.

Do not edit `pm/tests/run_transcripts.py`; the overseer updates the runner.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py
rg -n 'unbuilt|PM_UNBUILT_LOG' pm/cli pm/tools
python3 -B docs/check_structure.py
```

The first exits 0 with `pending 0, failed 0`; the second prints nothing (exit 1);
the third passes.

## Report

Commit message `pm integration: remove the unbuilt mechanism`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-a-unbuilt.md`.
