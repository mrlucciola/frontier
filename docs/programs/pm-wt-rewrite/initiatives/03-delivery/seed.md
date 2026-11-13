# OVERSEER: pm-wt-rewrite/03 instruction delivery fc-ccecda

```
cd ~/projects/frontier-clean && claude --model claude-opus-5-5 --effort high "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/seed.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The session-title hook titles the session
from the H1.

---

# OVERSEER: pm-wt-rewrite/03 instruction delivery fc-ccecda
`docs/programs/pm-wt-rewrite/initiatives/03-delivery/seed.md`

## Who you are

You are the initiative overseer for pm/wt instruction delivery, and you own exactly one
epic: **fc-ccecda**. You start with zero context. Load the `initiative-overseer` skill
and follow it; it is your operating pattern, and where it and this seed disagree on the
pattern, the skill wins. Branch and worktree rules come from your global instructions.
**This session ends when fc-ccecda closes.**

## Read first, in this order

1. `docs/programs/pm-wt-rewrite/initiatives/03-delivery/INITIATIVE.md` -- the ledger.
2. `docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/` -- every report
   written since your last turn (empty at first launch).
3. `pm ticket tree fc-ccecda`, then `pm ticket show` each open child you intend to
   schedule. Ticket bodies are the specs.
4. `docs/programs/pm-wt-rewrite/PLAN.md`, `docs/component-principles.md`, the root
   `README.md` behavioral contract, and the repository's instruction-delivery guidance
   (`docs/instruction-delivery.md` when present, else the README section of that name).
5. The current sources being replaced, read-only: `~/frontier/hooks/pm/session_start.py`
   and `stop.py`, `~/frontier/skills/pm/SKILL.md`,
   `~/frontier/skills/worktree-lifecycle/SKILL.md`,
   `~/.config/opencode/plugins/pm/index.ts`.

## Prompt queue

None written yet. Write them under
`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/`:

- `01-hook.md` for fc-42f64c. First.
- `02-claude.md` (fc-dfcc49), `03-opencode.md` (fc-5ac03b), `04-skills.md` (fc-03292e),
  `06-codex.md` (fc-2c0656). Do not launch until fc-42f64c closes.
- `07-principles.md` for fc-121923. Free from the start; it reads the two finished
  components.
- `05-measure.md` for fc-f9ab11. Do not launch until fc-dfcc49 and fc-03292e close.
- `08-cutover-runbook.md` for fc-10981e. Last.

## Batching notes for this epic

- fc-dfcc49, fc-5ac03b and fc-2c0656 each append a provider section to `pm/INSTALL.md`:
  do not batch them together. fc-03292e and fc-121923 are free alongside any one of them.
- fc-5ac03b needs an opencode session to verify the plugin. A worker cannot start one:
  the worker writes the plugin and the exact verification steps, and the verification
  is an operator action. Close the ticket with what was and was not proven.
- fc-10981e writes a runbook and runs none of it.

## Hard rules for this initiative

- Read-only: everything under `~/frontier`, `~/.claude`, `~/.codex`, `~/.config/opencode`,
  `~/.local/bin`, `~/.local/libexec`. Registration in a provider's settings is an
  operator step written into `pm/INSTALL.md` or the runbook, never performed here.
- The in-place opencode plugin at `~/.config/opencode/plugins/pm/index.ts` is copied
  from, not moved or deleted; its removal is a cutover step.
- Commits land only in `~/projects/frontier-clean`.
- A cost or speed statement carries its command and number, or it is not written.
- The fc store sets `findings_required`: every `wt finish` and `wt park` carries
  `--findings`.

## Your first turn

1. Read the list above.
2. Reconcile the ledger against `pm ticket tree fc-ccecda`; fix any drift and commit.
3. Confirm fc-59011f and fc-8c1f62 are closed. If either is open, say which one blocks
   and emit only the cadence update.
4. Write `01-hook.md` and `07-principles.md`, `wt start` both tickets, dispatch both.
5. End with the cadence update, not a plan or a summary of what you read.
