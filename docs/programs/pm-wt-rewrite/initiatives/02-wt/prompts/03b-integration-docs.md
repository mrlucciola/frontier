# pm-wt-rewrite/02/03b wt integration: component docs and contract fc-262fa8:fc-8c1f62

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03b-integration-docs.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/03b wt integration: component docs and contract fc-262fa8:fc-8c1f62

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03b-integration-docs.md`

You are a worker on ticket fc-8c1f62, part 2 of 2. You start with zero context. Your
worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62` on branch
`fc-8c1f62`; the overseer created it. The code is done: every verb, `selftest`, and the
pm plugin under `wt/pm-plugin/`. You write documentation only.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run the installed `wt`, never mutate tickets with `pm ticket`, never
merge. Stop at 80k tokens or 40 tool calls. Read-only: everything under `~/frontier`,
`~/.local`, `~/.config/pm`, provider config dirs, `pm/`, and all of `wt/` except the four
docs below. You edit exactly: `wt/README.md`, `wt/AGENTS.md`, `wt/INSTALL.md`,
`wt/docs/contract.md`, and one row of `docs/contributing.md`.

## Read

`pm ticket show fc-8c1f62` and its notes (the spec); `/Users/matthias/projects/frontier-clean/docs/contributing.md`
(where component docs go and what each holds); `pm/README.md`, `pm/AGENTS.md`,
`pm/INSTALL.md` (the sibling component's docs, the shape to match);
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/INITIATIVE.md`
"Facts not to re-derive" (every ruling the docs must record); the code under `wt/cli`,
`wt/tools`, `wt/pm-plugin`, and `wt/tests/run_wt.py`'s docstring.

## Deliver

- **`wt/docs/contract.md`**: rewrite the verbatim old README into this component's own
  reference. Keep every verb, refusal and output line the new wt keeps (the suite
  `wt/tests/test_wt_cli.py` is the authority on wording). Remove frontier paths, ticket
  ids, deploy and posture mechanics, and the old Layout and Cross-repo sections'
  Python module names. Record as dropped or changed, each in one line with the reason:
  `wt pending` (use `pm ls parked`); `.pm/config.json` `gate`/`known_red` replaced by an
  executable `.wt/gate` and `.wt/known-red`; a non-executable `.wt/gate` refuses; the
  `selftest` scratch removal as the one `rm -r` wt runs; the old wt deviations the suite
  pins on the new side (the stale worktree of a closed ticket is torn down); the
  rebase-conflict resume kept as is pending fc-f0cc16 -- here a ticket id is allowed,
  because it points at open work. Keep the Claude and Codex sandbox notes only where
  they tell a wt user what an output line means.
- **`wt/README.md`**: what wt is, the verbs, how it reaches pm (`pm get`, `pm take`,
  `pm done`, `pm park`, `pm drop`, `pm emit`; `WT_CALLER=1`), its files (`.wt/gate`,
  `.wt/known-red`), the plugin, and a link to the contract.
- **`wt/INSTALL.md`**: install (the `~/.local/bin/wt` symlink to `wt/cli/wt`; the plugin
  symlink `~/.config/pm/plugins/wt` -> `wt/pm-plugin`), verification (`wt selftest`
  prints `SELFTEST PASSED`), configuration (`.wt/gate`, `.wt/known-red`, and the
  environment variables wt reads: `WT_ACTOR`, `PM_SESSION_ID`, `CODEX_THREAD_ID`,
  `CLAUDE_CODE_SESSION_ID`, `WT_FAULT_REPORT_DIR`, `GIT_PAIRS_FILE`), and removal. These
  are operator steps the cutover runbook will run; write them as commands, but do not
  run them.
- **`wt/AGENTS.md`**: maintenance routes; the test commands
  (`/usr/bin/python3 -B wt/tests/run_wt.py --cli wt/cli/wt --pm new`, the `--pm old` run
  against the old wt, `-k`, and the plugin transcripts run with
  `/usr/bin/python3 -B pm/tests/run_transcripts.py --dir wt/tests/t`); that
  `tests/test_wt_cli.py` is accepted and edited only by an explicit ruling; the no
  `branch -D` / `worktree remove --force` / `rm -rf` rule with the selftest exception.
- **`docs/contributing.md`**: delete the `wt` `A-RUN` row from the exemptions table.

Keep each doc short; no history, no ticket ids except the one allowed above.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/docs/check_structure.py
```

exit 0. Also `rg -n 'frontier/|runtime-tools|fr-[0-9a-f]{6}|cl-[0-9a-f]{6}' <worktree>/wt/docs/contract.md <worktree>/wt/README.md <worktree>/wt/INSTALL.md <worktree>/wt/AGENTS.md`
prints nothing (exit 1). Paste both in EVIDENCE.

## Stop and report

Commit on branch `fc-8c1f62` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03b-integration-docs.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
