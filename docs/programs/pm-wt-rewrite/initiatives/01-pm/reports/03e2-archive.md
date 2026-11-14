TICKET: fc-913d02 -- checks and views (03e2 archive)
DID: pm/tools/verbs/archive.py: new verb (ids, --closed-before, both, --dry-run, all refusals, parent/child, bulk skip, tickets-<year>.jsonl, archive-index.jsonl, index rides the ticket-file commit via Store.extra_commit_paths, skipped when git ignores it; no-op writes and commits nothing). Also exposes hint(store) (old _archive_hint) for the future summary verb.
DID: No store.py change; helpers (select, move, live_children, fixed_point) live in the verb. No contract-test argv change needed.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k archive -k test_no_op_mutation_does_not_commit --allow-pending
  -> Ran 18 tests OK; "parity: passed 6, pending 12, failed 0, skipped 0"; "unbuilt verbs still needed: claim, close"
  pending: 12 test_cli_parity.ValidateTest.test_archive_* / test_archived_id_is_refused_as_archived_not_as_unknown (each waits on claim or close)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 17 tests OK (skipped=20)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  -> "parity: passed 76, pending 186, failed 0, skipped 9"
  -> "unbuilt verbs still needed: claim, close, cross-store-edge, dep, edit, hold, lint, list, note, ready, release, reparent, summary, unlink"
Because the 12 archive parity tests are pending on claim/close, I smoke-tested by hand (.tmp/smoke_archive.py, temp git repo, hand-seeded rows): no-args refusal, open row naming close, parent of live children, dry-run, bulk skip of parent of live child, already archived, no-op archive (no commit, empty stderr), single commit "pm: archive 2" touching tickets.jsonl and archive/archive-index.jsonl, tickets-2020.jsonl written. Texts match the old source.
COMMITS: see git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-913d02 log -2 (verb + report, message "pm checks: archive (fc-913d02)")
NOT DONE: The 12 pending archive parity tests are unproven until claim and close land; rerun -k archive then. The full run's unbuilt line names neither validate nor archive (met). Sweep untouched (deferred).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/verbs/archive.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e2-archive.md
