VERDICT: CONFIRMED
FINDINGS:
- finding 1 fixed: every `wt park <id>` line now carries `--findings none --note ...` (CUTOVER.md:50, :123, :165). That form gets past the old wt's refusals at wt_core.py:667-678 and :1132-1135.
- finding 2 fixed: the ancestor check moved to step 1 item 2 (:200-211), ahead of the hashes in item 4 (:223-233).
- finding 3 fixed: the red path now has a retry, R1-R6 (:552-609), and it holds together:
  - R1 reverts the ff-only range on main.
  - R4 fast-forwards the branch onto those reverts and reverts them again. The branch then strictly contains main, so on retry step 1.2's ancestor check and step 4A's `merge --ff-only` both pass.
  - R6 leaves a re-import that works. With each `.pm/log.jsonl` moved aside, `store.locate_dir` finds no log (store.py:58-71), so `import.check` sees an empty store and proceeds (import.py:172-174). Import never reads `refs/pm/log`; only `pm restore` does (store.py:344-352). `_backup` just overwrites that ref with the new log (store.py:355-363).
  - Nothing in R1-R6 writes or moves any tickets.jsonl. The new pm never writes it, and the 4A hand runs only read pm.
- finding 4 fixed: a posture-gate baseline with the old pm is now step 1 item 3 (:212-221).
- finding 5 fixed: both hand runs in 4A item 4 match the hooks' tests and source:
  - The `dispatch.py stop` payload matches test-policy-done-gate.py:87-92 and dispatch.py:339-345. `Ticket: fr-453840 done` matches done_gate's TICKET_LINE (done_gate.py:47-48). The ledger decisions `shadow_done`/`shadow_not_done`, and `None` with `err "unavailable: ..."` on a pm failure, match done_gate.py:277-302. `CLAUDE_HOOKS_LEDGER_DIR` and `CLAUDE_HOOKS_STATE_DIR` are the names lib/ledger.py:65 and lib/hookio.py:217 read.
  - The session-title payload and environment match test-session-title.py:60-87. The expected title matches the source: `fallback_desc` strips the id (session-title.py:218-220), `repo_name` gives `frontier-clean` (:105-124), and `compose` builds `epic:id MM/DD` (:245-256).
- finding 6 fixed: the test_bin_test_pm_validate semantics note is now in the table row at :446 and in the ticket body at :123.
- New coordinates hold: dispatch.py:339-348, test-policy-done-gate.py:87-92, test-session-title.py:77-82, bin/test:160-161, posture/render/check.py:44 and :103, wt_core.py:667-678 and :1132-1135, import.py:173-174.
- No blocking defects found.
RE-VERIFY: NONE
