# frontier-clean

Self-contained components for agentic coding. This guide defines contribution
standards and intended behavior. Component documentation describes supported
providers, current behavior, and setup.

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

## Instruction discovery and delivery

Evaluate supported hooks for detecting workspace markers, tool operations, and
session lifecycle events. Choose triggers using observed usage patterns and
common action sequences. Keep detection inexpensive and avoid redundant injection
while guidance remains available in context.

The following examples illustrate possible triggers and the guidance they deliver.

| Situation | Targeted guidance |
| --- | --- |
| First prompt in a workspace containing `.icm/` | Essential ICM orientation and where to find task-specific instructions. |
| A ticket claim operation, such as `pm ticket claim` | Guidance needed to claim the ticket and establish session ownership. |
| Session completion with an outstanding ticket claim | Guidance to close, park, or release that session's ticket. |

Workspace markers establish relevance. Operations and current state determine
which instructions are actionable. Base completion reminders on actual outstanding
obligations. Document each provider's supported triggers and limitations.

## Repository and component structure

Each top-level directory represents a capability or component, except `docs/` and
directories beginning with `.`. Root documentation provides navigation and shared
contribution standards. Each component owns its detailed documentation.

Use the following layout as applicable. Create directories for the files the
component needs.

```text
<component>/
  README.md           Purpose, supported providers, and documentation links
  INSTALL.md          Setup, first use, verification, disabling, and removal
  instructions/       Agent instructions
  skills/<name>/      Discoverable skills and their supporting files
  hooks/              Event hooks
  cli/                User-facing executables
  tools/              Internal runtime tools and helpers
  config/             Provider configuration fragments
  tests/              Component tests
  docs/               Detailed design and reference documentation
```

Organize source files consistently with their role in agent environments. Document
exact provider destinations, such as paths under `~/.claude/`, `~/.codex/`, or
`~/.config/opencode/`, in the component's setup guide.

## Setup and integration standards

- Symlink skills into the provider's supported discovery location.
- Expose command-line executables through symlinks in `~/.local/bin` when needed.
- Run hooks from their component directory wherever supported. Add provider-side
  symlinks only where the provider requires files at a particular location.
- Document the minimal configuration needed to register hooks, expose skills, and
  load instructions. Preserve unrelated user configuration during setup and removal.
- Keep shared component state in a provider-independent location where practical,
  such as `~/.local/state/concepts/`. Document current paths and any migration steps.
- Begin with clear operator instructions. Add small setup scripts when actual use
  demonstrates repetitive work worth automating.

## Documentation and validation

Write component setup guides as concise walkthroughs with enough explanation to
understand each step. Include prerequisites, copyable commands, expected results,
and instructions for disabling and removing the integration. Explain how removal
affects user data.

Keep component tests local and runnable with Python's standard library. Document
the relevant validation commands in the component guide and update instructions
when behavior or setup changes. Measure context and hook overhead before making
performance claims.

## Components

| Component | Purpose |
| --- | --- |
| [ICM](icm/) | Workspace methodology and staged work. |
| [Feynman](feynman/) | Explanations, concept cards, and relevant recall. |
| [Quiz](quiz/) | Adaptive questions and recorded learning progress. |
| [Session telemetry](session-telemetry/README.md) | Usage and timing observations for authorized fresh Codex sessions. |
