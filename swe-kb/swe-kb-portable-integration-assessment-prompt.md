# swekb-01 assess the software design knowledge base fc-2e9c44

```
cd ~/projects/frontier-clean && claude --model claude-opus-5-5 --effort high "$(cat swe-kb/swe-kb-portable-integration-assessment-prompt.md)"
```

The launch line submits this file as the first message of a fresh session rooted at `~/projects/frontier-clean`; nothing to paste.

---

# swekb-01 assess the software design knowledge base fc-2e9c44

`swe-kb/swe-kb-portable-integration-assessment-prompt.md`

This is an assessment, not an implementation. Change no files; the result goes in notes on ticket fc-2e9c44 (`pm ticket show fc-2e9c44`).

## What exists

- `swe-kb/swe-kb-portable.md`: a 356 KB single-file transport of a software design knowledge base: 204 concepts (architectural, design and Gang of Four patterns, implementation techniques, integration patterns, design principles), TSV catalog and aliases, generated `INDEX.md` routes, a read-only lookup CLI (`scripts/kb`), an index builder and tests. Its own text calls the content unverified seed data. It has never been extracted. Its extractor writes into `swe-kb/kb/`.
- `swe-kb/README.md`: what is here and why it is tabled.
- Possible consumers, none of which uses it today: the cwf design skill (`cwf/skills/cwf-design/`), which is absorbing a design-review gate, and any other component that reasons about software design.

## Rules that already decide part of the answer

Read these before forming a view:

- [Behavioral contract](/README.md#behavioral-contract): independent use; roles, not names; one maintained source.
- [Contribution standards](/docs/contributing.md): component layout, the `AGENTS.md` template, the deploy script, state outside the repository, imports conform before use.
- [Component principles](/docs/component-principles.md): especially 8 (every mechanism names the requirement it serves) and 9 (decoupled by default).
- [cwf product requirements](/cwf/docs/PRD.md): R05, R10 and the non-goals.

Consequences to take as given unless you find evidence against them:

- If the KB is kept, it is its own component (`swe-kb/`), not part of cwf or any other component.
- A consumer refers to it by role ("a design-knowledge lookup, when available") and works without it. No consumer embeds the catalog or restates its rules.
- Its CLI is the interface; a deploy script links it onto the PATH like any other component's.

## Questions

1. **Keep or drop.** Is there a requirement in this repository that the KB serves? Which consumer would use it, for which task, and what would that task do worse without it? If nothing needs it, say so; "drop" and "keep tabled" are acceptable answers.
2. **Content.** Sample at least ten concepts across categories. Is the content accurate enough to act on, or would an agent do as well from its own knowledge? Is the relationship data usable?
3. **Shape, if kept.** Extract into `swe-kb/kb/` or restructure? What in the extracted bundle conflicts with the contribution standards: its generated root `AGENTS.md` versus the component `AGENTS.md` template, the extractor's refusal to overwrite files whose bytes differ (compare with the no-byte-validation ruling), the index generator's scan of the directory it lives in, tests run from the KB root rather than the repository root.
4. **Consumer contract, if kept.** The exact role sentence a consumer would carry, the CLI commands it would call, and what happens when the KB is absent. Any change to cwf skill text needs a behavioral check on OpenCode with `openai/gpt-6-luna` (LUNA CHECK PROTOCOL note on ticket fc-91e7d2); state the cases that check would run.
5. **Cost.** Bytes an agent would read per typical lookup, and any always-loaded text the integration adds.

## Out of scope

Building a general knowledge-management system, a registry or plugin layer, embeddings, or changing any component.

## Report

One RESULT note on fc-2e9c44 with: the recommendation (drop, keep tabled, or adopt as a component), the evidence for it with file and line references, the answers to the five questions, the minimal change set if adopted (files, owner, verification), and what you did not check. End your session with `Ticket: fc-2e9c44 <status>`; leave the ticket open for the operator's ruling.
