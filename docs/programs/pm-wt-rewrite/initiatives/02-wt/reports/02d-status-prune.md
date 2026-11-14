TICKET: fc-983ff4 -- wt verbs: status prune
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4/wt/tools/verbs/status.zsh: worktree list joined to tickets via wt_pm_get status; bare and main skipped; prunable -> deferred-teardown; no ticket -> FOREIGN/ORPHAN.
- /Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4/wt/tools/verbs/prune.zsh: calls wt_prune_debt (not quiet).
- Both resolve with wt_resolve_repos using an empty id; store defaults to the cwd repo by passing it as the store option (no ticket id to ask pm).
EVIDENCE:
/bin/zsh -n status.zsh -> exit 0, no output; /bin/zsh -n prune.zsh -> exit 0, no output
/usr/bin/python3 -B <wt>/wt/tests/run_wt.py --cli <wt>/wt/cli/wt --pm new --allow-pending
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4/wt/cli/wt (pm new)
  wt suite: passed 43, pending 80, skipped 2, failed 0
  (OK (skipped=2)). `pending:` lines naming status or prune as first unbuilt step: none. Pending in StatusPruneTest: park_waits_on, prune_prints_remaining (finish), selftest, status_after_park (park) -- all other verbs.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4 74077a7 (branch fc-983ff4)
NOT DONE: NONE. Untested until finish exists: test_prune_prints_remaining_registrations, test_prune_clears_the_debt, test_status_after_park (all pending on finish/park).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4/wt/tools/verbs/status.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-983ff4/wt/tools/verbs/prune.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02d-status-prune.md
