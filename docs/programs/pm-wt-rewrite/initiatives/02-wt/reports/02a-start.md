TICKET: fc-8ecb48 -- wt verb: start
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48/wt/tools/verbs/start.zsh: new verb in the old cmd_start order (parse, resolve, actor check, guards, WIP-tip refusal, adopt or pm take, quiet prune, worktree add or resume + rebase, undo on failure, pm emit wt.start, OK line).
- Round 2: renamed the read-only zsh special `status` to `prior`; a ticket held (status taken) by anything but the adopting claim now refuses before pm is called unless --force, because pm calls a same-token other-actor claim "yours" and would take it (test_refuses_foreign_claim_other_actor).
EVIDENCE:
/bin/zsh -n .../wt/tools/verbs/start.zsh -> exit 0, no output
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending -k StartTest
  Ran 18 tests; 16 passed, 1 pending, 0 failed
  pending: test_wt_cli.StartTest.test_codex_thread_id_is_the_default_session: first unbuilt step `wt park tk-1 --findings none`
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending
  Ran 125 tests ... OK (skipped=2)
  cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48/wt/cli/wt (pm new)
  wt suite: passed 36, pending 87, skipped 2, failed 0
Pending lines naming `wt start` as first unbuilt step: none (all name finish, land, park, prune, status or selftest).
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48 9fccaab (branch fc-8ecb48; earlier c592b74; overseer's lib fix c865198 beneath)
NOT DONE:
- Gate clause "StartTest has no pending test" cannot hold yet: test_codex_thread_id_is_the_default_session ends by calling `wt park`, which is not built. Its start steps (refuse th2, adopt th1, adopt via env) run before that and pass. It goes green when park lands.
- Unverified by a test: undo of a take when `git worktree add` fails (pm drop, or pm park if it was parked), and re-park on resume rebase conflict (only the contract-pinned `wt: resuming ... conflicted` line is tested, in a finish-class test that is still pending).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48/wt/tools/verbs/start.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02a-start.md
