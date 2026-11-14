# pm-wt-rewrite/01/04c pm integration: component docs fc-c3514f:fc-59011f

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04c-docs.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/04c pm integration: component docs fc-c3514f:fc-59011f

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04c-docs.md`

Ticket **fc-59011f** (pm integration), third serial worker on its branch. The code is at
parity and the golden diff is clean (reports `04a-*` and `04b-*` under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/`). You write the component's
docs. Read and obey `docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md`
("Where you work" and "Rules"); your write set is the docs named below and nothing
under `pm/tools/` or `pm/tests/`.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f`.

## Read first

`docs/contributing.md` (what a component's README, AGENTS and INSTALL must hold),
`README.md` (behavioral contract, component table), one finished component's docs for
the house shape (`session-telemetry/README.md`, `AGENTS.md`, `INSTALL.md`), and the
current `pm/README.md`, `pm/AGENTS.md`, `pm/INSTALL.md`, `pm/docs/cut-list.md`.

## Deliver

1. `pm/INSTALL.md`: setup by symlinking `pm/cli/pm` into `~/.local/bin` (with the note
   that the installed frontier `pm` lives there today and cutover is a separate
   operator-run runbook, so these steps are for a machine without it or for a side
   install under another name), verification (a command and its expected output),
   disabling, removal, and what removal does to `.pm/` data (nothing: stores are plain
   files in each repo). Every command runnable as written.
2. `pm/README.md`: what pm is, its two entry points (`pm ticket <verb>`, `pm view
   board|overview`), the kept verbs in one line each or a table, the store registry
   default `~/.config/pm/stores.json` and `PM_STORES_FILE`, and the routes table kept
   current. Drop the "being rewritten" status line; say instead that the installed `pm`
   stays the frontier one until the operator's cutover.
3. `pm/AGENTS.md`: the maintenance routes and gate commands as they are now, including
   `golden_diff.py`, `test_cli_contract.py`, `test_gitcommit.py`, `test_views.py`, and
   the fact that the unbuilt mechanism is gone.
4. The pm row in the root `README.md` component table exists; change its purpose text
   only if the README you wrote says something different.

## Gate

```sh
python3 -B docs/check_structure.py
/usr/bin/python3 -B -m unittest discover -s pm/tests
```

Run from the worktree root. `check_structure.py` must report no violation in `pm/` or
the root README; a violation elsewhere that exists on main too (`git -C <main checkout>`
is not yours to change) is listed in NOT DONE with its text, not fixed.

## Report

Commit message `pm integration: component docs (fc-59011f)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04c-docs.md`.
