# pm-wt-rewrite/03/04 measure pm/wt instruction cost before and after fc-ccecda:fc-f9ab11

```
cd ~/projects/frontier-clean/.worktrees/fc-f9ab11 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/04-measure.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-f9ab11 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/03/04 measure pm/wt instruction cost before and after fc-ccecda:fc-f9ab11

`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/04-measure.md`

You are a worker for ticket **fc-f9ab11** (epic fc-ccecda). You start with zero
context. The worker brief binds you and is not restated here:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-f9ab11`, branch
  `fc-f9ab11`. The overseer created it. Every edit is under it; every git command on
  this repository is `git -C <that path> ...`. You never run `wt` against this
  repository, never merge, never run `pm ticket close|note|claim` on the fc store.
- Write set: `pm/docs/cost.md`, plus one route line linking it from `pm/AGENTS.md` if
  `docs/check_structure.py` asks for it. Nothing else is committed.
- Read-only: everything under `~/frontier`, `~/.claude`, `~/.codex`, `~/.config`,
  `~/.local`. Running the old tools and the old hook script is fine; editing them is
  not.

## The spec

`pm ticket show fc-f9ab11 --all-notes` is the spec. Deliver `pm/docs/cost.md` with
the command and the number for each of these:

1. **Today, before any ticket work.** Bytes of pm and wt guidance a session carries:
   the `description:` front-matter values of `~/frontier/skills/pm/SKILL.md` and
   `~/frontier/skills/worktree-lifecycle/SKILL.md`; both SKILL.md files whole; the pm
   and wt parts of `~/frontier/instructions/claude-global/CLAUDE.md` (name the line
   ranges you counted: the "Worktrees and tickets" recipe block, the section
   "Branches and worktrees (shared checkouts)", and any other pm paragraph you find);
   and the old session-start injection in this repository: run
   `~/frontier/hooks/pm/session_start.py` with a session-start JSON on stdin and the
   cwd set to this repository's main checkout, and count its stdout.
2. **The new system.** `pm hook session-start` (and `prompt` and `stop`, with the
   payloads `pm/docs/design.md` "Harness hooks" names) run by
   `/Users/matthias/projects/frontier-clean/pm/cli/pm` in a copy of this repository's
   store after `pm import`, and the same in a directory with no store (expect zero).
   The new wt's guidance: `wt help` and the longest `wt help <verb>`, from
   `wt/cli/wt`. See `pm/tests/import_check.py` for how a store is copied and imported.
3. **One ticket's life, old against new.** Bytes of command output for file, take,
   note, finish, in scratch stores: old = the installed `pm` and `wt` on PATH
   (`pm ticket create`, `wt start`, `pm ticket note`, `wt finish`); new =
   `pm/cli/pm` and `wt/cli/wt` (`pm new`, `wt start`, `pm note`, `wt finish`). Count
   stdout and stderr separately.
4. **Hook wall time.** Median and max of at least 20 runs of each hook, old and new,
   measured by a `.tmp/` python script with `time.perf_counter`; state the machine
   load caveat in one line.

Every number in the file sits beside the exact command that produced it. Byte counts
are diagnostic, not token savings: say so at the top. Where something cannot be
measured from this sandbox, say what and why, and give the command an operator would
run.

## Scratch repositories: read this before any `git init`

A scratch git repository goes under the main checkout's `.tmp/`:
`git init /Users/matthias/projects/frontier-clean/.tmp/cost-<name>`, never inside
your worktree. An earlier worker's refused `git init` let later git commands act on
the real repository. So, right after each `git init`, run
`git -C <scratch path> rev-parse --show-toplevel` and continue only if it prints the
scratch path itself. If it prints anything else, or the init is refused, stop and
report in NOT DONE; do not try another form. Copies of `.pm/` stores go under
`/Users/matthias/projects/frontier-clean/.tmp/` too. Never delete scratch.

## Gate

```sh
python3 -B docs/check_structure.py
```

From the worktree root. Also write a `.tmp/` python script that lists every line of
`pm/docs/cost.md` holding a digit outside a code span or fence and checks that a
command appears in the same table row or the paragraph's fenced block; paste its
output in EVIDENCE (expect no unbacked numbers). Do not commit that script.

## Budget and report

Stop at 80k tokens or 40 tool calls. If you get there, commit what is green and list
the remainder in NOT DONE.

Commit on branch `fc-f9ab11` with explicit `git add` paths. The commit message ends
with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write your
report in the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-f9ab11/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/04-measure.md`,
commit it on the same branch, and print only that path.
