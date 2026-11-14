TICKET: fc-c5e673 -- pm history verb: status enable disable sync restore, commit modes
DID: pm/tools/verbs/history.py new: status/enable/disable/sync/restore ported from old ticket (refusals, crash-resume, `.pm/history-pending` gitignore line, marker cleared by sync/restore/disable); the five sub-verbs also take --store/--repo after the sub-verb (the `history sync --repo X` remedy prints that form).
DID: pm/tools/gitcommit.py: commit_store gains keyword `legacy=False` (forces the default-branch path on a history_ref store); no existing signature changed.
DID: pm/tests/test_cli_contract.py: new HistoryMarkerTest (gitignore lines, test-written fault marker, disable/sync/restore clear it).
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k HistoryCliTest -k AutoCommitTest -k WorktreeStoreTest --allow-pending
  parity: passed 18, pending 19, failed 0, skipped 9
  (the 19 pending: lines all name an unbuilt verb other than history: close, claim, note, archive, summary, validate, list)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 17 tests ... OK (skipped=21)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests ... OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 34, pending 228, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, hold, lint, list, note, ready, release, reparent, summary, validate
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673 9c0567d (branch fc-c5e673); report committed after.
NOT DONE: Parity HistoryCliTest cases that create/claim/close/summary/validate are pending on other unbuilt verbs, so enable/disable/sync/restore are exercised end to end only by HistoryMarkerTest plus the cases that ran; re-run HistoryCliTest after those verbs land. `deferred` state and history_interval_seconds not built (state() never returns "deferred"; tests skipped). The `summary` catch-up of a pending snapshot (old _store_dirty_line) and commit()'s marker clear on success belong to summary/store, not built here. history.py calls gitcommit's underscore helpers (_git, _fault, _default_branch, _clean_git_env), no public equivalents exist.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673/pm/tools/verbs/history.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673/pm/tools/gitcommit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673/pm/tests/test_cli_contract.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03d-history.md
