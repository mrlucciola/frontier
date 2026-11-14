TICKET: fc-30c060 -- wt characterization part 4: status, prune, resolution
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: adapter methods register_store and blockers (both sides) plus AdapterTest.test_register_store_and_blockers
DID: same file: StatusPruneTest (11 tests: status x4, park --waits-on <id>, pending, prune x3, start-runs-prune-quietly, start twice, selftest) and ResolutionTest (9 tests)
DID: no wt/docs/uncovered.md needed; every case ran (remaining-registrations line provoked with the git shim)
EVIDENCE:
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
wt suite: passed 95, pending 0, skipped 0, failed 0
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm new --allow-pending -k AdapterTest
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm new)
wt suite: passed 9, pending 0, skipped 0, failed 0
(the pending test skips itself on the new side, "dropped for pm ls parked"; the full new-side run was not made, only AdapterTest as the prompt asked)
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060 8cbfd20 (branch fc-30c060)
NOT DONE: NONE of the prompt's list. Findings for the overseer (old wt behavior pinned, not contract-stated):
- start twice from the same session (test_start_twice_from_the_same_session): old wt adopts the claim, then fails in `git worktree add` (already exists): exit 1, `wt: git worktree add for <id> failed`, fault row, no OK. A new wt that treats a live worktree as resumable would differ; decide which.
- `wt start` runs prune on every call, so two stale registrations made before a second start collapse; prune test starts both tickets before deleting directories.
- Any cross-repo call (registered prefix elsewhere, --store, --repo with cwd in another repo) is refused by old wt unless the git-pairs file declares the pair (`wt: cross-repo commit into ... is not a declared git-pairs pair`). Not in the contract's resolution section; tests declare pairs in the private GIT_PAIRS_FILE (ResolutionTest.pair). The new wt needs the same rule or the tests need it dropped.
- Old pm drops a closed blocker from `blocked_by`; pinned in the pending test. The old `pending` line is `<id>  P<n>  clean|CONFLICT  <title>`; no-match line is `no done-unmerged tickets with cleared blockers`.
- Old registry entry holds a path only (prefix comes from the store's config.json), so register_store(prefix, repo) on the old side ignores `prefix`; the caller must have made the store with that prefix.
- Prune deletes a branch only from cleared registrations or refs/wt/merged markers; an unmarked merged branch (`plain-merged`) is kept. Pinned in test_prune_keeps_a_branch_a_worktree_holds.
- No contradiction with the contract found that needs a named test; I did not re-read contract.md line by line beyond the verbs the tests quote.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-4-status.md
