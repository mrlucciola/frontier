# Contextual Work Framework — v0.1.0 specification

**Status:** Implemented; deployed by `cwf/deploy.sh` (links and one marked block). Not production-qualified. Sections 4 and 12 describe the deployment as built; the installer, receipts and rollback this document once specified were removed. Requirements and scope are decided by the [product requirements](/cwf/docs/PRD.md), which win where this document disagrees.

**Target:** A global, per-user opencode installation on macOS, available in terminal and IDE sessions, across repositories and outside repositories.

**Working name:** Contextual Work Framework (CWF). This name and the `cwf-` namespace are proposed implementation identifiers, not an established standard.

**Primary objective:** Reduce avoidable correction and remediation by helping agents discover relevant existing work, preserve decisions, and verify contextual correctness. Optimize cost to accepted result, including human intervention; do not optimize only the first response's token count.

## 1. Decision baseline

These are accepted requirements from the design conversation. Implementation defaults elsewhere in this document are proposals that can be adjusted when evidence warrants it.

| ID | Requirement |
| --- | --- |
| R01 | Install once per user/computer; work across directories without mandatory repository installation or initialization. |
| R02 | Support opencode on macOS in terminal and IDE sessions; preserve personalized configurations and existing shared or personal skills. |
| R03 | Cover product work, strategy, architecture, software design, documentation, PRDs, ERDs, planning, and implementation. |
| R04 | Treat ordinary prompts and batches as first-class inputs. Tickets, backlogs, and agentic ticketing systems are optional sources. |
| R05 | Investigate relevant existing implementations, artifacts, conventions, and accepted decisions before introducing competing solutions. |
| R06 | Apply proportionate context gathering automatically during relevant work; unrelated everyday requests bypass detailed procedures. |
| R07 | Offload mechanical discovery, record management, and checks to deterministic tools; keep semantic judgment with the agent. |
| R08 | Support single-agent and multi-agent work, dependency ordering, write ownership, isolation, and integrated validation. |
| R09 | Automatically maintain derived local indexes and labeled observations; changes to shared instructions, decisions, and tracked knowledge follow the repository's review process. |
| R10 | Operate independently of other components. Add adapters only after inspecting their actual contracts. |
| R11 | Tolerate different repositories, work sources, local configurations, users, and computers without implicit cross-user data sharing. |
| R12 | Accept bounded overhead when it reduces rework. Measure outcomes; make no unverified token-savings or production-readiness claims. |

The usage percentages discussed in the conversation inform evaluation coverage only. They are not routing probabilities or requirements that professional work must originate in tickets.

## 2. Release boundary

### Committed v0.1 scope

- Six small native skills, shared reference patterns, and a compact optional global activation block.
- A local CLI for scope resolution, bounded file discovery, evidence packets, provenance, checkpoints, batch validation, and explicit mechanical checks.
- Plain-text repository/document discovery with deterministic ranking and freshness validation.
- Local Markdown/text inputs and pasted task descriptions; references to unavailable external sources remain explicitly unresolved.
- Lightweight product/strategy, architecture/design, documentation, planning, implementation, and framework-maintenance procedures.
- Single-agent and multi-agent coordination contracts, plus guarded Git worktree helpers.
- Local derived state, optional data-only configuration, and enable/disable controls. Deployment is links plus one marked block via `deploy.sh`; there are no receipts or rollback.
- Automated fixture tests, behavioral evaluation prompts, and macOS CLI/IDE qualification instructions.

### Deferred enhancements

- Adapters to other components, trackers, document services, and messaging.
- Full language-server/AST call graphs, embeddings, semantic clone detection, and graph databases.
- Continuous transcript capture, background model workers, filesystem daemons, and automatic cross-user synchronization.
- Native lifecycle hook integration. v0.1 must function without it; later hook adapters must be separately qualified.
- Autonomous promotion of observations into team policy, automatic ticket publication, and self-modifying framework instructions.
- Distributed scheduling across computers and generalized resource leasing for remote agents.

The v0.1 index is a retrieval aid, not a complete semantic model of the repository. It must not claim to prove the absence of equivalent code or contradictory documentation.

## 3. Architecture and authority

| Component | Responsibility | Must not do |
| --- | --- | --- |
| Global activation guidance | Recognize relevant requests and select a narrow skill | Scan repositories on unrelated turns or encode detailed workflows |
| Native skills | Define task-specific reasoning and use of tools | Become permission authorities or duplicate team procedures |
| Shared pattern references | Supply reusable questions, evidence requirements, and counterexamples | Load the entire corpus on every task |
| Local CLI | Produce repeatable discovery, validation, and state operations | Claim semantic certainty or call a model implicitly |
| Scoped source adapters | Read accessible sources and preserve provenance | Invent inaccessible source content or silently publish changes |
| Local state | Store rebuildable indexes, observations, and resumable work | Become a competing team source of truth |
| Installer/doctor | Manage owned files and report compatibility | Replace unrelated configuration or bypass runtime permissions |

