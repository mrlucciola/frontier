# Delegating within a stage

Paper §4.1: the orchestrating agent uses the workspace's own context files to fill sub-agent prompts. The folder structure is the delegation spec. Keep it that way.

ICM never requires delegation. A stage done sequentially by one agent is always valid.

## When

- Your instructions and the task allow sub-agents, and
- the stage's Process has independent units (one script per section, one slide per beat, one issue per sub-agent), or the contract or entry file says to.
- Not when the stage is one creative pass that needs a single voice. Splitting a 90-second script across three sub-agents produces three voices.

## What each sub-agent receives

1. `stages/<current>/CONTEXT.md`, or the Process steps its unit owns, quoted verbatim
2. The Inputs rows relevant to its unit, loaded at the stated Section/Scope
3. Its unit of work and the one output path it must write to; no two units share a path

Add no workspace material beyond that: no entry file, no root CONTEXT.md, no sibling outputs, no "here is the whole workspace for context". The runtime's own standing instructions still apply to the sub-agent. If a sub-agent needs a file not in the Inputs table, the contract is wrong. Report that, and do not widen the prompt.

## What the orchestrator does

- Collects sub-agent outputs into the stage's `output/`, or merges them into the single artifact the Outputs table names.
- Runs the stage Audit over the merged result, not per sub-agent.
- Runs or requests the stage's check once, then stops like any other stage.

Sub-agents do not record verdicts, run another stage, edit contracts or change tickets, and none reviews its own work.

## Code-producing stages

When units write to a repository, follow that repository's own checkout rules (its worktree tool, if it has one). ICM adds none. Writes outside `output/` still need the stage's contract exception (SKILL.md, "Loading and writing").

## Vendor notes

How to spawn differs: Claude Code subagents; OpenCode's `task` tool with a subagent; Codex sub-agents; some runtimes have none. The rule about what goes in the prompt does not change by vendor. If the runtime has no sub-agents, run the units sequentially yourself with the same per-unit context discipline.
