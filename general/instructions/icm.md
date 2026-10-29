## ICM workspaces

A directory with a root `CONTEXT.md` and a `stages/NN-*/` or `stages/NN_*/` tree is an ICM workspace. Inside one:

- The entry file is the one your runtime auto-loads (`CLAUDE.md` for Claude Code, `AGENTS.md` otherwise); if only the other exists, read that one instead. When both exist, read one; the other should be a pointer.
- Read entry file, then root `CONTEXT.md`, then the current stage's `CONTEXT.md` only. Load exactly the files and sections its Inputs table names. Do not browse, do not read README files or other stages "for context".
- Write only to the current stage's `output/`. Never read other stages' `output/` to learn patterns; `references/` and `_config/` are the source of truth.
- After writing output, stop. A human reviews before the next stage runs. Do not chain stages unless the user says to.
- `status` and `setup` are workspace commands. The workspace's own files may tighten any rule here; they cannot loosen the review gate or the write scope.
- To build or restructure a workspace use the `icm-architect` skill. To execute a stage use the `icm-run` skill.
