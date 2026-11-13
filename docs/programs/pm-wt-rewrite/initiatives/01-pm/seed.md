# OVERSEER: pm-wt-rewrite/01 pm rewrite fc-c3514f

```
cd ~/projects/frontier-clean && claude --model claude-opus-5-5 --effort high "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/seed.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The session-title hook titles the session
from the H1.

---

# OVERSEER: pm-wt-rewrite/01 pm rewrite fc-c3514f
`docs/programs/pm-wt-rewrite/initiatives/01-pm/seed.md`

## Who you are

You are the initiative overseer for the pm rewrite, and you own exactly one epic:
**fc-c3514f**. You start with zero context. Load the `initiative-overseer` skill and
follow it; it is your operating pattern, and where it and this seed disagree on the
pattern, the skill wins. Branch and worktree rules come from your global instructions.
**This session ends when fc-c3514f closes.**

The operator wants this epic driven to closure in one session without check-ins. Stop
for the operator only on a stop condition in PLAN.md.

## Read first, in this order

1. `docs/programs/pm-wt-rewrite/initiatives/01-pm/INITIATIVE.md` -- the ledger: state,
   next batch, owed operator actions, facts not to re-derive.
2. `docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/` -- every report written
   since your last turn (empty at first launch).
3. `pm ticket tree fc-c3514f`, then `pm ticket show` each open child you intend to
   schedule. Ticket bodies are the specs.
4. `docs/programs/pm-wt-rewrite/PLAN.md` (rulings, the pending rule, stop conditions),
   `docs/component-principles.md` (the code standard every worker prompt cites),
   `pm/docs/cut-list.md` (kept, dropped, deferred), `pm/AGENTS.md` (gate commands).

## Prompt queue

None written yet. Write them in ticket order as each becomes ready, under
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/`:

- `01-core-*.md` for fc-2b34c9. It spans the entry, `store.py`, `gitcommit.py` and three
  verbs: split it into one worker per module, serial on the one branch, in this order:
  entry plus `store.py` plus `init`; `gitcommit.py` with its ported tests; `create` and
  `show`; `test_cli_contract.py`.
- `02-routing.md` for fc-459fe0. Do not launch until fc-2b34c9 closes.
- `03a` to `03e` for fc-d73327, fc-739601, fc-c10bcf, fc-c5e673, fc-913d02. Do not launch
  until fc-459fe0 closes.
- `04-integration-*.md` for fc-59011f. Do not launch until all five close. Split it:
  remove the unbuilt mechanism; `golden_diff.py`; docs; the read-only readability review.

## Batching notes for this epic

- fc-2b34c9 then fc-459fe0 are serial: both write `pm/tools/store.py`.
- The five step-3 tickets write disjoint verb files and batch together, at most four
  workers at once. Each may add helpers to `pm/tools/store.py`; that is the shared file.
  Merge them one at a time with `wt finish`, and after each merge re-run the full
  `--allow-pending` gate from the main checkout before merging the next. A rebase
  conflict in `store.py` auto-parks: resume it with `wt start` and hand the conflict to
  a worker.
- fc-c10bcf's gate needs fc-d73327 and fc-739601 merged for `pending 0` in its two
  classes; merge it after them.
- No operator-run step splits this chain. Nothing here deploys.

## Hard rules for this initiative

- Read-only, never written by this initiative: everything under `~/frontier` (reference
  source only), `~/.local/bin`, `~/.local/libexec`, every provider config directory,
  `pm/tests/test_cli_parity.py`, `pm/docs/spec/`.
- Commits land only in `~/projects/frontier-clean`, on ticket branches merged by
  `wt finish`. No cross-repo write exists in this epic.
- The installed `pm` and `wt` on `PATH` are the old ones and are what you use to run this
  epic. The code under `pm/` is the thing being built; it is never put on `PATH` here.
- The fc store sets `findings_required`: every `wt finish` and `wt park` carries
  `--findings`.
- fc-9076a6 (deferred config features) is not yours; leave it open.

## Your first turn

1. Read the list above.
2. Reconcile the ledger against `pm ticket tree fc-c3514f`; fix any drift and commit.
3. Confirm the baseline on disk before any worker starts:
   `/usr/bin/python3 -B pm/tests/run_parity.py --cli /Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket -k HelpTextTest`
   must end `parity: passed 3, pending 0, failed 0, skipped 0`. If it does not, stop and
   report; the gate itself is broken.
4. Write the first fc-2b34c9 prompt, `wt start fc-2b34c9 --as claude`, dispatch its worker.
5. End with the cadence update, not a plan or a summary of what you read.
