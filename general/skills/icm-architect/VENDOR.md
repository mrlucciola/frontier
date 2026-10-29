# icm-architect (vendored)

Upstream: https://github.com/RinDig/icm-architect
License: MIT
Format: Agent Skills (SKILL.md entry, references/, assets/templates/, scripts/)

The vendored tree is committed to this repo at the commit named in `VENDOR.lock`,
so a fresh clone deploys without network. `vendor.sh` is the only thing that writes
it: pull, replace, lock. Do not edit vendored files; if a change is needed, carry it
in `icm-run/references/` and let the workspace's own files override.

## Pin and bump

`PIN` in `vendor.sh` holds the full SHA. First pull: `ICM_ARCHITECT_COMMIT=main bash
vendor.sh`, paste the printed SHA into `PIN`, commit the tree, the lock, and the script
together. Bump the same way, deliberately. Upstream is active and its templates define
stage numbering (`01_name`) that icm-run's detection also accepts alongside `01-name`.

## What the skill provides

- Build mode: dialogue extraction -> form (Pipeline, Umbrella, Record library,
  Knowledge bundle, Context map, System map) -> scaffold -> contracts -> walk test
- Restructure mode: inventory -> classify (catalog/contract/factory/product/dead)
  -> reference-integrity check -> approval gate -> copy-verify-remove -> walk test
- scripts/: standard-library Python a workspace copies into `_tools/` (link check,
  graph, index generation, quote check). The permission rule they need is in the
  top-level README.

## Known skew between upstream sources

- Paper and icm-architect: `01_name`. CONVENTIONS.md and the LvlyBot gist: `01-name`.
  Follow what the generator emits.
- The gist ("Interpreted Context Methodology") is a bot-automation variant with
  in-memory handoff and no human gate. Its "What NOT to Load" table and per-stage
  "Completion" section are worth adopting; its handoff model is not.
