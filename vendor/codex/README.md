# vendor/codex

Nothing is installed automatically for Codex; `install.py` targets Claude Code. The
general layer still applies:

- `general/instructions/icm.md` and `general/instructions/feynman.md` belong in
  `~/.codex/AGENTS.md` (append, same as the Claude installer does for CLAUDE.md).
- Skills: copy or symlink `general/skills/*` into `~/.agents/skills/` (verify the path
  against the installed Codex version).
- The concept store and `cg` are provider-neutral. Codex sessions use the same
  `~/.claude/tools/concept-graph/cg.py` and the same `~/.claude/concepts/` store, so a
  card learned in one harness is recalled in the other. Codex's sandbox must allow
  reads and writes there; if it does not, set `CONCEPT_GRAPH_ROOT` to a path it allows
  and accept two stores.

## Prompt recall hook (unverified on this Codex version)

Recent Codex versions run `user_prompt_submit` hooks from `~/.codex/hooks.json` and add
the hook's stdout to the turn. The engine already supports the bare-text envelope:

```json
{
  "type": "command",
  "command": "bash \"$HOME/.claude/hooks/concept-graph/recall.sh\" --plain",
  "timeout": 3,
  "statusMessage": "concept recall"
}
```

`--plain` makes `cg.py hook-recall` print the block itself instead of Claude's JSON
wrapper. Codex will ask to trust the new hook once. If this Codex version has no hook
support, the skill's own recall step (step 0) still works; only passive recall is lost.
