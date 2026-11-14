TICKET: fc-30c060 -- wt characterization part 2b: finish merge paths and teardown
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: adapter `findings(repo, ticket)` on both sides, `AdapterTest.test_findings_reader`, 2a's `--findings` test now asserts the value, `started()` gained `name` and `labels`, 12 new `FinishTest` cases (rebase-conflict auto-park, ff-only retry absorbs one move, three moves auto-park, refusal after merge, merged-marker route, nested repo refusal, `.vscode` refusal, failed remove `STOP.`, failed-remove leaves nothing to adopt, table-driven "every refusal names a next step").
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/docs/uncovered.md: new; deferred teardown (operator `wt selftest`) and the `.vscode` fallback.
DID: ff-only retries provoked with a `post-rewrite` hook via `core.hooksPath` that commits to main; main is moved once before finish so the rebase rewrites and the hook fires (a no-op rebase fires nothing).
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
  cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
  wt suite: passed 51, pending 0, skipped 0, failed 0
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm new --allow-pending -k AdapterTest
  cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm new)
  wt suite: passed 8, pending 0, skipped 0, failed 0
(The old-side full run preceded a one-line new-side-only edit to the findings reader test's `pm done` call, which the new-side run covers.)
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060 3a4b9fe
NOT DONE:
- Deferred teardown cannot be provoked on purpose; listed in uncovered.md with the operator command.
- Old wt vs contract, pinned as old wt behaves:
  1. `test_rebase_conflict_auto_parks`: contract "Reading wt output" says `wt start` resumes an auto-parked ticket; old `start` rebases, hits the same conflict, exits 1 with `wt: resuming <id>: rebase onto main conflicted; worktree removed again, branch kept`. The test pins that.
  2. `test_failed_remove_prints_stop`: contract line 111 says the STOP line never invites `--force`; old wt's STOP line (all one line, starting `wt: STOP.`) hands the operator `git worktree remove --force` in its operator-run cleanup. Pinned: `--force` appears only after `operator-run`.
  3. `test_failed_remove_leaves_nothing_for_finish_to_adopt`: contract line 198 says `wt finish <id>` handles a stale worktree; after a failed remove git has already dropped the registration, so old `finish` answers `wt: no worktree at <path> for <id> -- nothing to finish` and the ticket stays taken. The stale-and-merged route is only reached in the suite by building it by hand (`test_stale_merged_worktree_is_torn_down_and_closed`).
- `refs/wt/merged/<id>` is cleared when the branch is deleted, so after a clean finish it is absent; the test asserts the marker in the failed-remove case (branch kept) and via the hand-built stale case.
- `.vscode` refusal runs here; in a sandbox that denies it the test skips itself and `skipped 0` fails the gate (noted in uncovered.md).
- Old rebase-conflict park also leaves main with pm's ticket commit; the test asserts main's content and ancestry, not an unchanged SHA.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/docs/uncovered.md
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-2b-finish-merge.md
