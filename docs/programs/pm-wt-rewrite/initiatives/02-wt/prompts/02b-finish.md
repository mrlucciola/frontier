# pm-wt-rewrite/02/02b wt verbs: finish and land fc-262fa8:fc-249727

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02b-finish.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/02b wt verbs: finish and land fc-262fa8:fc-249727

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02b-finish.md`

You are a worker on ticket fc-249727. You start with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-249727` on branch `fc-249727`; the
overseer created it after `start` merged, so `wt start` works in the suite. `park` is
being written in parallel by another worker and is not on your branch.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
it binds you (rules, the core, the rulings, the gate, the report).

## Deliver

`wt/tools/verbs/finish.zsh` only (`land` is dispatched to it with `WT_VERB=land`). Read
`pm ticket show fc-249727` (the spec; two of its lines are overruled, below), the
contract's `finish`, `land`, "Gate" and "Reading wt output" sections
(`wt/docs/contract.md`), the suite's `FinishTest`, the finish cases of
`DeferredTeardownTest`, `NeverForceTest` and `ResolutionTest`, and the old `cmd_finish`,
`read_gate`, `read_known_red`, `known_red_scan`, `run_gate`, `check_findings`,
`_close_ticket`, `_render_close_command` and `_finish_teardown` in
`/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only, lines 627-1066).

Overruled in the ticket body: no `pm done --dry-run` before the merge (findings are
checked through `wt_findings_required`, see `02-common.md`); and `refs/wt/merged/<id>`
stays a git ref (`git update-ref refs/wt/merged/<id> refs/heads/<id>` after a successful
ff-only merge of a branch with commits), with an optional `pm emit <id> wt.merged
sha=<sha>`.

The gate and known reds live in this file (they have one user). They read the **target
repo** (`WT_REPO`), not the store: `.wt/gate`, run in the worktree, label `.wt/gate`,
the line `wt: gate .wt/gate exit N, SKIP lines: K`, the last 30 output lines on failure;
a `.wt/gate` that exists and is not executable (or is a directory) refuses with exactly
`wt: <gate path> is not executable, so wt cannot run the gate; fix it or pass --no-gate.`;
`.wt/known-red` lines `<ticket id> <text>`, blank and `#` lines skipped, the id matched
literally (`${line#"$id"}`). The removed lib code that did this is
`git -C /Users/matthias/projects/frontier-clean show 4635204^:wt/tools/lib/config.zsh`:
port it into this file.

Port `cmd_finish` in the old order: refusals before any change (no worktree, merged
route, dirty worktree, store and repo guards, undeletable paths, findings), the gate
(unless `--no-gate`), rebase onto the default branch (a conflict auto-parks), the
ff-only merge from the main checkout retried up to three times (exhaustion auto-parks),
the merged marker, teardown with the lib (deferred line, `STOP.` line), then `pm done`
(skipped for `land` / `--keep-open`, which reject `--note` and `--findings`); a `pm done`
refusal after the merge prints the `OK: <id> merged ...; ticket NOT closed: ...` line
ending with the `pm done ...` command to run later.

**Auto-park** runs `"$WT_COMPONENT/cli/wt" park <id> --auto [--store S] [--repo R]` as a
subprocess and wraps its stdout note in finish's own line, as the old `cmd_finish` does
(lines 905-940). On your branch `park.zsh` does not exist, so that subprocess exits 70
and logs `park` to `$WT_UNBUILT_LOG`: finish must then exit 70 itself (so the test is
pending, not failed). The overseer re-runs the auto-park tests after both branches merge.

## Gate

Per `02-common.md`. Classes that must have no failed test, and no pending test except
those pending on `park` (the auto-park and park-calling cases): `FinishTest`, the finish
cases of `DeferredTeardownTest` and `NeverForceTest`, and the finish and land cases of
`ResolutionTest`. Every other pending test must name a verb other than `finish` or
`land` as its first unbuilt step. List the tests pending on `park` in the report.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02b-finish.md`
