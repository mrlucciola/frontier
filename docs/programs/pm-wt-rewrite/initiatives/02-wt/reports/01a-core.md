TICKET: fc-122c0d -- wt core: zsh dispatcher and lib (git, pm, fail, config), verb table (part 1 of 2)
DID:
- wt/cli/wt: zsh dispatcher. Resolves itself via `${0:A}`; verbs `start finish land park status prune selftest`; `land` has NO land.zsh: the dispatcher maps it to `verbs/finish.zsh` and sets `WT_VERB=land` (finish.zsh reads it for --keep-open). Missing verb file: appends the typed verb name to `$WT_UNBUILT_LOG`, prints `wt: '<verb>' is not built yet`, exit 70. No/unknown verb: one usage line, exit 2; `pending` adds `Parked tickets are listed by: pm ls parked`.
- wt/tools/lib/{git,pm,fail,config}.zsh and crossrepo.py, findings_required.py (see ARTIFACTS list below).
- Verb calling convention for part 2 (my choice, not in the prompt): the dispatcher sources every `tools/lib/*.zsh` (so teardown.zsh is picked up automatically), sources the verb file, then calls `wt_verb "$@"`. Each verb file must define `wt_verb` and return its exit status. Globals set for verbs: `WT_TOOLS`, `WT_COMPONENT`, `WT_VERB`.

Lib functions (callers = the verbs that should use them):
- git.zsh `wt_repo_root <path>`: main checkout of a path's repo (start finish park status prune)
- git.zsh `wt_default_branch <repo>`: prints branch, own `wt:` error (start finish park prune)
- git.zsh `wt_worktree_path <repo> <id>`: `<repo>/.worktrees/<id>` (start finish park status)
- git.zsh `wt_branch_exists <repo> <id>`: (start finish park prune)
- git.zsh `wt_worktree_list <repo>`: fills WT_WORKTREE_PATHS / _BRANCHES / _PRUNABLE (finish park status prune)
- git.zsh `wt_is_ancestor <repo> <a> <b>`: (finish park prune; merged-marker check)
- pm.zsh `wt_pm <store> <session> <pm args>`: runs pm from the store repo with WT_CALLER=1, session -> PM_SESSION_ID (the base of the wrappers)
- pm.zsh `wt_pm_get <store> <id> <field>` (all verbs), `wt_pm_take <store> <session> <id> [args]` (start), `wt_pm_done <store> <session> <id> [args]` (finish, park via zero-delta?), `wt_pm_park` (park, finish auto-park), `wt_pm_drop` (park zero-delta, start rollback), `wt_pm_emit <store> <id> wt.<name> k=v` (start finish park). take/drop/park/done have fewer than three callers on their own; they are one-line wrappers kept because the ticket names them. Part 2 may inline any it does not use.
- pm.zsh `wt_resolve_repo <path> <option>`: --store/--repo path as repo root, with the old refusals (used by wt_resolve_repos only)
- pm.zsh `wt_resolve_repos <store opt> <repo opt> <id> <cwd repo>`: sets WT_STORE and WT_REPO (start finish park status prune). Store comes from `pm get <id> store` run in the cwd repo; failure or empty falls back to the cwd repo.
- fail.zsh `wt_say <text>`: the `wt: ...` line on stderr (all verbs)
- fail.zsh `wt_fault_row <key> <repo> <ticket> <verb> <detail>`: appends the markdown row under `$WT_FAULT_REPORT_DIR/<day>-wt-<key>.md`, prints the path (called by wt_fail; also direct for deferred-teardown rows in part 2)
- fail.zsh `wt_fail <infra|flow> <key> <repo> <ticket> <verb> <what> [<next>]`: the one fixed failure line plus row; returns 1
- fail.zsh `wt_guard <source> <target> <git sub> <ticket> <verb>`: runs crossrepo.py, refusal printed via wt_fail flow (start finish park prune)
- config.zsh `wt_gate_find <store repo>`: prints `.wt/gate` path rc 0; rc 1 none; rc 2 not executable (prints `wt: ... gate ... fix it or pass --no-gate.`) (finish; land is finish) -- one verb only, left in lib because the ruling placed it there
- config.zsh `wt_known_red <repo>`: fills WT_RED_TICKETS / WT_RED_MATCH (finish only, same note)
- config.zsh `wt_findings_required <store>`: rc 0 when required, via findings_required.py (finish park)
- Not written, left to the verbs: the `pm done --dry-run` preflight (not used, per ruling), `_own_claim_assignees`, `check_findings` messaging, gate run and known-red scan, teardown helpers (part 2).

EVIDENCE:
$ /bin/zsh -n .../wt/cli/wt  (and one call each for git.zsh pm.zsh fail.zsh config.zsh): exit 0, no output
$ /usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending
  Ran 125 tests in 47.174s / OK (skipped=2) / wt suite: passed 9, pending 114, skipped 2, failed 0
$ wt/cli/wt                      -> usage: wt <start|finish|land|park|status|prune|selftest> ... ; exit=2
$ wt/cli/wt pending              -> wt: no verb 'pending'. Parked tickets are listed by: pm ls parked ; exit=2
$ WT_UNBUILT_LOG=.tmp/unbuilt.log wt/cli/wt start x -> wt: 'start' is not built yet ; exit=70 ; log contains `start`
$ GIT_PAIRS_FILE=.tmp/pairs-empty.json /usr/bin/python3 -B crossrepo.py <worktree> /Users/matthias/frontier worktree
  -> cross-repo worktree into /Users/matthias/frontier is not a declared git-pairs pair from <worktree> (...); exit=1
$ GIT_PAIRS_FILE=.tmp/pairs-declared.json (same args) -> no output; exit=0
Lib smoke (.tmp/smoke.zsh, sourced functions in the worktree only): wt_repo_root maps the worktree to the main checkout; wt_default_branch prints fc-122c0d; wt_worktree_list fills both arrays; wt_fail infra and flow print the pinned line shapes and write one row file; a non-executable `.wt/gate` returns 2 with the gate/--no-gate line; known-red skips `#` and blank lines. NOT exercised (no verb exists to drive them): wt_pm_* against a real store, wt_resolve_repos, wt_guard end to end, wt_findings_required on a true value in a throwaway repo (it returned 0 against the worktree's own .pm/config.json).

COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d bd0b0c6 (branch fc-122c0d, check-required: no destructive operation; overseer runs wt finish)

NOT DONE:
- pm.zsh functions are only syntax-checked and smoke-untested against pm; the first real run is part 2's start verb. Assumptions to verify there: `pm get <id> store` prints a repo root path (design says PM_STORE is the repo root); a ticket pm cannot find gives non-zero or empty output.
- crossrepo.py ports the same-repository and pair check; submodule and non-`.git` bare common-dir cases are not ported (same scope as the old module).
- No test was edited; none looked wrong.

BLOCKED ON OPERATOR: NONE

ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/git.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/pm.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/fail.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/config.zsh
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/crossrepo.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tools/lib/findings_required.py
