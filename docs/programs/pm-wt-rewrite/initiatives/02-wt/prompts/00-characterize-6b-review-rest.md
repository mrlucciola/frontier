# pm-wt-rewrite/02/00-6b wt characterization: review gaps in start, resolution, refusals fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-6b-review-rest.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-6b wt characterization: review gaps in start, resolution, refusals fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-6b-review-rest.md`

You are a worker on ticket fc-30c060, part 6b, the last characterization part. You start
with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`; the
overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway
under the test's temp root. Each new repo in a test gets its own store prefix (the new
pm's `init` registers prefixes and refuses a repeat).

## What exists

`WT/tests/test_wt_cli.py` and `WT/tests/run_wt.py`: a black-box suite green against the
old wt. Read the whole test file first and reuse its helpers (`StartedCase.started`,
the `git` shim via `wt(..., path_first=...)`, `faults()`, the adapter's
`register_store`). Keep its style: docstring quotes the contract phrase; assert exit
codes and the first words of wt's own lines; never pm's text. Contract:
`WT/docs/contract.md`. Old wt, read-only:
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`.

Read the review
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-review.md`
and part 6a's report `reports/00-characterize-6a-review-finish.md` beside it. The overseer
accepted the review; 6a closed the finish, land and teardown findings. This part closes:

1. **session sources** (contract.md:47-50, 290-293): `wt start --session X` claims with
   token X (adopt with the same `--session`, refuse with another); with no `--session`
   and no `PM_SESSION_ID`, `CLAUDE_CODE_SESSION_ID` is used; `CODEX_THREAD_ID` is the
   default when `PM_SESSION_ID` is unset (pin which of the two wins when both are set,
   as the old wt does). Set these variables per call, in the test, not in setUp.
2. **start EPERM hint** (127-128): with the `git` shim making `worktree add` fail with
   `.git/worktrees` and `Operation not permitted`, `start` appends its restart/resume
   hint. Pin the first words.
3. **stale worktree, ticket already closed** (198-200): a worktree whose ticket is
   already done and whose branch is merged: `wt finish` tears it down, and its last line
   reports the close failed because the ticket is already closed. Pin wt's words only.
4. **`where` failures** (85-86): pm missing from `PATH` stops `start` with a `wt:` line
   (pin its first words), nothing created; the two-owners test pins first words beyond
   `wt: ` (old side only); a prefix registered to another repo resolves for `finish` and
   `park` too, not only `start`.
5. **prune remainder line** (148-150): it ends with
   `Operator: !git -C <repo> worktree prune`.
6. **first words of refusals**: malformed gate (66-67), dirty worktree (61-62), no actor
   (29) -- replace the bare `wt: ` checks with each line's first words up to its first
   variable part. Then make `test_every_refusal_names_a_next_step` assert, per case, the
   specific next-step words the old wt prints (a command or an action), not only
   non-empty text.
7. **nested repo and `.vscode` variants** (122-126): a nested `.git` dir with only
   `hooks` refuses; `.vscode` refuses `park` too; with six nested repos the line names
   five paths (pin how the old wt caps).
8. **selftest** (26, 258-259): `wt selftest` exits 0, prints its case lines and a final
   line with no failures (pin the first words), and leaves no worktree registration and
   no fault row behind. Do not pin its scratch path; the new wt may differ.

A case that cannot run sandboxed goes in `WT/docs/uncovered.md` (case, why, exact
operator-terminal command). If the old wt contradicts the contract, pin the old wt and
name the test and the contract line in NOT DONE.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```

The first: `failed 0`, `pending 0`, `skipped 0`. The second (a stand-in wt that answers
every verb as unbuilt): `failed 0`; every wt test pending except the expected skips.
Paste each run's last two lines in EVIDENCE.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-6b-review-rest.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
