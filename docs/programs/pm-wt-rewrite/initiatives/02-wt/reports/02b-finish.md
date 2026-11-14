TICKET: fc-249727 -- wt verbs: finish and land (gate, rebase, ff-only merge, teardown, done)
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/tools/verbs/finish.zsh: new; finish and land (WT_VERB=land), refusals, .wt/gate and .wt/known-red ported in-file, rebase, ff-only x3, merged ref marker + `pm emit wt.merged`, teardown via lib, `pm done`, auto-park as `"$WT_COMPONENT/cli/wt" park <id> --auto` subprocess (exit 70 passes through).
- Overseer fix applied: the "ticket has a note" check for `--findings none` on a findings_required store now reads `pm show <id>` text and looks for a line starting `notes:` or `notes (last` (design.md "Output"), no JSON.
- Deviation from the old order: pm refuses `--findings none` without a reason, so teardown supplies `-m "wt finish: merged <id> into <default>"` when findings is `none` and no note exists (also in the rendered `pm done` command). A pm done failure after the merge: status already `done` -> `wt:` "merged ... `pm done` failed" line; otherwise the `OK: ... ticket NOT closed: pm refused (...) ... run <pm done command>` line, exit 0. No pm exit code is relied on.
EVIDENCE:
Hand check of the notes pattern (throwaway repo under $TMPDIR/hc1, `git init` succeeded, script /Users/matthias/projects/frontier-clean/.worktrees/fc-249727/.tmp/hc.zsh):
  `pm show hc-1` before `pm note`: "hc-1  P2  open  t" -> RESULT: no note
  `pm show hc-1` after `pm note hc-1 "a note"`: "...\n\nnotes:\n  2026-11-14 claude: a note" -> RESULT: has note
  (pattern: [[ $log != (#s)(*$'\n')#(notes:|notes \(last)* ]] under extendedglob; the "(last 5 of N" heading form was not produced, only read from design.md:207-208)
/bin/zsh -n .../wt/tools/verbs/finish.zsh -> exit 0, no output
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending
  Ran 125 tests in 130.404s / OK (skipped=2)
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/cli/wt (pm new)
  wt suite: passed 79, pending 44, skipped 2, failed 0
  `pending:` lines naming finish or land as first unbuilt step (all pending on `park`, the subprocess exit 70):
    FinishTest.test_every_refusal_names_a_next_step: `wt finish tkr6-1` (conflict subcase; earlier subcases passed)
    FinishTest.test_ffonly_retries_exhausted_auto_parks, test_infra_fault_line_names_the_recorded_path, test_rebase_conflict_auto_parks: `wt finish tk-1`
    FinishTest.test_land_ffonly_exhaustion_auto_parks, test_land_rebase_conflict_auto_parks: `wt land tk-1`
  Other pending name park, prune, status or selftest. No failed test anywhere.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-249727 a1114c7, 907bc93 (branch fc-249727)
NOT DONE:
- Auto-park tests above are pending until park merges; overseer re-runs them after both branches merge. The `nested` subcase of test_every_refusal_names_a_next_step runs after the conflict subcase and was not reached (other nested-repo refusal tests pass).
- The findings_required + `none` + no note refusal path itself is not covered by a suite test; only the pattern was proven by hand.
- Not hand-checked: a gate that fails to start (reports as gate failure, exit 126/127), known-red indentation-tree coverage beyond the three suite cases.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-249727/wt/tools/verbs/finish.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02b-finish.md
