# pm-wt-rewrite/04/03a2 pm plugins: review fixes fc-2a6562:fc-a731f4

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03a2-plugins-review-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/03a2 pm plugins: review fixes fc-2a6562:fc-a731f4

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03a2-plugins-review-fixes.md`

Ticket **fc-a731f4**, fix round on its branch. A read-only reviewer read the plugin
change and returned PARTIAL: `reports/03a-review.md` in the worktree. The overseer
added transcript `pm/tests/t/24-plugin-edges.t` for the edge cases. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4`.

## Deliver

Fix these review findings, on this branch, keeping `store.change` short and plain:

1. Drift between the pre-checked events and the locked ones: under the lock, compare
   the events `check` returns with the ones the `pre` hooks ran on, ignoring `ts` and
   `by`; when they differ, append nothing and refuse
   `the store changed while pm was checking. Run the command again.`
2. Skip the outside-the-lock `check` and the `pre` hooks entirely when no plugin has
   any `pre-*` file.
3. A `pre` hook that exits non-zero with no output refuses
   `plugin <name> refused <op> <id>.` (transcript 24).
4. A plugin file that cannot be executed (`OSError` from `subprocess`): a `pre` hook or
   `cmd` refuses `plugin <name> could not run <file>: <strerror>.`; an `orient` or
   `post` hook prints `pm: warning: plugin <name> could not run <file>: <strerror>.`
   on stderr and the verb carries on with its exit code unchanged. A `post` hook can
   never turn an appended change into a failure: collect post output before anything
   that can fail, and print the verb's output first.
5. `pilot`'s `pre-done` (and anything else in `pm/plugins/` that runs `pm`) runs with
   `cwd=$PM_STORE`, so a `done` on another store's ticket reads that store.
6. `emit` accepts only `[a-z0-9_-]+(\.[a-z0-9_-]+)+` and otherwise prints its existing
   refusal (transcript 24).
7. `pm help`'s `plugins:` line leaves out a plugin whose name is a verb or alias.
8. Drop names nobody uses from `plugins.py`'s return values (principle 6).

Prove by hand, in `<worktree>/.tmp/`, items 1, 4 (a broken `post` and a broken
`orient`) and 5 (a cross-store `pm done` with `pilot` linked), and paste the output.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 15 -k 17 -k 22 -k 23 -k 24 -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The first exits 0 with `passed 5`. The second exits 0 with `failed 0`.

## Report

Commit message `pm plugins: review fixes`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/03a2-plugins-review-fixes.md`.
