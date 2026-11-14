TICKET: fc-59011f -- pm integration: review fixes in shared modules (fixes 1-9)
DID: pm/tools/gitcommit.py and callers (store, archive, summary, history, close, tests/test_gitcommit.py): git, clean_env, fault, default_branch public (1); summary.py and close.py use gitcommit.git with the same timeouts, history.py bytes call kept with a comment (2).
DID: pm/tools/store.py, verbs/release.py, verbs/close.py, verbs/summary.py, verbs/archive.py, verbs/create.py, verbs/history.py, routing.py: acting_identity(session) in store (3); one hold_is_stale (4); archive.hint deleted with imports (5); label_problem/LABEL_MAX in create.py (6); store_root public, used by history.py and routing.py (7).
DID: pm/tools/verbs/*.py, pm/tools/ticket: args.repo replaces getattr (8); ROUTED_VERBS maps verb to mutate flag, fc-c10bcf dropped (9).
EVIDENCE:
test_cli_contract.py: Ran 30 tests ... OK
test_gitcommit.py: Ran 24 tests ... OK (test patch target renamed to "git")
test_views.py: Ran 19 tests ... OK
run_parity.py --cli pm/tools/ticket (.tmp/parity.txt): parity: passed 267, pending 0, failed 0, skipped 9
golden_diff.py (.tmp/golden.txt): exit 0; golden_diff: stores 10, comparisons 90, same 90, DIFF 0, SKIP 0, ruled skips 0
rg -n 'gitcommit\._|from verbs\.release|fc-c10bcf|getattr\(args, "repo"|def hint\(' pm/tools: no output
COMMITS: frontier-clean e431ec3 (branch fc-59011f; report commit follows on the same branch)
NOT DONE: NONE. Notes: validate.py keeps its own "no ticket store found" JSON error (different output shape, not the plain text); routing.py now uses store_root. summary.py's status call now runs with gitcommit's clean env (as close.py's already did).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04d1-review-fixes-shared.md
