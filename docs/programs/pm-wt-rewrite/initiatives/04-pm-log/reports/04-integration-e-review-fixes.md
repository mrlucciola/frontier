TICKET: fc-d6c61c (pm-wt-rewrite/04/04e pm integration: readability review fixes)

DID:
- Every [FIX] item done: pilot.py open_pilots (now safe via ls ruling); new.py refuses `--blocks` for another store (uses store.home), drops `from store import now`; import.py getsize guard, `_new` loses `by`; log.py and show.py read the id's own store (`home_of`); `store.open_blockers` shared by take, ls, orient, render.line; render.show `waiting` is `store.blocked_elsewhere`; park/hold refusals add `Yours: pm ls mine`; reopen refusal adds `Give it back first: pm drop <id>` (` --force` when not yours); cli/pm unused import removed; change() docstring (check may run twice, must be pure) and note/edit use `target[:] = [...]`; post-hook why-comment; orient `_rank` inlined; emit uses `store.KEY_ORDER`; note uses `isdigit() or store.ID_RE`; doctor sorts `(n, text)` tuples; pilot `has_note` moved into pre-done, `overdue` compares the date to `today()`.
- Rulings: `ls --json` with no match prints nothing; `store.change(..., hooks=False)` (additive) used by import, skips pre and post hooks; registry path is the rest of the line with optional trailing ` ro`; orient hook stderr or non-zero exit prints one `pm: warning: plugin <name> orient failed.` and its stdout is dropped on non-zero; cli/pm catches Exception, KeyboardInterrupt exits 130; restore takes LOCK_EX on the existing log around os.replace; hook.py why-comment.
- Left as ruled: pinned refusals without next command, `_DUP_ID_RE`/`now_ts`, targets helper, orient_text, pilot PATH note. `home` kept (new.py calls it).

EVIDENCE:
- run_transcripts.py: `transcripts: passed 25, pending 0, failed 0`
- `/usr/bin/python3 -B -m unittest discover -s pm/tests`: `Ran 7 tests ... OK`
- `python3 -B docs/check_structure.py`: `check_structure: ok (7 components, 4 exempted)`
- Timing (rule 10): copy of ~/work/lai/.pm (largest, tickets.jsonl 2.47 MB, 880 tickets after import) in `.tmp/perf/lai`, PM_STORES lists only the copy, no plugins; median of 3 runs.

| command | runs (ms) | median (ms) |
| --- | --- | --- |
| pm | 100, 101, 102 | 101 |
| pm ls | 106, 111, 104 | 106 |
| pm show lai-5d2539 (epic) | 161, 163, 169 | 163 |
| pm take --dry-run | 163, 162, 167 | 163 |

All under 500 ms; nothing optimised.

COMMITS: see `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c log --oneline -n 2` (message `pm integration: readability review fixes`).

NOT DONE:
- Not covered by a transcript beyond t/25: restore's flock, orient warning for a plugin with stderr and non-zero exit (only the no-pilot-ticket path is covered), reopen/park/hold new refusal text (unpinned).
- Orient hook change: a hook exiting non-zero now has its stdout discarded, not just warned about. Judgment from "carry on"; say if stdout should be kept.
- restore.py:23/29 and link.py:46 / import.py:40 NOTEs: no next command added (nothing runnable / low value); left.
- store.py replay O(n^2): measured, fine at 880 tickets.

BLOCKED ON OPERATOR: none.

ARTIFACTS: scratch `.tmp/perf.py`, `.tmp/perf/` (gitignored).
