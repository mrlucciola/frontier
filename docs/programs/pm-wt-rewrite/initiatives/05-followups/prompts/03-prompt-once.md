# pm-wt-rewrite/05/03 pm hook prompt mentions each ticket once per session fc-359b5b:fc-d3d87b

```
cd ~/projects/frontier-clean/.worktrees/fc-d3d87b && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/03-prompt-once.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-d3d87b worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/05/03 pm hook prompt mentions each ticket once per session fc-359b5b:fc-d3d87b

`docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/03-prompt-once.md`

You are a worker for ticket **fc-d3d87b** (epic fc-359b5b), starting with zero
context. The worker brief binds you:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first, then `pm ticket show fc-d3d87b`.

Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b`, branch
`fc-d3d87b`. Edit only under it, and use `git -C <worktree>` for git. Never run `wt`,
never merge, never run `pm ticket close|note|claim`.

**Spec:** `pm/docs/design.md` "Harness hooks", the `prompt` row. Shown ids go in
`$TMPDIR/pm-mentioned-<token>`, one per line, where the token is the session token
from `tools/who.py`. Use `tempfile.gettempdir()` when `$TMPDIR` is unset. With no
token, nothing is kept. A failed read or write still prints the lines. Update the
module docstring, which is `pm help hook`, in one sentence; it must stay under the
700-byte help ceiling in `pm/tests/test_budgets.py`.

**Gate:** the extended transcript `pm/tests/t/16-hook.t`, which the overseer committed
on your branch. Never edit the design, `pm/tests/t/` or `pm/tests/fixtures/`. If one
looks wrong, stop and report it.

**Write set:** `pm/tools/verbs/hook.py`.

Run each of these once, by absolute path, from the worktree root:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tests
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/docs/check_structure.py
```

The transcripts must end with `failed 0`. The structure check may report only
`pm/README.md:76`.

Stop at 80k tokens or 40 tool calls. Commit with explicit `git add` paths; the message
ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report in
the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/03-prompt-once.md`,
commit it, and print only that path.
