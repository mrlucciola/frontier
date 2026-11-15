# pm and wt rewrite into frontier-clean

pm (ticket store CLI) and wt (worktree lifecycle CLI) live in
`~/frontier/runtime-tools/` and deploy through frontier's pipeline. They move
into `pm/` and `wt/` here as self-contained components. The old tools stay
installed and untouched until an operator-run cutover.

The work is orchestrated runs, one per epic, each launched from its seed in
[PROGRAM.md](/docs/programs/pm-wt-rewrite/PROGRAM.md). The operator rules between
runs.

## Where this stands

| Run | Epic | State |
| --- | --- | --- |
| 01 pm port | fc-c3514f | Closed 2026-11-14. A faithful port of the old pm, at parity with it. |
| 04 pm redesign | fc-2a6562 | Closed 2026-11-14. The event-log pm replaces the port; all 25 transcripts pass. |
| 02 wt | fc-262fa8 | Closed 2026-11-14. A zsh wt on the redesigned pm; its 125-test black-box suite is green against the old wt and, with 2 old-side-only skips, the new one. |
| 03 delivery | fc-ccecda | Closed 2026-11-15. wt help with byte ceilings, the cost baseline in `pm/docs/cost.md`, Codex hooks recorded, principles finalized, and the cutover runbook, which nobody has run. |

## Rulings

Operator, 2026-11-12:

- **Language.** pm is standard-library Python at `/usr/bin/python3`. wt is zsh.
  JSON is never parsed in shell.
- **Runs.** One overseer session per epic. Cutover is never part of a run.

Operator, 2026-11-14, after the port landed:

- **Redesign pm.** The store becomes an append-only event log, verbs follow the
  agent's workflow, there is no skill, and plugins attach by file presence. The
  whole specification is [pm/docs/design.md](/pm/docs/design.md).
- **The format freeze is lifted.** Spec v2 is replaced; each store is imported
  once. Old ids are kept.
- **Order.** pm redesign, then wt as its first plugin, then delivery.
- **Other families leave pm.** Dashboards, the dispatch loop and intake are
  their own components, reached as plugins. The dispatch headings check and the
  pilot contract ship as two plugins inside `pm/plugins/`.

Superseded by that ruling: the port as the end state, the parity suite as the
gate, and fc-9076a6, the three write-reduction config keys, which solve a problem
the log does not have.

Operator, 2026-11-15, after delivery:

- **No sharing across clones.** A store's log belongs to one checkout; no `pm sync`.
- **dash-ui is its own tool.** It lives at `dash-ui/`, a nested repo ignored here.
  It reads tickets through the `pm` command, and pm has no knowledge of it. When pm
  changes, the agents working in dash-ui keep it current. This supersedes
  "Dashboards ... reached as plugins" above.
- **Follow-ups** run as epic fc-359b5b: nested stores, the per-store backup, the
  prompt hook once per session, `link --note`, and runbook additions.

## How "done" is decided

Each run has a command that exits 0.

