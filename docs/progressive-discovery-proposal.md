# Proposal: progressive discovery with a small zsh reader

Status: proposed; no runtime changes or installation. This document specifies a
bounded pilot for `frontier-clean`.

## Purpose and acceptance rule

Make relevant guidance easy to find and read without repeatedly loading unrelated
material. Optimize total task cost while preserving correctness, useful context,
and reliable recovery. Fewer retrieved tokens alone do not establish improvement.

Adopt the pilot only if representative tasks retain their required guidance and
successful outcomes, while total input tokens decrease beyond ordinary run
variation and latency does not materially regress. Otherwise simplify it or keep
the existing Markdown navigation. The current shared guides are short enough that
an extra command may cost more than it saves.

Follow the existing [behavioral contract](/README.md#behavioral-contract),
[contribution standards](/docs/contributing.md), and
[instruction delivery guidance](/docs/instruction-delivery.md). This proposal does not
replace those sources or turn discovery into a mandatory workflow.

## Design

Use a small Markdown route table and one noninteractive zsh executable. The agent
chooses a route; the script validates it and returns the requested source text.
The same table remains understandable and usable without the script.

Discovery has three levels:

1. An existing entry point names the relevant index and why to read it.
2. The index lists route IDs, concrete reasons to read, and source locations.
3. Reading a route returns a complete document or an explicitly selected section,
   including its subsections. References in that text support further discovery.

Keep essential safety, authorization, and universally applicable obligations at
their existing entry points. A route must not hide requirements needed to decide
whether to follow that route. Reading a procedure as evidence does not invoke it
or grant permission to perform its actions.

### One readable index format

Each index is a `routes.md` file containing a short purpose paragraph and exactly
one table with these columns:

```markdown
| ID | When to read | Source | Section |
| --- | --- | --- | --- |
| setup | Setting up or removing a component | INSTALL.md | - |
| validation | Changing component implementation or tests | AGENTS.md | Validation |
```

This is an illustrative component index; it is not a claim that these headings
exist in every current component.

- IDs are unique within the index: lowercase letters, digits, and hyphens.
- `When to read` states the decision or operation the source helps with.
- `Source` is a plain path relative to the index. Spaces are supported; literal
  pipes and newlines inside cells are not. Cells contain no executable syntax.
- `Section` is `-` for the whole file, or the exact unique heading title.
- Start with whole-file routes. Select a section only after checking that it is
  understandable with the normal entry-point context. Prefer whole files when
  prerequisites are scattered through a document.
- An index has one owner and is the maintained source for its route metadata.
  Existing entry points link to it when adopted; they do not maintain duplicate
  copies of the same table. Small existing tables can remain as they are when
  moving them would add navigation without benefit.

Keep procedure text in its current owning document. Avoid YAML dependencies,
generated summaries, copied instruction bodies, and a separate metadata database.

### Command interface

Proposed commands, shown from the repository root:

```sh
zsh discovery/cli/discover list path/to/routes.md
zsh discovery/cli/discover read path/to/routes.md validation
zsh discovery/cli/discover read path/to/routes.md validation --full
zsh discovery/cli/discover check path/to/routes.md
```

`list` prints the index's purpose and route table. `read` prints a short source
header followed by verbatim source text. `--full` explicitly returns the complete
source file. `check` validates every row and target in that index, printing a
concise result and returning nonzero for any defect.

The index path is explicit, with no ambient project detection or global registry.
Repeated reads return the same current content; there is no persistent read cache
or suppression based on previous sessions. This supports recovery after context
loss. A previously retrieved section is not evidence that the agent still has it.

## Reliability contract

- Validate input before printing source content. Unknown IDs, duplicate IDs,
  malformed tables, unreadable targets, and missing or duplicate selected headings
  produce an actionable error on stderr and a nonzero exit status.
- On a bad section reference, report the source path so a human or agent can read
  the full file directly. Do not silently substitute another section or a summary.
- Print the resolved source path and selected heading, or `whole file`, in the
  output header. Never truncate to a token budget or omit text without saying so.
- Recognize ordinary ATX headings (`#` through `######` followed by a space).
  A selected section ends at the next heading of equal or shallower depth.
  Ignore heading-like lines inside backtick or tilde fenced code blocks. Match
  titles literally; do not guess GitHub anchor slugs. Unsupported heading styles
  use whole-file routes until there is evidence to justify broader parsing.
- Treat all index fields as data. Never use `eval`, source a route file, expand
  shell expressions from cells, or execute commands embedded in documents.
- Resolve paths relative to the index, independently of the caller's working
  directory. For the repository pilot, reject absolute paths, URLs, and targets
  whose canonical path escapes the repository, including through symlinks.
  Check the resolved boundary before reading a target. Parent-relative paths
  within the repository are allowed. This is a scope guard, not a replacement for
  host permissions; discovery never expands existing read authorization.
- No automatic traversal of references or prerequisite graphs. If route selection
  is unclear, inspect the relevant index or source using normal text search. Direct
  reading remains available when the helper cannot express a useful retrieval.

## Ownership and zsh structure

If the pilot proceeds, keep implementation in a standalone `discovery/` component:

```text
discovery/
  AGENTS.md                Maintenance routes and validation commands
  README.md                Purpose, command contract, and limitations
  INSTALL.md               Direct use, optional symlink, verification, removal
  cli/discover             One executable zsh script
  tests/test_discover.py   Standard-library tests invoking zsh
  tests/fixtures/          Small route and document fixtures
  docs/evaluation.md       Baseline, paired results, and adoption decision
```

Each adopted index belongs beside the documentation it routes. Shared routing
belongs under `docs/`; component-specific routing belongs in that component.
Create only the pilot index initially. Add the component to the root component
index when it exists and has passed its local checks.

Implement the script as small functions with explicit arguments and local
variables: `usage`, `load_routes`, `resolve_source`, `read_section`, `list_routes`,
`read_route`, `check_routes`, and `main`. Keep parsing separate from output and
dispatch. Use `emulate -L zsh`, quoted paths, `read -r`, `print -r --`, and explicit
error returns. Avoid elaborate option parsing, a library framework, global mutable
session state, and reliance on implicit shell error behavior.

Keep the parser limited to the documented table and heading subset. Unsupported
input should produce a clear failure rather than encouraging a general Markdown
engine. Runtime needs zsh and ordinary local file access; tests use Python's
standard library, consistent with the repository's contribution standards.

Initial use runs directly from the checkout. Document an optional executable
symlink only after usefulness is demonstrated. Hooks, provider configuration,
automatic installation, interactive menus, embeddings, and external services are
outside this pilot.

## Implementation and evaluation sequence

1. **Establish a baseline before moving instructions.** Select a small set of
   actual tasks: known-route lookup, ambiguous discovery, a task spanning multiple
   documents, full-source recovery, and rereading after context loss. Record the
   guidance and outcomes each task must preserve. Include a short-document case
   where direct reading is likely better. Use existing routes as the comparison.
2. **Implement the helper against fixtures.** Add the single zsh executable and
   standard-library tests. Verify exact section output, nested sections, fenced
   headings, final lines without newlines, paths with spaces, caller-directory
   independence, malformed input, duplicate IDs/headings, missing targets,
   symlink escapes, and `--full` recovery. Confirm shell-like cell text stays inert.
3. **Pilot a few real routes.** Choose one documentation area with evidence of
   repeated unnecessary reading. Its owner reviews each selected section for
   omitted prerequisites. Run `check` against the real index. Preserve ordinary
   entry-point navigation while the experiment is optional; migrate its route
   table only upon adoption.
4. **Compare complete task runs.** Hold task, source revision, model settings, and
   starting context constant between baseline and candidate. Repeat paired runs
   and alternate their order. Record total input/output tokens, tool calls,
   elapsed time, successful outcomes, missed guidance, and recovery behavior.
   Count index reads, command overhead, errors, rereads, and fallback reads.
   Byte counts are diagnostic only, not proof of token savings. Keep provider
   measurements separate and record cached input separately where available.
5. **Decide from the evidence.** Require no missed required guidance or regression
   on the agreed task checks, and successful recovery for every deliberate fault.
   Report token and latency deltas per task, medians, and spread; do not hide a
   material regression in an aggregate. Set the acceptable latency margin before
   measurement. If savings do not exceed run variation, retain ordinary navigation.
6. **Adopt incrementally.** Publish results and limitations, link the proven index
   from its existing entry point, and document use/removal. Expand to another area
   only when it has the same demonstrated need. Keep all source documents usable
   directly so removing the helper does not remove guidance.

Proposed implementation checks are `zsh -n discovery/cli/discover` and
`python3 -m unittest discover -s discovery/tests`. These commands describe future
validation; no implementation or efficiency experiment has been run for this
proposal. Performance and task reliability remain hypotheses to test.
