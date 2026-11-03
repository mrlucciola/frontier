---
name: icm-run
description: Execute one stage of an existing ICM (Interpretable Context Methodology) workspace, report pipeline status, or run its setup questionnaire. Use when the current directory has a root CONTEXT.md and a stages/NN-*/ tree and the user says "status", "setup", "run stage N", "next stage", "continue the pipeline", or names a stage folder. Not for building or restructuring a workspace; that is icm-architect.
---

# ICM Run

Execute a stage of an ICM workspace the way the paper specifies: one agent, the right files at the right moment, output as a plain file a human edits before anything else runs. This skill is the floor. A workspace's entry file or stage contract may make it stricter; it cannot loosen the review gate or the write scope.

Method: Van Clief & McDermott, arXiv:2603.16021. Conventions: `_core/CONVENTIONS.md` in RinDig/Interpretable-Context-Methodology. The always-loaded ICM instruction gives the load order, write scope, and gate; this skill adds the mechanics. Detail files are under this skill's `references/`.

## Commands

| User says | Do | Detail |
|---|---|---|
| `status` | Scan `stages/*/output/`, render the pipeline diagram, name the next pending stage | `references/status.md` |
| `setup` | Run `setup/questionnaire.md` once, fill placeholders, verify none remain | `references/setup.md` |
| run / next / stage name | Execute exactly one stage, then stop | `references/walk.md` |

If the user gives a topic with no command, that is the entry stage's per-run input. Run `status` silently first; if stage 01 output already exists, ask whether this is a new run before overwriting.

## Executing a stage

`references/walk.md` is the procedure: load order, how to read the Inputs table, Checkpoints, Audit, output naming, the closing report. In one line: load exactly what the contract lists, follow Process in order, pass every Audit row, write to `stages/<current>/output/`, stop.

## Rules beyond the instruction

- Never edit `references/`, `_config/`, or any `CONTEXT.md` during a run. If the contract looks wrong, say so and stop; fixing the factory is a separate decision the human makes (paper §6.3).
- Never hand-edit generated indexes; they are rebuilt by scripts in `_tools/`.
- Token check before acting: entry + root context + stage contract + inputs should land near 2k to 8k tokens. If it is far above, the Inputs table is too broad; report it rather than silently loading everything.
- Delegation: if your runtime supports sub-agents and the stage benefits, each sub-agent gets the stage contract plus its listed inputs and nothing more. See `references/delegate.md`.

## Contract sections this skill honors

Inputs, Process, Outputs (required, Pattern 1). Checkpoints (Pattern 11). Audit (Pattern 12). Optional extensions a workspace may include: Verify, Completion, What NOT to Load. See `references/contract-extensions.md`.
