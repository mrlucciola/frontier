TICKET
fc-e2d8c9 (pm stores, routing and doctor)

DID
- registry.py: added `stores(prefix)`, `known()`, `read_only_path(path)`.
- store.py: `ticket` routes by prefix (unknown prefix refuses `no store has prefix <p>. Known: ...`; first listed store that has the ticket wins). `is_done` looks the blocker up in the registry (stub removed, signature kept). `change` refuses `store <p> is read-only (<path>).` before opening the log. New helpers: `locate(prefix, tid)` -> (Store, ticket) or None; `home(s, tid)` -> the Store a ticket lives in (verbs that change a ticket that may be in another store call `store.change(store.home(s, id), ...)`); `blocked_elsewhere(tid, tickets)`.
- render.py: `show` `blocks:` adds tickets in the local store and every registered store that are blocked-by this one and not done.
- verbs/doctor.py: new; reports non-event lines, events for unknown tickets, links to tickets no store has.

EVIDENCE
- `run_transcripts.py -k 13-stores -k 21-doctor -v`: passed 0, pending 2, failed 0.
- `run_transcripts.py --allow-pending -v`: passed 2, pending 21, failed 0; unbuilt list: backup, done, duplicate, edit, get, hook, import, link, ls, note, orient, park, plugins, take (no routing, no doctor).
- 13-stores.t waits on `link` (`pm new --blocked-by` calls store.unbuilt("link")); steps before it (init, new, stores) pass.
- 21-doctor.t waits on `ls`; steps before it (init, new, doctor ok, doctor line 2 message and exit 1) pass.
- Not covered by the gate, checked by hand in .tmp/m (script .tmp/manual.py): `show u-1` from t lists `blocks: t-1` (with a hand-written link event); `show zz-1` refuses with `Known: t, u`; with `u ... ro`, `pm new` in u refuses `store u is read-only (<path>).`; reads still work; doctor reports unknown-ticket event and unfindable link.

COMMITS
pm stores: routing by prefix, read-only stores, doctor (this branch, with this report)

NOT DONE
- Verbs that mutate a ticket named by a foreign id (take, done, note ...) must use `store.home(s, id)` as the store passed to `store.change`; the contract's `ticket()` returns only the ticket dict. Other step-2 workers need to know this; their branches are untouched by me.
- doctor's `backup:` line is a later ticket's.
- `pm init` still exits 70 on `backup` (pre-existing).

BLOCKED ON OPERATOR
none

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9/pm/tools/verbs/doctor.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9/pm/tools/store.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9/pm/tools/registry.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9/pm/tools/render.py
