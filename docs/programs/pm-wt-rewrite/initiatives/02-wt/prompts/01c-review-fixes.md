# pm-wt-rewrite/02/01c wt core: lib review fixes fc-262fa8:fc-122c0d

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01c-review-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/01c wt core: lib review fixes fc-262fa8:fc-122c0d

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01c-review-fixes.md`

You are a worker on ticket fc-122c0d, the fix round after review. You start with zero
context. Your worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d`
on branch `fc-122c0d`; the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run the installed `wt`, never mutate tickets with `pm ticket`, never
merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest under
NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`, provider
config dirs, this repo's `pm/`, `WT/tests/`. **Hand checks run in throwaway dirs under
`$TMPDIR`, never under the worktree's `.tmp/`; a driver that needs a git repo stops at
once if `git init` fails** (a refused `git init` once let git act on the real
repository). Most of these fixes need no git repo: test the zsh expansions directly.

## Input

The review: `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01-review.md`.
The lib: `WT/cli/wt`, `WT/tools/lib/*.zsh`, `crossrepo.py`, `findings_required.py`; its
two reports `reports/01a-core.md` and `reports/01b-teardown.md` beside the review. Old
source (read-only): `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`,
`crossrepo.py`, `faultreport.py`.

## Fix, as the overseer ruled

- Findings 1 to 9, 11 and 12: apply the review's fix as written. For 1, 6 and 7 prove the
  zsh behavior with a tiny zsh script under `$TMPDIR` before and after (print the
  expansion), and paste both results.
- Finding 10: restore the old text in every listed line (the contract keeps every
  output line); for the STOP and deferred lines use stderr, else stdout, as the old
  code did.
- Finding 13 (principle 2, three callers): 
  - **Delete `config.zsh`.** `.wt/gate` and `.wt/known-red` have one user, `finish`;
    the finish worker writes them in `finish.zsh`. Keep the fixed text of the
    non-executable-gate refusal in your report so the finish worker can copy it.
  - **`wt_findings_required` stays shared** (finish and park), moved into `pm.zsh`;
    `findings_required.py` stays. The overseer records this as a proposed amendment to
    principle 2 (two verbs that share one teardown family).
  - **Inline** `wt_resolve_repo` into `wt_resolve_repos`, `wt_is_deferred_remove` into
    `wt_worktree_remove`, and `wt_branch_proven_merged` into `wt_prune_debt`.
  - **Remove** `wt_record_merged` (finish writes the marker itself) and the one-line
    wrappers `wt_pm_take`, `wt_pm_done`, `wt_pm_park`, `wt_pm_drop`, `wt_pm_emit`:
    verbs call `wt_pm <store> <session> <verb> ...` directly. Keep `wt_pm` and
    `wt_pm_get`.
  - Check nothing left in the lib calls a removed function (`rg -n` for each name).

Then write the updated function list, one line each with callers, at the top of your
report's DID, so the step-2 workers read the lib from it.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt --pm new --allow-pending
```

exit 0, `failed 0`. `/bin/zsh -n` on `WT/cli/wt` and each remaining `.zsh` file, one call
each. Paste the runner's last two lines and the zsh proofs in EVIDENCE.

## Stop and report

Commit on branch `fc-122c0d` with explicit `git -C <worktree> add <paths>` (and
`git -C <worktree> rm` for `config.zsh`); the message ends with
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01c-review-fixes.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