**pm redesign.** `pm/tests/t/` holds 23 transcripts: shell sessions with their
exact expected output and exit codes. They were written before the code.

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py
```

There is no implementation to prove them against, which the parity suite had.
What was proven on 2026-11-14: the runner passes, fails and reports pending
correctly against a stand-in CLI; all 23 transcripts parse and run to the end;
the import fixture is a valid spec v2 store by the installed pm's `validate`.
So a transcript can be wrong. The rule: a worker never edits a transcript, the
fixtures or the design. A contradiction goes to the overseer, who fixes one side
in a commit of its own and records it in the ledger.

**The pending rule.** The dispatcher's verb table is complete from the first
ticket. A verb with no file reports itself: it appends its name to the file in
`$PM_UNBUILT_LOG` and exits 70. A transcript whose first wrong step comes at or
after such a call is `pending`. One whose first wrong step comes before any is
`failed`. After every ticket `--allow-pending` must exit 0, and pending only
shrinks. The last ticket removes the mechanism and requires `pending 0`.

Two more gates close the epic: `pm/tests/test_budgets.py`, byte ceilings on help,
refusals and injected text; and `pm/tests/import_check.py`, which imports a copy
of every registered store and compares it with the installed pm's view.

**wt.** The old wt tests import Python internals and cannot gate a zsh rewrite.
The wt run's first ticket writes a black-box suite from the
[behavior contract](/wt/docs/contract.md). It reaches tickets through an adapter
with an old-pm and a new-pm side, and is proven green against the old wt on the
old pm. The same pending rule applies, keyed on `$WT_UNBUILT_LOG`.

## Run 04: pm redesign (epic fc-2a6562)

The first ticket moves the port to `pm/v2/` untouched, so new code is born at its
final paths. The last ticket deletes `pm/v2/`.

| Step | Ticket | Transcripts | Mode |
| --- | --- | --- | --- |
| 1 | fc-dac416 core: quarantine, dispatcher, store, `init new show help` | 01, 02 | serial |
| 2 | fc-195118 lifecycle | 03, 04, 05, 10, 12 | parallel |
| 2 | fc-ef483a reads | 06, 07, 14, 20 | parallel |
| 2 | fc-8b871a structure and the duplicate guard | 08, 09, 11 | parallel |
| 2 | fc-e2d8c9 stores, routing, doctor | 13, 21 | parallel |
| 2 | fc-3f4bfa backup and restore | 18 | parallel |
| 3 | fc-a731f4 plugins, with `dispatch` and `pilot` | 15, 22, 23 | after lifecycle and reads |
| 3 | fc-a761be harness hooks, Claude and opencode | 16 | after lifecycle and reads |
| 3 | fc-4a8593 import and the import check | 19 | after lifecycle, structure and stores |
| 4 | fc-d6c61c integration: budgets, concurrency, remove `pm/v2`, docs, review | 17, all | serial |

## Run 02: wt (epic fc-262fa8)

```text
wt/cli/wt                         zsh dispatcher
wt/tools/lib/{git,pm,fail,config}.zsh
wt/tools/verbs/<verb>.zsh         start finish park status prune selftest
wt/pm-plugin/                     pre-done, post-take, orient
wt/tests/test_wt_cli.py           black-box suite
```

wt keeps no JSON. It reads tickets with `pm get`, keeps its own facts with
`pm emit`, and takes its configuration from files: an executable `.wt/gate` and
a `.wt/known-red` list. `wt pending` is dropped for `pm ls parked`.

| Step | Ticket | Mode |
| --- | --- | --- |
| 0 | fc-30c060 characterization suite, green against the old wt | serial |
| 1 | fc-122c0d dispatcher and lib | serial; waits on fc-d6c61c |
| 2 | fc-8ecb48 start; fc-249727 finish and land; fc-917232 park; fc-983ff4 status and prune; fc-347c67 the pm plugin | parallel |
| 3 | fc-8c1f62 integration, selftest, docs, review | serial |

If the old wt cannot be characterized inside the sandbox, step 0 lists the
uncovered cases with the operator-terminal command for each and the run stops
there.

## Run 03: delivery (epic fc-ccecda)

| Ticket | Delivers |
| --- | --- |
| fc-03292e | wt help that teaches, its byte ceilings, and a line-by-line account of the old skill |
| fc-f9ab11 | instruction cost measured before and after |
| fc-2c0656 | Codex: supported events recorded and wired |
| fc-121923 | component principles and behavioral contract finalized |
| fc-10981e | cutover runbook |

fc-42f64c, fc-dfcc49 and fc-5ac03b were closed as superseded by fc-a761be.

## Cutover

Operator-run, after Run 03, from [the runbook](/docs/programs/pm-wt-rewrite/CUTOVER.md)
fc-10981e writes. It imports each
store, writes the registry, switches the `~/.local/bin` symlinks, links the
plugins, registers hooks, and retires the frontier packages and skills. Import
leaves every `tickets.jsonl` untouched, so rollback is re-pointing two symlinks.

## Stop conditions for every run

- A gate red after two attempts without a diagnosis: failure-retro, stop.
- Any need to write under `~/frontier`, or to edit provider configuration: out
  of scope; park the ticket and report.
- A transcript, fixture, characterization test or the design looks wrong: the
  worker stops and reports. Only the overseer changes them.
- For the redesign: a verb needs a second writer or a rewrite of the log; a
  plugin use case cannot be met by the four plugin files; import would lose a
  ticket, or a note other than an edit-trail note.

## The old pm keeps moving

Upstream commits landed in `~/frontier/runtime-tools/pm` all through the port,
and five drift tickets ported them. The redesign does not chase output text, but
a new upstream feature is still a requirement. On its first turn and before
closing, the Run 04 overseer runs this and files a ticket for each new behavior
the design does not already cover:

```sh
git --no-pager -C /Users/matthias/frontier log --oneline 90f8b81c..HEAD -- runtime-tools/pm runtime-tools/wt
```

Freezing feature work on the old pm and wt until cutover removes this.
