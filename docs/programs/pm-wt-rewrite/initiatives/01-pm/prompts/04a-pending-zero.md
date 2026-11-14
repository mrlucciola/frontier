# pm-wt-rewrite/01/04a pm integration: remove the unbuilt mechanism, parity pending 0 fc-c3514f:fc-59011f

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04a-pending-zero.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/04a pm integration: remove the unbuilt mechanism, parity pending 0 fc-c3514f:fc-59011f

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04a-pending-zero.md`

Ticket **fc-59011f** (pm integration), first of several serial workers on its branch.
Every kept verb is merged. You remove the scaffolding that let the build proceed verb by
verb and bring the full parity suite to `pending 0, failed 0`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` (its "Where you
work" and "Rules" sections bind you too; your worktree is named below).

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f`.
- Spec: `pm ticket show fc-59011f`, body and every note.

## Deliver

1. Remove the unbuilt mechanism: `store.unbuilt`, `UNBUILT_EXIT`, every call to it, and
   the missing-verb-file branch in `pm/tools/ticket` (a kept verb with no file is now a
   bug, not a state). The epilog line about exit 70 goes too. `pm/tests/run_parity.py`
   stays as it is.
2. `pm/tests/test_cli_contract.py`: remove the `skipTest("unbuilt: ...")` branches and
   the unbuilt-contract test; every refusal case now runs and passes. Fix a test's argv
   shape where it was a placeholder copied from the old parser (the `dep`/`unlink`
   cases use `tt-other`).
3. Run the full suite without `--allow-pending`. Make every failing test pass; a fix may
   touch any file under `pm/tools/`, still keeping texts byte-identical to the old CLI.
   `StoreRoutingTest` gets its first full run here: read its failures carefully.

## Gate

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B -m unittest discover -s pm/tests
```

The first must end `pending 0, failed 0` with `skipped 9` (the `@DEFERRED` tests) and
exit 0; the second must pass with no skips other than those. Redirect the parity run to
the worktree's `.tmp/` and paste its last three lines.

## Report

Commit message `pm integration: remove the unbuilt mechanism; parity pending 0 (fc-59011f)`.
Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04a-pending-zero.md`.
