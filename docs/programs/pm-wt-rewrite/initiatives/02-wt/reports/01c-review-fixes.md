TICKET: fc-122c0d -- wt core: lib review fixes
DID:
Lib function list after the fixes (WT = worktree wt/; all in WT/tools/lib/; callers are the planned verbs, none built yet except where noted):
- pm.zsh `wt_pm <store> <session> <pm args>`: every pm call; returns 127 + `wt:` line if pm not on PATH. Callers: all verbs, wt_pm_get.
- pm.zsh `wt_pm_get <store> <id> <field>`: wt_resolve_repos; start/status as needed.
- pm.zsh `wt_findings_required <store>`: finish, park (shared teardown family; proposed principle-2 amendment).
- pm.zsh `wt_resolve_repos <store opt> <repo opt> <id> <cwd repo>`: sets WT_STORE, WT_REPO; every verb. --store/--repo/pm-store resolution is inlined here.
- git.zsh `wt_repo_root [dir]`: wt_resolve_repos, verbs (cwd repo).
- git.zsh `wt_default_branch <repo>`: start, finish, park, prune, status.
- git.zsh `wt_worktree_path <repo> <id>`: start, finish, park, status.
- git.zsh `wt_branch_exists <repo> <branch>`: start, wt_branch_already_merged, wt_prune_debt.
- git.zsh `wt_worktree_list <repo>`: fills WT_WORKTREE_PATHS/BRANCHES/PRUNABLE/BARE (BARE = 1 or empty); wt_prune_debt, status, start.
- git.zsh `wt_is_ancestor <repo> <a> <b>`: wt_branch_already_merged, wt_prune_debt, finish.
- fail.zsh `wt_say <text>`, `wt_fault_row ...`, `wt_fail <infra|flow> ...`, `wt_guard <src> <target> <sub> <ticket> <verb>`: every verb; wt_guard: start, finish, park, land.
- teardown.zsh `wt_wt_shape <path>`: wt_cleanup_steps, wt_worktree_remove, wt_merged_route.
- teardown.zsh `wt_cleanup_steps <repo> <path>`: finish, park, land (failed-remove STOP hand-over).
- teardown.zsh `wt_keep_worktrees_dir <repo>`: wt_worktree_remove, wt_prune_debt.
- teardown.zsh `wt_worktree_remove <repo> <path>`: finish, land, park, prune/start (quiet). Sets WT_REMOVE_RC, WT_REMOVE_OUT (stderr+stdout, for the deferred check), WT_REMOVE_ERR (stderr else stdout, trimmed; what the lines quote), WT_REMOVE_ACTION, WT_REMOVE_DEFERRED. Deferred check is inlined.
- teardown.zsh `wt_stop_remove_failed`, `wt_deferred_line`: finish, land, park. Read WT_REMOVE_ERR.
- teardown.zsh `wt_wip_tip <repo> <id>`: start (mass-delete resume refusal), park.
- teardown.zsh `wt_clear_merged <repo> <id>`: wt_prune_debt, finish, park. (Writing the marker is the verb's own `git update-ref refs/wt/merged/<id> refs/heads/<id>`.)
- teardown.zsh `wt_branch_already_merged <repo> <default> <id>`: wt_merged_route, finish, park.
- teardown.zsh `wt_undeletable_paths`, `wt_refuse_undeletable <path> <ticket> <did_not> <verb>`: finish, park.
- teardown.zsh `wt_merged_route <repo> <default> <path> <ticket> <verb>`: finish, park.
- teardown.zsh `wt_prune_debt <repo> <default> [quiet]`: prune, start (quiet). Proven-merged check inlined.
- crossrepo.py, findings_required.py: unchanged apart from the finding-10 text.
Removed: config.zsh (git rm), wt_resolve_repo, wt_is_deferred_remove, wt_branch_proven_merged, wt_record_merged, wt_pm_take/done/park/drop/emit (verbs call `wt_pm <store> <session> take|done|park|drop|emit ...`). `rg` of each name over WT minus tests: no hits.
Fix notes: 1 `path` local gone. 2/9 `pm get` rc split in wt_resolve_repos, last line used. 3 pm-on-PATH check in wt_pm. 4 stdout-only values, stderr only for error text. 8 wt_guard: rc 1 with reason = refusal, else infra `crossrepo-guard-failed`. 10 old text restored in git.zsh, pm.zsh, crossrepo.py, fail.zsh header (em dashes, runtime-tools line, triage doc), STOP/deferred lines use stderr else stdout. 11 WT_WORKTREE_BARE. 5 and 12 vanish with config.zsh; the finish worker must read the gate and known-red from WT_REPO (the target repo), and quote `$id` as `${line#"$id"}`.
For the finish worker, non-executable gate refusal, verbatim (old config.zsh:10), printed on stderr, gate path = `$WT_REPO/.wt/gate`, returned after `[[ -e $gate ]]` passes and `[[ ! -x $gate || -d $gate ]]`:
  wt: <gate path> is not executable, so wt cannot run the gate; fix it or pass --no-gate.
The removed gate and known-red code is in `git -C <worktree> show 4635204^:wt/tools/lib/config.zsh`.
Not run for lack of a git repo-free way: findings 4, 10 (git text), 11 and the guard split were checked by reading only; the suite does not reach them until start/finish exist.

EVIDENCE:
Finding 1 (zsh -f, local special name; PATH shown inside the function):
  BEFORE (`local path=/tmp`): `PATH=/tmp git=NOTFOUND`
  AFTER (`local dir=/tmp`): `PATH=/Users/matthias/.pyenv/shims:...:/Users/matthias/.foundry/bin git=/Users/matthias/.local/bin/git`
Finding 6 (`v="a|b|c"`): BEFORE `${v//|//}` -> `a/b/c`; AFTER `${v//\|//}` -> `a/b/c`. The review's suspicion did not reproduce: the unescaped form already worked on this zsh. The escaped form is applied anyway, harmless.
Finding 7 (`emulate -L zsh`, input `hi  <tab>`, `${e%%[[:space:]]#}`): BEFORE `[hi  <tab>]` (no trim); AFTER with `setopt extendedglob` `[hi]`. wt_worktree_remove (where the trim now happens) sets extendedglob.
Hand check, pm off PATH (zsh -f, libs sourced): `wt_resolve_repos "" "" tk-1 /tmp` -> `wt: could not run \`pm get tk-1 store\`: pm is not on PATH; put pm on PATH and re-run.` rc=1. `wt_resolve_repos /nonexistent ...` -> `wt: --store /nonexistent is not a directory` rc=1. `wt_worktree_remove /nonexistent /nonexistent/x` -> rc=1, WT_REMOVE_ERR `fatal: cannot change to '/nonexistent': ...`, DEFERRED=0.
/bin/zsh -n on WT/cli/wt, pm.zsh, git.zsh, fail.zsh, teardown.zsh: each exit 0, no output.
Gate: `/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending`
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt (pm new)
  wt suite: passed 9, pending 114, skipped 2, failed 0
  (exit 0; "OK (skipped=2)")
Hand checks ran with `zsh -f -c` inline because the Write tool refused files under $TMPDIR (/tmp/claude-501); nothing under the worktree's .tmp/ except the commit message file.

COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d 4635204 (branch fc-122c0d)
NOT DONE:
- Finding 6 could not be confirmed as a bug (see EVIDENCE).
- Findings 4, 10, 11 and 8 are verified by reading and a few direct calls only; the 114 pending tests cover them once start/finish/park exist. Re-run the review's RE-VERIFY line then.
- wt_worktree_remove now uses a mktemp file under ${TMPDIR:-/tmp} to keep git's stderr and stdout apart (falls back to merged output if mktemp fails); the overseer may prefer another approach.
- Principle-2 amendment (wt_findings_required shared by finish and park) is for the overseer to record; I did not edit docs.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/pm.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/git.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/fail.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/teardown.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/crossrepo.py
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01c-review-fixes.md
