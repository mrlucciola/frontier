# pm-wt-rewrite/03/02 finalize component principles and behavioral contract fc-ccecda:fc-121923

```
cd ~/projects/frontier-clean/.worktrees/fc-121923 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/02-principles.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-121923 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/03/02 finalize component principles and behavioral contract fc-ccecda:fc-121923

`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/02-principles.md`

You are a worker for ticket **fc-121923** (epic fc-ccecda). You start with zero
context. The worker brief binds you and is not restated here:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-121923`, branch
  `fc-121923`. The overseer created it. Every edit is under it; every git command is
  `git -C <that path> ...`. You never run `wt`, never merge, never run
  `pm ticket close|note|claim`.
- Write set: `docs/component-principles.md`, the root `README.md` (its "Behavioral
  contract" section only), `docs/contributing.md`. Nothing else. In particular not
  `pm/`, `wt/`, or `docs/instruction-delivery.md`.

## The spec

`pm ticket show fc-121923 --all-notes` is the spec; read it and every note. Deliver:

1. `docs/component-principles.md` out of draft. For each of the ten rules: kept,
   changed or dropped, with one line of evidence from the pm redesign or the wt
   rewrite. Evidence is a path (`file:line`), a commit, or a review finding, never a
   recollection. Put the evidence where a reader can check it (a short "Evidence"
   line under each rule, or one table at the end; pick one).
2. Rule on each proposal the notes carry, and record the ruling with its evidence:
   - rule 1: a verb defined as another verb plus X may import that verb
     (pm `lint` and `validate`);
   - rule 2: a helper also earns the shared module when two verbs must enforce the
     identical rule (pm: a verb and its `--mutate` preflight; claim and
     `create --claim-as`), and when two verbs form one family (wt finish and park:
     `wt_findings_required` in `wt/tools/lib/pm.zsh`, the four teardown helpers in
     `wt/tools/lib/teardown.zsh`; recorded in `wt/AGENTS.md`);
   - the three practices from the redesign: transcripts as the contract, size
     budgets as tests, plugins by file presence (`pm/docs/design.md`). Each becomes
     a rule, folds into an existing rule, or is declined with the reason.
   If a ruling would make existing code non-conforming (for example you decline the
   wt family exception), do not change the code: list the file and what must move in
   NOT DONE.
3. Link the contribution standards (`/docs/contributing.md`) from the principles page
   (Run 0 note).
4. Extend the root behavioral contract and `docs/contributing.md` only where the two
   builds showed a gap, each addition with its evidence in your report. The two
   documents stay separate: the contract says how components behave, the principles
   say how to build them. No restating one in the other; link instead.

## Where the evidence is

- Code: `pm/` and `wt/` in the worktree; `pm/docs/design.md`; `wt/AGENTS.md`;
  `wt/docs/contract.md`.
- The closed initiatives' ledgers and review reports, retired from the tree:
  `git -C /Users/matthias/projects/frontier-clean show 523ae74:docs/programs/pm-wt-rewrite/initiatives/04-pm-log/INITIATIVE.md`
  and `bd6a9c5:docs/programs/pm-wt-rewrite/initiatives/02-wt/INITIATIVE.md`; list
  their reports with
  `git -C /Users/matthias/projects/frontier-clean ls-tree -r --name-only bd6a9c5 docs/programs/pm-wt-rewrite/initiatives/02-wt/reports`
  (and the same for `523ae74` and `04-pm-log`), then `git show <sha>:<path>`.
- Ticket notes: `pm ticket show fc-2a6562` and `pm ticket show fc-262fa8`.

Keep the page short: it is a review yardstick, read cold. A rule that needs a
paragraph of exceptions is the wrong rule.

## Gate

```sh
python3 -B docs/check_structure.py
```

Run from the worktree root; it must pass.

## Budget and report

Stop at 80k tokens or 40 tool calls. If you get there, commit what is green and list
the remainder in NOT DONE.

Commit on branch `fc-121923` with explicit `git add` paths. The commit message ends
with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write your
report in the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/02-principles.md`,
commit it on the same branch, and print only that path. In EVIDENCE, list each
ruling in one line (rule, kept/changed/dropped/added, evidence coordinate).
