TICKET: fc-30c060 -- wt characterization part 3: park and deferred teardown
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: ParkTest (20 tests) and DeferredTeardownTest (4 tests, git shim on PATH for the wt call only via new `path_first` arg of `wt()`); moved `started`, `head`, `faults`, `locked_started` from FinishTest into new base `StartedCase` (FinishTest, ParkTest, DeferredTeardownTest inherit); `.vscode` note moved into `test_vscode_dir_refuses_before_merge` docstring.
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/docs/uncovered.md: deleted with `git rm` (both entries gone, nothing uncovered).
EVIDENCE:
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
wt suite: passed 73, pending 0, skipped 0, failed 0
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm new --allow-pending -k AdapterTest
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm new)
wt suite: passed 8, pending 0, skipped 0, failed 0
Old-wt behaviors pinned (differ from a naive reading of the prompt/contract):
- park's resume line carries `--session <id>` whenever a session is in the environment, not only when `--session` is passed (test_generated_note_ends_with_resume_line); a park with no session anywhere has none (test_resume_line_has_no_session_when_none_is_given); explicit `--session` also appears (test_waits_on_note_and_session_in_resume_line).
- park closes the ticket (`parked`) BEFORE the remove, so a failed remove leaves the ticket `parked`, not `taken` (test_failed_remove_prints_stop).
- main moves during park (pm commits to it); tests assert the parked work is not on main, not that main's sha is unchanged.
- lost `.git` refusal line is `wt: <wt> has no .git file: ...` (not "refusing to park").
- deferred park's `OK:` line does not mention the deferral (finish's does); the deferral is the separate `wt: worktree for <id> is gone ...` line; zero-delta deferred park's OK line says `registration deferred to wt prune`.
- zero-delta park: branch deleted (`branch -d`), `--note/--findings` print `wt: --note/--findings were NOT recorded`.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060 85d68fa (branch fc-30c060)
NOT DONE: NONE. Not run: `--waits-on <ticket-id>` (records a pm dep) -- only the free-text form is tested; no test for `wt park` of a deferred zero-delta branch deletion (branch -d under the shim; assertion left out as unpinned).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/docs/uncovered.md (deleted)
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-3-park.md
