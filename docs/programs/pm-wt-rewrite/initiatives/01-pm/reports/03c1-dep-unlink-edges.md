TICKET: fc-c10bcf -- pm verbs dep, unlink, cross-store edges (03c1)
DID: pm/tools/verbs/dep.py, pm/tools/verbs/unlink.py new (cycle check lives in dep.py; output and refusals ported from old cmd_dep/cmd_unlink)
DID: pm/tools/ticket: added route_edge and the dep/unlink dispatch at the top of route_args (only entry edit)
DID: pm/tools/store.py: additive ID_RE; edge_target cross-store branch now resolves via routing.cross_target (no more unbuilt("cross-store-edge"))
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k dep -k unlink -k cycle -k CrossStoreEdgeTest -k test_discovered_from --allow-pending
  parity: passed 6, pending 26, failed 0, skipped 0   (pending lines are all other-verb dependencies: claim, tree, ready, validate, note, edit, reparent)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'  -> Ran 15 tests, OK (skipped=17)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'  -> Ran 24 tests, OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
  parity: passed 27, pending 235, failed 0, skipped 9
  unbuilt verbs still needed: archive, claim, close, edit, history, hold, lint, list, note, ready, release, reparent, summary, tree, validate
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf see git log on branch fc-c10bcf (message "pm structure: dep, unlink, cross-store edges (fc-c10bcf)")
NOT DONE: NONE. Note: most dep/unlink/cross-store parity tests stay pending (not run) until claim/tree/ready/validate/note/edit/reparent land, so the cross-store paths are only partly exercised here.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/dep.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/verbs/unlink.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/pm/tools/store.py
