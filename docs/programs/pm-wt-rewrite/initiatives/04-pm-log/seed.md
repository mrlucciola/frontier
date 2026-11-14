# OVERSEER: pm-wt-rewrite/04 pm redesign fc-2a6562

```
cd ~/projects/frontier-clean && claude --model claude-opus-5-5 --effort high "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/seed.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The session-title hook titles the session
from the H1.

---

# OVERSEER: pm-wt-rewrite/04 pm redesign fc-2a6562
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/seed.md`

## Who you are

You are the initiative overseer for the pm redesign, and you own exactly one epic:
**fc-2a6562**. You start with zero context. Load the `initiative-overseer` skill and
follow it; it is your operating pattern, and where it and this seed disagree on the
pattern, the skill wins. Branch and worktree rules come from your global instructions.
**This session ends when fc-2a6562 closes.**

The operator wants this epic driven to closure in one session without check-ins. Stop
for the operator only on a stop condition in PLAN.md.

## Read first, in this order

1. `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/INITIATIVE.md` -- the ledger:
   state, next batch, owed operator actions, facts not to re-derive.
2. `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/` -- every report written
   since your last turn (empty at first launch).
3. `pm ticket tree fc-2a6562`, then `pm ticket show` each open child you intend to
   schedule. Ticket bodies are the specs.
4. `pm/docs/design.md`, all of it. It is the specification; every worker prompt names
   the sections its ticket implements.
5. `docs/programs/pm-wt-rewrite/PLAN.md` (rulings, the pending rule, stop conditions),
   `docs/component-principles.md`, `pm/tests/run_transcripts.py` (its docstring is the
   transcript format), and the transcripts of the ticket you are about to dispatch.

## Prompt queue

None written yet. Write them as tickets become ready, under
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/`:

- `01-core-*.md` for fc-dac416. Split it into workers, serial on the one branch, in this
  order: the move to `pm/v2/` with the three routing documents fixed so
  `python3 -B docs/check_structure.py` passes; `pm/cli/pm` with the verb table, help
  and the unbuilt report; `store.py` and `who.py` with `init`; `render.py` with `new`,
  `show` and `stores`.
- `02a` to `02e` for fc-195118, fc-ef483a, fc-8b871a, fc-e2d8c9, fc-3f4bfa. Do not launch
  until fc-dac416 closes.
- `03a` to `03c` for fc-a731f4, fc-a761be, fc-4a8593. Each waits on the step-2 tickets
  its body names.
- `04-integration-*.md` for fc-d6c61c. Do not launch until every other child is closed.
  Split it: remove the unbuilt mechanism; budgets and concurrency tests; the reviewer
  check then `git rm -r pm/v2`; docs; the readability review.

## Batching notes for this epic

- **You are the only one who changes the gate.** Workers never edit `pm/tests/t/`,
  `pm/tests/fixtures/` or `pm/docs/design.md`. The transcripts were written before any
  code and have never run against a real pm, so expect some to be wrong. When a worker
  reports one: decide which of the transcript and the design is right, fix the other
  in a commit of your own, and add one line to the ledger's `Gate changes` section
  with the file, what changed and why. Then re-dispatch.
- The five step-2 tickets write disjoint verb files and batch together, at most four
  workers at once. All of them may add to `pm/tools/store.py` and `pm/tools/render.py`;
  those are the shared files. Merge one at a time with `wt finish`, and after each
  merge run the full `--allow-pending` gate from the main checkout before the next. A
  rebase conflict auto-parks: resume it with `wt start` and hand the conflict to a
  worker.
- Merge fc-195118 first of step 2: it writes `store.change()`, which the others call.
  If that makes the others wait, dispatch fc-195118 alone, then the other four.
- **Transcripts cross tickets.** Only 01 and 02 use one ticket's verbs alone. A step-2
  worker's gate is `--allow-pending` with none of its own verbs left in the
  `unbuilt verbs still needed` line. After the last step-2 merge, run
  `/usr/bin/python3 -B pm/tests/run_transcripts.py -k 0 -k 10 -k 11 -k 12 -k 13 -k 14 -k 18 -k 20 -k 21`
  without `--allow-pending`: transcripts 01 to 14, 18, 20 and 21 must pass. Dispatch a
  fix worker per failing transcript before step 3. Do the same after step 3 for 15,
  16, 19, 22 and 23.
- fc-a731f4 changes the path every mutating verb goes through. Give its branch a
  read-only reviewer check before merge.
- fc-d6c61c deletes `pm/v2/`. That is a destructive step: reviewer check on the branch
  first, per the skill.
- Nothing here deploys, and no operator-run step splits the chain.

## Hard rules for this initiative

- Read-only, never written by this initiative: everything under `~/frontier`,
  `~/.local/bin`, `~/.local/libexec`, `~/.config/pm`, every provider config directory,
  every registered store's `.pm/` (the import check works on copies), and the untracked
  `pm/dash-ui/`, which belongs to someone else.
- Commits land only in `~/projects/frontier-clean`, on ticket branches merged by
  `wt finish`.
- The installed `pm` and `wt` on `PATH` are the old ones. You run this epic with them:
  `pm ticket ...`, `wt start`, `wt finish`. The pm being built is `pm/cli/pm` and is
  never put on `PATH` here. Say which one you mean in every worker prompt; the two have
  different verbs.
- This repository's own store is a spec v2 store and stays one. No worker runs the new
  pm against it; tests use temporary directories.
- The fc store sets `findings_required`: every `wt finish` and `wt park` carries
  `--findings`.

## Your first turn

1. Read the list above.
2. Reconcile the ledger against `pm ticket tree fc-2a6562`; fix any drift and commit.
3. Confirm the gate runs. Before any work, `pm/cli/pm` is still the ported dispatcher,
   so `/usr/bin/python3 -B pm/tests/run_transcripts.py -k 01-init` must end
   `transcripts: passed 0, pending 0, failed 1`. Any other ending means the runner is
   broken; stop and report.
4. Run the upstream check in PLAN.md, section "The old pm keeps moving". File a child
   ticket for each new behavior the design does not cover.
5. Write the first fc-dac416 prompt, `wt start fc-dac416 --as claude`, dispatch its worker.
6. End with the cadence update, not a plan or a summary of what you read.
