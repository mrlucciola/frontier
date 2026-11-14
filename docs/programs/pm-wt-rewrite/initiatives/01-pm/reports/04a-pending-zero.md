TICKET: fc-59011f -- pm integration: remove the unbuilt mechanism, parity pending 0
DID: pm/tools/store.py: removed `UNBUILT_EXIT` and `unbuilt()`; pm/tools/ticket: removed the missing-verb-file branch and the "70 the verb is not built yet." epilog sentence.
DID: pm/tests/test_cli_contract.py: removed every `skipTest("unbuilt: ...")` branch, the `skipUnless(built("history"))`, `UnbuiltTest`, `built()`, `VERBS_DIR`, `KEPT`, the `PM_UNBUILT_LOG` pop and the docstring paragraph.
DID: No argv fix was needed: the `dep`/`unlink` cases with `tt-other` pass in the refusal tests; no non-test fix was needed (StoreRoutingTest passes).
EVIDENCE: /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket > .tmp/parity-04a.txt, last three lines:
  OK (skipped=9)
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/ticket
  parity: passed 267, pending 0, failed 0, skipped 9
EVIDENCE: /usr/bin/python3 -B -m unittest discover -s pm/tests -> Ran 349 tests in 176.199s, OK (skipped=9)
EVIDENCE: /usr/bin/python3 -B -m unittest discover -s pm/tests -p test_cli_contract.py -> Ran 30 tests, OK (no skips)
COMMITS: frontier-clean 4890a60 on branch fc-59011f (code); the report commit follows it on the same branch
NOT DONE: NONE. Left as the prompt says: pm/tests/run_parity.py still mentions PM_UNBUILT_LOG/--allow-pending/"unbuilt verbs still needed" (untouched by instruction); pm/tests/test_views.py:40 docstring says "while dep is unbuilt" (stale wording, not edited).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/pm/tests/test_cli_contract.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/.tmp/parity-04a.txt
