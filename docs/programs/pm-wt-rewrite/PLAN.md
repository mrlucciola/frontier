# pm and wt rewrite into frontier-clean

pm (ticket store CLI) and wt (worktree lifecycle CLI) live in
`~/frontier/runtime-tools/` and deploy through frontier's pipeline. They move
into `pm/` and `wt/` here as self-contained components, rewritten to the
[component principles](/docs/component-principles.md), with hook-driven
instruction delivery and an opencode integration. The old tools stay installed
and untouched until an operator-run cutover.

The work is three orchestrated runs, one per epic, each launched from its seed
in [PROGRAM.md](/docs/programs/pm-wt-rewrite/PROGRAM.md). The operator rules
between runs.

## Rulings (operator, 2026-11-12)

- **Language.** pm is standard-library Python at `/usr/bin/python3`. wt is zsh.
  JSON is never parsed in shell: wt reads ticket facts through pm's plain-text
  output.
- **Surface.** The [cut list](/pm/docs/cut-list.md) names every kept, dropped
  and deferred item.
- **Data.** The on-disk format, [spec v2](/pm/docs/spec/v2/SPEC.md), is frozen.
  A ticket that needs a format change stops its run.
- **Runs.** One overseer session per epic. Cutover is never part of a run.

## How "done" is decided

Each run has a command that exits 0.

**pm.** `pm/tests/test_cli_parity.py` is the old CLI suite, trimmed to the kept
surface. It drives a CLI as a subprocess, so it runs unchanged against old and
new code.

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
```

Baseline against the old CLI at `~/frontier/runtime-tools/pm/ticket/src/ticket`,
frontier `ff71ab3a`:

```text
Ran 268 tests in 232.077s
OK (skipped=9)
parity: passed 259, pending 0, failed 0, skipped 9
```

**The old pm is a moving target.** Three upstream commits landed while the
suite was being prepared. The suite is pinned to `ff71ab3a`; the
[cut list](/pm/docs/cut-list.md) holds the drift check the integration ticket
runs before declaring parity. Freezing feature work on the old pm for the
length of Run 1 removes this risk entirely.

**The pending rule.** While verbs are still being built, anything not built
calls `store.unbuilt(<name>)`: it appends the name to the file in
`$PM_UNBUILT_LOG` and exits 70. The runner counts a test that fails after
touching something unbuilt as `pending`, not `failed`. So after every ticket,
`--allow-pending` must exit 0 with `failed 0`, and the pending count only
shrinks. A real regression can never hide as "not done yet". The last pm ticket
removes the mechanism and requires `pending 0`.

**wt.** The old wt tests import Python internals and cannot gate a zsh rewrite.
The wt run's first ticket writes a black-box suite, `wt/tests/test_wt_cli.py`,
from the [behavior contract](/wt/docs/contract.md) and proves it green against
the old wt. The same pending rule applies, keyed on `$WT_UNBUILT_LOG`.

## Run 1: pm (epic fc-c3514f)

```text
pm/cli/pm                  dispatcher: pm ticket|view|hook <verb>
pm/tools/ticket            argparse entry, fixed tuple of kept verbs, lazy import of verbs/<verb>.py
pm/tools/store.py          find store, load, validate, lock, atomic write, commit, unbuilt()
pm/tools/routing.py        registry, prefix to store, frozen check, cross-store row lookup
pm/tools/gitcommit.py      default-branch commit and pm-store plumbing commit
pm/tools/verbs/<verb>.py   one file per verb: register(subparsers) and run(args)
```

The verb tuple is written once, in the first ticket. Parallel workers add only
their own verb files.

| Step | Ticket | Mode |
| --- | --- | --- |
| 1 | fc-2b34c9 core: store, entry, `init create show` | serial |
| 2 | fc-459fe0 routing, registry, frozen, `where stores` | serial |
| 3 | fc-d73327 lifecycle; fc-739601 reads; fc-c10bcf structure and edges; fc-c5e673 history; fc-913d02 checks and views | parallel, at most four workers at once |
| 4 | fc-59011f integration: `pending 0`, golden diff on every registered store, docs, readability review | serial |

### Open ruling: the deferred config features

fc-9076a6 holds `history_interval_seconds`, `compact_closed_after_days` and
`archive_closed_after_days`. They were deferred on the finding that no store
used them. That stopped being true the same night: frontier-clean 88103df
turned all three on for this repository's store. As ruled, fc-9076a6 is outside
Run 1 and blocks the cutover runbook (fc-10981e).

Recommended instead: build them in Run 1. Run these before launching the seed,
and the overseer schedules fc-9076a6 as a sixth step-3 ticket:

```sh
pm ticket reparent fc-9076a6 fc-c3514f
pm ticket dep fc-459fe0 blocks fc-9076a6
pm ticket dep fc-9076a6 blocks fc-59011f
```

Either way the rewrite must read rows the old pm already compacted; that is in
fc-2b34c9.

## Run 2: wt (epic fc-262fa8)

```text
wt/cli/wt                         zsh dispatcher
wt/tools/lib/{git,pm,fail}.zsh
wt/tools/verbs/<verb>.zsh         start finish park status pending prune selftest
wt/tests/test_wt_cli.py           black-box suite
```

| Step | Ticket | Mode |
| --- | --- | --- |
| 0 | fc-30c060 characterization suite, green against the old wt | serial; can start before Run 1 ends |
| 1 | fc-122c0d dispatcher and lib | serial; waits on fc-59011f |
| 2 | fc-8ecb48 start; fc-249727 finish and land; fc-917232 park; fc-983ff4 status, pending, prune | parallel |
| 3 | fc-8c1f62 integration on the rewritten pm, selftest, docs, review | serial |

If the old wt cannot be characterized inside the sandbox, step 0 lists the
uncovered cases with the operator-terminal command for each and the run stops
there.

## Run 3: instruction delivery (epic fc-ccecda)

| Ticket | Delivers |
| --- | --- |
| fc-42f64c | `pm hook <event>` for session-start, prompt and stop, one provider-neutral source |
| fc-dfcc49 | Claude adapter and registration fragment |
| fc-5ac03b | opencode plugin owned by the component |
| fc-03292e | pm and wt skills as orientation, route table and verb cards |
| fc-f9ab11 | instruction cost measured before and after |
| fc-2c0656 | Codex: supported events recorded and wired |
| fc-121923 | component principles and behavioral contract finalized |
| fc-10981e | cutover runbook |

## Cutover

Operator-run, after Run 3, from the runbook fc-10981e writes. It switches the
`~/.local/bin` symlinks, moves the registry, registers hooks, and retires the
frontier packages. Rollback is re-pointing two symlinks at `~/.local/libexec`.

## Stop conditions for every run

- A gate red after two attempts without a diagnosis: failure-retro, stop.
- Any need to change the spec v2 format, write under `~/frontier`, or edit
  provider configuration: out of scope; park the ticket and report.
- A parity or characterization test that looks wrong is never edited by a
  worker. It goes to the overseer, and a change lands in the cut list with its
  reason.

## Changes from the approved plan

- The Claude hook adapter is Python, not zsh. Its input and output are JSON.
- `pm ticket show <id> --field <name>` is new. It gives the zsh wt plain-text
  ticket facts.
- The runner gained the pending rule above, so each parallel ticket has a
  mechanical gate before the whole surface exists.
- The root README component rows for pm and wt are added by each epic's
  integration ticket, when the component passes its checks.
