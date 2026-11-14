TICKET: fc-459fe0 -- pm routing (02b: where and stores verbs)
DID: pm/tools/verbs/where.py (new): port of cmd_where incl. --mutate preflight with --verb/--findings, writes nothing.
DID: pm/tools/verbs/stores.py (new): port of cmd_stores, listing plus --check (all checks in its help, exit 2).
DID: pm/tools/store.py (additive, no signature changed): status_hint, refuse_if_unclaimed, refuse_if_closed, close_open_children, parse_findings (raise TicketError; function-level `import routing`; use store.cross_cache) for reuse by close/release (fc-d73327). Nothing added to routing.py.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_where -k test_stores -k HelpTextTest --allow-pending
  parity: passed 2, pending 23, failed 0, skipped 0
  unbuilt verbs still needed: claim, dep, validate
  pending (all): CrossStoreEdgeTest.test_stores_check_reports_dangling_and_blocker_side_edges (dep); HelpTextTest.test_validate_help_names_version_and_exits (validate); StoreRoutingTest: test_stores_check_flags_a_bad_successor, test_stores_check_reports_a_bad_role_as_exit_2_naming_it, test_stores_check_reports_a_malformed_registry_as_exit_2, test_stores_check_reports_foreign_prefix_rows, test_stores_check_reports_missing_path_and_collision, test_stores_check_reports_two_frozen_owners_but_not_a_symlink_twin, test_stores_lists_and_check_passes, test_where_findings_needs_mutate, test_where_mutate_accepts_good_findings, test_where_mutate_passes_for_a_live_id_and_writes_nothing, test_where_mutate_refuses_a_frozen_store, test_where_mutate_refuses_an_already_closed_ticket_like_close, test_where_mutate_refuses_an_epic_with_open_children_like_close, test_where_mutate_refuses_an_unknown_id, test_where_mutate_refuses_an_untrusted_registry_even_for_the_cwd_store, test_where_mutate_release_needs_a_claim_like_release, test_where_mutate_validates_findings_with_the_close_parser, test_where_prints_the_owning_repo_root, test_where_refuses_with_the_design_text_when_nothing_owns_the_prefix, test_where_verb_needs_mutate_and_release_takes_no_findings, test_where_works_outside_any_store (all claim)
  (passed: HelpTextTest.test_stores_check_help_names_checks and one more)
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k StoreRoutingTest --allow-pending
  parity: passed 0, pending 67, failed 0, skipped 0
  unbuilt verbs still needed: claim
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'  -> Ran 15 tests ... OK (skipped=21)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'  -> Ran 24 tests ... OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 21, pending 241, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, history, hold, lint, list, note, ready, release, reparent, summary, validate
Smoke (.tmp/smoke2.py, temp stores in $TMPDIR, mirrors the pending where/stores tests, rows set by editing tickets.jsonl since claim/close are unbuilt): `FAILS 0 []`, 54 PASS lines. Covered: where bare/prefix/outside-store/unowned design text; --mutate live/cross/outside-store, frozen via cwd and --store, unknown id, untrusted registry, findings (bad, none+ids, empty entry, unknown, foreign, good), already closed, release unclaimed/closed/claimed, epic open children then closed, --verb/--findings flag errors; stores listing, OK: 3 stores, missing path, live collision, successor (non-frozen, non-dir), bad role, malformed registry exit 2, foreign-prefix row, two frozen owners but not a symlink twin, dangling cross edge, cross-store blocks edge on blocker.
COMMITS: frontier-clean 399d93f (code, branch fc-459fe0); the report lands in the next commit on the same branch
NOT DONE: Parity not proven by the suite for 21 where/stores tests (setUp calls claim) and the dep-dependent dangling test; re-run `-k test_where -k test_stores` once claim, close, dep land. Stores --check on the old-store "--mutate ... release of claimed" path proven only via patched rows. Test-side: none looked wrong.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/pm/tools/verbs/where.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/pm/tools/verbs/stores.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/.tmp/smoke2.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/.tmp/g1.txt
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/.tmp/g3.txt
/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/02b-where-stores.md
