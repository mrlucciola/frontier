TICKET: fc-739601 -- pm read verbs: list ready (first of two workers; tree, summary remain)
DID: pm/tools/verbs/list.py: list with --status (repeatable), --label, --all-stores (rows gain `store`; frozen/unreadable store named on stderr as `skipped <path>: frozen` / `skipped <path>: <error>`), --json.
DID: pm/tools/verbs/ready.py: ready with --scope (epic subtree or label, neither is an error), --limit (>=1), frozen one-liner via routing.frozen_notice in text mode, --json.
DID: readiness across cross-store edges reuses store.is_ready (fails closed via routing.unsatisfied_cross); no store.py/routing.py edits. STATUSES lives in list.py and the subtree walk in ready.py (no shared helper yet; tree worker may want the walk). test_cli_contract.py cases ran and passed unchanged.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k list -k ready --allow-pending
  parity: passed 1, pending 10, failed 0, skipped 0
  unbuilt verbs still needed: claim, dep, summary
  (pending lines: CrossStoreEdgeTest.test_ready_hides_the_gate_until_the_blocker_closes (dep); CrossStoreEdgeTest.test_show_lists_remote_blockers_and_the_reverse_line (dep); CrossStoreEdgeTest.test_summary_lists_waiting_gates_in_text_only (summary); StoreRoutingTest.test_frozen_summary_and_ready_print_one_line_with_successor (claim); StoreRoutingTest.test_list_all_stores_tags_rows_with_store_and_skips_frozen_on_stderr (claim); StoreRoutingTest.test_stores_lists_and_check_passes (claim); StoreRoutingTest.test_where_mutate_refuses_an_already_closed_ticket_like_close (claim); TicketCliTest.test_blocks_gates_ready_until_closed (dep); TicketCliTest.test_ready_scope_and_limit (dep); TicketCliTest.test_summary_lists_stale_holds_only_when_session_is_gone (claim))
python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 15 tests ... OK (skipped=21)
python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests ... OK
full: parity: passed 25, pending 237, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, history, hold, lint, note, release, reparent, summary, validate
COMMITS: frontier-clean (see git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-739601 log -1 on branch fc-739601)
NOT DONE: Most list/ready parity tests are pending (they need claim/dep to build fixtures), so list --all-stores, ready --scope/--limit and cross-store readiness were not exercised by a passing parity test; only structural checks passed. Re-run those tests once claim and dep land. tree and summary belong to the second worker.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/list.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/pm/tools/verbs/ready.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-739601/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03b1-list-ready.md
