# pm-wt-rewrite/04/03b pm harness hooks: Claude and opencode fc-2a6562:fc-a761be

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03b-hooks.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/03b pm harness hooks: Claude and opencode fc-2a6562:fc-a761be

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03b-hooks.md`

Ticket **fc-a761be**, one of three step-3 workers running in parallel. Every verb but
`hook` and `import` is built and merged. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first. Run
`pm ticket show fc-a761be` (the old pm, read-only) for the ticket body. fc-a731f4
edits `pm/cli/pm`, `store.change` and `orient.py` in parallel; do not edit those.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-a761be`.

## Read first

`pm/docs/design.md` "Harness hooks"; transcript `16-hook.t`; `pm/tools/verbs/orient.py`;
`pm/INSTALL.md`; `docs/instruction-delivery.md`; the in-place opencode plugin at
`~/.config/opencode/plugins/pm/index.ts` (read only; never edit it or anything under
`~/.config`).

## Deliver

1. `pm/tools/verbs/hook.py`: `pm hook session-start|prompt|stop`, reading one JSON
   object on stdin (any of `cwd`, `session_id`, `prompt`, `stop_hook_active`; a
   missing or bad stdin is an empty object). `cwd` decides the store; `session_id`
   wins over the environment for identity. `session-start` prints nothing outside a
   store, else `pm tickets in this repo:`, the bare `pm` output, `All verbs: pm help`;
   get the bare `pm` output by running this component's `pm` with no argument in
   `cwd` (a subprocess of `/usr/bin/python3 <component>/cli/pm`), so plugin orient
   lines arrive without code here. `prompt` and `stop` exactly as transcript 16.
2. `pm/config/claude/hooks.json`: the SessionStart, UserPromptSubmit and Stop
   registrations, each command the absolute path of the component's `pm` with
   `hook <event>`. Before relying on stdout reaching context and on exit 2 from Stop
   blocking with stderr shown to the model, read the Claude Code hooks documentation
   (use WebFetch on https://docs.claude.com/en/docs/claude-code/hooks) and record
   what you read, with the URL, in the report.
3. `pm/hooks/opencode/pm.ts`: ported from the in-place plugin, reduced to building
   that JSON and calling `pm hook`; no ticket parsing in TypeScript.
4. `pm/INSTALL.md` provider sections: the exact settings edit as operator steps,
   verification in a fresh session, disabling, removal. Run
   `python3 -B docs/check_structure.py`.

What cannot be verified from inside this session (a real Claude or opencode session
loading the hooks) goes in NOT DONE as not proven, with the operator command.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 16-hook -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
python3 -B docs/check_structure.py
```

The first exits 0 with `passed 1`. The second exits 0 with `failed 0` and no `hook`
in its unbuilt line.

## Report

Commit message `pm harness hooks: pm hook, Claude and opencode wiring`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-a761be/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/03b-hooks.md`.
