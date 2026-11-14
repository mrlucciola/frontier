TICKET
fc-d6c61c (04c, remove pm/v2)

DID
- pm/README.md: removed the paragraph saying pm/v2/ is kept for reference (was line 9-10), and the two route rows linking /pm/v2/docs/cut-list.md and /pm/v2/docs/spec/v2/SPEC.md (were lines 20, 21).
- pm/AGENTS.md: removed the table row "The ported pm in pm/v2/" (was line 24 of the review's numbering; line 20 on this branch).
- .gitignore:127-128: comment reworded to "# .pm/lock is local bookkeeping, not repo content (folds cl-f7d6b4)."; no longer cites spec/v2/SPEC.md.
- git rm -r pm/v2 (43 files, 10929 lines) in its own commit.
- HISTORY hits under docs/programs/ left as is.

EVIDENCE
Source lines (non-empty; .py and extensionless files; docs, transcripts, fixtures excluded), from .tmp/sizes.py, before removal:

    pm/v2/cli          1 files     22 lines
    pm/v2/tools       29 files   4294 lines
    pm/v2/tests        6 files   4093 lines
    port subtotal                8409 lines
    pm/cli             1 files    104 lines
    pm/tools          28 files   1924 lines
    pm/plugins         5 files     85 lines
    pm/hooks           1 files     96 lines
    new subtotal                 2209 lines

Gate on the final commit (worktree root):
- run_transcripts.py: exit 0, "transcripts: passed 24, pending 0, failed 0"
- unittest discover -s pm/tests: "Ran 7 tests ... OK"
- docs/check_structure.py: "check_structure: ok (7 components, 4 exempted)"
- rg -n 'pm/v2' --glob '!docs/programs/**' .: no output, exit 1

COMMITS
- b4a9d04 pm integration: references to the port
- 78465ef pm integration: remove pm/v2
- report commit follows (last commit on the branch)

NOT DONE
- Nothing from the gate. The runner reports pending 0, not a nonzero count as the brief expected; no action needed.
- pm/README.md routes no longer mention the old store format or cut list; the later docs worker rewrites these docs fully.

BLOCKED ON OPERATOR
none

ARTIFACTS
/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-c-remove-v2.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/.tmp/sizes.py
