# pm-wt-rewrite/03/03 Codex lifecycle hooks recorded and wired for pm fc-ccecda:fc-2c0656

```
cd ~/projects/frontier-clean/.worktrees/fc-2c0656 && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/03-codex.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-2c0656 worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path instead.

---

# pm-wt-rewrite/03/03 Codex lifecycle hooks recorded and wired for pm fc-ccecda:fc-2c0656

`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/03-codex.md`

You are a worker for ticket **fc-2c0656** (epic fc-ccecda). You start with zero
context. The worker brief binds you and is not restated here:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656`, branch
  `fc-2c0656`. The overseer created it. Every edit is under it; every git command is
  `git -C <that path> ...`. You never run `wt`, never merge, never run
  `pm ticket close|note|claim`.
- Write set: `pm/INSTALL.md` (a new "Codex" subsection under "Harness hooks", in the
  shape of the "Claude Code" and "opencode" subsections, with Verify, Disable and
  Remove), a registration fragment under `pm/config/codex/` if Codex supports any of
  the events, and a probe under `pm/tests/codex/`. Nothing else under `pm/`; if
  `pm hook` itself must change to accept Codex's payload, stop and report what and
  why in NOT DONE.
- Read-only, never written: `~/.codex` (including `config.toml` and `hooks.json`),
  `~/.local/bin`, `~/frontier`. Registering anything in Codex's configuration is an
  operator step you write down, never perform.
- You cannot start a Codex session, and must not try (`codex`, `codex exec`, or any
  verb that contacts a model). Reading the client's help, version and bundled docs is
  fine.

## The spec

`pm ticket show fc-2c0656 --all-notes`. In short: from the installed client's
documentation and a probe, state which session-start, prompt and stop events Codex
exposes; wire `pm hook <event>` to those; where an event does not exist, the
repository `AGENTS.md` line that `pm init` prints carries the guidance. No claim
without its evidence.

## What the overseer already saw (verify, do not trust)

- The client is `/Users/matthias/.local/bin/codex`; it is not on the agent `PATH`, so
  call it by absolute path.
- `/Users/matthias/.codex/hooks.json` exists, and `~/.codex/config.toml` has
  `[hooks.state."/Users/matthias/.codex/hooks.json:user_prompt_submit:0:0"]`, which
  suggests Codex reads a hooks file with at least a `user_prompt_submit` event.
- What `pm hook` reads: `pm/docs/design.md` "Harness hooks" (one JSON object on stdin
  with any of `cwd`, `session_id`, `prompt`, `stop_hook_active`; Claude's field
  names) and `pm/tools/verbs/hook.py`. The Claude fragment is
  `pm/config/claude/hooks.json`.

## Steps

1. Establish the event names, the hooks file format, the stdin payload fields, and how
   a hook's stdout or exit code reaches the model, from: `codex --version`,
   `codex --help` and any hooks-related subcommand help, docs shipped with the
   installed client (find the package the `codex` symlink or script points into), and
   `~/.codex/hooks.json` as a working example. Record each source as a path or a
   command with its output.
2. Write the probe: a small script under `pm/tests/codex/` that, registered as a
   Codex hook for each candidate event, appends the event name, its argv and its stdin
   payload to a file the operator names, and exits 0 printing nothing. Plus the exact
   operator steps to register it, run one short Codex session, read the capture, and
   unregister it. Prefer a scratch `CODEX_HOME` if the client supports it and say
   whether auth carries over; if you cannot tell, say so.
3. Map the payload to what `pm hook` reads. If the fields match, the fragment calls
   `pm hook <event>` directly. If they differ, say exactly which field differs; do
   not write an adapter in this ticket, list it in NOT DONE.
4. Write the Codex subsection of `pm/INSTALL.md`: what is proven from docs, what only
   the probe would prove (marked as not yet proven, with the probe step that proves
   it), registration as operator steps in the handed-off-actions shape
   (`/Users/matthias/frontier/references/protocols/handoff-contract/README.md`
   "Handed-off actions"), and the `AGENTS.md` fallback for any missing event.

## Gate

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s pm/tests
python3 -B docs/check_structure.py
```

Run from the worktree root, each once. Also run the probe script once by hand with a
sample payload on stdin and a capture path under the worktree's `.tmp/`, and show the
captured line.

## Budget and report

Stop at 80k tokens or 40 tool calls. If you get there, commit what is green and list
the remainder in NOT DONE.

Commit on branch `fc-2c0656` with explicit `git add` paths. The commit message ends
with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write your
report in the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/03-codex.md`,
commit it on the same branch, and print only that path. BLOCKED ON OPERATOR carries
the probe run as numbered steps. NOT DONE says plainly what was not proven.
