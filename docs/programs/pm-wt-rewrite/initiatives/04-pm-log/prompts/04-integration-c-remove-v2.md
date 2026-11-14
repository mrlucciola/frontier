# pm-wt-rewrite/04/04c pm integration: remove pm/v2 fc-2a6562:fc-d6c61c

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-c-remove-v2.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/04c pm integration: remove pm/v2 fc-2a6562:fc-d6c61c

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-c-remove-v2.md`

Ticket **fc-d6c61c**, third of five serial workers on its branch. A read-only
reviewer has confirmed what refers to `pm/v2/` (report
`reports/04-integration-c-review.md` in the worktree, verdict CONFIRMED). Read and
obey `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c`.

## Deliver

1. Before removing anything, record the size of the port and of the new tree:
   write `<worktree>/.tmp/sizes.py`, which counts source lines (non-empty, not
   counting docs or transcripts) under `pm/v2/cli`, `pm/v2/tools`, `pm/v2/tests`, and
   under `pm/cli`, `pm/tools`, `pm/plugins`, `pm/hooks`, and prints a table; paste it
   under EVIDENCE.
2. For each reference the review lists outside `pm/v2/` that is not a historical
   record (a program ledger, a report, a closed initiative), change it to what
   replaces it, or remove it. Name each under DID.
3. `git -C <worktree> rm -r pm/v2` in a commit of its own.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s pm/tests
python3 -B docs/check_structure.py
rg -n 'pm/v2' --glob '!docs/programs/**' .
```

The first three pass; the last prints nothing, or only lines you list under NOT DONE
with why each stays.

## Report

Commit messages `pm integration: references to the port` and
`pm integration: remove pm/v2`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-c-remove-v2.md`.
