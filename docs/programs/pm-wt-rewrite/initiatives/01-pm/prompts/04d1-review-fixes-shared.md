# pm-wt-rewrite/01/04d1 pm review fixes: shared modules and the entry fc-c3514f:fc-59011f

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04d1-review-fixes-shared.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/04d1 pm review fixes: shared modules and the entry fc-c3514f:fc-59011f

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04d1-review-fixes-shared.md`

Ticket **fc-59011f** (pm integration). A read-only reviewer read every code file
against `docs/component-principles.md`; its findings are
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04-review.md` in the worktree.
You fix the ones listed below, which touch the shared modules and the entry; the next
worker fixes the verb-local ones. The overseer's rulings decide scope, not the review.
Read and obey `docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md`
("Where you work" and "Rules"; refusal texts stay byte-identical).

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f`.

## Fix (each item is a review finding; read its line there)

1. `gitcommit.py`: rename `_git`, `_clean_git_env`, `_fault`, `_default_branch` to `git`,
   `clean_env`, `fault`, `default_branch`, update every caller (store, archive, summary,
   history) and `pm/tests/test_gitcommit.py`.
2. `summary.py` and `close.py`: their direct `subprocess.run(["git", ...])` calls go
   through `gitcommit.git(...)` with the same timeouts. `history.py`'s bytes call stays,
   with a one-line comment saying why.
3. `acting_identity(session)` moves from `verbs/release.py` to `store.py` beside
   `session_assignee`; `release.py` and `close.py` call it there; no verb imports another
   verb except `lint` importing `validate` (ruled acceptable).
4. `store.hold_is_stale` and `HOLD_STALE_SECONDS` become the one copy: `summary.py`
   drops its own and calls the store's.
5. `archive.hint` and its now-unused imports are deleted (summary keeps its copy).
6. `label_problem` and `LABEL_MAX` move from `store.py` into `create.py`, their one
   user; `LABEL_RE` stays in `store.py`.
7. `store._located` becomes public `store_root(repo)`; `history.py` calls it instead of
   repeating the "no ticket store found" text. `routing.py` and `validate.py` keep their
   own copies only where a parity test pins those bytes (check with `rg`).
8. `getattr(args, "repo", None)` becomes `args.repo` in every verb (the entry always
   defines it).
9. `pm/tools/ticket`: `ROUTED_VERBS` maps verb to a mutate flag only (every entry used
   `"id"`); drop the `(fc-c10bcf)` ticket id from its comment.

Not in scope, by ruling: the `.gitignore` comment `init` writes stays byte-identical to
the old CLI; principle amendments go to fc-121923, not here.

## Gate

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_views.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B pm/tests/golden_diff.py
rg -n 'gitcommit\._|from verbs\.release|fc-c10bcf|getattr\(args, "repo"|def hint\(' pm/tools
```

All pass; parity ends `pending 0, failed 0`; the golden diff exits 0; the `rg` prints
nothing. Redirect the parity and golden runs to the worktree's `.tmp/` and paste their
summary lines.

## Report

Commit message `pm integration: review fixes in shared modules (fc-59011f)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04d1-review-fixes-shared.md`.
