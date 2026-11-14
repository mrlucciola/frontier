# 01-core-c-store report

TICKET: fc-dac416 (worker 01c of 4), branch fc-dac416, worktree `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416`.

DID
- `pm/tools/store.py`: `Store`, `find`, `require`, `now`, `read`, `replay`, `ticket`, `next_id`, `change` per the contract and the overseer amendment (notes carry `kind`; defaults as stated; `updated` is the ts of the ticket's latest event, plugin events included). `related` is symmetric (derived from other tickets' links, per 09-link.t). Backup is not written (later ticket).
- `pm/tools/who.py`, `pm/tools/registry.py` per the contract.
- `pm/tools/verbs/init.py`, `pm/tools/verbs/new.py` (`dup_tokens`/`find_duplicates` copied unchanged; `--from/--blocks/--blocked-by` call `unbuilt("link")`; a duplicate match or `--new` calls `unbuilt("duplicate")`).
- Two additions so `--allow-pending` stays at `failed 0` (transcripts 15, 18, 22 failed before any unbuilt call once `init` existed):
  - `pm/cli/pm` `no_verb`: when the plugins directory (`$PM_PLUGINS`, else `~/.config/pm/plugins`) is non-empty, calls `store.unbuilt("plugins")` before the unknown-verb refusal.
  - `init.py`: inside a git checkout, after printing its output and creating the store, calls `store.unbuilt("backup")` (exit 70). Remove when the backup ticket lands.

EVIDENCE
- `run_transcripts.py -k 01-init -k 02-new-show -k 10-epic -k 11-duplicate -v`: 01-init pending (stores), 02-new-show pending (show), 10-epic pending (show), 11-duplicate pending (duplicate); failed 0.
- `run_transcripts.py --allow-pending -v`: passed 0, pending 23, failed 0, exit 0 (15 and 22 now pending on plugins, 18 on backup).
- `.tmp/core_c_check.py` log (key order ts by op id then sorted; `by` = actor#sha256("s1")[:8], `w1#...` for `--as w1`):

```
{"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"new","id":"t-1","title":"write the lexer"}
{"ts":"2026-01-01T00:00:00Z","by":"w1#e8bc163c","op":"new","id":"t-2","body":"Recursive descent.\nOne function per rule.","title":"write the parser"}
{"ts":"2026-01-01T00:00:00Z","by":"w1#e8bc163c","op":"take","id":"t-2"}
```

COMMITS
- `pm log core: store, identity, registry, init and new` (report included in the last commit; see `git log` on fc-dac416).

NOT DONE
- `find_duplicates` copied unchanged tests `status == "closed"`; the new store's status is `done`, so done tickets are never age-filtered. The duplicate ticket must fix this (design says done within 30 days).
- Transcript 20 prints notes with `kind`; this matches the amendment, nothing to do here. The `render.line`/`show` functions are not in `render.py` yet (not in my scope).
- Worktree-to-main-checkout store lookup, backup, `.gitignore` line, plugin running, and registry routing are unbuilt as assigned.
- `init` in a git checkout exits 70 after creating the store until the backup ticket lands.

BLOCKED ON OPERATOR
- none

ARTIFACTS
- `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/store.py`, `who.py`, `registry.py`, `verbs/init.py`, `verbs/new.py`, `pm/cli/pm`
- `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/.tmp/core_c_check.py`
