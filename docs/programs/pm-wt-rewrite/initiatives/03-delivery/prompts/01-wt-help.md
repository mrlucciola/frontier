# pm-wt-rewrite/03/01 wt help that teaches, byte ceilings, skill account fc-ccecda:fc-03292e

```
cd ~/projects/frontier-clean/.worktrees/fc-03292e && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/01-wt-help.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-03292e worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/03/01 wt help that teaches, byte ceilings, skill account fc-ccecda:fc-03292e

`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/01-wt-help.md`

You are a worker for ticket **fc-03292e** (epic fc-ccecda). You start with zero
context. The worker brief binds you and is not restated here:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e`, branch
  `fc-03292e`. The overseer created it. Every edit is under it; every git command is
  `git -C <that path> ...`. You never run `wt`, never merge, never run
  `pm ticket close|note|claim`.
- Read-only: everything under `~/frontier`, `~/.claude`, `~/.codex`, `~/.config`,
  `~/.local`.

## The spec

`pm ticket show fc-03292e --all-notes` is the spec; read it. In short:

1. `wt help` and `wt help <verb>` in the shape of `pm help`: one verb table in the
   dispatcher `wt/cli/wt`, and each verb file's leading comment under
   `wt/tools/verbs/` is that verb's help. Read how pm does it first:
   `pm/cli/pm` (its verb table) and `pm/tests/test_budgets.py`.
2. A byte-ceiling test in `wt/tests/` modeled on `pm/tests/test_budgets.py`:
   `wt help` under 1200 bytes, any one verb's help under 700, any failure line wt
   prints under 400.
3. The guidance an agent needs at the moment of use moves into wt's own output and
   the lines its pm plugin prints (`wt/pm-plugin/{orient,post-take,pre-done}`).
4. `wt/docs/instruction-map.md`: every line of
   `/Users/matthias/frontier/skills/worktree-lifecycle/SKILL.md`, and of the wt and
   worktree parts of `/Users/matthias/frontier/instructions/claude-global/CLAUDE.md`
   (the section "Branches and worktrees (shared checkouts)" and the "Worktrees and
   tickets" block under "Command recipes"), each accounted for as exactly one of:
   printed by wt at the moment it applies (name the file and the line), kept in
   `wt/docs/contract.md`, or dropped with the reason. Also account for the old
   contract's environment sections the ticket's note lists
   (`git -C /Users/matthias/projects/frontier-clean show 61b8f1d:wt/docs/contract.md`).
   A table with one row per source line (or per contiguous line range that says one
   thing) is fine; every source line number must be covered.
5. No skill is shipped for pm or wt. Link the new doc from `wt/README.md` or
   `wt/AGENTS.md` so `docs/check_structure.py` passes.

## Rules for this ticket

- `wt/tests/test_wt_cli.py` is the accepted characterization suite. Never edit it.
  If a change to a failure line breaks one of its tests, keep the tested text and
  report the conflict in NOT DONE rather than editing the test.
- Plugin transcripts in `wt/tests/t/` and pm's `pm/tests/t/` are also not yours to edit.
- Do not edit anything under `pm/`. If wt's guidance needs a pm change, list it in
  NOT DONE.
- A byte number you write into a doc carries the command that produced it
  (component principle 10).

## Gate (run each once, from the worktree root, read the full output)

```sh
/usr/bin/python3 -B wt/tests/run_wt.py --cli wt/cli/wt --pm new
/usr/bin/python3 -B pm/tests/run_transcripts.py --dir wt/tests/t
/usr/bin/python3 -B -m unittest discover -s wt/tests -p 'test_budgets.py'
python3 -B docs/check_structure.py
```

The first must exit 0 with `pending 0, failed 0`. Name your new test file
`wt/tests/test_budgets.py` so the third line runs it. Also show that every source
line is covered: a `.tmp/` python script that reads the map and the two source files
and prints the uncovered line numbers (expect none). Commit the script's output in
EVIDENCE, not the script.

## Budget and report

Stop at 80k tokens or 40 tool calls. If you get there, commit what is green and list
the remainder in NOT DONE; the overseer re-dispatches it.

Commit on branch `fc-03292e` with explicit `git add` paths. The commit message ends
with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write your
report in the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/01-wt-help.md`,
commit it on the same branch, and print only that path.
