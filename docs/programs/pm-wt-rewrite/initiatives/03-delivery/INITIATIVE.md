# INITIATIVE: pm/wt delivery (fc-ccecda)

## State

```text
fc-ccecda  P2  open          pm/wt delivery: wt help that teaches, cost measurement, Codex, principles, cutover runbook [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-42f64c  P2  closed        pm hook command: session-start, prompt and stop events from one provider-neutral source
  fc-dfcc49  P2  closed        pm Claude integration: hook adapter, registration fragment, setup steps
  fc-5ac03b  P2  closed        pm opencode integration: plugin owned by the component, calling pm hook
  fc-03292e  P2  open          wt instruction delivery: help that teaches, plugin hints, no skill
  fc-f9ab11  P2  open          Measure pm/wt instruction cost before and after hook delivery
  fc-2c0656  P2  open          Codex: record what lifecycle hooks exist and wire pm guidance to what is supported
  fc-121923  P2  open          Finalize component principles and the behavioral contract from the pm and wt builds
  fc-10981e  P2  open          Cutover runbook: operator steps to switch pm and wt to frontier-clean and retire the frontier packages
```

## Next batch

fc-03292e, fc-121923 and fc-2c0656, once fc-2a6562 and fc-262fa8 are closed.

## Owed operator actions

None yet. Expected by the end: the Codex probe, and the cutover runbook itself.

## Facts not to re-derive

- **Reduced 2026-11-14.** The pm redesign took the hook command and the Claude and
  opencode wiring into its own ticket, fc-a761be, and removed the pm skill. The three
  tickets for those here are closed as superseded. Nothing was built under them.
- **What exists before cutover.** Claude: `~/frontier/hooks/pm/session_start.py`
  injects `pm ticket summary` when the working directory is inside a repo with `.pm/`;
  `stop.py` blocks once on a claim this session holds. opencode: a plugin written in
  place at `~/.config/opencode/plugins/pm/index.ts`, registered by absolute path in
  `opencode.json` under `plugins`. Skills: `~/frontier/skills/pm/SKILL.md` 89 lines,
  `~/frontier/skills/worktree-lifecycle/SKILL.md` 120 lines.
- **What replaces it.** `pm hook session-start|prompt|stop`, registered from
  `pm/config/claude/hooks.json`, and `pm/hooks/opencode/pm.ts`. No skill for pm or wt.
- **Not verified.** Whether Codex exposes session-start, prompt or stop events.
  fc-2c0656 establishes it from the installed client before writing anything that
  depends on it.
- **Stores at cutover.** Ten are registered in `~/frontier/runtime-tools/pm/stores.json`;
  `~/claude` is frozen; frontier lists `cl` as a legacy prefix; this repository's store
  sets three write-reduction keys the new pm does not use; only lai sets `gate`.
- **Frontier references to pm and wt** that the cutover runbook must account for were
  found in: `deploy/registry.json`, `posture/posture.json` and its rendered outputs,
  `hooks/pm/stop.py`, `hooks/core-hooks/session-title.py`,
  `hooks/core-hooks/config/deprecated-sources.json`, `tools/gen_instructions.py`,
  `tools/audit/retired_roots.py` and its allowlist, `deploy/gitcommit.py`,
  `deploy/gitfault.py`, `skills/pm/SKILL.md`, `skills/worktree-lifecycle/SKILL.md`,
  `runtime-tools/session-cost/`, and the core-hooks policies `continuity_nudge.py`,
  `done_gate.py`, `git_branch_guard.py`, `destructive_ops.py`. That list came from two
  searches on 2026-11-12; fc-10981e re-runs them and records each hit as `file:line`.
