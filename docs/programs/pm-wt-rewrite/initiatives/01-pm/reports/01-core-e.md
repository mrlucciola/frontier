TICKET: fc-2b34c9 -- pm core review fixes
DID: fixes 1,5,6,9(store),10: pm/tools/verbs/show.py, pm/tools/verbs/create.py, pm/tools/store.py (is_remote_ref in show; fmt_line/claim_veto/edge_target moved to store; Store.rows; ID_RE and store._git removed, _worktree_main uses gitcommit._git; create's ticket id comment removed)
DID: fixes 2,4,8,9(gitcommit): pm/tools/store.py (commit(root, message, repo=None, extra_paths=()); history sync --repo remedy; Store.extra_commit_paths passed by locked_store), pm/tools/gitcommit.py (commit_store extra_paths kw; config.json probe timeout/OSError reads as tracked; unused env= dropped from guard_env/on_failure, kept on classify/identity_env_missing which tests pass)
DID: fixes 3,7,11: pm/cli/pm (help exit 0, view board|overview only), pm/tools/ticket (allow_abbrev=False), pm/tests/test_cli_contract.py, pm/tests/test_gitcommit.py (new tests)
EVIDENCE:
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -> Ran 15 tests, OK (skipped=21)
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py' -> Ran 24 tests, OK
run_parity.py --cli pm/tools/ticket -k test_create -k DuplicateGuardTest -k test_frozen_row_is_a_read_fallback_under_a_live_owner --allow-pending -> parity: passed 10, pending 8, failed 0, skipped 0
run_parity.py --cli pm/tools/ticket --allow-pending -> parity: passed 20, pending 241, failed 0, skipped 9
(parity run with absolute paths, since cd is refused)
COMMITS: see git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9 log (branch fc-2b34c9)
NOT DONE: NONE. Notes: extra_paths apply on the branch path only; a history_ref store records the ticket blob alone. create's --claim-as epic check now goes through claim_veto on a stub row (same message).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/cli/pm
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/store.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/gitcommit.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/ticket
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/verbs/create.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tools/verbs/show.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tests/test_cli_contract.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/pm/tests/test_gitcommit.py
