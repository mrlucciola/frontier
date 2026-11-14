# 02c pm structure verbs report

TICKET
fc-8b871a (epic fc-2a6562)

DID
- Added pm/tools/verbs/note.py, edit.py, link.py, unlink.py.
- new.py: `--from`, `--blocks`, `--blocked-by` appended in the same `change` as the `new` event; duplicate refusal (transcript 11) and `--new`; the copied age filter now tests `status == "done"`. The duplicate check runs inside `check`, so it sees the replay under the lock.
- Choices: a note with a bad `-k` is a usage error (exit 2, per transcript 08); `link` refuses a self-link and a transitive cycle ("<b> already blocks <a>."); `unlink` emits an `unlink` event on each side that holds a link.

EVIDENCE
- run_transcripts.py -k 08-note-edit -k 09-link -k 11-duplicate -v: `11-duplicate.t: ok`, 08 pending (get), 09 pending (take); passed 1, pending 2, failed 0.
- run_transcripts.py --allow-pending -v: passed 3, pending 20, failed 0; unbuilt verbs still needed: backup, doctor, done, drop, get, hook, import, json, orient, park, plugins, routing, take. None of note edit link unlink duplicate.
- Pending 08 waits on `get` (line 46); 09 waits on `take` (line 15). The runner stops at the first unbuilt verb, so every step before it matched. 04's `--from` step sits after `done`, so it is not exercised yet.

COMMITS
See `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-8b871a log --oneline -n 1`: "pm structure verbs: note edit link unlink, new's links and duplicate guard".

NOT DONE
- Steps of 08 after `get`, 09 after `take`, and 04's `--from` check are unproven until those verbs land.
- `edit` does not refuse `--under` pointing at the ticket itself.

BLOCKED ON OPERATOR
none

ARTIFACTS
pm/tools/verbs/note.py, edit.py, link.py, unlink.py, new.py
