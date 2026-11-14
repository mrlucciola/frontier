TICKET: fc-30c060 -- wt characterization part 7: side-neutral assertions and last gaps
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py: rulings 1-8 applied. Adapter methods `gate_label(argv)` and `unregister_store(repo)` (abstract, OldPm, NewPm). All 5 gate-argv echoes use `gate_label` (pass, fail, land pass, land fail, land --no-gate), plus the `gate skipped (--no-gate): <label>` close-note assertion. Malformed gate is a `wt:` line with `gate` and `fix it or pass --no-gate.` plus assert_untouched. Stale closed-ticket worktree branched by SIDE (docstring starts `Old wt deviates from the contract:`, cites contract.md:198-200; new side asserts worktree gone, branch gone, status done, last line `wt:` naming the id and containing "close" and "fail"; no exit code pinned). `test_rebase_conflict_auto_parks` docstring has `See fc-f0cc16.`. Fault rows: one file, >= 1 row. start-twice: state only (worktree at same tip, `taken`, same holder, one registration). Unregistered prefix test calls `unregister_store`.
- Same file, new tests: `test_undeclared_pair_refuses_land_and_mutates_nothing` (land guard), `test_partial_pair_refuses_finish_and_mutates_nothing` (pair declared for `commit` only), and a `land_findings` case in `test_every_refusal_names_a_next_step` (next-step words as `--note` has them).
- Partial-pair: crossrepo.py `pair_allows` checks the pair's `git` list per subcommand (/Users/matthias/frontier/runtime-tools/wt/src/crossrepo.py:145), so the old guard does distinguish; the test was added and is green on the old side.
EVIDENCE:
Command: /usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
```
cli under test: /Users/matthias/frontier/runtime-tools/wt/cli/wt (pm old)
wt suite: passed 125, pending 0, skipped 0, failed 0
```
Command: /usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```
cli under test: /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub (pm new)
wt suite: passed 9, pending 114, skipped 2, failed 0
```
Skips: test_two_owners_stop_with_a_wt_line, test_pending_lists_done_unmerged_with_cleared_blockers.
Old-only word grep (rg over test_wt_cli.py), remaining hits and why safe:
- `.pm/config.json` :111 (PmAdapter._edit_config, used by OldPm and by NewPm only for the shared `findings_required` key via `pm init`'s own config), :270 (NewPm.make_store commits the new pm's own config file; not a wt output assertion).
- `non-empty list`: no hits.
- `pm ticket`: :219, :261 are in OldPm adapter calls (`--unmerged ... --via wt`, `close --via wt`); other hits are docstrings. Residual: :2497 `wt: \`pm ticket where ...\` failed` sits in the two-owners test, which is skipped on the new side.
- `--via`: :219, :261 only, OldPm.
- `claimed`: :36 OLD_STATUS map (old adapter vocabulary); :2238 `words = {"taken","claimed"}` in the status test (ruled: not changed); all other hits are docstrings/comments, not assertions.
- `done-unmerged`: :36 map; :618, :1225, :1292, :2291, :2303: docstrings, except :2303 which is an assertion on the old-pending line inside the test skipped on the new side (I did not re-open :2291-2303 to confirm the branch; the skip list above shows that test is skipped on new).
- `where --mutate`: no hits.
NOT DONE: NONE. Caveats: (a) the new-side branch of `test_stale_worktree_of_a_closed_ticket`, the new `unregister_store`, `gate_label` (".wt/gate") and the partial-pair/land guard tests are only proven on the old side, since the new wt does not exist; the stub run proves they pend rather than fail. (b) The new-side `unregister_store` rewrites `$PM_STORES` keeping lines whose last field is not the repo; the file's line format `<prefix> <path>` was taken from NewPm.register_store, not verified against pm/cli/pm. (c) wt/AGENTS.md says not to edit the accepted test file; edited here under the overseer's explicit rulings.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/test_wt_cli.py
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-7-review2-fixes.md
COMMITS: frontier-clean fc28c3f (branch fc-30c060)
