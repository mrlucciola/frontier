# 03b pm harness hooks report

TICKET
fc-a761be (parent fc-2a6562), branch fc-a761be, worktree /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be.

DID
- `pm/tools/verbs/hook.py`: `pm hook session-start|prompt|stop`. One JSON object on stdin; missing, tty or bad stdin is `{}`. `cwd` picks the store (`store.find`), `session_id` sets `PM_SESSION_ID` so it wins over the environment. session-start prints the header, the bare `pm` output from a subprocess of `/usr/bin/python3 <component>/cli/pm` run in `cwd`, then `All verbs: pm help`. prompt and stop as transcript 16 (stop: stderr, exit 2, skipped when `stop_hook_active` is true or the ticket has a `hold`). Unknown event is a usage error. Docstring under 700 bytes.
- `pm/config/claude/hooks.json`: SessionStart, UserPromptSubmit, Stop, each `/Users/matthias/projects/frontier-clean/pm/cli/pm hook <event>`.
- `pm/hooks/opencode/pm.ts`: ported and reduced. Builds `{cwd, session_id, stop_hook_active}`, calls `pm hook`, puts session-start output in the keyed `pm` instruction entry (first prompt, refreshed after pm/wt bash calls), on idle calls `pm hook stop` and sends stderr as a synthetic turn on exit 2. No ticket parsing. pm binary: plugin option `pm`, else `$PM_BIN`, else `~/.local/bin/pm`.
- `pm/INSTALL.md`: "Harness hooks" section with Claude Code and opencode operator steps, verify, disable, remove. Claude steps edit the source `/Users/matthias/frontier/config/claude/settings.config.json` (settings are generated from there), not `~/.claude`.

EVIDENCE
- `/usr/bin/python3 -B pm/tests/run_transcripts.py -k 16-hook -v`: `passed 1, pending 0, failed 0`.
- `/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v`: `passed 19, pending 4, failed 0`; `unbuilt verbs still needed: import, plugins` (no `hook`).
- `python3 -B docs/check_structure.py`: `check_structure: ok (7 components, 4 exempted)`.
- Claude Code hooks documentation, read at https://code.claude.com/docs/en/hooks (docs.claude.com 301-redirects there): (1) "UserPromptSubmit, UserPromptExpansion, SessionStart, and PostModelSwitch: Claude Code adds plain-text stdout as context that Claude can see and act on." (2) exit-code table row "Stop | Yes | Prevents Claude from stopping, continues the conversation"; general rule "The message that comes with the block is your hook's stderr." (3) UserPromptSubmit hooks receive a `prompt` field; common fields include `session_id` and `cwd`; the SubagentStop example payload shows `stop_hook_active`, described there as under "Stop input". (4) Registration shape: `hooks.<Event>[{matcher?, hooks:[{type:"command", command}]}]`, matcher optional. I did not read the Stop section itself (the fetch tool truncates the page and returned the Stop region only as an unreadable saved file), so "Stop exit 2 shows stderr to the model" rests on the general rule above, and the `stop_hook_active` semantics on the SubagentStop example.

COMMITS
See `git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be log --oneline -n 2`; subject `pm harness hooks: pm hook, Claude and opencode wiring`.

NOT DONE
- Not proven: a real Claude session loading the hooks (context gets the session-start text, Stop blocks once and the model sees stderr). Operator: do the INSTALL.md Claude steps, then in a fresh session in a repo with a `.pm/` store run `pm take`, end the turn.
- Not proven: a real opencode session. Operator: `PM_BIN=~/.local/bin/pm-next opencode` after the INSTALL.md opencode steps. The `@opencode/plugin` API calls (`ctx.session.instructions.entry.put`, `ctx.session.hook`, `ctx.session.wait`, `ctx.session.synthetic`, `ctx.tool.hook`) are copied from the in-place plugin, not exercised. The TypeScript was not compiled or run.
- opencode identity gap: `who.token()` reads only `PM_SESSION_ID`, `CLAUDE_CODE_SESSION_ID`, `CODEX_THREAD_ID`. The hook passes opencode's session id through JSON, but the agent's own `pm take` in a bash call needs `PM_SESSION_ID=<opencode session id>` in its environment for the same token, or the stop hook will not see the ticket as held by that session. I do not know how the old plugin's environment gave `sha256(sessionID)[:8]`; I have not checked. This may need a `who.py` change or a plugin env hook; overseer decision.
- opencode has no per-prompt `mentioned:` output: the `prompt` hook's text field name is unknown to me, so `pm hook prompt` is not wired in pm.ts.
- Claude hook commands use the main-checkout path `/Users/matthias/projects/frontier-clean/pm/cli/pm`, which exists only after this branch merges. INSTALL.md says so.
- No `pm/tests/test_budgets.py` exists yet, so the 760-byte session-start ceiling is untested here; the output is the header, bare pm (<=700) and one line.
- Settings line numbers in INSTALL.md (183-190, 212-219) are as of today in `/Users/matthias/frontier/config/claude/settings.config.json`; the current text is quoted in each step.

BLOCKED ON OPERATOR
- Settings edits and deploy per `/Users/matthias/projects/frontier-clean/pm/INSTALL.md` "Harness hooks" (Claude: frontier `config-claude`, run with `--dry-run`; opencode: symlink step). Only after the step's last merge.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be/pm/tools/verbs/hook.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be/pm/config/claude/hooks.json
- /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be/pm/hooks/opencode/pm.ts
- /Users/matthias/projects/frontier-clean/.worktrees/fc-a761be/pm/INSTALL.md
