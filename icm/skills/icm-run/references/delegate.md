# Delegating within a stage

Paper §4.1: the orchestrating agent uses the workspace's own context files to fill sub-agent prompts. The folder structure is the delegation spec. Keep it that way.

## When

- The stage's Process has independent units (one script per section, one slide per beat, one issue per sub-agent).
- The contract or entry file says to.
- Not when the stage is one creative pass that needs a single voice. Splitting a 90-second script across three sub-agents produces three voices.

## What each sub-agent receives

Exactly:

1. `stages/<current>/CONTEXT.md` (or the subset of Process steps it owns, quoted verbatim)
2. The Inputs rows relevant to its unit, loaded at the stated Section/Scope
3. Its unit of work and the output path it must write to

Nothing else. No entry file, no root CONTEXT.md, no sibling outputs, no "here is the whole workspace for context". If a sub-agent needs a file not in the Inputs table, the contract is wrong; fix the contract later, do not widen the prompt now.

## What the orchestrator does

- Collects sub-agent outputs into the stage's `output/` (or merges them into the single artifact the Outputs table names).
- Runs the stage Audit over the merged result, not per sub-agent.
- Reports once, then stops at the gate like any other stage.

## Isolation for code-producing stages

If sub-agents write to a repo, the orchestrator creates one git worktree per sub-agent, hands each the path, and collects a diff or branch name back. Sub-agents never create or remove worktrees themselves, and no two edit the same tree.

## Vendor notes

How to spawn differs (Claude Code subagents and Agent Teams; Codex sub-agents; some runtimes have none). The vendor layer may add a note on mechanics. The rule above about what goes in the prompt does not change by vendor. If the runtime has no sub-agents, run the units sequentially yourself with the same per-unit context discipline.
