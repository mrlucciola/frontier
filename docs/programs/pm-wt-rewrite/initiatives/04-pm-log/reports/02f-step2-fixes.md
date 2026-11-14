# 02f pm step-2 fixes report

TICKET
fc-f3c2bd (fc-2a6562)

DID
- `take`: blocked refusal now `<id> is blocked by <ids>. Pick another: pm ls ready`.
- New `store.home_of(s, words)` placed after `home` in `pm/tools/store.py`: the one store that holds the named ids (None words skipped, digits get the local prefix), or refuses `<ids> are in different stores. Name them one store at a time.`
- `take drop done park reopen hold note edit unlink emit` resolve `s = store.home_of(...)` before `store.change`, so `check` looks tickets up in that store's replay and a read-only store refuses.
- `link`: home is the blocked side's store (`blocks`: the ids after `blocks`; `related`: the first id), as before the link stays on the blocked ticket.
- `get`: `store` prints the root of the store that holds the ticket; list fields print space-separated.

EVIDENCE
- `run_transcripts.py -k 09-link -k 13-stores -v`: `transcripts: passed 2, pending 0, failed 0`.
- `run_transcripts.py --allow-pending -v`: 17 ok (01-14, 17, 20, 21), 6 pending (15 16 18 19 22 23), `transcripts: passed 17, pending 6, failed 0`; unbuilt verbs still needed: backup, hook, import, plugins.

COMMITS
Branch fc-f3c2bd: `pm step-2 fixes: foreign ids change their own store` (includes this report).

NOT DONE
- `new --blocked-by` unchanged (new always creates in the local store; the link stays on the new ticket).
- `done --findings <foreign id>` resolves through `store.ticket` routing, not tested by a transcript.
- `show`/`ls` untouched.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-f3c2bd/pm/tools/store.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-f3c2bd/pm/tools/verbs/{take,drop,done,park,reopen,hold,note,edit,link,unlink,emit,get}.py
