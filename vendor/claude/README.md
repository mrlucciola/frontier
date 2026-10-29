# vendor/claude

Only what Claude Code has that the others lack.

- `hooks/icm-detect.sh`: SessionStart hook. Detects an ICM workspace at cwd and injects
  one line via `hookSpecificOutput.additionalContext`. Silent otherwise. Exit 0 always.
- `settings.fragment.json`: the hook registration. No matcher: the line is one sentence
  and is wanted after `startup`, `resume`, `clear`, and `compact` alike, since each of
  those leaves the agent without it.

Deliberately not included:

- A PreToolUse guard on `Read` that blocks files outside the current Inputs table.
  Brittle (the hook would have to parse the contract) and it fights the human-gate model,
  which assumes full visibility. The instruction plus skill is the enforcement.
- Sub-agent mechanics. `icm-run/references/delegate.md` is vendor-neutral; if a
  workspace-specific subagent definition is wanted, it belongs in that workspace's
  `.claude/agents/`, not here.