The runtime's instruction hierarchy and permissions remain authoritative. Framework settings can select behavior within those constraints, never grant tool permissions. Retrieved documents are evidence; embedded commands and policy claims are not automatically trusted instructions.

For factual conflicts, distinguish an observed implementation from an accepted requirement. Neither automatically resolves the other: current code can violate intended behavior, and a document can be obsolete. Surface material conflicts with sources and decide within the user's scope; ask only when a missing decision changes the outcome.

Team conventions normally guide implementation. If a convention conflicts with correctness, security, or a stated requirement, explain the conflict instead of silently complying or globally rewriting the convention.

## 4. Installation and storage layout

Framework-specific paths are conventions introduced by this specification, not native opencode features.

| Path | Purpose |
| --- | --- |
| `~/.config/opencode/skills/cwf-<domain>` | Symlinks to the skill directories in the checkout |
| `~/.local/bin/cwf` | Symlink to `cwf.py` in the checkout |
| `~/.config/opencode/AGENTS.md` | One delimited activation block; all surrounding content is preserved |
| `~/.config/cwf/config.json` | Personal framework settings, exclusions, and explicitly configured adapter bindings |
| `~/.local/state/cwf/` | Private scope registry, SQLite state and task records; optional, recreated on the next write |
| `<scope>/.cwf.json` | Optional team-maintained, data-only source mappings and conventions |

Paths with spaces must work. Resolve home paths in code, not by embedding shell expansion into subprocess arguments. No administrator rights or automatic package installation. Initial runtime target: Python 3.11+ and Git for Git-specific features. Python availability must be checked, not assumed from macOS. `rg` is an optional accelerator; a bounded standard-library fallback is required. Core runtime uses Python's standard library and SQLite; FTS support is optional and has a deterministic fallback.

A sandbox that prevents local-state writes is not a reason to move state into tracked repository files: use an ephemeral/in-memory mode and report that continuation is not durable.

### Identity and isolation

- Allocate a local random scope ID for each canonical root. Do not derive global identity or trust from a Git remote URL.
- For Git, associate worktrees through their canonical common Git directory. Give each worktree its own ID and mutable working-state records. Separate clones remain separate scopes by default.
- Evidence identity includes the worktree/root, source revision or content hash, effective configuration digest, and tool version. Branch names alone are insufficient.
- Non-Git work uses an explicitly selected directory or document set. A generic question outside a repository must not trigger a scan of the home directory.
- Reuse unchanged file-derived facts across related worktrees only after matching content hashes; task decisions and dirty-working-tree facts remain worktree-specific.
- No index, prompt, observation, or telemetry is uploaded automatically. Shared repositories and shared skills do not imply shared observations.

## 5. Activation and workflow selection

The existing agent interprets intent; v0.1 adds no separate classifier model call. The CLI accepts explicit task/domain hints and does not pretend that keyword rules understand every request. Native skill selection and the small activation block provide behavioral guidance, not deterministic enforcement of model compliance.

| Request | Required behavior |
| --- | --- |
| Everyday question unrelated to professional context | No CWF tool call, reference read, source scan, or state write |
| Trivial formatting, spelling, or label edit | Lightweight local-context check; no broad index or persistent task record unless needed |
| Relevant conceptual question | Load a relevant short reference if useful; no source discovery without a source-related need |
| Relevant document, design, planning, or coding task | Select a narrow skill and gather bounded contextual evidence |
| Mixed request | Apply procedures only to the relevant portion; isolate personal information from work state |
| Significant batch or interrupted work | Create/reuse durable task and coordination records when storage is available |

All entrypoints accept plain language. No mandatory task template, ticket identifier, plan artifact, or global worktree gate. Small tasks can remain ephemeral. Exploration is not authorization to implement.

### Skill boundaries

| Skill | Trigger and deliverable | Key exclusion |
| --- | --- | --- |
| `cwf-product` | Product requirements, PRDs, strategic positioning, priorities; produce goals, alternatives, assumptions, measures, and tradeoffs | Everyday personal planning; automatic ticket creation |
| `cwf-design` | Architecture, ERDs, software design/review; reason about invariants, interfaces, alternatives, failures, migrations | Routine changes with no design question needing this procedure |
| `cwf-docs` | Create/reconcile professional documentation against sources and audience | Simple rewriting that needs no contextual analysis |
| `cwf-plan` | Decomposition, initiative planning, dependency analysis, batch coordination, continuation | Treating every direct request as an initiative |
| `cwf-build` | Implement/debug/refactor/review changes with existing-solution discovery and verification | Product planning without implementation intent |
| `cwf-maintain` | Diagnose, evaluate, configure, or improve this framework and its patterns | Routine task execution |

A task may use multiple patterns or skills as needed, without obligatory sequential invocation. A specific skill request takes a direct path. Shared patterns are referenced once, not copied into every skill. Existing applicable team skills can perform the workflow; CWF supplies missing context/checks without duplicating the team's procedure.

