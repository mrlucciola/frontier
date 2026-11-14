VERDICT: BROKEN

I did not run anything; I had no shell. Every finding comes from reading the code. Findings 1 and 6 depend on zsh behaviour I could not test here (noted on each line).

FINDINGS:
1. wt/tools/lib/pm.zsh:29 -- `local path=...` uses zsh's special `path` array, which is tied to `$PATH`. Unless declared with `-h`, a special parameter keeps its special behaviour when made local, so this sets PATH to the --store/--repo directory for the rest of wt_resolve_repo and everything it calls. Changing path also clears zsh's command hash, so the `git` call at :35 and wt_repo_root at :44 cannot find git. The new pm registers every store at init, so nearly every start/finish/park in the suite (test_wt_cli.py:2471-2594) goes through this function. Fix: rename the variable to `dir` or `p`. No other lib local uses a special name; I checked by grep.
2. wt/tools/lib/pm.zsh:58-63 -- Suspicion CONFIRMED. Any failure of `pm get <id> store` falls back to the cwd repo, and stderr is thrown away (`2>/dev/null`). With pm off PATH, `env` exits 127, wt silently uses the cwd repo, and the later take fails with `env: pm: No such file or directory`. The suite needs `wt: could not run \`pm ` (test_wt_cli.py:2511), and contract.md:84-86 says any other failure stops. Fix: capture stderr and the exit code separately. rc 0 with output: use the store. rc 1 with stderr starting `pm: no store has prefix`: use cwd_repo. rc 1 with `pm: no ticket <id>`: also cwd_repo, because test_wt_cli.py:677-682 needs the later `wt: ticket tk-nope is not claimable` line, not a resolve error. rc 127: `wt_say "could not run \`pm get $id store\`: pm is not on PATH"; return 1`. Anything else: `wt_say "\`pm get $id store\` failed (exit $rc): $err"; return 1`. The old code made the same split (wt_core.py:460-469).
3. wt/tools/lib/pm.zsh:6-16 -- wt_pm cannot tell "pm missing" apart from a pm refusal: `exec env ... pm` exits 127 and prints env's own text. Each of the five verbs would have to detect this itself. Fix: in wt_pm, before the subshell, `(( $+commands[pm] )) || { wt_say "could not run \`pm $*\`: pm is not on PATH"; return 127 }`. Also give the `cannot enter store` line at :13 a next step, like every other `wt:` line.
4. wt/tools/lib/git.zsh:8, git.zsh:27 and pm.zsh:35 -- `2>&1` mixes stderr into the value on success. A sandbox git warning (for example `warning: unable to access ... Operation not permitted` on a HOME config file) then corrupts the repo root path or the branch name. The old code read stdout and used stderr only for the error text (wt_core.py:88-95, 126-131). Fix: `top=$(git ... 2>/dev/null) || { err=$(git ... 2>&1 >/dev/null); wt_say ...; return 1 }`. Do the same at git.zsh:54.
5. wt/tools/lib/config.zsh:3 -- The comment, and the 01a report, say `wt_gate_find <store repo>`. The gate belongs to the target repo (contract.md:58 says "target repo's"; the old code calls `read_gate(repo)` at wt_core.py:883, and `read_known_red(repo)` at :887). The finish author will pass WT_STORE and read the wrong repo's gate when --repo differs. Fix: document both functions as `<target repo>` (WT_REPO). wt_findings_required correctly stays on the store (wt_core.py:666).
6. wt/tools/lib/fail.zsh:14 -- `${v//|//}`: I think zsh may read a bare `|` as alternation (empty|empty), which matches the empty string, so this would mangle every cell or leave `|` unescaped and break the table. Unverified. Fix: `v=${v//\|//}`. Then check one row in a written report contains a literal `/` where the input had `|`.
7. wt/tools/lib/teardown.zsh:100 and :113 -- `${err%%[[:space:]]#}` needs extendedglob, but the function only has `emulate -L zsh`, so `#` is a literal and the trim does nothing. Fix: add `setopt extendedglob` in wt_stop_remove_failed and wt_deferred_line, as fail.zsh:48 and config.zsh:21 already do.
8. wt/tools/lib/fail.zsh:70 -- Any non-zero exit from crossrepo.py counts as a refusal: a usage error (exit 2) or a Python traceback gives `wt:  (reported: ...)` with an empty reason, plus a false crossrepo-refused row. Fix: refuse only on rc 1 with a reason; any other code goes through `wt_fail infra crossrepo-guard-failed ...`.
9. wt/tools/lib/pm.zsh:58-60 -- It passes pm's whole stdout as the store path. The old code took the last line (wt_core.py:465). Fix: `found=${${(f)found}[-1]}`.
10. These output lines differ from the old code and are not pinned by the suite, so they change silently. Restore the old text or record the ruling:
    - git.zsh:29: old text at wt_core.py:129-130 is "(main checkout must stay on a named branch, never detached HEAD)".
    - pm.zsh:41: old text at wt_core.py:119 is "is not a repo root -- it resolves to".
    - crossrepo.py:101-103: old text at old crossrepo.py:167-169 is "wt refuses what gitguard would refuse. Standing need: ask the operator to add the pair."
    - fail.zsh:29-35: the report header lost the em dashes and the triage-doc line (faultreport.py:24-33).
    - teardown.zsh:99/112: the STOP and deferred text now merges git stdout and stderr; the old code used stderr, else stdout (wt_core.py:213, 251).
