# pm-wt-rewrite/02/00-4 wt characterization: status, prune, resolution fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-4-status.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-4 wt characterization: status, prune, resolution fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-4-status.md`

You are a worker on ticket fc-30c060, part 4, the last. You start with zero context. Your
worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch
`fc-30c060`; the overseer created it. `WT/` below means that worktree's `wt/` directory.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway under
the test's temp root; nothing touches a real repository or a registered store -- a
registry a test writes is the private one in the suite's env (`PM_STORES_FILE` on the old
side, `PM_STORES` on the new).

## What exists

Parts 1 to 3 on branch `fc-30c060`: `WT/tests/run_wt.py`, and in `WT/tests/test_wt_cli.py`
the isolated env, `WtCase.wt()`, `make_repo()`, the `OldPm`/`NewPm` adapters,
`AdapterTest`, `StartTest`, the finish classes, `ParkTest`, and empty `StatusPruneTest`
and `ResolutionTest`; maybe `WT/docs/uncovered.md`. Read the whole test file first; reuse
its helpers and keep its style: docstring quotes the contract phrase; assert exit codes
and the first words of wt's own lines; never pm's text. Earlier reports:
`docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-*.md` in the main
checkout.

## Read

1. `pm ticket show fc-30c060` -- the spec.
2. `WT/docs/contract.md`: "Verbs" (status, pending, prune, selftest, `--store`/`--repo`),
   "Deferred teardown and prune", "Reading wt output".
3. Old wt `cmd_status`, `cmd_pending`, `cmd_prune`, `cmd_selftest` and the store/repo
   resolution in `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py` (read-only).
   Read how the old pm's `where` reads its registry (`PM_STORES_FILE`) under
   `/Users/matthias/.local/libexec/pm/` (read-only) before you write a registry entry.

## Adapter addition

`register_store(prefix, repo)`: add a line to the side's private registry (old: the JSON
file at `PM_STORES_FILE`, in the shape the old pm reads; new: a `prefix path` line in the
file at `PM_STORES`, design.md "Ids and the registry"). Add one `AdapterTest` for it.

## Deliver

**`StatusPruneTest`**, each its own test:

- **status**: lists live worktrees joined against their tickets (ticket id, status in the
  output); a worktree with no ticket behind it shows as such; pin the line shape.
- **status after park**: a just-parked ticket is not listed by status.
- **status labels a deferred-teardown entry** `deferred-teardown`: a registration whose
  directory is gone. Build it by deleting a worktree directory in the throwaway repo with
  `shutil.rmtree` (test code, not wt) while its registration stays.
- **pending** (old side only; `self.skipTest` on the new side with the reason "dropped
  for pm ls parked"): lists `done-unmerged` tickets; pin how cleared blockers show.
- **prune**: clears a registration whose directory is gone, keeps the `.keep` entry,
  deletes a branch only when it is an ancestor of `main` and no worktree holds it, keeps
  an unmerged branch. Pin the remaining-registrations line shape if you can provoke it;
  else `uncovered.md`.
- **start runs prune quietly**: a stale registration is gone after an unrelated
  `wt start`, and start prints no prune output.
- **start with the worktree already present**: run `wt start <id>` twice from the same
  session; pin what the old wt does (it is not stated by the contract -- say so in the
  docstring).
- **selftest**: `wt selftest` exits 0. Its scratch goes under `$HOME/.claude/.tmp`, which
  is the private HOME.

**`ResolutionTest`**, each its own test:

- **unregistered prefix**: the store is the cwd repo.
- **registered prefix from another repo**: run `wt start <id>` with cwd in repo A for a
  ticket whose prefix is registered to repo B: the ticket is taken in B and the worktree
  is `B/.worktrees/<id>`.
- **two owners**: a prefix registered to two stores stops with a `wt:` line (assert only
  wt's prefix; pm's message is pm's).
- **`--store <path>`** overrides the lookup for an unregistered store, and the worktree
  target defaults to that store's repo.
- **`--repo <path>`** overrides the worktree target independently of the store.
- the same flags on `finish` and `park` (one test each is enough) and on `status` and
  `prune`.

A contract case that cannot run in the sandbox goes in `WT/docs/uncovered.md` (case, why,
the exact operator-terminal command). If the old wt contradicts the contract, pin what the
old wt does, and name the test and contract line in NOT DONE.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
```

must end `failed 0` with `pending 0, skipped 0`. Also run
`--pm new --allow-pending -k AdapterTest`: all pass. Both runs' last two lines go in
EVIDENCE verbatim.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-4-status.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
