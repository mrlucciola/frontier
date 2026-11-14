TICKET: fc-249727 -- wt verbs: finish and land (gate, rebase, ff-only merge, teardown, done)
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/tools/verbs/finish.zsh: new; finish and land (WT_VERB=land), refusals, .wt/gate and .wt/known-red ported in-file, rebase, ff-only x3, merged ref marker + `pm emit wt.merged`, teardown via lib, `pm done`, auto-park as `"$WT_COMPONENT/cli/wt" park <id> --auto` subprocess (exit 70 passes through).
- Deviation from the old order: pm refuses `--findings none` without a reason, so teardown supplies `-m "wt finish: merged <id> into <default>"` when findings is `none` and no note exists (also in the rendered `pm done` command).
- A pm done failure after the merge: ticket status `done` already -> `wt:` line "merged ... `pm done` failed" (test_stale_worktree_of_a_closed_ticket); otherwise the `OK: ... ticket NOT closed: pm refused (...)... run `cd <store> && pm done ...`` line, exit 0. No pm exit code is relied on.
EVIDENCE:
/bin/zsh -n .../wt/tools/verbs/finish.zsh -> exit 0, no output
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending
  Ran 125 tests in 132.210s / OK (skipped=2)
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/cli/wt (pm new)
  wt suite: passed 79, pending 44, skipped 2, failed 0
  `pending:` lines naming finish or land as the first unbuilt step (all pending on `park`, the subprocess exit 70):
    FinishTest.test_every_refusal_names_a_next_step: first unbuilt step `wt finish tkr6-1` (conflict subcase; the subcases before it passed)
    FinishTest.test_ffonly_retries_exhausted_auto_parks, test_infra_fault_line_names_the_recorded_path, test_rebase_conflict_auto_parks: `wt finish tk-1`
    FinishTest.test_land_ffonly_exhaustion_auto_parks, test_land_rebase_conflict_auto_parks: `wt land tk-1`
  Pending naming park (not finish): DeferredTeardownTest.test_park_deferred, test_zero_delta_park_deferred; NeverForceTest.test_start_park_never_forces; ResolutionTest.test_park_takes_store_and_repo_flags, test_undeclared_pair_refuses_park_and_mutates_nothing, test_registered_prefix_resolves_finish_and_park_too; ParkTest.* and others. Other pending: prune, status, selftest.
  No failed test in FinishTest, the finish cases of DeferredTeardownTest (test_finish_deferred green), NeverForceTest (start_finish, failed_remove green) or ResolutionTest.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-249727 a1114c7 (branch fc-249727)
NOT DONE:
- Auto-park tests (list above) are pending until park merges; overseer re-runs them after both branches merge. The `nested` subcase of test_every_refusal_names_a_next_step runs after the conflict subcase, so it was not reached; the other nested-repo refusal tests pass.
- Unverified: the findings_required + `--findings none` + no note case reads existing notes by looking for a non-empty `"text":"..."` in `pm log <id>` output (no test covers it; I did not inspect pm log's shape). If the ticket body event also carries `text`, the pre-merge refusal never fires and pm's own refusal lands after the merge.
- `land` success line says "To keep working: `wt start <id>`" instead of the old `pm ticket release` text (no `release` verb in the new pm); the overseer may want other wording.
- Not hand-checked: gate that fails to start (a non-runnable executable reports as a gate failure with exit 126/127), known-red indentation-tree coverage beyond the three suite cases.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/tools/verbs/finish.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02b-finish.md
