TICKET: fc-419332 -- CUTOVER.md additions: stray refs/pm/log before import, the dropped board views, sharing across clones dropped
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/programs/pm-wt-rewrite/CUTOVER.md: trigger 7 (fc-359b5b closed, covers fc-5e5a20 and fc-c8212a) in "What must be true first"; new "Step 1A" between steps 1 and 2 deleting the two stray refs/pm/log with their shas (existing steps not renumbered; the run-order sentence at the top names 1A); the board line (pm view board, pm view overview, pm ticket overview removed, dash-ui reads pm on its own) in the step 4 intro, where the runbook says what the switch removes; the sharing ruling as settled decision D3, after D1 and D2.
EVIDENCE:
git --no-pager -C /Users/matthias/frontier rev-parse refs/pm/log -> f5775a9f4d1f2499808e372073ef278e94d050fd (matches the ticket)
git --no-pager -C /Users/matthias/projects/frontier-clean rev-parse refs/pm/log -> d5fe02f404b4b0568ee16d653b48f9f526a35139 (matches the ticket)
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/check_structure.py -> pm/README.md:76 L-TARGET only; "check_structure: 1 violations (7 components, 2 exempted)"
COMMITS: frontier-clean 5024fb7 (branch fc-419332); the report commit follows this file
NOT DONE: NONE. Notes: step 1A uses "update-ref -d <ref> <old sha>", so it refuses if a ref moved; the ticket's text had no proof beyond for-each-ref and both are in the block. No runbook step was run. D3 is not under a settled marker because the runbook has none: D1 and D2 carry options and a recommendation, so D3 says "Settled by the operator on 2026-11-15, nothing to decide" under the existing "Decisions to make before step 0" heading. I did not check what fc-c8212a's fix does to step 2.1's import_check (the ticket says scratch stores under .tmp overwrite the ref; the runbook says import_check uses the old pm, which does not write refs/pm/log).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/programs/pm-wt-rewrite/CUTOVER.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-419332/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/05-runbook.md
