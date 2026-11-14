TICKET: fc-30c060 -- wt characterization suite, part 1 of 4 (runner, pm adapter, start)
DID: wt/tests/run_wt.py: runner (--cli, --pm, -k, --allow-pending, -v), pending as a distinct counted outcome keyed on exit 70 plus growth of $WT_UNBUILT_LOG
DID: wt/tests/test_wt_cli.py: isolated env, one wt helper, repo fixture, OldPm and NewPm adapters (all methods, both sides), AdapterTest (7), StartTest (13), empty FinishTest/ParkTest/StatusPruneTest/ResolutionTest
DID: wt/docs/uncovered.md not written: every start case ran in the sandbox
EVIDENCE:
$ /usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
wt suite: passed 20, pending 0, skipped 0, failed 0
$ /usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm new --allow-pending -k AdapterTest
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm new)
wt suite: passed 7, pending 0, skipped 0, failed 0
Pending mechanism check, fake wt exiting 70 and logging, -k StartTest, --pm new --allow-pending:
wt suite: passed 0, pending 13, skipped 0, failed 0
COMMITS: /Users/matthias/projects/frontier-clean 29e8a2a on branch fc-30c060 (no check required)
NOT DONE:
- Adapter: NewPm.set_gate(malformed=...) raises Unavailable. The new gate is an executable `.wt/gate` and the contract defines no malformed form. The old-side malformed-gate case is covered by the adapter only; no wt test uses it yet (part 2, finish).
- Unpinned, ambiguous: `wt start` run again while the worktree directory already exists. The contract does not say. Not tested, nothing guessed.
- Not tested: `start` appends a hint when `git worktree add` fails with "Operation not permitted" (needs sandbox denial); `start` running prune quietly; `--store`/`--repo` for start (belongs to ResolutionTest, part 4); cross-repo guard.
- Old-side guard_refuse_done (bin/deploy close-check stub, ticket labelled tooling) is implemented but only exercised by AdapterTest, not through wt (part 2).
- Deviation from the prompt's identity rule: setUp sets PM_AGENT=claude/worker for every call. Without it the old pm writes `human:<actor>` claims, which `start` can never adopt (observed: "already claimed by human:ada"), so the adopt case could not run. The new pm ignores PM_AGENT. The new wt's provider derivation for adoption is unspecified in the prompt; part 2+ may need to revisit.
- Old store prefix must be 2 to 8 chars; the fixture uses `tk`.
- Behavior pinned from the old wt, not stated by the contract: refusal lines are `wt: ticket <id> is not claimable ...` and exit 1; `start` with no `--as` and no $WT_ACTOR exits non-zero with a `wt:` line, claiming nothing (test_no_actor_refuses_before_claim; contract only says `--as` defaults to $WT_ACTOR); the mass-delete refusal line starts `wt: refusing to resume <id>`; the forced reminder line starts `forced claim on <id>` and contains `wt park` and ``never `wt finish` ``. A rewrite that words these differently should be judged against the contract, not this suite.
- Resume-parked and resume-branch tests build the branch with `git switch` inside the throwaway repo.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
