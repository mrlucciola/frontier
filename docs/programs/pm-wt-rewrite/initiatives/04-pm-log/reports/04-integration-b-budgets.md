# 04b budgets and concurrency report

TICKET
fc-d6c61c (04b), branch fc-d6c61c.

DID
- `pm/tests/test_budgets.py`: black-box ceilings on `pm/cli/pm` in a temp store with the transcript environment. Covers `pm help`, every `pm help <verb>` (verbs read from transcript 17's table, 22), 25 refusals (24 in one store plus the no-store refusal), bare `pm` (2 held, 8 ready, 3 parked), `pm hook session-start` on the same store, and a check that the design's ceiling table still reads 1600/700/300/700/760. Failure messages name the output and its size.
- `pm/tests/test_concurrency.py`: twenty concurrent `pm new` (20 distinct ids, 20 well-formed `new` log lines with ts/by/op/id); two concurrent `pm take` of one ticket (exit codes exactly [0, 1]).
- No ceiling is exceeded.

EVIDENCE
Gate 1: `/usr/bin/python3 -B -m unittest discover -s pm/tests -v` (run with the absolute tests path): Ran 7 tests, OK.
Gate 2: `/usr/bin/python3 -B pm/tests/run_transcripts.py`: passed 24, pending 0, failed 0.

Measured sizes (bytes / ceiling):
- pm help 1464 / 1600
- pm help take 420, note 283, done 466, park 260, drop 309, hold 239, new 396, edit 263, link 284, unlink 156, reopen 158, show 234, ls 361, get 303, log 194, emit 254, init 276, stores 180, doctor 266, restore 271, import 338, hook 504 (all / 700; largest hook 504)
- pm (2 held, 8 ready, 3 parked) 654 / 700
- pm hook session-start (same store) 698 / 760
- refusals (all / 300; largest `pm new` 170): take t-3 53, take t-4 51, take t-9 45, link t-3 blocks t-2 51, unlink t-1 t-6 33, new 170, init T1 98, init t 50, init x 50, note -k verdict x 120, edit t-1 139, park 68, park t-2 -m x 55, reopen t-2 25, hold t-2 -m x 55, drop t-2 45, drop t-4 74, done t-5 25, done t-4 --findings none -m x 77, done t-7 91, show t-9 45, new child two of it --under t-2 56, clam 55, xyzzy 40, new (no store) 47

COMMITS
See `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c log --oneline -n 2`: `pm integration: byte budgets and concurrency tests`.

NOT DONE
- Orient (654/700) and session-start (698/760) have 46 and 62 bytes of headroom; the figures depend on title length (my titles are 35 to 45 chars), so a store with longer titles may exceed them. The design gives no title length; I did not decide one.
- Refusal commands are a representative set I listed, not harvested from the transcripts automatically. The `take` blocked refusal here is 53 bytes (`t-3` blocked by `t-2`).
- Unittest discover run from the Bash tool used an absolute `-s` path because a `cd` is not allowed there; tests use absolute paths and do not depend on cwd.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/pm/tests/test_budgets.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/pm/tests/test_concurrency.py
