# frontier-clean workspace

This checkout is a frontier-clean workspace: self-contained agentic-coding
components. The instruction tree is `AGENTS.md`: read the root `AGENTS.md`
first, then the owning component's `AGENTS.md`; the root file routes to each
component.

Kiro integration in this workspace is version-pinned to Kiro CLI 2.x. Agents
here are JSON-only configs. Do not use Kiro 3.x surfaces (markdown agents,
`permissions.yaml`, standalone hook JSON, PascalCase triggers). If
`kiro-cli --version` reports 3 or later, stop and say so.

The durable plan is `kiro/docs/plan.md`; run `kiro-probe` for a machine
report.
