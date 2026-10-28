# Walking a stage

The five-layer load order. Stop reading as soon as you have what the stage needs.

| Layer | File | Question | Budget |
|---|---|---|---|
| 0 | `AGENTS.md` / `CLAUDE.md` | Where am I, where does everything live | ~800 tok |
| 1 | root `CONTEXT.md` | Which stage handles this task | ~300 tok |
| 2 | `stages/<current>/CONTEXT.md` | What exactly do I do | 200 to 500 tok |
| 3 | rows the Inputs table marks reference | What rules apply (internalize) | 500 to 2k tok |
| 4 | rows the Inputs table marks working | What am I transforming (process) | varies |

## Determining the current stage

1. If the user named a stage, that is it.
2. Otherwise run the status scan: the first stage whose `output/` is empty (or `.gitkeep` only) is current.
3. If every stage has output, report the pipeline complete and ask whether to start a new run or re-run a stage.

Re-running a stage is normal (incremental recompilation, paper §6.1). Re-running stage N does not touch stage N-1. Say which existing output files will be overwritten before overwriting.

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

Run every row after the process completes and before writing. Report each as pass or fail with one line of evidence. On any fail, revise and re-audit. Write only on all-pass.

## Writing output

- Location: the Outputs table. Default `stages/<current>/output/`.
- Name: `[topic-slug]-[artifact-type].md` unless the Outputs table gives a name.
- A short metadata header (topic, stage, date, inputs consumed by path) makes later tracing cheap and costs a few lines. Add it unless the Outputs table specifies a format that forbids it.
- Then stop. One stage per invocation. The edit surface is the point.

## Status after writing

Report in this shape:

```
Wrote: stages/02-script/output/hello-world-script.md
Next:  03-production (pending). Review the file above before running it.
```
