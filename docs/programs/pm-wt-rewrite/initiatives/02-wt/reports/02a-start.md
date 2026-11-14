TICKET: fc-8ecb48 -- wt verb: start
DID:
- /Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48/wt/tools/verbs/start.zsh: new verb, written in the old cmd_start order (parse, resolve, actor check, guards, WIP-tip refusal, adopt or pm take, quiet prune, worktree add or resume + rebase, undo on failure, pm emit wt.start, OK line).
- Gate NOT met: every start-dependent test fails before reaching my code because of a core bug (see NOT DONE 1). The verb is therefore unproven end to end.
EVIDENCE:
/bin/zsh -n .../wt/tools/verbs/start.zsh -> exit 0, no output
/usr/bin/python3 -B .../wt/tests/run_wt.py --cli .../wt/cli/wt --pm new --allow-pending -k StartTest
  18 of 18 F, every one: `wt: pm store o is not a directory` (from wt_resolve_repos, before start.zsh logic runs)
Full gate run: starts with 9 dots then F for most tests (all via `started()` -> wt start); not exit 0. Not pasted further: the last two lines were truncated in the tool output.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48 c592b74 (branch fc-8ecb48)
NOT DONE:
1. CORE BUG (wt/tools/lib/pm.zsh line 49, read-only for me). `${${(f)found}[-1]}` takes the last CHARACTER of the joined string (pm prints the store path, last char "o" of ".../repo"... shown as "o"/"1"), not the last line. Exact edit, replace line 49
   `      kinds+=(store) raws+=("${${(f)found}[-1]}") labels+=("pm store")`
   with these two lines:
   `      local -a found_lines=("${(@f)found}")`
   `      kinds+=(store) raws+=("${found_lines[-1]}") labels+=("pm store")`
   (`local` inside the if-branch is fine in zsh function scope.) After that edit re-run the gate; I could not, because Edit on a $TMPDIR copy was denied and I will not route around that.
2. Because of 1, these start.zsh choices are unverified by any test run and should be checked first on re-run:
   - adoption token: sha256 of (session, else $CLAUDE_CODE_SESSION_ID), first 8 hex, compared with `pm get <id> holder` equal to `<actor>#<token>`; assumes `holder` prints exactly `by`.
   - `pm take` stderr is folded into the `not claimable` line (`2>&1`).
   - re-park on resume rebase conflict uses `pm park <id> -m ...` as the prompt says; the old wt left the ticket claimed.
   - undo of the take: `pm drop` (or `pm park` if it was parked before).
   - `wt_prune_debt ... quiet` output discarded.
3. Contract/fault keys reused from the old wt: start-resume-mass-deletion, start-worktree-add-failed, start-resume-rebase-conflict. Mass-delete threshold 50 (old MASS_DELETE_MIN).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-8ecb48/wt/tools/verbs/start.zsh
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02a-start.md
