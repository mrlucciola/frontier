# pm-wt-rewrite/05/01 nested store resolution and the pre-import refusal fc-359b5b:fc-5e5a20

```
cd ~/projects/frontier-clean/.worktrees/fc-5e5a20 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/01-nested.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-5e5a20 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/05/01 nested store resolution and the pre-import refusal fc-359b5b:fc-5e5a20

`docs/programs/pm-wt-rewrite/initiatives/05-followups/prompts/01-nested.md`

You are a worker for ticket **fc-5e5a20** (epic fc-359b5b), starting with zero
context. The worker brief binds you:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first, then `pm ticket show fc-5e5a20`.

Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20`, branch
`fc-5e5a20`. Edit only under it, and use `git -C <worktree>` for git. Never run `wt`,
never merge, never run `pm ticket close|note|claim`.

**Spec:** `pm/docs/design.md` "Store", second paragraph. The store is the nearest
ancestor with a `.pm/config.json` or a `.pm/log.jsonl`. With no log, a linked
worktree falls back to the main checkout's store. A store with a config and no log is
refused. When a v2 `tickets.jsonl` sits beside the config, the refusal says to
import.

**Gate:** the new transcript `pm/tests/t/26-nested.t`, which the overseer committed on
your branch. Never edit the design, `pm/tests/t/` or `pm/tests/fixtures/`. If one
looks wrong, stop and report it.

**Write set:** `pm/tools/store.py` (`locate_dir`, `require`), plus a verb file only
if the transcript cannot pass otherwise. Name it in DID.

Run each of these once, by absolute path, from the worktree root:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/pm/tests
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/docs/check_structure.py
```

The transcripts must end with `failed 0`. The structure check may report only
`pm/README.md:76`.

Stop at 80k tokens or 40 tool calls. Commit with explicit `git add` paths; the message
ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report in
the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/01-nested.md`,
commit it, and print only that path.
