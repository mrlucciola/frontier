# vendor/claude

What Claude Code needs beyond the provider-neutral `general/` layer.

| File | Role |
|---|---|
| `install.py` | copies or symlinks everything into `~/.claude`, merges `settings.fragment.json` into `~/.claude/settings.json`, appends the instruction sections to `~/.claude/CLAUDE.md`. `--dry-run`, `--link`, `--uninstall`. |
| `settings.fragment.json` | the two hook registrations (SessionStart: `icm-detect.sh`; UserPromptSubmit: `concept-graph/recall.sh`) and the Bash allow rules for the `cg` command. Claude Code's own schema; merged, never copied over. |
| `hooks/icm-detect.sh` | SessionStart: one line of context when the cwd is an ICM workspace. |
| `hooks/concept-graph/recall.sh` | UserPromptSubmit: shell fast path over the concept lexicon, python only on a hit, at most one JSON object out, exit 0 always. |

The ICM hook has no matcher: its one line is wanted after `startup`, `resume`, `clear`
and `compact` alike, since each leaves the agent without it.

Deliberately not included, for ICM:

- A PreToolUse guard on `Read` that blocks files outside the current Inputs table.
  Brittle (the hook would have to parse the contract) and it fights the human-gate
  model, which assumes full visibility. The instruction plus skill is the enforcement.
- Sub-agent mechanics. `icm-run/references/delegate.md` is vendor-neutral; a
  workspace-specific subagent definition belongs in that workspace's `.claude/agents/`.

Runtime state the hook and the tool create: `~/.claude/concepts/` (cards, index,
lexicon, log, `.state/`). Never installed, never removed by `--uninstall`.

Why the allow rule uses the literal `~/.claude/tools/concept-graph/cg.py` form: Bash
permission rules match the command text as typed, and the skill tells the model to type
exactly that form. `Bash(cg:*)` covers a `cg` wrapper on PATH if you add one.

Tests: `python3 tests/test_hook.py` (ICM hook), `python3 tests/test_recall_hook.py`
(recall hook end to end, including "python never starts on a miss").
