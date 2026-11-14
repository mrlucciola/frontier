# pm-wt-rewrite/02/01b wt core: teardown lib fc-262fa8:fc-122c0d

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01b-teardown.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/01b wt core: teardown lib fc-262fa8:fc-122c0d

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01b-teardown.md`

You are a worker on ticket fc-122c0d, part 2 of 2. You start with zero context. Your
worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d` on branch
`fc-122c0d`; the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` (the installed one is the old tool that runs this epic),
never mutate tickets with `pm ticket`, never merge. Stop at 80k tokens or 40 tool calls,
commit what is green, report the rest under NOT DONE. Read-only: everything under
`~/frontier`, `~/.local`, `~/.config/pm`, provider config dirs, this repo's `pm/`, and
`WT/tests/test_wt_cli.py` and `WT/tests/run_wt.py` (accepted; report, never edit).

## What exists

Part 1 on this branch: `WT/cli/wt` (dispatcher) and `WT/tools/lib/{git,pm,fail,config}.zsh`
plus `crossrepo.py`. Its report, with every lib function and its callers:
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01a-core.md`.
Read it and the lib files first; reuse them, do not change their signatures (if one is
wrong, say so in NOT DONE).

## Read

`pm ticket show fc-122c0d`; `/Users/matthias/projects/frontier-clean/docs/component-principles.md`;
`WT/docs/contract.md` sections "Settled decisions" and "Deferred teardown and prune";
the suite's `DeferredTeardownTest`, the failed-remove, nested-repo, `.vscode`, merged-marker
and prune tests in `WT/tests/test_wt_cli.py` (they pin the lines this lib prints); and,
read-only, `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`: `_stop_remove_failed`,
`_is_deferred_remove`, `_deferred_line`, `_keep_worktrees_dir`, `_is_wt_wip_tip`,
`_record_merged`, `_clear_merged`, `_branch_already_merged`, `undeletable_paths`,
`_refuse_undeletable`, `_merged_route`, `_wt_shape`, `_cleanup_steps`,
`_branch_proven_merged`, `_prune_debt`.

## Deliver: `WT/tools/lib/teardown.zsh`

The worktree-removal concern, shared by `finish`/`land`, `park`, `prune` and `start`
(quiet prune), ported faithfully from the functions above with the same output lines:
the keep entry (`.git/worktrees/.keep/locked`, written before and after each teardown),
removing a worktree and telling a deferred teardown (admin dir `Operation not permitted`
with the tree gone) from every other failure, the deferred line, the `STOP.` line with
the per-shape operator cleanup steps (dir gone, partial tree, `.git` file missing),
undeletable paths (nested repo with `config` or `hooks`, `.vscode`; at most five named),
the merged marker `refs/wt/merged/<id>` (record, clear, "branch tip equals marker and is
in the default branch"), the mass-deleting `WIP: park` tip check, and the prune of
deferred registrations with the remaining-registrations line. Where the old code merges
two concerns (for example `_merged_route` also closes the ticket), keep only the git and
filesystem part here and leave the ticket change to the verb; say which in the report.

Rules: `emulate -L zsh` in every function, quoted paths, explicit `return`s, never
`git branch -D`, `git worktree remove --force` or `rm -rf`. Use the fault-row and
failure-line functions from `fail.zsh`. No ticket ids in comments.

## Gate

```sh
/bin/zsh -n /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/teardown.zsh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt --pm new --allow-pending
```

`zsh -n`: exit 0. The suite: exit 0, `failed 0`. Also exercise the lib by hand in a
throwaway repo under the worktree's `.tmp/` (a short zsh driver script there that sources
the libs, never a real repo): write a keep entry and remove a clean worktree; detect a
merged marker; list undeletable paths for a tree holding a nested `.git/hooks` dir.
Paste the commands and results in EVIDENCE.

## Stop and report

Commit on branch `fc-122c0d` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01b-teardown.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
List every function you wrote, one line each with its intended callers.
