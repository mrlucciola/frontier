TICKET: fc-913d02 -- pm checks and views: validate (03e1; lint, archive, board, overview are later workers)
DID: pm/tools/verbs/validate.py: I-01..I-19, numbered steps, exit 0/1/2, --json (also without a store), --workspace fan-out (JSONC, W-01/W-02), history-pending tolerated, pre-v2 config is one I-02 step; own raw load (Loaded), schemas read from pm/docs/spec/v2.
DID: pm/docs/cut-list.md: old and new text for the three replaced fix hints in the existing fix-hint bullet, plus a fourth.
DID: v1 configs (spec_version 1) are treated like v0: one I-02 step, issues.jsonl tolerated by I-01; the old validated v1 stores, the cut list drops that.
EVIDENCE:
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k ValidateTest --allow-pending -> parity: passed 38, pending 17, failed 0, skipped 0 (pending are archive/claim/close/ready/release tests)
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k validate --allow-pending -> parity: passed 8, pending 10, failed 0, skipped 1 (pending need claim/close/unlink)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p test_cli_contract.py -v -> Ran 17 tests OK (skipped=20); ValidateHintTest.test_fix_hints_name_no_dropped_verb ... ok (ran, not skipped)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p test_gitcommit.py -> Ran 24 tests OK
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending -> parity: passed 74, pending 188, failed 0, skipped 9
unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, hold, lint, list, note, ready, release, reparent, summary, unlink   (validate absent)
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-913d02 2c30259 (branch fc-913d02)
NOT DONE: Pending (unbuilt-verb) validate tests, such as test_mechanical_fixes_resolve_their_invariant and CrossStoreEdgeTest.test_validate_flags_a_blocked_by_without_a_cross_store_target, have not run; they run once release/unlink etc. land. Not compared byte-for-byte on a live store (integration ticket diffs). The new "-k validate" run passes a single -k; the gate's two -k flags were run as two commands since run_parity takes one pattern.
NOT DONE: I-10 invalid-label hint (a fourth, beyond the three the prompt named) also named fix-labels and the contract test uses an invalid label, so it was reworded; recorded in cut-list.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/tools/verbs/validate.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/pm/docs/cut-list.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-913d02/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03e1-validate.md
