---
name: icm-run
description: Only inside an ICM workspace (root CONTEXT.md plus stages/NN-name folders) - report its status, run or continue its next stage, record an approval or rejection of a stage, run setup. Not for other repositories or for building one (icm-architect).
---

# ICM Run

One stage per invocation, loading only the files its contract names, writing plain files, and stopping at the stage's check. A workspace's own files may make these rules stricter; they cannot loosen the check or the write scope.

Method: Van Clief & McDermott, arXiv:2603.16021. Scripts and detail files are in this skill's directory: `scripts/`, `references/`.

## Start with the state

Run `python3 <this skill's directory>/scripts/state.py <dir>`, where `<dir>` is the workspace root or a folder inside one stage. It is read-only. It prints each stage's state, whether the entry file is sound, and the one next action.

- Exit 1, "not an ICM workspace": stop using this skill and handle the request as ordinary work.
- `next: stop: entry ...`: report it and propose making `AGENTS.md` the entry with one-line pointers (`CLAUDE.md` holding `@AGENTS.md`). Change nothing.
- States: `unproduced` (required output absent, empty or partial), `pending` (output exists, no current verdict), `rejected`, `accepted` (verdict bound to the current outputs, inputs and contract), `stale` (a file changed after the verdict), `blocked`.

A file being present never means accepted. Neither does a closed ticket, an earlier conversation, or your own Audit.

## Commands

| Request | Do | May write |
|---|---|---|
| `status` | Run state.py and report its output | nothing |
| run, next, a stage name, or a topic for the entry stage | Run the stage state.py marks `may_run`. Naming a later stage does not skip an earlier one. Procedure: `references/walk.md` | that stage's declared outputs under its `output/` |
| the user approves or rejects a stage | Record it, as in "The check" below | that stage's `output/check.md` |
| `setup` | `references/setup.md` | only the files it lists to the user first |

Building, restructuring or fixing a contract is `icm-architect`, and only when the owner asks for it.

## The check

The stage's `## Check` section names the reviewer. When it names none, the reviewer is a person.

- **Human.** After writing, stop and report that the stage is waiting for review. Record only a verdict the person actually gave for these files: `python3 <skill dir>/scripts/record.py <root> <stage> --reviewer human --by <name> --decision pass|fail --reason "<why>"`. "continue", "next", a chaining request or your Audit is not a verdict. Ask for one.
- **Script** (`Reviewer: script <command>`): `record.py <root> <stage> --reviewer script` runs the command and records its result.
- **Model** (`Reviewer: model <reviewer>`): give that reviewer, as a separate subagent and never yourself, the outputs, the contract's criteria and its inputs. Record its verdict with `--reviewer model --by <reviewer>`. No usable verdict means the stage stays pending.

record.py refuses a reviewer kind the contract does not declare. Do not work around a refusal. After a stage is accepted, the next one runs on a new request, or within a chain the user stated by naming the stages or an end point. A chain never stands in for a human check that has not happened. A rejection, missing evidence or a refusal ends the chain.

## Loading and writing

- Read `AGENTS.md`, then the root `CONTEXT.md`, then the current stage's `CONTEXT.md`, then exactly the Inputs rows at their stated scope. Skip a file your runtime already loaded. Read no README, no other stage, and no other stage's output unless an Inputs or Verify row names it. A missing input stops the run.
- Write only the stage's declared outputs under its `output/`, and `check.md` only through record.py. Never edit a `CONTEXT.md`, `references/`, `_shared/`, `_config/` or a generated index during a run. If the contract looks wrong, say so and stop. Before re-running a stage, name the outputs it will replace.
- A stage that writes outside `output/`, such as code in a repository, needs an exception in its contract naming the files, the writer, the reason, the check and when it expires. Without one, stop. Symlinks and `..` paths do not widen the scope.
- ICM never changes a ticket's status, claim or dependencies.
- The entry file, root context, stage contract and inputs should total roughly 2k to 8k tokens. If they come to far more, report that the Inputs table is too broad instead of loading everything.
- Delegate only when the stage benefits and your instructions allow it: `references/delegate.md`.

## Contract sections this skill honors

Inputs, Process, Outputs, Check, Checkpoints and Audit. A workspace may add Verify, Completion and What NOT to Load: `references/contract-extensions.md`.
