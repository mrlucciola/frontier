# 01-core-d-render report

TICKET: fc-dac416 (01d: render, show, stores; last of four serial workers)

DID
- `pm/tools/render.py`: `line(t, tickets)` and `show(t, tickets, all_notes=False)` per the design's "Output" section (line order, children, body, notes with last-five heading, tag-only note lines).
- `pm/tools/store.py`: `is_done(tid, tickets)` directly after `next_id`. Used by `render.line` (`blocked by`) and `render.show` (`blocks:`).
- `pm/tools/verbs/show.py` (`--json` calls `store.unbuilt("json")`), `pm/tools/verbs/stores.py`.

EVIDENCE
Run from the worktree:
```
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 01-init -k 02-new-show
transcripts: passed 2, pending 0, failed 0
```
```
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
01-init.t: ok
02-new-show.t: ok
03-take-drop.t: pending (take)
04-done-findings.t: pending (done)
05-park-reopen-hold.t: pending (park)
06-orient.t: pending (take)
07-ls.t: pending (edit)
08-note-edit.t: pending (note)
09-link.t: pending (link)
10-epic.t: pending (done)
11-duplicate.t: pending (duplicate)
12-default-id.t: pending (note)
13-stores.t: pending (link)
14-get-emit-log.t: pending (get)
15-plugins.t: pending (plugins)
16-hook.t: pending (hook)
17-help.t: pending (take)
18-backup.t: pending (backup)
19-import.t: pending (import)
20-json.t: pending (note)
21-doctor.t: pending (doctor)
22-plugin-dispatch.t: pending (plugins)
23-plugin-pilot.t: pending (orient)
cli under test: /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/cli/pm
transcripts: passed 2, pending 21, failed 0
unbuilt verbs still needed: backup, doctor, done, duplicate, edit, get, hook, import, link, note, orient, park, plugins, take
```
Pending check: I ran each transcript through `run_one` (script `.tmp/check_pending.py`) and read the first mismatching step of all 21. Every one is a step whose got text is `pm: <verb> is not built yet.` exit 70, so no earlier step is wrong. Cases to know: 18-backup's first mismatch is `pm init t`, which calls the unbuilt `backup` mid-step (its other lines match); 05-park's first mismatch is `pm park` with no `-m`, wrongly expected to give a usage error, hidden by the unbuilt verb (the later `park` worker owns it).
Not exercised: show of `from`/`related`/`findings` formats, `children` with more than ten, and `--notes` are only covered by transcripts that are still pending.

COMMITS
`pm log core: render, show and stores` (code); report committed with the last commit.

NOT DONE
- `store.is_done` for an id outside `tickets`: without a Store argument, "another store's prefix" is approximated as a prefix not seen on any ticket in `tickets`; it then calls `unbuilt("routing")`. The stores/routing ticket should replace it with a registry lookup. In 13-stores the `blocks:` line for u-1 needs the cross-store link read, which depends on `link`/routing.
- `findings` rendered as a string or a comma-joined list; the `done` worker must pick one storage form (`none` or a list) and it must match.
- `render.show` `blocks:` uses `t["blocks"]` and so lists only same-store dependents; cross-store `blocks:` (13-stores line 17) is for the routing ticket.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/render.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/store.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/verbs/show.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/verbs/stores.py
