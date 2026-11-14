# pm-wt-rewrite/02/02c wt verb: park fc-262fa8:fc-917232

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02c-park.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/02c wt verb: park fc-262fa8:fc-917232

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02c-park.md`

You are a worker on ticket fc-917232. You start with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-917232` on branch `fc-917232`; the
overseer created it after `start` merged, so `wt start` works in the suite.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
it binds you (rules, the core, the rulings, the gate, the report).

## Deliver

`wt/tools/verbs/park.zsh` only. Read `pm ticket show fc-917232` (the spec), the
contract's `park` lines (`wt/docs/contract.md`), the suite's `ParkTest`,
`DeferredTeardownTest` (park cases), the park cases of `StatusPruneTest`,
`NeverForceTest` and `ResolutionTest`, and the old `cmd_park` in
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only; lines 1068-1263).
Port it in the same order: no-worktree refusal; the merged route (tear down and close
with `pm done`, never park or drop); `.local` refusal; the cross-repo guards; the
missing-`.git` refusal; undeletable paths; findings (not on a zero-delta park; with
`--auto`, `none` on a `findings_required` store); the mass-deletion refusal; the WIP
commit `WIP: park <id>`; the zero-delta path (`pm drop`, worktree and branch removed with
`git branch -d`, the `--note/--findings were NOT recorded` line); else the note
`branch <id> @ <sha>; waits-on <x>; resume: wt start <id> [--as A] [--session S]
[--store S] [--repo R] && wt finish <id> [--store S] [--repo R]` (actor read from the
holder with `wt_pm_get` before parking; `--session` only when given or in the
environment, as the suite pins), the caller's `--note` prepended with `; `,
`pm park <id> -m <note>` (with `--findings` when given -- check `pm help park` for
whether pm accepts it, and if not, say what you did in the report), teardown with the
lib (keep entry, deferred line, `STOP.` line), `--waits-on <ticket id>` recorded as
`pm link <waits-on> blocks <id>` (a failure is a fault row, not a refusal), and
`pm emit <id> wt.park sha=<sha>`. Print `OK: <id> parked -- <note>` unless `--auto`.

`--auto` is the interface `finish` uses (see `02-common.md`, "finish -> park
interface"): print only the note on stdout, no `OK:` line, exit 0.

## Gate

Per `02-common.md`. Classes that must have no pending or failed test: `ParkTest`,
and the park cases of `DeferredTeardownTest` (`test_park_deferred`,
`test_zero_delta_park_deferred`). Every other pending test must name a verb other than
`park` as its first unbuilt step.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02c-park.md`
