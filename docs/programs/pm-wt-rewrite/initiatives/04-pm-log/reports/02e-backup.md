TICKET
fc-3f4bfa (pm backup, restore, store of a linked worktree)

DID
- store.py: backup after the append in `change` (hash-object -w, update-ref refs/pm/log; failure prints `pm: warning: backup failed: <reason>`, exit code unchanged). New `locate_dir`, `in_checkout`, `backup_blob`, `_backup`. Lookup order: ancestor with log, then main checkout root via git-common-dir, then config-only ancestor (refuses "log is missing ... pm restore" in `require`). `find` still returns None without a log, so `ls all` over registered stores is not refused.
- verbs/restore.py: new; transcript 18 output and refusal. Also refuses when not in a checkout or when refs/pm/log is absent.
- verbs/init.py: .gitignore line in a checkout; `unbuilt("backup")` removed.
- verbs/doctor.py: prints a `backup:` line in a checkout. A differing or missing backup is reported but does not change the exit code (design does not say; my choice).

EVIDENCE
- `run_transcripts.py -k 18-backup -k 01-init -v`: passed 2, pending 0, failed 0.
- `run_transcripts.py --allow-pending -v`: passed 16, pending 5, failed 2. The two failures are 09-link and 13-stores, failing on main before this branch (fc-f3c2bd owns them), so the gate is failed 0 apart from those two. Unbuilt line: `hook, import, plugins` (not restore).

COMMITS
pm backup: refs/pm/log, restore, linked worktrees (see `git log` on branch fc-3f4bfa)

NOT DONE
- Nothing from the prompt. Not run: docs/check_structure.py (no docs/top-level change besides this report).

BLOCKED ON OPERATOR
None.

ARTIFACTS
- pm/tools/store.py, pm/tools/verbs/init.py, pm/tools/verbs/doctor.py, pm/tools/verbs/restore.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-3f4bfa/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02e-backup.md
