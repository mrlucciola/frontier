TICKET: fc-739601 -- pm read verbs (finish)
DID: pm/tools/verbs/summary.py: an owed history snapshot is now built via gitcommit.commit_store under the store lock (marker cleared on success, "history is pending" note on failure), replacing store.unbuilt("history").
DID: the now-runnable list/ready/tree/summary tests needed no other change; all pass or stay pending on dep/lint.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k list -k ready -k tree -k summary -k test_summary_catches_up --allow-pending
  parity: passed 15, pending 9, failed 0, skipped 1
  pending: CrossStoreEdgeTest.test_ready_hides_the_gate_until_the_blocker_closes (dep)
  pending: CrossStoreEdgeTest.test_show_lists_remote_blockers_and_the_reverse_line (dep)
  pending: CrossStoreEdgeTest.test_summary_lists_waiting_gates_in_text_only (dep)
  pending: CrossStoreEdgeTest.test_tree_shows_remote_blockers_as_leaves (dep)
  pending: TicketCliTest.test_blocks_gates_ready_until_closed (dep)
  pending: TicketCliTest.test_epic_parent_and_tree (dep)
  pending: TicketCliTest.test_lint_and_summary_enforce_the_pilot_contract (lint)
  pending: TicketCliTest.test_ready_scope_and_limit (dep)
  pending: TicketCliTest.test_summary_surfaces_semaphores_and_unmerged (dep)
test_cli_contract.py: Ran 31 tests, OK (skipped=11)
test_gitcommit.py: Ran 24 tests, OK
full run: parity: passed 123, pending 141, failed 1, skipped 9
unbuilt verbs still needed: archive, cross-store-edge, dep, edit, lint, note, reparent, unlink, validate
COMMITS: frontier-clean (see git log on branch fc-739601, tip commit "pm reads: summary history catch-up; now-runnable read tests (fc-739601)")
NOT DONE: full run has 1 failure outside my write set: test_cli_parity.TicketCliTest.test_create_writes_blocks_and_blocked_by_edges -- merged `create` (pm/tools/verbs/create.py) does not accept --blocks/--blocked-by (argparse rc=2 "unrecognized arguments"). Needs a create fix by its owner (likely depends on dep edge code). Not in the four read verbs.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/summary.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03b3-reads-finish.md
