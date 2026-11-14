TICKET: fc-30c060 -- wt characterization suite, part 2a (finish, land, gate)
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: FinishTest, 22 tests (happy path, ff-only, note/findings, findings warning and refusal, gate pass/fail/in-worktree/malformed, --no-gate, no gate, known red x3, dirty, land x4).
DID: same file: NewPm.set_gate(malformed=...) now writes and commits a non-executable .wt/gate; AdapterTest.test_malformed_gate updated (the ruling).
EVIDENCE:
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
wt suite: passed 40, pending 0, skipped 0, failed 0
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm new --allow-pending -k AdapterTest
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm new)
wt suite: passed 7, pending 0, skipped 0, failed 0
COMMITS: frontier-clean 38634fa on branch fc-30c060
NOT DONE: NONE of the listed cases. Pinned facts for the overseer:
- Old gate line is "wt: gate <argv joined by space> exit N, SKIP lines: K" (stderr, "wt: " prefix; contract omits the prefix). Pinned with the prefix.
- Old wt takes `--findings` only as ticket ids or `none` (pm rejects other text: "no registered store owns prefix"); the test uses `none` with `--note`. The adapter exposes only note texts, so the findings value itself is not asserted on the ticket, only that the no-findings warning is absent and the close succeeds. Contract line "--findings VALUE reaches the close" is therefore only partly pinned; an adapter `findings()` reader would close it (not added: only set_gate edit allowed).
- Old known-red "stale" refusal line is "wt: known-red now green: ..."; an uncovered extra FAIL line refuses (pinned in test_known_red_uncovered_failure_still_refuses). "Matches" is substring of a non-pass line (not starting PASS/ok/SKIP/DEGRADED).
- Gate tail is exactly the last 30 gate-output lines (11..40 present, 1..10 absent).
- Close note carries "gate: <argv> exit N, SKIP K" too; not asserted.
- Old gate is read from the main repo's config and runs with cwd = the worktree.
- `land` with --note/--findings exits non-zero with a "wt: " line, nothing merged (argparse accepts the flags for the land alias; cmd_finish rejects them).
- No contract case needed uncovered.md. No old-wt/contract contradiction found beyond the "wt: " prefix above.
- `Unavailable` class in the test file is now unused; left in place.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
