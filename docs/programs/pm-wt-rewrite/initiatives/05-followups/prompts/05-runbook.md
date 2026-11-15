# pm-wt-rewrite/05/05 CUTOVER.md additions fc-359b5b:fc-419332

```
cd ~/projects/frontier-clean/.worktrees/fc-419332 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/05-runbook.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-419332 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/05/05 CUTOVER.md additions fc-359b5b:fc-419332

`docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/05-runbook.md`

You are a worker for ticket **fc-419332** (epic fc-359b5b), starting with zero
context. The worker brief binds you:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first, then `pm ticket show fc-419332`, which is the spec.

Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-419332`, branch
`fc-419332`. Edit only `docs/programs/pm-wt-rewrite/CUTOVER.md` under it, and use
`git -C <worktree>` for git. Never run `wt`, never merge, never run
`pm ticket close|note|claim`. You write the runbook and run none of it; in
particular, never touch any `refs/pm/log`.

The runbook's shape is "Handed-off actions" in
`/Users/matthias/frontier/references/protocols/handoff-contract/README.md`: one
numbered step per physical action, one fenced block with the commands and their
proof, and the repo each change lands in. Read the runbook's existing triggers, its
step 1 and step 2 first. Place the stray-ref step after the freeze and before the
first import. Add it as a new item; do not renumber the existing steps. Before you
write the two shas, check them with read-only commands:
`git --no-pager -C <repo> rev-parse refs/pm/log`. If either differs from the ticket,
use what you see and say so in the report.

The board line belongs where the runbook says what the switch removes. The ruling on
sharing belongs in the decisions section, as a settled decision. Check how the
runbook marks those today and follow it.

Gate, once, by absolute path from the worktree root:
`python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/check_structure.py`.
It may report only `pm/README.md:76`.

Stop at 80k tokens or 40 tool calls. Commit with explicit `git add` paths; the message
ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report in
the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/05-runbook.md`,
commit it, and print only that path.
