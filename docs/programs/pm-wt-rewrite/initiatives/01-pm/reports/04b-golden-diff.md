TICKET: fc-59011f -- pm integration: golden diff on the live stores
DID: pm/tests/golden_diff.py added: old vs new CLI via --store on every registry store (summary, ready, list, stores --check, show x<=5), compares stdout + exit code, SKIPs history-pending or unreadable stores.
DID: No pm/tools/ change needed: 0 DIFF, so no normalization was added either.
DID: docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04b-golden-diff.md (this report).
EVIDENCE:
/usr/bin/python3 -B pm/tests/golden_diff.py -> exit 2; last lines:
  SKIP /Users/matthias/projects/frontier-clean: .pm/history-pending exists (summary would commit)
  golden_diff: stores 9, comparisons 81, same 81, DIFF 0, SKIP 1
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket (run with --allow-pending, which is moot at 0) -> parity: passed 267, pending 0, failed 0, skipped 9
/usr/bin/python3 -B -m unittest discover -s pm/tests -> Ran 349 tests, OK (skipped=9)
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-59011f branch fc-59011f (sha in git log; tip is the commit with message "pm integration: golden diff on the live stores (fc-59011f)")
NOT DONE: Gate asks exit 0 but the run exits 2: the registry store ~/projects/frontier-clean has .pm/history-pending, so summary would commit a snapshot; by the read-only rule it is skipped, and this skip is not an unreadable-repo-outside-sandbox case. Comparing it needs the pending marker cleared (history sync by its owner), then a rerun.
BLOCKED ON OPERATOR:
1. Clear the marker, then rerun (owner of the main checkout; this is a write to a live store, so I did not do it).
   # expect: summary line SKIP 0, exit 0
   /usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tests/golden_diff.py
   (marker clearing command: I have not checked which verb clears it; likely `pm ticket history sync` in /Users/matthias/projects/frontier-clean.)
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tests/golden_diff.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04b-golden-diff.md
