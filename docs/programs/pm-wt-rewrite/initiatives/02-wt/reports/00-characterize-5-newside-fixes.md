TICKET: fc-30c060 -- wt characterization, part 5 new-side setup fixes
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: `make_repo` default prefix is `tk` for the default name and `tk<alnum name>` otherwise (fixes the shared `tk` prefix across FinishTest.test_every_refusal_names_a_next_step cases; no other test builds two repos with the same prefix, they pass explicit prefixes).
DID: same file: that test collects `Pending` raised inside each subTest and raises the first one after the loop (assertion failures stay failures, recorded by subTest).
DID: same file: `test_two_owners_stop_with_a_wt_line` skips on `SIDE == "new"` with the ruled reason; docstring says old side only. `run_wt.py` unchanged.
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
  cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
  wt suite: passed 95, pending 0, skipped 0, failed 0
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
  cli under test: /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub (pm new)
  wt suite: passed 9, pending 84, skipped 2, failed 0
COMMITS: frontier-clean 51c9993 on branch fc-30c060 (tip 51c9993); no check required
NOT DONE: NONE. Note: wt/AGENTS.md says not to edit tests/test_wt_cli.py after acceptance; this edit was directed by the prompt and the overseer ruling. Default prefix for non-default repo names changed (e.g. r1 -> tkr1), so ticket ids in those cases read tkr1-1 rather than tk-1; no assertion depends on it (old suite green).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-5-newside-fixes.md
