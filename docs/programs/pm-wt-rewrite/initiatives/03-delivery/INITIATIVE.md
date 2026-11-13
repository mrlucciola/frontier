# INITIATIVE: pm/wt instruction delivery (fc-ccecda)

## State

```text
fc-ccecda  P2  open          pm/wt instruction delivery: hook-injected guidance, skills, opencode, principles, cutover runbook [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-42f64c  P2  open          pm hook command: session-start, prompt and stop events from one provider-neutral source
  fc-dfcc49  P2  open          pm Claude integration: hook adapter, registration fragment, setup steps
  fc-5ac03b  P2  open          pm opencode integration: plugin owned by the component, calling pm hook
  fc-03292e  P2  open          pm and wt skills rewritten for progressive discovery: orientation, route table, verb cards
  fc-f9ab11  P2  open          Measure pm/wt instruction cost before and after hook delivery
  fc-2c0656  P2  open          Codex: record what lifecycle hooks exist and wire pm guidance to what is supported
  fc-121923  P2  open          Finalize component principles and the behavioral contract from the pm and wt builds
  fc-10981e  P2  open          Cutover runbook: operator steps to switch pm and wt to frontier-clean and retire the frontier packages
```

## Next batch

fc-42f64c and fc-121923, once fc-59011f and fc-8c1f62 are closed.

## Owed operator actions

None yet. Expected by the end: the opencode plugin verification, and the cutover
runbook itself.

## Facts not to re-derive

- **What exists today.** Claude: `~/frontier/hooks/pm/session_start.py` injects
  `pm ticket summary` when cwd is inside a repo with `.pm/`; `stop.py` blocks once on a
  claim this session holds. opencode: a plugin written in place at
  `~/.config/opencode/plugins/pm/index.ts` (207 lines) that reimplements both in
  TypeScript, including its own parse of `tickets.jsonl`, and is registered by absolute
  path in `opencode.json` under `plugins`.
- **Skill sizes today.** `~/frontier/skills/pm/SKILL.md` 89 lines,
  `~/frontier/skills/worktree-lifecycle/SKILL.md` 120 lines. Both use if-provider blocks.
- **Session token.** A claim is attributed with `sha256(session id)[:8]`. The stop event
  must compute the same token the claim verb does; reuse pm's function, do not copy it.
- **Not verified.** Whether Codex exposes session-start, prompt or stop events, and
  where opencode discovers skills. fc-2c0656 and fc-5ac03b each establish theirs from
  the installed client before writing anything that depends on it.
- **Frontier references to pm and wt** that the cutover runbook must account for were
  found in: `deploy/registry.json`, `posture/posture.json` and its rendered outputs,
  `hooks/pm/stop.py`, `hooks/core-hooks/session-title.py`,
  `hooks/core-hooks/config/deprecated-sources.json`, `tools/gen_instructions.py`,
  `tools/audit/retired_roots.py` and its allowlist, `deploy/gitcommit.py`,
  `deploy/gitfault.py`, `skills/pm/SKILL.md`, `skills/worktree-lifecycle/SKILL.md`,
  `runtime-tools/session-cost/`. That list came from one search for the install paths;
  fc-10981e re-runs it and records each hit as `file:line`.
