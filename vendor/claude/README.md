# vendor/claude

Only what Claude Code has that the others lack.

- `hooks/icm-detect.sh`: SessionStart hook. Detects an ICM workspace at cwd and injects
  one line via `hookSpecificOutput.additionalContext`. Silent otherwise. Exit 0 always.
- `settings.fragment.json`: merge into `~/.claude/settings.json` (frontier's merge step).
  Matcher `startup|resume`; `clear` is excluded on purpose so a `/clear` mid-run does not
  re-inject.

Deliberately not included:

- A PreToolUse guard on `Read` that blocks files outside the current Inputs table.
  Brittle (the hook would have to parse the contract) and it fights the human-gate model,
  which assumes full visibility. The instruction plus skill is the enforcement.
- Sub-agent mechanics. `icm-run/references/delegate.md` is vendor-neutral; if a
  workspace-specific subagent definition is wanted, it belongs in that workspace's
  `.claude/agents/`, not here.

Permissions: workspaces copy icm-architect scripts into `_tools/`. Add an allow rule for
`Bash(python3 _tools/*)` (or the project-scoped equivalent) if the global config is deny-by-default.
