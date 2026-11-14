TICKET: fc-30c060 -- wt characterization part 6a (review gaps in finish, land, teardown)
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: 12 review items closed (+16 tests: 111 total, was 95); new classes/tests are land refusals/gate (5), ff-only two-move + counter 6 pin, failed-remove shapes (2), fault-row (2), cross-repo guard (3), NeverForceTest (3 runs with logging git and rm shims).
DID: same file: tightened happy-path branch removal (deferred escape dropped), rev-list --merges empty, NOT-closed OK line, STOP text regex, deferred line/OK text, land branch removal.
DID: no WT/docs/uncovered.md written: every case ran sandboxed here.
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
  Ran 111 tests in 218.348s / OK
  wt suite: passed 111, pending 0, skipped 0, failed 0
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
  OK (skipped=2)
  wt suite: passed 9, pending 100, skipped 2, failed 0
  (skips: test_two_owners_stop_with_a_wt_line, test_pending_lists_done_unmerged_with_cleared_blockers; both pre-existing)
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060 f82be24 (branch fc-30c060)
NOT DONE:
- Item 5 vs contract (99-103, 163-165): the old wt does NOT dedup rows. faultreport.append keeps one file per (root cause, day) and appends one row per occurrence. Pinned in test_fault_row_ends_the_line_with_reported_path_and_dedups (one file, 2 rows after 2 runs). Contract line 100 says "one deduplicated row"; contract line 163 says the line ends `(reported: <path>)`.
- Item 5, the `(reported: <path>)` suffix: in the old wt only `infra=False` failures (cross-repo refusal, start mass-deletion refusal) end that way. Infra failures (rebase conflict, STOP, deferred) say `Recorded in <path>. This is infrastructure, not a finding`. Both pinned (test_fault_row_..., test_infra_fault_line_names_the_recorded_path). Pinned the old wt; the contract wording is imprecise.
- Item 3: only the cross-repo `start --store`, `start --repo`, and `finish --store/--repo` guards are tested. Not tested: guard on park, and the "pair declared for commit but not worktree" partial case.
- Item 4: `rm -rf` is observed only through a logging `rm` shim; wt in Python could delete via shutil, which no shim sees. The old wt has no such call in wt_core.py (rg for rm -rf shows only handoff text).
- Item 1 land conflict/ff-only: auto-park moves main via pm's own commits, so the tests assert ancestry and README content rather than an unchanged HEAD.
- Not in my list (6b): the other review findings (stale closed worktree, session token sources, `where` failure texts, prune Operator line, .vscode on park, selftest scratch, no-actor first words, etc.).
- AGENTS.md in wt/ says not to edit test_wt_cli.py after acceptance; I edited it because the prompt directs it.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/.tmp/commit-msg-fc-30c060-6a.txt
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-6a-review-finish.md