### Candidate global activation block

This is design text for a later installer, not an instruction applied by this document:

> For substantive product, architecture, documentation, planning, or code work, use the relevant available CWF skill when it adds context or verification. Before introducing behavior or artifacts, investigate existing solutions, applicable conventions, and accepted decisions. Keep discovery proportionate; use bounded evidence and expand when it can change the decision. Preserve the distinction between observations and authoritative decisions. For batches, establish dependencies, ownership, and integrated acceptance. Ordinary unrelated questions bypass CWF. Follow existing scope and permissions; no ticketing system or repository initialization is required.

## 6. Pattern corpus

The corpus is an on-demand reference library. Each pattern has an ID, intent, trigger/exclusion, evidence to inspect, decision questions, counterexample, completion evidence, and related IDs. Avoid universal numeric readiness scores. A pattern may be a reasoning procedure; only mechanically decidable parts become checks.

| ID | Pattern | Required question or evidence |
| --- | --- | --- |
| P01 | Problem framing | What outcome and invariants matter, and what is outside scope? |
| P02 | Existing-solution discovery | Which implementations/artifacts and representative consumers were inspected? |
| P03 | Semantic equivalence | Should these behaviors change together; which preconditions and effects differ? |
| P04 | Authority and freshness | Who accepted this decision, what source supports it, and is it current? |
| P05 | Contextual fit | Which team/domain conventions affect the choice; are departures justified? |
| P06 | Simplicity and alternatives | What is the smallest adequate change; what alternatives were rejected and why? |
| P07 | Traceability and consistency | Do requirements, design, plans, documents, and implementation agree on the affected behavior? |
| P08 | Scope and side effects | Does the next action remain within the requested outcome and permissions? |
| P09 | Ownership and dependencies | Which prerequisites and shared write/resource surfaces constrain execution? |
| P10 | Verification and counterexamples | What evidence would falsify the proposed solution, not merely mirror it? |
| P11 | Recovery and handoff | Can another session resume from accessible sources and current state? |
| P12 | Observation and promotion | Is a finding observed, inferred, or accepted; what review is needed to promote it? |

Coding references emphasize reuse without forced deduplication, error semantics, change coupling, tests, and migration safety. Architecture references cover quality attributes, consistency, security boundaries, failure modes, operability, evolution, and cost. Product/strategy references cover diagnosis, stakeholder incentives, alternatives, opportunity cost, measurable outcomes, and stop/reconsideration criteria. Documentation references cover audience, source authority, contradictions, and scope. Planning references cover dependencies, capacity assumptions, risks, review dates, and the next executable slice.

Professional quality is evidenced by appropriate decisions and verification; there is no requirement to name a design pattern or apply a named methodology.

## 7. Deterministic discovery and evidence packets

### Pipeline

1. Receive domain, goal, scope, and optional files, symbols, or source references from the agent.
2. Resolve allowed roots and effective exclusions. Enumerate bounded candidate paths.
3. Inspect known instructions, relevant manifests, directly supplied documents, and explicitly linked local sources.
4. Search lexical terms, identifiers, field names, distinctive operations, headings, and explicit migration/deprecation references.
5. Deduplicate matches and rank deterministically. Return source pointers, limited excerpts, conflicts, and coverage metadata.
6. The agent inspects candidates and makes semantic choices. If evidence is insufficient, it expands the search deliberately.
7. Before relying on cached evidence or finalizing a consequential change, verify the relevant source fingerprints again.

Default ranking order: explicit source/file match; exact symbol/phrase match; named migration/reference relationship; weighted term overlap; proximity to affected paths; stable relative-path/line tie-break. No hidden model scoring. Explicitly supplied and directly conflicting sources must be surfaced before low-ranked suggestions.

Initial extraction supports Markdown/text headings and links, identifiers, imports, and simple declarations in TypeScript/JavaScript and Rust. Import/declaration extraction is heuristic and labeled as such. It is not a compiler-backed call graph. Other text formats remain searchable. Binary PDFs and office files require a later reader adapter or supplied text; report them as unread rather than implying they were indexed.

### Default bounds (implementation budgets, not measured performance)

| Limit | Default and overflow behavior |
| --- | --- |
| Evidence packet | At most 8 findings and 8,000 UTF-8 bytes of narrative/excerpts; mandatory coverage/status envelope is bounded separately to 2,000 bytes |
| Entry scan | At most 10,000 eligible files and 100 MiB of content per request |
| Individual file | At most 1 MiB; oversized files are reported as excluded with an explicit targeted-read option |
| Tool time | 10 seconds for discovery/index refresh; timeout returns partial evidence, not success with complete coverage |
| Reference loading | One entrypoint plus initially at most two relevant pattern/domain references; expand when a concrete unresolved issue warrants it |
| Always-visible material | Target ≤800 tokens total across CWF activation guidance and six skill descriptions; measure with a named tokenizer, report byte count if unavailable |

