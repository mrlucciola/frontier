# pm-wt-rewrite/02/00-2b wt characterization: finish merge paths and teardown fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-2b-finish-merge.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-2b wt characterization: finish merge paths and teardown fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-2b-finish-merge.md`

You are a worker on ticket fc-30c060, part 2b. You start with zero context. Your worktree
is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`;
the overseer created it. `WT/` below means that worktree's `wt/` directory.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway under
the test's temp root; nothing touches a real repository or a registered store. A test
that changes permissions (`chmod`) restores them in an `addCleanup` so the temp root can
be removed.

## What exists

Parts 1 and 2a on branch `fc-30c060`: `WT/tests/run_wt.py` and `WT/tests/test_wt_cli.py`
with the isolated env, `WtCase.wt()`, `make_repo()`, the `OldPm`/`NewPm` adapters,
`AdapterTest`, `StartTest`, and `FinishTest` (gate, known red, findings, notes, dirty,
land) with its start-and-commit helper. Read the whole file first; reuse its helpers and
keep its style (docstring quotes the contract phrase; assert exit codes and the first
words of wt's own `OK:`, `wt:` and `STOP.` lines; never pm's text). Reports of parts 1
and 2a: `docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-1-start.md`
and `00-characterize-2a-finish-gate.md` in the main checkout.

## Read

1. `pm ticket show fc-30c060` -- the spec.
2. `WT/docs/contract.md`: "Settled decisions", "Deferred teardown and prune", and
   "Reading wt output" (auto-park, the `NOT closed` line, the deferred line, the `STOP.`
   line, a stale worktree of your own).
3. Old wt `cmd_finish`, its merge loop, teardown and refusal helpers in
   `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only), for exact line
   shapes and what triggers each path.

## Deliver: more `FinishTest` cases (same class; add a second class `FinishMergeTest` if
the file reads better that way)

Each its own test:

- **rebase conflict auto-parks**: `main` and the ticket branch change the same line.
  Result: ticket `parked`, branch kept with its commit, worktree dir gone, `main`
  unchanged. Pin the line shape. `wt start <id>` afterwards resumes it.
- **ff-only retry**: `main` moves after wt's rebase and before its merge; one move is
  absorbed by a retry and the finish succeeds; three or more moves exhaust the retries
  and auto-park. A way to provoke it with no wt internals: a git hook that runs on the
  rebase (`post-rewrite`, or `reference-transaction`) and commits to `main` in the main
  checkout, with a counter file limiting how many times. Install it through
  `git config core.hooksPath <dir under the test root>` in the throwaway repo. If no
  hook fires at the right moment for the old wt, list the case in `uncovered.md`.
- **refusal after the merge**: the merge lands, the ticket stays `taken`, and wt prints
  the `OK: <id> merged` line saying the ticket is NOT closed (contract, "Reading wt
  output"). Use the adapter's `guard_refuse_done` (old side: file the ticket with
  `labels=("tooling",)`). Assert only wt's words.
- **merged marker**: after a successful ff-only merge of a branch with commits,
  `refs/wt/merged/<id>` points at the tip. Then a stale worktree of your own: a ticket
  whose branch tip equals that marker and is in `main` (build it: merge by hand in the
  throwaway repo and write the ref, or reach it through a finish that stopped after the
  merge) is torn down and closed by `wt finish`, never parked or released.
- **nested git repo refusal**: a worktree holding a directory with a `.git` dir that has
  `config` or `hooks` refuses `finish` before any merge: line names the path and the
  operator-run `rm -rf`; nothing merged; ticket `taken`; no fault row in
  `$WT_FAULT_REPORT_DIR`.
- **`.vscode` refusal**: same for a `.vscode` dir. The sandbox denies writing any
  `.vscode` path segment, so this probably cannot be built here: try once; if it is
  denied, list it in `uncovered.md`.
- **failed remove prints `STOP.`**: make `git worktree remove` fail for a reason other
  than the admin-dir `Operation not permitted`, for example a git-ignored file inside a
  directory you `chmod 0555` (remove deletes ignored files, so the permission is what
  stops it). Assert the `STOP.` line, that it never suggests `--force` or a retry, the
  ticket still `taken`, and a fault row written under `$WT_FAULT_REPORT_DIR`.
- **deferred teardown** is the sandbox refusing to delete `.git/worktrees/<id>`. If you
  cannot provoke it on purpose, do not fake it: the happy-path tests already accept the
  deferred `OK:` line; list the forced case in `uncovered.md` with the operator command.
- **every failure line names a next step**: for each refusal you provoke in parts 2a and
  2b, the `wt:` line is non-empty after the prefix. One table-driven test is enough.

For `WT/docs/uncovered.md`: one entry per case -- the case, why it cannot run sandboxed,
the exact operator-terminal command that covers it. If the old wt contradicts the
contract, pin what the old wt does, and name the test and the contract line in NOT DONE.

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
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-2b-finish-merge.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