11. wt/tools/lib/git.zsh:58-64 -- wt_worktree_list drops the `bare` line, but the old status skips bare entries (wt_core.py:1275), so the status author has to re-parse the porcelain output. Fix: add a WT_WORKTREE_BARE array (or an empty-branch marker), filled from `bare` lines.
12. wt/tools/lib/config.zsh:30 -- `${line#$id}` uses $id unquoted as a pattern, so an id containing `*` or `[` strips the wrong text. Fix: `${line#"$id"}`.
13. component-principles.md rule 2 says a shared helper needs three verbs. These have fewer:
    - config.zsh as a whole (finish only, since land is finish.zsh)
    - wt_resolve_repo (one caller)
    - wt_is_deferred_remove (one caller)
    - wt_branch_proven_merged (prune only, a one-line wrapper of wt_is_ancestor)
    - wt_record_merged (finish only)
    - wt_pm_take (start only)
    Fix: move each into its verb or inline it, or record the ruling in wt/docs. The report's "the ruling placed it there" is not recorded in the component docs.

Checked and found sound:
- Dispatcher (cli/wt): verb table; the pending/usage/unbuilt (exit 70) and WT_UNBUILT_LOG paths; `(N)` on the lib glob; libs use `typeset -g` because they are sourced inside main().
- wt_fail: the infra and flow shapes match the old _fail (wt_core.py:183-202), including the `rstrip` equivalents.
- Fault report: one file per (key, day) with an exclusive header via noclobber, `WT_FAULT_REPORT_DIR` honoured, and the `(reported: <path>)` / `Recorded in` endings the suite pins (test_wt_cli.py:1584, 1601).
- Teardown: wt_wt_shape, wt_cleanup_steps, wt_keep_worktrees_dir and wt_worktree_remove (`$?` captured from the assignment, deferred check made on any exit code, keep entry before and after) match the old code at wt_core.py:974-1006.
- Merged route and markers: wt_merged_route, wt_branch_already_merged (now uses the full ref), wt_wip_tip and wt_undeletable_paths/wt_refuse_undeletable (prune rules, symlink skip, five-path cap, sorted under LC_ALL=C) match.
- wt_prune_debt: same order, counts and OK/remaining lines as wt_core.py:1310-1356; it uses only `branch -d`.
- No `branch -D`, `worktree remove --force` or `rm -rf` is run anywhere; those strings appear only as operator-facing text, as the contract requires.
- No JSON is parsed in zsh; findings_required.py and the pairs logic in crossrepo.py match the old code.
- The library never reads PM_SESSION_ID, CLAUDE_CODE_SESSION_ID, CODEX_THREAD_ID or WT_ACTOR itself; pm (design.md:86-90) and the verbs own them, and that is correct.

RE-VERIFY: Run this once start.zsh exists:
`/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt --pm new -k ResolutionTest -k test_unknown_ticket_not_claimable -k test_fault_row_ends_the_line_with_reported_path_and_dedups -v`
Expect `failed 0` and no pending. Findings 4-13 are not covered by that suite and need a hand check.
