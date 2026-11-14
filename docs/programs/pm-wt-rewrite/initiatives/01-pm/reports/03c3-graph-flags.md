TICKET: fc-c10bcf -- structure verbs (03c3: create --blocks/--blocked-by, dep several targets and --note)
DID: pm/tools/verbs/create.py: --blocks/--blocked-by parsed and written in the same call (all or nothing); pm/tools/verbs/dep.py: DST nargs="+", --note, plan-then-write; pm/tools/store.py: added priority_type and would_cycle (moved out of create.py/dep.py); pm/tools/verbs/edit.py imports priority_type from store.
DID: pm/tools/ticket route_edge: dst may be a list (old CLI route_edge shape); without it every multi-dst dep crashed in routing (outside the named write set, needed for the parity tests).
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k dep -k unlink -k reparent -k edit -k note -k CrossStoreEdgeTest -k DuplicateGuardTest -k test_create --allow-pending
  parity: passed 43, pending 22, failed 0, skipped 1
  pending lines (22): all name unbuilt verbs in parentheses, none dep/unlink/reparent/edit/note:
  CrossStoreEdgeTest: test_an_unregistered_blocker_keeps_the_gate_hidden (ready); test_dep_from_an_unrelated_cwd_mutates_the_blocked_stores_repo (ready); test_dep_related_stays_on_the_source_as_prefix_slash_id (ready); test_json_projections_keep_their_shape (ready); test_local_only_stores_never_read_the_registry (ready); test_local_pairs_still_run_todays_code (ready); test_ready_hides_the_gate_until_the_blocker_closes (ready); test_summary_lists_waiting_gates_in_text_only (summary); test_tree_shows_remote_blockers_as_leaves (tree); test_unlink_blocks_removes_the_blocked_by_in_either_form (ready); test_validate_flags_a_blocked_by_without_a_cross_store_target (validate)
  DuplicateGuardTest.test_new_writes_the_row_and_the_marker (validate)
  TicketCliTest: test_create_can_claim_in_the_same_call (ready); test_create_refuses_title_over_limit_and_writes_nothing (list); test_create_refuses_to_claim_an_epic (list); test_create_writes_blocks_and_blocked_by_edges (ready); test_dep_blocks_several_targets_all_or_none (ready); test_edit_append_body_to_nonempty_body_records_history (lint); test_edit_priority_and_body_preserves_ticket_and_records_history (lint); test_lifecycle_verbs_write_their_kind_and_show_hides_edit_trail (lint); test_note_kind_is_stored_and_optional (lint)
  ValidateTest.test_I14_notes_out_of_order (validate)
unittest discover -p test_cli_contract.py: Ran 31 tests ... OK (skipped=1)
unittest discover -p test_gitcommit.py: Ran 24 tests ... OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 139, pending 126, failed 0, skipped 9
  unbuilt verbs still needed: archive, lint, list, ready, summary, tree, validate
Note: the three named parity tests run through their dep/create steps and pend only at the final `ready` call (unbuilt); the earlier argparse exit-2 failure of test_create_writes_blocks_and_blocked_by_edges is gone (failed 0).
COMMITS: frontier-clean (see git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf log --oneline -n 1) on branch fc-c10bcf
NOT DONE: (1) the three named parity tests cannot fully pass until `ready` is built; their dep/create writes are exercised but the final read is unproven. (2) pm/tools/verbs/close.py:9 imports `from verbs.release import acting_identity`, a verb-imports-verb breach of the 03c3 rule; outside my write set, left as is. (3) Old dep refusals now end "; nothing written" per 944f3cda; the stricter text was ported, existing parity passes.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/create.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/dep.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/edit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03c3-graph-flags.md
