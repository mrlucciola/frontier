TICKET: fc-2b34c9 -- pm core (worker b: gitcommit)
DID: pm/tools/gitcommit.py (commit_store policy, commit_paths, commit_blob_to_ref, GitFault, scrubbed GIT_* env, classifier/announce/guard_env/on_failure folded from gitfault.py; report writer dropped)
DID: pm/tools/store.py (commit() calls gitcommit.commit_store; policy skip -> one stderr line + by-hand command; GitFault -> same + git output + GitCommitFailed; history_ref store -> history-sync line, history-pending marker on fault, no raise; new GitCommitFailed, GIT_COMMIT_FAILED_EXIT=3, HISTORY_PENDING; no existing signature changed), pm/tools/ticket (except store.GitCommitFailed -> exit 3, silent as the old entry)
DID: pm/tests/test_gitcommit.py (22 tests: old test_gitcommit.py whole, ClassifyTest, announce/guard cases; imports the module by path)
EVIDENCE:
$ /usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
Ran 22 tests in 1.024s / OK
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_init -k HelpTextTest.test_epilog_exit_codes
parity: passed 3, pending 0, failed 0, skipped 0
$ /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending   (exit 0, output in .tmp/parity-full.txt)
cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/ticket
parity: passed 3, pending 258, failed 0, skipped 9
unbuilt verbs still needed: create, list, ready, release, stores, validate
(Commands run by absolute path: the cd hook refuses `cd <worktree> && ...`.)
COMMITS: frontier-clean 2d14d4b on fc-2b34c9 (report committed after; see branch tip)
NOT DONE: Dropped tests, "report writer dropped": test_gitfault.ReportTest.test_report_writes_a_dedup_file_for_identity_missing, test_two_occurrences_same_day_collapse_into_one_file, test_report_writer_unimportable_degrades_to_none (the setUpModule CLAUDE_SIGNING_REPORT_DIR patch also dropped).
NOT DONE: The store.commit wiring (exit 3, by-hand text, history marker) is not exercised by any test: every parity test that commits needs the unbuilt create verb; worker d's contract tests or the create worker should cover it. I smoke-checked nothing end to end.
NOT DONE: commit_store takes ticket_file="tickets.jsonl" (spec v2 only; no ticket_filename/legacy flag, since pre-v2 stores are refused). The old `legacy=True` path for `history enable` is not ported; the history verb worker must add it if needed.
NOT DONE: the old gitfault announce text dropped its cl-ids ("cl-2ccf74/A15", "cl-9a7d54") from REMEDY lines; the exact remedy commands are unchanged. The off-branch reason keeps "(cl-111ef6)" because parity test line 1629 asserts it.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/gitcommit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tests/test_gitcommit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-b.md
