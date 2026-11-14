# pm-wt-rewrite/04/04d pm integration: component docs fc-2a6562:fc-d6c61c

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-d-docs.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/04d pm integration: component docs fc-2a6562:fc-d6c61c

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-d-docs.md`

Ticket **fc-d6c61c**, fourth of five serial workers on its branch. The new pm is
complete, `pm/v2/` is gone (reports `04-integration-a-*` to `-c-*`). You write the
component's final docs. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first; your
write set is `pm/README.md`, `pm/AGENTS.md`, `pm/INSTALL.md` and the pm row of the
root `README.md` component table, nothing under `pm/tools/` or `pm/tests/`.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c`.

## Read first

`docs/contributing.md`; the root `README.md` (behavioral contract, component table);
one finished component's docs for the house shape (`session-telemetry/README.md`,
`AGENTS.md`, `INSTALL.md`); `pm/docs/design.md`; the current pm docs, including the
provider sections fc-a761be added to `pm/INSTALL.md`.

## Deliver

1. `pm/README.md`: what pm is (an append-only event log per repository, verbs that
   follow an agent's work, plugins by file presence), the entry point and the verb
   list in one table (from `pm help`), the registry (`~/.config/pm/stores`,
   `$PM_STORES`), plugins (`~/.config/pm/plugins`, `$PM_PLUGINS`, the two shipped in
   `pm/plugins/`), the harness hooks, and the routes table. Say that the installed
   `pm` stays the frontier one until the operator's cutover.
2. `pm/AGENTS.md`: maintenance routes and gate commands as they are now:
   `run_transcripts.py`, `unittest discover -s pm/tests` (budgets, concurrency),
   `import_check.py`; never edit the transcripts, fixtures or design without the
   design owner.
3. `pm/INSTALL.md`: setup by one symlink into `~/.local/bin` (as a side install named
   `pm-next` while the frontier pm is installed), the plugin directory and how to link
   a plugin, the provider hook sections kept, verification (a command and its
   expected output), disabling, removal, and what removal does to `.pm` data and to
   the registry. Every command runnable as written.
4. The pm row in the root `README.md`: change its purpose text only if it no longer
   matches.

## Gate

Run from the worktree root:

```sh
python3 -B docs/check_structure.py
/usr/bin/python3 -B pm/tests/run_transcripts.py
```

## Report

Commit message `pm integration: component docs`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d6c61c/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-d-docs.md`.
