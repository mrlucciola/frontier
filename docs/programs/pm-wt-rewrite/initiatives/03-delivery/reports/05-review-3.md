VERDICT: PARTIAL
FINDINGS:
- CUTOVER.md:157 and :162-165 (step 0 item 4): the old `wt park` will refuse as written, and the fallback refuses too. The branch has commits, so old `cmd_park` runs `check_findings`, which refuses whenever `findings_required` is set and `--findings` is missing (/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py:1132-1135 and :667-670). The fallback `--findings none` then refuses again, because it needs a non-empty `--note` or an existing ticket note (:672-678), and the ticket filed at :122 has no notes. Fix: `wt park <id> --waits-on "cutover step 4A" --findings none --note "<what was checked>"`. The same correction is needed at :50 and in the ticket body at :122.
- CUTOVER.md:204-214 (step 1 item 3) runs after the hashes in item 2 (:193-200). Its exit-1 remedy (old `wt start`, rebase, `wt park`) rewrites frontier's tickets.jsonl, so step 2.4's `shasum -c` (:284) then fails. Move the ancestor check before item 2, or repeat item 2 after the remedy.
- CUTOVER.md:513-523 (step 4A red path): the undo itself is sound. The revert range is free of merge commits (ff-only), there is no reset, the diff stat proves the tree is back, and core-hooks was not deployed. But nothing says how to retry. After `revert <before>..<merged>` the branch `<id>` is an ancestor of main, so on a second attempt step 1.3 passes, `merge --ff-only <id>` says "Already up to date", and the readers stay reverted. The red path needs a "revert the revert commits, or rebuild the branch" step.
- CUTOVER.md:503-512 (step 4A item 4, the check.py deviation): moving the real run to 4A is acceptable. Step 0 cannot run check.py, because frontier has no log before step 2 and its cwd is fixed to frontier (posture/render/check.py:44). But no pre-cutover baseline is recorded, so a check.py red that already exists today (for example an ack owner that is already done) rolls back the whole cutover. Add a run of the old check.py with the old pm in step 1 and expect exit 0.
- CUTOVER.md:138-152 (step 0 item 3) says the change is "tested against the new pm", but `--hermetic` skips the only pm-calling step (bin/test:160-161). done_gate.py and session-title.py are exercised only through fixtures. So no step before step 6.3 runs the rewritten done_gate or session-title against the real new pm; 4A item 5 proves only `verify` and `rg`. State this as not proven, or add one direct run with `PM_BIN` in a scratch store.
- CUTOVER.md:427 (low): the row for tests/test_bin_test_pm_validate.py changes only the verbs (:56, :59, :78). The test also asserts lint WARN lines for dead or `.local/` paths and reads `.pm/tickets.jsonl` (:90). `pm doctor` has no WARN lines and no tickets.jsonl, so the ticket has to decide that test's semantics, not just swap verbs.
- finding 1 fixed: no agent session runs from step 4 to 6.3. Step 4A is operator-only (:400-409); step 0 is the only agent work and runs before step 1; the remaining session reference (:666) comes after 6.3.
- finding 2 fixed: no `wt finish` remains. :543 runs `pm done <id> --findings none -m ...`, which pm/tools/verbs/done.py:42-69 accepts on a parked ticket. The `wt` plugin's pre-done passes because the worktree is gone (wt/pm-plugin/pre-done:3).
- finding 3 fixed: tests run before the merge (step 0) and before the deploy (4A item 4).
- finding 4 fixed: the :298 doctor loop uses the scratch registry, which holds every primary prefix plus `cl` for ~/claude.
- finding 5 fixed: :1230-1231.
- New coordinates checked and correct:
  - done_gate.py:123-124
  - session-title.py:188
  - bin/test:160-161, :166
  - tests/test_bin_test_pm_validate.py:25, :56, :59, :78
  - posture/render/check.py:43, :44, :103
  - pm/tools/verbs/done.py:66-69
  - wt/pm-plugin/pre-done:3
  - frontier .pm/config.json:3
  - wt/docs/contract.md:76-78
  - pm/INSTALL.md:185
  - The old `pm ticket create --label/--body` flags exist (runtime-tools/pm/ticket/src/ticket:2944-2952).
RE-VERIFY: `rg -n 'wt park <id> --waits-on "cutover step 4A"' /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/CUTOVER.md` should show `--findings none --note` on every hit. After that, `git --no-pager -C /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e show HEAD -- docs/programs/pm-wt-rewrite/CUTOVER.md` should show step 1's ancestor check placed before the hash step, and a retry branch in 4A's red path.
