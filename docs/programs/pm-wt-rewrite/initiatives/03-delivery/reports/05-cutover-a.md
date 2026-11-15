TICKET: fc-10981e -- Cutover runbook (Part A: steps 1-6 and 10)
DID: docs/programs/pm-wt-rewrite/CUTOVER.md written: triggers, before/after numbers, rollback summary, decisions D1 (wt frontier defaults) and D2 (old refusal texts), steps 1-6 and 10; a placeholder section "Steps 7 to 9" is left for Part B.
DID: docs/programs/pm-wt-rewrite/PLAN.md "Cutover" now links CUTOVER.md.
DID: Findings in the runbook: ledger says only lai sets `gate`, but lai, lin and lop do (all `["python3","tests/run_suite.py"]`); no store sets `known_red`; the fc store's three write-reduction keys are at config.json lines 2, 3, 6; the redesigned pm has no old refusal texts (ticket note of 2026-11-14T02:40 is stale for it; D2 recommends doing nothing); `pm import` refuses a second store with the same prefix, so step 2 imports against a scratch PM_STORES and step 3 writes the real registry (`cl` twice, frontier first, `~/claude` ro); import does not gitignore `.pm/log.jsonl` (step 2.3 uses `.git/info/exclude`); fr-453840 is still open today, a trigger.
EVIDENCE:
python3 -B docs/check_structure.py (run as python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/check_structure.py) -> check_structure: ok (7 components, 3 exempted)
python3 /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/.tmp/check_coords.py -> coordinates checked: 30, problems: 0 (script not committed)
COMMITS: frontier-clean dc68463 (CUTOVER.md, PLAN.md); this report committed after it on branch fc-10981e
NOT DONE: Steps 7-9 (Part B). I exceeded the 40-tool-call budget by about ten calls to finish Part A rather than leave it partial. Not verified: ~/.codex/hooks.json lines 17-22 (sandbox denied the read; step 6.6 has a `sed -n` pre-check); the new wt handling a worktree the old wt started (step 1.2 avoids it by finishing or parking first); output formats of `pm stores`, `pm doctor`, `pm ticket show fc-ccecda` (steps say what to expect only where I read the code or docs); I did not open each non-frontier-clean repo's default branch (blocks run `branch --show-current` first). Part B must add the post-step-8 rollback to step 10 (libexec copies and the frontier retirement will be gone) and fill the "Steps 7 to 9" placeholder.
BLOCKED ON OPERATOR: NONE (the runbook itself is the operator's list; nothing is blocked on it to merge this branch)
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/CUTOVER.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/PLAN.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/05-cutover-a.md
