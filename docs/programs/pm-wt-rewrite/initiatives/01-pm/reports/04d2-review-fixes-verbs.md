TICKET: fc-59011f -- pm integration: review fixes in verb files (04d2, fixes 1-8)
DID: validate.py (I-19 hint is `operator: {lineno} /closure_reason: set it to null by hand`; `run_code(args) -> int`; `run_workspace` returns its code; `_relpath` inlined), pm/docs/cut-list.md (I-19 old/new hint bullet), lint.py (calls `validate.run_code`, `return run_dispatch(args)`, store opened once)
DID: summary.py (docstring; `store.is_semaphore`), edit.py (docstring; `locked_verb`, body inlined), note.py (`locked_verb`, body inlined, dead spec_version refusal deleted), reparent.py (`locked_verb`, `_reparent` inlined), dep.py and unlink.py (subject string, no lambda), stores.py (dead elif deleted)
DID: overview.py (regenerate line `pm view overview --store <root> --out <file>`, `REGEN_COMMAND` removed), pm/tests/test_views.py:159 (asserts the new text)
EVIDENCE:
/usr/bin/python3 -B -m unittest discover -s pm/tests -> Ran 349 tests in 170.878s; OK (skipped=9)
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -> parity: passed 267, pending 0, failed 0, skipped 9
/usr/bin/python3 -B pm/tests/golden_diff.py -> golden_diff: stores 10, comparisons 90, same 90, DIFF 0, SKIP 0, ruled skips 0
rg -n 'closure-reason null|Reads only; never writes|spec_version.*< *2' pm/tools/verbs -> no output
(A first run failed 2 parity tests with exit 1 vs 2 because inlining `_relpath` left call sites; fixed and rerun green.)
COMMITS: frontier-clean d19229a (branch fc-59011f; report commit follows on the same branch)
NOT DONE: NONE. Note: fix 6 made note, edit and reparent subjects come from `locked_verb`; parity commit-log checks pass, so subjects are byte-identical. `run_workspace` now returns its code instead of calling sys.exit (needed for `run_code`).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04d2-review-fixes-verbs.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/verbs/validate.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/verbs/lint.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/verbs/overview.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/docs/cut-list.md
