---
name: feynman
description: Use when the user asks how or why something works, asks to explain or understand a concept or a part of a codebase, or runs /feynman; recalls and updates the global concept graph instead of answering from scratch.
argument-hint: <concept or question>
---

# Feynman

Answer explanatory questions the Feynman way and leave a card behind in the concept
graph, so the next time the concept comes up, in any repo, the answer starts from what
is already known and from the gaps that are still open.

The graph is a directory of markdown cards. Every read and write goes through one
command. Use this literal form so the permission rule matches:

```
python3 ~/.claude/tools/concept-graph/cg.py <subcommand> ...
```

`cg` below means that command. Card schema and field rules: `references/card.md`.
Full-weight template: `references/protocol.md`.

## Two weights

| Trigger | Output | Persist |
|---|---|---|
| `/feynman <topic>` | full protocol from `references/protocol.md` | always |
| an ordinary explanatory question | lite form: simple explanation, analogy with its breaking point, open gaps, under about 150 words, then the direct answer if the question needs more | when the concept is new or the card changed |

## Steps

0. **Recall.** `cg recall <two or three key terms>`. A hit means refine that card, not
   restart; show its open gaps first. If a `memory:` block already appeared for this
   prompt, that is the same recall; do not run it again. For a repo-specific question
   run `cg check --scope here` first so a stale card is marked before it is reused.
1. **Explain** at the level a bright 12-year-old follows, under 120 words. One analogy,
   then one sentence on where the analogy breaks.
2. **Audit.** List every place the explanation went vague or leaned on a term you did
   not define. For each gap decide how it closes: read code, run something, cite a
   source, or ask the user. Any jargon left gets a one-line definition.
3. **Close** each gap by its method. Evidence classes, strongest first:
   `verified-in-code` (file, line, commit), `ran` (command and output), `source-cited`
   (URL or document), `reasoned`, `user-declared`. A question about a codebase closes
   gaps only with the first three; a gap you can only reason about stays open with a
   due date.
4. **Refine.** Rewrite the explanation with the gaps closed, write the 30-second pitch,
   rate your confidence 1 to 5 honestly.
5. **Persist.** New concept: `cg add <slug> --title ... --alias ... --explain ...
   --analogy ... --breaks ... --pitch ... --confidence N`. Existing: `cg write` for text,
   `cg set` for confidence. Then `cg gap <slug> add|close`, at least one `cg link` to a
   neighbour, and `cg anchor <slug> --path <file> --line N` for every claim about code.
   Scope is global by default; add `--scope here` when the concept is specific to this
   repo, `--local-only` when it means nothing outside it.

## Rules

- Never pretend. An unclosed gap written down is worth more than a confident guess.
- Shorter wins. The child-level bar is high; meet it, do not wave at it.
- Do not edit card files by hand; `cg` keeps the index and lexicon in step.
- Inside an ICM workspace (root `CONTEXT.md` plus a numbered `stages/` tree) do not
  fire on ordinary questions; an explicit `/feynman` still works and writes only to the
  concept store, never into the workspace.
- `cg grade <slug>` asks a model to grade the explanation blind. Run it only when the
  user asks for a grade; it costs a model call.

## Anti-triggers

- A request to change, write, or fix code. Do the work; use this skill only if the
  user also asks to understand something.
- A lookup with a one-line factual answer, or a question about this conversation.
- A prompt that already carries a `memory:` block answering it fully.

## Output (lite form)

```text
<concept>: <simple explanation>
Analogy: <analogy>. Breaks: <where>.
Open gaps: <none | list with due dates>
Card: <slug> (<new | refined>, confidence N/5, <evidence class>)
```
