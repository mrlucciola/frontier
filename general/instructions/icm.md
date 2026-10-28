## ICM workspaces

A directory with a root `CONTEXT.md` and a `stages/NN-*/` or `stages/NN_*/` tree is an ICM workspace. Inside one:

- Treat `AGENTS.md` or `CLAUDE.md` at the root as the entry file, whichever exists, regardless of which agent you are.
- Read entry file, then root `CONTEXT.md`, then the current stage's `CONTEXT.md` only. Load exactly the files and sections its Inputs table names. Do not browse, do not read README files or other stages "for context".
- Write only to the current stage's `output/`. Never read other stages' `output/` to learn patterns; `references/` and `_config/` are the source of truth.
- After writing output, stop. A human reviews before the next stage runs. Do not chain stages unless the user says to.
- `status` and `setup` are workspace commands. The workspace's own entry file overrides anything here.
- To build or restructure a workspace use the `icm-architect` skill. To execute a stage use the `icm-run` skill.
