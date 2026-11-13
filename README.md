# frontier-clean

Self-contained components for agentic coding. Each component owns its behavior,
implementation, tests, and documentation.

## Behavioral contract

- **Independent use.** Each component must own its instructions, implementation,
  configuration, tests, and documentation. Components must remain independently
  usable. Optional integrations must use small, explicit interfaces.
- **Thin global context.** Keep global instructions and skill descriptions limited
  to essential orientation and discovery. Load detailed guidance as it becomes
  relevant to the task.
- **Scoped instruction delivery.** Deliver instructions for the relevant component,
  workspace, operation, and session state. Surface outstanding obligations when
  the agent can act on them, including after long tasks or context compaction.
- **One maintained source.** Keep executable files in their owning component.
  Provider integration should reference those files directly or through symlinks.
  Keep shared requirements in one source and isolate necessary provider differences.

## Contributing

Use the guide relevant to your change.

| Work | Guide |
| --- | --- |
| Component structure, provider integration, setup, and validation | [Contribution standards](/docs/contributing.md) |
| Scoped instructions, discovery, and lifecycle hooks | [Instruction delivery](/docs/instruction-delivery.md) |
| Agent development workflow | [Agent instructions](/AGENTS.md) |

## Components

| Component | Purpose | Development instructions |
| --- | --- | --- |
| [ICM](/icm/README.md) | Workspace methodology and staged work | [ICM maintenance](/icm/AGENTS.md) |
| [Feynman](/feynman/README.md) | Explanations, concept cards, and recall | [Feynman maintenance](/feynman/AGENTS.md) |
| [Quiz](/quiz/README.md) | Adaptive questions and learning progress | [Quiz maintenance](/quiz/AGENTS.md) |
| [Session telemetry](/session-telemetry/README.md) | Fresh Codex usage and timing observations | [Telemetry maintenance](/session-telemetry/AGENTS.md) |
| [CWF](/cwf/README.md) | Contextual discovery, task continuity, and coordinated work | [CWF maintenance](/cwf/AGENTS.md) |
| [pm](/pm/README.md) | Ticket store for agent work | [pm maintenance](/pm/AGENTS.md) |
| [wt](/wt/README.md) | Worktree lifecycle for ticketed work | [wt maintenance](/wt/AGENTS.md) |
