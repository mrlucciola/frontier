TICKET: fc-d73327 -- pm lifecycle verbs: claim hold release (close, reopen are 03a2)
DID: pm/tools/verbs/claim.py, hold.py, release.py: the three verbs, incl. `claim --reopen`, `hold` status_hint refusal, release `released_by` and stray-assignee fix, the four exit lines.
DID: pm/tools/store.py (additive only): each_id, locked_verb, hold_state_dir, touch_session_seen, hold_is_stale, split_assignee, hold_marker, `import time`.
DID: pm/tests/test_cli_contract.py: ClaimReopenHoldTest (5 CLI cases: reopen refusal text, reopen drops findings/findings_absent/closed_by, reopen readiness as if open, hold status_hint, hold/release round trip). Typed note kinds: claim, hold and release write no notes in the old CLI, so none are written; the kinds in the ticket note belong to close (03a2).
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k claim -k hold -k release -k test_bulk --allow-pending -> parity: passed 4, pending 25, failed 0, skipped 2 (pending lines all name unbuilt close/dep/list/ready/summary/validate; none claim/hold/release)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 20 tests ... OK (skipped=15)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests ... OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending -> parity: passed 25, pending 237, failed 0, skipped 9
unbuilt verbs still needed: archive, close, cross-store-edge, dep, edit, history, lint, list, note, ready, reparent, summary, unlink, validate
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-d73327 34a8cb0 (branch fc-d73327)
NOT DONE: close, reopen (03a2). Spec-v1 store checks of the old hold ("hold needs a spec v2 store") and acting_identity omitted: the rewrite is v2-only (store.session_assignee has no v1 path). Most claim/hold/release parity tests are pending only because they call unbuilt close/list/ready/summary/validate/dep, so they are unproven end to end until those land. No byte-diff against the old CLI on a live store was run (integration ticket).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/pm/tools/verbs/claim.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/pm/tools/verbs/hold.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/pm/tools/verbs/release.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/pm/tests/test_cli_contract.py
