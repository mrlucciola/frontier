# pm-wt-rewrite/05/02 back up only a store at the top of its checkout fc-359b5b:fc-c8212a

```
cd ~/projects/frontier-clean/.worktrees/fc-c8212a && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/02-backup.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-c8212a worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/05/02 back up only a store at the top of its checkout fc-359b5b:fc-c8212a

`docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/02-backup.md`

You are a worker for ticket **fc-c8212a** (epic fc-359b5b), starting with zero
context. The worker brief binds you:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first, then `pm ticket show fc-c8212a`.

Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a`, branch
`fc-c8212a`. Edit only under it, and use `git -C <worktree>` for git. Never run `wt`,
never merge, never run `pm ticket close|note|claim`. Never delete or move any
`refs/pm/log` in a real repository; the runbook does that.

**Spec:** `pm/docs/design.md` "Backup". Back up only when the store's directory is the
top of its git checkout, as `git rev-parse --show-toplevel` reports it, compared as
real paths. The same condition decides whether `pm doctor` prints a backup line, and
whether `pm restore` runs or refuses with the design's exact text. A linked worktree's
store is the main checkout's, which is at its top. Keep the rule in one function in
`pm/tools/store.py` and use it from all three callers.

**Gate:** the extended transcript `pm/tests/t/18-backup.t`, which the overseer
committed on your branch. Never edit the design, `pm/tests/t/` or
`pm/tests/fixtures/`. If one looks wrong, stop and report it.

**Write set:** `pm/tools/store.py`, `pm/tools/verbs/doctor.py`,
`pm/tools/verbs/restore.py`.

Run each of these once, by absolute path, from the worktree root:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tests
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/docs/check_structure.py
```

The transcripts must end with `failed 0`. The structure check may report only
`pm/README.md:76`.

Stop at 80k tokens or 40 tool calls. Commit with explicit `git add` paths; the message
ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report in
the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/02-backup.md`,
commit it, and print only that path.