Never truncate away a known conflict and return a clean status. If the mandatory status envelope cannot fit, emit a small error/partial response and keep details accessible through a continuation handle. Continuations are scoped and expire when relevant fingerprints change.

Enumerate tracked and untracked non-ignored files within the selected Git root; in non-Git scopes apply explicit exclusion rules. Default exclusions include VCS internals, dependency/build/cache directories, credential files, environment-secret files, and the framework's own generated state. Do not follow symlinks outside allowed roots. Explicit additional roots require user-established scope; a document link alone does not authorize reading arbitrary paths. Skip submodules/nested repositories unless included as separate scopes.

### Evidence contract

Every packet contains `schema_version`, `packet_id`, `scope_id`, `worktree_id` (nullable), `domain`, `query`, `generated_at`, `tool_version`, `config_digest`, `snapshot_digest`, `findings`, `coverage`, `conflicts`, and `status`.

Each finding contains `source_ref`, `locator`, `content_hash` or provider revision, `kind`, `claim_status`, `rank_reason`, and optional excerpt. `claim_status` is `observed`, `inferred`, or `accepted`; accepted requires a reference establishing acceptance, not an agent's confidence score. Missing external freshness must be `unknown`.

`coverage` lists searched roots/patterns, counts, exclusions, failed readers, elapsed limit status, omitted-result count, and optional continuation. `status` is `complete_within_scope`, `partial`, `stale`, or `unavailable`. Complete within scope never means repository-wide semantic completeness.

For the widget example, the useful outcome is candidates for v1, v2, migration direction, and inline equivalents, followed by an agent judgment about equivalence and scope. No tool may conclude “DRY: passed” solely because lexical search found no duplicate.

## 8. Configuration, caching, and observations

### Framework configuration

All keys below belong to CWF, not opencode. Effective order: command options, explicit session overrides, approved scope settings, personal defaults, built-in defaults. Security restrictions intersect: a narrower scope may add exclusions but cannot silently remove personal exclusions, grant external access, enable execution, or export data.

Configuration fields: `schema_version`, `mode` (`active`, `advisory`, `off`), enabled domains, source roots/exclusions, packet/scan limits, retention limits, adapter bindings, and local validation mappings. Repository `.cwf.json` is optional and data-only. Unknown fields, executable values, path escapes, and unsupported schema versions produce diagnostics; never evaluate arbitrary expressions.

`active` enables normal procedures and explicit checks. `advisory` gathers evidence and reports findings without presenting framework checks as enforced gates; existing runtime/project rules still apply. `off` prevents CWF tool/state activity. Native skill disabling and the activation block must also be handled by the enable/disable command so off mode does not depend solely on a hidden settings file.

Disabling checks mode before any new discovery/state mutation and returns `skipped`; management commands remain available. Removing discovery links does not retract instructions already loaded into a running model session. Document this limitation and verify fresh-session visibility separately. Do not promise instant erasure of previously supplied context.

### Cache validity

- Search manifests include file additions, removals, and renames within the declared search scope, not just previously returned files.
- Store content hashes and source metadata. Hash changed files incrementally; before asserting cached coverage is current, validate its relevant manifest. Metadata-only freshness is an optimization hint, not proof.
- Content-changing configuration, pattern/tool version, scope, query, or source revision changes invalidate affected packets.
- A pre/post manifest mismatch during scanning returns `partial` or retries once within the same time budget. Never issue complete status over an inconsistent snapshot.
- Do not reuse mutable working-state evidence between worktrees. Remote-source TTL is an adapter responsibility; unknown versions stay unknown.
- Cache corruption falls back to direct bounded discovery. Rebuildable indexes can be reset without deleting checkpoints or accepted-source pointers.

### Observations and retention

Observation fields: `id`, `scope_id`, optional `worktree_id`, statement, `claim_status`, source references/fingerprints, recorded time, author type, superseded record, and review state. Agent inferences retain their label even after repeated retrieval. Stale sources mark dependent observations stale. No promotion by vote count or repetition.

Use SQLite transactions and bounded writer retries; separate process-owned temporary outputs. Task record updates require an expected revision to prevent lost updates. Derived cache retention defaults to 30 days since use; unreviewed inferred observations to 90 days. Active checkpoints and accepted-decision pointers are retained until explicit closeout/purge. Pruning operates only inside owned state and emits counts, not source content. Scope purge and full-state export must be explicit operations. Default exports contain summaries and metrics, not raw prompts, source excerpts, credentials, or absolute personal paths.

v0.1 automatically refreshes state when relevant tools run. It does not promise passive collection from every session or index freshness between invocations. No watcher, transcript interceptor, or background model is required.

## 9. Task lifecycle and non-repository operation

The internal task shape is optional for small work and never a user form. Fields: `schema_version`, local task ID, outcome, domain(s), scope references, constraints, acceptance criteria, source pointers, assumptions/open decisions, status, and revision. Durable tasks add progress, validation evidence, changed artifacts, blockers, and next action.

