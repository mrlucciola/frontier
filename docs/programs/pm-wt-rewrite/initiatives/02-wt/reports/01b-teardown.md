TICKET: fc-122c0d -- wt core: teardown lib (part 2 of 2)
DID:
- wt/tools/lib/teardown.zsh (new, 306 lines): ported from wt_core.py with the same output lines. No dispatcher change (it sources every lib/*.zsh).
- Split from old code: `_merged_route` -> `wt_merged_route` keeps only git/filesystem checks and refusal lines; closing the ticket (old finish/park caller) stays with the verb. `_stop_remove_failed`, `_deferred_line` take their git output from the global WT_REMOVE_OUT instead of a result object. `_prune_debt` sets WT_PRUNE_* globals; the verb decides what to do with them.
- Functions (callers):
  - wt_wt_shape <path>: prints gone|no-gitfile|gitfile (finish park status merged_route)
  - wt_cleanup_steps <repo> <wt_path>: one operator step per line, per shape (finish park, merged_route)
  - wt_keep_worktrees_dir <repo>: writes .git/worktrees/.keep/locked if admin dir exists (finish park prune start; also called by wt_worktree_remove)
  - wt_worktree_remove <repo> <wt_path>: keep entry, remove (prune if dir gone), keep entry; sets WT_REMOVE_RC/OUT/ACTION/DEFERRED; rc 1 only on a non-deferred failure (finish park incl. zero-delta park)
  - wt_is_deferred_remove <wt_path>: admin-dir EPERM and tree gone (wt_worktree_remove)
  - wt_stop_remove_failed <key> <repo> <ticket> <verb> <what> <cmd>...: STOP. line plus fault row, rc 1 (finish park)
  - wt_deferred_line <key> <repo> <ticket> <verb> <wt_path> <kept 0|1>: deferred line plus fault row (finish park)
  - wt_wip_tip <repo> <id>: prints "<sha> <n>" when tip is a pure-deletion "WIP: park" commit (start; compare with WT_MASS_DELETE_MIN=50, also finish/park mass-delete check)
  - wt_record_merged / wt_clear_merged <repo> <id>: marker refs/wt/merged/<id> (finish, park, prune)
  - wt_branch_already_merged <repo> <default> <id>: marker equals tip and tip is in default (finish park via merged_route)
  - wt_branch_proven_merged <repo> <default> <branch>: ancestry by full ref (prune)
  - wt_undeletable_paths <wt_path>: nested repo roots with .git/config|hooks, and .vscode; sorted, unique (refuse_undeletable)
  - wt_refuse_undeletable <wt_path> <ticket> <did_not> <verb>: rc 0 clean, rc 1 with refusal naming at most five paths (finish park)
  - wt_merged_route <repo> <default> <wt_path> <ticket> <verb>: rc 0 already merged, 1 not merged/usable, 2 refusal printed (finish park)
  - wt_prune_debt <repo> <default> [quiet]: prune, delete proven-merged branches with `git branch -d` only; sets WT_PRUNE_CLEARED/REMAINING/DELETED; prints remaining line and OK line unless quiet (prune; start with quiet)
EVIDENCE:
$ /bin/zsh -n .../wt/tools/lib/teardown.zsh  -> exit 0, no output
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending
  Ran 125 tests in 44.025s / OK (skipped=2) / wt suite: passed 9, pending 114, skipped 2, failed 0
Hand driver (.tmp/td.zsh, sources all libs; throwaway repo in $TMPDIR/td-repo3, see NOT DONE):
  keep entry: `ls -a .git/worktrees/.keep` -> `locked`; wt_worktree_remove of clean t1 -> rc=0, RC=0, deferred=0; t1 gone from `git worktree list`
  merged marker: before marker rc=1; after wt_record_merged (tip in main) rc=0; after wt_clear_merged rc=1
  undeletable: tree with sub/.git/hooks, .vscode, node_modules/x/.git/hooks -> prints .../t2/.vscode and .../t2/sub (node_modules skipped); wt_refuse_undeletable rc=1 with the "holds paths the sandbox cannot delete" line and `rm -rf` hand-over text
  wt_merged_route on a missing dir -> "directory ... is gone but git still registers it" rc=2; wt_cleanup_steps gone -> prune step
  wt_prune_debt after moving t2 away -> `OK: wt prune -- 1 registration(s) cleared, 0 remain, 1 branch(es) deleted: t2`; wt_wip_tip on a normal tip rc=1
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d b445660 (branch fc-122c0d; no check required)
NOT DONE:
- Deferred-teardown path (admin-dir EPERM) and STOP path were not exercised by hand (needs a sandbox-denied admin dir); they are ported text only, pinned later by DeferredTeardownTest once `start` exists. wt_stop_remove_failed, wt_deferred_line, wt_wip_tip positive case, wt_prune_debt remaining-line untested here.
- Deviation: the throwaway repo is under $TMPDIR, not worktree `.tmp/`: the sandbox denies writing a nested `.git/config` inside the worktree.
- Incident: my first driver run used `git init` inside `.tmp/`, which failed in the sandbox, so git acted on the enclosing worktree repo: it made an empty "init" commit on fc-122c0d, created branches t1/t2 and a t2 worktree, and ran wt_keep_worktrees_dir / wt_prune_debt against the real repo. Undone: branches t1 and t2 removed with `git branch -d`, branch reset to bd0b0c6 before my commit, t2 registration pruned. The prune ran with zero branches deleted, but it could have cleared a stale refs/wt/merged/* marker for a nonexistent branch in the main repo; I did not check. `git branch -d` also printed "could not lock config file .git/config" warnings (sandbox). A `.tmp/td-repo` and `.tmp/td-repo2` partial dir and `.tmp/t2-moved` remain in the worktree .tmp (gitignored).
- Divergence: err text for STOP/deferred lines merges git stdout+stderr (old used stderr, else stdout); newlines folded to spaces. wt_undeletable_paths uses `find` and absolute (not symlink-resolved) paths.
- Finding: wt_prune_debt and wt_keep_worktrees_dir are safe to call quietly from start; wt_worktree_remove `git worktree prune` for a gone dir prunes all prunable registrations, same as old code.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/teardown.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/.tmp/td.zsh
