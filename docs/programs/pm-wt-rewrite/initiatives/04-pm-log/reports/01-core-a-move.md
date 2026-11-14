# 01a pm log core: move report

TICKET
fc-dac416 (01a), branch fc-dac416.

DID
- Moved pm/cli, pm/tools, pm/docs/cut-list.md, pm/docs/spec and the six named tests to the same paths under pm/v2/ with git mv; 43 pure renames (100%), no content changes.
- No moved markdown file needed a link fix.
- Rewrote pm/README.md, pm/AGENTS.md, pm/INSTALL.md for the new layout.
- No file outside pm/ edited. pm/dash-ui/ is untracked in the main checkout and absent from the worktree; untouched.

EVIDENCE
- `python3 -B docs/check_structure.py` before the docs rewrite: 6 violations, all in pm/AGENTS.md and pm/README.md (links to the moved cut list and spec, and the unittest A-TARGET).
- After: `check_structure: ok (7 components, 4 exempted)`.
- Transcripts not run (pm/cli/pm no longer exists, as the prompt says).

COMMITS
- 0e9d39b pm log core: move the port to pm/v2
- the docs commit: pm log core: routing documents for the new layout (includes this report)

NOT DONE
- Nothing. INSTALL's `pm-next help` verification cannot run until the dispatcher lands; it says so.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/README.md
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/AGENTS.md
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/INSTALL.md
