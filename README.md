# frontier: ICM layer

Adds Interpretable Context Methodology (ICM, Van Clief & McDermott, arXiv:2603.16021)
to the global agent config that frontier deploys to ~/.claude, ~/.codex, ~/.omlx.

Design rule: ICM is a per-workspace architecture. The global layer stays thin.
One always-loaded instruction, two skills loaded on demand, one vendor hook. Nothing else.

## Layout

```
general/                        vendor-agnostic; deployed to every provider
  instructions/icm.md           one section for the global AGENTS.md / CLAUDE.md
  skills/
    icm-architect/              upstream skill, vendored and committed at a pin (see VENDOR.md)
    icm-run/                    executor skill for existing workspaces (written here)
vendor/                         only where a provider has a feature or gap
  claude/hooks/icm-detect.sh    SessionStart: detect workspace, inject one line
  claude/settings.fragment.json the hook registration, in Claude Code's hooks schema
  codex/README.md               nothing extra; explains why
  omlx/README.md                unknown config model; explains what to verify
tests/test_hook.py              fixture workspaces through the hook; checks the JSON
```

## Deploying

This repo is a staging layer. frontier's deployer (`~/frontier/bin/deploy`) reads
frontier's own tree, not this one, and its content-hash sync reverts anything appended
to a deployed file by hand. Each item below is ported into frontier's source and
deployed from there.

| This repo | frontier source | Lands in |
|---|---|---|
| general/instructions/icm.md | `instructions/claude-global/CLAUDE.md` and `instructions/codex-global/` (via `tools/gen_instructions.py`) | ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md |
| general/skills/icm-run, icm-architect | `skills/icm-run/`, `skills/icm-architect/` | ~/.claude/skills/, ~/.agents/skills/ (verify the Codex path) |
| vendor/claude/hooks/icm-detect.sh | `hooks/icm/icm-detect.sh` (new package) | ~/.claude/hooks/icm/ |
| vendor/claude/settings.fragment.json | one entry in the `SessionStart` list of `config/claude/settings.config.json`, same shape as the existing entries | ~/.claude/settings.json |
| `_tools/*.py` allow rule (below) | `posture/posture.json` | per-provider permission files |

omlx: deploy the instruction only until `vendor/omlx/README.md`'s questions are answered.

Permissions: workspaces copy icm-architect's scripts into `_tools/`, so a deny-by-default
config needs an allow rule for `python3 _tools/*.py` (Claude: `Bash(python3 _tools/*)`;
Codex: the equivalent in its approval schema). It is a posture change, not a settings edit.

## First-time steps

1. Vendor the upstream skill once (needs network) and commit the result:
   `ICM_ARCHITECT_COMMIT=main bash general/skills/icm-architect/vendor.sh`, then paste the
   printed SHA into `PIN` in vendor.sh.
2. `python3 tests/test_hook.py` must print `OK`.
3. Port per the table above and deploy from frontier.
4. In any directory, say "build me a workspace for X" (icm-architect) or `cd` into a
   workspace and say `status` (icm-run).

## Sources

- Paper: https://arxiv.org/abs/2603.16021
- Protocol repo and 15 conventions: https://github.com/RinDig/Interpretable-Context-Methodology
- Builder skill: https://github.com/RinDig/icm-architect
