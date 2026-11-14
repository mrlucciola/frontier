TICKET: fc-2b34c9 -- pm core (worker a: entry, store module, init)
DID: pm/cli/pm (dispatcher), pm/tools/ticket (entry, kept-verb tuple, lazy verb import, unbuilt for missing verb files)
DID: pm/tools/store.py (find_store with worktree resolution, Store load/get/read/archived lookup, locked_store, atomic save, commit stub calling unbuilt("gitcommit") inside a git work tree, unbuilt())
DID: pm/tools/verbs/init.py (port of cmd_init, same output, refusals, .gitignore lines)
EVIDENCE:
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_init -k HelpTextTest.test_epilog_exit_codes
parity: passed 3, pending 0, failed 0, skipped 0
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending   (exit 1)
Ran 271 tests in 44.415s / FAILED (errors=1, skipped=9)
cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/ticket
parity: passed 3, pending 258, failed 1, skipped 9
unbuilt verbs still needed: create, list, ready, release, stores, validate
COMMITS: frontier-clean c7f2484 on branch fc-2b34c9 (report committed after; see branch tip)
NOT DONE: Second gate command fails (failed 1, not 0). The one failure is ValidateTest.test_archive_year_filename_follows_spec_version (test_cli_parity.py:1354-1359): it does `import ticket_core` from the CLI's directory and calls ticket_core.archive_year_filename(1|None|2, "2026"). That imports an old internal module, which the rewrite does not have (component principles rule 5; cut-list "Old tests not carried over"). I did not edit the test or add a ticket_core shim. Overseer ruling needed: remove or replace it (the CLI-level `test_archive_on_v2_store_writes_tickets_year_file` already covers the v2 filename). The other 258 pending tests wait on unbuilt verbs (create, list, ready, release, stores, validate; "show" and the rest are not exercised first).
NOT DONE: Pre-v2 refusal text and read/mutation lookups are untested by parity (no test); the contract tests (worker d) should cover compacted and archived ids.
NOT DONE: GitCommitFailed (exit 3) is not wired in tools/ticket; the epilog states exit 3 and 70. Worker b (gitcommit.py) adds it.
NOT DONE: frozen-store refusal and routing are absent by design (fc-459fe0).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/cli/pm
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/verbs/init.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-a.md
