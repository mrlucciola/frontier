# pm-wt-rewrite/01/01b pm core gitcommit.py and its tests fc-c3514f:fc-2b34c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-b-gitcommit.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/01b pm core gitcommit.py and its tests fc-c3514f:fc-2b34c9

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-b-gitcommit.md`

You are a worker on ticket **fc-2b34c9** (pm core), second of four serial workers on
its branch. The first built `pm/cli/pm`, `pm/tools/ticket`, `pm/tools/store.py` and
`pm/tools/verbs/init.py`; its report is
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-a.md` in the worktree.
You build `pm/tools/gitcommit.py`, port its tests, and wire the store's commit step to
it. Do only that.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9`, branch
  `fc-2b34c9`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`. If the worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop.
- Code standard: `docs/component-principles.md`. Read it first.

## Read first (selectively: budget is 80k tokens / 40 tool calls)

- The 01-core-a report, then `pm/tools/store.py` (find its commit function and the
  write path that calls it).
- `pm/docs/cut-list.md`, the "Dropped" row and the paragraph under it on gitfault.
- Old source, read-only, at `/Users/matthias/frontier/runtime-tools/pm/ticket/src/`:
  `gitcommit.py` (220 lines, read whole), `gitfault.py` 25-115 and 165-207 (skip
  117-163, the report writer, which is dropped), `ticket_core.py` 2142-2222
  (`locked_store`: how a `GitFault` becomes exit 3 and its text) and 2487-2608
  (`_default_branch`, `_off_default_branch`, `commit_store`).
- Old tests, read-only: `/Users/matthias/frontier/runtime-tools/pm/ticket/tests/test_gitcommit.py`
  (192 lines) and `test_gitfault.py` (206 lines).

## Deliver

1. `pm/tools/gitcommit.py`, one module owning every git call the store makes:
   - the store commit policy (`commit_store`: legacy default-branch commit of the
     ticket file, a fresh untracked `config.json` riding on the first commit, the
     off-default-branch skip with its printed by-hand command, a `history_ref` store
     committing by plumbing to `refs/heads/<history_ref>`);
   - the mechanics (`commit_paths` with `git commit -o`, the scrubbed `GIT_*` env,
     the timeout, `commit_blob_to_ref`, `GitFault`);
   - the fault classifier folded in from `gitfault.py`: identity-missing and signing
     detection and their exact remedy lines on stderr. Drop `_report_writer`,
     `_FauxCtx`, `_FauxState` and `report()`: the rewrite does not import from
     `~/.claude/hooks` (component principle 9). No optional-import fallback is
     needed; it is one module now.
2. `pm/tools/store.py`: replace the body of its commit function so it calls
   `gitcommit.commit_store` and turns a `GitFault` into the old exit-3 behavior and
   text, and a policy skip into the old one stderr line. Change no other function's
   signature; if you must, stop and report it.
3. `pm/tests/test_gitcommit.py`: port the old `test_gitcommit.py` and the
   `ClassifyTest` and announce/guard cases of `test_gitfault.py` that do not depend
   on the dropped report writer. Import `pm/tools/gitcommit.py` by path. Name each
   dropped test in NOT DONE with "report writer dropped".

Do not write `create.py`, `show.py`, `test_cli_contract.py`, any doc, or a README. Do
not edit `pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or anything under
`pm/docs/`; a parity test that looks wrong goes in NOT DONE with its name and why.
Never write under `~/frontier`.

## Gate (run from the worktree root, all must pass)

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_init -k HelpTextTest.test_epilog_exit_codes
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

The second must still end `parity: passed 3, pending 0, failed 0, skipped 0`. The third
must exit 0 with `failed 0`; paste its last three lines. The full run takes about four
minutes; run it once at the end.

## Report

Commit on `fc-2b34c9` with explicit `git add` paths, message `pm core: gitcommit
module and its tests (fc-2b34c9)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-b.md`,
commit it on the same branch, and print only that path.
