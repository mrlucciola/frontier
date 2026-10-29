# vendor/codex

Nothing extra. The general layer covers Codex:

- `general/instructions/icm.md` lands in `~/.codex/AGENTS.md`. It already tells the agent
  to fall back to `CLAUDE.md` as the entry file when a workspace has no `AGENTS.md`, which is
  the main Codex gap (older ICM workspaces ship only `CLAUDE.md`).
- Skills land in `~/.agents/skills/` per icm-architect's install table. Verify this path
  against the installed Codex version before relying on it.

Unverified: whether this Codex version has a session-start hook equivalent to Claude's.
If it does, port `vendor/claude/hooks/icm-detect.sh` (the script is shell, the JSON
envelope is the only Claude-specific part). If not, the instruction alone does the job.
