TICKET: fc-8ef942 -- pm link --note: the reason for a link, as a note on each ticket after the relation
DID: pm/tools/verbs/link.py: added `--note TEXT`; after the link events, `check` appends one `note` event (with `text`) per target ticket (b, c ...; not a), deduplicated, in the same `store.change` write, also when the link already existed. Overseer fix round: the first commit also noted a, which could put a note event in a store with no `new` for a ("event for unknown ticket").
DID: pm/tools/verbs/link.py: docstring usage line is now `pm link a blocks|related b [c ...] [--note "text"]`, plus one sentence on --note; `pm help link` is 404 / 700 bytes.
DID: pm/tools/verbs/link.py: an empty or whitespace-only --note is a usage error ("--note needs text."), matching `pm note`; the design does not say, so this is my choice.
EVIDENCE (after the fix, run once each):
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/pm/tests/run_transcripts.py -> transcripts: passed 25, failed 0
/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/pm/tests -> Ran 7 tests in 7.196s / OK (pm help link 404 / 700)
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/docs/check_structure.py -> only pm/README.md:76 L-TARGET "/pm/dash-ui/README.md" does not exist (1 violation, expected)
COMMITS: frontier-clean f77a777 (first cut), 4a74f64 (fix: targets only); report commit follows on branch fc-8ef942
NOT DONE: NONE. Not covered by the transcript: --note with `related`, and the note on an already-existing link; both follow the same code path.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/pm/tools/verbs/link.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-8ef942/docs/programs/pm-wt-rewrite/initiatives/05-followups/reports/04-link-note.md
