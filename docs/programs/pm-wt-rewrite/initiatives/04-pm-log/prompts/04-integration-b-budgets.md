# pm-wt-rewrite/04/04b pm integration: budgets and concurrency tests fc-2a6562:fc-d6c61c

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-b-budgets.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/04b pm integration: budgets and concurrency tests fc-2a6562:fc-d6c61c

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-b-budgets.md`

Ticket **fc-d6c61c**, second of five serial workers on its branch. The unbuilt
mechanism is gone (report `04-integration-a-*`). Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c`.

## Read first

`pm/docs/design.md` "Size budgets", "Store" (the lock) and "Harness hooks";
`pm/tests/run_transcripts.py` (how it isolates the environment: copy that, do not
import it).

## Deliver

1. `pm/tests/test_budgets.py`, `unittest`, black-box: each ceiling of the design's
   table measured by running `pm/cli/pm` in a temporary store with the transcript
   environment: `pm help`; every `pm help <verb>` for the verbs in the help table;
   every refusal the transcripts print (collect them by running the transcripts'
   refusal commands, or list a representative set of at least ten, one per verb that
   refuses); bare `pm` with 2 held, 8 ready, 3 parked; `pm hook session-start` on
   the same store. Each failure message names the output and its size.
2. `pm/tests/test_concurrency.py`, `unittest`, black-box: twenty processes run
   `pm new` at once in one store: twenty distinct ids and twenty well-formed log
   lines; two processes `pm take` the same ticket: exactly one exits 0.
3. Print every measured size once (a `-v` run shows them, or a summary line per
   output); the overseer copies them into the close note.

A ceiling that the current output exceeds is a finding, not a reason to raise the
ceiling: report the output, its size and the ceiling in NOT DONE, and leave that test
failing.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests -v
/usr/bin/python3 -B pm/tests/run_transcripts.py
```

## Report

Commit message `pm integration: byte budgets and concurrency tests`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-b-budgets.md`,
with every measured size under EVIDENCE.
