# pm-wt-rewrite/05/04 pm link --note fc-359b5b:fc-8ef942

```
cd ~/projects/frontier-clean/.worktrees/fc-8ef942 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/04-link-note.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-8ef942 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/05/04 pm link --note fc-359b5b:fc-8ef942

`docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/04-link-note.md`

You are a worker for ticket **fc-8ef942** (epic fc-359b5b), starting with zero
context. The worker brief binds you:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first, then `pm ticket show fc-8ef942`.

Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942`, branch
`fc-8ef942`. Edit only under it, and use `git -C <worktree>` for git. Never run `wt`,
never merge, never run `pm ticket close|note|claim`.

**Spec:** `pm/docs/design.md` "Verbs", the `pm link` row. `--note TEXT` appends one
`note` event, with `text`, on each ticket after the relation. It goes in the same
`store.change` write as the link events. It is added even when the link already
existed. Add `[--note "text"]` to the docstring's usage line, which is
`pm help link`; it must stay under the 700-byte ceiling in
`pm/tests/test_budgets.py`.

**Gate:** the extended transcript `pm/tests/t/09-link.t`, which the overseer committed
on your branch. Never edit the design, `pm/tests/t/` or `pm/tests/fixtures/`. If one
looks wrong, stop and report it.

**Write set:** `pm/tools/verbs/link.py`.

Run each of these once, by absolute path, from the worktree root:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/pm/tests
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/docs/check_structure.py
```

The transcripts must end with `failed 0`. The structure check may report only
`pm/README.md:76`.

Stop at 80k tokens or 40 tool calls. Commit with explicit `git add` paths; the message
ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report in
the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/04-link-note.md`,
commit it, and print only that path.
