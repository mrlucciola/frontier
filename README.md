# frontier: ICM layer

Adds Interpretable Context Methodology (ICM, Van Clief & McDermott, arXiv:2603.16021)
to the global agent config that frontier deploys to ~/.claude, ~/.codex, ~/.omlx.

Design rule: ICM is a per-workspace architecture. The global layer stays thin.
One always-loaded instruction (under 12 lines), two skills loaded on demand,
one vendor hook. Nothing else.

## Layout

```
general/                        vendor-agnostic; deployed to every provider
  instructions/icm.md           appended to the global AGENTS.md / CLAUDE.md
  skills/
    icm-architect/              upstream skill, vendored by manifest (see VENDOR.md)
    icm-run/                    executor skill for existing workspaces (written here)
vendor/                         only where a provider has a feature or gap
  claude/hooks/icm-detect.sh    SessionStart: detect workspace, inject one line
  claude/settings.fragment.json hook registration to merge into ~/.claude/settings.json
  codex/README.md               nothing extra; explains why
  omlx/README.md                unknown config model; explains what to verify
```

## Deploy mapping

| Source | Claude Code | Codex CLI | omlx |
|---|---|---|---|
| general/instructions/icm.md | ~/.claude/CLAUDE.md (append) | ~/.codex/AGENTS.md (append) | verify |
| general/skills/* | ~/.claude/skills/ | ~/.agents/skills/ (verify against installed version) | verify |
| vendor/claude/* | ~/.claude/hooks/, ~/.claude/settings.json | n/a | n/a |

## First-time steps

1. `bash general/skills/icm-architect/vendor.sh` to pull the upstream skill at the pinned commit.
2. Deploy with frontier as usual.
3. In any directory, say "build me a workspace for X" (icm-architect) or `cd` into a
   workspace and say `status` (icm-run).

## Sources

- Paper: https://arxiv.org/abs/2603.16021
- Protocol repo and 15 conventions: https://github.com/RinDig/Interpretable-Context-Methodology
- Builder skill: https://github.com/RinDig/icm-architect
