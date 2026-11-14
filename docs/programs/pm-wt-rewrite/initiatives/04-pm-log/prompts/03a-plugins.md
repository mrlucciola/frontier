# pm-wt-rewrite/04/03a pm plugins: cmd, pre, post, orient; dispatch and pilot fc-2a6562:fc-a731f4

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03a-plugins.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/03a pm plugins: cmd, pre, post, orient; dispatch and pilot fc-2a6562:fc-a731f4

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03a-plugins.md`

Ticket **fc-a731f4**, one of three step-3 workers running in parallel. Every verb but
`hook` and `import` is built and merged. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.
Run `pm ticket show fc-a731f4` (the old pm, read-only) for the ticket body. This
ticket changes the path every mutating verb goes through: a read-only reviewer
checks your branch before it merges, so keep the change to `store.change` small and
plain.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4`.

## Read first

`pm/docs/design.md` "Plugins" and "Not carried over"; transcripts `15-plugins.t`,
`22-plugin-dispatch.t`, `23-plugin-pilot.t`, `17-help.t`; `pm/cli/pm`,
`pm/tools/store.py` (`change`), `pm/tools/verbs/orient.py`. For what the two plugins
replace: `pm/v2/tools/verbs/lint.py` (dispatch headings) and the pilot contract in
`pm/v2/tools/verbs/lint.py` and `summary.py`.

## Deliver

1. `pm/tools/plugins.py`: list plugin directories under `$PM_PLUGINS`, else
   `~/.config/pm/plugins`, in name order; run a named executable in each with the
   design's environment (`PM_OP PM_ID PM_STORE PM_BY PM_STATUS PM_TEXT PM_LABELS`
   plus the caller's environment). It is the one place that runs plugin files.
2. `pm/cli/pm`: `pm <name> args` runs `<name>/cmd` when it exists, passing args and
   exit code through; replace the `store.unbuilt("plugins")` in `no_verb`. `pm help`
   ends with `plugins: <names>` when any exist.
3. `store.change`: for each event to append, run `pre-<op>` outside the lock, before
   it is taken; a non-zero exit refuses with the plugin's output on stderr, exit 1,
   nothing appended. After the append, run `post-<op>` and print its stdout after the
   verb's own output (the verb prints first; return the post text to the caller or
   print it at exit, your choice, but every verb must get it without per-verb code).
   `dry_run` runs `pre` and skips `post`. Because `check` runs before `pre` to know
   the events, and again under the lock, it must stay pure.
4. `verbs/orient.py`: replace its `store.unbuilt("plugins")` with each plugin's
   `orient` stdout after the sections.
5. `pm/plugins/dispatch/cmd` (shell, reads `pm get <id> body`) and
   `pm/plugins/pilot/` (`cmd`, `orient`, `pre-done`, Python at `/usr/bin/python3`),
   per transcripts 22 and 23. Each plugin reads tickets only through `pm get` /
   `pm ls --json` and never parses JSON in shell.
6. Name `pm/plugins/` in `pm/AGENTS.md`'s routes table and run
   `python3 -B docs/check_structure.py`.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 15-plugins -k 17-help -k 22-plugin-dispatch -k 23-plugin-pilot -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
python3 -B docs/check_structure.py
```

The first exits 0 with `passed 4`. The second exits 0 with `failed 0` and no
`plugins` in its unbuilt line.

## Report

Commit message `pm plugins: cmd, pre, post and orient; dispatch and pilot`. Report
path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/03a-plugins.md`.