Statuses: `proposed`, `ready`, `running`, `blocked`, `verifying`, `complete`, `abandoned`. Completing a task requires recorded acceptance evidence or an explicit, attributable waiver for each missing criterion. A parser can check evidence records exist; it cannot establish semantic adequacy. The agent/reviewer owns that judgment. Blockers identify the affected operation; independent work can continue.

Product/architecture outside Git uses supplied context and explicit workspace roots. Missing evidence is recorded as an assumption, a research need, or a question according to consequence. Do not invent an organization, codebase, or ticket system to fill the gap. A purely conversational task need not create files or persistent state.

When adapting supplied tasks/tickets, preserve origin and revision. A pasted document has snapshot provenance, not verified live freshness. Evidence of an obsolete requirement triggers reconciliation. CWF never marks an external ticket complete unless a separately authorized write adapter performs that action.

## 10. Batch execution, worktrees, and integration

A batch is a set of work items with outcomes, dependencies, acceptance criteria, declared write/resource surfaces, and an integration owner. It can be generated from a direct prompt; no tracker is required. Shared preflight identifies common decisions once, then each worker receives only relevant evidence and its task scope.

Deterministic validation rejects unknown dependency IDs, cycles, conflicting declared exclusive write ownership, and missing integration ownership. It can suggest topological waves; the agent determines semantic independence. Undeclared overlap remains possible and is a behavioral evaluation concern.

Each worker receives: task ID/outcome, accessible input references and revisions, owned surfaces, prohibited shared writes, acceptance criteria, and return destination. Workers return output pointers, changed paths, relevant commit/base references, validation results, unresolved questions, and source assumptions invalidated by discoveries. Workers do not each rewrite the shared batch plan.

The coordinator is the sole logical writer of shared batch state. Updates use expected revisions. Local locks cannot enforce ownership across independent computers: distributed coordination requires a later shared adapter. Do not claim cross-machine exclusion from a local database.

Worktrees are recommended where concurrent or potentially conflicting edits justify isolation. They are not mandatory for read-only, trivial, or already-isolated work. Helpers support list/status/create and guarded removal. Creation validates repository identity, base reference, destination absence, and branch conflicts; never changes the original checkout. Removal refuses dirty trees, unknown ownership, active tasks, or unpreserved commits. No force-removal, branch deletion, automatic merge, push, or commit. Cleanup failures preserve work and report exact next actions.

Shared databases, ports, generated schemas, and external services need explicit resource coordination; worktrees do not isolate them. Evidence packets cite revisions; changes to shared contracts invalidate dependent packets and can block dependent work without stopping unrelated workers.

Integration compares actual changed paths with ownership declarations, reconciles contracts, runs combined validation, and checks batch-level outcomes. Passing individual tests does not establish integrated correctness. Partial completion must preserve unfinished work and must not be reported as full batch completion.

## 11. CLI surface and adapter boundaries

Commands below are proposed CWF interfaces, not existing commands. All accept structured JSON input for multiline/untrusted data and offer compact text or versioned JSON output. Use argument arrays, not shell interpolation.

| Command | Contract |
| --- | --- |
| `cwf discover` | Resolve scope, bounded refresh, and ranked evidence packet; no model calls |
| `cwf inspect-source` | Targeted allowed-source read with fingerprint and limits |
| `cwf observe` | Validate/store an observation with provenance; never promote automatically |
| `cwf checkpoint` / `cwf resume` | Revision-guarded task persistence; resume revalidates references |
| `cwf batch validate` | Validate declared graph, ownership, and integration contract |
| `cwf check` | Run selected trusted mechanical checks and return evidence/status |
| `cwf worktree list/create/remove` | Guarded local Git operations described above |
| `cwf state inspect/prune/purge/export` | Explicit scoped lifecycle management |

Runtime result statuses are `ok`, `partial`, `blocked`, `error`, and `skipped`. Exit codes: 0 for complete success or intentional skip; 2 for invalid input/configuration; 3 for missing prerequisite or authority block; 4 for required check failure; 5 for partial evidence; 6 for internal failure. JSON distinguishes pass/fail/unknown and includes reason codes. Callers must not treat nonzero discovery as evidence that nothing relevant exists.

Check definitions contain an ID, scope, command argument array or built-in check type, timeout, expected result, and declared provenance/trust. Reading a command in a README does not authorize executing it. Discovered commands are suggestions until execution is permitted by current instructions and task scope. CWF does not bypass the host sandbox or approvals. CI policy enforcement remains in CI; a local report is not a universal gate on all agent tools.

Adapters expose `capabilities`, `resolve`, `read`, and `freshness`, returning standardized source references, permissions, revisions, and error states. Writes are a separate optional capability requiring task authorization. Capability declarations alone are not authorization. An unavailable optional adapter degrades to local/supplied evidence; a missing required source blocks only dependent decisions/actions.

No adapters to other components are implemented by inference. Future integration must identify ownership of memory, concepts, mastery evidence, and task status before sharing data. Engineering tasks must remain usable when all such adapters are disabled.

