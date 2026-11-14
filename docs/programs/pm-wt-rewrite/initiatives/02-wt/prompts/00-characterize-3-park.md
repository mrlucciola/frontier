# pm-wt-rewrite/02/00-3 wt characterization: park fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-3-park.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-3 wt characterization: park fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-3-park.md`

You are a worker on ticket fc-30c060, part 3. You start with zero context. Your worktree
is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`;
the overseer created it. `WT/` below means that worktree's `wt/` directory.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway under
the test's temp root; nothing touches a real repository or a registered store. A test
that changes permissions restores them in an `addCleanup`.

## What exists

Parts 1, 2a and 2b on branch `fc-30c060`: `WT/tests/run_wt.py`, and in
`WT/tests/test_wt_cli.py` the isolated env, `WtCase.wt()`, `make_repo()`, the
`OldPm`/`NewPm` adapters, `AdapterTest`, `StartTest`, `FinishTest` (and any finish class
2b added), an empty `ParkTest`, and `WT/docs/uncovered.md` if 2b wrote one. Read the
whole test file first; reuse its helpers (finish's start-and-commit helper, the
refusal and `STOP.` provocations of 2b) and keep its style: docstring quotes the contract
phrase; assert exit codes and the first words of wt's own lines; never pm's text. Earlier
reports: `docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-*.md` in
the main checkout.

## Read

1. `pm ticket show fc-30c060` -- the spec.
2. `WT/docs/contract.md`: "Verbs" (park, `--note`/`--findings`, zero-delta release),
   "Settled decisions", and in "Reading wt output" the park and resume lines.
3. Old wt `cmd_park` in `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`
   (read-only) for exact line shapes.

## Deliver: `ParkTest` in `WT/tests/test_wt_cli.py`

Each its own test:

- **WIP commit and park**: uncommitted changes in the worktree are committed (pin the
  `WIP: park` subject shape), the ticket is `parked`, the branch is kept with that
  commit, the worktree directory is gone at once, `main` unchanged, the `OK:` line
  (accept the deferred-teardown variant too).
- **already-committed work**: park with a clean worktree and commits ahead parks with no
  WIP commit.
- **the note**: the generated note names the branch and sha and ends with the resume line
  (`wt start ... && wt finish ...`); `--note TEXT` is prepended to it and the resume line
  stays last; `--waits-on <id-or-note>` appears where the old wt puts it; `--session ID`
  is folded into the resume line's `wt start` only when given.
- **findings**: `--findings` reaches the park; without it, a warning; on a
  `findings_required` store, refused before any WIP commit or teardown.
- **zero-delta release**: a worktree with no commits and no changes releases the ticket
  instead (status `open`, no holder), records neither note nor findings, and says so;
  branch handling as the old wt does it -- pin it.
- **`.local` refusal**: a non-empty `<worktree>/.local` blocks the park (gitignore it in
  the throwaway repo so it is the wt check, not git's, that refuses -- see the contract's
  "Pinned empirically" note): nothing committed, ticket `taken`, worktree intact.
- **mass deletion refusal**: a worktree that is only deletions, more than 50, refuses.
  50 or fewer does not.
- **lost `.git` file refusal**: a worktree whose `.git` file is gone refuses.
- **nested git repo refusal** for park, as for finish.
- **merged marker**: park on a branch whose tip equals `refs/wt/merged/<id>` and is in
  `main` tears down and closes the ticket (`done`), never parks or releases it.
- **failed remove `STOP.`** on park, as for finish (reuse 2b's provocation).
- **resume after park**: `wt start <id>` from the parked state brings the worktree back
  with the WIP commit, and `wt finish` merges it.

A contract case that cannot run in the sandbox goes in `WT/docs/uncovered.md` (case, why,
the exact operator-terminal command). If the old wt contradicts the contract, pin what the
old wt does, and name the test and contract line in NOT DONE.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
```

must end `failed 0` with `pending 0, skipped 0`. Also run
`--pm new --allow-pending -k AdapterTest`: all pass. Both runs' last two lines go in
EVIDENCE verbatim.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-3-park.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
