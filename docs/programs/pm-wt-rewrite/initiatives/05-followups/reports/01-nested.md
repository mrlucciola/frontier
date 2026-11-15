TICKET: fc-5e5a20 -- pm: a nested store with config.json but no log.jsonl silently resolves to the parent store's log
DID: pm/tools/store.py `locate_dir` walks once for the nearest `.pm/` holding config.json or log.jsonl; with no log there, the main checkout's store is used only when the found store root is the git toplevel (or no store was found), so a nested store inside a linked worktree is not hijacked by the main store.
DID: pm/tools/store.py `require` refuses with "this store has not been imported yet. Fill its log: pm import" when `.pm/tickets.jsonl` sits beside a config with no log; otherwise the restore line. New helper `_toplevel`. No verb file changed.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_transcripts.py -> transcripts: passed 26, failed 0
/usr/bin/python3 -B -m unittest discover -s pm/tests -> Ran 7 tests ... OK
python3 -B docs/check_structure.py -> only pm/README.md:76 L-TARGET "/pm/dash-ui/README.md" (1 violation, as allowed)
COMMITS: frontier-clean 44548e4 (branch fc-5e5a20; report commit follows on the same branch)
NOT DONE: NONE. Note: the `_toplevel` guard (not in the design text) is my addition; no transcript covers a nested store inside a linked worktree.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-5e5a20/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/01-nested.md
