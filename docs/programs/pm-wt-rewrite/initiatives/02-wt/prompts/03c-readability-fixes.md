# pm-wt-rewrite/02/03c wt integration: readability review fixes fc-262fa8:fc-8c1f62

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03c-readability-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/03c wt integration: readability review fixes fc-262fa8:fc-8c1f62

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03c-readability-fixes.md`

You are a worker on ticket fc-8c1f62, the last fix round. You start with zero context.
Your worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62` on branch
`fc-8c1f62`; the overseer created it. The new wt is complete and green (suite on the new
pm: passed 123, pending 0, failed 0; `wt selftest` passes); this round changes no
behavior.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
its binding rules and code rules bind you, with this change: for this round you may edit
`wt/cli/wt`, every file under `wt/tools/`, `wt/AGENTS.md` and `wt/INSTALL.md`.
`wt/tests/` stays read-only.

## Input

The review: `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03-review.md`
(line numbers are at commit 5b2e29a). The code standard:
`/Users/matthias/projects/frontier-clean/docs/component-principles.md`.

## Fix, as the overseer ruled

Apply every finding's fix as the review writes it, except where a ruling below says
otherwise:

- **Two-verb teardown helpers stay shared.** `wt_stop_remove_failed`, `wt_deferred_line`,
  `wt_refuse_undeletable`, `wt_merged_route` (finish and park) are a recorded exception
  to rule 2, like `wt_findings_required`: finish auto-parks through park, so they are
  one teardown family. Record both exceptions in `wt/AGENTS.md`, one line each.
- **Mass-deletion threshold.** Move `wt_wip_tip` into `start.zsh`. Keep
  `WT_MASS_DELETE_MIN` in `teardown.zsh` (start and park both use it) and make start
  use it instead of `50`.
- **Session precedence.** One rule in every verb: `--session` overrides the environment.
  Change park's `pm_session` to match, unless a suite test fails because of it; then
  restore it and add a one-line comment saying which test needs it and why.
- **`_wt_red_covered`.** Inline it into `_wt_red_scan` as a loop if that reads straight;
  otherwise keep it and add one comment naming the caller-scoped arrays it reads.
- **Fault directory default** becomes `$HOME/frontier/docs/backlog/inbox/infra-faults`
  (the same path on this machine); `wt/INSTALL.md` names it.
- **Operator hand-off strings** (`rm -rf`, `git worktree remove --force` in the text wt
  prints): quote the paths with `${(q)...}`, and record in `wt/AGENTS.md` that wt hands
  these commands to the operator in its failure lines and never runs them.
- `finish.zsh` stays one file (land is the same verb); with the dead code, unused
  parameters and locals gone, add a short header comment saying `land` arrives with
  `WT_VERB=land` from the dispatcher and what the merged-route codes 0, 1, 2 mean.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt --pm new
/bin/zsh /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt selftest
```

The first: exit 0, `pending 0, failed 0`. The second: `SELFTEST PASSED`. `/bin/zsh -n` on
every zsh file you touched, one call each. Then
`rg -n 'rc == 70|cl-0c03c7|cmds_text|> 50' /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/tools`
prints nothing (exit 1). Paste all of it in EVIDENCE, with one line per review finding
saying fixed or ruled.

## Stop and report

Commit on branch `fc-8c1f62` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03c-readability-fixes.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
