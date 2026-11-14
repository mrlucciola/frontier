TICKET: fc-2b34c9 -- pm core (worker c: create and show)
DID: pm/tools/verbs/create.py (port of cmd_create, every flag, duplicate guard whole incl. --json candidates/--new marker/--dup-of finding note, discovered-from to compacted/archived ids, remote ref -> unbuilt("cross-store-edge"), subject "pm: create <minted id>")
DID: pm/tools/verbs/show.py (port of cmd_show text/--json/--notes/--all-notes/archived/compacted/subtasks/parent title; remote edge or unowned prefix -> unbuilt("routing"); registry-lists-a-store -> unbuilt("routing"); new --field, mutually exclusive with --json)
DID: pm/tools/store.py additive: Store.blockers_of/children/is_ready, title_problem, label_problem, make_note, session_token, session_assignee, owned_prefixes, ref_prefix, local_id, is_remote_ref (no existing signature changed)
EVIDENCE:
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_create_show_roundtrip
parity: passed 1, pending 0, failed 0, skipped 0
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k DuplicateGuardTest -k test_archived_id_is_refused_as_archived_not_as_unknown -k test_create -k AutoCommitTest
Ran 30 tests ... OK (exit 1 only because pending tests exist without --allow-pending)
pending: DuplicateGuardTest.test_match_survives_closing_within_the_window (close); DuplicateGuardTest.test_new_writes_the_row_and_the_marker (validate); ValidateTest.test_archived_id_is_refused_as_archived_not_as_unknown (claim); CrossStoreEdgeTest.test_create_discovered_from_takes_a_cross_store_id (cross-store-edge); StoreRoutingTest.test_create_mints_the_primary_prefix_only (claim); TicketCliTest.test_create_can_claim_in_the_same_call (ready); test_create_refuses_title_over_limit_and_writes_nothing (list); test_create_refuses_to_claim_an_epic (list); AutoCommitTest x9 (close/claim/note/archive/summary)
parity: passed 13, pending 17, failed 0, skipped 0
$ /usr/bin/python3 -B -m unittest discover -s pm/tests -p test_gitcommit.py
Ran 22 tests / OK
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending   (exit 0)
parity: passed 20, pending 241, failed 0, skipped 9
unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, history, hold, lint, list, note, ready, release, reparent, stores, summary, validate
COMMITS: frontier-clean 2742251 on fc-2b34c9 (report committed after; see branch tip)
NOT DONE: AutoCommitTest still does not exercise store.commit: all 9 of its tests are pending on close/claim/note/archive/summary, none reaches create alone. The commit wiring is covered only by test_create_show_roundtrip passing (policy path); exit 3 and history-pending paths remain untested end to end.
NOT DONE: --field unknown-field message is "pm: show: no field <name>; fields: <sorted, comma-separated>" (prompt did not fix the list format). No test covers --field or --field/--json exclusion (argparse mutually exclusive group, exit 2).
NOT DONE: claim_veto is inlined in create (epic only; status/assignee cases cannot arise for a new row); the claim worker may want it in store.py. Cross-store parts of show (cross_blockers, "blocks (other stores)" contents) are unbuilt stubs awaiting routing.py.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/verbs/create.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/verbs/show.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-c.md
