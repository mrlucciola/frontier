TICKET: fc-2b34c9 -- pm core (worker d: CLI contract tests)
DID: pm/tests/test_cli_contract.py (12 tests: dropped verbs, no telemetry under HOME, show --field, compacted read, compacted/archived refusals, validate hints, unbuilt contract)
DID: no CLI code changed; no test exposed a defect in this ticket's surface
DID: refusal and validate cases skip as "unbuilt: <verb>" until the verb file exists
EVIDENCE:
$ /usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -v
Ran 12 tests in 1.771s / OK (skipped=21)
skipped lines: "unbuilt: claim|hold|release|close|reopen|note|edit|dep|unlink|reparent" (10 each in test_compacted_refused and test_archived_refused = 20), "unbuilt: validate" (1)
$ /usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
Ran 22 tests / OK
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_create_show_roundtrip
parity: passed 1, pending 0, failed 0, skipped 0
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending   (exit 0)
parity: passed 20, pending 241, failed 0, skipped 9
(commands were run with absolute worktree paths because cd is refused)
COMMITS: frontier-clean see branch fc-2b34c9 tip (tests commit, then this report)
NOT DONE: refusal tests (case 5) and validate hint test (case 6) are all skipped, so the compacted/archived refusal texts are asserted only against store.py text, not yet exercised through a built verb. Mutator argv shapes are copied from the old CLI parser and may need adjusting when each verb lands (dep/unlink use a placeholder second id tt-other).
NOT DONE: the telemetry test uses `python -B` in the subprocess; without it, macOS python writes pycache under HOME/Library.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tests/test_cli_contract.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-d.md
