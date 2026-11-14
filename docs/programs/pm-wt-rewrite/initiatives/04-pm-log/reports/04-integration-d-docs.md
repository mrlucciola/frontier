# 04-integration-d-docs report

TICKET
fc-d6c61c, step d (component docs).

DID
- pm/README.md rewritten: what pm is, verb table (from `pm help`), registry, plugins (dispatch, pilot), harness hooks, routes, cutover note.
- pm/AGENTS.md: gate adds `unittest discover -s pm/tests` and `import_check.py`; two route rows (budgets/locking, harness hooks).
- pm/INSTALL.md: intro now describes the real install; plugin linking section; Verify, Disable, Remove (data and registry effects); provider hook sections kept unchanged.
- Root README pm row unchanged (purpose text still matches).

EVIDENCE
- `python3 -B docs/check_structure.py`: check_structure: ok (7 components, 4 exempted) (after fixing one A-RUN violation in pm/AGENTS.md)
- `/usr/bin/python3 -B pm/tests/run_transcripts.py`: transcripts: passed 24, pending 0, failed 0
- Verb table taken from `pm help` run in `.tmp/h`.

COMMITS
`pm integration: component docs` (this report included).

NOT DONE
- Not run: `unittest discover`, `import_check.py` (docs-only change; import_check needs the frontier stores list).
- INSTALL claim that plugin scripts reach the frontier pm until cutover rests on dispatch/cmd calling bare `pm get`; I did not test the pilot plugin under `pm-next`.
- INSTALL commands (symlinks, `pm-next help`) not executed, to avoid touching `~/.local/bin` and `~/.config/pm`.

BLOCKED ON OPERATOR
None.

ARTIFACTS
pm/README.md, pm/AGENTS.md, pm/INSTALL.md.
