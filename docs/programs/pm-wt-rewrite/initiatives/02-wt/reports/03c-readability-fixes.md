# 03c readability fixes (fc-8c1f62)

STATUS: DONE. Commit 8563983 on branch fc-8c1f62 (11 files under wt/).

## DONE (one line per review finding)
- cli/wt, start, status, prune, pm-plugin "sound" findings: no change needed.
- finish.zsh rc==70 dead code and "70 means park is not built" comment: fixed (both checks and the comment removed).
- wt_wip_tip / WT_MASS_DELETE_MIN: fixed. wt_wip_tip moved into start.zsh; start uses WT_MASS_DELETE_MIN (kept in teardown.zsh).
- Two-verb teardown helpers: ruled. Kept shared; exceptions recorded in wt/AGENTS.md.
- park pm_session precedence: ruled. Changed to --session-first, a suite test failed (ParkTest.test_waits_on_note_and_session_in_resume_line: pm refused as "taken by ada, not yours"), restored, comment above it names the test and why; wt/AGENTS.md says so.
- selftest prune if/else: fixed.
- park branch_out unused / wrong tail: fixed. Tail now says "branch <id> kept" when `branch -d` failed without a deferred remove.
- finish `have` parameter: fixed (removed from `_wt_finish_close_cmd` and `_wt_finish_teardown`; that slot now carries `verb`).
- finish unused `cmds_text`, `t`: fixed (also unused `j` in `_wt_red_scan`).
- `_wt_red_covered`: fixed. Inlined into `_wt_red_scan` as a forward ancestor pass and a backward covered pass; no dynamic scoping.
- emulate -L zsh in cli/wt `wt_usage`, `main`, and selftest `wt_st_ok`, `wt_st_fail`: fixed.
- fail.zsh header ticket id and stale path: fixed.
- Fault dir default: fixed (`$HOME/frontier/docs/backlog/inbox/infra-faults`; named in INSTALL.md).
- start `$?` after if/else: fixed (args array, one `git worktree add`).
- Operator hand-off strings: fixed (`${(q)...}` on wt_path and p in teardown.zsh) and recorded in wt/AGENTS.md.
- Fault key/verb hardcoded `finish`: fixed (verb passed through `_wt_finish_teardown`; the key names `finish-...` unchanged).
- git.zsh / pm.zsh refusals with no next step: fixed (remedy appended to default-branch, `pm get` failed, not-a-directory lines).
- park `export PM_ACTOR`: ruled. Kept, one-line why comment added (I did not verify pm's behavior beyond reading the code: the reason given is that the actor comes from the ticket holder).
- park redundant `-d` test: fixed.
- teardown `${4:-finish}`: fixed (`verb=$4`).
- fail.zsh:79 and finish.zsh:374 missing return: fixed (`return 1`, `return $?`).
- finish.zsh header comment (land, WT_VERB, route codes 0/1/2): added.

## EVIDENCE
```
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new
OK (skipped=2)
wt suite: passed 123, pending 0, skipped 2, failed 0

/bin/zsh .../wt/cli/wt selftest
... SELFTEST PASSED
```
`/bin/zsh -n` on cli/wt, finish, park, start, selftest, teardown, fail, git, pm: no output each.
`rg -n 'rc == 70|cl-0c03c7|cmds_text|> 50' .../wt/tools`: no output (I did not capture the exit code separately).
`python3 -B docs/check_structure.py`: `check_structure: ok (7 components, 3 exempted)`.

## NOT DONE
- Nothing from the prompt. wt/tests untouched.
- Note: the new refusal texts in git.zsh and pm.zsh are longer; the suite did not pin them.
- Note: the AGENTS.md "recorded exception" for `wt_findings_required` was not present in wt/AGENTS.md before; I added it alongside.
