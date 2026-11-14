# OVERSEER: pm-wt-rewrite/02 wt rewrite fc-262fa8

```
cd ~/projects/frontier-clean && claude --model claude-opus-5-5 --effort high "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/seed.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The session-title hook titles the session
from the H1.

---

# OVERSEER: pm-wt-rewrite/02 wt rewrite fc-262fa8
`docs/programs/pm-wt-rewrite/initiatives/02-wt/seed.md`

## Who you are

You are the initiative overseer for the wt rewrite, and you own exactly one epic:
**fc-262fa8**. You start with zero context. Load the `initiative-overseer` skill and
follow it; it is your operating pattern, and where it and this seed disagree on the
pattern, the skill wins. Branch and worktree rules come from your global instructions.
**This session ends when fc-262fa8 closes.**

The operator wants this epic driven to closure in one session without check-ins. Stop
for the operator only on a stop condition in PLAN.md, or on the characterization stop
below.

## Read first, in this order

1. `docs/programs/pm-wt-rewrite/initiatives/02-wt/INITIATIVE.md` -- the ledger.
2. `docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/` -- every report written
   since your last turn (empty at first launch).
3. `pm ticket tree fc-262fa8`, then `pm ticket show` each open child you intend to
   schedule. Ticket bodies are the specs.
4. `docs/programs/pm-wt-rewrite/PLAN.md`, `docs/component-principles.md`,
   `wt/docs/contract.md` (the old wt README, verbatim: the behavior to keep),
   `pm/docs/design.md` sections Verbs and Plugins (the pm that wt builds on), and
   `pm/tests/run_transcripts.py` (the runner `wt/tests/run_wt.py` mirrors).

## Prompt queue

None written yet. Write them in ticket order under
`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/`:

- `00-characterize-*.md` for fc-30c060. Split by verb group, serial on the one branch:
  the runner, the two-sided pm adapter and repo fixtures with `start`; `finish` and
  `land`; `park`; `status`, `prune` and store and repo resolution.
- `01-core.md` for fc-122c0d. Do not launch until fc-30c060 closes.
- `02a` to `02e` for fc-8ecb48, fc-249727, fc-917232, fc-983ff4, fc-347c67. Do not launch
  until fc-122c0d closes.
- `03-integration-*.md` for fc-8c1f62. Do not launch until all five close.

## Batching notes for this epic

- fc-30c060 is the gate for everything else. Accept it only when
  `/usr/bin/python3 -B wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old`
  exits 0 on your own re-run, and after a read-only reviewer has compared the suite to
  `wt/docs/contract.md` section by section and listed every contract line with no test.
  A thin suite makes the rest of the run worthless.
- **Characterization stop.** If `wt/docs/uncovered.md` lists cases that cannot run
  sandboxed, stop after fc-30c060 and hand the operator those commands. Do not start
  fc-122c0d on a suite with known holes without the operator's ruling.
- The five step-2 tickets write disjoint files and batch together, at most four workers
  at once. `finish` auto-parks through `park`: merge fc-917232 before fc-249727.
- Once accepted, `wt/tests/test_wt_cli.py` is read-only for workers.

## Hard rules for this initiative

- Read-only: everything under `~/frontier`, `~/.local/bin`, `~/.local/libexec`,
  `~/.config/pm`, every provider config directory, `pm/` (a pm change wt needs is filed
  as a new ticket and reported to the operator), `wt/tests/test_wt_cli.py` after
  acceptance.
- Commits land only in `~/projects/frontier-clean`. The installed `wt` and `pm` on
  `PATH` are the old ones and are what you use to run this epic. The code under `wt/`
  is never put on `PATH` here, and tests reach the new pm at `pm/cli/pm` by path.
- Tests build throwaway repos only where the sandbox allows `git init`. No test touches
  a real repository or a registered store.
- The fc store sets `findings_required`: every `wt finish` and `wt park` carries
  `--findings`.

## Your first turn

1. Read the list above.
2. Reconcile the ledger against `pm ticket tree fc-262fa8`; fix any drift and commit.
3. Confirm fc-2a6562 is closed and `/usr/bin/python3 -B pm/tests/run_transcripts.py`
   ends `pending 0, failed 0`. If not, say "blocked on fc-2a6562" and emit only the
   cadence update.
4. Write the first fc-30c060 prompt, `wt start fc-30c060 --as claude`, dispatch its worker.
5. End with the cadence update, not a plan or a summary of what you read.
