# INITIATIVE: pm/wt delivery (fc-ccecda)

Status: closed 2026-11-15. Cutover is operator-run from
[CUTOVER.md](/docs/programs/pm-wt-rewrite/CUTOVER.md).

## State

```text
fc-ccecda  P2  closed        pm/wt delivery: wt help that teaches, cost measurement, Codex, principles, cutover runbook [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-42f64c  P2  closed        pm hook command: session-start, prompt and stop events from one provider-neutral source
  fc-dfcc49  P2  closed        pm Claude integration: hook adapter, registration fragment, setup steps
  fc-5ac03b  P2  closed        pm opencode integration: plugin owned by the component, calling pm hook
  fc-03292e  P2  closed        wt instruction delivery: help that teaches, plugin hints, no skill
  fc-f9ab11  P2  closed        Measure pm/wt instruction cost before and after hook delivery
  fc-2c0656  P2  closed        Codex: record what lifecycle hooks exist and wire pm guidance to what is supported
  fc-121923  P2  closed        Finalize component principles and the behavioral contract from the pm and wt builds
  fc-10981e  P2  closed        Cutover runbook: operator steps to switch pm and wt to frontier-clean and retire the frontier packages
```

## Next batch

None. The epic is closed.

## Owed operator actions

None for this epic. The cutover is the operator's: CUTOVER.md, beginning at its
triggers and step 0. Its triggers include fr-453840 and fc-5e5a20. The Codex probe
(`pm/INSTALL.md` "Codex" > "Probe") is one of its steps.

## Findings routed

- fc-53fc6e: pm/AGENTS.md records no two-verb shared helpers (from fc-121923).
- fc-5e5a20 (P1): a nested pm store with config.json but no log resolves to its
  parent's log (from the fc-10981e review). It is a cutover trigger.
- Notes on fc-10981e, all folded into CUTOVER.md: the instruction map, the cost
  baseline, the stale deployed worktree-lifecycle skill, and Codex probe ordering.

## Not proven

- Codex hooks in a live session. Plain-text `SessionStart` stdout and the events
  under `codex exec` both wait on the probe.
- wt failure lines with long real paths against the 400-byte ceiling. The test
  measures templates with stand-ins.
- The runbook itself. Nobody has run it. Each of its unchecked points is marked
  "I have not" where it applies.

## Facts not to re-derive

- **Review history of CUTOVER.md.** The opus check returned BROKEN, BROKEN, PARTIAL,
  then CONFIRMED (`reports/05-review*.md`). Step 4A was redesigned as operator-only,
  with the frontier reader changes prepared and parked beforehand in step 0, so that
  no agent session runs inside the cutover window.
- **Scratch git repos.** The hook refuses an absolute-path `git init`; its remedy is
  `git init -b main .tmp/<name>` from the main checkout, then `rev-parse
  --show-toplevel` before the next git command.
- **Codex facts.** These come from the codex-cli 0.167.0 binary's embedded schemas.
  `SessionStart`, `UserPromptSubmit` and `Stop` exist with Claude's key names, so
  `pm/config/codex/hooks.json` calls `pm hook` with no adapter.
- **Worker budgets ran over.** 04-measure used 117 tool calls, 05-a 75 and 05-b 105,
  against a budget of 40. A large runbook should be split into more than two parts.
