VERDICT: BROKEN
FINDINGS:
- CUTOVER.md:376-384 vs :275 and :318-319 (new, step 4A): item 1 is "Agent-run", but step 4 says no Claude session may start before 6.3, and 4A itself says no agent session until item 1 is deployed. So the step cannot run as ordered. If an agent does run it, its session has three problems:
  - The old `hooks/pm` session-start and stop hooks are still registered until 6.3 (settings.config.json:183-190, :212-219) and call verbs the new pm does not have.
  - The old CLAUDE.md and the still-deployed pm and worktree-lifecycle skills tell it to use `pm ticket ...`, which the new pm does not have.
  - done_gate fails open on its own close.
  - Item 1 also gives no `pm new` / `wt start <id> --as <actor>` commands for the ticket it requires.
  - Fix: move 6.1-6.3 (operator steps) before 4A, and hand the agent the new-verb commands.
- CUTOVER.md:384 (new): `wt finish <the frontier ticket id>` has no `--findings`. Frontier sets `findings_required` (/Users/matthias/frontier/.pm/config.json:3), so wt refuses before any merge (wt/docs/contract.md:76-78). `<before>` then equals `<merged>`, and the step 10.6 revert range at :1069 is empty.
- CUTOVER.md:384-387 (new): `bin/test --hermetic` and `check.py` run after the ff-only merge into frontier main. Frontier has no `.wt/gate`, so nothing tests the 4A change before it lands (wt/docs/contract.md:70). Run both in the worktree before `wt finish`.
- CUTOVER.md:213-216 (now sharper): step 2.4 expects `pm doctor` to print `ok: <prefix>, ...` in every store, but it runs before step 3 writes the registry. doctor resolves foreign link targets through the registry (pm/tools/verbs/doctor.py:28-32, :58-60). /Users/matthias/frontier/.pm/tickets.jsonl has 14 edges to fc, lai, lin, lop, obs, ps, pse or mo ids, so frontier's doctor will print "links to ..., which cannot be found" and exit 1. Fix: run the doctor check after step 3, or with `PM_STORES` set to the scratch import registry.
- CUTOVER.md:1068-1069 (low): the `log --merges` guard and the range `revert` are in the same block, so the revert runs before the operator can act on the guard. If a merge commit were in range, git would stop mid-sequence, and no `git revert --abort` is given. In practice `wt finish` is ff-only (contract.md:16), so the range should contain no merges; the guard can go.
- finding 1 fixed: :181 imports deepest path first. Traced through pm/tools/store.py:58-71: each child (lin, lop, obs, pse) finds no log at or above it, falls through to its own config.json and lands in its own log. lai and ps then find no log at or above them either. All ten land in their own logs.
- finding 2 fixed: :108-137 finishes worktrees first and hashes after.
- finding 3 fixed: :867 no longer names the five removed paths.
- finding 4 fixed as a mechanism (rev-parse before and after `wt finish`, :383-385). As written, the `wt finish` it brackets refuses (see the --findings finding above).
- finding 5 fixed: :343 adds a check.py row; the design.md:172 and :189 citations it adds hold.
- finding 6 partly fixed: the readers moved up to step 4A, but the new ordering contradiction above replaces it.
- finding 7 fixed: :336.
- finding 8 fixed: :255.
- finding 9 fixed: :1065-1067, reverse patch with `:(exclude)deploy/registry.json`.
- finding 10 fixed: pm/AGENTS.md:18 and import_check.py:18 are the only two hits; none in wt/.
- finding 11 fixed: :912-915 now states the two-deploy window.
- finding 12 fixed: :930, :954.
- finding 13 fixed: :1093-1098.
- finding 14 fixed: :708.
- finding 15 fixed: :303-305, matches selftest.zsh:124.
RE-VERIFY: Two checks. First, `cd /Users/matthias/frontier && PM_STORES=/Users/matthias/projects/frontier-clean/.tmp/cutover-import-registry /Users/matthias/projects/frontier-clean/pm/cli/pm doctor` (run after step 2.2; expect `ok: fr, ...`, exit 0). Second, after the fix, `rg -n 'wt finish <the frontier ticket id>' /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/CUTOVER.md`, which should show `--findings`, with step 6.1-6.3 placed before step 4A.
