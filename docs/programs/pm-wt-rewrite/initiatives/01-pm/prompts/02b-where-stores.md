# pm-wt-rewrite/01/02b pm where and stores verbs fc-c3514f:fc-459fe0

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/02b-where-stores.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/02b pm where and stores verbs fc-c3514f:fc-459fe0

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/02b-where-stores.md`

You are a worker on ticket **fc-459fe0** (pm routing), second of two serial workers on
its branch. The first built `pm/tools/routing.py` and wired it into the entry,
`store.py` and `show`; its report is `reports/02a-routing-module.md` under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree. You build the `where`
and `stores` verbs. Do only that.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0`, branch
  `fc-459fe0`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`; `cd` is refused by a hook, so use absolute paths. If the
  worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop. Budget: 80k tokens / 40
  tool calls; near it, commit what is green and list the rest in NOT DONE.
- Code standard: `docs/component-principles.md`. Read it first.

## Read first (selectively)

- The 02a report; `pm/tools/routing.py`; one existing verb file
  (`pm/tools/verbs/show.py`) for the shape a verb takes here.
- Old source, read-only, at `/Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket`.
  Line numbers move; find each with `rg -n`: `cmd_where`, `cmd_stores`, their
  parsers in `_main` (`add_parser("where"`, `add_parser("stores"`), and the
  helpers `cmd_where --mutate` calls (`refuse_if_unclaimed`, `refuse_if_closed`,
  `close_open_children`, `parse_findings`).
- Parity tests: in `pm/tests/test_cli_parity.py`, every `test_where_*` and
  `test_stores_*` test and `HelpTextTest.test_stores_check_help_names_checks`.

## Deliver

1. `pm/tools/verbs/where.py`: port of `cmd_where`, including `--mutate` preflight
   with `--verb` and `--findings`, writing nothing. Its close-time checks (findings
   parsing, epic with open children, unclaimed release) are the same rules
   `close` and `release` will use (fc-d73327): put what both need in `store.py`
   additively, or in `routing.py` if it is about which store owns an id, and say
   which in DID.
2. `pm/tools/verbs/stores.py`: port of `cmd_stores`, the listing and `--check` with
   every check its help names and exit 2 on problems.

Do not edit `pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or anything under
`pm/docs/`; a parity test that looks wrong goes in NOT DONE with its name and why.
Change no existing function signature in a shared module; if you must, stop and
report it. Never write under `~/frontier`.

## Gate (absolute paths, from the worktree root)

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_where -k test_stores -k HelpTextTest --allow-pending
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k StoreRoutingTest --allow-pending
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

Every run must exit 0 with `failed 0`. Redirect the parity runs to files under the
worktree's `.tmp/` and paste only their `parity:` and `unbuilt verbs still needed:`
lines, plus every `pending:` line of the first run. Run the full suite once at the end.

## Report

Commit on `fc-459fe0` with explicit `git add` paths, message `pm routing: where and
stores verbs (fc-459fe0)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/02b-where-stores.md`,
commit it on the same branch, and print only that path.
