# pm-wt-rewrite/01/01e pm core review fixes fc-c3514f:fc-2b34c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-e-review-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/01e pm core review fixes fc-c3514f:fc-2b34c9

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-e-review-fixes.md`

You are a worker on ticket **fc-2b34c9** (pm core), fixing what a read-only review
found before five parallel tickets build on this code. The review is
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-review.md` in the worktree;
the overseer's rulings on it are below and they decide scope. Do exactly the list.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9`, branch
  `fc-2b34c9`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`; `cd` is refused by a hook, so use absolute paths. Temp
  stores and git repos go in `$TMPDIR` (tempfile defaults), never the repo's `.tmp/`.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
  You never run `wt`, `pm ticket` writes, rebase or merge. Commit and stop. Budget:
  80k tokens / 40 tool calls; near it, commit what is green and list the rest.
- Code standard: `docs/component-principles.md`.

## Read first

The review; `pm/cli/pm`, `pm/tools/ticket`, `pm/tools/store.py`,
`pm/tools/gitcommit.py`, `pm/tools/verbs/create.py`, `pm/tools/verbs/show.py`,
`pm/tests/test_cli_contract.py`. Old source, read-only, by function name with
`rg -n` (line numbers move): frontier `runtime-tools/pm/cli/pm`; `ticket`: `fmt_line`,
`claim_veto`, `edge_target`; `ticket_core.py`: `locked_store`, `commit_store`.

## Fix (overseer rulings on the review)

1. `show.py`: decide "another store's id" with `store.is_remote_ref`, as `create`
   does, so a legacy prefix whose row this store lacks calls `unbuilt("routing")`.
2. History-ref by-hand remedy: when the caller named a store (`--store`/`--repo`),
   print `pm ticket history sync --repo <repo>` as the old code does. Pass the repo
   through as a new keyword argument with a default (`commit(root, message,
   repo=None)`), so no existing call changes.
3. `pm/cli/pm`: `pm view` accepts only `board` and `overview`; bare `pm`, `pm -h` and
   `pm --help` print help and exit 0. Match the old dispatcher's usage text where it
   still fits the kept surface.
4. Archive index commit: give `store.Store` a list attribute of extra repo-relative
   paths a verb wants committed with the store file (name it for what it holds), and
   give `gitcommit.commit_store` a keyword argument with an empty default that adds
   them to the same commit. `commit` passes them through. No verb uses it yet; the
   archive verb will.
5. Move `fmt_line`, `claim_veto` and `edge_target` into `store.py` and have `create`
   and `show` call them there. `edge_target`'s cross-store branch keeps calling
   `unbuilt("cross-store-edge")`.
6. `Store` keeps `rows`, a list of `(lineno, obj)` for every non-blank line, as the old
   one did, for `validate`. Loading stays as permissive as the old one: no new
   validation.
7. `pm/tools/ticket`: `allow_abbrev=False` on the top-level parser only.
8. `gitcommit.commit_store`: a timeout or OSError on the `config.json` status probe
   reads as "tracked" and commits the ticket file alone, as the old code does.
9. Delete what no caller uses: `store.ID_RE`; `store._git` (route its callers through
   `gitcommit`'s runner); the `env=` parameters in `gitcommit` that no caller or test
   passes (keep any a test passes).
10. Remove the ticket id from the comment at `create.py` (rule 7). Keep
    `(cl-111ef6)` in `gitcommit.py`: a parity test pins it.
11. Add to `pm/tests/test_cli_contract.py`: `pm view create x` exits 2 and writes
    nothing; `pm --help` exits 0; a `history_ref` store whose commit fails, run with
    `--store` from another directory, prints the `--repo` remedy (make the ref update
    fail the way `test_ref_update_failure_exits_0_marks_pending_and_next_write_catches_up`
    in `test_cli_parity.py` does). Add to `pm/tests/test_gitcommit.py`: one test that
    `commit_store` with the new keyword commits the extra path in the same commit as
    the ticket file, and one that the default commits the ticket file alone.

Not in scope, by ruling: refusal texts the old CLI printed stay byte-identical (the
integration ticket diffs both CLIs on live stores), so the review's Q3 items are not
changed. The frozen-store refusal and routing-before-open belong to fc-459fe0.
Do not edit `pm/tests/test_cli_parity.py`, `run_parity.py` or `pm/docs/`. Never write
under `~/frontier`.

## Gate (absolute paths, from the worktree root)

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_create -k DuplicateGuardTest -k test_frozen_row_is_a_read_fallback_under_a_live_owner --allow-pending
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

All exit 0. Redirect the parity runs to the worktree's `.tmp/` and paste only their
`parity:` lines. The full run must show `passed 20` or more and `failed 0`.

## Report

Commit on `fc-2b34c9` with explicit `git add` paths, message `pm core: review fixes
(fc-2b34c9)` plus the trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
Write the report, in the worker-brief shape with one DID line per numbered fix (group
to stay within the shape), to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-e.md`,
commit it, and print only that path.
