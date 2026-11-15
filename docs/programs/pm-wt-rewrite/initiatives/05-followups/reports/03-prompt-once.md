TICKET: fc-d3d87b -- pm hook prompt: mention each ticket once per session
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tools/verbs/hook.py: `prompt` skips ids already in $TMPDIR/pm-mentioned-<token> (tempfile.gettempdir() when unset), appends the shown ids (at most three per prompt, only those printed), keeps nothing without a token, and prints even when the read or write fails.
DID: same file: module docstring (pm help hook) gains one clause naming the once-per-session rule and the file; pm help hook is 552 / 700 bytes.
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tests/run_transcripts.py -> transcripts: passed 25, failed 0
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tests -> Ran 7 tests in 7.582s, OK
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/docs/check_structure.py -> pm/README.md:76: L-TARGET link target "/pm/dash-ui/README.md" does not exist; check_structure: 1 violations (7 components, 2 exempted)
COMMITS: frontier-clean af0c496 (branch fc-d3d87b); report commit follows on the same branch
NOT DONE: NONE
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/pm/tools/verbs/hook.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-d3d87b/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/03-prompt-once.md
