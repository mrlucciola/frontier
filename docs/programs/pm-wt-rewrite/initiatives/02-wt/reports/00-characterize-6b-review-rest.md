TICKET: fc-30c060 -- wt characterization part 6b (review gaps in start, resolution, refusals)
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: 123 tests (was 111). Items 1-9 landed: session sources (4 tests), EPERM hint, stale closed ticket (old behaviour pinned), where failures (pm missing, two-owners words, finish/park through a registered prefix), prune `Operator:` line end, first words for malformed gate / dirty / no actor, per-case next-step words in test_every_refusal_names_a_next_step, nested hooks-only, six nested repos (five named, `and 1 more`), `.vscode` on park, park cross-repo guard, selftest lines and leftovers.
DID: same file: `wt()` helper gained `env=` (per-call variables) and `path=` (replace PATH); adapters gained `close_ticket` (old: `pm ticket close --via wt --findings none`; new: `pm done --findings none -m closed`, unverified, no new wt to run it yet).
DID: no WT/docs/uncovered.md: every case ran sandboxed (the `.vscode` tests ran, not skipped).
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
  cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
  wt suite: passed 123, pending 0, skipped 0, failed 0
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
  cli under test: /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub (pm new)
  wt suite: passed 9, pending 112, skipped 2, failed 0
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060 c85a178 (branch fc-30c060)
NOT DONE:
- Item 3 vs contract (198-200): old wt does NOT tear down a stale worktree whose ticket is already closed. cmd_finish runs preflight_mutation (`pm ticket where --mutate`) before teardown; pm answers `already closed`, so wt prints `wt: pm would refuse to update <id>: ...`, exits 1, keeps worktree and branch. Pinned in FinishTest.test_stale_worktree_of_a_closed_ticket; contract wording "last line reports the close failed" does not hold. Also note old pm refuses a plain `pm ticket close` while a worktree exists, so the test closes with `--via wt`.
- Item 1: old wt reads `CODEX_THREAD_ID` only in cli/wt (the `--session` default, `PM_SESSION_ID or CODEX_THREAD_ID`); wt_core's own adopt check reads `--session`, PM_SESSION_ID, CLAUDE_CODE_SESSION_ID (not CODEX_THREAD_ID). With only CODEX_THREAD_ID set it still works because the CLI passes it as `--session`. PM_SESSION_ID wins over both others (pinned).
- Item 4: old pm-missing line is `wt: could not run \`pm ticket where <id>\`: ...`; the test pins only `wt: could not run \`pm ` so a new pm without `ticket where` can pass. Two-owners line pinned in old words (test is old side only).
- Item 6: malformed-gate words are old only: `wt: <path>/.pm/config.json: \`gate\` must be a non-empty list of strings (an argv), got ...` (the new side's `.wt/gate` will say something else; pinned the old line as ordered). Old wt prints a `wt: no --findings` warning first on finish without --findings.
- Item 9: old wt leaves three files `wt-selftest-pairs.json`, `-nopairs.json`, `-pairs-d.json` in $TMPDIR after selftest; the test fails only on a leftover directory. Contradicts "leaves nothing behind" only for files; new wt need not copy it.
- Item 8: the park guard line is the same `wt: cross-repo ` refusal; tested only with the pair removed after start (same shape as 6a's finish test); the "pair declared for commit but not worktree" partial case remains untested.
- wt/AGENTS.md says not to edit test_wt_cli.py after acceptance; edited because the prompt directs it.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/.tmp/commit-msg-fc-30c060-6b.txt
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-6b-review-rest.md
