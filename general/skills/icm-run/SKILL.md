---
name: icm-run
description: Execute one stage of an existing ICM (Interpretable Context Methodology) workspace, report pipeline status, or run its setup questionnaire. Use when the current directory has a root CONTEXT.md and a stages/NN-*/ tree and the user says "status", "setup", "run stage N", "next stage", "continue the pipeline", or names a stage folder. Not for building or restructuring a workspace; that is icm-architect.
---

# ICM Run

Execute a stage of an ICM workspace the way the paper specifies: one agent, the right files at the right moment, output as a plain file a human edits before anything else runs. This skill is the floor. If the workspace's own entry file or stage contract says something stricter or different, the workspace wins.

Method: Van Clief & McDermott, arXiv:2603.16021. Conventions: `_core/CONVENTIONS.md` in RinDig/Interpretable-Context-Methodology.

## Commands

| User says | Do | Detail |
|---|---|---|
| `status` | Scan `stages/*/output/`, render the pipeline diagram, name the next pending stage | [references/status.md](references/status.md) |
| `setup` | Run `setup/questionnaire.md` once, fill placeholders, verify none remain | [references/setup.md](references/setup.md) |
| run / next / stage name | Execute exactly one stage, then stop | [references/walk.md](references/walk.md) |

If the user gives a topic with no command, that is the entry stage's per-run input. Run `status` silently first; if stage 01 output already exists, ask whether this is a new run before overwriting.

## Executing a stage (summary; walk.md is authoritative)

1. Read entry file (`AGENTS.md` or `CLAUDE.md`), root `CONTEXT.md`, then only `stages/<current>/CONTEXT.md`.
2. Load exactly what the Inputs table lists, at the Section/Scope it names. Reference rows (Layer 3) are constraints to internalize. Working rows (Layer 4) are input to transform. Nothing else gets read.
3. If the contract has a Checkpoints table, stop at each one and let the human steer.
4. Follow Process steps in order. Do not reorder or merge them.
5. If the contract has a Verify section, cross-check the named earlier output against its criteria and list discrepancies before the audit.
6. If the contract has an Audit table, run every check. Any failure: revise, do not write.
7. Write to `stages/<current>/output/` using `[topic-slug]-[artifact].md` unless the Outputs table says otherwise.
8. Stop. Say what landed where and that the human should review before the next stage. Do not start the next stage.

## Hard rules

- Never read another stage's `output/` unless the current Inputs table lists it. Early outputs are the worst outputs; references are the source of truth (Pattern 14).
- Never edit `references/`, `_config/`, or any `CONTEXT.md` during a run. If the contract looks wrong, say so and stop; fixing the factory is a separate decision the human makes (paper §6.3).
- Never hand-edit generated indexes; they are rebuilt by scripts in `_tools/`.
- Token check before acting: entry + root context + stage contract + inputs should land near 2k to 8k tokens. If it is far above, the Inputs table is too broad; report it rather than silently loading everything.
- Delegation: if your runtime supports sub-agents and the stage benefits, each sub-agent gets the stage contract plus its listed inputs and nothing more. See [references/delegate.md](references/delegate.md).

## Contract sections this skill honors

Inputs, Process, Outputs (required, Pattern 1). Checkpoints (Pattern 11). Audit (Pattern 12). Optional extensions a workspace may include: Verify, Completion, What NOT to Load. See [references/contract-extensions.md](references/contract-extensions.md).
