TICKET: fc-03292e -- wt instruction delivery: help that teaches, plugin hints, no skill
DID: wt/cli/wt now has the one verb table plus `wt help` and `wt help <verb>`; leading comments of wt/tools/verbs/{start,finish,park,status,prune,selftest}.zsh are each verb's help; start prints an "edit only under it" line after OK (wt/tools/verbs/start.zsh:152); STOP line shortened (wt/tools/lib/teardown.zsh:116)
DID: wt/tests/test_budgets.py (help < 1200, verb help < 700, failure line < 400); wt/docs/instruction-map.md maps every line of SKILL.md 1-120 and CLAUDE.md 142-145 and 160-170, plus the old contract's environment sections; wt/docs/contract.md gains "Rules wt does not enforce", E2BIG/allow-list and Codex no-escalation bullets, and "Help and byte ceilings"
DID: wt/AGENTS.md links the map and lists the budget test, so docs/check_structure.py passes
EVIDENCE:
$ /usr/bin/python3 -B wt/tests/run_wt.py --cli wt/cli/wt --pm new
  wt suite: passed 123, pending 0, skipped 2, failed 0   (exit 0; first run failed 3 tests pinning "operator-run, in order" in the STOP line, fixed by keeping that text)
$ /usr/bin/python3 -B pm/tests/run_transcripts.py --dir wt/tests/t
  transcripts: passed 3, failed 0
$ /usr/bin/python3 -B -m unittest discover -s wt/tests -p 'test_budgets.py' -v
  Ran 5 tests ... OK. wt help 748/1200; verb helps 157-676 of 700 (park 676, finish and land 648, start 573); longest failure template 372/400; 21 live usage-failure lines 58-159 of 400
$ python3 -B docs/check_structure.py
  check_structure: ok (7 components, 3 exempted)
$ python3 -B .tmp/map_check.py   (reads wt/docs/instruction-map.md; also checks cited file:line is within the file)
  SKILL uncovered: [] double: [] outside: []
  CLAUDE uncovered: [] double: [] outside: []
  rows 61 problems []
REVIEW FIXES (second round, all three applied): STOP line restored to "against this worktree" (wt/tools/lib/teardown.zsh:116, err cap 100 kept; longest failure template still 372/400, byte count unchanged); wt/docs/instruction-map.md coverage-script paragraph deleted; wt/AGENTS.md prose now says the fourth line runs the transcripts and the last runs the byte-ceiling tests. Re-ran once each after the fixes: run_wt.py "wt suite: passed 123, pending 0, skipped 2, failed 0"; test_budgets.py "Ran 5 tests ... OK"; check_structure "ok (7 components, 3 exempted)"; map_check.py re-run, same output as above.
COMMITS: frontier-clean 8d42b0b (work), 6be56a0 (review fixes; branch fc-03292e tip before this report commit); report commits follow on the same branch
NOT DONE:
- Plugin lines (wt/pm-plugin/{orient,post-take,pre-done}) are unchanged. Their exact text is pinned by wt/tests/t/*.t, which I may not edit, and each already names the verb to run (wt start, wt finish, wt park). Any extra guidance there needs a transcript change under a ruling.
- Failure-line ceiling is proven for the usage failures (real CLI) and for every wt_say/wt_fail template with 24-byte stand-ins plus a 90-byte fault path. Lines that quote git's error or an operator command list (STOP, deferred, nested-git, dirty-worktree) can exceed 400 with real long paths; the test cannot see that. I capped git's quote in the STOP line at 100 bytes and cut its prose; the pinned phrases (operator-run, in order; Do not run any further git, wt or pm command against this worktree; do not escalate) stay.
- The instruction map justifies cutting the global instructions and the skill, but that edit is in ~/frontier/instructions/claude-global/ and ~/frontier/skills/worktree-lifecycle/ (read-only for me). Until the overseer lands it those lines stay in force. The map marks CLAUDE 164 and 166 "printed" partly through contract-only rules (final-response rule, branch -D cherry rule); the contract, not wt output, carries those.
- wt/docs/contract.md "Dropped or changed" still describes old behavior in places I did not touch; I did not re-audit it.
- Doc-line/ordering nit: the map cites tools/verbs/*.zsh and cli/wt line numbers; they drift on any edit to those files.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/cli/wt
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/start.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/finish.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/park.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/status.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/prune.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/verbs/selftest.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tools/lib/teardown.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/tests/test_budgets.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/docs/contract.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/docs/instruction-map.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-03292e/wt/AGENTS.md