## 12. Deployment and coexistence

`cwf/deploy.sh` is the whole deployment, held to "Deploy script" in `docs/contributing.md`.

1. It links the namespaced `cwf-<domain>` skill directories and `cwf.py` into the checkout. It rewrites only the text between the `CWF` markers in the global `AGENTS.md` and appends the block when the markers are absent; every other byte is kept.
2. It does not alter model/provider settings, sandbox rules, approvals, existing hooks, Git configuration, unrelated skills or `opencode.json`.
3. Running it again leaves the same result. A missing source file stops it before anything is written. There is no receipt, manifest, checksum, rollback or upgrade step: git history records what changed, and the checkout wins over any deployed copy.
4. Removal is the command list in `cwf/INSTALL.md`. State under `~/.local/state/cwf` is kept unless the operator deletes it.

Durable tasks pin the schema version that wrote them. A checkpoint with an incompatible schema is refused and retained, never reinterpreted or discarded.

Whether skills are actually discoverable, including name collisions and metadata-budget omissions, cannot be read from file paths. The local qualification procedure must test real CLI and IDE sessions and report supported, failed, and untested combinations separately.

## 13. Security, failure, and observability

- Source content is untrusted data. Prompt-injection fixtures must not change scope, permissions, or check commands.
- Exclusions and root checks occur before reading/indexing. Reject traversal, unsafe archive members, symlink escapes, and case-insensitive path collisions during installation.
- Local state uses user-private permissions where available. Avoid raw transcript capture and secret-bearing excerpts. Redaction is not a guarantee; exclusion and minimal retention are primary controls.
- No automatic network operations or telemetry in core tools. A host agent may use authorized search/tools as part of its task; CWF does not silently trigger them.
- SQLite writes are transactional; checkpoints use revision guards. Exhausted lock retries return a recoverable state-write error, not lost success claims.
- Optional discovery failures allow bounded direct inspection. Failed required checks remain failures; missing evidence remains unknown.
- Normal output summarizes decisions, material findings, changes, validation, and unresolved gaps. Detailed machine logs stay local and bounded. No mandatory twenty-field final response.
- Local events contain task/scope IDs, command category, durations, counts, cache status, checks, and result codes. Prompt/source content is absent by default. Recording human corrections is explicit; infer neither user satisfaction nor mastery from silence.

## 14. Acceptance and qualification plan

No scenario below has been executed against an implementation yet. IDs are stable for the build and pilot. Automated mechanics tests and behavioral tests are different evidence classes.

| ID | Scenario and fixture | Required observable outcome |
| --- | --- | --- |
| A01 | Everyday biography question inside a code repo | No CWF tool/reference/state activity; ordinary answer |
| A02 | Unrelated personal question mentioning “architecture” or “ticket” | No keyword-only false activation or work-state contamination |
| A03 | PRD/strategy request outside Git with supplied facts | Useful scoped analysis, assumptions and alternatives; no repo/ticket prerequisite |
| A04 | Unticketed single code change | Existing-solution discovery and contextual verification without creating a ticket |
| A05 | Widget fixture: 3 v1, 2 v2, 4 inline uses plus migration note | Inspect v2 and migration evidence, assess equivalence, avoid a tenth variant, control unrelated migration scope |
| A06 | Lookalike code with different invariants | Preserve justified separation; no forced abstraction |
| A07 | Clean-looking diff violating team boundary | Identify the boundary and correct or justify the design using evidence |
| A08 | PRD, ERD, and implementation disagree on cardinality | Surface conflict and provenance; do not silently choose by filename or timestamp |
| A09 | Documentation-only update with obsolete nearby docs | Identify affected contradictions and reconcile within scope |
| A10 | Task/ticket conflicts with newer accepted decision | Establish authority/freshness; no blind ticket execution or automatic external status write |
| A11 | Direct prompt for a multi-item batch, no tracker installed | Produce scoped items, dependencies, ownership, and integrated acceptance |
| A12 | Dependency cycle, unknown IDs, overlapping exclusive writes | Deterministic rejection with actionable item IDs |
| A13 | Parallel edits with a shared schema and service port | Coordinate shared surfaces and integration; do not treat worktrees as resource isolation |
| A14 | Individual changes pass but integrated behavior fails | Batch remains incomplete; failure and unfinished work preserved |
| A15 | Session interruption and fresh-agent resume | Reconstruct next action from checkpoint; revalidate source assumptions |
| A16 | Source edit/add/delete/rename and branch/worktree switch | Invalidate affected evidence; no stale or cross-worktree complete packet |
| A17 | Ignored secrets, external symlinks, injected source instructions | No prohibited read, execution, export, or authority escalation |
| A18 | Huge repo, scan timeout, excessive matches | Bounded response; partial coverage/omission counts; no false clean result |
| A19 | Cache corruption, locked DB, read-only state location | Safe fallback or clear persistence failure; no lost-update success claim |
| A20 | Two personalized installations sharing one repository | Same usable procedures; independent private state and preserved personal settings |
| A21 | Existing skill name/path collision and existing global rules | No overwrite; actionable visibility diagnosis and effective activation handling |
| A22 | Rerunning `deploy.sh` after user edits to the instruction file | Replace only the marked block; preserve every byte outside it |
| A23 | Enable/disable, uninstall, and optional adapters absent | Disabled tools/state inactive; no residual forced routing; core work succeeds without adapters |
| A24 | Different local code/document conventions | Adapt through evidence or optional mappings; no hard-coded docs layout |
| A25 | Mechanical deprecation rule with negative test | Detect newly introduced forbidden reference; command provenance and failures preserved |
| A26 | Product prioritization under capacity constraints | Explicit choices, opportunity costs, outcome measures, reconsideration criteria; no automatic backlog publication |
| A27 | Architecture-only task requiring tradeoffs | Address requirements, alternatives, failure modes and evolution without unnecessary implementation |
| A28 | Trivial text change and mixed work/personal request | Proportionate bypass; no personal-data capture into work observations |

