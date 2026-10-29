# Feynman layer: assessment, abstraction, and target design

Status: design, 2026-10-29. Implementation is the next turn. Same staging pattern as
the ICM layer in this repo: `general/` is provider-neutral, `vendor/` holds only what a
provider needs, everything is ported into `~/frontier` and deployed from there.

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
a shell-fast-path prompt hook at 9/10. Store path `~/.claude/concepts/` with explicit
posture rows (read, edit, sandbox write for Claude; read and write for Codex).

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
general/
  skills/feynman/
    SKILL.md                    protocol, two weights, persistence rules (about 700 words)
    references/protocol.md      full-weight template (the upstream four steps, revised)
    references/card.md          card schema with a filled example
    routing-corpus.jsonl        >=10 cases, both polarities, >=2 adversarial
    NOTICE                      upstream attribution, MIT
  tools/concept-graph/
    cg.py                       stdlib only; see 5.4
    tests/test_cg.py
vendor/
  claude/README.md              nothing extra at 8/10
  codex/README.md               skill path, tool path, no hook at 8/10
docs/feynman/design.md          this file
```

Frontier targets: `skills/feynman/` (package `skill-feynman`, providers claude and
codex, corpus excluded), `runtime-tools/concept-graph/` (deploys to
`~/.claude/tools/concept-graph/`), two posture rows per plane for
`~/.claude/concepts/`.

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
| 1 | **Prompt recall hook** `hooks/concept-graph/recall.sh`: grep the prompt's tokens against `lexicon.txt`; on a hit exec `recall.py`, which prints one `memory:` block (graph-memory grammar: header, provenance per card, guard line, 1,200-char cap, at most 2 cards). Silent otherwise, exit 0 always, timeout 3. | Concepts surface in any dir without the model remembering to look. Zero tokens on no match. | one `UserPromptSubmit` entry in `config/claude/settings.config.json` (operator-run deploy of config-claude); about 5 ms on miss |
| 2 | **Due gaps in recall.** A matched card with a due open gap is printed with the gap first. `cg gaps --due` is step 0 of the skill. | Spaced re-encounter without a scheduler. | none |
| 3 | **Anchor drift check** wired into the skill's step 0 for repo scopes (`cg check --scope <repo>` before recall). | A stale card is marked before it is recalled as current. | one git call per anchor |
| 4 | **Opt-in blind grading** `cg grade <slug>`: `claude -p` at the reviewer model id from `providers/claude.json`, prompt holds the explanation and pitch only, returns a 1 to 5 score and one sentence; written to the card log. Explicit command, never automatic. | Closes the self-grading hole at the user's discretion. | one model call when asked |
| 5 | **Codex parity.** Skill deploys to `~/.agents/skills/feynman`; `cg` is reached at its Claude tools path; recall via a `user_prompt_submit` entry in `~/.codex/hooks.json` printing the bare block (same shape as graph-memory Stage C3, operator-applied snippet in `ops/`). | Same graph from both providers. | posture rows for Codex; one operator step |
| 6 | **Gate coverage.** Routing corpus passes `routing_eval.py --mechanical-only`; `lint-skill-metadata.sh` clean; `cg` and hook tests in `.deploy.json` test_commands; overlap lane run once against `repo-onboarding` and `memory-gardener` descriptions. | A new capability without evals is not done by this repo's own rules. | eval time |

Explicitly out of the 9/10: everything in section 6.

## 8. Validation (next turn)

- `python3 general/tools/concept-graph/tests/test_cg.py`: add, set, gap open and close,
  link, anchor plus drift, index rebuild, recall match on title, alias and token,
  recall miss prints nothing, export shapes.
- `python3 tests/test_hook.py` extended: recall.sh silent on miss, valid JSON on hit,
  guard line byte-identical to graph-memory's, cap respected, exit 0 on a missing store.
- `bash ~/frontier/tools/lint-skill-metadata/lint-skill-metadata.sh general/skills`:
  no SM1xx warnings on `feynman`.
- `python3 ~/frontier/runtime-tools/routing-eval/routing_eval.py --mechanical-only general/skills/feynman/routing-corpus.jsonl`: PASS.
- Manual: in a repo, ask "how does the wt finish merge work" and confirm the lite
  form, a card, an anchor; `cd` elsewhere and ask about the same concept, confirm
  recall from `global` scope.

## 9. Stop conditions

- The store path needs anything beyond posture rows (a new harness directory
  convention): stop and take the `projects/global/memory` fallback instead.
- A second prompt hook measurably slows prompts (over 20 ms on miss on this machine):
  ship 8/10 and revisit.
- The description collides with `repo-onboarding` or `memory-gardener` in the overlap
  lane at FAIL tier: narrow it before deploy.
- Any step requires editing graph-memory: that is the 10/10 track, a separate ticket.

## 10. Implementation order (next turn)

1. `general/tools/concept-graph/cg.py` and tests. Store root from
   `CONCEPT_GRAPH_ROOT` env for tests, default `~/.claude/concepts`.
2. `general/skills/feynman/` (SKILL.md, references, corpus, NOTICE). Lint and
   mechanical eval.
3. `vendor/claude/hooks/concept-recall.sh` plus `recall.py`, settings fragment, test.
4. `vendor/codex/README.md` and the hooks.json snippet.
5. Port table in `README.md` (same shape as the ICM table), posture rows listed with
   their exact JSON.
6. Commit per component.

## 11. Decisions taken here, change them if wrong

- Store at `~/.claude/concepts/`, explicit posture rows. Fallback named above.
- Skill name `feynman`, tool name `cg`, hook package `concept-graph`.
- No global instruction snippet for Claude. For Codex the same, since skills are
  listed from `~/.agents/skills`. A two-line snippet is drafted in the skill's
  README only for a provider that does not list skill descriptions.
- Lite form fires on explanatory questions; task prompts and one-line lookups do not
  trigger. The routing corpus pins this.
