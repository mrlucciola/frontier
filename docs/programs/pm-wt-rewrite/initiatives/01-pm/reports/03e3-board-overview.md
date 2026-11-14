TICKET: fc-913d02 -- checks and views (board, overview)
DID: pm/tools/verbs/board.py, pm/tools/verbs/overview.py: ports of the old renderers (pm ticket|view board|overview, same flags/output; board still prints render() via print, as the old CLI did).
DID: pm/tools/store.py: additive `PROJECTION_VERSION`, `project()`, `Store.prefix`, `Store.is_semaphore`.
DID: pm/tests/test_views.py: 19 CLI-subprocess tests ported from the old board/overview tests (edges written to tickets.jsonl by a `block` helper because `dep` is unbuilt; ids tracked from `create` because `list` is unbuilt). No fixes were needed in validate.py or archive.py.
EVIDENCE:
/usr/bin/python3 -B -m unittest discover -s pm/tests -p test_views.py -> Ran 19 tests, OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k board -k overview --allow-pending -> parity: passed 0, pending 0, failed 0, skipped 0 (no parity test name matches board or overview; no pending lines)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p test_cli_contract.py -> Ran 31 tests, OK (skipped=10)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p test_gitcommit.py -> Ran 24 tests, OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending -> parity: passed 172, pending 92, failed 1, skipped 9
  the one failure: TicketCliTest.test_create_writes_blocks_and_blocked_by_edges (the known main failure)
  unbuilt verbs still needed: cross-store-edge, dep, edit, lint, list, note, ready, reparent, summary, unlink
COMMITS: frontier-clean 62765b6 (branch fc-913d02)
NOT DONE: byte-identity of board/overview against the old CLI on a live store is not diffed here (integration ticket); the `generated` timestamp differs per run by design.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/verbs/board.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/verbs/overview.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tests/test_views.py
