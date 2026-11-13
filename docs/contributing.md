# Contribution standards

Read the [behavioral contract](../README.md#behavioral-contract) for shared
requirements. These conventions guide component development. Component guides
describe their current implementation and supported setup.

## Repository and component structure

Each top-level directory represents a capability or component, except `docs/` and
directories beginning with `.`. Root documentation provides navigation and shared
contribution standards. Each component owns its detailed documentation.

Use the following layout as applicable. Create directories for the files the
component needs.

```text
<component>/
  AGENTS.md           Maintenance instructions and task-specific routes
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
