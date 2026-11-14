# pm-wt-rewrite/04/02e pm backup, restore, the store of a linked worktree fc-2a6562:fc-3f4bfa

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02e-backup.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02e pm backup, restore, the store of a linked worktree fc-2a6562:fc-3f4bfa

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02e-backup.md`

Ticket **fc-3f4bfa**, the fifth step-2 worker. The core and fc-e2d8c9 (routing and
`doctor`) are merged, with every other step-2 ticket. fc-f3c2bd runs in parallel and
edits the mutating verb files and `get.py`; your write set is `store.py`, `init.py`,
`doctor.py` and the new `restore.py`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first,
especially "Module contract" and "Shared files in a parallel step".

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-3f4bfa`.

## Read first

`pm/docs/design.md` sections "Store" and "Backup"; transcript `18-backup.t`;
`pm/tools/store.py`, `pm/tools/verbs/init.py` and `pm/tools/verbs/doctor.py`.

## Deliver

1. The backup in `store.change`, after the append: inside a git checkout only,
   `git hash-object -w .pm/log.jsonl` then `git update-ref refs/pm/log <sha>`, run
   with `subprocess` and the store root as cwd. Any failure prints one line,
   `pm: warning: backup failed: <reason>`, on stderr, and never changes the exit code.
2. Store lookup, in this order: the nearest ancestor with `.pm/log.jsonl`; else, in a
   git checkout, the main checkout's root (from `git rev-parse --git-common-dir`)
   when it has `.pm/log.jsonl`; else an ancestor with `.pm/config.json` but no log
   refuses `this store's log is missing. Bring it back from its git backup: pm restore`.
   A linked worktree carries the tracked `config.json` without the log, so the second
   step must come before the third.
3. `pm/tools/verbs/restore.py`: writes the blob at `refs/pm/log` back when the log is
   missing or shorter, with the output and refusal of transcript 18.
4. `init` adds `.pm/log.jsonl` to `.gitignore` (creating it, or appending the line
   when absent), only inside a git checkout. Remove the `store.unbuilt("backup")`
   call core left in `init.py` for a git checkout.
5. `doctor` adds `backup: refs/pm/log is current`, or says how it differs, inside a
   git checkout.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 18-backup -k 01-init -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The second exits 0 with `failed 0`, and its `unbuilt verbs still needed` line names
not `restore`. If `18-backup.t` is still pending, name the verb it waits on and
confirm every step before that call matches.

## Report

Commit message `pm backup: refs/pm/log, restore, linked worktrees`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-3f4bfa/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02e-backup.md`.
