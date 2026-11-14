TICKET: fc-917232 -- wt verb: park
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/tools/verbs/park.zsh: new verb, ported from old cmd_park in the old order (no-worktree, merged route via pm done, .local, guards, undeletable, findings, mass-deletion, WIP commit, zero-delta pm drop, else pm park note, teardown, pm link, pm emit wt.park); --auto prints only the note.
- pm park takes only `-m`, so --findings is recorded as `findings=` on `pm emit <id> wt.park`, not passed to pm park.
- Ruling 4 applied: `--findings none` on a findings_required store with no --note passes only when `wt_pm "$store" "" show "$id"` prints a line starting `notes:` or `notes (last` (`_wt_park_has_note`); else refused before anything changes.
EVIDENCE:
- `/bin/zsh -n .../wt/tools/verbs/park.zsh` -> exit 0, no output
- Hand proof under $TMPDIR (.tmp/note_proof.py: git init ok, pm/cli/pm on PATH, `_wt_park_has_note <repo> <id>`): no note -> `rc=1`; after `pm note <id> "a note"` -> `rc=0`.
- `/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending`:
  `cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/cli/wt (pm new)`
  `wt suite: passed 61, pending 62, skipped 2, failed 0`
- pending lines naming park as first unbuilt step: none.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-917232 bc6fad5, d71b956 (branch fc-917232)
NOT DONE:
- The refusal path of the notes rule is proven only through the helper (rc=1/0), not end to end through `wt park`: no suite test covers it.
- Not covered by the suite, written from the old source: the park --auto path and the merged route's failed-remove branch.
- Accepted rulings applied as reported: `--waits-on` ticket-id test is regex plus `pm get <it> status`; PM_ACTOR exported from the holder on the unmerged route only; merged-route `pm done` gets a fallback `-m` text.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-917232/wt/tools/verbs/park.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-917232/.tmp/note_proof.py
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02c-park.md
