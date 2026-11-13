# Agent instructions

Follow the [behavioral contract](/README.md#behavioral-contract). For component work,
identify its owner through the [component index](/README.md#components), then read
that component's `AGENTS.md`. For shared documentation, use the task routes below.
Read supporting documents for the operation at hand. Link targets beginning with `/`
are relative to the repository root, which is the worktree root inside a worktree;
put the checkout path in front before opening one.

| Work | Read when relevant |
| --- | --- |
| Component structure, setup, or documentation | [Contribution standards](/docs/contributing.md) |
| Instruction placement, skills, hooks, or context loading | [Instruction delivery](/docs/instruction-delivery.md) |
| Component implementation or tests | The component's `AGENTS.md` and its task-specific routes |
| Ticketed work | The ticket body, notes, and applicable workstream contract through `pm ticket` |

Preserve other contributors' work and stay within the requested scope. Run the
relevant component checks and update documentation affected by the change. After
changing a `README.md`, `AGENTS.md`, `CLAUDE.md`, `INSTALL.md`, a `docs/` page, or
a top-level directory, run `python3 -B docs/check_structure.py` from the
repository root.
Report validation and outstanding work at handoff. For ticketed work, persist
findings and remaining steps in ticket notes.
