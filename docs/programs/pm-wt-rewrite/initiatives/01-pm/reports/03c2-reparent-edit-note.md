TICKET: fc-c10bcf -- structure verbs (second worker: reparent, edit, note)
DID: pm/tools/verbs/reparent.py (epic/--none, refuses non-epic, self, cycle, both target and --none)
DID: pm/tools/verbs/edit.py (atomic title/priority/body/append-body, edit-trail notes, refusals write nothing; priority_type imported from verbs/create.py)
DID: pm/tools/verbs/note.py (positional/--text, --kind before or after text via intermixed parser, kind choices -> argparse exit 2)
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k reparent -k edit -k note --allow-pending
  parity: passed 13, pending 8, failed 0, skipped 1  (pending: close x5, lint x3 incl. ValidateTest.test_I14_notes_out_of_order -> validate; all other verbs' absence)
  unbuilt verbs still needed: close, lint, validate
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 15 tests, OK (skipped=11)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests, OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 41, pending 221, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, history, hold, lint, list, ready, release, summary, tree, validate
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf branch fc-c10bcf; tip SHA in `git -C <worktree> rev-parse --short HEAD` (code commit plus this report commit)
NOT DONE: NONE. Note: edit.py imports priority_type from verbs/create.py (two users, so not promoted to store.py); NOTE_KINDS and the would-cycle walk live in note.py and reparent.py.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/reparent.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/edit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/note.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03c2-reparent-edit-note.md
