TICKET: fc-739601 -- pm verbs tree summary
DID: pm/tools/verbs/tree.py and pm/tools/verbs/summary.py new (tree impacts, blocked-by chain with remote leaves, subtree, archived refusal; summary sections, --limit, --json, pilot/hold/archive-hint/dirty/history-behind helpers kept in summary.py).
DID: pm/tools/store.py gains Store.walk(start, step) and Store.subtree(tid) (additive); pm/tools/verbs/ready.py drops its own subtree_ids and calls store.subtree.
DID: summary never writes: a owed history catch-up (history-pending marker on a history_ref store) calls store.unbuilt("history"); gitcommit.py offers no catch-up.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k tree -k summary -k HelpTextTest -k test_lint_and_summary_enforce_the_pilot_contract --allow-pending
  parity: passed 5, pending 14, failed 0, skipped 1  (OK, ran 20; pending are all on unbuilt claim/dep/history/lint/validate, e.g. test_epic_parent_and_tree (dep), test_lint_and_summary_enforce_the_pilot_contract (lint), test_summary_catches_up_a_pending_snapshot (history))
unittest discover -p test_cli_contract.py: Ran 15 tests OK (skipped=21)
unittest discover -p test_gitcommit.py: Ran 24 tests OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 26, pending 236, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, history, hold, lint, note, release, reparent, validate
COMMITS: /Users/matthias/projects/frontier-clean 134732a (branch fc-739601 tip, plus this report commit)
NOT DONE: Most tree/summary parity tests cannot run yet: they create state through unbuilt claim/dep/lint/history/hold, so they are pending, not passed; tree and summary behavior is untested against them. History catch-up in summary exits 70 via unbuilt("history") until fc-c5e673 lands. Not byte-compared with the old CLI on live stores (integration ticket).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/tree.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/summary.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/ready.py
