# 03c pm import and the import check

TICKET: fc-4a8593 (worker; not closed)

DID:
- `pm/tools/verbs/import.py`: spec v2 rows (plus `archive/tickets-*.jsonl` rows and epic `subtasks`) to one `store.change` append, per the design's mapping. Event order is all `new`, then notes, links, status events, holds, so no link or status event precedes its `new`. Each event keeps its own `ts` and `by`. Assignee and `closed_by` become `<name>#<token>`. Edit-trail notes are skipped. Other note kinds are kept. Registers the prefix, leaves old files, refuses a log with events.
- `pm/tests/import_check.py`: per store in stores.json, copies `.pm` to `.tmp/import-check/<n>/{old,new}`, installed `pm ticket list --json` per status vs `pm import` then `pm ls all -n 0 --json` here, field by field (title, body, kind, pri, under, labels, status, holder, hold, findings, reason, non-edit-trail notes, blocked_by incl. inverse `blocks`, related, from, created) plus the id set. `GIT_DIR` points at a nonexistent path so the copy's backup never touches this repo's refs.

EVIDENCE:
- `run_transcripts.py -k 19-import -v`: `passed 1, pending 0, failed 0`, exit 0.
- `run_transcripts.py --allow-pending -v`: `passed 19, pending 4, failed 0`; `unbuilt verbs still needed: hook, plugins` (no `import`), exit 0.
- `import_check.py`: all 10 stores `ok` (493, 880, 108, 135, 29, 27, 55, 5, 661, 78 tickets), `stores: 10, differing: 0`, exit 0.

COMMITS: see `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-4a8593 log --oneline -n 1` (message `pm import: spec v2 to the log, and the import check`).

NOT DONE:
- `updated` is not compared: replay sets it from the last event in file order, and the phase order (links written before status events) can leave it earlier than the old row's `updated` on rows that gained a link. Not a data loss; `created` and every note ts are exact.
- A `blocks` edge to an id not in the store cannot be written (replay skips a link on an unknown ticket); import prints `pm: warning: skipped <id> blocks <target>` and the check prints it as `note:`. None appeared in any of the 10 stores.
- A row line that is not valid JSON makes import refuse rather than skip; no store hit it.

BLOCKED ON OPERATOR: none.

ARTIFACTS:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-4a8593/pm/tools/verbs/import.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-4a8593/pm/tests/import_check.py
