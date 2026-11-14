TICKET: fc-8c1f62 -- wt integration: selftest, drop the unbuilt path (part 1 of 2)
DID: wt/tools/verbs/selftest.zsh: new verb; scratch repo under mktemp -d, private PM_STORES/PM_PLUGINS/WT_FAULT_REPORT_DIR, git identity, pm symlink (sibling pm/cli/pm else PATH) first on PATH; cases start, finish, park, resume+finish, zero-delta park, land, prune; removes scratch with `rm -r -- "$scratch"` (recorded exception, docs part records it).
DID: wt/cli/wt: removed the WT_UNBUILT_LOG append and exit 70; a missing verb file now prints `wt: missing <path>; reinstall wt.` and exits 1.
EVIDENCE:
  /usr/bin/python3 -B <wt>/wt/tests/run_wt.py --cli <wt>/wt/cli/wt --pm new
    Ran 125 tests in 142.273s / OK (skipped=2)
    cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt (pm new)
    wt suite: passed 123, pending 0, skipped 2, failed 0      (exit 0)
  /bin/zsh <wt>/wt/cli/wt selftest
    ok: start / ok: finish merged, worktree and branch gone / ok: finish closes the ticket / ok: park marks the ticket parked / ok: park keeps the branch, removes the worktree / ok: start resumes the parked ticket / ok: resumed finish merges both commits / ok: zero-delta park releases the ticket / ok: land merges and tears down / ok: land keeps the ticket taken / ok: prune with nothing to do
    SELFTEST PASSED      (exit 0)
  /bin/zsh -n wt/tools/verbs/selftest.zsh: no output. /bin/zsh -n wt/cli/wt: no output.
  Scratch check: the selftest does not print its scratch path, so `ls -d` on it was not possible; `find "$TMPDIR" -maxdepth 1 -name 'wt-selftest-*'` after the run printed nothing. The suite's test_selftest_exits_zero also asserts no leftover wt-selftest* directory (passed).
COMMITS: frontier-clean b4637c3 (branch fc-8c1f62)
NOT DONE: NONE. Notes: the selftest does not exercise a failing case (no negative-path proof that FAIL lines and exit 1 work); the docs part (part 2) must record the `rm -r --` exception.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/tools/verbs/selftest.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03a-integration-selftest.md
