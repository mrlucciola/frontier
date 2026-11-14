TICKET: fc-913d02 -- checks and views (lint)
DID: pm/tools/verbs/lint.py: new verb. `validate` output and exit code, then WARN stale-path / local-path lines (stderr under --json, none under --workspace or unopenable store), P-01/P-02 pilot problems merged into validate's result (exit 1), `lint <id>` dispatch-heading check. Own copy of the path and pilot helpers (principle 2); imports `Problem`, `validate_one`, `print_result`, `run` from `verbs.validate`.
EVIDENCE:
- `/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k lint -k Lint -k pilot -k Pilot --allow-pending` -> `parity: passed 5, pending 0, failed 0, skipped 0`
- `/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'` -> `Ran 31 tests ... OK (skipped=1)`
- `/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'` -> `Ran 24 tests ... OK`
- `/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending` -> `parity: passed 265, pending 0, failed 0, skipped 9`; no `unbuilt verbs still needed:` line printed (nothing unbuilt).
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-913d02 branch fc-913d02, message `pm checks: lint (fc-913d02)` (tip: `git -C <worktree> rev-parse --short HEAD`)
NOT DONE: NONE. Note: 9 skipped tests in the full run were not inspected; none is lint-related per the -k run. I did not touch pm/docs/cut-list.md.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/verbs/lint.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e4-lint.md
