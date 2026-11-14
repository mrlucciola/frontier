# pm-wt-rewrite/02/00-2a wt characterization: finish and land, gate and findings fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-2a-finish-gate.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-2a wt characterization: finish and land, gate and findings fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-2a-finish-gate.md`

You are a worker on ticket fc-30c060, part 2a. You start with zero context. Your worktree
is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`;
the overseer created it. `WT/` below means that worktree's `wt/` directory.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway under
the test's temp root; nothing touches a real repository or a registered store.

## What exists (part 1, commit 29e8a2a)

`WT/tests/run_wt.py` (runner, pending rule) and `WT/tests/test_wt_cli.py`: the isolated
env, `WtCase.wt()` (the one wt helper), `make_repo()`, `commit_file()`,
`assert_wt_line()`, the `OldPm`/`NewPm` adapters (`make_store`, `file_ticket`, `status`,
`holder`, `notes`, `take`, `park`, `block`, `set_gate`, `add_known_red`,
`guard_refuse_done`), `AdapterTest`, `StartTest`, and an empty `FinishTest`. Read the
whole file before writing; reuse its helpers, keep its style (docstring quotes the
contract phrase, assert exit codes and the first words of wt's own lines, never pm's
text). Part 1's report: `docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-1-start.md`
in the main checkout.

## Read

1. `pm ticket show fc-30c060` -- the spec.
2. `WT/docs/contract.md`: "Verbs" (finish, land, `--note`/`--findings`, `--keep-open`),
   "Gate", and in "Reading wt output" the `OK:` lines for finish.
3. Old wt `cmd_finish` and the gate code in `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`
   (read-only) for exact line shapes.

## Overseer ruling you implement in the adapter

The new side has no "malformed JSON gate". Its equivalent: `.wt/gate` exists but is not
executable. The new wt must refuse that, as the old refuses a gate that is not a list of
strings: a typo never turns the gate off. Change `NewPm.set_gate(malformed=...)` to write
a non-executable `.wt/gate` (and commit it) instead of raising `Unavailable`, and update
`AdapterTest.test_malformed_gate` to match. This is the only edit to part 1's code you
make.

## Deliver: `FinishTest` in `WT/tests/test_wt_cli.py`

A test helper that starts a ticket with `wt start`, commits one change in its worktree
(`git -C <worktree> ...`), and returns `(repo, ticket, worktree)` will serve every case;
put it on `FinishTest`. Cover, each its own test:

- **finish happy path**: merged into `main` (ff-only), worktree dir gone, branch gone,
  ticket `done`, the `OK:` line. Accept the deferred-teardown `OK:` line too (contract,
  "Deferred teardown"): the sandbox may refuse deleting the admin dir.
- **`--note` and `--findings`** reach the close: the note text is on the ticket. Each is
  omitted when not given.
- **findings warning**: without `--findings` on a store without `findings_required`,
  finish warns and still finishes.
- **findings refusal**: store with `findings_required`, no `--findings`: refused before any
  merge or teardown -- `main` unchanged, worktree intact, ticket `taken`.
- **gate pass**: the `gate <argv> exit 0, SKIP lines: K` line, K counted from output lines
  matching `skip`/`skipped` case-insensitively (make the gate print two such lines).
- **gate fail**: non-zero exit refuses: nothing merged, ticket `taken`, worktree intact,
  the last 30 lines of gate output printed (make it print 40 numbered lines; assert line
  11 to 40 present and line 10 absent, or whatever the old wt really does -- pin it).
- **gate runs in the worktree**, after the dirty check and before rebase or merge (a gate
  that writes `pwd` to a file outside the repo proves where it ran).
- **malformed gate refuses** (both sides, through the ruling above).
- **`--no-gate`**: bypasses the gate and the close note carries `gate skipped (--no-gate): `.
- **no gate configured, no gate**: no `gate ` line.
- **known red**: a gate whose output has a line matching a known-red entry for this ticket
  passes; the close note carries `known red <ticket>`. An entry whose line no longer fails
  refuses until it is dropped. Read the old code to learn what "matches" and "stopped
  failing" mean, and pin that.
- **dirty worktree** refuses: nothing merged, ticket `taken`.
- **land** (and `finish --keep-open`): merged, worktree and branch removed, ticket still
  `taken` by the same holder; `land --note x` and `land --findings x` are rejected;
  `land --no-gate` prints the skip line; `wt start <id>` from the same session afterwards
  adopts the claim (the `adopting existing claim` line).

A contract case that cannot run in the sandbox: add it to `WT/docs/uncovered.md` (case,
why, the exact operator-terminal command that covers it), do not fake it. If the old wt
contradicts the contract, pin what the old wt does, and name the test and the contract
line in NOT DONE.

Rebase conflicts, the ff-only retry, a refusal after the merge, the merged marker,
nested-repo and `.vscode` refusals and failed removes are part 2b; do not write them.

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
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-2a-finish-gate.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
