TICKET: fc-c8212a -- back up only a store at the top of its checkout
DID: pm/tools/store.py: new has_backup(s) (git toplevel via the existing _toplevel equals realpath of s.root); _backup uses it.
DID: pm/tools/verbs/doctor.py: prints the backup line only when store.has_backup(s).
DID: pm/tools/verbs/restore.py: refuses with "this store is not at the top of a git checkout, so it has no backup." unless store.has_backup(s); docstring updated.
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tests/run_transcripts.py
  transcripts: passed 26, failed 0
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tests
  Ran 7 tests in 7.372s -- OK
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/docs/check_structure.py
  pm/README.md:76: L-TARGET link target "/pm/dash-ui/README.md" does not exist
  check_structure: 1 violations (7 components, 2 exempted)
COMMITS: frontier-clean ede790f (branch fc-c8212a); report commit follows. check-required: no
NOT DONE: Ticket body also asks to stop the config-only refusal in store.require recommending restore when the backup's first event is from another prefix; not in the prompt's write set or gate, left undone (with has_backup the scratch-ref path no longer writes, so only the two pre-existing stray refs remain a hazard). Stray ref deletion and the CUTOVER.md trigger are not done (runbook/operator).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tools/verbs/doctor.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/pm/tools/verbs/restore.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c8212a/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/02-backup.md
