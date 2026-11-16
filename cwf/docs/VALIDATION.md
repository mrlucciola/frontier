# Validation — CWF 0.1.0

Date: 2026-11-07. Status: **tested installation candidate; target qualification pending**.

Implementation and packaging deliverables for M1–M5 are present. This does not mean every behavioral acceptance gate passed: M3 implicit activation/contextual-quality qualification remains incomplete. M6 instructions and pilot rubrics are supplied, not executed. No installation was made into the authoring session's live configuration.

The installer, its tests and the results below that cover installation, upgrade, rollback, toggles and uninstall are historical: fc-6441eb removed that installer, and `cwf/deploy.sh` replaced it.

## Executed checks

| Check | Result | Evidence and limits |
| --- | --- | --- |
| Automated mechanics | 65 passed, 0 failed, 1 skipped; 66 total | `tests/test_cwf.py` |
| Published schema equality and built-in validation | Passed | Runtime contracts equal packaged JSON schemas; positive/negative contract tests |
| Independent JSON Schema validator | Skipped | Optional `jsonschema` development dependency unavailable; not silently installed |
| Native skill structure | 6 passed, 0 failed | All six staged skills passed the skill-authoring validator; this is not live visibility or activation evidence |
| Explicit build-skill exercise | Limited pass | Fresh agent inspected widget utility/migration, reused v2, and kept unrelated callers unchanged; structural checks and Node execution of transformed fixture code; no TypeScript compiler check |
| Explicit docs-skill exercise | Partial | Fresh agent surfaced accepted PRD versus draft ERD conflict; absent implementation source was reported, so full three-source A08 remains unqualified |

The automated suite covers discovery limits and ordering, content invalidation, ignored files, secrets/symlinks, scope roots, stale observations, corruption fallback, checkpoint revisions and evidence requirements, batch cycles/ownership collisions, command timeout/output limits, worktree ownership and dirty/active-task refusal, installation coexistence, upgrade/rollback, toggles, uninstall, interruption recovery, and later user edits.

Independent review found issues in targeted-read boundaries, scope-root narrowing, descendant worktree tasks, equivalent write-path normalization, instruction preservation across management operations, and interrupted-transaction handling. These were fixed and regression tests added. A separate review exercised process interruption at three write boundaries for initial install, disable, uninstall, and rollback. The final receipt-recovery and pending-journal fixes were verified by the automated suite; the reviewer exhausted its usage allowance before independently rechecking those final fixes.

## Acceptance coverage

“Mechanics passed” below is deliberately narrower than a full behavioral scenario pass. No implicit-routing scenario is certified by a file existing or a schema validating.

| Scenario | Status in authoring environment |
| --- | --- |
| A01 everyday question | Untested implicit bypass; instructions supplied |
| A02 misleading personal keywords | Untested implicit bypass |
| A03 product work outside Git | Non-Git tool mechanics passed; product reasoning untested |
| A04 unticketed code | Limited explicit-skill exercise passed |
| A05 widget reuse | Retrieval regression and limited explicit-skill exercise passed; implicit activation untested |
| A06 different invariants | Fixture/rubric supplied; behavioral evaluation untested |
| A07 team boundary | Procedure supplied; behavioral evaluation untested |
| A08 PRD/ERD/runtime conflict | Partial explicit exercise; runtime source unavailable |
| A09 obsolete neighboring docs | Partial overlap with docs exercise; full reconciliation untested |
| A10 task versus accepted decision | Freshness/attribution mechanics passed; behavioral arbitration untested |
| A11 unticketed batch | Batch contract/topological mechanics passed; prompt-to-batch behavior untested |
| A12 cycles and overlaps | Mechanics passed |
| A13 shared schema/port | Shared-resource rejection passed; live parallel integration untested |
| A14 integrated failure | Required-check and completion-evidence mechanics passed; multi-agent integration scenario untested |
| A15 interruption/resume | Checkpoint revisions/freshness/pinning passed; fresh-session behavioral resume untested |
| A16 changes and worktrees | Add/edit/delete and worktree isolation passed; full branch-switch matrix untested |
| A17 secrets/symlinks/injection | Read-boundary mechanics passed; model resistance to injected prose untested |
| A18 excessive input | File/byte/result bounds and partial reporting passed; real huge-repo latency unmeasured |
| A19 unavailable state | Corruption fallback and schema refusal passed; exhaustive locked/read-only combinations untested |
| A20 independent users | Temporary-home coexistence/isolation passed; two real computers untested |
| A21 collisions/global rules | Mechanics passed; actual client visibility untested |
| A22 failed upgrade/later edits | Recovery and preservation regressions passed |
| A23 toggles/uninstall/no adapters | Mechanics passed; already-loaded model instructions cannot be retracted |
| A24 varying conventions | Config/scope mechanics passed; real-repository adaptation untested |
| A25 deprecation check | Positive/negative/unknown checks and command provenance mechanics passed |
| A26 prioritization | Pattern/protocol supplied; behavioral evaluation untested |
| A27 architecture tradeoffs | Pattern/protocol supplied; behavioral evaluation untested |
| A28 trivial/mixed request | Proportionate routing instructions supplied; implicit behavior untested |

## Reproduce and qualify

From the extracted package:

```sh
python3 -B -m unittest discover -s tests -v
```

Tests create disposable homes/repositories, including paths containing spaces. They do not use real opencode configuration. Git is required for worktree cases. Python runtime has no third-party dependencies; the optional cross-validator is reported as skipped if absent.

Read `docs/DEVIATIONS.md` before interpreting coverage. Retrieval is bounded lexical discovery, not semantic clone detection. Warm cache matches still reread bounded sources. Global instruction and skill metadata overhead is small but nonzero even for bypassed requests; actual token counts, activation reliability, remediation savings, and latency distributions are unmeasured. No estimates are presented as release evidence.

Deploy with `cwf/deploy.sh` on each target Mac, then follow `docs/PILOT.md`. Mac hardware/OS, CLI/IDE integration, managed policies, model behavior, cross-user operation, and paired cost/quality results remain untested here. Qualify only configurations actually exercised.