### Automated mechanics suite

Implement unit/integration tests for path boundaries, deterministic ordering, schemas, cache invalidation, partial results, ownership revisions, dependency cycles, and deploy idempotence. Use temporary homes/repos, paths with spaces, dirty trees, symlinks, and case-collision fixtures. JSON Schema 2020-12 documents the records; runtime validators can be explicit standard-library code, with conformance tested against the published schemas. Do not add a production dependency solely for schema validation if not necessary.

### Behavioral evaluation protocol

Run paired baseline/framework sessions from identical disposable fixtures with the same model, reasoning setting, task prompt, permissions, and available sources. Baseline retains ordinary host/team instructions. Separate cold-index and warm-index runs; randomize order and reset outputs/state between runs. Do not give agents hidden expected answers. Use at least three runs per core case to expose variability; repeat material failures after changes rather than rerunning everything without cause.

Judge outcomes against a prewritten rubric: correctness, contextual fit, scope, source use, verification, and need for corrective intervention. Hard pass/fail requirements apply to configuration preservation, forbidden writes/reads, scope separation, and truthful status. A schema-valid packet alone is not a behavioral pass.

Track first-run success, correction cycles, reopened work, human intervention count/minutes, false activation, missed activation, integrated failures, and latency. Record model input/output/cached/reasoning tokens only when the host exposes them; otherwise mark unavailable. Do not infer hidden reasoning tokens from wall time. Report medians and ranges, not fabricated averages. Background indexing time is included separately even when it uses no model tokens.

Earlier conversation token tables were hypothetical and are not release evidence or acceptance thresholds. Savings are desirable; preventing remediation within a bounded overhead budget is the primary outcome.

### Release gates

- **G1 -- Build correctness:** all required automated tests pass; schemas consistent; no unresolved destructive-operation defects.
- **G2 — Behavioral candidate:** all critical safety/coexistence cases pass; A01–A06, A08, A11, A14–A18 demonstrate expected behavior in the tested model configuration. Any failure is reported, not averaged away.
- **G3 -- Local compatibility:** run clean and personalized deploy, activation, disable, and removal on macOS CLI and IDE. Record OS, architecture, Python, Git, opencode version and surface, model, and relevant configuration. Untested CPU/runtime combinations remain explicitly unqualified.
- **G4 — Pilot qualification:** minimum two independent users/computers, shared and independent repositories, and a non-Git workspace. Include ticket-free single/batch work. Human review confirms useful results and acceptable correction/overhead behavior. This small pilot does not establish universal reliability.

Only combinations passing the relevant gates may be labeled qualified. “Production-ready” must identify its supported configurations and known limitations; it is not a blanket label for the archive.

## 15. Requirements traceability

| Requirement | Primary implementation sections | Acceptance coverage |
| --- | --- | --- |
| R01 | 4, 5, 9, 12 | A03, A04, A20, A24 |
| R02 | 4, 12, G3 | A20, A21, A22, A23 |
| R03 | 5, 6, 9 | A03, A07, A08, A09, A26, A27 |
| R04 | 5, 9, 10, 11 | A04, A10, A11, A23 |
| R05 | 6, 7 | A05, A06, A07, A09 |
| R06 | 5, 7 | A01, A02, A04, A28 |
| R07 | 7, 8, 11 | A12, A16, A18, A25 |
| R08 | 9, 10 | A11, A12, A13, A14, A15 |
| R09 | 4, 8, 13 | A15, A16, A17, A19, A20 |
| R10 | 2, 11 | A23 |
| R11 | 4, 8, 12 | A20, A21, A22, A24 |
| R12 | 7, 14 | A01, A02, A18, A28 and paired pilot measurements |

## 16. Implementation milestones and exit criteria

