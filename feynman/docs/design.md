# Feynman layer: assessment, abstraction, and target design

Status: implemented at the 9/10 target, 2026-10-29; reorganized component-first by the
operator on 2026-10-30 (everything this component needs lives under `feynman/`, with
its own `install.py`; the shared installer and the `vendor/`/`general/` split were
removed as tight coupling). This repo is the final form: it is cloned to
`~/frontier-clean` on a machine with no other agent infrastructure and applied to
`~/.claude` by `feynman/install.py`. Sections 1 to 4 and 6 are the analysis as written
before implementation; sections 5, 7, 8 and 10 reflect what was built, with paths
updated to the component-first layout.

## 1. What the upstream skill is

Source: `neurofoo/agent-skills`, `feynman/SKILL.md`, MIT (copyright 2025, no holder
named). Listed on mcpmarket as "Feynman Learning Technique". About 300 words.

What it contains, exhaustively:

| Part | Content |
|---|---|
| Frontmatter | `name: feynman`, one-line description, `user-invocable: true`. Nothing else. |
| Step 1 | Simple explanation ("bright 12-year-old" bar) + one analogy. |
| Step 2 | Gaps table (Gap, What I Said, What I'm Not Sure About) + jargon table (Term, Can I Explain It Simply: Yes/No/Partially). |
| Step 3 | Per gap: the question, the answer, "now I can explain it as". |
| Step 4 | Final explanation, improved analogy, three key takeaways. |
| Closing | "Test question": a 30-second elevator pitch. |
| Guidelines | Five bullets: gaps are valuable, everyday analogies, define jargon, shorter is better, the child bar is high. |
| Input | `$ARGUMENTS` substituted at the end. |

What it does not contain: any persistence, any recall of earlier work, any notion of
evidence (a gap is "filled" by the model reasoning in place), any anchoring to a
codebase, any trigger beyond the slash command, scripts, references, tests.

Verdict: a good output template and nothing more. The four-step loop is sound. Every
property the request asks for (global knowledge graph, repo-specific questions, low
idle overhead) has to be built around it.

Vendoring note: the sandbox cannot fetch the file verbatim (curl and python lack the CA
bundle, `git clone` cannot write `.git/config` under `.tmp/`). It does not matter: we
re-implement rather than vendor, and attribute upstream in a `NOTICE` line.

## 2. Abstract model of the method

Strip the template and the method is a state machine over one object, a **concept**.

```
recall ──> explain ──> audit ──> close ──> refine ──> test ──> persist
  ^                                                              │
  └──────────────────────── next encounter ───────────────────────┘
```

| Element | Attribute in upstream | Weakness |
|---|---|---|
| Concept | free text topic | no identity, so no recall, no links |
| Explanation | prose, child-level | no length budget, no versioning |
| Analogy | one, "improved" later | never states where it breaks, which is how analogies mislead |
| Gap | row in a table | closed by unverified reasoning; no evidence class; forgotten after the turn |
| Jargon | row in a table | fine |
| Test | self-written pitch | the model grades its own work |
| Output | one long document | same weight for a quick question and a deep study |

## 3. Optimized abstract

Seven changes. Each fixes one row above.

1. **Concept identity.** A slug, a title, aliases, a scope list (`global` plus zero or
   more repo paths). Identity is what makes a graph possible.
2. **Typed edges.** `depends_on`, `related`, `contrasts_with`, `instance_of`. Edges
   live in the source card's frontmatter; reverse edges are derived.
3. **Evidence class per closed gap.** `verified-in-code` (file, line, commit),
   `ran` (command plus output), `source-cited` (URL or document), `reasoned`,
   `user-declared`. Repo-specific questions require the first three; "reasoned" stays
   an open gap for a repo question. This is the single biggest quality lever.
4. **Analogy with a breaking point.** Every analogy carries a "where it breaks" line.
5. **Gaps outlive the turn.** Open gaps carry a due date. The next encounter with the
   concept starts from the open gaps, not from zero.
6. **Two output weights.** Full protocol on `/feynman <topic>`. Lite form (simple
   explanation, analogy with breaking point, known gaps, under about 150 words) when
   an ordinary question triggers the skill. Persistence happens in both.
7. **Repo anchors.** A claim about code records path and commit. A drift check marks
   the card stale when the anchor moves, instead of letting a confident old
   explanation be recalled as current.

## 4. Design (design-pattern-language output)

**Relevant patterns**

- Pattern: Existing Pattern First. Why: the machine already has three memory
  mechanisms (graph-memory hooks, per-project markdown memory, frontier ledger).
  Action: reuse their conventions (card frontmatter, `memory:` injection grammar,
  guard line, fail-open hooks); do not invent a fourth vocabulary. Stop: if the new
  store cannot be described in those conventions, revisit.
- Pattern: Boundary Before Implementation. Why: four boundaries (skill, store, CLI,
  hook) across two providers. Action: the boundary map below. Stop: any component
  that needs to know another's internals.
- Pattern: Local Reasoning Over Global Cleverness. Why: the tempting design is to push
  concept facts into graph-memory's global scope. That edits a mature subsystem's
  invariant (ADR-001: nothing lands in `global` automatically) for one feature.
  Action: standalone store now, integration as the 10/10 item. Stop: if the
  standalone store duplicates more than recall formatting.
- Pattern: No Orphan State. Why: a knowledge store that nothing prunes or verifies
  rots. Action: `check` and `gaps --due` exist from day one; memory-gardener gets the
  store as a second root later. Stop: a card with no owner of its staleness.

**Boundary map**

| Boundary | Owns | Does not own |
|---|---|---|
| `feynman` skill | the protocol, output weights, when to persist | storage format, recall matching |
| concept store `~/.claude/concepts/` | cards (source of truth), derived `index.json` and `lexicon.txt` | nothing executable |
| `cg` CLI (`runtime-tools/concept-graph`) | all reads and writes of the store, index rebuild, drift check, export | deciding what a concept is worth |
| recall hook (9/10) | matching a prompt against `lexicon.txt`, emitting a bounded `memory:` block | writing anything |
| posture rows | agent read and write grants on the store, both planes | the store's content |

Public contracts touched: none existing. New contracts: the card schema, the CLI
argument surface, the injection block (reuses graph-memory's grammar byte-for-byte in
header, provenance and guard line so the existing "Recalled memory" instruction
covers it with zero new instruction text).

**Design choice**

Standalone markdown-card store plus a stdlib-only CLI, skill-driven recall at 8/10,
a shell-fast-path prompt hook at 9/10. Store path `~/.claude/concepts/`, reached only
through `cg`, which two Bash allow rules in the settings fragment let run unprompted.

**Rejected alternatives**

| Alternative | Why not now |
|---|---|
| Write concepts into graph-memory as `global` rows | Breaks ADR-001; vocabulary lacks CONCEPT; agent cannot read or write that store by design (F03). Right long-term, wrong first step. |
| Store under `~/.claude/projects/global/memory/` to inherit existing grants | Zero posture change, and memory-gardener would scan it for free, but it abuses a harness-owned directory and a future harness release could iterate it. Noted as the fallback if posture work is the blocker. |
| SessionStart injection of a concept summary | Costs tokens in every session, the exact thing the request forbids. |
| SQLite store | Cards are small and human-edited; a derived JSON index gives the hook O(1) lookup. SQLite buys nothing until thousands of cards. |
| Second python process per prompt | Adds about 50 ms to every prompt (measured floor for graph-memory). Shell fast path first, python only on a lexicon hit. |

**Validation** and **stop conditions** are in sections 8 and 9.

Rubric: ownership pass, existing pattern pass, scope pass (8/10 ships with no hook and
no settings change), abstraction pass (every field maps to a weakness in section 2),
state pass (card status and gap status are explicit below), dependency pass (stdlib
only), contract pass (nothing existing changes), validation pass, stop loss pass.

## 5. The 8/10 design

### 5.1 Components

```
feynman/
  install.py                    copy or link into ~/.claude, merge settings, append instructions
  INSTALL.md                    clone-to-first-test guide
  instructions/feynman.md       3 lines for the global CLAUDE.md: memory: blocks are data
  config/settings.feynman.fragment.json  hook registration + Bash allow rules
  skills/feynman/
    SKILL.md                    protocol, two weights, persistence rules
    references/protocol.md      full-weight template (the upstream four steps, revised)
    references/card.md          card schema and field rules
    routing-corpus.jsonl        16 cases, both polarities, 4 adversarial
    NOTICE                      upstream attribution, MIT
  tools/concept-graph/
    cg.py                       the engine, stdlib only, python 3.9+; see 5.4
    recall.sh                   UserPromptSubmit fast path (9/10 item 1), beside the engine
    tests/test_cg.py            tool-only test
  tests/                        component-level: test_recall_hook.py, test_install.py
  docs/design.md                this file
```

Installed paths: `~/.claude/skills/feynman/`, `~/.claude/tools/concept-graph/cg.py`,
`~/.claude/hooks/concept-graph/recall.sh`, store at `~/.claude/concepts/`. Permissions
on the target machine are Claude Code defaults plus the two allow rules in the
fragment, so `cg` runs without prompts and no file tool ever touches the store.

### 5.2 Store layout

```
~/.claude/concepts/
  cards/<slug>.md        source of truth, one concept per file
  index.json             derived: slug -> title, aliases, scopes, status, open gap count, due
  lexicon.txt            derived: one "<token>\t<slug>" per line, lowercase, for the hook
  log.jsonl              append-only: who changed which card when (session id, action)
```

Only `cards/` is hand-editable. `cg index` rebuilds the other three; every write
command rebuilds them itself.

### 5.3 Card schema

```markdown
---
name: wal-mode
title: SQLite WAL mode
aliases: [write-ahead log, wal]
scopes: [global, /Users/matthias/frontier]
status: understood          # learning | understood | stale
confidence: 4               # 1..5, self-rated after the test question
epistemic: verified-in-code # strongest class among the card's closed gaps
edges:
  depends_on: [sqlite-journal]
  related: [graph-memory-store]
  contrasts_with: [rollback-journal]
anchors:
  - repo: /Users/matthias/frontier
    path: hooks/graph-memory/schema.sql
    line: 10
    sha: 5b2dbee
gaps:
  - q: Why do readers never block writers in WAL?
    status: closed
    evidence: source-cited
    ref: https://sqlite.org/wal.html
  - q: What happens to a WAL file on an unclean shutdown?
    status: open
    opened: 2026-10-29
    due: 2026-11-05
created: 2026-10-29
updated: 2026-10-29
---
## Simple explanation
<= 120 words, child bar.

## Analogy
One analogy. Then: **Where it breaks:** one sentence.

## Pitch
The 30-second version.

## Log
- 2026-10-29 created from a question in frontier (session 2335381c)
```

State model: `learning` (open gaps, confidence under 3), `understood` (no open gaps or
confidence 3+), `stale` (set only by `cg check` when an anchor moved or a due gap is
over 30 days late). Transitions happen only through `cg`; the skill never edits a
card file directly.

### 5.4 CLI surface

```
cg recall <term>...            cards whose title, alias or lexicon token matches; compact print
cg show <slug>                 full card
cg add <slug> --title T [--alias A]... [--scope S]...   creates the card from stdin body
cg set <slug> key=value...     frontmatter fields (status, confidence, epistemic)
cg gap <slug> add|close "<q>" [--evidence CLASS --ref R] [--due YYYY-MM-DD]
cg link <slug> <edge> <slug>   edge in {depends_on, related, contrasts_with, instance_of}
cg anchor <slug> --repo R --path P [--line N]   records the current HEAD sha
cg gaps [--due] [--scope S]    open gaps, optionally only those due
cg check [--scope S]           anchor drift (path missing, sha no longer contains the line) -> status stale
cg neighbors <slug> [--depth N]
cg export --format mermaid|json [--scope S]
cg index                       rebuild index.json, lexicon.txt
```

Compact print format for `recall` is the injection block of section 6 minus the
header, so the skill and the hook show the same text.

### 5.5 Skill protocol

Trigger surface is the skill description only. No line is added to the global
instructions for Claude. Draft description (under 220 chars, single sentence, trigger
language for the lint):

> Use when the user asks how or why something works, asks to explain or understand a
> concept or part of a codebase, or runs /feynman; recalls and updates the global
> concept graph.

Steps in SKILL.md:

0. **Recall.** `cg recall` with the topic's key terms. A hit means refine the card, not
   restart. Show open gaps first.
1. **Explain** at child level, under 120 words, plus one analogy with its breaking point.
2. **Audit.** Gaps table with a fourth column, "How to close" (read code, run,
   source, ask). Jargon table unchanged.
3. **Close** each gap by its method. Repo questions: close only with
   `verified-in-code`, `ran`, or `source-cited`; anything else stays open with a due
   date one week out.
4. **Refine** the explanation, write the pitch, self-rate confidence.
5. **Persist.** `cg add` or `cg set`, gaps, edges to at least one neighbour, anchors
   for every code claim. Scope is `global` unless the concept only makes sense in
   this repo, then `global` plus the repo path.

Weights: `/feynman <topic>` runs the full template from `references/protocol.md`. A
triggered ordinary question runs steps 0 to 5 but prints only the lite form.

Anti-triggers in SKILL.md: a request to change code, a lookup with a one-line factual
answer, a question about this conversation, any prompt already carrying a `memory:`
block that answers it.

### 5.6 Overhead budget

| Condition | Tokens | Latency |
|---|---|---|
| Session that never touches the skill | about 60 (the description in the skills list) | 0 |
| Skill fires, lite form | SKILL.md about 1.1k plus the recall print, 400 cap | one `cg` call |
| `/feynman` full | plus `references/protocol.md`, about 600 | |

No hook, no settings change, no instruction snippet at 8/10.

## 6. What 10/10 would be

1. **One store.** Concept cards ingested into graph-memory under a CONCEPT entity type
   and a curated-global write path, so one recall hook, one provenance contract, one
   quarantine ledger and one eval corpus serve both. Needs an ADR-001 amendment and
   vocabulary change in a subsystem with its own evals.
2. **Semantic recall.** Paraphrased questions hit cards; today's match is title, alias
   and token. Needs an embedding model and a per-prompt vector lookup.
3. **Blind grading.** A reviewer-tier model grades the simple explanation and pitch
   without seeing the card, and writes the confidence. Removes self-grading.
4. **Automatic gap harvesting.** A Stop-hook policy mines the finished turn for hedges
   and files them as gap candidates on matching cards.
5. **Fleet-wide drift.** `cg check` runs from daily-brief across every repo, not on
   demand.
6. **Subagent recall.** Subagents never receive prompt-hook injection (graph-memory
   ADR-003 accepts the same limit); 10/10 passes the matched cards into subagent
   prompts.
7. **Method-agnostic graph.** Socratic, 5-whys and premortem skills feed the same
   cards.

Each of these is either an LLM call per prompt or card, or a change inside a system
that has its own contracts. None is needed to make the method work daily.

## 7. The 9/10 target

8/10 plus these six, none of which touches graph-memory or adds a model call to the
prompt path:

| # | Addition | Why it earns the point | Cost |
|---|---|---|---|
| 1 | **Prompt recall hook** `hooks/concept-graph/recall.sh`: grep the payload's tokens against `lexicon.txt`; on a hit run `cg.py hook-recall`, which verifies whole phrases against the prompt, filters by scope, dedups per session by card content hash, and prints one `memory:` block (header, per-card provenance, guard line, 1,200-char cap, at most 2 cards). Silent otherwise, exit 0 always, timeout 3. | Concepts surface in any dir without the model remembering to look. Zero tokens on no match, and a card is injected once per session unless it changes. | one `UserPromptSubmit` entry, merged by `install.py`; about 5 ms on miss |
| 2 | **Due gaps in recall.** A matched card with a due open gap is printed with the gap first. `cg gaps --due` is step 0 of the skill. | Spaced re-encounter without a scheduler. | none |
| 3 | **Anchor drift check** wired into the skill's step 0 for repo scopes (`cg check --scope <repo>` before recall). | A stale card is marked before it is recalled as current. | one git call per anchor |
| 4 | **Opt-in blind grading** `cg grade <slug>`: `claude -p` (model from `--model` or `CONCEPT_GRAPH_GRADE_MODEL`, default `claude-opus-5-5`), prompt holds the explanation, analogy and pitch only, returns a 1 to 5 score and one sentence; written to the card. Explicit command, never automatic. | Closes the self-grading hole at the user's discretion. | one model call when asked |
| 5 | **Codex parity.** Dropped at the 2026-10-30 reorg: deployment targets Claude Code only. The engine keeps `hook-recall --plain` (bare-block output) so another harness can register `recall.sh --plain` itself; porting is manual and out of scope here. | Kept the engine harness-neutral without a second deploy path. | none here |
| 6 | **Test coverage.** `test_cg.py` (engine end to end, including anchor drift against a real git repo), `test_recall_hook.py` (fast path proves python never starts on a miss), `test_install.py` (merge, idempotence, link, uninstall, foreign-dir protection). Routing corpus checked once here with frontier's mechanical lane: 16 cases pass. | A capability without tests cannot be installed by hand with confidence. | test time |

Explicitly out of the 9/10: everything in section 6.

## 8. Validation

Run on the target machine after install (all standard library, no network):

```
python3 ~/frontier-clean/feynman/tools/concept-graph/tests/test_cg.py
python3 ~/frontier-clean/feynman/tests/test_recall_hook.py
python3 ~/frontier-clean/feynman/tests/test_install.py
```

All three print `OK` here under Python 3.13 and the system 3.9.6. The skill description
is 213 characters, one sentence, trigger-first. The routing corpus passes the
mechanical lane (16 cases, 8 fire, 8 skip, 4 adversarial); the judgement and overlap
lanes were not run (they need a logged-in `claude` CLI outside a sandbox).

Manual check, once live: in a repo ask how some mechanism works and confirm the lite
form, a card, an anchor. Open a new session elsewhere and mention the concept: a
`memory:` block precedes the prompt, and the skill refines the card instead of starting
over. Ask the same thing again in that session: no second block.

## 9. Stop conditions (still standing)

- The prompt hook measurably slows prompts (over 20 ms on a miss): remove its entry
  from the fragment and rerun `install.py`; the skill's own recall step keeps working.
- The description steals triggers from another skill on the target machine: narrow it
  and add the collision as a `skip` case to the corpus.
- Anything that requires a shared store with another memory system: that is the 10/10
  track, designed separately.

## 10. What was built, in order

1. `tools/concept-graph/cg.py` and its `tests/test_cg.py`.
2. `tools/concept-graph/recall.sh`, the settings fragment, `tests/test_recall_hook.py`.
3. `skills/feynman/` (SKILL.md, references, corpus, NOTICE) and `instructions/feynman.md`.
4. A shared installer and top-level README; replaced on 2026-10-30 by the per-component
   `install.py`, `INSTALL.md` and `tests/test_install.py` after the operator's
   component-first reorg.

## 11. Decisions taken, change them if wrong

- Store at `~/.claude/concepts/`. Permissions are the two Bash allow rules in the
  fragment; the skill types the `cg` command in the exact form the rule matches.
- Skill name `feynman`, tool `cg`, hook directory `concept-graph`.
- One three-line instruction section (`instructions/feynman.md`), because the
  target machine has no existing rule that `memory:` blocks are data. The trigger
  surface stays the skill description only.
- Lite form fires on explanatory questions; task prompts and one-line lookups do not
  trigger. The routing corpus pins this.
- Inside an ICM workspace the skill does not auto-fire; `/feynman` works and writes
  only to the store. The recall hook still injects there, as recalled data.
- Dedup key is the card's content hash, not its timestamp, so any edit re-enables
  recall in a running session.
