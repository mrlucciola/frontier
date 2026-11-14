VERDICT: PARTIAL

The core matches the old code in most places. These match: init's config, gitignore lines and footprint; create's checks and their order, the duplicate guard, the commit subject and the --claim-as assignee; the lock and save (an exception skips the save, and the commit runs while the lock is held); the git commit path and its exit 3 / policy-skip split; find_store; and the compacted-row reader. There is one wrong answer that would show up in a test or to a user, two smaller differences a user would see, and several foundation risks for the parallel tickets. `show --field` and the `~/.config/pm/stores.json` registry default are not findings: both are ruled in docs/programs/pm-wt-rewrite (PLAN.md:157, initiatives/01-pm/INITIATIVE.md:85 and :94).

FINDINGS:
- pm/tools/verbs/show.py:66-68 -- the check for an id from another store uses only "is this prefix one I own", while create.py:122 uses st.is_remote_ref. A legacy prefix the store owns but whose row it does not hold therefore falls through to store.read and stops with "no such ticket", exit 1. It should go to unbuilt("routing"), exit 70. test_cli_parity.py:2695 (test_frozen_row_is_a_read_fallback_under_a_live_owner) fails outright instead of counting as pending, because its pm() helper asserts rc 0 (test_cli_parity.py:2316). Fix: use `st.is_remote_ref(store, args.id)`.
- pm/tools/store.py:419-422 -- on a history_ref store, the printed by-hand remedy is a bare `pm ticket history sync`. The old code adds `--repo <repo_dir>` when a store was named (ticket_core.py:2272-2274). Someone who ran with --store from another directory gets a command that syncs the wrong store. The parity asserts at 1863 and 2136 are substring checks, so they do not catch it. commit() never receives `repo`, so fixing it means passing repo through or always printing `--store`.
- pm/cli/pm:6-12 -- `pm view <anything>` is passed straight to the ticket tool, so `pm view create x` creates a ticket. The old dispatcher allowed only board|overview (frontier cli/pm:35-39). Also, bare `pm` and `pm --help` now exit 2 with a usage line; the old one printed help and exited 0 (cli/pm:29-31). No test runs this file, because the parity suite drives tools/ticket.
- pm/tools/store.py:382-396 (foundation) -- locked_store has no step after the save where a verb can add work. The old one also refused frozen stores (ticket_core.py:2239), committed the archive index (:2253-2254), ran the sweep (:2250) and applied the history deferral (:2256):
  - Frozen stores are kept surface and routing.py comes next. Calling routing from locked_store means store and routing import each other. The alternative is every mutating verb calling it, so decide before the 5 verb tickets write their mutating paths.
  - The archive verb cannot commit archive/archive-index.jsonl under the lock unless locked_store or commit(root, message) changes shape, because gitcommit.commit_store hard-codes the paths it commits (gitcommit.py:284).
- pm/tools/verbs/show.py:63-69 (foundation) -- show opens the cwd store and only then checks the id's prefix. The old CLI routed first (ticket:3144, route_args before args.fn). With no store in the cwd, an id that routing would send elsewhere gets "no ticket store found". Every id-taking verb that copies show's pattern bakes in the wrong order, so routing should hand verbs a store root before open_store or locked_store runs.
- pm/tools/verbs/show.py:24, pm/tools/verbs/create.py:118, pm/tools/verbs/create.py:152 (foundation) -- helpers that several verbs need live inside one verb:
  - fmt_line is needed by list, ready, tree and claim; it was shared in the old code (ticket:183).
  - edge_target is needed by dep (old ticket:391).
  - The epic refusal is inlined here, but it was the shared claim_veto (old ticket:197) that claim needs too.
  - The parallel tickets will copy these or import across verb files. Move them into store.py now.
- pm/tools/store.py:121-125 and :140 (foundation) -- Store() refuses spec_version < 2, keeps no line numbers (the old code had self.rows, ticket_core.py:891), and stops with a traceback on a malformed row. validate must still report I-02 on a pre-v2 config (cut-list.md:53-55), and a bad row must exit 2 instead. So validate cannot use Store, and will either copy the loader or force a change to Store's signature.
- pm/tools/ticket:34-44 and :74-75 -- verb_in does not know argparse accepts abbreviated flags. `pm ticket --stor /x show ID` finds no verb, argparse still accepts the call, and line 75 prints "no such verb: show", exit 2. The old CLI accepted it. Line 75 is reachable only on this path. Fix: allow_abbrev=False.
- pm/tools/gitcommit.py:278-283 -- a timeout or OSError on the config.json status probe now returns a fault, which means exit 3. The old code treated it as "config.json is tracked" and committed tickets.jsonl alone (ticket_core.py:2676-2680). Low.
- Q2 (lines I could delete without a test failing):
  - store.py:262 ID_RE has no caller.
  - The `env=` parameters of identity_env_missing, classify, guard_env and on_failure (gitcommit.py:63, 75, 92, 101) are never passed.
  - store.py:48 `_git` is a second git runner without the clean environment, which contradicts gitcommit.py:1 ("Every git call the store makes").
- Q3 (refusals that name no next command):
  - store.py:123-125 names the old upgrade only by directory, not as a command to run.
  - store.py:196 "no such ticket", :234 and :244.
  - create.py:151 "parent X is not an epic".
  - Check whether the parity tests pin the exact text before changing it.
- Rule 7: create.py:14 has a ticket id, "(fr-1bdf6d)", in a source comment. The "(cl-111ef6)" at gitcommit.py:240 is pinned by test_cli_parity.py:1629, so it stays.

RE-VERIFY: /usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_frozen_row_is_a_read_fallback_under_a_live_owner
(run from /Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9; with the show.py fix it should report pending, not failed. The store.py:419 and pm/cli/pm findings have no test; they need new tests in pm/tests/test_cli_contract.py.)