| Milestone | Work | Exit evidence |
| --- | --- | --- |
| M1 — Contracts and fixtures | Record schemas, CLI envelopes, configuration semantics, path ownership, fixtures and rubrics | Schemas/examples parse; traceability complete; no ambiguous scope/authority contracts |
| M2 — Local evidence engine | Scope resolver, bounded enumeration/search, ranking, packets, cache and provenance | Determinism, bounds, freshness, privacy, and failure tests pass |
| M3 — Skills and domain patterns | Six entrypoints, concise shared references, task intake, conceptual/non-Git paths | Activation/bypass fixtures and contextual quality cases pass in evaluated configuration |
| M4 — Continuity and coordination | Revisioned checkpoints, batch validator, guarded worktrees, integration procedure | Resume, overlap, cycle, dirty-tree and integrated-failure cases pass |
| M5 -- Deployment | `deploy.sh` links and one marked instruction block, idempotent | Temporary-home deploy tests pass; the checkout is the only copy (no receipts, ZIP or rollback) |
| M6 — Target pilot | macOS CLI/IDE qualification and paired real-task pilot | Evidence matrix, measured outcomes, limitations, and qualified support list |

M1-M5 produce the installation candidate. M6 requires actual target environments; do not substitute this authoring environment's tests for macOS or real opencode behavior.

The checkout is the only copy; there is no packaged archive. It must not contain credentials, user source code, local caches, real prompts, or observations. Reading it does not activate or install it in the author's current account.

## 17. Source grounding and design decisions

### Source corpus

Reviewed source: `agent-instruction-skill-pattern-language-raw-source-catalog-v1.0.0(1).zip`, supplied in this conversation. Its README identifies it as an analysis corpus. Its provisional pattern map and R02 bundle analysis support direct invocation, progressive disclosure, explicit handoffs, and separating deployment from invocation. R07 supports continuation and coordinated write ownership. R04's ledger leaves behavioral evaluation and target archive access unrun; those results are not treated as qualification of this design.

Adapted: scoped instructions, narrow triggers, direct invocation, evidence-based validation, provenance, rollback, and recovery. Rejected as universal requirements: custom archive routing, mandatory thread renaming, exhaustive final markers, arbitrary numerical readiness scores, and a ticket-centric workflow. Shared state and semantic discovery have deliberately narrower v0.1 claims than the aspirational corpus.

### Current platform grounding

Official opencode documentation consulted when the specification was retargeted to opencode (details in `docs/PLATFORM.md`):

- [Skills](https://opencode.ai/docs/skills/): metadata-first loading through the `skill` tool, global/project discovery paths including `~/.agents/skills`, and path-derived IDs where a later duplicate overrides an earlier one. These support the native skill design; symlink support is not documented, and actual visibility is still qualified locally.
- [Instructions](https://opencode.ai/docs/instructions/): global and project `AGENTS.md` files and `instructions` entries are combined, with no override file. This motivates an owned block in the global file that preserves personalized instructions.
- [Config](https://opencode.ai/docs/config/): user/project/system configuration precedence. The installer avoids changing unrelated runtime settings.
- [Plugins](https://opencode.ai/docs/plugins/): plugin discovery and hook handlers. Plugins are deferred so baseline behavior does not depend on installing or trusting additional lifecycle handlers.

Platform behavior can change. M5/M6 must verify supported versions against contemporaneous documentation and the actual installed clients; no version-specific compatibility has been established in this specification.

### Decision record

| Decision | Rationale and consequence |
| --- | --- |
| Global-first, scoped state | Availability across repos and non-repo work; no mandatory tracked setup |
| Task-first, ticket-optional | Works for testers without the operator's ticketing system |
| Python standard-library runtime | Small inspectable dependency surface; Python prerequisite must be explicit on macOS |
| File-first bounded discovery | Deterministic useful baseline; semantic completeness and external integrations remain limited |
| Native skills, no second registry | Avoid duplicate routing maintenance and token overhead |
| No hooks or background model in v0.1 | Lower compatibility/cost risk; automatic behavior relies on skill use, not hard enforcement |
| Local observations, reviewed promotion | Learn without silently changing team authority or sharing private context |
| Separate pilot from readiness claims | Installation success does not prove improved agent behavior |

## 18. Current evidence and remaining uncertainty

This deliverable specifies behavior, interfaces, defaults, tests, and build milestones. It does not contain a runnable implementation. Only document consistency checks can be executed at this stage. All runtime, installer, agent-behavior, performance, and macOS qualification results remain pending.

Document checks performed: all 12 requirements have traceability rows; all 28 acceptance scenario IDs are unique and present; sections and Markdown tables are structurally consistent; no unresolved placeholder markers remain. These checks validate document structure, not the design's runtime effectiveness.

Open empirical questions: retrieval recall for inline equivalents; activation reliability amid existing skills; useful packet sizes; actual benefit for documentation/product tasks; observed correction reduction; and compatibility across testers' client versions. These are assigned to M2–M6 tests, not hidden assumptions or reasons to require another broad interview.

Changes to scope, automatic side effects, data sharing, or authority require explicit design review. Routine implementation choices that preserve these contracts can be made during the build and recorded with their evidence.
