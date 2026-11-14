TICKET
fc-195118 pm lifecycle verbs: take drop done park reopen hold

DID
- Added pm/tools/verbs/take.py, drop.py, done.py, park.py, reopen.py, hold.py. No shared module edited; all use store.change(), store.ticket(), render.show.
- take: bare take picks top ready (pri, then creation); idempotent on held; parked resumes; --force records `from`; blocked refused without --force; several ids and --dry-run.
- drop/done: several ids all or nothing, --force, --dry-run; done has -m, --findings, --reason, findings_required, epic children rule, `next:` line.
- park/hold: need -m (usage error exit 2); only the holder.
- Choices not pinned by a transcript (my wording, under 300 bytes): take blocked: `<id> is blocked by <ids>. Finish <first> first: pm take <first>`; take done: `<id> is done. Reopen it: pm reopen <id>`; park/hold by non-holder of a taken ticket: `<id> is taken by <a>, not yours. Only <a> parks|holds it.`; reopen of a taken ticket: `<id> is taken by <a>. Only done or parked tickets reopen.`; bad --reason: usage error. done is allowed from parked (design diagram does not list it); take of an epic by id is allowed.

EVIDENCE
- Gate 1 (-k six transcripts -v): passed 1 (10-epic), pending 5, failed 0.
- Gate 2 (--allow-pending -v): passed 3, pending 20, failed 0; exit 0; unbuilt verbs still needed: backup, doctor, duplicate, edit, get, hook, import, link, log, ls, note, orient, plugins (none of take drop done park reopen hold).
- Pending among mine, each matched every step before the named call (runner's pending rule): 03-take-drop waits on log (`pm log t-1 -n 1`); 04-done-findings on ls; 05-park-reopen-hold on orient (bare `pm`); 12-default-id on note; 17-help on ls.
- Docstrings are each well under 700 bytes; take's is byte-identical to transcript 17.

COMMITS
pm lifecycle verbs: take drop done park reopen hold (verbs, plus this report in the last commit; hash from git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-195118 log --oneline -n 2)

NOT DONE
- Steps after the pending calls (log, ls, orient, note) are unverified until those verbs merge.
- Plugin pre hooks on these verbs belong to the plugins ticket.
- No contradictions found in the transcripts.

BLOCKED ON OPERATOR
none

ARTIFACTS
/Users/matthias/projects/frontier-clean/.worktrees/fc-195118/pm/tools/verbs/{take,drop,done,park,reopen,hold}.py
