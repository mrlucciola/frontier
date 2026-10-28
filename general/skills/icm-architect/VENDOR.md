# icm-architect (vendored)

Upstream: https://github.com/RinDig/icm-architect
License: MIT
Format: Agent Skills (SKILL.md entry, references/, assets/templates/, scripts/)

This folder is populated by `vendor.sh`, not committed by hand. Do not edit
vendored files; if a change is needed, carry it in `icm-run/references/`
and let the workspace's own files override.

## Pin

Set `ICM_ARCHITECT_COMMIT` in vendor.sh to a full SHA before first deploy.
Bump deliberately. Upstream is active (13 commits at vendoring time) and
its templates define stage numbering (`01_name`) that icm-run's detection
regex also accepts alongside `01-name`.

## What the skill provides

- Build mode: dialogue extraction -> form (Pipeline, Umbrella, Record library,
  Knowledge bundle, Context map, System map) -> scaffold -> contracts -> walk test
- Restructure mode: inventory -> classify (catalog/contract/factory/product/dead)
  -> reference-integrity check -> approval gate -> copy-verify-remove -> walk test
- scripts/: standard-library Python a workspace copies into `_tools/` (link check,
  graph, index generation, quote check). Permission configs need an allow rule
  for `python3 _tools/*.py` in each vendor's schema.

## Known skew between upstream sources

- Paper and icm-architect: `01_name`. CONVENTIONS.md and the LvlyBot gist: `01-name`.
  Follow what the generator emits.
- The gist ("Interpreted Context Methodology") is a bot-automation variant with
  in-memory handoff and no human gate. Its "What NOT to Load" table and per-stage
  "Completion" section are worth adopting; its handoff model is not.
