# Shared reasoning patterns

Use only questions relevant to the current task. None grants tool permission.

| Pattern | Evidence and decision | Counterexample / completion |
| --- | --- | --- |
| P01 Frame | Outcome, constraints, invariants, non-goals | Do not turn a small edit into an initiative; confirm requested behavior |
| P02 Discover | Existing implementation/artifacts, representative consumers, tests | A new name does not imply new behavior; cite candidates inspected |
| P03 Equivalence | Preconditions, side effects, error semantics, reasons to change | Similar arithmetic can encode different business rules; reuse only when justified |
| P04 Authority | Source, acceptance provenance, revision, freshness | Newest document need not be authoritative; surface conflicts |
| P05 Context | Relevant team/domain conventions and tooling | Consistency does not justify broken invariants; explain departures |
| P06 Simplicity | Smallest adequate change and meaningful alternatives | DRY is not minimizing lines; avoid unnecessary coupling |
| P07 Traceability | Requirements/design/docs/code agree on affected behavior | Passing tests can encode the wrong requirement; resolve contradictions |
| P08 Scope | Requested outcome, allowed mutations, dependent work | Finding duplication does not authorize global refactoring |
| P09 Ownership | Dependencies, exclusive write surfaces, shared services | Different tickets/worktrees may still conflict; integrate explicitly |
| P10 Verify | Counterexamples, acceptance checks, integrated behavior | A checklist or self-assessment is not outcome evidence |
| P11 Recover | Accessible sources, revisions, completed/remaining work | Chat history alone is not a durable handoff; revalidate on resume |
| P12 Promote | Observed/inferred/accepted distinction and attribution | Repeated agent claims do not become team policy; use review process |

For product/strategy: distinguish diagnosis from solution; compare opportunity costs, stakeholders, capacity assumptions, measurable outcomes, and reconsideration criteria.
For architecture: cover relevant workload/quality needs, consistency, failures, security boundaries, operability, migration, and reversibility.
For documentation: establish audience, canonical sources, intended versus observed behavior, terminology, and affected links.
For planning: choose the next executable slice, identify dependencies and review points, and avoid parallel work with uncoordinated shared resources.
