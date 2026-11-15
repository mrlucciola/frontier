# Walking a stage

The five-layer load order. Stop reading as soon as you have what the stage needs.

| Layer | File | Question | Budget |
|---|---|---|---|
| 0 | `AGENTS.md` (a `CLAUDE.md` is only a pointer to it) | Where am I, where does everything live | ~800 tok |
| 1 | root `CONTEXT.md` | Which stage handles this task | ~300 tok |
| 2 | `stages/<current>/CONTEXT.md` | What exactly do I do | 200 to 500 tok |
| 3 | rows the Inputs table marks reference | What rules apply (internalize) | 500 to 2k tok |
| 4 | rows the Inputs table marks working | What am I transforming (process) | varies |

## Determining the current stage

1. Run `scripts/state.py`. The current stage is the earliest one that is not accepted, and only it can show `may_run`.
2. A stage the user names runs only if it is that stage. If it is a later one, report what blocks it.
3. If every stage is accepted, report that and ask whether to start a new run or re-run a stage.

Re-running a stage is normal (incremental recompilation, paper section 6.1). Re-running stage N does not touch stage N-1 or any other stage's output or `check.md`. Say which existing output files will be overwritten before overwriting. A re-run leaves the stage pending until it is checked again, and state.py shows later stages that used the old output as stale.

## Reading the Inputs table

Upstream shape (Pattern 1 and 4):

```
| Source | File/Location | Section/Scope | Why |
```

- Paths are relative to the stage folder. `../01-research/output/` means the previous stage's output.
- Section/Scope is binding. "Voice Rules through What the Voice Is NOT" means load those headings and nothing else from that file. "Full file" means the whole file.
- A row pointing at a `SKILL.md` means: read the index, then load only the rule files the stage needs.
- A row pointing at a folder means every file directly in it, not recursively, unless stated.
- If a listed file does not exist, stop and report it. Do not substitute a similar file.

## Checkpoints

```
| After Step | Agent Presents | Human Decides |
```

Complete the step, present exactly what the table says, wait. Do not pre-empt the human's choice by continuing with a default.

## Audit

```
| Check | Pass Condition |
```

Run every row after the process completes and before writing. Report each as pass or fail with one line of evidence. On any fail, revise and re-audit. Write only on all-pass. Passing the Audit is your own verification, not the stage's check.

## Writing output

- Location: the Outputs table. Default `stages/<current>/output/`.
- Name: `[topic-slug]-[artifact-type].md` unless the Outputs table gives a name.
- A short metadata header (topic, stage, date, inputs consumed by path) makes later tracing cheap and costs a few lines. Add it unless the Outputs table specifies a format that forbids it.
- Then stop. One stage per invocation. The edit surface is the point.

## Status after writing

Run the stage's check if it is a script, or hand it to its model reviewer (SKILL.md, "The check"). Then run state.py again and report in this shape:

```
Wrote: stages/02-script/output/hello-world-script.md
Check: 02-script pending (human check). Review the file above; 03-production waits for your verdict.
```
