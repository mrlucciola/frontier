# 02b pm read verbs report

TICKET
fc-ef483a (epic fc-2a6562), branch fc-ef483a.

DID
- `pm/tools/verbs/orient.py`: bare `pm` (yours, ready, parked; five then `+N more`; one-line how-to-file when empty).
- `pm/tools/verbs/ls.py`: word grammar, priority-then-creation order, cap 20, `-n`, `+N more: add -n 0`, `nothing matches.`, `--json`, `--all-stores` (every registry store via `store.find`, deduplicated by root; `--json` adds `store`).
- `pm/tools/verbs/get.py`, `log.py`, `emit.py` as specified.
- `render.as_json(t, store_root=None)` placed directly after `show` in `pm/tools/render.py`; `show.py` now uses it instead of `store.unbuilt("json")`.
- Orient calls `store.unbuilt("plugins")` when the plugins directory (`$PM_PLUGINS`, else `~/.config/pm/plugins`) is non-empty. Without it 23-plugin-pilot.t failed at its first bare `pm` (expected plugin line). The plugins ticket removes this call and adds the real orient output.

EVIDENCE
- `-k 06-orient -k 07-ls -k 14-get-emit-log -k 20-json -v`: 14-get-emit-log ok; 06 pending (take), 07 pending (edit), 20 pending (note). Runner reports `passed 1, pending 3, failed 0` (exit 1 without `--allow-pending`, as pending steps exist).
- `--allow-pending -v`: `passed 3, pending 20, failed 0`; `unbuilt verbs still needed: backup, doctor, done, duplicate, edit, hook, import, link, note, park, plugins, take`: none of orient ls get log emit json.
- Pending transcripts: 06 waits on `take` (its seventh `pm take`, after the `pm new` lines), 07 waits on `edit` (`pm edit t-3 --under t-4`), 20 waits on `note`. Every step before those calls matches (runner checks them). The steps after are not exercised by the runner, so I ran a hand-built log in `.tmp/smoke.py` reproducing 07 (all ls forms, `-n 2` cap line, `done` empty), 20 (`show --json`, `ls --json`, same key order) and a 06-shaped bare `pm`; output matched the transcripts' expected text. The five-then-`+1 more` orient case and the `parked` section were not exercised.

COMMITS
See `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a log --oneline -n 1` (message `pm read verbs: bare pm, ls, get, log, emit, --json`).

NOT DONE
- Orient's parked overflow line reads `+N more: pm ls parked`; the design says `pm ls ready` for both sections, which would point at the wrong list. Overseer to confirm; no transcript pins it.
- `pm log` with no id follows the design rule (the ticket this session holds); there is no way to print the whole log. Overseer to decide if the whole log is wanted.
- `get` joins `labels`, `blocked-by`, `blocks` with `, ` (transcript 14 pins only a single label).
- Cross-store blockers still hit `store.unbuilt("routing")` inside `is_done`/`ticket`; 13-stores.t remains pending on `link` and routing.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/orient.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/ls.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/get.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/log.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/emit.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/verbs/show.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/pm/tools/render.py
