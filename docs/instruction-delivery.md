# Instruction discovery and delivery

Keep the [global context thin](/README.md#behavioral-contract). Read this guide
when changing instruction placement, skill discovery, or hooks.

## Runtime guidance

Evaluate supported hooks for detecting workspace markers, tool operations, and
session lifecycle events. Choose triggers using observed usage patterns and
common action sequences. Keep detection inexpensive and avoid redundant injection
while guidance remains available in context.

The following examples illustrate possible triggers and the guidance they deliver.

| Situation | Targeted guidance |
| --- | --- |
| First prompt in a workspace containing `.icm/` | Essential ICM orientation and where to find task-specific instructions. |
| A ticket claim through the ticket store | Guidance needed to claim the ticket and establish session ownership. |
| Session completion with an outstanding ticket claim | Guidance to close, park, or release that session's ticket. |

Workspace markers establish relevance. Operations and current state determine
which instructions are actionable. Base completion reminders on actual outstanding
obligations. Document each provider's supported triggers and limitations.

## Development guidance

- Keep repository-wide behavior in the root contribution contract and routing in
  the root `AGENTS.md`.
- Put component maintenance instructions, validation commands, and task routes in
  that component's `AGENTS.md`. Introduce deeper instructions when a subtree has
  distinct requirements.
- Keep agent task procedures in the owning skill and link operation-specific
  references from its command or trigger table.
- Put operator setup in the component guide and detailed design and reference
  material in component `docs/`. Link to the owning document instead of repeating
  its content.
- Give each route a concrete reason to read its target. Load the relevant section
  and follow further references as the task requires.

Repository maintenance instructions and runtime skill procedures have different
entry points. Keep each discoverable from the file an agent uses for that work.

For a proposed optional zsh retrieval helper and its quality and cost evaluation,
see the [progressive discovery proposal](/docs/progressive-discovery-proposal.md).
It is a design proposal, not an installed component or a runtime requirement.
