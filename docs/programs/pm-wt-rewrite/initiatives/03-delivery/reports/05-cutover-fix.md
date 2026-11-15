TICKET: fc-10981e -- pm and wt cutover runbook, fix round for 05-review (BROKEN, 15 findings)
DID: docs/programs/pm-wt-rewrite/CUTOVER.md: all 15 findings fixed (one commit).
DID: step 4A added right after step 4 (old 8.0 table and item 1 moved there, posture/render/check.py row added); step 8.0 is now a one-item proof stub so step 8 item numbers 2 to 7 are unchanged.
DID: report written at this path.
EVIDENCE:
- Each finding was verified against its source before the edit; none found wrong. Sources read: pm/tools/store.py:36-43,61; pm/tools/verbs/import.py:173-174; pm/tools/store.py:79-82; `pm help`, `pm help ls`, `wt help`; deploy/engine.py:3446-3448 (retire has no --dry-run); posture/render/check.py:43-45,101-119; wt/tools/verbs/selftest.zsh:124; pm/AGENTS.md:18.
- 1: fixed at CUTOVER.md:172-195 (deepest-first loop, one-line why, per-store prefix expectation at :214, lost-child-log risk at :190-193), trigger fc-5e5a20 at :45-47.
- 2: fixed at :108-137 (worktree finish/park is now item 1, hashing item 2; lin-381db0 named).
- 3: fixed at :867 (five removed paths dropped from `git add`; :764 and :872 say why).
- 4: fixed at :380-396 (`rev-parse --short HEAD` before and after `wt finish`, deploy afterwards; range `<before>..<merged>`), consumed at :1055 and :1068-1069.
- 5: fixed at :343 (check.py row in the step 4A table) and :384-386 (`check.py` run in the proof block).
- 6: fixed at :310-324 (step 4A right after step 4, window stated at :312-319 as fail-open between the switch and `deploy core-hooks`), step 4 pointer at :246-250, step 8.0 stub at :711-724.
- 7: fixed at :336 (`pm ls taken -n 0 --all-stores --json`).
- 8: fixed at :255 (`cd /Users/matthias/frontier` first) plus the no-store note under that block.
- 9: fixed at :1055-1069 (step 8 item 7 reverted as a reverse patch excluding deploy/registry.json; :872-874 states it).
- 10: fixed at :100 (expect exactly two hits, pm/AGENTS.md:18 and pm/tests/import_check.py:18; :93-95 explains).
- 11: fixed at :912-915 (two deploys, 4A item 1 and step 9 item 5; I did not read whether the gate compares the printed word).
- 12: fixed at :930 and :954 (`release` to `drop`). Verbs checked against `pm help` and `wt help`: pm <verb>, pm help, pm stores, pm show/note/done/ls/doctor/log/get, wt help, wt finish/park/land/status/prune/selftest all exist. `wt pending` is absent from the new wt (the runbook already says so and only uses it in step 1 with the old wt).
- 13: fixed at :1093-1097 (skill-pm@codex, skill-worktree-lifecycle@codex, instructions-codex added to the verify list).
- 14: fixed at :708 (no `--dry-run` on retire, engine.py:3446-3448).
- 15: fixed at :303-305 and :748 (selftest drives the sibling pm, selftest.zsh:124; PATH side proved by readlink and `pm help`).
- python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/check_structure.py -> `check_structure: ok (7 components, 3 exempted)`
- python3 /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/.tmp/coords.py -> `897: CLAUDE.md:143 past end (1 lines)` then `checked 130 coordinates`. The one hit is a false positive: the script resolved bare `CLAUDE.md` to this worktree's one-line CLAUDE.md; the coordinate means /Users/matthias/frontier/instructions/claude-global/CLAUDE.md, which has 177 lines (wc -l). Script not committed.
COMMITS: frontier-clean 082040b (CUTOVER.md); this report is committed separately on the same branch fc-10981e. check-required: branch fc-10981e, tip = the report commit (git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-10981e rev-parse --short HEAD).
NOT DONE: Nothing from the 15 findings. Things I did not prove, all written into the runbook as "I have not ...": `pm restore` from a child with no log; what A10b means by `blocked` (the check.py OPEN_STATES choice is left to the frontier ticket); what tests/test_posture.py:578-580 test; whether the new wt resumes a worktree the old wt started (step 1 still avoids it); whether `git revert <before>..<merged>` meets a merge commit (a `-m 1` fallback is given). The step 4A window is only shortened to the edit-and-test time of the frontier ticket, because that ticket must be started with the new wt after step 4; I did not find a way to prepare it before step 4 without the old-wt/new-wt question. Overseer: step 4A introduces a frontier ticket the runbook does not name; file it when step 4 is scheduled.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/CUTOVER.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/05-cutover-fix.md
