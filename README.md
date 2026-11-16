# frontier-clean

Self-contained components for agentic coding. Each component owns its behavior,
implementation, tests, and documentation.

## Behavioral contract

- **Independent use.** Each component must own its instructions, implementation,
  configuration, tests, and documentation. Components must remain independently
  usable. Optional integrations must use small, explicit interfaces.
- **Roles, not names.** Outside an interface file two components share, a
  component refers to another by the role it fills (the ticket store, the
  worktree tool), never by its name, and never restates its rules. The
  [role table](/AGENTS.md#roles) in the root `AGENTS.md` is the one place a role
  is bound to a tool, so replacing a tool is an edit there.
- **Thin global context.** Keep global instructions and skill descriptions limited
  to essential orientation and discovery. Load detailed guidance as it becomes
  relevant to the task.
- **Scoped instruction delivery.** Deliver instructions for the relevant component,
  workspace, operation, and session state. Surface outstanding obligations when
  the agent can act on them, including after long tasks or context compaction.
- **Output that teaches.** A component's own output carries the guidance for the
  next step. A refusal names what was refused and the command to run next, help is
  short enough to read whole, and a workspace the component has no state in gets
  no injected text.
- **One maintained source.** The checkout is the only copy. Deployment never
  copies component files: a deployed path is a symlink into the checkout or a
  marked block in a shared file. No release directories, version pointers,
  manifests, checksums, receipts, or install journals. Keep shared requirements in
  one source and isolate necessary provider differences.

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
| [swe-kb](/swe-kb/README.md) | Tabled: software design knowledge base, not used | [swe-kb maintenance](/swe-kb/AGENTS.md) |
| [Kiro](/kiro/README.md) | Kiro CLI 2.x provider adapter: gated deploy, paste transport, recon probe | [Kiro maintenance](/kiro/AGENTS.md) |
