TICKET: fc-917232 -- wt verb: park
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/tools/verbs/park.zsh: new verb, ported from old cmd_park in the old order (no-worktree, merged route via pm done, .local, guards, undeletable, findings, mass-deletion, WIP commit, zero-delta pm drop, else pm park note, teardown, pm link, pm emit wt.park); --auto prints only the note.
- pm park takes only `-m` (design.md Verbs), so --findings is not passed to pm on a park; it is recorded as `findings=` on the `pm emit <id> wt.park` event. The zero-delta and merged routes follow the suite.
EVIDENCE:
- `/bin/zsh -n .../wt/tools/verbs/park.zsh` -> exit 0, no output
- `/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending`:
  `cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/cli/wt (pm new)`
  `wt suite: passed 61, pending 62, skipped 2, failed 0`
- pending lines naming park as first unbuilt step: none (every pending test names finish, land, prune, status or selftest; ParkTest.test_start_resumes_the_parked_work_and_finish_merges_it names finish).
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-917232 bc6fad5 (branch fc-917232)
NOT DONE:
- Decisions for the overseer: (1) `--waits-on` counts as a ticket id when it matches `^[a-z0-9]+-[a-z0-9]+$` AND `pm get <it> status` succeeds (the old `-[0-9a-f]{6}` regex does not match new ids like tk-2). (2) Resume-line actor is read from the holder (`${holder%%#*}`, prefix up to `:` or `/` stripped); the verb exports PM_ACTOR=<that actor> so pm "yours" holds when no session token exists (suite: test_resume_line_has_no_session_when_none_is_given). Only set on the unmerged route; the merged route does not export it. (3) Merged route: `pm done` gets a fallback `-m "already merged into <default>; worktree torn down by wt park"` when no --note, because pm refuses `--findings none` without a reason. (4) `--findings none` on a findings_required store with no --note is refused without looking at existing ticket notes (no pm field exposes them); pm's own done check still applies on the merged route, after teardown.
- Not covered by the suite, written from the old source: the park --auto path (finish's interface) and the merged route's failed-remove branch.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/tools/verbs/park.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02c-park.md
