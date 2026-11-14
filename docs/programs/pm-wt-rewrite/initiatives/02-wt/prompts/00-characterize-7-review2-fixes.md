# pm-wt-rewrite/02/00-7 wt characterization: side-neutral assertions and last gaps fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-7-review2-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-7 wt characterization: side-neutral assertions and last gaps fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-7-review2-fixes.md`

You are a worker on ticket fc-30c060, part 7, the final fix round. You start with zero
context. Your worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060`
on branch `fc-30c060`; the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` against a real repo, never mutate tickets with `pm ticket`,
never merge. Stop at 80k tokens or 40 tool calls, commit what is green, report the rest
under NOT DONE. Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config dirs, and this repo's `pm/`. Every repo a test builds is a throwaway
under the test's temp root, each with its own store prefix.

## Context

`WT/tests/test_wt_cli.py` (123 tests) and `WT/tests/run_wt.py` run one wt executable
against one of two pm sides, chosen by `WT_PM_SIDE`: `old` (installed `pm ticket ...`,
JSON gate config) or `new` (this repo's `pm/cli/pm`; the new wt runs an executable
`.wt/gate` and reads `.wt/known-red`). The suite is green against the old wt. The new
wt does not exist yet; it must be able to pass the same suite on the new side.

A second review found assertions a correct new wt could not pass:
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-review-2.md`.
Read it, then the test file. Line numbers there refer to commit c85a178.

## Overseer rulings (binding; record each in the touched test's docstring)

1. **Gate label.** Add an adapter method `gate_label()`: old side `" ".join(argv)` of
   the configured gate, new side the literal `.wt/gate`. Every assertion that echoes the
   gate argv uses it: the `wt: gate <label> exit N, SKIP lines: K` lines (pass, fail,
   land pass, land fail), `wt: --no-gate: skipping gate <label>`, and the close note's
   `gate skipped (--no-gate): <label>`.
2. **Malformed gate.** Side-neutral: a `wt:` line that contains `gate` and
   `fix it or pass --no-gate.`, plus `assert_untouched`. Drop the JSON wording.
3. **Contract over old wt, branched by side.** Where the old wt contradicts the
   contract and the contract is the behavior to keep, the test pins the old behavior
   when `SIDE == "old"` and the contract behavior when `SIDE == "new"`. Its docstring
   starts `Old wt deviates from the contract:` and names the contract line. Apply to:
   - **stale worktree, ticket already closed** (contract.md:198-200): new side --
     worktree gone, branch gone, status `done`, and the last line starts `wt:`, names
     the id and says the close failed. Do not pin the exit code on the new side.
4. **Keep the old behavior on both sides** (a later ticket, fc-f0cc16, changes it):
   `test_rebase_conflict_auto_parks`, `wt start` re-conflicting. No change; add
   `See fc-f0cc16.` to its docstring.
5. **Fault rows.** Assert one file per root cause and at least one row; drop the
   "exactly 2 rows" check.
6. **`start` twice from the same session.** Assert state only: the worktree still
   exists at the same tip, the ticket is `taken` by the same holder, there is one
   registration for it. Do not pin the exit code or the output.
7. **Unregistered prefix on the new side.** Add an adapter method
   `unregister_store(repo)` (new: delete that repo's line from the `$PM_STORES` file;
   old: no-op, the old registry starts empty) and call it in
   `test_unregistered_prefix_uses_cwd_repo`.
8. **Remaining gaps**: a `land` cross-repo guard test (reuse the finish guard helper);
   next-step words for `land --findings`, as `--note` has them. The partial-pair guard
   case (pair declared for commit but not for worktree): add it if the old wt's guard
   distinguishes the two (read `crossrepo.py`); else say so in NOT DONE.

Not to change: the selftest scratch path (not pinned, by ruling), the merged marker
after a successful finish (the old wt clears it with the branch; 2b pinned that), and
`status` accepting `taken` or `claimed`.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.tmp/wt-unbuilt-stub --pm new --allow-pending
```

The first: `failed 0`, `pending 0`, `skipped 0`. The second (a stand-in wt that answers
every verb as unbuilt): `failed 0`, exactly 2 skips, every other wt test pending. Paste
each run's last two lines in EVIDENCE. Then grep the test file for old-only words a
correct new wt cannot print outside an `if SIDE == "old"` branch or the old adapter
(`.pm/config.json`, `non-empty list`, `pm ticket`, `--via`, `claimed`, `done-unmerged`,
`where --mutate`) and list each remaining hit with its line and why it is safe.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-7-review2-fixes.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
